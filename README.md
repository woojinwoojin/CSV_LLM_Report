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

## 이번 주에 하지 않는 것
AWS, Docker, DB

## 완료 체크
- [ ] 예시 CSV 준비
- [ ] Pandas 기본 분석 스크립트
- [ ] LLM API 연결
- [ ] 분석 결과 → 보고서 생성

## 블로그 주제
LLM에게 CSV를 그대로 넘기지 않고 Python으로 먼저 분석해야 하는 이유
