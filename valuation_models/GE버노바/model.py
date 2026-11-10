"""GE버노바(GEV) 밸류에이션 모델 — 2026-11-06 재조사. 단위: 백만 달러(주당·배수·비율 제외). 실행: python valuation/GE버노바/model.py
원래 리포트: 2026-09-01 BUY $1,180(당시 $914.07, 08-29 종가 표기). 기준일 2026-11-06(금) · 기준주가 11-06 미국 종가 $774.11(yfinance).
자료: SEC 10-K FY25, 10-Q 1~3Q26, 8-K 3Q26 보도자료(10-28) → sec_key_20261106.json, 피어 배수(yfinance, 11-06 종가 기준) → peers_20261106.json,
     미국채 10년 → tools/macro_2026-11-06.json. 애널리스트 의견(Guggenheim·Susquehanna·BMO·JPMorgan·Citi, 10-29~11-02)은 교차확인 표에만.
방법: A. DCF(FCFF = 조정 EBITDA × 현금전환율, 2027~2036 + 영구성장) 60% + B. 2027E 조정 EBITDA × 피어 EV/EBITDA 중앙값 + 순현금 40%.
     선수금(계약부채) 유입으로 부풀려진 2026 FCF는 쓰지 않는다. 출력: results.json
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
ORIG = dict(date="2026-09-01", pxdate="2026-08-28", rating="BUY", tp=1180, px=914.07, method="DCF·PER·컨센서스 종합")

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["pxdate"], "Close"])
HI_SINCE = float(px.loc[ORIG["pxdate"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["pxdate"]:ASOF, "Close"].idxmax().date())
B_ = K["balance_20260930"]
SH_OUT = K["shares_outstanding"]["2026-09-30"]
SH_DIL = K["quarterly"]["diluted_shares_wavg"]["3Q26"]
DEBT = B_["debt_lt"] + B_["debt_current"]
NET_CASH = B_["cash_incl_restricted"] - DEBT
MCAP = PRICE * SH_OUT
EV = MCAP - NET_CASH

G26 = K["guidance_2026_as_of_20261028"]
REV26 = float(np.mean(G26["revenue"])); M26 = float(np.mean(G26["adj_ebitda_margin"])); EBITDA26 = REV26 * M26
REV_9M = K["ytd_9m26"]["revenue"]; EBITDA_9M = K["ytd_9m26"]["adj_ebitda"]
REV_4Q = REV26 - REV_9M; EBITDA_4Q = EBITDA26 - EBITDA_9M
BACKLOG = K["q3_26_press"]["backlog_rpo"]

UST = MAC["ust10y"]["value"] / 100
BETA = beta_us("GEV", "2026-11-05", 2)
ERP = 0.05
WACC = UST + BETA["blume"] * ERP
G_T = 0.03
TAX = 0.21
DA_PCT = 0.025                                         # 감가상각/매출 (자본 지출 매출 2.5~3%와 비슷한 수준으로 가정)

# 피어 EV/EBITDA·선행 PER (11-06 종가 기준)
PEERS = {t: v for t, v in P.items() if t != "GEV"}
EVEB = {t: v["enterpriseToEbitda"] for t, v in PEERS.items() if v.get("enterpriseToEbitda")}
FPE = {t: v["forwardPE"] for t, v in PEERS.items() if v.get("forwardPE")}
EVEB_MED = float(np.median(list(EVEB.values())))
FPE_MED = float(np.median(list(FPE.values())))
EVEB_EX_HIT = float(np.median([v for t, v in EVEB.items() if t != "6501.T"]))

SC = {"보수": dict(g27=0.10, g28=0.08, m27=0.155, m28=0.17, m_lt=0.17, conv=0.55, mult=-1),
      "기본": dict(g27=0.15, g28=0.12, m27=0.17, m28=0.19, m_lt=0.20, conv=0.65, mult=0),
      "낙관": dict(g27=0.18, g28=0.15, m27=0.18, m28=0.21, m_lt=0.22, conv=0.75, mult=1)}
G_LATE = [0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.035]   # 2029~2036
MULT = {-1: float(min(EVEB.values()) if False else np.percentile(list(EVEB.values()), 25)), 0: EVEB_MED, 1: float(np.percentile(list(EVEB.values()), 75))}


def project(s):
    rows = [dict(year=2026, rev=REV26, m=M26)]
    rev = REV26 * (1 + s["g27"]); rows.append(dict(year=2027, rev=rev, m=s["m27"]))
    rev *= 1 + s["g28"]; rows.append(dict(year=2028, rev=rev, m=s["m28"]))
    ms = np.linspace(s["m28"], s["m_lt"], len(G_LATE) + 1)[1:]
    for i, (g, m) in enumerate(zip(G_LATE, ms)):
        rev *= 1 + g; rows.append(dict(year=2029 + i, rev=rev, m=float(m)))
    for r in rows:
        r["ebitda"] = r["rev"] * r["m"]; r["fcff"] = r["ebitda"] * s["conv"]
        r["ni"] = (r["ebitda"] - r["rev"] * DA_PCT) * (1 - TAX); r["eps"] = r["ni"] / SH_DIL
    return rows


def dcf(rows, wacc, conv):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    pv = EBITDA_4Q * conv / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows[1:]):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + G_T) / (wacc - G_T) / (1 + wacc) ** (t0 + len(rows) - 1)
    return (pv + tv + NET_CASH) / SH_DIL, pv, tv


OUT = {}
for k, s in SC.items():
    rows = project(s)
    va, pv, tv = dcf(rows, WACC, s["conv"])
    mult = MULT[s["mult"]]
    vb = (rows[1]["ebitda"] * mult + NET_CASH) / SH_DIL
    OUT[k] = dict(rows=rows, va=va, vb=vb, pv=pv, tv=tv, mult=mult, tp=0.6 * va + 0.4 * vb)
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -1))
UP = TP / PRICE - 1
RATING = rating_of(UP)

# 민감도: WACC × 장기 EBITDA 마진 (A), 현금전환율 × WACC
waccs = [WACC - 0.02, WACC - 0.01, WACC, WACC + 0.01]
mlts = [0.17, 0.20, 0.23]
SENS = dict(wacc=waccs, m=mlts, v=[[0.6 * dcf(project(dict(SC["기본"], m_lt=m)), w, SC["기본"]["conv"])[0] + 0.4 * Bs["vb"] for w in waccs] for m in mlts])
convs = [0.55, 0.65, 0.75]
SENS_C = dict(wacc=waccs, conv=convs, v=[[dcf(project(dict(SC["기본"], conv=c)), w, c)[0] for w in waccs] for c in convs])
# 현재가가 내포한 2029~2036 성장률 (A만)
IMPL = None
for gl in np.arange(0.035, 0.40, 0.0025):
    save = list(G_LATE); G_LATE[:] = [float(gl)] * len(save)
    v = dcf(project(SC["기본"]), WACC, SC["기본"]["conv"])[0]
    G_LATE[:] = save
    if v >= PRICE:
        IMPL = float(gl); break

ANALYSTS = [("Guggenheim", "11-02", "Buy", 1400, 1450), ("Susquehanna", "10-29", "Positive", 1250, 1270), ("BMO", "10-29", "Outperform", 1200, 1250),
            ("JPMorgan", "10-29", "-", 1035, None), ("Citi", "10-29", "Neutral", 1000, 1125)]
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, orig=ORIG, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D,
         hi52=HI52, lo52=LO52, sh_out=SH_OUT, sh_dil=SH_DIL, net_cash=NET_CASH, debt=DEBT, mcap=MCAP, ev=EV, rev26=REV26, m26=M26, ebitda26=EBITDA26,
         rev_9m=REV_9M, ebitda_9m=EBITDA_9M, rev_4q=REV_4Q, ebitda_4q=EBITDA_4Q, backlog=BACKLOG, ev_ebitda26=EV / EBITDA26,
         ust=UST, beta=BETA, erp=ERP, wacc=WACC, g_t=G_T, tax=TAX, peers=PEERS, eveb=EVEB, fpe=FPE, eveb_med=EVEB_MED, fpe_med=FPE_MED, mult=MULT,
         scen=OUT, scen_assump=SC, g_late=G_LATE, sens=SENS, sens_c=SENS_C, implied_g=IMPL, analysts=ANALYSTS, key=K,
         per27_now=PRICE / Bs["rows"][1]["eps"], ev_ebitda27=EV / Bs["rows"][1]["ebitda"])
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:.2f} (08-28 {PX_ORIG:.2f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:.2f} {HI_SINCE_D}) mcap {MCAP:,.0f} EV {EV:,.0f} net cash {NET_CASH:,.0f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} WACC {WACC:.4f}  EV/EBITDA26 {EV/EBITDA26:.1f} 27E {EV/Bs['rows'][1]['ebitda']:.1f}  peer EV/EBITDA med {EVEB_MED:.1f} (ex Hitachi {EVEB_EX_HIT:.1f}) fwdPE med {FPE_MED:.1f} MULT {MULT}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"27E rev {r[1]['rev']:,.0f} EBITDA {r[1]['ebitda']:,.0f} EPS {r[1]['eps']:.2f} | 28E EPS {r[2]['eps']:.2f} | A {v['va']:.0f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) B {v['vb']:.0f} ({v['mult']:.1f}x) TP {v['tp']:.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "PER27", round(PRICE / Bs["rows"][1]["eps"], 1), "implied 2029-36 g", IMPL)
