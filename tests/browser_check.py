"""Run against a live local Streamlit server. Browser installed separately."""
import json
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1512, 'height': 1300}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8501', wait_until='networkidle')
    page.get_by_text('01 / 支付規模', exact=True).wait_for(timeout=30000)
    page.locator('[data-testid="stPlotlyChart"]').last.wait_for(timeout=30000)
    assert page.locator('[data-testid="stPlotlyChart"]').count() == 5
    assert page.locator('[data-testid="stException"]').count() == 0
    page.screenshot(path=str(ROOT / 'docs/dashboard.png'), full_page=True)
    page.get_by_text('金額', exact=True).first.click()
    page.get_by_role('combobox').click()
    page.get_by_role('option', name='批量支付', exact=True).click()
    page.get_by_text('下載篩選後 CSV', exact=True).scroll_into_view_if_needed()
    with page.expect_download() as download_info:
        page.get_by_text('下載篩選後 CSV', exact=True).click()
    download = download_info.value
    download.save_as('/tmp/fps-browser-download.csv')
    frame = pd.read_csv('/tmp/fps-browser-download.csv')
    assert len(frame) == 96
    assert frame.iloc[-1].total_volume == 82587554
    assert not errors, errors
    page.screenshot(path=str(ROOT / 'docs/dashboard-detail.png'), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto('http://127.0.0.1:8501', wait_until='networkidle')
    page.get_by_text('01 / 支付規模', exact=True).wait_for(timeout=30000)
    page.screenshot(path=str(ROOT / 'docs/dashboard-mobile.png'), full_page=True)
    assert page.locator('[data-testid="stException"]').count() == 0
    print(json.dumps({'charts': 5, 'csv_rows': len(frame), 'browser_errors': errors,
                      'screenshots': ['dashboard.png', 'dashboard-detail.png', 'dashboard-mobile.png']}, indent=2))
    browser.close()
