"""에스피지(058610) 밸류에이션 모델 — 2026-11-18 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/에스피지/model.py
원래 리포트: 2026-08-22 BUY 124,000원. 기준일 2026-11-18(수) · 기준주가 11-18 종가(네이버 기반 FinanceDataReader).
자료: DART 연결재무제표(2021~3Q26) → fs_summary_2026-11-18.csv, 3Q26 분기보고서(11-13), 3Q26 잠정(11-12), 중간배당 결정(09-07).
     정밀감속기 매출(2023 76억 → 2024 102억 → 2025 140억)은 원래 리포트 값. 피어 배수: tools/peers.py → peers_20261117.csv.
방법(2026-11-18 본인 OK): A. 2027E EPS × 자기 PER 밴드 중앙값 50% + B. SOTP = 모터 등 본업 2027E 순이익 × 12배 + 정밀감속기 2027E 매출 × EV/매출 20배 − 순차입 50%.
'BUY가 되기 위한 조건'(재조사 원칙 8)은 목표가와 따로 계산. 증권사 목표주가는 쓰지 않음. 출력: results.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr
from valuation.tools.report_kit import rating_of
from valuation.tools.simple_val import hist, band
from valuation.tools.buy_cond import buy_price, solve_min, cond_price

ASOF = "2026-11-18"
ORIG = dict(date="2026-08-22", rating="BUY", tp=124000, method="PER·SOTP 종합")
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-17.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07

# ───────────────────────── 시세
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px[px.index < ORIG["date"]]["Close"].iloc[-1])        # 원래 작성일(토) 직전 거래일 08-21 종가
HI_SINCE = float(px.loc[ORIG["date"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["date"]:ASOF, "Close"].idxmax().date())
SH = 22_177_360                                            # 자기주식 없음(3Q26 분기보고서)
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적·재무
FY, Q = hist("에스피지", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
M9 = {k: Q["20261Q"][k] + Q["20262Q"][k] + Q["20263Q"][k] for k in ("매출", "영업이익", "지배순이익")}
M9P = {k: Q["20251Q"][k] + Q["20252Q"][k] + Q["20253Q"][k] for k in ("매출", "영업이익", "지배순이익")}
DEBT_3Q, CASH_ST_3Q = 700.0, 341.0                         # 차입금 약 700억, 현금·단기금융상품 341억(3Q26)
NET_DEBT = DEBT_3Q - CASH_ST_3Q
EQ_3Q = Q["20263Q"]["지배자본"]
REDUCER = {"2023": 76, "2024": 102, "2025": 140}           # 정밀감속기 매출(원래 리포트)
NI_CONV = 0.76                                             # 순이익 / 영업이익 (2022년 0.77, 이자·기타비용 감안)

BETA = beta_kr("058610", ASOF, 2, "^KQ11")
COE = RF + BETA["blume"] * MRP

PEER = pd.read_csv(HERE / "peers_20261117.csv")
PEER = PEER[PEER["name"] != "에스피지"][["name", "PER", "PBR", "EV/EBITDA", "EV/Sales", "OPM"]]

pser = px["Close"].astype(float)
BAND = band(pser, Q, SH, ASOF, start="2022-03-31", kind="per")
bs = pd.Series(BAND["series"]); BAND["median"] = float(bs.median()); BAND["q25"] = float(bs.quantile(.25)); BAND["q75"] = float(bs.quantile(.75))
PBAND = band(pser, Q, SH, ASOF, start="2022-03-31", kind="pbr")
pb = pd.Series(PBAND["series"]); PBAND["median"] = float(pb.median()); PBAND["q75"] = float(pb.quantile(.75))

# ───────────────────────── 추정 (2026-11-18 본인 OK 제안값)
SC = {"보수": dict(q4=820, q4m=0.035, g27=0.00, m27=0.04, red27=180, evs=10.0, per="q25"),
      "기본": dict(q4=850, q4m=0.047, g27=0.06, m27=0.055, red27=250, evs=20.0, per="median"),
      "낙관": dict(q4=880, q4m=0.055, g27=0.12, m27=0.07, red27=350, evs=30.0, per="q75")}
MOTOR_PER = 12.0
RED_NI_M = 0.08                                            # 감속기 순이익률(본업과 분리할 때만 사용)


def forecast(s):
    rev26 = M9["매출"] + s["q4"]; op26 = M9["영업이익"] + s["q4"] * s["q4m"]
    ni26 = M9["지배순이익"] + s["q4"] * s["q4m"] * NI_CONV
    rev27 = rev26 * (1 + s["g27"]); op27 = rev27 * s["m27"]; ni27 = op27 * NI_CONV
    red_ni = s["red27"] * RED_NI_M
    return dict(rev26=rev26, op26=op26, ni26=ni26, rev27=rev27, op27=op27, ni27=ni27, eps27=ni27 * 1e8 / SH,
                red27=s["red27"], motor_ni27=ni27 - red_ni)


def value(s):
    f = forecast(s)
    per = BAND[s["per"]] if isinstance(s["per"], str) else s["per"]
    va = f["eps27"] * per
    vb = (f["motor_ni27"] * MOTOR_PER + f["red27"] * s["evs"] - NET_DEBT) * 1e8 / SH
    return dict(f=f, per=per, evs=s["evs"], va=va, vb=vb, tp=(va + vb) / 2)


OUT = {k: value(s) for k, s in SC.items()}
for v in OUT.values():
    v["upside"] = v["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -3))
UP = TP / PRICE - 1
RATING = rating_of(UP)

evs_list = [10.0, 15.0, 20.0, 30.0, 50.0]
red_list = [180, 250, 350]
SENS_P = dict(evs=evs_list, red=red_list, v=[[value(dict(SC["기본"], red27=r, evs=e))["tp"] for e in evs_list] for r in red_list])
per_list = [20.0, 30.0, BAND["median"], 70.0]
m_list = [0.04, 0.055, 0.07]
SENS_A = dict(per=per_list, m=m_list, v=[[value(dict(SC["기본"], m27=m, per=p))["va"] for p in per_list] for m in m_list])

# ───────────────────────── BUY가 되기 위한 조건
BUYP = buy_price(PRICE)
need_evs = solve_min(lambda e: value(dict(SC["기본"], evs=e))["tp"], 5, 500, BUYP)                 # 감속기 매출 250억일 때 필요한 EV/매출
need_red = solve_min(lambda r: value(dict(SC["기본"], red27=r))["tp"], 100, 20000, BUYP)           # EV/매출 20배일 때 필요한 감속기 매출
need_per = solve_min(lambda p: value(dict(SC["기본"], per=p))["tp"], 10, 1000, BUYP)               # 같은 이익일 때 필요한 PER (A)
PEAK = dict(rev=max(FY[y]["매출"] for y in YRS), op=max(FY[y]["영업이익"] for y in YRS), ni=max(FY[y]["지배순이익"] for y in YRS),
            ni_y=max(YRS, key=lambda y: FY[y]["지배순이익"]))
BUY = dict(buy_price=BUYP, need_evs=need_evs, need_red27=need_red, need_per=need_per, reducer=REDUCER, peak=PEAK,
           cond=[dict(cond="지금 추정(기본) 그대로", px=cond_price(Bs["tp"])),
                 dict(cond="감속기 연 매출 350억 이상 확인(사업보고서) + 본업 영업이익률 7% 회복(낙관 경로)", px=cond_price(OUT["낙관"]["tp"]))])

TTM_NI = Q["20254Q"]["지배순이익"] + M9["지배순이익"]
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH,
         hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], ni=FY[y]["지배순이익"], eq=FY[y]["지배자본"]) for y in YRS},
         q={k: dict(rev=Q[k]["매출"], op=Q[k]["영업이익"], ni=Q[k]["지배순이익"]) for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q")},
         m9=M9, m9p=M9P, debt=DEBT_3Q, cash_st=CASH_ST_3Q, net_debt=NET_DEBT, eq_3q=EQ_3Q, reducer=REDUCER, ni_conv=NI_CONV,
         rf=RF, mrp=MRP, beta=BETA, coe=COE, band=BAND, pband=PBAND, peer=PEER.to_dict("records"), motor_per=MOTOR_PER, red_ni_m=RED_NI_M,
         scen=OUT, scen_assump=SC, sens_p=SENS_P, sens_a=SENS_A, buy=BUY,
         ttm_ni=TTM_NI, per_ttm=MCAP / TTM_NI, pbr=MCAP / EQ_3Q, per_27_now=PRICE / Bs["f"]["eps27"],
         red_evs_now=(MCAP + NET_DEBT - Bs["f"]["motor_ni27"] * MOTOR_PER) / Bs["f"]["red27"])
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} (08-21 {PX_ORIG:,.0f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:,.0f} {HI_SINCE_D}) 시총 {MCAP:,.0f}억 52주 {HI52:,.0f}/{LO52:,.0f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} 순차입 {NET_DEBT:,.0f} PER밴드 중앙 {BAND['median']:.1f} q25 {BAND['q25']:.1f} q75 {BAND['q75']:.1f} PBR {MCAP/EQ_3Q:.1f} TTM PER {MCAP/TTM_NI:.0f}")
    for k, v in OUT.items():
        f = v["f"]
        print(k, f"26E {f['rev26']:,.0f}/{f['op26']:,.0f} 27E {f['rev27']:,.0f}/{f['op27']:,.0f} NI {f['ni27']:,.0f} EPS {f['eps27']:,.0f} A {v['va']:,.0f} ({v['per']:.1f}배) B {v['vb']:,.0f} TP {v['tp']:,.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "감속기 내재 EV/매출", round(R["red_evs_now"], 1))
    print("BUY", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in BUY.items() if k not in ("cond", "peak", "reducer")}, [round(c["px"], -2) for c in BUY["cond"]])
