"""HKD-only FPS acquisition, validation and centralized calculations."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/banking/'
URLS = {kind: BASE + 'ch-statistics-turnover-fps-hkd-payment-' + suffix
        for kind, suffix in [('volume', 'vol'), ('value_hkd_thousand', 'val')]}
LABELS = {
    'total': '總支付', 'rt_payment': '即時支付', 'bat_payment': '批量支付',
    'rtctp': '即時轉帳', 'rtddp': '即時扣帳',
    'rtctp_pp_payee_proxy_id': '個人：收款人代碼',
    'rtctp_pp_payee_acc_no': '個人：帳戶號碼', 'rtctp_other_payment': '其他即時轉帳',
}
FIELDS = list(LABELS)
SUBTYPES = ['rtctp_pp_payee_proxy_id', 'rtctp_pp_payee_acc_no', 'rtctp_other_payment']
HK = ZoneInfo('Asia/Hong_Kong')


class DataError(ValueError):
    """Raised when source data fail validation."""


def fetch_pages(url, pagesize=1000, session=None):
    if not 1 <= pagesize <= 1000:
        raise ValueError('pagesize must be between 1 and 1000')
    session = session or requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(
        total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])))
    pages, records, seen = [], [], set()
    offset = 0
    for _ in range(10000):
        response = session.get(url, params={'pagesize': pagesize, 'offset': offset,
                                           'sortby': 'end_of_month', 'sortorder': 'asc'}, timeout=(10, 35))
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get('header', {}).get('success') is not True:
            raise DataError(f'API reported failure: {payload!r}'[:400])
        result = payload.get('result', {})
        batch = result.get('records')
        if not isinstance(batch, list) or result.get('datasize') != len(batch):
            raise DataError('Invalid records or datasize in API response')
        if any(not isinstance(row, dict) for row in batch):
            raise DataError('API records must be objects')
        signature = hashlib.sha256(json.dumps(batch, sort_keys=True).encode()).hexdigest()
        if batch and signature in seen:
            raise DataError('API repeated a page; stopped to prevent an infinite loop')
        seen.add(signature)
        pages.append({'request_url': response.url, 'payload': payload})
        records.extend(batch)
        if len(batch) < pagesize:
            return records, pages
        offset += len(batch)
    raise DataError('Pagination safety limit exceeded')


def clean(records, kind, report):
    if not records:
        raise DataError(f'{kind}: empty dataset')
    frame = pd.DataFrame(records)
    required = ['end_of_month', *FIELDS]
    missing = set(required) - set(frame.columns)
    if missing:
        raise DataError(f'{kind}: missing fields {sorted(missing)}')
    if not frame.end_of_month.astype(str).str.fullmatch(r'\d{4}-\d{2}').all():
        raise DataError(f'{kind}: invalid month format')
    try:
        frame['end_of_month'] = pd.to_datetime(frame.end_of_month, format='%Y-%m', errors='raise')
    except ValueError as exc:
        raise DataError(f'{kind}: invalid month') from exc
    if frame.end_of_month.duplicated().any():
        raise DataError(f'{kind}: duplicate months')
    frame = frame[required].set_index('end_of_month').sort_index()
    for col in FIELDS:
        converted = pd.to_numeric(frame[col], errors='coerce')
        if (frame[col].notna() & converted.isna()).any():
            raise DataError(f'{kind}.{col}: non-numeric data')
        if (converted.dropna() < 0).any() or not np.isfinite(converted.dropna()).all():
            raise DataError(f'{kind}.{col}: negative or non-finite data')
        if kind == 'volume' and (converted.dropna() % 1 != 0).any():
            raise DataError(f'{kind}.{col}: fractional transaction count')
        frame[col] = converted
    calendar = pd.date_range(frame.index.min(), frame.index.max(), freq='MS')
    report[kind] = {'rows': len(frame), 'start': str(frame.index.min().date()),
                    'end': str(frame.index.max().date()),
                    'missing_months': calendar.difference(frame.index).strftime('%Y-%m').tolist(),
                    'null_counts': {k: int(v) for k, v in frame.isna().sum().items()},
                    'extra_fields': sorted(set(records[0]) - set(required))}
    relations = [('total', ['rt_payment', 'bat_payment']),
                 ('rt_payment', ['rtctp', 'rtddp']), ('rtctp', SUBTYPES)]
    # Value precision is 0.00001 thousand HKD in the observed response.
    tolerance = 0 if kind == 'volume' else 0.0001
    for parent, children in relations:
        residual = frame[parent] - frame[children].sum(axis=1, min_count=len(children))
        for month, diff in residual[residual.abs() > tolerance].items():
            report['reconciliation_issues'].append({'dataset': kind, 'month': month.strftime('%Y-%m'),
                'relation': f'{parent} = ' + ' + '.join(children), 'residual': float(diff)})
    return frame.add_suffix('_' + kind)


def divide(numerator, denominator):
    return numerator.div(denominator.where(denominator > 0))


def derive(frame, as_of=None):
    """Require a full monthly calendar: shift(12) then means the same month last year."""
    frame = frame.copy().reindex(pd.date_range(frame.index.min(), frame.index.max(), freq='MS'))
    frame.index.name = 'end_of_month'
    now = pd.Timestamp(as_of) if as_of else pd.Timestamp(datetime.now(HK).date())
    frame['is_partial_launch_month'] = frame.index == pd.Timestamp('2018-09-01')
    frame['is_complete_calendar_month'] = frame.index < now.to_period('M').to_timestamp()
    eligible = (~frame.is_partial_launch_month) & frame.is_complete_calendar_month
    frame = {name: frame[name] for name in frame.columns}
    for category in FIELDS:
        frame[category + '_value_hkd'] = frame[category + '_value_hkd_thousand'] * 1000
        frame[category + '_avg_hkd'] = divide(frame[category + '_value_hkd'], frame[category + '_volume'])
        for measure in ['volume', 'value_hkd', 'avg_hkd']:
            name = category + '_' + measure
            series = frame[name].where(eligible)
            for lag, label in [(1, 'mom'), (12, 'yoy')]:
                baseline = series.shift(lag)
                frame[name + '_' + label + '_abs'] = series - baseline
                frame[name + '_' + label + '_pct'] = divide(series - baseline, baseline) * 100
            frame[name + '_ma12'] = series.rolling(12, min_periods=12).mean()
        for measure in ['volume', 'value_hkd']:
            frame[category + '_' + measure + '_share_total_pct'] = divide(
                frame[category + '_' + measure], frame['total_' + measure]) * 100
    for measure in ['volume', 'value_hkd']:
        personal = frame[SUBTYPES[0] + '_' + measure] + frame[SUBTYPES[1] + '_' + measure]
        for category in SUBTYPES:
            frame[category + '_' + measure + '_share_rtctp_pct'] = divide(
                frame[category + '_' + measure], frame['rtctp_' + measure]) * 100
        frame['proxy_' + measure + '_share_personal_pct'] = divide(frame[SUBTYPES[0] + '_' + measure], personal) * 100
    return pd.DataFrame(frame).rename_axis('end_of_month')


def prepare(volume, value, as_of=None):
    report = {'reconciliation_issues': []}
    vol, val = clean(volume, 'volume', report), clean(value, 'value_hkd_thousand', report)
    report['months_only_in_volume'] = vol.index.difference(val.index).strftime('%Y-%m').tolist()
    report['months_only_in_value'] = val.index.difference(vol.index).strftime('%Y-%m').tolist()
    merged = vol.merge(val, left_index=True, right_index=True, how='outer', validate='one_to_one')
    report['warnings'] = []
    for kind in URLS:
        if report[kind]['missing_months'] or any(report[kind]['null_counts'].values()):
            report['warnings'].append(f'{kind}: missing months or values; no filling applied')
    if report['months_only_in_volume'] or report['months_only_in_value']:
        report['warnings'].append('Month coverage differs between sources')
    if report['reconciliation_issues']:
        report['warnings'].append('Source totals do not reconcile; original values retained')
    return derive(merged, as_of), report


def latest_complete(frame):
    valid = frame.is_complete_calendar_month & ~frame.is_partial_launch_month
    valid &= frame[['total_volume', 'total_value_hkd']].notna().all(axis=1)
    if not valid.any():
        raise DataError('No common complete month with both totals')
    return frame.loc[valid].iloc[-1]


def findings(frame):
    row = latest_complete(frame)
    def pct(value):
        return '不適用' if pd.isna(value) else f'{value:+.2f}%'
    return [
        f'{row.name:%Y-%m} 總筆數為 {row.total_volume:,.0f} 筆，按月 {pct(row.total_volume_mom_pct)}，按年 {pct(row.total_volume_yoy_pct)}。',
        f'同月總金額為 {row.total_value_hkd / 1e8:,.2f} 億港元，按年 {pct(row.total_value_hkd_yoy_pct)}；平均每筆 {row.total_avg_hkd:,.2f} 港元。',
        f'即時支付佔總筆數 {row.rt_payment_volume_share_total_pct:.2f}%，佔總金額 {row.rt_payment_value_hkd_share_total_pct:.2f}%；筆數與金額組成並不相同。',
    ]


def refresh(root=ROOT):
    root = Path(root)
    stamp = datetime.now(HK).strftime('%Y%m%dT%H%M%S%f%z')
    raw_dir = root / 'data/raw' / stamp
    raw_dir.mkdir(parents=True, exist_ok=False)
    records, hashes = {}, {}
    for kind, url in URLS.items():
        records[kind], pages = fetch_pages(url)
        raw_path = raw_dir / (kind + '.json')
        raw_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
        hashes[kind] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    frame, report = prepare(records['volume'], records['value_hkd_thousand'])
    latest_complete(frame)
    output_dir = root / 'data/processed' / stamp
    output_dir.mkdir(parents=True)
    frame.to_csv(output_dir / 'fps.csv', date_format='%Y-%m', encoding='utf-8-sig')
    metadata = {'snapshot': stamp, 'retrieved_at': datetime.now(HK).isoformat(),
                'sources': URLS, 'raw_sha256': hashes, 'report': report,
                'findings': findings(frame)}
    (output_dir / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    # Publish both sources together; a failed refresh leaves the previous pointer intact.
    pointer = root / 'data/current.json'
    temporary = root / 'data' / ('current-' + stamp + '.tmp')
    temporary.write_text(json.dumps({'snapshot': stamp}), encoding='utf-8')
    os.replace(temporary, pointer)
    return frame, metadata


def load_snapshot(root=ROOT):
    root = Path(root)
    pointer = json.loads((root / 'data/current.json').read_text())
    stamp = pointer['snapshot']
    if Path(stamp).name != stamp:
        raise DataError('Invalid snapshot path')
    meta = json.loads((root / 'data/processed' / stamp / 'metadata.json').read_text())
    records = {}
    for kind in URLS:
        path = root / 'data/raw' / stamp / (kind + '.json')
        if hashlib.sha256(path.read_bytes()).hexdigest() != meta['raw_sha256'][kind]:
            raise DataError(f'Raw snapshot checksum mismatch: {kind}')
        records[kind] = [row for page in json.loads(path.read_text()) for row in page['payload']['result']['records']]
    # Recompute from original responses with today's complete-month eligibility.
    frame, _ = prepare(records['volume'], records['value_hkd_thousand'])
    return frame, meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download, validate and publish a complete HKD FPS snapshot')
    parser.add_argument('--offline', action='store_true', help='Verify and analyse saved official responses')
    args = parser.parse_args()
    data, metadata = load_snapshot() if args.offline else refresh()
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
