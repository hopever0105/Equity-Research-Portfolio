<div align="center">

# 📊 Equity Research Portfolio

**"Top-down 리서치: 한국·미국 증시 투자 아이디어 발굴"**

`DCF` · `NAV` · `Multiples` · `R` · `Python`

</div>

---

## 🎯 Portfolio Overview

| 항목 | 내용 |
|---|---|
| 목적 | 한국·글로벌 증시 전 섹터 투자 아이디어 발굴 및 실전 검증 |
| 방법론 | 정량분석(DCF, NAV, Multiples) + 정성판단(산업 구조, 경쟁력) |
| 기간 | 2026.05 ~ 진행 중 |
| 데이터 | DART(OpenDART API), 한국은행 ECOS, FnGuide, FactSet, Bloomberg, KRX, SEC Filings, Yahoo Finance |

---

## 📁 Research Coverage

| 구분 | 완료 | 예정 |
|---|:---:|:---:|
| 🇰🇷 Korea Equities | 29 | 1 |
| 🌎 Global Equities | 9 | 1 |
| 🎯 Theme & Sector | 4 | 0 |
| 📊 ETF & Macro | 0 | 4 |
| **합계** | **42** | **6** |

### 🆕 최근 업데이트 — 공시 기반 독자 밸류에이션 (계산 코드 공개)

증권사 목표주가는 계산에 넣지 않고 DART 공시 · 한국은행 ECOS · 시세 DB로 직접 산출했습니다. 가정과 민감도는 리포트와 코드에 함께 있습니다.

| 기업 | 기준일 | 투자의견 · 목표주가 | 방법 | 리포트 · 코드 |
|---|---|---|---|---|
| 케이뱅크 (279570) | 2026.10.27 | SELL · 4,800원 (이익 추정 시나리오 3,900원) | 공모가 산식 단계별 재계산 → 초과자본 분리 적정 PBR + PBR–ROE 회귀, 2026E~2028E 이익 추정 · RIM | `01_Korea_Equities/케이뱅크_리서치리포트_2026.pdf` · `valuation_models/케이뱅크` |
| 현대자동차 (005380) | 2026.10.06 | SELL · 325,000원 | 본업 PER · PBR 50:50 + 보스턴다이내믹스 SOTP, 환율 민감도 | `01_Korea_Equities/현대자동차_리서치리포트_2026_개정판.pdf` |
| 한화생명 (088350) | 2026.10.01 | BUY · 7,900원 (RIM 시나리오 9,600원) | CSM 롤포워드로 보통주 ROE 추정 → 고든 적정 PBR + IFRS17 이후 자기 PBR 밴드 50:50, 금리–자본(ALM) 민감도. 이전판(05-12, 7,500원) 대비 수정 9건은 8장 개정 내역 | `01_Korea_Equities/한화생명_리서치리포트_2026_개정판.pdf` · `valuation_models/한화생명` |

### 🇰🇷 Korea Equities

✅ **완료 (29)**
영원무역 · 한화생명 · 맥쿼리인프라 · 대한항공 · 마키나락스 · 한미반도체 · 주성엔지니어링 · 원익IPS · 네이버 · 대한광통신 · 서진시스템 · 에스피지 · LS ELECTRIC · 두산에너빌리티 · OCI홀딩스 · 현대제철 · SK이터닉스 · 삼성물산 · 한화오션 · 현대자동차 · 삼성전기 · LIG디펜스에어로스페이스 · HMM · 현대로템 · 현대모비스 · HL만도 · SK오션플랜트 · 오리온 · 케이뱅크

🔲 **예정 (1)** 에이피알

### 🌎 Global Equities

✅ **완료 (9)**
팔란티어(PLTR) · 알파벳(GOOGL) · 캐터필러 · 루멘텀홀딩스 · GE버노바 · 엑슨모빌 · 일라이릴리 · 유나이티드헬스 · 록히드마틴

🔲 **예정 (1)** 월마트

### 🎯 Theme & Sector

✅ **완료 (4)** 양자컴퓨터 · 광통신 · 로봇 · 에너지

### 📊 ETF & Macro

🔲 **예정 (4)** 환율전략 · 채권전망 · 크립토 · 2027년 상반기 매크로 전망

---

## 🛠️ 기술 스택

| 구분 | 내용 |
|---|---|
| 언어 | R, Python, SQL |
| Valuation | DCF, NAV, RIM(잔여이익모델), PER/PBR/PSR Multiples, EV/EBITDA, SOTP, 적정 PBR((ROE−g)/(COE−g)) |
| Quantitative | NCAV, Graham Number, ROE Decomposition, DuPont Analysis |
| Statistical | 회귀분석(PBR–ROE 등), VIF, 상관관계 분석, 민감도 분석 |
| 시각화 | ggplot2, R Shiny, matplotlib |
| 데이터 | OpenDART API, 한국은행 ECOS, MySQL 시세 DB, FnGuide, Yahoo Finance API, Quandl |
| 코드 | `valuation_models/` — 모델(model.py) · 리포트 생성(make_full_report.py) · 공시 수집 도구(tools/) |

---

## 📌 주요 성과

- 💼 **실전 투자**: KOSPI 가치주·성장주 + 미국 원자재 ETF 포트폴리오 운용 중
- 🏆 **DB금융투자 투자대회**: 팀장, 데이터 분석, 퀀텀 (2026.06 ~ 08)
- 🎓 **고려대학교(안암, 서울) 통계학 심화전공 졸업**: 정량분석 역량
- 💻 **코딩**: R 기반 데이터 분석, Python 기반 퀀트 및 계량분석

| 자격증 | 취득 |
|---|---|
| 감정평가사 1차 합격 | 2024, 2026 |
| SQLD | 2026.06 |
| TOEIC 850 | 2026.07 |
| 금융투자분석사 | 2026.07 |
| 투자자산운용사 | 2026.09 |
| ADsP | 2026.08 |
| 재무위험관리사 | 2026.09 |
| 빅데이터분석기사 | 2026.09 ~ 10 |

---

## 💡 특징

1. **실전 투자 검증**: 직접 투자하며 분석 역량을 확인합니다.
2. **Sector-Agnostic**: 가치·성장·테마를 가리지 않는 Top-down 접근
3. **글로벌 커버리지**: 한국·미국·원자재·외환 다각화
4. **통계적 검증**: R 기반 정량분석, 회귀모델 활용
5. **실물자산 이해**: 감정평가사 1차 합격, 리츠·인프라 NAV 분석 강점

---

## 📧 Contact

이메일: hobeensong@gmail.com
GitHub: [github.com/hopever0105](https://github.com/hopever0105)

## 📜 License

허락 없는 복제 및 유포를 금지합니다.