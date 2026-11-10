"""월마트(WMT) 밸류에이션 모델 — 신규, 기준일 2026-11-06. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/월마트/model.py
기준주가: 11-06 미국 종가 $125.52(yfinance). 회계연도 2~1월(FY27 = 2026-02~2027-01). 3Q FY27 실적(11월 중순)은 기준일 뒤라 쓰지 않음.
자료: SEC 10-K FY26, 10-Q 1·2Q FY27, 8-K 2Q FY27 보도자료·가이던스(08-20) → sec_key_20261106.json, 피어 배수(yfinance, 11-06 종가 기준) → peers_20261106.json,
     미국채 10년 → tools/macro_2026-11-06.json. 애널리스트 목표가(Bernstein·Morgan Stanley·Roth·Evercore·BofA)·FY28 EPS 컨센서스는 교차확인 표에만.
방법: A. 12개월 선행 PER = FY28E 조정 EPS × 목표 PER(자기 5년 선행 PER 평균과 코스트코의 중간) 50%
     + B. DCF(FCFF FY28~FY37 + 영구성장) 50%. 출력: results.json
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

K = json.loads((HERE / "sec_key_20261106.json").read_text(encoding="utf-8"))
P = json.loads((HERE / "peers_20261106.json").read_text(encoding="utf-8"))
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-06.json").read_text(encoding="utf-8"))
ASOF = "2026-11-06"

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
YTD = PRICE / float(px.loc[:"2025-12-31", "Close"].iloc[-1]) - 1
SH_OUT = K["shares_outstanding"]["2026-08-26"]
SH_DIL = K["quarterly"]["diluted_shares_wavg"]["2Q FY27"]
BAL = K["balance_20260731"]
DEBT = K["q2_fy27_press"]["total_debt"]
CASH = BAL["cash"]
LEASE = BAL["op_lease_nc"]
NCI = BAL["nci"]
NET_DEBT = DEBT - CASH
CLAIMS = NET_DEBT + LEASE + NCI                          # EV에서 주주가치로 갈 때 빼는 것
MCAP = PRICE * SH_OUT
EV = MCAP + CLAIMS

G = K["guidance_fy27_as_of_20260820"]
SALES26 = K["annual"]["net_sales_fy26"]; ADJOP26 = K["annual"]["adj_op_income_fy26"]; EPS26 = K["annual"]["adj_eps_fy26"]
EPS27 = float(np.mean(G["adj_eps"]))                     # $2.835
SALES27 = SALES26 * (1 + np.mean(G["net_sales_cc"]))
ADJOP27 = ADJOP26 * (1 + np.mean(G["adj_op_income_cc"]))
TOTREV27 = SALES27 * K["annual"]["revenue"]["FY26"] / SALES26   # 회원비 등 포함 총매출

UST = MAC["ust10y"]["value"] / 100
BETA = beta_us("WMT", "2026-11-05", 2)
ERP = 0.05
WACC = UST + BETA["blume"] * ERP
G_T = 0.03
TAX = 0.24

# 피어 선행 PER
PEERS = {t: v for t, v in P.items() if t != "WMT"}
FPE = {t: v["forwardPE"] for t, v in PEERS.items() if v.get("forwardPE")}
WMT_FPE_YF = P["WMT"]["forwardPE"]
OWN_FPE_5Y = [21.06, 22.76, 24.21, 36.96, 41.65]        # FY2022~FY2026 연도별 선행 PER (stockanalysis.com, 기준 시점 명시 없음 → 참고치)
OWN_AVG = float(np.mean(OWN_FPE_5Y))
COST_FPE = FPE["COST"]
PER_BASE = round((OWN_AVG + COST_FPE) / 2, 1)            # 자기 5년 평균과 코스트코의 중간
CONS = dict(fy28_eps=3.2255, fy27_eps=2.89, tp_mean=127.48, tp_median=130, n=43)

SC = {"보수": dict(op28=0.06, sh=-0.007, per=OWN_AVG, g=0.035, m_lt=0.048, capex_lt=0.036),
      "기본": dict(op28=0.09, sh=-0.010, per=PER_BASE, g=0.045, m_lt=0.054, capex_lt=0.033),
      "낙관": dict(op28=0.12, sh=-0.012, per=COST_FPE, g=0.055, m_lt=0.060, capex_lt=0.030)}
DA_PCT = 0.019                                           # 감가상각/매출 (FY25 수준 가정)


def eps28(s):
    """FY28E 조정 EPS = FY27E 가이던스 중간값 × (1 + 조정 영업이익 증가율) ÷ 주식수 변화 (이자·세율 FY27과 같다고 가정)."""
    return EPS27 * (1 + s["op28"]) / (1 + s["sh"])


def project(s):
    rows, rev = [], TOTREV27
    m0 = ADJOP27 / TOTREV27
    ms = np.linspace(m0, s["m_lt"], 11)[1:]
    cps = np.linspace(0.040, s["capex_lt"], 11)[1:]
    for i in range(10):                                   # FY28~FY37
        rev_prev = rev
        rev *= 1 + s["g"]
        ebit = rev * ms[i]
        fcff = ebit * (1 - TAX) + rev * DA_PCT - rev * cps[i]
        rows.append(dict(fy=2028 + i, rev=rev, m=float(ms[i]), ebit=ebit, capex=rev * cps[i], fcff=fcff))
    return rows


def dcf(rows, wacc):
    t0 = (pd.Timestamp("2027-01-31") - pd.Timestamp(ASOF)).days / 365      # FY27 남은 기간
    fcff27_rest = (ADJOP27 * (1 - TAX) + TOTREV27 * DA_PCT - TOTREV27 * 0.040) * t0
    pv = fcff27_rest / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + G_T) / (wacc - G_T) / (1 + wacc) ** (t0 + len(rows))
    return (pv + tv - CLAIMS) / SH_DIL, pv, tv


OUT = {}
for k, s in SC.items():
    e = eps28(s)
    va = e * s["per"]
    rows = project(s)
    vb, pv, tv = dcf(rows, WACC)
    OUT[k] = dict(eps28=e, per=s["per"], va=va, vb=vb, pv=pv, tv=tv, rows=rows, tp=(va + vb) / 2)
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"]))
UP = TP / PRICE - 1
RATING = rating_of(UP)

# 민감도: 목표 PER × FY28 EPS 성장(A), WACC × 장기 마진(B)
pers = [30, 33, PER_BASE, 39, 42]
gs = [0.06, 0.09, 0.12]
SENS_A = dict(per=pers, g=gs, v=[[EPS27 * (1 + g) / (1 - 0.01) * p for p in pers] for g in gs])
waccs = [WACC - 0.01, WACC - 0.005, WACC, WACC + 0.005]
mls = [0.048, 0.054, 0.060, 0.066]
SENS_B = dict(wacc=waccs, m=mls, v=[[dcf(project(dict(SC["기본"], m_lt=m)), w)[0] for w in waccs] for m in mls])
# 현재가가 내포한 영구성장률 (B만, 다른 가정 기본)
IMPL_G = None
for gt in np.arange(0.03, 0.075, 0.0005):
    G_SAVE = G_T
    G_T = float(gt)
    v = dcf(project(SC["기본"]), WACC)[0]
    G_T = G_SAVE
    if v >= PRICE:
        IMPL_G = float(gt); break

ANALYSTS = [("Bernstein", "11-03", "Buy", 142), ("Morgan Stanley", "11-02", "Buy", 125), ("Roth MKM", "10-29", "Buy", 138),
            ("Evercore ISI", "10-20", "Buy", 130), ("BofA", "10-19", "Buy", 126)]
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, hi52=HI52, lo52=LO52, ytd=YTD, sh_out=SH_OUT, sh_dil=SH_DIL, debt=DEBT, cash=CASH,
         lease=LEASE, nci=NCI, net_debt=NET_DEBT, claims=CLAIMS, mcap=MCAP, ev=EV, sales26=SALES26, adjop26=ADJOP26, eps26=EPS26, eps27=EPS27,
         sales27=SALES27, adjop27=ADJOP27, totrev27=TOTREV27, guide=G, ust=UST, beta=BETA, erp=ERP, wacc=WACC, g_t=G_T, tax=TAX, da_pct=DA_PCT,
         peers=PEERS, fpe=FPE, wmt_fpe_yf=WMT_FPE_YF, own_fpe_5y=OWN_FPE_5Y, own_avg=OWN_AVG, cost_fpe=COST_FPE, per_base=PER_BASE, cons=CONS,
         scen=OUT, scen_assump=SC, sens_a=SENS_A, sens_b=SENS_B, implied_g=IMPL_G, analysts=ANALYSTS, key=K,
         per27_now=PRICE / EPS27, per28_now=PRICE / Bs["eps28"], ev_ebit27=EV / ADJOP27)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:.2f} YTD {YTD:+.1%} 52w {HI52:.2f}/{LO52:.2f} mcap {MCAP:,.0f} EV {EV:,.0f} (net debt {NET_DEBT:,.0f} lease {LEASE:,.0f} NCI {NCI:,.0f})")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} WACC {WACC:.4f} EPS27 {EPS27:.3f} PER27 {PRICE/EPS27:.1f} adjOP27 {ADJOP27:,.0f} EV/EBIT27 {EV/ADJOP27:.1f}")
    print(f"own 5y avg fwd PE {OWN_AVG:.1f} COST {COST_FPE:.1f} → base PER {PER_BASE}  peers {FPE}")
    for k, v in OUT.items():
        print(k, f"EPS28 {v['eps28']:.3f} × {v['per']:.1f} = A {v['va']:.1f} | B {v['vb']:.1f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) TP {v['tp']:.1f} {v['upside']:+.1%}  FY37 m {v['rows'][-1]['m']:.3f}")
    print("TP", TP, RATING, f"{UP:+.1%}", "implied g", IMPL_G)
