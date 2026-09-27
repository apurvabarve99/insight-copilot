from tools.calculation_tool import (
    calculate_sum,
    calculate_percentage_change
)
from tools.data_tool import (
    get_top_n,
    get_grouped_summary,
    get_monthly_summary
)
from tools.trend_tool import get_monthly_trend
from tools.anomaly_tool import detect_anomalies


def test_calculate_sum():
    result = calculate_sum([10, 20, 30])
    assert result == 60


def test_percentage_change():
    result = calculate_percentage_change(100, 120)
    assert result == 20.0


def test_top_products():
    result = get_top_n(
        group_by="Product",
        metric="Revenue",
        n=5
    )

    assert len(result) == 5
    assert "Product" in result.columns
    assert "Revenue" in result.columns


def test_region_summary():
    result = get_grouped_summary(
        group_by="Region",
        metric="Revenue"
    )

    assert not result.empty
    assert "Region" in result.columns
    assert "Revenue" in result.columns


def test_monthly_summary():
    result = get_monthly_summary(
        metric="Revenue"
    )

    assert len(result) == 12
    assert "Month" in result.columns
    assert "Revenue" in result.columns


def test_monthly_trend():
    result = get_monthly_trend(
        metric="Revenue"
    )

    assert len(result) == 12
    assert "Month" in result.columns
    assert "Revenue" in result.columns
    assert "Percentage_Change" in result.columns


def test_anomaly_detection():
    result = detect_anomalies(
        column="Profit"
    )

    assert "Profit" in result.columns
    assert len(result) > 0