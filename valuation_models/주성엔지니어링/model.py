"""주성엔지니어링(036930) 밸류에이션 모델 — 2026-11-18 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/주성엔지니어링/model.py
원래 리포트: 2026-08-12 HOLD 173,000원. 기준일 2026-11-18(수) · 기준주가 11-18 종가(네이버 기반 FinanceDataReader).
자료: DART 연결재무제표(2021~3Q26) → fs_summary_2026-11-18.csv, 3Q26 분기보고서(11-13: 수주잔고·매출 지역), 3Q26 잠정실적(11-04).
방법(2026-11-18 본인 OK): A. 12개월 선행 PER = 2027E EPS × 목표 PER 30배 50% + B. DCF(FCFF 4Q26~2036, 영구성장 2%) 50%.
'BUY가 되기 위한 조건'(재조사 원칙 8)은 목표가와 따로 계산한다. 증권사 목표주가는 쓰지 않음. 출력: results.json
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
ORIG = dict(date="2026-08-12", rating="HOLD", tp=173000, method="PER·DCF 종합")
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-17.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07
G_T = 0.02
TAX = 0.15            # 법인세(연구개발 세액공제 반영, 2023~2025 유효세율 수준)

# ───────────────────────── 시세
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["date"], "Close"])
HI_SINCE = float(px.loc[ORIG["date"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["date"]:ASOF, "Close"].idxmax().date())
SH = 45_693_922                                           # 3Q26 분기보고서 유통주식수(자기주식 제외)
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적
FY, Q = hist("주성엔지니어링", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
M9 = {k: Q["20261Q"][k] + Q["20262Q"][k] + Q["20263Q"][k] for k in ("매출", "영업이익", "지배순이익")}
M9P = {k: Q["20251Q"][k] + Q["20252Q"][k] + Q["20253Q"][k] for k in ("매출", "영업이익", "지배순이익")}
CASH_3Q = Q["20263Q"]["현금"]
DEBT_3Q = 450.0                                           # 3Q26 재무상태표 차입금 합계(단기 + 장기, 리스 제외)
NET_CASH = CASH_3Q - DEBT_3Q
EQ_3Q = Q["20263Q"]["지배자본"]
BACKLOG = dict(semi=2118.39, disp=424.48, total=2542.87)  # 2026-09-30 수주잔고(별도, 억원)
EXPORT = dict(m9_dom=1382, m9_exp=547, fy25_dom=1098, fy25_exp=2009)   # 매출 지역(3Q26 분기보고서)

# ───────────────────────── 할인율
BETA = beta_kr("036930", ASOF, 2, "^KQ11")
WACC = RF + BETA["blume"] * MRP                            # 순현금 → WACC = COE

# ───────────────────────── 추정 (2026-11-18 본인 OK 제안값)
SC = {"보수": dict(q4=800, q4m=0.15, g27=0.25, m27=0.15, g28=0.00, m_lt=0.14, per=18.0),
      "기본": dict(q4=850, q4m=0.20, g27=0.45, m27=0.20, g28=0.10, m_lt=0.18, per=30.0),
      "낙관": dict(q4=900, q4m=0.23, g27=0.65, m27=0.25, g28=0.20, m_lt=0.22, per=49.0)}
G_LATE = [0.06, 0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.02]   # 2029~2036
INT_INC = 20.0                                              # 순현금 이자수익(억원/년)
DA_R, CAPEX_R, NWC_R = 0.054, 0.05, 0.15                    # 감가상각 = 2025 매출의 5.4%(168억), 설비투자, 운전자본


def forecast(s):
    rev26 = M9["매출"] + s["q4"]; op26 = M9["영업이익"] + s["q4"] * s["q4m"]
    rows = [dict(year=2026, rev=rev26, op=op26, opm=op26 / rev26)]
    rev = rev26 * (1 + s["g27"]); rows.append(dict(year=2027, rev=rev, op=rev * s["m27"], opm=s["m27"]))
    rev *= 1 + s["g28"]; rows.append(dict(year=2028, rev=rev, op=rev * s["m27"], opm=s["m27"]))
    ms = np.linspace(s["m27"], s["m_lt"], len(G_LATE) + 1)[1:]
    for i, (g, m) in enumerate(zip(G_LATE, ms)):
        rev *= 1 + g; rows.append(dict(year=2029 + i, rev=rev, op=rev * m, opm=float(m)))
    prev_rev = FY["2025"]["매출"]
    for r in rows:
        r["ni"] = r["op"] * (1 - TAX) + INT_INC
        r["eps"] = r["ni"] * 1e8 / SH
        r["da"] = r["rev"] * DA_R
        r["capex"] = r["rev"] * CAPEX_R
        r["dnwc"] = (r["rev"] - prev_rev) * NWC_R
        r["fcff"] = r["op"] * (1 - TAX) + r["da"] - r["capex"] - r["dnwc"]
        prev_rev = r["rev"]
    rows[0]["ni"] = M9["지배순이익"] + (rows[0]["op"] - M9["영업이익"]) * (1 - TAX) + INT_INC / 4
    rows[0]["eps"] = rows[0]["ni"] * 1e8 / SH
    return rows


def dcf(rows, wacc):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    r26 = rows[0]
    q4_share = (r26["rev"] - M9["매출"]) / r26["rev"]
    pv = r26["fcff"] * q4_share / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows[1:]):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + G_T) / (wacc - G_T) / (1 + wacc) ** (t0 + len(rows) - 1)
    return (pv + tv + NET_CASH) * 1e8 / SH, pv, tv


def value(s, wacc=None):
    rows = forecast(s)
    va = rows[1]["eps"] * s["per"]
    vb, pv, tv = dcf(rows, wacc or WACC)
    return dict(rows=rows, per=s["per"], va=va, vb=vb, pv=pv, tv=tv, tp=(va + vb) / 2)


# ───────────────────────── PER·PBR 밴드 (월말, 공시 시점 기준)
pser = px["Close"].astype(float)
BAND = band(pser, Q, SH, ASOF, start="2022-03-31", kind="per")
bs = pd.Series(BAND["series"]); BAND["median"] = float(bs.median()); BAND["q25"] = float(bs.quantile(.25)); BAND["q75"] = float(bs.quantile(.75))
PBAND = band(pser, Q, SH, ASOF, start="2022-03-31", kind="pbr")
pb = pd.Series(PBAND["series"]); PBAND["median"] = float(pb.median()); PBAND["q75"] = float(pb.quantile(.75))
PEER = pd.read_csv(HERE.parents[0] / "원익IPS" / "peers_semi_20261117.csv")
PEER = PEER[PEER["name"].isin(["유진테크", "피에스케이", "테스", "이오테크닉스", "케이씨텍"])][["name", "PER", "PBR", "EV/EBITDA", "OPM"]]
PEER_PER_MED = float(PEER["PER"].median())

OUT = {k: value(s) for k, s in SC.items()}
for v in OUT.values():
    v["upside"] = v["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -3))
UP = TP / PRICE - 1
RATING = rating_of(UP)

# 민감도: 목표 PER × 2027 영업이익률 (목표주가), 장기 마진 × WACC (B)
per_list = [18, 24, 30, 40, 49]
m_list = [0.15, 0.20, 0.25]
SENS_P = dict(per=per_list, m=m_list, v=[[value(dict(SC["기본"], m27=m, per=p))["tp"] for p in per_list] for m in m_list])
w_list = [WACC - 0.02, WACC - 0.01, WACC, WACC + 0.01]
ml_list = [0.14, 0.18, 0.22]
SENS_D = dict(wacc=w_list, m=ml_list, v=[[dcf(forecast(dict(SC["기본"], m_lt=m)), w)[0] for w in w_list] for m in ml_list])

# ───────────────────────── BUY가 되기 위한 조건 (목표가와 별개)
BUYP = buy_price(PRICE)
need_per = solve_min(lambda p: value(dict(SC["기본"], per=p))["tp"], 10, 400, BUYP)          # 같은 이익일 때 필요한 PER
need_g27 = solve_min(lambda g: value(dict(SC["기본"], g27=g))["tp"], 0, 6, BUYP)             # 같은 PER·마진일 때 필요한 2027 성장
need_g27_hi = solve_min(lambda g: value(dict(SC["기본"], g27=g, m27=0.30, m_lt=0.22))["tp"], 0, 6, BUYP)   # 마진 30%(2022년 정점 28%↑)일 때
rows_need = forecast(dict(SC["기본"], g27=need_g27)) if need_g27 is not None else None
rows_need_hi = forecast(dict(SC["기본"], g27=need_g27_hi, m27=0.30, m_lt=0.22)) if need_g27_hi is not None else None
PEAK = dict(rev=max(FY[y]["매출"] for y in YRS), ni=max(FY[y]["지배순이익"] for y in YRS),
            rev_y=max(YRS, key=lambda y: FY[y]["매출"]), ni_y=max(YRS, key=lambda y: FY[y]["지배순이익"]))
BUY = dict(buy_price=BUYP, need_per=need_per, base_eps27=Bs["rows"][1]["eps"],
           need_g27=need_g27, need_rev27=rows_need[1]["rev"] if rows_need else None, need_ni27=rows_need[1]["ni"] if rows_need else None,
           need_g27_hi=need_g27_hi, need_rev27_hi=rows_need_hi[1]["rev"] if rows_need_hi else None, need_ni27_hi=rows_need_hi[1]["ni"] if rows_need_hi else None,
           peak=PEAK, backlog=BACKLOG,
           cond=[dict(cond="지금 추정(기본) 그대로", px=cond_price(Bs["tp"])),
                 dict(cond="분기 매출 1,000억 이상 · 영업이익률 25% 이상 2개 분기 연속(낙관 경로 확인)", px=cond_price(OUT["낙관"]["tp"]))])

TTM_NI = Q["20254Q"]["지배순이익"] + M9["지배순이익"]
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH,
         hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], ni=FY[y]["지배순이익"], eq=FY[y]["지배자본"]) for y in YRS},
         q={k: dict(rev=Q[k]["매출"], op=Q[k]["영업이익"], ni=Q[k]["지배순이익"]) for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q")},
         m9=M9, m9p=M9P, cash=CASH_3Q, debt=DEBT_3Q, net_cash=NET_CASH, eq_3q=EQ_3Q, backlog=BACKLOG, export=EXPORT,
         rf=RF, mrp=MRP, beta=BETA, wacc=WACC, g_t=G_T, tax=TAX, band=BAND, pband=PBAND, peer=PEER.to_dict("records"), peer_per_med=PEER_PER_MED,
         scen=OUT, scen_assump=SC, g_late=G_LATE, sens_p=SENS_P, sens_d=SENS_D, buy=BUY,
         ttm_ni=TTM_NI, per_ttm=MCAP / TTM_NI, pbr=MCAP / EQ_3Q, per_27_now=PRICE / Bs["rows"][1]["eps"])
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} (08-12 {PX_ORIG:,.0f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:,.0f} {HI_SINCE_D}) 시총 {MCAP:,.0f}억 52주 {HI52:,.0f}/{LO52:,.0f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} WACC {WACC:.4f} 순현금 {NET_CASH:,.0f} PER밴드 중앙 {BAND['median']:.1f} q75 {BAND['q75']:.1f} PBR밴드 중앙 {PBAND['median']:.2f} 피어PER {PEER_PER_MED:.1f}")
    print(f"9M 매출 {M9['매출']:,.0f} OP {M9['영업이익']:,.0f} NI {M9['지배순이익']:,.0f} TTM PER {MCAP/TTM_NI:.0f} PBR {MCAP/EQ_3Q:.1f}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"26E {r[0]['rev']:,.0f}/{r[0]['op']:,.0f} 27E {r[1]['rev']:,.0f}/{r[1]['op']:,.0f} NI27 {r[1]['ni']:,.0f} EPS27 {r[1]['eps']:,.0f} A {v['va']:,.0f} B {v['vb']:,.0f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) TP {v['tp']:,.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}")
    print("BUY", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in BUY.items() if k not in ("cond", "peak", "backlog")}, [round(c["px"], -2) for c in BUY["cond"]])
