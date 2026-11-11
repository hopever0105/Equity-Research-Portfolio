"""일라이릴리(LLY) 밸류에이션 모델 — 2026-11-09 재조사. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/일라이릴리/model.py
원래 리포트: 2026-10-15 BUY $1,340(당시 10-14 종가 표기 $1,211.11). 기준일 2026-11-09(월) · 기준주가 11-09 미국 종가(yfinance).
자료: SEC 8-K·10-Q 3Q26(10-29) → sec_key_20261109.json, 피어(대형 제약·바이오 8개사, yfinance 11-09 종가 기준) → peers_20261109.json,
     미국채 10년 → tools/macro_2026-11-09.json. 애널리스트 목표가는 교차확인에만.
방법: 이익 = 매출 × 성과마진(매출 − 원가 − 연구개발 − 판관비) − 인수 IPR&D(정상 연 $3B) − 이자 → 세후.
     A. DCF(FCFF = 순이익 × 현금전환율 + 세후 이자, 2027~2036 + 영구성장 3%; 2036년 무렵 터제파타이드 특허 만료를 마진 하락으로 반영) 50%
     + B. 2027E EPS × 피어 선행 PER 중앙값 50%. 2026E = 회사 가이던스 중간값. 출력: results.json
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
ORIG = dict(date="2026-10-15", pxdate="2026-10-14", rating="BUY", tp=1340, px=1211.11, method="PER(2027E $48.29) + 증권사 목표가 종합")

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["pxdate"], "Close"])
HI_SINCE = float(px.loc[ORIG["pxdate"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["pxdate"]:ASOF, "Close"].idxmax().date())
PX_PRE, PX_EARN = float(px.loc["2026-10-28", "Close"]), float(px.loc["2026-10-29", "Close"])

A_, Q_, Y9, G, BB, P3 = K["annual"], K["quarterly"], K["ytd_9m26"], K["guidance_2026"]["20261029"], K["balance_20260930"], K["q3_26_press"]
SH_DIL = G["shares"]
DEBT = BB["debt_lt"] + BB["debt_current"]
NET_DEBT = DEBT - BB["cash"]
MCAP = PRICE * SH_DIL
EV = MCAP + NET_DEBT

mid = lambda x: float(np.mean(x))
REV26, PM26, TAX26, EPS26 = mid(G["revenue"]), mid(G["perf_margin"]), mid(G["tax"]), mid(G["eps"])
IPRD26_PS = Y9["ipr_d"] / SH_DIL                       # 9M 인수 IPR&D 주당(비과세라 세전=세후로 근사)
EPS26_UND = EPS26 + IPRD26_PS                          # IPR&D를 뺀 2026E 기초 EPS
INT = 1300                                             # 순이자비용(연, 3Q 316 × 4)
IPRD_NORM = 3000                                       # 매년 반복되는 사업개발 — 정상 인수 IPR&D 연 $3B(2025 9M $2.4B)
TAX = 0.19
SH_DECL = 0.005
FCF_CONV = {2027: 0.70, 2028: 0.75, 2029: 0.80}; CONV_LT = 0.85   # 제조설비 증설(텍사스·버지니아 등)로 설비투자가 큼 → 점진 회복

UST = MAC["ust10y"]["value"] / 100
BETA = beta_us("LLY", ASOF, 2)
ERP = 0.05
COE = UST + BETA["blume"] * ERP
KD = 0.050 * (1 - TAX)
WD = DEBT / (DEBT + MCAP)
WACC = COE * (1 - WD) + KD * WD
G_T = 0.03

PEERS = {t: v for t, v in P.items() if t != "LLY"}
FPE = {t: v["forwardPE"] for t, v in PEERS.items() if v.get("forwardPE")}
FPE_MED = float(np.median(list(FPE.values())))
MULT = {-1: float(np.percentile(list(FPE.values()), 25)), 0: FPE_MED, 1: float(np.percentile(list(FPE.values()), 75))}

# 성장: 터제파타이드 물량 증가 vs 가격 하락(3Q 가격 −15%), 경구 Foundayo·레타트루타이드(2027 BLA). 2034~36년 특허 만료 구간에 마진 하락.
SC = {"보수": dict(g27=0.12, g28=0.08, g_late0=0.06, pm=0.50, pm_lt=0.38, mult=-1),
      "기본": dict(g27=0.20, g28=0.14, g_late0=0.10, pm=0.52, pm_lt=0.42, mult=0),
      "낙관": dict(g27=0.27, g28=0.20, g_late0=0.13, pm=0.53, pm_lt=0.45, mult=1)}


def project(s):
    gs = [s["g27"], s["g28"]] + list(np.linspace(s["g_late0"], 0.0, 8))   # 2036년 성장 0%(특허 만료 시작)
    pms = [s["pm"]] * 6 + list(np.linspace(s["pm"], s["pm_lt"], 5)[1:])  # 2027~2032 유지, 2033~2036 하락
    rows = [dict(year=2026, rev=REV26, g=REV26 / A_["revenue"]["2025"] - 1, pm=PM26, eps=EPS26, eps_und=EPS26_UND, ni=EPS26 * SH_DIL)]
    rev = REV26
    for i, (g, pm) in enumerate(zip(gs, pms)):
        y = 2027 + i
        rev *= 1 + g
        pre = rev * pm - IPRD_NORM - INT
        ni = pre * (1 - TAX)
        sh = SH_DIL * (1 - SH_DECL) ** (i + 1)
        conv = FCF_CONV.get(y, CONV_LT)
        rows.append(dict(year=y, rev=rev, g=g, pm=pm, ni=ni, sh=sh, eps=ni / sh, fcff=ni * conv + INT * (1 - TAX)))
    return rows


def dcf(rows, wacc, g=G_T):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    q4 = (rows[0]["ni"] - Y9["net_income"]) * 0.7
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
    OUT[k] = dict(rows=rows, va=va, vb=vb, pv=pv, tv=tv, mult=MULT[s["mult"]], tp=0.5 * va + 0.5 * vb)
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -1))
UP = TP / PRICE - 1
RATING = rating_of(UP)

waccs = [WACC - 0.01, WACC, WACC + 0.01, WACC + 0.02]
pmlts = [0.38, 0.42, 0.45]
SENS = dict(wacc=waccs, pm=pmlts, v=[[0.5 * dcf(project(dict(SC["기본"], pm_lt=p)), w)[0] + 0.5 * Bs["vb"] for w in waccs] for p in pmlts])
g27s = [0.12, 0.20, 0.27]; pers = [MULT[-1], FPE_MED, MULT[1], 28.0]
SENS_B = dict(g=g27s, per=pers, v=[[project(dict(SC["기본"], g27=g))[1]["eps"] * p for p in pers] for g in g27s])
IMPL = None                                            # 현재가가 내포한 2029년 매출 성장률(A만, 2036년 0%로 수렴)
for gl in np.arange(0.10, 0.40, 0.0025):
    if dcf(project(dict(SC["기본"], g_late0=float(gl))), WACC)[0] >= PRICE:
        IMPL = float(gl); break

R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, orig=ORIG, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D,
         px_pre=PX_PRE, px_earn=PX_EARN, hi52=HI52, lo52=LO52, sh_dil=SH_DIL, debt=DEBT, net_debt=NET_DEBT, mcap=MCAP, ev=EV,
         rev26=REV26, pm26=PM26, eps26=EPS26, eps26_und=EPS26_UND, iprd26_ps=IPRD26_PS, int_=INT, iprd_norm=IPRD_NORM, tax=TAX, fcf_conv=FCF_CONV, conv_lt=CONV_LT,
         ust=UST, beta=BETA, erp=ERP, coe=COE, kd=KD, wd=WD, wacc=WACC, g_t=G_T,
         peers=PEERS, fpe=FPE, fpe_med=FPE_MED, mult=MULT, scen=OUT, scen_assump=SC, sens=SENS, sens_b=SENS_B, implied_g=IMPL,
         per26_now=PRICE / EPS26_UND, per27_now=PRICE / Bs["rows"][1]["eps"], key=K)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:.2f} (10-14 {PX_ORIG:.2f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:.2f} {HI_SINCE_D}) earn day {PX_EARN/PX_PRE-1:+.1%} mcap {MCAP:,.0f} net debt {NET_DEBT:,.0f}")
    print(f"2026E rev {REV26:,.0f} PM {PM26:.3f} EPS {EPS26:.2f} (IPR&D {IPRD26_PS:.2f}/sh → 기초 {EPS26_UND:.2f}) PER26 기초 {PRICE/EPS26_UND:.1f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} WACC {WACC:.4f} | peer fwdPE med {FPE_MED:.1f} {MULT}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"27E rev {r[1]['rev']:,.0f} EPS {r[1]['eps']:.2f} 28E {r[2]['eps']:.2f} 30E {r[4]['eps']:.2f} | A {v['va']:.0f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) B {v['vb']:.0f} ({v['mult']:.1f}x) TP {v['tp']:.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "PER27", round(PRICE / Bs["rows"][1]["eps"], 1), "implied g29", IMPL)
