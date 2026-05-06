# 📊 Equity Research Portfolio

> **"데이터 기반 Bottom-up 리서치: 한국·미국 증시 투자 아이디어 발굴"**

---

## 🎯 Portfolio Overview

**목적**: 한국·글로벌 증시 전 섹터 투자 아이디어 발굴 및 실전 검증  
**방법론**: 정량분석(DCF, NAV, Multiples) + 정성판단(산업 구조, 경쟁력)  
**기간**: 2026.05 ~ 진행중  
**데이터**: FnGuide, FactSet, Bloomberg, KRX, SEC Filings, Yahoo Finance

---

## 📁 Research Coverage 

### 🇰🇷 Korea Equities

| 종목 | 섹터 | 핵심 논점 | 스타일 | 파일 |
|------|------|-----------|--------|------|
| 영원무역 | 의류제조 | NCAV 50% 할인, 베트남 공장 NAV 미반영 | Deep-Value | 
| 한화생명 | 보험 | 부동산·주식 포트폴리오 PBR 0.3배 저평가 | Asset-Value |
| 맥쿼리인프라 | 인프라펀드 | 배당수익률 6%+, 안정적 현금흐름 | Income |
| 대한항공 | 항공운송 | 아시아나 합병 시너지, 국제선 회복 | Event-Driven | 
| 농심 | 식품 | 안정적 브랜드, 저PER 방어주 | Defensive | 
| 카카오뱅크 | 핀테크 | 순이익 YoY 30% vs PER 15배 | GARP |
| 강원랜드 | 레저 | 카지노 독점, 고배당+저PBR | Monopoly-Value |
| 신한지주 | 은행 | ROE 10%+, PBR 0.4배, 배당 5% | 저PBR 금융주 | 
| 롯데리츠 | 리츠 | NAV 대비 20% 할인, 배당 6% | Real Estate |

### 🌎 Global Equities (5종)

| 종목 | 시장 | 섹터 | 핵심 논점 | 파일 |
|------|------|------|-----------|------|
| Alibaba (BABA) | NYSE | 이커머스 | 중국 규제 완화, 클라우드 분사 가치 |
| NVIDIA (NVDA) | NASDAQ | AI반도체 | AI 수요 vs 밸류에이션 과열 검증 |
| Netflix (NFLX) | NASDAQ | 스트리밍 | 광고 티어 성장, FCF 개선 | 
| Vale (VALE) | NYSE | 원자재 | 철광석 수요, 배당 8%+ | 
| Freeport (FCX) | NYSE | 원자재 | 구리 수요 vs 공급 부족, EV 수혜 |

### 🎯 Theme & Sector (3종)

| 주제 | 섹터 | 핵심 논점 | 파일 |
|------|------|-----------|------|
| 방산주 바스켓 | 방산 | 한화에어로·LIG넥스원 수출 모멘텀 | 
| AI 인프라 | 반도체 | SK하이닉스 HBM vs AMD·Broadcom | 
| 한국 은행주 | 금융 | 금리 인하기 은행주 밸류에이션 | 

### 📊 ETF & Macro (3종)

| 주제 | 자산군 | 핵심 논점 | 파일 |
|------|--------|-----------|------|
| 한국 ETF 전략 | 주식 ETF | KODEX 레버리지 vs 고배당 로테이션 |
| 채권·금·비트코인 | 대체자산 | 금리 환경별 안전자산 배분 전략 | 
| 환율 전략 | 외환 | 원화·엔화·위안화 vs 수출주 영향 | 

---

## 🛠️ 기술 스택

**언어**: R , Python , SQL  
**R 패키지**: quantmod, TTR, PerformanceAnalytics, tidyverse, ggplot2  
**분석 기법**:
- Valuation: DCF, NAV, PER/PBR/PSR Multiples, EV/EBITDA
- Quantitative: NCAV, Graham Number, ROE Decomposition, DuPont Analysis
- Statistical: 회귀분석, VIF, 상관관계 분석

**시각화**: ggplot2, R Shiny  
**데이터**: FnGuide, Yahoo Finance API, Quandl

