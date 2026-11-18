"""대한광통신(010170) 밸류에이션 모델 — 2026-11-18 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/대한광통신/model.py
원래 리포트: 2026-08-17 BUY 24,500원. 기준일 2026-11-18(수) · 기준주가 11-18 종가(네이버 기반 FinanceDataReader).
자료: DART 연결재무제표(2021~3Q26) → fs_summary_2026-11-18.csv, 3Q26 분기보고서(11-13: 수주잔고·수출·주식 수 변동·차입금).
     피어 배수: tools/peers.py → peers_20261117.csv(2Q26까지 4개 분기 합).
방법(2026-11-18 본인 OK): A. DCF(FCFF 4Q26~2036, 영구성장 2%) 50% + B. 2027E 매출 × 목표 EV/매출 3배 − 순차입 50%.
'BUY가 되기 위한 조건'(재조사 원칙 8)은 목표가와 따로 계산. 증권사 목표주가는 쓰지 않음. 출력: results.json
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
from valuation.tools.buy_cond import buy_price, solve_min, cond_price

ASOF = "2026-11-18"
ORIG = dict(date="2026-08-17", rating="BUY", tp=24500, method="DCF·EV/매출 종합")
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-17.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07
G_T = 0.02
TAX = 0.20
KD = 0.055                                                 # 차입 이자율(3Q26 이자비용 ÷ 평균 차입금 수준)

# ───────────────────────── 시세
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px[px.index < ORIG["date"]]["Close"].iloc[-1])        # 원래 작성일(일) 직전 거래일 08-14 종가
HI_SINCE = float(px.loc[ORIG["date"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["date"]:ASOF, "Close"].idxmax().date())
SH = 155_485_660                                           # 3Q26 분기보고서(자기주식 없음)
SH_2025 = 131_985_660
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적
FY, Q = hist("대한광통신", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
M9 = {k: Q["20261Q"][k] + Q["20262Q"][k] + Q["20263Q"][k] for k in ("매출", "영업이익", "지배순이익")}
M9P = {k: Q["20251Q"][k] + Q["20252Q"][k] + Q["20253Q"][k] for k in ("매출", "영업이익", "지배순이익")}
CASH_3Q = Q["20263Q"]["현금"]
DEBT_3Q = 1000.0                                           # 3Q26 차입금 약 900억 + 리스부채 포함 약 1,000억
NET_DEBT = DEBT_3Q - CASH_3Q
EQ_3Q = Q["20263Q"]["지배자본"]
BACKLOG = dict(telecom=994.72, power=151.33, total=1146.05)      # 2026-09-30 수주잔고
EXPORT = dict(m9_exp=905, m9_tel_exp=665, fy25_tel_exp=561)

# ───────────────────────── 할인율 (시가 기준 가중)
BETA = beta_kr("010170", ASOF, 2, "^KQ11")
COE = RF + BETA["blume"] * MRP
WACC = (MCAP * COE + DEBT_3Q * KD * (1 - TAX)) / (MCAP + DEBT_3Q)

PEER = pd.read_csv(HERE / "peers_20261117.csv")
PEER = PEER[PEER["name"] != "대한광통신"][["name", "PER", "PBR", "EV/EBITDA", "EV/Sales", "OPM"]]

# ───────────────────────── 추정 (2026-11-18 본인 OK 제안값)
SC = {"보수": dict(q4=580, q4m=0.03, g27=0.10, m27=0.03, g28=0.05, m_lt=0.07, evs=2.0),
      "기본": dict(q4=620, q4m=0.056, g27=0.25, m27=0.06, g28=0.12, m_lt=0.10, evs=3.0),
      "낙관": dict(q4=660, q4m=0.08, g27=0.40, m27=0.10, g28=0.20, m_lt=0.15, evs=4.0)}
G_LATE = [0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.03]   # 2029~2036
DA_R, CAPEX_R, NWC_R = 0.04, 0.035, 0.20                    # 2025 감가상각 58억 / 매출 1,394억 ≈ 4%


def forecast(s):
    rev26 = M9["매출"] + s["q4"]; op26 = M9["영업이익"] + s["q4"] * s["q4m"]
    rows = [dict(year=2026, rev=rev26, op=op26, opm=op26 / rev26)]
    rev = rev26 * (1 + s["g27"]); rows.append(dict(year=2027, rev=rev, op=rev * s["m27"], opm=s["m27"]))
    ms = np.linspace(s["m27"], s["m_lt"], len(G_LATE) + 2)[1:]
    rev *= 1 + s["g28"]; rows.append(dict(year=2028, rev=rev, op=rev * ms[0], opm=float(ms[0])))
    for i, (g, m) in enumerate(zip(G_LATE, ms[1:])):
        rev *= 1 + g; rows.append(dict(year=2029 + i, rev=rev, op=rev * m, opm=float(m)))
    prev_rev = FY["2025"]["매출"]
    for r in rows:
        r["ni"] = (r["op"] - DEBT_3Q * KD) * (1 - TAX)
        r["eps"] = r["ni"] * 1e8 / SH
        r["da"] = r["rev"] * DA_R
        r["capex"] = r["rev"] * CAPEX_R
        r["dnwc"] = (r["rev"] - prev_rev) * NWC_R
        r["fcff"] = r["op"] * (1 - TAX) + r["da"] - r["capex"] - r["dnwc"]
        prev_rev = r["rev"]
    return rows


def dcf(rows, wacc):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    r26 = rows[0]
    q4_share = (r26["rev"] - M9["매출"]) / r26["rev"]
    pv = r26["fcff"] * q4_share / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows[1:]):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + G_T) / (wacc - G_T) / (1 + wacc) ** (t0 + len(rows) - 1)
    return (pv + tv - NET_DEBT) * 1e8 / SH, pv, tv


def value(s, wacc=None):
    rows = forecast(s)
    va, pv, tv = dcf(rows, wacc or WACC)
    vb = (rows[1]["rev"] * s["evs"] - NET_DEBT) * 1e8 / SH
    return dict(rows=rows, evs=s["evs"], va=va, vb=vb, pv=pv, tv=tv, tp=(va + vb) / 2)


pser = px["Close"].astype(float)
PBAND = band(pser, Q, SH, ASOF, start="2022-03-31", kind="pbr")

OUT = {k: value(s) for k, s in SC.items()}
for v in OUT.values():
    v["upside"] = v["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -2))
UP = TP / PRICE - 1
RATING = rating_of(UP)

evs_list = [1.0, 2.0, 3.0, 4.0, 6.0]
g_list = [0.10, 0.25, 0.40]
SENS_P = dict(evs=evs_list, g=g_list, v=[[value(dict(SC["기본"], g27=g, evs=e))["tp"] for e in evs_list] for g in g_list])
w_list = [WACC - 0.02, WACC - 0.01, WACC, WACC + 0.01]
ml_list = [0.07, 0.10, 0.15]
SENS_D = dict(wacc=w_list, m=ml_list, v=[[dcf(forecast(dict(SC["기본"], m_lt=m)), w)[0] for w in w_list] for m in ml_list])

# ───────────────────────── BUY가 되기 위한 조건
BUYP = buy_price(PRICE)
need_evs = solve_min(lambda e: value(dict(SC["기본"], evs=e))["tp"], 0.5, 60, BUYP)          # 같은 매출일 때 필요한 EV/매출
need_rev27 = (BUYP * SH / 1e8 + NET_DEBT) / 3.0                                              # B만으로 보면 EV/매출 3배에 필요한 2027 매출
need_mlt = solve_min(lambda m: value(dict(SC["기본"], m_lt=m, m27=0.10))["tp"], 0.05, 0.80, BUYP)   # 2027 마진 10%일 때 필요한 장기 마진
PEAK = dict(rev=max(FY[y]["매출"] for y in YRS), rev_y=max(YRS, key=lambda y: FY[y]["매출"]), op=max(FY[y]["영업이익"] for y in YRS))
BUY = dict(buy_price=BUYP, need_evs=need_evs, need_rev27_evs3=need_rev27, need_mlt=need_mlt, base_rev27=Bs["rows"][1]["rev"],
           peak=PEAK, backlog=BACKLOG, peer_evs_max=float(PEER["EV/Sales"].max()),
           cond=[dict(cond="지금 추정(기본) 그대로", px=cond_price(Bs["tp"])),
                 dict(cond="분기 매출 900억 이상 · 영업이익률 10% 이상 2개 분기 연속(낙관 경로)", px=cond_price(OUT["낙관"]["tp"]))])

R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, sh_2025=SH_2025,
         hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], ni=FY[y]["지배순이익"], eq=FY[y]["지배자본"]) for y in YRS},
         q={k: dict(rev=Q[k]["매출"], op=Q[k]["영업이익"], ni=Q[k]["지배순이익"]) for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q")},
         m9=M9, m9p=M9P, cash=CASH_3Q, debt=DEBT_3Q, net_debt=NET_DEBT, eq_3q=EQ_3Q, backlog=BACKLOG, export=EXPORT,
         rf=RF, mrp=MRP, beta=BETA, coe=COE, kd=KD, wacc=WACC, g_t=G_T, tax=TAX, pband=PBAND, peer=PEER.to_dict("records"),
         scen=OUT, scen_assump=SC, g_late=G_LATE, sens_p=SENS_P, sens_d=SENS_D, buy=BUY,
         pbr=MCAP / EQ_3Q, evs_27_now=(MCAP + NET_DEBT) / Bs["rows"][1]["rev"])
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} (08-14 {PX_ORIG:,.0f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:,.0f} {HI_SINCE_D}) 시총 {MCAP:,.0f}억 52주 {HI52:,.0f}/{LO52:,.0f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} WACC {WACC:.4f} 순차입 {NET_DEBT:,.0f} PBR {MCAP/EQ_3Q:.1f} EV/27E매출 {R['evs_27_now']:.1f}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"26E {r[0]['rev']:,.0f}/{r[0]['op']:,.0f} 27E {r[1]['rev']:,.0f}/{r[1]['op']:,.0f} A(DCF) {v['va']:,.0f} B(EV/S) {v['vb']:,.0f} TP {v['tp']:,.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}")
    print("BUY", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in BUY.items() if k not in ("cond", "peak")}, [round(c["px"], -1) for c in BUY["cond"]])
