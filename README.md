# 1주차 — CSV → Python 분석 → LLM → 분석 보고서

## 목표
CSV 하나를 읽고 Pandas로 기본 분석을 한 뒤, 그 결과를 LLM에 넘겨
"데이터 분석가처럼 설명해주는" 자연어 보고서를 만든다.

## 흐름
```
CSV → Pandas → 기본 분석(매출, 성장률, 구매자 수, 평균 주문금액 등) → LLM → 자연어 보고서
```

## 예시 데이터 컬럼
`date`, `user_id`, `product`, `category`, `price`, `quantity`, `channel`

## 데이터
Kaggle `Superstore Dataset` — `data/Sample - Superstore.csv`
- 9,994행(상품 단위), 주문 5,009건, 고객 793명, 2014-01 ~ 2017-12
- 읽기: `encoding='cp1252'`, 날짜 형식 `%m/%d/%Y`

## 확정 KPI
**전체 요약**
- 총 매출 (`Sales` 합계), 총 이익 (`Profit` 합계)
- 주문 수 (`Order ID` 고유값), 고객 수 (`Customer ID` 고유값)
- 카테고리별 매출

**월별 추이**
- 월별 매출 / 이익 / 주문 수 / 고객 수
- 전월 대비 성장률 (MoM)

## 실행 방법
```powershell
# 1. 데이터: Kaggle "Superstore Dataset"에서 받아 data/Sample - Superstore.csv 로 저장 (git에는 포함 안 함)
# 2. 환경 준비
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env   # 그다음 .env에 API 키 입력

# 3. 실행
.\.venv\Scripts\python analysis.py   # KPI만 계산 (API 호출 없음)
.\.venv\Scripts\python report.py     # LLM 보고서 생성 (기본: OpenAI gpt-5.4-mini)
```

## 이번 주에 하지 않는 것
AWS, Docker, DB

## 완료 체크
- [ ] 예시 CSV 준비
- [ ] Pandas 기본 분석 스크립트
- [ ] LLM API 연결
- [ ] 분석 결과 → 보고서 생성

## 블로그 주제
LLM에게 CSV를 그대로 넘기지 않고 Python으로 먼저 분석해야 하는 이유
