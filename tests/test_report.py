import json

import pandas as pd
import pytest

import report
from report import build_kpi_payload, current_model


@pytest.fixture
def sample_df() -> pd.DataFrame:
    df = pd.DataFrame(
        [
            ("2024-01-10", "O1", "C1", "A", 100.4, 10.0),
            ("2024-02-10", "O2", "C2", "B", 300.0, -30.0),
        ],
        columns=["date", "order_id", "customer_id", "category", "sales", "profit"],
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_payload_is_json_serializable(sample_df):
    payload = build_kpi_payload(sample_df, "USD")

    json.dumps(payload)  # numpy 타입이나 NaN이 남아 있으면 실패한다
    assert payload["currency"] == "USD"
    assert payload["period"] == "2024-01-10 ~ 2024-02-10"


def test_payload_converts_ratios_to_percent_and_nan_to_null(sample_df):
    payload = build_kpi_payload(sample_df, "USD")
    months = payload[f"monthly_last_{report.RECENT_MONTHS}"]

    assert months[0]["sales_mom_pct"] is None  # 첫 달은 비교 대상 없음
    assert months[1]["sales_mom_pct"] == pytest.approx(198.8, abs=0.1)
    assert payload["by_category"]["B"]["profit_margin_pct"] == -10.0


def test_payload_without_profit(sample_df):
    payload = build_kpi_payload(sample_df.drop(columns="profit"), "KRW")

    assert "total_profit" not in payload["summary"]
    assert "profit_margin_pct" not in payload["by_category"]["A"]


def test_payload_keeps_only_recent_months():
    dates = pd.date_range("2022-01-01", periods=24, freq="MS")
    df = pd.DataFrame(
        {
            "date": dates,
            "order_id": [f"O{i}" for i in range(24)],
            "customer_id": "C1",
            "category": "A",
            "sales": 100.0,
        }
    )

    months = build_kpi_payload(df, "USD")[f"monthly_last_{report.RECENT_MONTHS}"]

    assert len(months) == report.RECENT_MONTHS
    assert months[0]["month"] == "2023-01"


def test_current_model_defaults_to_openai_mini(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    assert current_model() == ("openai", report.DEFAULT_MODELS["openai"])


def test_current_model_reads_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-5-5")

    assert current_model() == ("anthropic", "claude-opus-5-5")


def test_current_model_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown")

    with pytest.raises(ValueError):
        current_model()
