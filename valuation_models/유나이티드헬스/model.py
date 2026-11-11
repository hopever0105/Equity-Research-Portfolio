"""유나이티드헬스(UNH) 밸류에이션 모델 — 2026-11-09 재조사. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/유나이티드헬스/model.py
원래 리포트: 2026-10-15 BUY $435(당시 10-14 종가 $395.62). 기준일 2026-11-09(월) · 기준주가 11-09 미국 종가(yfinance).
자료: SEC 10-Q 3Q26(11-03)·8-K 3Q26(10-13) → sec_key_20261109.json, 피어(관리의료 6개사, yfinance 11-09 종가 기준) → peers_20261109.json,
     미국채 10년 → tools/macro_2026-11-09.json. 애널리스트 목표가는 교차확인에만.
방법: 보험사는 부채가 영업의 일부라 주주 기준으로 본다.
     A. DCF(FCFE = 조정 순이익 × 90%, 자기자본비용, 2027~2036 + 영구성장 3%) 50% + B. 2027E 조정 EPS × 피어 선행 PER 중앙값 50%.
     2026E = 회사 가이던스 하한(조정 EPS $20.50 이상). 출력: results.json
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
ORIG = dict(date="2026-10-15", pxdate="2026-10-14", rating="BUY", tp=435, px=395.64, method="PER(2027E $23.2) + 증권사 목표가 종합, 정성 조정 −2%")

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["pxdate"], "Close"])
HI_SINCE = float(px.loc[ORIG["pxdate"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["pxdate"]:ASOF, "Close"].idxmax().date())

A_, Q_, Y9, BB = K["annual"], K["quarterly"], K["ytd_9m26"], K["balance_20260930"]
SH_OUT = K["shares_outstanding"]["2026-10-30"]
SH_DIL = Q_["diluted_shares_wavg"]["3Q26"]
DEBT = BB["debt_lt"] + BB["debt_short"]
MCAP = PRICE * SH_OUT
EPS26 = K["guidance_2026"]["20261013"]["adj_eps_min"]
NI26 = EPS26 * SH_DIL

UST = MAC["ust10y"]["value"] / 100
BETA = beta_us("UNH", ASOF, 2)
ERP = 0.05
COE = UST + BETA["blume"] * ERP
G_T = 0.03
PAYOUT = 0.90                                            # FCFE/순이익: 영업현금은 순이익의 약 1.2배(3Q)지만 법정자본·인수 재투자를 빼 90%
SH_DECL = 0.01

PEERS = {t: v for t, v in P.items() if t != "UNH"}
FPE = {t: v["forwardPE"] for t, v in PEERS.items() if v.get("forwardPE")}
FPE_MED = float(np.median(list(FPE.values())))
MULT = {-1: float(np.percentile(list(FPE.values()), 25)), 0: FPE_MED, 1: float(np.percentile(list(FPE.values()), 75))}

# 회사 목표: 2027년부터 조정 EPS 연 13~16%. 기본은 상업보험 비용 추세·2027 별점 하락(2028 매출 영향)을 반영해 하한보다 낮게.
SC = {"보수": dict(g27=0.07, g28=0.04, g_late0=0.07, mult=-1),
      "기본": dict(g27=0.12, g28=0.09, g_late0=0.09, mult=0),
      "낙관": dict(g27=0.15, g28=0.14, g_late0=0.11, mult=1)}


def project(s):
    gs = [s["g27"], s["g28"]] + list(np.linspace(s["g_late0"], 0.03, 8))
    rows = [dict(year=2026, eps=EPS26, ni=NI26, g=EPS26 / A_["eps_diluted"]["2025"] - 1)]
    eps = EPS26
    for i, g in enumerate(gs):
        eps *= 1 + g
        sh = SH_DIL * (1 - SH_DECL) ** (i + 1)
        rows.append(dict(year=2027 + i, g=g, eps=eps, sh=sh, ni=eps * sh, fcfe=eps * sh * PAYOUT))
    return rows


def dcf(rows, coe, g=G_T):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    q4 = (NI26 - Y9["net_income"]) * PAYOUT
    pv = q4 / (1 + coe) ** (t0 / 2)
    for i, r in enumerate(rows[1:]):
        pv += r["fcfe"] / (1 + coe) ** (t0 + i + 0.5)
    tv = rows[-1]["fcfe"] * (1 + g) / (coe - g) / (1 + coe) ** (t0 + len(rows) - 1.5)
    return (pv + tv) / SH_DIL, pv, tv


OUT = {}
for k, s in SC.items():
    rows = project(s)
    va, pv, tv = dcf(rows, COE)
    vb = rows[1]["eps"] * MULT[s["mult"]]
    OUT[k] = dict(rows=rows, va=va, vb=vb, pv=pv, tv=tv, mult=MULT[s["mult"]], tp=0.5 * va + 0.5 * vb)
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -1))
UP = TP / PRICE - 1
RATING = rating_of(UP)

coes = [COE - 0.01, COE, COE + 0.01, COE + 0.02]
g27s = [0.07, 0.12, 0.15]
SENS = dict(coe=coes, g=g27s, v=[[0.5 * dcf(project(dict(SC["기본"], g27=g)), c)[0] + 0.5 * project(dict(SC["기본"], g27=g))[1]["eps"] * FPE_MED for c in coes] for g in g27s])
pers = [MULT[-1], FPE_MED, MULT[1], 17.0]
SENS_B = dict(g=g27s, per=pers, v=[[project(dict(SC["기본"], g27=g))[1]["eps"] * p for p in pers] for g in g27s])
IMPL = None                                              # 현재가가 내포한 자기자본비용 (A만)
for c in np.arange(COE, 0.15, 0.0005):
    if dcf(project(SC["기본"]), float(c))[0] <= PRICE:
        IMPL = float(c); break

R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, orig=ORIG, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D,
         hi52=HI52, lo52=LO52, sh_out=SH_OUT, sh_dil=SH_DIL, debt=DEBT, mcap=MCAP, eps26=EPS26, ni26=NI26,
         ust=UST, beta=BETA, erp=ERP, coe=COE, g_t=G_T, payout=PAYOUT, sh_decl=SH_DECL,
         peers=PEERS, fpe=FPE, fpe_med=FPE_MED, mult=MULT, scen=OUT, scen_assump=SC, sens=SENS, sens_b=SENS_B, implied_g=IMPL,
         per26_now=PRICE / EPS26, per27_now=PRICE / Bs["rows"][1]["eps"], div_yield=K["q3_26"]["dividend_q"] * 4 / PRICE, key=K)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:.2f} (10-14 {PX_ORIG:.2f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:.2f} {HI_SINCE_D}) mcap {MCAP:,.0f} PER26 {PRICE/EPS26:.1f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} | peer fwdPE med {FPE_MED:.1f} {MULT}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"27E EPS {r[1]['eps']:.2f} 28E {r[2]['eps']:.2f} | A {v['va']:.0f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) B {v['vb']:.0f} ({v['mult']:.1f}x) TP {v['tp']:.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "PER27", round(PRICE / Bs["rows"][1]["eps"], 1), "implied COE", IMPL)
