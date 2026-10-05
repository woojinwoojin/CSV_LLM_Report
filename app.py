"""로컬 확인용 Streamlit UI.

실행: .\\.venv\\Scripts\\streamlit run app.py
"""

import io
import json

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from analysis import SUPERSTORE, ColumnMap, Dataset, category_kpis, load_data, monthly_kpis, summarize
from report import RECENT_MONTHS, build_kpi_payload, current_model, generate_report

load_dotenv()
st.set_page_config(page_title="AI Data Analyst", page_icon="📊", layout="wide")

ROLES = {
    "date": ("주문 날짜", ["order date", "date", "주문일", "날짜"]),
    "sales": ("매출 금액", ["sales", "revenue", "amount", "매출", "금액"]),
    "order_id": ("주문 ID", ["order id", "order_id", "invoice", "주문"]),
    "customer_id": ("고객 ID", ["customer id", "customer_id", "user_id", "고객"]),
    "category": ("카테고리", ["category", "카테고리", "분류"]),
    "profit": ("이익 (선택)", ["profit", "이익"]),
}
NONE = "(없음)"


def guess_column(columns: list[str], keywords: list[str]) -> int:
    """컬럼 이름에 키워드가 들어 있으면 그 위치를, 없으면 0을 돌려준다."""
    for i, col in enumerate(columns):
        if any(k in col.lower() for k in keywords):
            return i
    return 0


@st.cache_data
def load_uploaded(data: bytes, mapping: dict, encoding: str, date_format: str | None) -> pd.DataFrame:
    dataset = Dataset(
        path=io.BytesIO(data),
        columns=ColumnMap(**mapping),
        currency="",
        encoding=encoding,
        date_format=date_format,
    )
    return load_data(dataset)


@st.cache_data
def load_default() -> pd.DataFrame:
    return load_data(SUPERSTORE)


def select_dataset() -> tuple[pd.DataFrame, str] | None:
    """사이드바에서 데이터를 고르고, (역할 이름으로 바뀐 df, 통화 단위)를 돌려준다."""
    st.sidebar.header("데이터")
    source = st.sidebar.radio("데이터 선택", ["기본 예시 (Superstore)", "CSV 업로드"])

    if source == "기본 예시 (Superstore)":
        if not SUPERSTORE.path.exists():
            st.error(f"기본 데이터가 없습니다: {SUPERSTORE.path}\nREADME의 데이터 다운로드 방법을 확인하세요.")
            return None
        return load_default(), SUPERSTORE.currency

    uploaded = st.sidebar.file_uploader("CSV 파일", type="csv")
    if uploaded is None:
        st.info("왼쪽에서 CSV 파일을 업로드하세요.")
        return None

    data = uploaded.getvalue()
    encoding = st.sidebar.selectbox("인코딩", ["utf-8", "cp1252", "cp949"])
    try:
        columns = list(pd.read_csv(io.BytesIO(data), nrows=0, encoding=encoding).columns)
    except (UnicodeDecodeError, pd.errors.ParserError) as e:
        st.error(f"파일을 읽지 못했습니다. 인코딩을 바꿔 보세요. ({e})")
        return None

    st.sidebar.subheader("컬럼 매핑")
    mapping = {}
    for role, (label, keywords) in ROLES.items():
        if role == "profit":
            options = [NONE] + columns
            choice = st.sidebar.selectbox(label, options, index=guess_column(options, keywords))
            mapping[role] = None if choice == NONE else choice
        else:
            mapping[role] = st.sidebar.selectbox(label, columns, index=guess_column(columns, keywords))

    date_format = st.sidebar.text_input("날짜 형식 (비우면 자동)", placeholder="%m/%d/%Y") or None
    currency = st.sidebar.text_input("통화 단위", value="KRW")

    try:
        return load_uploaded(data, mapping, encoding, date_format), currency
    except (ValueError, KeyError, TypeError) as e:
        st.error(f"매핑한 컬럼으로 분석할 수 없습니다. 매핑과 날짜 형식을 확인하세요. ({e})")
        return None


def show_kpis(df: pd.DataFrame, currency: str) -> None:
    summary = summarize(df)
    cols = st.columns(4)
    cols[0].metric(f"총 매출 ({currency})", f"{summary['total_sales']:,.0f}")
    cols[1].metric(f"총 이익 ({currency})", f"{summary['total_profit']:,.0f}" if "total_profit" in summary else "—")
    cols[2].metric("주문 수", f"{summary['order_count']:,}")
    cols[3].metric("고객 수", f"{summary['customer_count']:,}")


def show_monthly(df: pd.DataFrame) -> None:
    monthly = monthly_kpis(df)
    st.subheader("월별 매출")
    chart = monthly["sales"].copy()
    chart.index = chart.index.to_timestamp()
    st.line_chart(chart, y_label="매출")

    st.caption(f"최근 {RECENT_MONTHS}개월 — MoM: 전월 대비, YoY: 전년 동월 대비")
    recent = monthly.tail(RECENT_MONTHS).copy()
    recent.index = recent.index.astype(str)
    st.dataframe(
        recent.style.format(
            {
                "sales": "{:,.0f}",
                "profit": "{:,.0f}",
                "sales_mom": "{:+.1%}",
                "sales_yoy": "{:+.1%}",
            },
            na_rep="—",
        ),
        width="stretch",
    )


def show_categories(df: pd.DataFrame) -> None:
    st.subheader("카테고리별 매출")
    categories = category_kpis(df)
    left, right = st.columns(2)
    left.bar_chart(categories["sales"], horizontal=True, x_label="매출", y_label="")
    formats = {"sales": "{:,.0f}", "profit": "{:,.0f}", "profit_margin": "{:.1%}"}
    right.dataframe(
        categories.style.format({k: v for k, v in formats.items() if k in categories}),
        width="stretch",
    )


def show_report(df: pd.DataFrame, currency: str) -> None:
    st.subheader("AI 분석 보고서")
    payload = build_kpi_payload(df, currency)

    with st.expander("LLM에 보내는 데이터 보기"):
        st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")

    try:
        provider, model = current_model()
    except ValueError as e:
        st.error(str(e))
        return
    st.caption(f"모델: {provider} / {model} — 버튼을 누를 때마다 API 크레딧이 사용됩니다.")

    # 같은 데이터로 만든 보고서는 다시 호출하지 않고 재사용한다.
    key = hash(json.dumps(payload, sort_keys=True))
    if st.button("보고서 생성", type="primary"):
        with st.spinner("보고서를 작성하는 중..."):
            try:
                st.session_state[key] = generate_report(payload)
            except Exception as e:  # API 키 누락, 크레딧 부족 등을 화면에 보여준다
                st.error(f"보고서 생성 실패: {e}")
    if key in st.session_state:
        st.markdown(st.session_state[key])


def main() -> None:
    st.title("📊 AI Data Analyst")
    st.caption("CSV → Python 분석 → LLM → 분석 보고서")

    selected = select_dataset()
    if selected is None:
        return
    df, currency = selected

    st.caption(f"기간: {df['date'].min().date()} ~ {df['date'].max().date()} · {len(df):,}행")
    show_kpis(df, currency)
    show_monthly(df)
    show_categories(df)
    show_report(df, currency)


main()
