"""루멘텀홀딩스(LITE) 밸류에이션 모델 — 2026-11-05 재조사. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/루멘텀홀딩스/model.py
원래 리포트: 2026-08-20 BUY $1,040. 이번 기준일 2026-11-05(한국시간) · 기준주가 2026-11-04 미국 종가(stock_db us_price).
자료: SEC 10-K FY2026, 10-Q·8-K 1Q FY27(11-02·03), 8-K 마벨 합병계약(11-02) → sec_key_20261104.json, 피어 SEC XBRL → sec_peers_20261104.json.
방법: 1) 단독 가치 = A. DCF(FCF − 주식보상, FY2027~FY2036 + 영구성장) 50% + B. FY2029E 매출 × 피어 현재 EV/매출 중앙값 50%
      2) 합병 가치 = 마벨 주식 4.5주 × 마벨 11-04 종가 (고정 교환비율, 전액 주식)
      목표주가 = 완료 확률 × 합병 가치 + (1 − 완료 확률) × 단독 가치. 증권사 목표주가·컨센서스는 쓰지 않음. 출력: results.json
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
ORIG = dict(date="2026-08-20", pxdate="2026-08-19", rating="BUY", tp=1040,
            method="증권사 목표가 컨센서스 40% · 최근 5개사 35% · 참고치 $700 25% (+2% 정성 조정)",
            earn="FY27E 매출 $5.3B(연환산), EPS $16~17(범위)", bull=1280, bear=600, ust=4.65)
px = pd.read_csv(HERE / "price_db.csv", parse_dates=["날짜"]).set_index("날짜")
PRICE = float(px.loc[PXDATE, "종가"])
PX_ORIG = float(px.loc[ORIG["pxdate"], "종가"])
CHG_SINCE = PRICE / PX_ORIG - 1
PX_1028 = float(px.loc["2026-10-28", "종가"])
w52 = px[(px.index <= PXDATE) & (px.index > pd.Timestamp(PXDATE) - pd.Timedelta(days=365))]
HI52, LO52 = float(w52["고가"].max()), float(w52["저가"].min())
B = K["balance_2026_09_26"]
SH_BASIC = B["shares_cover_2026-10-28"]
SH_DIL = B["diluted_shares_nongaap_1Q"]                               # 100.9 (전환사채·NVIDIA 우선주 포함)
CASH = B["cash"] + B["short_term_investments"]                        # 1,979.6
CONV = B["debt_current"] + B["debt_noncurrent"]                       # 1,399.6 (희석 주식에 포함, 부채에서 빼지 않음)
MCAP_DIL = PRICE * SH_DIL
EV = MCAP_DIL - CASH
A = K["annual"]; QQ = K["quarterly"]; Q1 = QQ["1Q FY27"]
REV26 = A["revenue"]["FY2026"]
GUIDE = K["guide_2Q_FY27"]

# ───────────────────────── FY2027E 분기: 1Q 실제, 2Q 가이던스 중간, 3Q·4Q +8%
QG = 0.08
QS = [QQ["revenue"]["1Q FY27"], float(np.mean(GUIDE["revenue"]))]
QS += [QS[-1] * (1 + QG), QS[-1] * (1 + QG) ** 2]
REV27 = sum(QS)
OPM27 = float(np.mean([QQ["nongaap_op_margin"]["1Q FY27"], np.mean(GUIDE["nongaap_op_margin"]), np.mean(GUIDE["nongaap_op_margin"]), np.mean(GUIDE["nongaap_op_margin"])]))
TAX_NG = 0.15
EPS27 = REV27 * OPM27 * (1 - TAX_NG) / SH_DIL
TTM_REV = sum(QQ["revenue"][k] for k in ("2Q FY26", "3Q FY26", "4Q FY26", "1Q FY27"))

UST = MAC["ust10y"]["value"] / 100
BETA = beta_us("LITE", PXDATE, 2)
ERP = 0.05
WACC = UST + BETA["blume"] * ERP
G_T = 0.03
REV28 = 9000                                                           # FY27 4Q 연환산 $7.5B + 대형 NPO/CPO 수주(구매 약정 $5B 초과)
TAIL = [0.20, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04]               # FY2029~FY2036


def project(rev28=REV28, m_t=0.24, m27=0.20, m28=0.26, gmult=1.0):
    revs = [REV27, rev28]
    for g in TAIL:
        revs.append(revs[-1] * (1 + g * gmult))
    ms = [m27, m28] + list(np.linspace(m28, m_t, len(TAIL) + 1)[1:])
    return [dict(fy=2027 + i, rev=r, m=float(m), fcf=r * m, g=(r / (REV26 if i == 0 else revs[i - 1]) - 1)) for i, (r, m) in enumerate(zip(revs, ms))]


def dcf(rows, wacc, g=G_T):
    t0 = (pd.Timestamp("2027-06-30") - pd.Timestamp(ASOF)).days / 365    # FY27 말까지 0.65년
    fy27_left = 1 - QS[0] / REV27                                       # 1Q 지난 몫 제외
    pv = rows[0]["fcf"] * fy27_left / (1 + wacc) ** (t0 / 2)
    pv += sum(r["fcf"] / (1 + wacc) ** (t0 + i - 0.5) for i, r in enumerate(rows) if i > 0)
    tv = rows[-1]["fcf"] * (1 + g) / (wacc - g) / (1 + wacc) ** (t0 + len(rows) - 1)
    return (pv + tv + CASH) / SH_DIL, pv, tv


c = conn()
PEER = {}
for t, v in P["peers"].items():
    p0 = float(pd.read_sql("SELECT `종가` FROM us_price WHERE `티커`=%s AND `날짜`<=%s ORDER BY `날짜` DESC LIMIT 1", c, params=[t, PXDATE]).iloc[0, 0])
    mc = p0 * v["shares"] / 1e6
    ev = mc - (v["cash"] + v["sti"] + v["lti"] - v["debt"]) / 1e6
    rev = v["rev_ttm"] / 1e6
    PEER[t] = dict(name=v["name"], price=p0, mcap=mc, ev=ev, rev=rev, g=v["g"], fcf_m=(v["cfo_ttm"] - v["capex_ttm"]) / v["rev_ttm"], ev_rev=ev / rev)
EXIT = float(np.median([v["ev_rev"] for v in PEER.values()]))
MRVL_PX = PEER["MRVL"]["price"]
MRVL_1028 = float(pd.read_sql("SELECT `종가` FROM us_price WHERE `티커`='MRVL' AND `날짜`='2026-10-28'", c).iloc[0, 0])
M = K["merger"]
DEAL = M["exchange_ratio"] * MRVL_PX                                   # 4.5 × 159.80
SPREAD = DEAL / PRICE - 1
FEE_REG_PS = M["fee_regulatory_to_lite"] / SH_DIL


def exit_value(rows, wacc, mult=None, fy=2029):
    t0 = (pd.Timestamp("2027-06-30") - pd.Timestamp(ASOF)).days / 365
    fy27_left = 1 - QS[0] / REV27
    pv = rows[0]["fcf"] * fy27_left / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows):
        if i == 0:
            continue
        if r["fy"] > fy:
            break
        pv += r["fcf"] / (1 + wacc) ** (t0 + i - 0.5)
    r_end = [r for r in rows if r["fy"] == fy][0]
    n = t0 + (fy - 2027)
    return (pv + r_end["rev"] * (mult or EXIT) / (1 + wacc) ** n + CASH) / SH_DIL, r_end


SCN = {"보수": dict(rev28=7500, m_t=0.20, gm=0.8, p=0.60), "기본": dict(rev28=REV28, m_t=0.24, gm=1.0, p=0.75),
       "낙관": dict(rev28=10500, m_t=0.28, gm=1.2, p=0.90)}
OUT = {}
for k, s in SCN.items():
    rows = project(s["rev28"], s["m_t"], gmult=s["gm"])
    va, pv, tv = dcf(rows, WACC)
    vb, r29 = exit_value(rows, WACC)
    sa = 0.5 * va + 0.5 * vb
    OUT[k] = dict(rows=rows, va=va, vb=vb, pv=pv, tv=tv, r29=r29, sa=sa, p=s["p"], deal=DEAL, tp=s["p"] * DEAL + (1 - s["p"]) * sa)
TP = int(round(OUT["기본"]["tp"] / 5) * 5)
UP = TP / PRICE - 1
RATING = "BUY" if UP >= .15 else ("HOLD" if UP >= -.05 else "SELL")
SA_BASE = OUT["기본"]["sa"]
P_IMPL = (PRICE - SA_BASE) / (DEAL - SA_BASE) if DEAL != SA_BASE else None   # 시장가가 뜻하는 완료 확률(기본 단독가치 기준)

ps = [0.5, 0.6, 0.75, 0.9, 1.0]
mrvls = [120, 140, MRVL_PX, 180, 200]
SENS = [[p * 4.5 * m + (1 - p) * SA_BASE for m in mrvls] for p in ps]
waccs = [0.10, 0.12, WACC, 0.16]
mts = [0.20, 0.24, 0.28]
SENS_SA = [[0.5 * dcf(project(REV28, m), w)[0] + 0.5 * exit_value(project(REV28, m), w)[0] for w in waccs] for m in mts]

R = dict(asof=ASOF, pxdate=PXDATE, orig=ORIG, px_orig=PX_ORIG, chg_since=CHG_SINCE, px_1028=PX_1028, price=PRICE, tp=TP, upside=UP, rating=RATING,
         hi52=HI52, lo52=LO52, sh_basic=SH_BASIC, sh_dil=SH_DIL, cash=CASH, conv=CONV, mcap_dil=MCAP_DIL, ev=EV,
         rev26=REV26, rev27=REV27, q27=QS, qg=QG, opm27=OPM27, eps27=EPS27, pe27=PRICE / EPS27, ttm_rev=TTM_REV, rev28=REV28,
         ust=UST, beta=BETA, erp=ERP, wacc=WACC, g_t=G_T, tail=TAIL, peers=PEER, exit=EXIT,
         mrvl_px=MRVL_PX, mrvl_1028=MRVL_1028, deal=DEAL, spread=SPREAD, fee_reg_ps=FEE_REG_PS, p_impl=P_IMPL, sa_base=SA_BASE,
         scen={k: dict(tp=v["tp"], va=v["va"], vb=v["vb"], sa=v["sa"], p=v["p"], pv=v["pv"], tv=v["tv"], rows=v["rows"], r29=v["r29"],
                       upside=v["tp"] / PRICE - 1) for k, v in OUT.items()}, scen_assump=SCN,
         sens=dict(p=ps, mrvl=mrvls, v=SENS), sens_sa=dict(wacc=waccs, m_t=mts, v=SENS_SA), key=K)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE} (08-19 {PX_ORIG:.2f}, {CHG_SINCE:+.1%}; 10-28 {PX_1028}) mcap(dil) {MCAP_DIL:,.0f} FY27 {REV27:,.0f} {QS} EPS27 {EPS27:.2f} PE27 {PRICE/EPS27:.1f}")
    print("beta", BETA, f"WACC {WACC:.2%}")
    for t, v in PEER.items():
        print(t, f"px {v['price']:.2f} mcap {v['mcap']:,.0f} EV/rev {v['ev_rev']:.1f} g {v['g']:.1%} fcf {v['fcf_m']:.1%}")
    print("exit", round(EXIT, 2), "MRVL", MRVL_PX, "(10-28", MRVL_1028, ") deal", round(DEAL, 1), f"spread {SPREAD:+.1%}", "fee/sh", round(FEE_REG_PS, 1))
    for k, v in OUT.items():
        print(k, "A", round(v["va"]), "B", round(v["vb"]), "SA", round(v["sa"]), "p", v["p"], "TP", round(v["tp"]), f"TV {v['tv']/(v['pv']+v['tv']):.0%}", "FY29", round(v["r29"]["rev"]))
    print("TP", TP, f"{UP:+.1%}", RATING, "p implied", P_IMPL)
