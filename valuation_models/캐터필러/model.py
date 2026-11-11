"""캐터필러(CAT) 밸류에이션 모델 — 2026-11-09 재조사. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/캐터필러/model.py
원래 리포트: 2026-08-24 BUY $1,030(당시 표기 $828.90, 08-21 종가 $827.90). 기준일 2026-11-09(월) · 기준주가 11-09 미국 종가(yfinance).
자료: SEC 10-K FY25, 10-Q 2·3Q26, 8-K 3Q26 보도자료(10-29) → sec_key_20261109.json, 피어 배수(yfinance, 11-09 종가 기준) → peers_20261109.json,
     미국채 10년 → tools/macro_2026-11-09.json. 애널리스트 목표가(실적 뒤 인하)는 교차확인 표에만.
방법: A. DCF(MP&E 기준 FCFF 2027~2036 + 영구성장) 50% + B. 2027E EPS × 피어 선행 PER 중앙값 50%.
     Cat Financial(금융) 부채는 고객 금융자산에 대응하므로 순차입에서 빼고, 금융 이익은 세후로 FCFF에 포함(모회사 배당으로 돌아옴).
     IEEPA 관세 환급(2026년 520)은 일회성이라 2027년 이후 마진에서 뺀다. 출력: results.json
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
ORIG = dict(date="2026-08-24", pxdate="2026-08-21", rating="BUY", tp=1030, px=828.90, method="증권사 컨센서스 + 실적 서프라이즈 재평가")

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["pxdate"], "Close"])
HI_SINCE = float(px.loc[ORIG["pxdate"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["pxdate"]:ASOF, "Close"].idxmax().date())
PX_PRE_EARN = float(px.loc["2026-10-28", "Close"]); PX_EARN = float(px.loc["2026-10-29", "Close"])

A_, Q_, Y9, B_ = K["annual"], K["quarterly"], K["ytd_9m26"], K["balance_20260930"]
SH_OUT = K["shares_outstanding"]["2026-09-30"]
SH_DIL = Q_["diluted_shares_wavg"]["3Q26"]
MPE_DEBT = B_["mpe_debt_lt"] + B_["mpe_debt_current"]
NET_DEBT = MPE_DEBT - B_["cash"] + 1405                 # 10-31 Fabick 인수 현금 $1.24B + 유보 $0.165B 반영
MCAP = PRICE * SH_OUT
EV = MCAP + NET_DEBT

# 2026E: 9M 실적 + 4Q (회사: 4Q 매출 moderate 성장 → +5%, 4Q 영업이익률 18.5% — 관세 $600M·딜러 재고 감소)
REV_4Q = Q_["revenue"]["4Q25"] * 1.05
OP_4Q = REV_4Q * 0.185
REV26 = Y9["revenue"] + REV_4Q
OP26 = Y9["op_income"] + OP_4Q
OP26_EX = OP26 - Y9["ieepa_recovery"]
TAX = K["outlook_2026_10q"]["tax_rate"]
OTHER = 200                                              # 영업외 순손익(연): 9M26 +654, 3Q +48 → 보수적으로 +200
NI26 = (OP26 + OTHER) * (1 - TAX)
EPS26 = Y9["eps_diluted"] + (OP_4Q + OTHER / 4) * (1 - TAX) / SH_DIL
BACKLOG = K["backlog"]["3Q26"]; BL_12M = BACKLOG - K["backlog"]["beyond_12m"]

UST = MAC["ust10y"]["value"] / 100
BETA = beta_us("CAT", ASOF, 2)
ERP = 0.05
COE = UST + BETA["blume"] * ERP
KD = 0.050 * (1 - TAX)                                   # MP&E 회사채 금리 약 5%(5.3% 2035년 만기 등), 세후
WD = MPE_DEBT / (MPE_DEBT + MCAP)
WACC = COE * (1 - WD) + KD * WD
G_T = 0.03
DA_PCT = 0.021                                           # MP&E 감가상각/매출 (9M26 1,225 ÷ 55,708)
CAPEX = {2027: 0.040, 2028: 0.037}                       # 2026 회사 계획 $3.3B(4.2%) → 증설 마무리 후 3.5%
CAPEX_LT = 0.035
NWC = 0.12                                               # 매출 증가분의 12%를 운전자본(재고·매출채권 − 선수금)으로
SH_DECL = 0.015                                          # 자사주로 희석주식 연 1.5% 감소 (2025→3Q26 −2.4%)

# 피어 선행 PER·EV/EBITDA (11-09 종가 기준)
PEERS = {t: v for t, v in P.items() if t != "CAT"}
FPE = {t: v["forwardPE"] for t, v in PEERS.items() if v.get("forwardPE")}
EVEB = {t: v["enterpriseToEbitda"] for t, v in PEERS.items() if v.get("enterpriseToEbitda")}
FPE_MED = float(np.median(list(FPE.values())))
EVEB_MED = float(np.median(list(EVEB.values())))
MULT = {-1: float(np.percentile(list(FPE.values()), 25)), 0: FPE_MED, 1: float(np.percentile(list(FPE.values()), 75))}

SC = {"보수": dict(g27=0.02, g28=0.00, m27=0.180, m28=0.165, m_lt=0.165, g_late0=0.04, mult=-1),
      "기본": dict(g27=0.07, g28=0.06, m27=0.195, m28=0.195, m_lt=0.185, g_late0=0.06, mult=0),
      "낙관": dict(g27=0.11, g28=0.09, m27=0.210, m28=0.215, m_lt=0.205, g_late0=0.07, mult=1)}


def g_late(s):
    return list(np.linspace(s["g_late0"], 0.03, 8))      # 2029~2036, 3%로 수렴


def project(s):
    rows = [dict(year=2026, rev=REV26, m=OP26_EX / REV26, sh=SH_DIL)]
    rev = REV26 * (1 + s["g27"]); rows.append(dict(year=2027, rev=rev, m=s["m27"]))
    rev *= 1 + s["g28"]; rows.append(dict(year=2028, rev=rev, m=s["m28"]))
    ms = np.linspace(s["m28"], s["m_lt"], 9)[1:]
    for i, (g, m) in enumerate(zip(g_late(s), ms)):
        rev *= 1 + g; rows.append(dict(year=2029 + i, rev=rev, m=float(m)))
    for i, r in enumerate(rows):
        r["op"] = r["rev"] * r["m"]
        r["ni"] = (r["op"] + OTHER) * (1 - TAX)
        r["sh"] = SH_DIL * (1 - SH_DECL) ** (i + 0.25)
        r["eps"] = r["ni"] / r["sh"]
        if i:
            d_rev = r["rev"] - rows[i - 1]["rev"]
            cap = CAPEX.get(r["year"], CAPEX_LT)
            r["fcff"] = r["op"] * (1 - TAX) + r["rev"] * DA_PCT - r["rev"] * cap - NWC * d_rev
    rows[0]["op"] = OP26; rows[0]["ni"] = NI26; rows[0]["eps"] = EPS26
    return rows


def dcf(rows, wacc):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    q4 = OP_4Q * (1 - TAX) + REV_4Q * (DA_PCT - 0.042)    # 4Q26 잔여 현금흐름(운전자본 제외)
    pv = q4 / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows[1:]):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + G_T) / (wacc - G_T) / (1 + wacc) ** (t0 + len(rows) - 1.5)
    return (pv + tv - NET_DEBT) / SH_DIL, pv, tv


OUT = {}
for k, s in SC.items():
    rows = project(s)
    va, pv, tv = dcf(rows, WACC)
    mult = MULT[s["mult"]]
    vb = rows[1]["eps"] * mult
    OUT[k] = dict(rows=rows, va=va, vb=vb, pv=pv, tv=tv, mult=mult, tp=0.5 * va + 0.5 * vb, g_late=g_late(s))
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -1))
UP = TP / PRICE - 1
RATING = rating_of(UP)

# 민감도 1: 장기 영업이익률 × WACC (목표주가, B 고정)
waccs = [WACC - 0.02, WACC - 0.01, WACC, WACC + 0.01]
mlts = [0.165, 0.185, 0.205]
SENS = dict(wacc=waccs, m=mlts, v=[[0.5 * dcf(project(dict(SC["기본"], m_lt=m)), w)[0] + 0.5 * Bs["vb"] for w in waccs] for m in mlts])
# 민감도 2: 2027E 매출 성장 × 목표 PER (B 값)
g27s = [0.02, 0.07, 0.11]
pers = [MULT[-1], FPE_MED, MULT[1], 22.0]
SENS_B = dict(g=g27s, per=pers, v=[[project(dict(SC["기본"], g27=g))[1]["eps"] * p for p in pers] for g in g27s])
# 현재가가 내포한 장기(2036) 영업이익률 (A만)
IMPL_M = None
for m in np.arange(0.185, 0.45, 0.0025):
    if dcf(project(dict(SC["기본"], m_lt=float(m))), WACC)[0] >= PRICE:
        IMPL_M = float(m); break
PE_IMPL = PRICE / Bs["rows"][1]["eps"]

ANALYSTS = [("Truist", "10-30", "Buy", 1027, None), ("Wells Fargo", "10-30", "-", 840, None), ("UBS", "10-30", "Hold", 750, 925),
            ("RBC", "10-30", "-", 722, 897), ("Morgan Stanley", "10-30", "Equal-weight", 675, 915)]
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, orig=ORIG, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D,
         px_pre_earn=PX_PRE_EARN, px_earn=PX_EARN, hi52=HI52, lo52=LO52, sh_out=SH_OUT, sh_dil=SH_DIL, mpe_debt=MPE_DEBT, net_debt=NET_DEBT, mcap=MCAP, ev=EV,
         rev26=REV26, op26=OP26, op26_ex=OP26_EX, eps26=EPS26, rev_4q=REV_4Q, op_4q=OP_4Q, backlog=BACKLOG, bl_12m=BL_12M,
         ust=UST, beta=BETA, erp=ERP, coe=COE, kd=KD, wd=WD, wacc=WACC, g_t=G_T, tax=TAX, other=OTHER, nwc=NWC, da=DA_PCT, capex=CAPEX, capex_lt=CAPEX_LT,
         peers=PEERS, fpe=FPE, eveb=EVEB, fpe_med=FPE_MED, eveb_med=EVEB_MED, mult=MULT,
         scen=OUT, scen_assump=SC, sens=SENS, sens_b=SENS_B, implied_m=IMPL_M, per27_now=PE_IMPL, per26_now=PRICE / EPS26, analysts=ANALYSTS, key=K)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:.2f} (08-21 {PX_ORIG:.2f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:.2f} {HI_SINCE_D}) mcap {MCAP:,.0f} EV {EV:,.0f} net debt {NET_DEBT:,.0f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} WACC {WACC:.4f}  2026E rev {REV26:,.0f} OP {OP26:,.0f} ({OP26/REV26:.1%}) EPS {EPS26:.2f} PER26 {PRICE/EPS26:.1f}")
    print(f"peer fwdPE med {FPE_MED:.1f} MULT {MULT} EV/EBITDA med {EVEB_MED:.1f}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"27E rev {r[1]['rev']:,.0f} OP {r[1]['op']:,.0f} EPS {r[1]['eps']:.2f} FCFF {r[1]['fcff']:,.0f} | 28E EPS {r[2]['eps']:.2f} | A {v['va']:.0f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) B {v['vb']:.0f} ({v['mult']:.1f}x) TP {v['tp']:.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "PER27", round(PE_IMPL, 1), "implied LT margin", IMPL_M)
