"""Unit tests for mock vs real backend routing (no Streamlit)."""

from portfolio_mode import (
    CLOUD_MOCK_OPTIONS,
    CLOUD_REAL_OPTIONS,
    MODE_MOCK,
    MODE_REAL,
    cloud_backend_options,
)


def test_cloud_options_mock():
    opts = cloud_backend_options(MODE_MOCK)
    assert "off" in opts
    assert CLOUD_MOCK_OPTIONS[0] in opts
    assert CLOUD_REAL_OPTIONS[0] not in opts


def test_cloud_options_real():
    opts = cloud_backend_options(MODE_REAL)
    assert "off" in opts
    assert CLOUD_REAL_OPTIONS[0] in opts
    assert CLOUD_MOCK_OPTIONS[0] not in opts
