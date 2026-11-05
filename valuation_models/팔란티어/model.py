"""팔란티어(PLTR) 밸류에이션 모델 — 2026-11-05 재조사. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/팔란티어/model.py
원래 리포트: 2026-08-11 HOLD $157. 이번 기준일 2026-11-05(한국시간) · 기준주가 2026-11-04 미국 종가(stock_db us_price).
자료: SEC 10-K FY2025, 10-Q 3Q26(11-03), 8-K 3Q26 보도자료(11-02) → sec_key_20261104.json, 피어 SEC XBRL → sec_peers_20261104.json,
      미국채 10년 → valuation/tools/macro_2026-11-05.json.
방법: A. DCF(FCF − 주식보상, 4Q26~2035 + 영구성장) 70% + B. 출구 배수법 30%:
      2030E EV를 ServiceNow·Palo Alto의 현재 EV/(FCF − SBC)로 계산해 할인. 증권사 목표주가·컨센서스는 쓰지 않음. 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_us
from valuation.tools.price import conn

K = json.loads((HERE / "sec_key_20261104.json").read_text(encoding="utf-8"))
P = json.loads((HERE / "sec_peers_20261104.json").read_text(encoding="utf-8"))
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-05.json").read_text(encoding="utf-8"))
ASOF, PXDATE = "2026-11-05", "2026-11-04"
ORIG = dict(date="2026-08-11", pxdate="2026-08-10", rating="HOLD", tp=157,
            method="DCF 30% · EV/매출 40배 40% · 컨센서스 30% (+13% 정성 조정)", wacc="10%", bull=190.6, bear=88.8,
            guide_rev=[8150, 8158], guide_fcf=[4500, 4700], ust=4.72)
px = pd.read_csv(HERE / "price_db.csv", parse_dates=["날짜"]).set_index("날짜")
PRICE = float(px.loc[PXDATE, "종가"])
PX_ORIG = float(px.loc[ORIG["pxdate"], "종가"])
CHG_SINCE = PRICE / PX_ORIG - 1
w52 = px[(px.index <= PXDATE) & (px.index > pd.Timestamp(PXDATE) - pd.Timedelta(days=365))]
HI52, LO52 = float(w52["고가"].max()), float(w52["저가"].min())
HI_SINCE = float(px.loc[ORIG["pxdate"]:PXDATE, "종가"].max()); HI_SINCE_D = str(px.loc[ORIG["pxdate"]:PXDATE, "종가"].idxmax().date())
B = K["balance_2026_09_30"]
SH_OUT = B["shares_outstanding"]
SH_DIL = K["quarterly"]["diluted_shares_wavg"]["3Q26"]
NET_CASH = B["cash"] + B["marketable_securities"] - B["debt"]
MCAP = PRICE * SH_OUT
EV = MCAP - NET_CASH
q = K["quarterly"]
TTM = K["ttm_3Q26"]
PER_TTM = PRICE / TTM["eps_diluted"]
PBR = MCAP / B["equity"]
G26 = K["press_release_3Q26"]["guide_FY26"]
REV26 = float(np.mean(G26["revenue"]))
ADJFCF26 = float(np.mean(G26["adj_fcf"]))
SBC_TTM = TTM["sbc"]
SBC26 = SBC_TTM * REV26 / TTM["revenue"]
M26 = (ADJFCF26 - SBC26) / REV26
REV_9M = q["revenue"]["1Q26"] + q["revenue"]["2Q26"] + q["revenue"]["3Q26"]
REV_4Q = REV26 - REV_9M

# ───────────────────────── 할인율
UST = MAC["ust10y"]["value"] / 100
BETA = beta_us("PLTR", PXDATE, 2)
ERP = 0.05
WACC = UST + BETA["blume"] * ERP
G_T = 0.03

# 2027 성장률: 4Q26 가이던스 연환산만으로 +24%, 분기 9% 성장이면 약 +55% → 기본 55%
GROWTH = [0.55, 0.40, 0.30, 0.25, 0.20, 0.17, 0.14, 0.12, 0.10]       # 2027~2035
RUNRATE_G = REV_4Q * 4 / REV26 - 1


def project(gmult=1.0, m_t=0.35):
    rows, rev = [], REV26
    ms = np.linspace(M26, m_t, len(GROWTH) + 1)[1:]
    for i, (g, m) in enumerate(zip(GROWTH, ms)):
        rev *= 1 + g * gmult
        rows.append(dict(year=2027 + i, g=g * gmult, rev=rev, m=float(m), fcf=rev * m))
    return rows


def dcf(rows, wacc, g=G_T):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365     # 0.15년
    cf26 = REV_4Q * M26                                                  # 4Q26 몫
    pv = cf26 / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows):
        pv += r["fcf"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcf"] * (1 + g) / (wacc - g) / (1 + wacc) ** (t0 + len(rows))
    return (pv + tv + NET_CASH) / SH_DIL, pv, tv


c = conn()
PEER = {}
for t, v in P["peers"].items():
    p0 = float(pd.read_sql("SELECT `종가` FROM us_price WHERE `티커`=%s AND `날짜`<=%s ORDER BY `날짜` DESC LIMIT 1", c, params=[t, PXDATE]).iloc[0, 0])
    mc = p0 * v["shares"] / 1e6
    nc = (v["cash"] + v["sti"] + v["lti"] - v["debt"]) / 1e6
    ev = mc - nc
    fcf = (v["cfo_ttm"] - v["capex_ttm"]) / 1e6; fs = fcf - v["sbc_ttm"] / 1e6; rev = v["rev_ttm"] / 1e6
    PEER[t] = dict(name=v["name"], price=p0, mcap=mc, ev=ev, rev=rev, g=v["g"], fcf_m=fcf / rev, fs_m=fs / rev,
                   ev_rev=ev / rev, ev_fs=ev / fs, r40=v["g"] + fcf / rev)
EXIT = float(np.mean([v["ev_fs"] for v in PEER.values()]))
PLTR_FCF_M = (TTM["cfo"] - TTM["capex"]) / TTM["revenue"]
PLTR_R40 = TTM["revenue"] / TTM["revenue_prev"] - 1 + PLTR_FCF_M


def exit_value(rows, wacc, mult=None, year=2030):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    pv = REV_4Q * M26 / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows):
        if r["year"] > year:
            break
        pv += r["fcf"] / (1 + wacc) ** (t0 + i + 0.5)
    r_end = [r for r in rows if r["year"] == year][0]
    n = t0 + (year - 2027) + 1
    return (pv + r_end["fcf"] * (mult or EXIT) / (1 + wacc) ** n + NET_CASH) / SH_DIL, r_end


SCN = {"보수": dict(gm=0.8, m_t=0.30), "기본": dict(gm=1.0, m_t=0.35), "낙관": dict(gm=1.2, m_t=0.40)}
OUT = {}
for k, s in SCN.items():
    rows = project(s["gm"], s["m_t"])
    va, pv, tv = dcf(rows, WACC)
    vb, r30 = exit_value(rows, WACC)
    OUT[k] = dict(rows=rows, va=va, vb=vb, pv=pv, tv=tv, tp=0.7 * va + 0.3 * vb, r30=r30)
TP = int(round(OUT["기본"]["tp"]))
UP = TP / PRICE - 1
RATING = "BUY" if UP >= .15 else ("HOLD" if UP >= -.05 else "SELL")

IMPL = None
for gm in np.arange(0.8, 3.0, 0.01):
    rr = project(gm, 0.35)
    if 0.7 * dcf(rr, WACC)[0] + 0.3 * exit_value(rr, WACC)[0] >= PRICE:
        IMPL = dict(gm=float(gm), cagr=float((rr[-1]["rev"] / REV26) ** (1 / len(rr)) - 1), rev2035=rr[-1]["rev"]); break
BASE_CAGR = float((OUT["기본"]["rows"][-1]["rev"] / REV26) ** (1 / 9) - 1)

waccs = [0.09, 0.10, 0.11, 0.12, WACC, 0.16]
mts = [0.30, 0.35, 0.40, 0.45]
SENS = [[0.7 * dcf(project(1.0, m), w)[0] + 0.3 * exit_value(project(1.0, m), w)[0] for w in waccs] for m in mts]
gms = [0.8, 1.0, 1.2, 1.5]
SENS_G = [[0.7 * dcf(project(g, 0.35), w)[0] + 0.3 * exit_value(project(g, 0.35), w)[0] for w in waccs] for g in gms]

R = dict(asof=ASOF, pxdate=PXDATE, orig=ORIG, px_orig=PX_ORIG, chg_since=CHG_SINCE, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D,
         price=PRICE, tp=TP, upside=UP, rating=RATING, hi52=HI52, lo52=LO52,
         sh_out=SH_OUT, sh_dil=SH_DIL, net_cash=NET_CASH, mcap=MCAP, ev=EV, ttm=TTM, per_ttm=PER_TTM, pbr=PBR,
         rev26=REV26, rev_4q=REV_4Q, runrate_g=RUNRATE_G, adjfcf26=ADJFCF26, sbc26=SBC26, m26=M26, sbc_ttm=SBC_TTM, ev_rev26=EV / REV26,
         ust=UST, beta=BETA, erp=ERP, wacc=WACC, g_t=G_T, growth=GROWTH, peers=PEER, exit=EXIT, pltr_r40=PLTR_R40, pltr_fcf_m=PLTR_FCF_M,
         scen={k: dict(tp=v["tp"], va=v["va"], vb=v["vb"], pv=v["pv"], tv=v["tv"], rows=v["rows"], r30=v["r30"], upside=v["tp"] / PRICE - 1)
               for k, v in OUT.items()}, scen_assump=SCN,
         implied=IMPL, base_cagr=BASE_CAGR, sens=dict(wacc=waccs, m_t=mts, v=SENS), sens_g=dict(wacc=waccs, gm=gms, v=SENS_G), key=K)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE} (08-10 {PX_ORIG:.2f}, {CHG_SINCE:+.1%}, high since {HI_SINCE:.2f} {HI_SINCE_D}) mcap {MCAP:,.0f} EV {EV:,.0f} EV/26 {EV/REV26:.1f} PER {PER_TTM:.0f} M26 {M26:.1%} 4Q {REV_4Q:,.0f} runrate g {RUNRATE_G:.1%}")
    print("beta", BETA, f"WACC {WACC:.2%}")
    for t, v in PEER.items():
        print(t, f"mcap {v['mcap']:,.0f} EV/rev {v['ev_rev']:.1f} EV/(FCF-SBC) {v['ev_fs']:.1f} g {v['g']:.1%} fcf {v['fcf_m']:.1%}")
    print("exit", round(EXIT, 1), "R40", round(PLTR_R40, 3))
    for k, v in OUT.items():
        print(k, "A", round(v["va"], 1), "B", round(v["vb"], 1), "TP", round(v["tp"], 1), f"TV {v['tv']/(v['pv']+v['tv']):.0%}", "2030 rev", round(v["r30"]["rev"]))
    print("TP", TP, f"{UP:+.1%}", RATING, "implied", IMPL, "base cagr", round(BASE_CAGR, 3))
