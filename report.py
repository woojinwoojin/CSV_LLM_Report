"""analysis.py의 KPI 결과를 LLM에 넘겨 자연어 분석 보고서를 만든다."""

import json
import os

import anthropic
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from analysis import SUPERSTORE, category_kpis, load_data, monthly_kpis, summarize

# .env의 LLM_PROVIDER로 openai / anthropic 중 선택한다. 모델도 .env에서 바꿀 수 있다.
# 크레딧 절약을 위해 기본값은 두 회사 모두 경량 모델.
DEFAULT_MODELS = {
    "openai": "gpt-5.4-mini",
    "anthropic": "claude-haiku-4-5",
}
RECENT_MONTHS = 12

SYSTEM_PROMPT = """당신은 이커머스 회사의 시니어 데이터 분석가입니다.
제공된 KPI 데이터만 근거로 경영진에게 보고할 분석 보고서를 한국어로 작성하세요.

- 숫자는 반드시 제공된 데이터에서만 인용하고, 직접 새로 계산하거나 추정한 값은 그렇다고 밝히세요.
- 월별 변화는 MoM(전월 대비)과 YoY(전년 동월 대비)를 함께 보고 해석하세요.
  쇼핑몰 매출은 계절성이 강하므로, MoM만으로 "급락/급등"이라고 결론 내리지 마세요.
- 데이터로 알 수 없는 원인은 단정하지 말고, 확인이 필요한 가설로 제시하세요.
- 금액에는 데이터의 currency 단위를 붙이세요 (예: $83,829).
- 월별 데이터를 표나 목록으로 다시 옮겨 적지 마세요. 의미 있는 변화와 특이점만 골라 해석하세요.
- 보고서는 제안 액션으로 끝내세요. 추가 작업을 제안하거나 질문하는 맺음말은 쓰지 마세요.

보고서 구성:
1. 핵심 요약 (3줄 이내)
2. 주요 KPI
3. 최근 12개월 추이와 특이점
4. 카테고리 분석 (매출과 수익성)
5. 제안 액션 (우선순위 순, 3개 이내)"""


def build_kpi_payload() -> dict:
    """LLM에 넘길 KPI를 JSON으로 바꿀 수 있는 형태로 모은다. 원본 행은 넘기지 않는다."""
    df = load_data(SUPERSTORE)
    monthly = monthly_kpis(df).tail(RECENT_MONTHS)

    monthly_rows = []
    for month, row in monthly.iterrows():
        monthly_rows.append(
            {
                "month": str(month),
                "sales": round(row["sales"]),
                "profit": round(row["profit"]),
                "orders": int(row["orders"]),
                "customers": int(row["customers"]),
                # 비교 대상이 없으면 NaN이므로 null로 넘긴다.
                "sales_mom_pct": None if pd.isna(row["sales_mom"]) else round(row["sales_mom"] * 100, 1),
                "sales_yoy_pct": None if pd.isna(row["sales_yoy"]) else round(row["sales_yoy"] * 100, 1),
            }
        )

    categories = {
        name: {
            "sales": round(row["sales"]),
            "profit": round(row["profit"]),
            "profit_margin_pct": round(row["profit_margin"] * 100, 1),
        }
        for name, row in category_kpis(df).iterrows()
    }

    return {
        "currency": SUPERSTORE.currency,
        "period": f"{df['date'].min().date()} ~ {df['date'].max().date()}",
        "summary": {k: round(float(v)) for k, v in summarize(df).items()},
        "by_category": categories,
        f"monthly_last_{RECENT_MONTHS}": monthly_rows,
    }


def build_user_message(payload: dict) -> str:
    return "다음 KPI 데이터로 분석 보고서를 작성해 주세요.\n\n" + json.dumps(
        payload, ensure_ascii=False, indent=2
    )


def generate_with_openai(payload: dict, model: str) -> str:
    client = OpenAI()  # .env의 OPENAI_API_KEY를 사용한다
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=build_user_message(payload),
        reasoning={"effort": "low"},  # 추론 토큰을 줄여 비용 절약
    )
    usage = response.usage
    print(f"[usage] {model} input={usage.input_tokens} output={usage.output_tokens}\n")
    return response.output_text


def generate_with_anthropic(payload: dict, model: str) -> str:
    client = anthropic.Anthropic()  # .env의 ANTHROPIC_API_KEY를 사용한다
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(payload)}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"모델이 요청을 거절했습니다: {response.stop_details}")
    usage = response.usage
    print(f"[usage] {model} input={usage.input_tokens} output={usage.output_tokens}\n")
    return "".join(block.text for block in response.content if block.type == "text")


def generate_report(payload: dict) -> str:
    provider = os.getenv("LLM_PROVIDER", "openai")
    if provider == "openai":
        return generate_with_openai(payload, os.getenv("OPENAI_MODEL", DEFAULT_MODELS["openai"]))
    if provider == "anthropic":
        return generate_with_anthropic(payload, os.getenv("ANTHROPIC_MODEL", DEFAULT_MODELS["anthropic"]))
    raise ValueError(f"지원하지 않는 LLM_PROVIDER: {provider}")


def main() -> None:
    load_dotenv()
    payload = build_kpi_payload()
    print(generate_report(payload))


if __name__ == "__main__":
    main()
