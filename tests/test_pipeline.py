import json
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from src import pipeline as p


def row(month, n=100):
    return dict(end_of_month=month, total=n, rt_payment=n * .8, bat_payment=n * .2,
                rtctp=n * .6, rtddp=n * .2, rtctp_pp_payee_proxy_id=n * .2,
                rtctp_pp_payee_acc_no=n * .2, rtctp_other_payment=n * .2)


def test_conversion_and_zero_volume():
    frame, _ = p.prepare([row('2025-01', 10000), row('2025-02', 0)],
                          [row('2025-01', 50000), row('2025-02', 50000)])
    assert frame.iloc[0].total_value_hkd == 50_000_000
    assert frame.iloc[0].total_avg_hkd == 5000
    assert pd.isna(frame.iloc[1].total_avg_hkd)


@pytest.mark.parametrize('change', ['duplicate', 'text', 'negative', 'infinite', 'badmonth', 'field'])
def test_reject_invalid_source(change):
    rows = [row('2025-01')]
    if change == 'duplicate': rows *= 2
    if change == 'text': rows[0]['total'] = 'unknown'
    if change == 'negative': rows[0]['total'] = -1
    if change == 'infinite': rows[0]['total'] = float('inf')
    if change == 'badmonth': rows[0]['end_of_month'] = '2025-13'
    if change == 'field': del rows[0]['rtctp']
    with pytest.raises(p.DataError): p.prepare(rows, [row('2025-01')])


def test_missing_month_not_previous_row_and_exact_yoy():
    rows = [row('2024-01', 100), row('2024-03', 200), row('2025-01', 300)]
    frame, report = p.prepare(rows, rows)
    assert pd.isna(frame.loc['2024-03-01', 'total_volume_mom_pct'])
    assert frame.loc['2025-01-01', 'total_volume_yoy_pct'] == 200
    assert '2024-02' in report['volume']['missing_months']


def test_launch_and_current_month_excluded():
    rows = [row('2018-09'), row('2018-10', 200), row('2018-11', 300)]
    frame, _ = p.prepare(rows, rows, as_of='2018-11-15')
    assert pd.isna(frame.loc['2018-10-01', 'total_volume_mom_pct'])
    assert p.latest_complete(frame).name == pd.Timestamp('2018-10-01')
    assert pd.isna(frame.loc['2018-11-01', 'total_volume_mom_pct'])


def test_zero_baseline_null_and_alignment():
    rows = [row('2025-01', 0), row('2025-02', 100)]
    frame, _ = p.prepare(rows, rows)
    assert pd.isna(frame.iloc[1].total_volume_mom_pct)
    assert frame.iloc[1].total_volume_mom_abs == 100
    values = [row('2025-01')]
    values[0]['total'] = None
    frame, report = p.prepare(rows, values)
    assert pd.isna(frame.iloc[0].total_avg_hkd)
    assert report['months_only_in_volume'] == ['2025-02']
    assert report['warnings']


def test_totals_logged_not_rewritten():
    rows = [row('2025-01')]
    rows[0]['total'] = 123
    frame, report = p.prepare(rows, rows)
    assert frame.iloc[0].total_volume == 123
    assert len(report['reconciliation_issues']) == 2


def test_denominators():
    rows = [row('2025-01')]
    frame, _ = p.prepare(rows, rows)
    assert frame.iloc[0].rtctp_pp_payee_proxy_id_volume_share_rtctp_pct == pytest.approx(100/3)
    assert frame.iloc[0].proxy_volume_share_personal_pct == 50
    assert frame.iloc[0].rt_payment_volume_share_total_pct == 80


def fake_response(records, success=True):
    response = Mock()
    response.url = 'https://example.test/page'
    response.json.return_value = {'header': {'success': success}, 'result': {'datasize': len(records), 'records': records}}
    return response


def test_pagination_including_exact_full_page():
    session = Mock()
    session.get.side_effect = [fake_response([row('2025-01'), row('2025-02')]), fake_response([])]
    rows, pages = p.fetch_pages('https://example.test', pagesize=2, session=session)
    assert len(rows) == 2 and len(pages) == 2
    assert session.get.call_args_list[1].kwargs['params']['offset'] == 2


def test_api_failure_and_repeated_pages():
    session = Mock()
    session.get.return_value = fake_response([], False)
    with pytest.raises(p.DataError): p.fetch_pages('https://example.test', session=session)
    session.get.return_value = fake_response([row('2025-01')])
    with pytest.raises(p.DataError, match='repeated'): p.fetch_pages('https://example.test', pagesize=1, session=session)


def test_failed_refresh_keeps_previous_pointer(tmp_path, monkeypatch):
    (tmp_path / 'data').mkdir()
    pointer = tmp_path / 'data/current.json'
    pointer.write_text('{"snapshot":"previous"}')
    mock = Mock(side_effect=[([row('2025-01')], []), RuntimeError('API unavailable')])
    monkeypatch.setattr(p, 'fetch_pages', mock)
    with pytest.raises(RuntimeError): p.refresh(tmp_path)
    assert json.loads(pointer.read_text())['snapshot'] == 'previous'


def test_saved_official_snapshot_matches_independent_decimal_calculation():
    frame, meta = p.load_snapshot()
    raw = {}
    for kind in p.URLS:
        pages = json.loads((p.ROOT / 'data/raw' / meta['snapshot'] / (kind + '.json')).read_text(), parse_float=Decimal)
        raw[kind] = {r['end_of_month']: r for page in pages for r in page['payload']['result']['records']}
    latest = p.latest_complete(frame)
    month = latest.name.strftime('%Y-%m')
    vol = Decimal(raw['volume'][month]['total'])
    val = raw['value_hkd_thousand'][month]['total'] * 1000
    assert latest.total_volume == int(vol)
    assert latest.total_value_hkd == pytest.approx(float(val))
    assert latest.total_avg_hkd == pytest.approx(float(val / vol))
    for lag, label in [(1, 'mom'), (12, 'yoy')]:
        previous = (latest.name - pd.DateOffset(months=lag)).strftime('%Y-%m')
        base = Decimal(raw['volume'][previous]['total'])
        assert latest['total_volume_' + label + '_pct'] == pytest.approx(float((vol/base-1)*100))
    assert frame.index.is_unique
    assert not meta['report']['warnings']