---

## 📌 주요 성과

✅ **실전 투자**: KOSPI 가치주·성장주 + 미국 원자재 ETF 포트폴리오 운용 중  
✅ **DB금융투자 투자대회**: 팀장, 데이터 분석, 퀀텀 (2026.06~08)  
✅ **자격증**: 
- 감정평가사 1차 합격 (2024,2026)
- SQLD (2026.05)
- 금융투자분석사(2026.07)
- 투자자산운용사 (2026.08)
- ADsP (2026.08)
- KCIA (2026.09)
- CFA Level 1 (2026.11)
✅ **고려대학교(안암, 서울) 통계학 심화전공** 졸업: 정량분석 역량   
✅ **코딩**: R 기반 데이터 분석, Python 



## 💡 
1. **실전 투자 검증** → 직접 투자하며 분석 역량 확인  
2. **Sector-Agnostic** → 가치/성장/테마 불문 Bottom-up 접근  
3. **글로벌 커버리지** → 한국·미국·원자재·외환 다각화  
4. **통계적 검증** → R 기반 정량분석, 회귀모델 활용  
5. **실물자산 이해** → 감평 1차 합격, 리츠·인프라 NAV 분석 강점


## 📂 Repository 구조
Equity-Research-Portfolio/
│
├── README.md
│
├── 01_Korea_Equities/           (한국 종목 9종 - 5~7월)
│   ├── 영원무역_NCAV.pdf
│   ├── 한화생명_Asset_Value.pdf
│   ├── 맥쿼리인프라_Income.pdf
│   ├── 대한항공_Event_Driven.pdf
│   ├── 농심_Defensive.pdf
│   ├── 카카오뱅크_GARP.pdf
│   ├── 강원랜드_Monopoly.pdf
│   ├── 신한지주_Bank.pdf
│   └── 롯데리츠_REIT.pdf
│
├── 02_Global_Equities/          (미국·글로벌 5종 - 6~8월)
│   ├── Alibaba_China.pdf
│   ├── NVIDIA_AI.pdf
│   ├── Netflix_Streaming.pdf
│   ├── Vale_IronOre.pdf
│   └── Freeport_Copper.pdf
│
├── 03_Theme_Sector/             (테마·섹터 3종 - 7~8월)
│   ├── 방산주_Sector.pdf
│   ├── AI인프라_HBM.pdf
│   └── 은행주_Valuation.pdf
│
├── 04_ETF_Macro/                (ETF·매크로 3종 - 8~9월)
│   ├── 한국ETF_Strategy.pdf
│   ├── 채권금비트코인_Alternative.pdf
│   └── 환율전략_FX.pdf
│
├── notebooks/                   (R·Python 분석 코드)
│   ├── 01_ncav_screening.R
│   ├── 02_valuation_model.R
│   ├── dacon_ncav_dashboard.R
│   └── (추후 Python 추가)
│
└── data/
└── (원천 데이터 보관)



## 🚀 Quick Start

```bash
# Repository 클론
git clone https://github.com/your-username/NCAV-Deep-Value-Research.git

# 패키지 설치 
install.packages(c("quantmod","tidyverse","ggplot2"))
```

---

## 📧 Contact

**이메일**: arlo0105@naver.com, hobeensong@gmail.com  
GitHub: github.com/hovever0105

---

## 📜 License
허락없는 복제 및 유포 금지합니다. 


🔖 작업 로드맵
Phase 1: Deep-Value
 Repository 세팅
 영원무역 NCAV 분석
 한화생명 저PBR 보험주
 금호석유 극단 저평가 
 etc...

Phase 2: Growth 2종 + Deep-Value 2종
 카카오뱅크 GARP
 에코프로비엠 2차전지
 Intel Turnaround
 Alibaba 중국 회복
etc...

Phase 3: Theme 2종 + ETF 1종 (7~8월)
 방산주 섹터 분석
 AI 인프라 한미 비교
 한국 ETF 전략
etc...

## 📂 Repository 구조
