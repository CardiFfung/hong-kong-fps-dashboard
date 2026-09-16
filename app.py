"""Presentation only: all financial calculations live in src/pipeline.py."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.pipeline import (LABELS, SUBTYPES, URLS, findings, latest_complete,
                          load_snapshot, refresh)

st.set_page_config(page_title='香港轉數快 · FPS Trends', page_icon='↗', layout='wide')
st.markdown('''<style>
.stApp {background:#f4f7fb;}
.block-container {padding-top:2.3rem; max-width:1480px;}
h1,h2,h3 {color:#102943;}
[data-testid="stMetric"] {background:white;padding:18px;border-radius:12px;border:1px solid #dce5ed;}
[data-testid="stMetricValue"] {color:#087d8d;}
[data-testid="stSidebar"] {background:#eaf0f6;}
</style>''', unsafe_allow_html=True)
st.caption('PAYMENTS OBSERVATORY  /  HONG KONG  /  HKD ONLY')
st.title('香港「轉數快」使用趨勢')
st.markdown('**Hong Kong FPS Trends Dashboard** · 用金管局月度統計，了解支付規模、組成與平均交易金額。')

with st.sidebar:
    st.header('資料與篩選')
    st.caption('啟動時讀取已驗證官方快照。按下面按鈕先會連線更新；呢個頁面並非即時交易監察。')
    update = st.button('搜尋', type='primary', use_container_width=True)

if update:
    try:
        with st.spinner('正在下載兩組官方數據並驗證…'):
            refresh()
        st.session_state.pop('refresh_error', None)
        st.session_state['refreshed'] = True
    except Exception as exc:
        st.session_state['refresh_error'] = f'{type(exc).__name__}: {exc}'

try:
    data, meta = load_snapshot()
except Exception as exc:
    st.error('未有可用嘅已驗證資料。請按「搜尋」，或先執行 python -m src.pipeline。')
    st.caption(f'讀取失敗：{type(exc).__name__}: {exc}')
    st.stop()

if st.session_state.get('refresh_error'):
    st.error('API 更新失敗；以下使用上次成功快照，擷取時間：' + meta['retrieved_at'])
    with st.expander('錯誤詳情'):
        st.code(st.session_state['refresh_error'])
else:
    st.info('官方資料快照｜最後成功擷取：' + meta['retrieved_at'] + '｜並非即時數據')

latest = latest_complete(data)
st.caption(f'最新可分析完整月份：{latest.name:%Y-%m}　•　官方快照涵蓋：{data.index.min():%Y-%m} — {data.index.max():%Y-%m}　•　港元 HKD')
st.markdown(f'官方來源：[交易筆數]({URLS["volume"]}) · [交易金額]({URLS["value_hkd_thousand"]}) · [欄位定義](https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/monthly-statistical-bulletin/banking/ch-statistics-turnover-fps-hkd-payment-vol/)')
st.caption('單位：1 萬筆 = 10,000 筆；1 億港元 = HK$100,000,000。官方金額以千港元提供，本頁已乘 1,000 轉為港元。')
if meta['report']['warnings']:
    st.warning('資料品質提示：' + '；'.join(meta['report']['warnings']))

with st.sidebar:
    months = data.index.strftime('%Y-%m').tolist()
    period = st.select_slider('圖表月份範圍', options=months,
                              value=(months[0], latest.name.strftime('%Y-%m')))
    metric = st.radio('組成及類別圖指標', ['筆數', '金額'], horizontal=True)
    category = st.selectbox('趨勢及平均金額類別', list(LABELS), format_func=LABELS.get)
    ma = st.checkbox('顯示 12 個月移動平均', value=True)
    st.caption('指標卡固定顯示最新完整月份；下面圖表跟隨篩選。2018-09 為推出月份，保留原值但不參與增長率或移動平均。')
    st.caption('MoM = 同上月比較；YoY = 同上年同月比較。冇相應月份或分母為零時，百分比不適用。')

filtered = data.loc[period[0]:period[1]]
suffix = 'volume' if metric == '筆數' else 'value_hkd'
unit, divisor = ('萬筆', 1e4) if suffix == 'volume' else ('億港元', 1e8)


def fmt(value, digits=2):
    return '不適用' if pd.isna(value) else f'{value:,.{digits}f}'


def changes(row, col, scale, units):
    lines = []
    for lag, label in [('mom', '按月'), ('yoy', '按年')]:
        absolute, percent = row[col + '_' + lag + '_abs'], row[col + '_' + lag + '_pct']
        a = '不適用' if pd.isna(absolute) else f'{absolute / scale:+,.2f} {units}'
        p = '不適用' if pd.isna(percent) else f'{percent:+.2f}%'
        lines.append(f'{label}：{a}（{p}）')
    return '　\n\n'.join(lines)


st.subheader(f'最新月份概覽 · {latest.name:%Y-%m}')
for container, col, scale, units, title in zip(st.columns(3),
        ['total_volume', 'total_value_hkd', 'total_avg_hkd'], [1e4, 1e8, 1],
        ['萬筆', '億港元', '港元／筆'], ['交易總筆數', '交易總金額', '平均每筆金額']):
    with container:
        st.metric(title, fmt(latest[col] / scale) + ' ' + units,
                  help='平均 = 同月同類別金額 ÷ 筆數；總支付 = 即時支付 + 批量支付。')
        st.caption(changes(latest, col, scale, units))

st.subheader('數據話你知')
for finding in findings(data):
    st.markdown('• ' + finding)
st.caption('以上由完整資料自動計算，唔受圖表篩選影響；描述統計變化，唔代表原因或個人使用習慣。')

COLORS = ['#098697', '#e4a044', '#7186ad']
span = f'{period[0]} 至 {period[1]}'


def style(fig, title, ytitle):
    fig.update_layout(title=dict(text=title, font=dict(size=17)), height=355,
        margin=dict(l=20, r=20, t=65, b=35), paper_bgcolor='white', plot_bgcolor='white',
        font=dict(family='Arial, sans-serif', color='#243d54'),
        legend=dict(orientation='h', y=-0.23), hovermode='x unified',
        xaxis=dict(title='月份', tickformat='%Y-%m', showgrid=False),
        yaxis=dict(title=ytitle, gridcolor='#eaf0f5', rangemode='tozero'))
    return fig


def trend(column, scale, title, units):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=filtered.index, y=filtered[column] / scale, name='每月',
                            mode='lines', line=dict(color=COLORS[0], width=2.5), connectgaps=False,
                            hovertemplate='%{y:,.2f} ' + units + '<extra>%{fullData.name}</extra>'))
    if ma:
        fig.add_trace(go.Scatter(x=filtered.index, y=filtered[column + '_ma12'] / scale,
                                name='12 個月平均', line=dict(color=COLORS[1], dash='dot'), connectgaps=False))
    if pd.Timestamp('2018-09-01') in filtered.index:
        fig.add_vrect(x0='2018-09-01', x1='2018-10-01', fillcolor='#e4a044', opacity=.18,
                      line_width=0, annotation_text='推出月')
    st.plotly_chart(style(fig, title + '<br><sup>' + span + '</sup>', units), use_container_width=True)


st.subheader('01 / 支付規模')
a, b = st.columns(2)
with a:
    trend(category + '_volume', 1e4, LABELS[category] + ' · 每月交易筆數', '萬筆')
    st.caption('點讀：看每月交易次數及長期方向。唔可以當成活躍用戶數；月份日數亦會影響月度總量。')
with b:
    trend(category + '_value_hkd', 1e8, LABELS[category] + ' · 每月交易金額', '億港元')
    st.caption('點讀：看同一類別流經系統嘅總金額。唔可以直接推斷零售消費、銀行收入或經濟增長。')

st.subheader('02 / 即時支付與批量支付')
fig = go.Figure()
for i, cat in enumerate(['rt_payment', 'bat_payment']):
    fig.add_trace(go.Scatter(x=filtered.index, y=filtered[cat + '_' + suffix + '_share_total_pct'],
        name=LABELS[cat], mode='lines', line=dict(color=COLORS[i], width=2), connectgaps=False,
        hovertemplate='%{y:.2f}%<extra>%{fullData.name}</extra>'))
st.plotly_chart(style(fig, f'{metric}佔比 · 分母：同月總支付<br><sup>{span}</sup>', '佔總數（%）'), use_container_width=True)
st.caption('點讀：切換「筆數／金額」，比較兩種模式嘅比重；分母係同月 total。佔比唔係增長率，亦唔代表市場佔有率。缺失值會斷線，來源合計不一致時唔會強行調整至 100%。')

st.subheader('03 / 平均每筆金額')
trend(category + '_avg_hkd', 1, LABELS[category] + ' · 平均每筆', '港元／筆')
st.caption('點讀：同類別同月金額（千港元）× 1,000 ÷ 筆數。例如 50,000 千港元 ÷ 10,000 筆 × 1,000 = 5,000 港元／筆。零筆數或缺失資料留空。平均值唔係中位數，可能受少量大額交易影響；虛線係 12 個月「月平均每筆」嘅簡單平均。')

st.subheader('04 / 即時轉帳內部組成')
fig = go.Figure()
for i, cat in enumerate(SUBTYPES):
    fig.add_trace(go.Scatter(x=filtered.index, y=filtered[cat + '_' + suffix] / divisor,
        name=LABELS[cat], mode='lines', line=dict(color=COLORS[i]), connectgaps=False))
st.plotly_chart(style(fig, f'即時轉帳三個互不重疊子類別 · {metric}<br><sup>{span}</sup>', unit), use_container_width=True)
comparison = pd.DataFrame({LABELS[c]: filtered[c + '_' + suffix + '_share_rtctp_pct'] for c in SUBTYPES})
comparison.index = comparison.index.strftime('%Y-%m')
st.dataframe(comparison.rename_axis('月份').tail(12), column_config={LABELS[c]: st.column_config.NumberColumn(format='%.2f%%') for c in SUBTYPES}, use_container_width=True)
st.caption('表格列出所選期間最後 12 個月；百分比分母係同月即時轉帳合計 rtctp，包括兩種個人發起方式及其他即時轉帳，唔包括即時扣帳或批量支付。唔可以由呢張圖推斷收款人係咪個人，亦唔能夠辨認獨立用戶。')
st.caption('「個人兩種發起方式之間嘅代碼比例」另外存於下載檔 proxy_*_share_personal_pct，分母只係代碼 + 帳戶號碼，唔包括其他即時轉帳。')

st.subheader('資料下載與核對')
st.caption('CSV 跟隨月份篩選，包含所有類別、兩種指標及集中計算嘅衍生欄位，方便重現分析。')
st.download_button('下載篩選後 CSV', filtered.to_csv(date_format='%Y-%m').encode('utf-8-sig'),
                   file_name=f'fps_hkd_{period[0]}_{period[1]}.csv', mime='text/csv')
with st.expander('查看目前資料及品質報告'):
    st.dataframe(filtered[['total_volume', 'total_value_hkd_thousand', 'total_value_hkd', 'total_avg_hkd']])
    st.json(meta['report'])
with st.expander('定義與限制（閱讀前請留意）'):
    st.markdown('''- 僅分析港元；不包含人民幣。整體月度統計，並非個人交易紀錄。
- 即時轉帳 + 即時扣帳 = 即時支付；即時支付 + 批量支付 = 總支付。切勿將合計再加子類別。
- 2018-09-30 全面推出；2018-09 可能僅屬部分月份，圖上標記，增長及移動平均排除。
- MoM、YoY 使用確切上月／上年同月。缺資料不補零，零分母百分比不適用。
- 最新完整月份指曆月已結束、兩組總數均可用，唔保證官方日後不修訂。
- 月份長短、節日及交易組成均可能影響數字；此作品不作因果推論或預測。''')
st.caption('Independent portfolio project · Public HKMA data · 並非金管局官方產品')
