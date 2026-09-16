from unittest.mock import patch
from src.pipeline import ROOT

from streamlit.testing.v1 import AppTest


def test_dashboard_filters_and_kpis():
    app = AppTest.from_file(ROOT / 'app.py').run(timeout=30)
    assert not app.exception
    assert len(app.metric) == 3
    assert len(app.get('plotly_chart')) == 5
    app.radio[0].set_value('金額')
    app.selectbox[0].set_value('bat_payment')
    app.select_slider[0].set_value(('2025-01', '2026-08'))
    app.run(timeout=30)
    assert not app.exception
    assert len(app.get('plotly_chart')) == 5


def test_api_error_shows_dated_fallback():
    app = AppTest.from_file(ROOT / 'app.py').run(timeout=30)
    with patch('src.pipeline.refresh', side_effect=RuntimeError('Simulated API unavailable')):
        app.button[0].click().run(timeout=30)
    assert not app.exception
    assert '上次成功快照' in app.error[0].value
    assert len(app.metric) == 3


def test_no_snapshot_never_displays_fake_kpis():
    with patch('src.pipeline.load_snapshot', side_effect=FileNotFoundError('No snapshot')):
        app = AppTest.from_file(ROOT / 'app.py').run(timeout=30)
    assert not app.exception
    assert len(app.error) == 1
    assert len(app.metric) == 0
