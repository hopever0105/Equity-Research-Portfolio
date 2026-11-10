"""네이버(035420) 밸류에이션 모델 — 2026-11-06 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/네이버/model.py
원래 리포트: 2026-08-13 BUY 270,000원(당시 213,000원). 기준일 2026-11-06(금) · 기준주가 11-06 종가 188,600원
  (네이버 기반 FinanceDataReader. stock_db 11-06 값 187,300원은 장중 수집값이라 쓰지 않음).
자료: DART 연결재무제표(2021~2Q26) → fs_summary_2026-11-06.csv, dart_fs_raw.csv(차입금), 2026 반기보고서(지분율: 네이버파이낸셜 89.21%,
     WEBTOON Entertainment 연결 59.23%, A Holdings 50%), 주식총수·자기주식(반기보고서), 엔비디아 유상증자 확정(11-03)·납입(11-06),
     채무보증(10-27, 브룩필드 AI 팩토리), 두나무 주식교환 일정 정정(10-07). LY 지분: LY Corporation 2026-06-30 공시(03-31 기준 A Holdings 계열 의결권 62.4%).
     시세: WBTN·4689.T·JPYKRW(yfinance, 11-06). 증권사 리포트는 가정 교차확인에만: LS(10-28), 메리츠(10-08), 유진(10-07).
방법: A. SOTP(본업 2027E 순영업이익 × 목표 PER + 라인야후 간접지분 시가 × (1−30%) + 웹툰 지분 시가 × (1−30%) + 순현금) 50%
     + B. 2027E 지배 EPS × 자기 PER 밴드 중앙값 50%. AI 팩토리·두나무 교환은 목표가에 넣지 않고 낙관 시나리오로만. 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr
from valuation.tools.report_kit import rating_of
from valuation.tools.simple_val import hist, band

ASOF = "2026-11-06"
ORIG = dict(date="2026-08-13", pxdate="2026-08-12", rating="BUY", tp=270000, px=213000, method="PER·시나리오 종합(증권사 컨센서스 참고)")
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-06.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07

# ───────────────────────── 시세·주식수
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["pxdate"], "Close"])
SH_ISSUED_0626, TREASURY = 156_944_242, 7_139_909      # 2026 반기보고서
NEW_SH = 6_558_435                                      # 엔비디아 제3자배정 (11-06 납입, 204,500원)
NEW_CASH = 13_411.99957500                              # 억원
SH = SH_ISSUED_0626 - TREASURY + NEW_SH                 # 156,362,768
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적
FY, Q = hist("네이버", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
H1 = {k: Q["20261Q"][k] + Q["20262Q"][k] for k in ("매출", "영업이익", "지배순이익")}
H1P = {k: Q["20251Q"][k] + Q["20252Q"][k] for k in ("매출", "영업이익", "지배순이익")}
# 순현금 (2026-06말, 리스부채 제외) + 증자
CASH = 63_843.70 + 20_170.73                             # 현금성자산 + 단기금융상품
DEBT = 22.21 + 3_028.12 + 7_643.98 + 17_180.26 + 11_071.36  # 유동성장기차입금 + 유동성사채 + 단기차입금 + 사채 + 장기차입금
NET_CASH = CASH - DEBT + NEW_CASH
EQ_2Q26 = Q["20262Q"]["지배자본"]

# 지분 가치 (11-06 시세)
FX_USD = MAC["usdkrw"]["value"]
JPYKRW = 8.83                                           # yfinance JPYKRW=X 11-06 종가(아래 스크립트 확인값으로 덮어씀)
try:
    import yfinance as yf
    s = yf.download("JPYKRW=X", start="2026-10-30", end="2026-11-07", progress=False, auto_adjust=False)["Close"].squeeze().dropna()
    JPYKRW = float(s.iloc[-1])
except Exception:
    pass
WBTN = dict(px=9.67, sh=135_711_070, stake=0.5923)       # WEBTOON Entertainment, 연결 지분율(반기보고서)
LY = dict(px=541.0, sh=6_888_742_311, a_stake=0.624, naver_in_a=0.50)
WBTN["mcap"] = WBTN["px"] * WBTN["sh"] * FX_USD / 1e8
LY["mcap"] = LY["px"] * LY["sh"] * JPYKRW / 1e8
LY["look"] = LY["a_stake"] * LY["naver_in_a"]            # 31.2%
A_BOOK = 149_292.76                                      # A Holdings 장부가(반기보고서, 억원)
HOLD_DISC = 0.30

# ───────────────────────── 할인율
BETA = beta_kr("035420", ASOF, 3)
COE = RF + BETA["blume"] * MRP
TAX = 0.25

# ───────────────────────── 추정 (2026E = 1H 실제 + 2H 추정)
SC = {"보수": dict(r2h=6.95e4, m2h=0.135, g27=0.11, m27=0.145, g28=0.09, m28=0.150, eqm=5000, per=-1, ai=0),
      "기본": dict(r2h=7.14e4, m2h=0.145, g27=0.15, m27=0.155, g28=0.12, m28=0.165, eqm=6000, per=0, ai=0),
      "낙관": dict(r2h=7.30e4, m2h=0.150, g27=0.17, m27=0.165, g28=0.15, m28=0.180, eqm=7000, per=1, ai=1)}
FIN = 1000                                               # 금융손익(이자 등) 연 1,000억 (2025 1,990억, 2026E 차입 증가)
NCI = 500                                                # 비지배 몫


def forecast(s):
    rev26 = H1["매출"] + s["r2h"]; op26 = H1["영업이익"] + s["r2h"] * s["m2h"]
    rows = [dict(year=2026, rev=rev26, op=op26)]
    rev27 = rev26 * (1 + s["g27"]); rows.append(dict(year=2027, rev=rev27, op=rev27 * s["m27"]))
    rev28 = rev27 * (1 + s["g28"]); rows.append(dict(year=2028, rev=rev28, op=rev28 * s["m28"]))
    for r in rows:
        r["opm"] = r["op"] / r["rev"]
        r["core_ni"] = (r["op"] + FIN) * (1 - TAX)       # 본업 순이익(지분법 제외)
        r["ni"] = r["core_ni"] + s["eqm"] - NCI          # 지배순이익 = 본업 + 지분법(라인야후 등) − 비지배
        r["eps"] = r["ni"] * 1e8 / SH
    rows[0]["ni"] = H1["지배순이익"] + (s["r2h"] * s["m2h"] + FIN / 2) * (1 - TAX) + s["eqm"] / 2 - NCI / 2
    rows[0]["eps"] = rows[0]["ni"] * 1e8 / SH
    return rows


# ───────────────────────── PER 밴드 (최근 4분기 지배 EPS, 월말, 2021-11~)
SH_HIST = SH_ISSUED_0626 - TREASURY
BAND = band(px["Close"].astype(float), Q, SH_HIST, ASOF, start="2021-11-30", kind="per")
bs = pd.Series(BAND["series"]); bs.index = pd.to_datetime(bs.index)
BAND["median"] = float(bs.median()); BAND["q25"] = float(bs.quantile(.25)); BAND["q75"] = float(bs.quantile(.75))
b24 = bs[bs.index >= "2024-01-31"]                       # 금리 상승기 이후 3년: 2021~2022년 고평가 구간 제외
BAND["median24"] = float(b24.median()); BAND["q25_24"] = float(b24.quantile(.25)); BAND["q75_24"] = float(b24.quantile(.75)); BAND["n24"] = int(len(b24))
G_J = 0.03
ROE27 = None                                            # 아래에서 기본 시나리오로 계산
PER_MAP = {-1: None, 0: BAND["median24"], 1: 20.0}      # 보수 = 적정 PER(고든), 낙관 = 중앙값과 상위 25% 사이
CORE_PER = {-1: 13.0, 0: 15.0, 1: 17.0}                  # 본업 PER: 지분법·현금을 따로 더하므로 밴드보다 낮게

# AI 팩토리 옵션 (낙관만): 200MW, MW당 연 EBITDA 확인 불가 → 엔비디아 신주 인수가(204,500원)와 현재가 차이는 쓰지 않고,
# 회사 계획 1단계 55MW가 2027년에 가동되어 투입 자본(엔비디아 납입액)만큼의 가치를 만든다고 가정 = 증자 자금 1.34조를 한 번 더 인정
AI_OPTION = NEW_CASH

_r = forecast(SC["기본"])[1]
EQ_START = EQ_2Q26 + NEW_CASH
ROE27 = _r["ni"] / (EQ_START + _r["ni"] / 2)
PER_J = (1 - G_J / ROE27) / (COE - G_J)
PER_MAP[-1] = PER_J

OUT = {}
for k, s in SC.items():
    rows = forecast(s)
    r27 = rows[1]
    core = r27["core_ni"] * CORE_PER[s["per"]]
    ly = LY["mcap"] * LY["look"] * (1 - HOLD_DISC)
    wb = WBTN["mcap"] * WBTN["stake"] * (1 - HOLD_DISC)
    ai = AI_OPTION if s["ai"] else 0
    sotp = core + ly + wb + NET_CASH + ai
    va = sotp * 1e8 / SH
    per = PER_MAP[s["per"]]
    vb = r27["eps"] * per
    OUT[k] = dict(rows=rows, core=core, core_per=CORE_PER[s["per"]], ly=ly, wb=wb, net_cash=NET_CASH, ai=ai, sotp=sotp, va=va, per=per, vb=vb,
                  tp=(va + vb) / 2)
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -3))
UP = TP / PRICE - 1
RATING = rating_of(UP)

# 민감도: 2027 영업이익률 × 본업 PER (A), 2027 EPS 성장 × PER 밴드 (B 대신 목표가 전체)
m_list = [0.135, 0.145, 0.155, 0.165, 0.175]
p_list = [12, 15, 18, 21]
SENS = dict(m=m_list, p=p_list, v=[])
for m in m_list:
    rr = forecast(dict(SC["기본"], m27=m)); r27 = rr[1]
    row = []
    for p in p_list:
        va_ = (r27["core_ni"] * p + Bs["ly"] + Bs["wb"] + NET_CASH) * 1e8 / SH
        row.append((va_ + r27["eps"] * Bs["per"]) / 2)
    SENS["v"].append(row)

TTM_NI = Q["20253Q"]["지배순이익"] + Q["20254Q"]["지배순이익"] + Q["20261Q"]["지배순이익"] + Q["20262Q"]["지배순이익"]
REFS = [("LS증권", "2026-10-28", "Buy", 293000, 16257, 27220, 28950),
        ("메리츠증권", "2026-10-08", "Buy", 330000, 16362, 25825, 23240),
        ("유진투자증권", "2026-10-07", "BUY", 320000, 15658, 24270, 18880)]   # (2027E 매출, 영업이익, 순이익) 억원
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, sh_issued=SH_ISSUED_0626, treasury=TREASURY, new_sh=NEW_SH,
         new_cash=NEW_CASH, hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], ni=FY[y]["지배순이익"], eq=FY[y]["지배자본"]) for y in YRS},
         q={k: dict(rev=Q[k]["매출"], op=Q[k]["영업이익"], ni=Q[k]["지배순이익"]) for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q")},
         h1=H1, h1p=H1P, cash=CASH, debt=DEBT, net_cash=NET_CASH, eq_2q26=EQ_2Q26, wbtn=WBTN, ly=LY, a_book=A_BOOK, jpykrw=JPYKRW, fx_usd=FX_USD,
         hold_disc=HOLD_DISC, rf=RF, mrp=MRP, beta=BETA, coe=COE, tax=TAX, fin=FIN, nci=NCI, band=BAND, core_per=CORE_PER,
         roe27=ROE27, per_j=PER_J, g_j=G_J,
         scen=OUT, scen_assump=SC, sens=SENS, ttm_ni=TTM_NI, per_ttm=PRICE * SH_HIST / 1e8 / TTM_NI, pbr=MCAP / (EQ_2Q26 + NEW_CASH),
         per_27_now=PRICE / Bs["rows"][1]["eps"], refs=REFS)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} (08-12 {PX_ORIG:,.0f} {PRICE/PX_ORIG-1:+.1%}) 주식 {SH:,} 시총 {MCAP:,.0f}억 52주 {HI52:,.0f}/{LO52:,.0f}")
    print(f"순현금 {NET_CASH:,.0f} (현금 {CASH:,.0f} 차입 {DEBT:,.0f} 증자 {NEW_CASH:,.0f}) JPYKRW {JPYKRW:.3f} LY시총 {LY['mcap']:,.0f}억 웹툰시총 {WBTN['mcap']:,.0f}억")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} PER밴드 평균 {BAND['mean']:.1f} 중앙 {BAND['median']:.1f} q25 {BAND['q25']:.1f} q75 {BAND['q75']:.1f} 현재 {BAND['now']:.1f} TTM PER {R['per_ttm']:.1f}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"26E {r[0]['rev']:,.0f}/{r[0]['op']:,.0f}/{r[0]['ni']:,.0f} 27E {r[1]['rev']:,.0f}/{r[1]['op']:,.0f}/{r[1]['ni']:,.0f} EPS27 {r[1]['eps']:,.0f}",
              f"SOTP 본업 {v['core']:,.0f} LY {v['ly']:,.0f} 웹툰 {v['wb']:,.0f} AI {v['ai']:,.0f} → A {v['va']:,.0f} | B {v['vb']:,.0f} (PER {v['per']:.1f}) TP {v['tp']:,.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "현재가/27E EPS", round(PRICE / Bs["rows"][1]["eps"], 1))
