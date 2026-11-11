"""록히드마틴(LMT) 밸류에이션 모델 — 2026-11-09 재조사. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/록히드마틴/model.py
원래 리포트: 2026-09-29 BUY $612(당시 09-28 종가 $518.10). 기준일 2026-11-09(월) · 기준주가 11-09 미국 종가(yfinance).
자료: SEC 8-K·10-Q 3Q26(10-22) → sec_key_20261109.json, 피어(yfinance, 11-09 종가 기준; 보잉은 적자 회복 중이라 제외) → peers_20261109.json,
     미국채 10년 → tools/macro_2026-11-09.json. 애널리스트 의견은 교차확인에만.
방법: A. DCF(FCFF = FCF + 세후 이자, 2027~2036 + 영구성장 3%) 50% + B. 2027E EPS × 피어(방산 5개사) 선행 PER 중앙값 50%.
     2026E = 회사 가이던스 중간값(10-22 상향). 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_us
from valuation.tools.report_kit import rating_of

K = json.loads((HERE / "sec_key_20261109.json").read_text(encoding="utf-8"))
P = json.loads((HERE / "peers_20261109.json").read_text(encoding="utf-8"))
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-09.json").read_text(encoding="utf-8"))
ASOF = "2026-11-09"
ORIG = dict(date="2026-09-29", pxdate="2026-09-28", rating="BUY", tp=612, px=518.10, method="증권사 컨센서스·목표가 종합 + 펀더멘털 개선분")

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["pxdate"], "Close"])
HI_SINCE = float(px.loc[ORIG["pxdate"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["pxdate"]:ASOF, "Close"].idxmax().date())
PX_PRE, PX_EARN = float(px.loc["2026-10-21", "Close"]), float(px.loc["2026-10-22", "Close"])

A_, Y9, G, BB = K["annual"], K["ytd_9m"], K["guidance_2026"]["current_20261022"], K["balance_20260927"]
SH_OUT = K["shares_outstanding"]["2026-10-19"]
SH_DIL = 231.5                                           # 2026 3Q 희석 가중평균 232, 2026 1~3Q 231~232
DEBT = BB["debt_lt"] + BB["debt_current"]
NET_DEBT = DEBT - BB["cash"]
MCAP = PRICE * SH_OUT
EV = MCAP + NET_DEBT
BACKLOG = K["q3_26_press"]["backlog"]

mid = lambda x: float(np.mean(x))
REV26, SEGOP26, EPS26, FCF26, CAPEX26 = mid(G["sales"]), mid(G["seg_op"]), mid(G["eps"]), mid(G["fcf"]), mid(G["capex"])
FAS = G["fas_cas"]
UNALLOC = (K["unallocated_9m26"]["intangible"] + K["unallocated_9m26"]["other"]) * 4 / 3   # 무형자산 상각·기타 (연 약 −$0.65B)
OP26 = SEGOP26 + FAS + UNALLOC
TAX = 0.17                                               # 2025~2026 실효세율 약 16~17%
NI26 = EPS26 * SH_DIL
NONOP = NI26 / (1 - TAX) - OP26                          # 영업외(이자·비영업 연금) — 가이던스 EPS에 맞춰 역산, 이후 고정
INT = 1100                                               # 이자비용(차입 $20.5B × 약 5.3%)
FCF_CONV = FCF26 / NI26                                  # 2026E FCF/순이익

UST = MAC["ust10y"]["value"] / 100
BETA = beta_us("LMT", ASOF, 2)
ERP = 0.05
COE = UST + BETA["blume"] * ERP
KD = 0.053 * (1 - TAX)
WD = DEBT / (DEBT + MCAP)
WACC = COE * (1 - WD) + KD * WD
G_T = 0.03
SH_DECL = 0.01                                           # 2026년 자사주 없음(1Q 0) → 배당 위주, 연 1% 감소 가정

PEERS = {t: v for t, v in P.items() if t not in ("LMT", "BA")}
FPE = {t: v["forwardPE"] for t, v in PEERS.items() if v.get("forwardPE")}
EVEB = {t: v["enterpriseToEbitda"] for t, v in PEERS.items() if v.get("enterpriseToEbitda")}
FPE_MED = float(np.median(list(FPE.values())))
EVEB_MED = float(np.median(list(EVEB.values())))
MULT = {-1: float(np.percentile(list(FPE.values()), 25)), 0: FPE_MED, 1: float(np.percentile(list(FPE.values()), 75))}

# 보수: F-35 Lot 20 협상 지연 손실(2027 −$1.0B 부문이익)·마진 정체 / 낙관: 미사일 증산이 마진을 끌어올림
SC = {"보수": dict(g27=0.03, g28=0.03, m27=0.095, m_lt=0.100, g_late0=0.03, conv=0.95, mult=-1),
      "기본": dict(g27=0.06, g28=0.05, m27=0.108, m_lt=0.110, g_late0=0.045, conv=1.00, mult=0),
      "낙관": dict(g27=0.08, g28=0.07, m27=0.112, m_lt=0.118, g_late0=0.055, conv=1.05, mult=1)}


def g_late(s):
    return list(np.linspace(s["g_late0"], 0.03, 8))


def project(s):
    rows = [dict(year=2026, rev=REV26, m=SEGOP26 / REV26, segop=SEGOP26, op=OP26, ni=NI26, eps=EPS26, fcff=FCF26 + INT * (1 - TAX))]
    rev = REV26
    gs = [s["g27"], s["g28"]] + g_late(s)
    ms = [s["m27"]] + list(np.linspace(s["m27"], s["m_lt"], 10)[1:])
    for i, (g, m) in enumerate(zip(gs, ms)):
        rev *= 1 + g
        segop = rev * m
        op = segop + FAS + UNALLOC
        ni = (op + NONOP) * (1 - TAX)
        sh = SH_DIL * (1 - SH_DECL) ** (i + 1)
        rows.append(dict(year=2027 + i, rev=rev, g=g, m=m, segop=segop, op=op, ni=ni, eps=ni / sh, fcff=ni * s["conv"] + INT * (1 - TAX)))
    return rows


def dcf(rows, wacc, g=G_T):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    q4 = (FCF26 - Y9["2026"]["fcf"])                     # 4Q26 잔여 FCF (가이던스 − 9M)
    pv = q4 / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows[1:]):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + g) / (wacc - g) / (1 + wacc) ** (t0 + len(rows) - 1.5)
    return (pv + tv - NET_DEBT) / SH_DIL, pv, tv


OUT = {}
for k, s in SC.items():
    rows = project(s)
    va, pv, tv = dcf(rows, WACC)
    vb = rows[1]["eps"] * MULT[s["mult"]]
    OUT[k] = dict(rows=rows, va=va, vb=vb, pv=pv, tv=tv, mult=MULT[s["mult"]], tp=0.5 * va + 0.5 * vb, g_late=g_late(s))
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -1))
UP = TP / PRICE - 1
RATING = rating_of(UP)

waccs = [WACC - 0.01, WACC, WACC + 0.01, WACC + 0.02]
gts = [0.02, 0.025, 0.03]
SENS = dict(wacc=waccs, g=gts, v=[[0.5 * dcf(project(SC["기본"]), w, g_)[0] + 0.5 * Bs["vb"] for w in waccs] for g_ in gts])
mls = [0.100, 0.110, 0.118]; pers = [MULT[-1], FPE_MED, MULT[1]]
SENS_B = dict(m=mls, per=pers, v=[[project(dict(SC["기본"], m27=m))[1]["eps"] * p for p in pers] for m in mls])
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, orig=ORIG, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D,
         px_pre=PX_PRE, px_earn=PX_EARN, hi52=HI52, lo52=LO52, sh_out=SH_OUT, sh_dil=SH_DIL, debt=DEBT, net_debt=NET_DEBT, mcap=MCAP, ev=EV, backlog=BACKLOG,
         rev26=REV26, segop26=SEGOP26, op26=OP26, eps26=EPS26, ni26=NI26, fcf26=FCF26, capex26=CAPEX26, fas=FAS, unalloc=UNALLOC, nonop=NONOP, int_=INT, fcf_conv=FCF_CONV,
         ust=UST, beta=BETA, erp=ERP, coe=COE, kd=KD, wd=WD, wacc=WACC, g_t=G_T, tax=TAX, sh_decl=SH_DECL,
         peers=PEERS, fpe=FPE, eveb=EVEB, fpe_med=FPE_MED, eveb_med=EVEB_MED, mult=MULT,
         scen=OUT, scen_assump=SC, sens=SENS, sens_b=SENS_B, per27_now=PRICE / Bs["rows"][1]["eps"], per26_now=PRICE / EPS26,
         fcf_yield=FCF26 / MCAP, ev_ebitda_lmt=P['LMT']['enterpriseToEbitda'], key=K)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:.2f} (09-28 {PX_ORIG:.2f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:.2f} {HI_SINCE_D}) earn day {PX_EARN/PX_PRE-1:+.1%} mcap {MCAP:,.0f} EV {EV:,.0f} net debt {NET_DEBT:,.0f}")
    print(f"2026E rev {REV26:,.0f} segOP {SEGOP26:,.0f} OP {OP26:,.0f} NI {NI26:,.0f} EPS {EPS26:.2f} FCF {FCF26:,.0f} conv {FCF_CONV:.2f} nonop {NONOP:,.0f} PER26 {PRICE/EPS26:.1f} FCF yld {FCF26/MCAP:.1%}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} WD {WD:.2f} WACC {WACC:.4f} | peer fwdPE med {FPE_MED:.1f} {MULT} EV/EBITDA med {EVEB_MED:.1f}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"27E rev {r[1]['rev']:,.0f} EPS {r[1]['eps']:.2f} FCFF {r[1]['fcff']:,.0f} | 28E EPS {r[2]['eps']:.2f} | A {v['va']:.0f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) B {v['vb']:.0f} ({v['mult']:.1f}x) TP {v['tp']:.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "PER27", round(PRICE / Bs["rows"][1]["eps"], 1))
