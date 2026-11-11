"""엑슨모빌(XOM) 밸류에이션 모델 — 2026-11-09 재조사. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/엑슨모빌/model.py
원래 리포트: 2026-09-07 BUY $175(당시 표기 약 $160.94, 09-04 종가 $159.47). 기준일 2026-11-09(월) · 기준주가 11-09 미국 종가(yfinance).
자료: SEC 8-K·10-Q 3Q26(ExxonMobil Holdings, 2026-07-01 텍사스 이전) → sec_key_20261109.json, 피어(yfinance, 11-09 종가 기준) → peers_20261109.json,
     미국채 10년·브렌트 → tools/macro_2026-11-09.json·yfinance. 애널리스트 목표가는 교차확인에만.
방법: 부문별 조정이익 = f(브렌트, 정제마진)로 추정해 '정상 이익'을 만든다.
     A. DCF(FCFF = 조정이익 + 감가상각 − 설비투자, 2027~2036 + 영구성장 2%) 50% + B. 2027E 조정 EPS × 피어 선행 PER 중앙값 50%.
     2026년 정제마진(중동 정제설비 손실로 10년 범위 위)은 2028년까지 정상화된다고 본다. 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_us
from valuation.tools.report_kit import rating_of

K = json.loads((HERE / "sec_key_20261109.json").read_text(encoding="utf-8"))
P = json.loads((HERE / "peers_20261109.json").read_text(encoding="utf-8"))
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-09.json").read_text(encoding="utf-8"))
ASOF = "2026-11-09"
ORIG = dict(date="2026-09-07", pxdate="2026-09-04", rating="BUY", tp=175, px=160.94, method="증권사 컨센서스·목표가 종합")

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["pxdate"], "Close"])
HI_SINCE = float(px.loc[ORIG["pxdate"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["pxdate"]:ASOF, "Close"].idxmax().date())

brent = yf.download("BZ=F", start="2024-01-01", end="2026-11-10", progress=False, auto_adjust=False)["Close"].squeeze().dropna()
brent = brent[brent.index <= ASOF]
BRENT_NOW = float(brent.iloc[-1])
BRENT_25 = float(brent["2025"].mean())
BRENT_9M25 = float(brent["2025-01":"2025-09"].mean()); BRENT_9M26 = float(brent["2026-01":"2026-09"].mean())
BRENT_3Q26 = float(brent["2026-07":"2026-09"].mean()); BRENT_QTD = float(brent["2026-10":].mean())

A_, Y9, SEG, SQ, P3, BB = K["annual"], K["ytd_9m"], K["segments_adj_9m"], K["segments_adj_q"], K["q3_26_press"], K["balance_20260930"]
SH_OUT = K["shares_outstanding"]["2026-09-30"]
SH_DIL = K["diluted_shares_3q26"]
DEBT = BB["debt_current"] + BB["debt_lt"]
NET_DEBT = DEBT - BB["cash"]
MCAP = PRICE * SH_OUT
EV = MCAP + NET_DEBT

# ── 부문 이익 함수 (연간, 조정이익) ─────────────────────────────
# Upstream: 2025 9M 17,511(브렌트 9M 평균) → 연환산 기준값. 2026 9M 22,762(중동 물량 손실 포함)와의 차이로 브렌트 $1당 이익을 추정.
UP_BASE = SEG["2025"]["Upstream"] * 4 / 3
UP_SENS = (SEG["2026"]["Upstream"] - SEG["2025"]["Upstream"]) * 4 / 3 / (BRENT_9M26 - BRENT_9M25)   # 연간, 브렌트 $1당
VOL_G = 0.03                                             # 가이아나·퍼미안·Golden Pass 물량 증가(연), 중동 물량 회복 포함
EP_NORM = 6500                                           # Energy Products 정상 이익(2025 연환산 약 $5.3B + 구조적 원가절감·보몬트 증설)
CHEM_NORM, SPEC_NORM = 2500, 3400
CORP = SEG["2026"]["Corporate"] * 4 / 3                  # 약 −3.6B
TAX_INT = 0                                              # 조정이익은 세후·이자 후 — FCFF 계산 시 세후 이자(약 $0.5B)는 무시


def earnings(brent_, ep, year, chem=CHEM_NORM, spec=SPEC_NORM):
    up = (UP_BASE + UP_SENS * (brent_ - BRENT_9M25)) * (1 + VOL_G) ** (year - 2025)
    return dict(up=up, ep=ep, chem=chem, spec=spec, corp=CORP, total=up + ep + chem + spec + CORP)


# 2026E: 9M 조정이익 + 4Q (3Q 이익을 브렌트 하락만큼 낮추고, 정제마진은 3Q의 80%)
Q4_UP = SQ["3Q26"]["Upstream"] + UP_SENS / 4 * (BRENT_QTD - BRENT_3Q26)
Q4 = Q4_UP + SQ["3Q26"]["Energy Products"] * 0.8 + SQ["3Q26"]["Chemical Products"] + SQ["3Q26"]["Specialty Products"] + SQ["3Q26"]["Corporate"]
ADJ26 = Y9["2026"]["adj_earnings"] + Q4
EPS26 = Y9["2026"]["adj_eps"] + Q4 / SH_DIL

UST = MAC["ust10y"]["value"] / 100
BETA2 = beta_us("XOM", ASOF, 2)
BETA = beta_us("XOM", ASOF, 5)                           # 2년 베타(−0.04)는 유가 충격이 시장과 반대로 움직인 결과라 5년 Blume 사용
ERP = 0.05
COE = UST + BETA["blume"] * ERP
TAX = 0.25
KD = 0.045 * (1 - TAX)
WD = DEBT / (DEBT + MCAP)
WACC = COE * (1 - WD) + KD * WD
G_T = 0.02                                               # 에너지 전환을 감안해 미국 공통 3%보다 낮게
DA = {2027: 27000, 2028: 27500}; DA_G = 0.02
CAPEX = {2027: 28000, 2028: 28000}; CAPEX_G = 0.02       # 2026 9M 설비투자 20,175 → 연 약 $27~28B, 이후 감가상각과 비슷하게
SH_DECL = 0.03                                           # 2027 자사주 $20B ÷ 시총 약 $670B

PEERS = {t: v for t, v in P.items() if t != "XOM"}
FPE = {t: v["forwardPE"] for t, v in PEERS.items() if v.get("forwardPE")}
EVEB = {t: v["enterpriseToEbitda"] for t, v in PEERS.items() if v.get("enterpriseToEbitda")}
FPE_MED = float(np.median(list(FPE.values())))
EVEB_MED = float(np.median(list(EVEB.values())))
MULT = {-1: float(np.percentile(list(FPE.values()), 25)), 0: FPE_MED, 1: float(np.percentile(list(FPE.values()), 75))}

# 시나리오: 2027 브렌트·정제이익, 2028년 이후 정상 브렌트·정제이익
SC = {"보수": dict(b27=70, ep27=7000, b_lt=65, ep_lt=5000, mult=-1),
      "기본": dict(b27=82, ep27=11000, b_lt=75, ep_lt=EP_NORM, mult=0),
      "낙관": dict(b27=95, ep27=16000, b_lt=85, ep_lt=8500, mult=1)}


def project(s):
    rows = [dict(year=2026, brent=float(brent["2026"].mean()), adj=ADJ26, eps=EPS26)]
    for i, y in enumerate(range(2027, 2037)):
        if y == 2027:
            b_, ep = s["b27"], s["ep27"]
        elif y == 2028:
            b_, ep = (s["b27"] + s["b_lt"]) / 2, (s["ep27"] + s["ep_lt"]) / 2
        else:
            b_, ep = s["b_lt"], s["ep_lt"]
        e = earnings(b_, ep, min(y, 2030))               # 물량 증가는 2030년까지만
        da = DA.get(y, DA[2028] * (1 + DA_G) ** (y - 2028)); cx = CAPEX.get(y, CAPEX[2028] * (1 + CAPEX_G) ** (y - 2028))
        sh = SH_DIL * (1 - SH_DECL) ** (i + 1)
        rows.append(dict(year=y, brent=b_, **e, adj=e["total"], da=da, capex=cx, fcff=e["total"] + da - cx, sh=sh, eps=e["total"] / sh))
    return rows


def dcf(rows, wacc, g=G_T):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    pv = Q4 * 0.6 / (1 + wacc) ** (t0 / 2)               # 4Q26 잔여 FCF(이익 × 0.6, 1~3Q FCF/이익 비율 근사 보수화)
    for i, r in enumerate(rows[1:]):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + g) / (wacc - g) / (1 + wacc) ** (t0 + len(rows) - 1.5)
    return (pv + tv - NET_DEBT) / SH_DIL, pv, tv


OUT = {}
for k, s in SC.items():
    rows = project(s)
    va, pv, tv = dcf(rows, WACC)
    vb = rows[1]["eps"] * MULT[s["mult"]]
    OUT[k] = dict(rows=rows, va=va, vb=vb, pv=pv, tv=tv, mult=MULT[s["mult"]], tp=0.5 * va + 0.5 * vb)
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"]))
UP = TP / PRICE - 1
RATING = rating_of(UP)

# 민감도 1: 정상 브렌트 × WACC (목표주가, B 고정)
waccs = [WACC - 0.01, WACC, WACC + 0.01, UST + 1.0 * ERP]
blts = [65, 75, 85]
SENS = dict(wacc=waccs, b=blts, v=[[0.5 * dcf(project(dict(SC["기본"], b_lt=b_)), w)[0] + 0.5 * Bs["vb"] for w in waccs] for b_ in blts])
# 민감도 2: 2027 브렌트 × 2027 정제이익 (2027E EPS)
b27s = [70, 82, 95]; ep27s = [7000, 11000, 16000]
SENS_E = dict(b=b27s, ep=ep27s, v=[[project(dict(SC["기본"], b27=b_, ep27=e_))[1]["eps"] for e_ in ep27s] for b_ in b27s])
# 현재가가 내포한 정상 브렌트 (A만)
IMPL_B = None
for b_ in np.arange(60, 160, 0.5):
    if dcf(project(dict(SC["기본"], b_lt=float(b_))), WACC)[0] >= PRICE:
        IMPL_B = float(b_); break
NORM = earnings(75, EP_NORM, 2027)

R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, orig=ORIG, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D,
         hi52=HI52, lo52=LO52, sh_out=SH_OUT, sh_dil=SH_DIL, debt=DEBT, net_debt=NET_DEBT, mcap=MCAP, ev=EV,
         brent_now=BRENT_NOW, brent_25=BRENT_25, brent_9m25=BRENT_9M25, brent_9m26=BRENT_9M26, brent_3q26=BRENT_3Q26, brent_qtd=BRENT_QTD,
         up_base=UP_BASE, up_sens=UP_SENS, vol_g=VOL_G, ep_norm=EP_NORM, corp=CORP, q4=Q4, adj26=ADJ26, eps26=EPS26, norm=NORM,
         ust=UST, beta=BETA, beta2=BETA2, erp=ERP, coe=COE, kd=KD, wd=WD, wacc=WACC, g_t=G_T, sh_decl=SH_DECL,
         peers=PEERS, fpe=FPE, eveb=EVEB, fpe_med=FPE_MED, eveb_med=EVEB_MED, mult=MULT,
         scen=OUT, scen_assump=SC, sens=SENS, sens_e=SENS_E, implied_b=IMPL_B, per27_now=PRICE / Bs["rows"][1]["eps"], per26_now=PRICE / EPS26,
         div_yield=P3["q4_dividend"] * 4 / PRICE, key=K)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:.2f} (09-04 {PX_ORIG:.2f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:.2f} {HI_SINCE_D}) mcap {MCAP:,.0f} EV {EV:,.0f} net debt {NET_DEBT:,.0f}")
    print(f"brent now {BRENT_NOW:.1f} 2025 {BRENT_25:.1f} 9M25 {BRENT_9M25:.1f} 9M26 {BRENT_9M26:.1f} 3Q26 {BRENT_3Q26:.1f} QTD {BRENT_QTD:.1f} | UP base {UP_BASE:,.0f} sens/$ {UP_SENS:,.0f}")
    print(f"Q4 {Q4:,.0f} ADJ26 {ADJ26:,.0f} EPS26 {EPS26:.2f} PER26 {PRICE/EPS26:.1f} | norm(75,2027) {NORM['total']:,.0f}")
    print(f"beta2 {BETA2['blume']:.2f} beta5 {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} WACC {WACC:.4f} | peer fwdPE med {FPE_MED:.1f} {MULT} EV/EBITDA med {EVEB_MED:.1f}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"27E adj {r[1]['adj']:,.0f} EPS {r[1]['eps']:.2f} FCFF {r[1]['fcff']:,.0f} | 29E EPS {r[3]['eps']:.2f} | A {v['va']:.0f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) B {v['vb']:.0f} ({v['mult']:.1f}x) TP {v['tp']:.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "PER27", round(PRICE / Bs["rows"][1]["eps"], 1), "implied brent", IMPL_B)
