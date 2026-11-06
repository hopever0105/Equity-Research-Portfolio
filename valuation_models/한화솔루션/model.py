"""한화솔루션(009830) 밸류에이션 모델 — 2026-11-06 신규. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/한화솔루션/model.py
기준일 2026-11-06 · 기준주가 2026-11-06 종가(stock_db, 보통 009830 / 우선 009835).
반영한 자료: 2016~2025 사업보고서, 1Q26 분기·2Q26 반기보고서(연결), 3Q26 영업(잠정)실적(10-29), 유상증자 결정·정정·결과
  (03-26 최초 → 07-20 확정 22,100원, 07-30 납입 53,000,000주 · 1조 1,713억), 불성실공시법인 지정(06-12), 주식소각(07-29),
  공동사업재편계획 승인(07-22, 여천NCC 증자 2,725억), 중대재해 발생(09-09 정정), 기업지배구조보고서(06-01).
방법: A. 적정 PBR (정상 ROE − g)/(COE − g) × 2026E말 BPS 50% + B. 자기 PBR 밴드(2021-05~2026-10) 평균 × 2026E말 BPS 50%.
      정상 ROE: 기본 = 2028E 모델 ROE(사업 재편·미국 공장 가동 후), 낙관 = 2016~2022 평균, 보수 = 2027E.
      교차확인: EV/EBITDA(리스 제외 차입금). 증권사 목표주가는 쓰지 않음. 출력: results.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr
from valuation.tools.report_kit import rating_of
from valuation.tools.simple_val import hist, band, gordon_pbr

ASOF = "2026-11-06"
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-05.json").read_text(encoding="utf-8"))
RF, MRP, G = MAC["ktb10y"]["value"] / 100, 0.07, 0.02

px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str}, parse_dates=["날짜"]).set_index("날짜")
px = px[px.index <= ASOF]
PRICE = float(px["종가"].iloc[-1])
PRICE_PREF = 14990.0                                   # 009835, 2026-11-06 종가(stock_db)
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["고가"].max()), float(w52["저가"].min())

SH_OLD = 171_892_536                                   # 유상증자 신주 상장(08-11) 전 보통주
NEW_SH, NEW_AMT, ISSUE_PX, PLAN_PX = 53_000_000, 11713, 22100, 27900
SH_COM = SH_OLD + NEW_SH                               # 224,892,536
SH_PREF = 2_544_616                                    # 08-04 소각(30,733주) 후
SH = SH_COM + SH_PREF
MCAP = (PRICE * SH_COM + PRICE_PREF * SH_PREF) / 1e8
DILUTION = NEW_SH / SH_OLD

FY, Q = hist("한화솔루션", ASOF)
OLD = {2016: (92588, 7792, 7553, 52849), 2017: (93418, 7564, 8247, 60151), 2018: (90460, 3543, 1867, 60900),
       2019: (95033, 3783, -2376, 57282), 2020: (91950, 5942, 3091, 59291)}     # 매출·영업이익·지배순이익·지배자본 (DART 사업보고서)
HIST = {str(y): dict(rev=v[0], op=v[1], nic=v[2], eqc=v[3]) for y, v in OLD.items()}
for y in ("2021", "2022", "2023", "2024", "2025"):
    HIST[y] = dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], nic=FY[y]["지배순이익"], eqc=FY[y]["지배자본"])
ROE, prev = {}, None
for y in sorted(HIST):
    e = HIST[y]["eqc"]
    ROE[y] = HIST[y]["nic"] / ((prev + e) / 2) if prev else HIST[y]["nic"] / e
    prev = e
ROE_1622 = sum(ROE[str(y)] for y in range(2016, 2023)) / 7
ROE_1625 = sum(ROE[str(y)] for y in range(2016, 2026)) / 10

# 2026: 1Q·2Q 연결 + 3Q 잠정(10-29)
Q3 = dict(rev=39486, op=905, ni=685, nic=573)
YTD = dict(rev=Q["20261Q"]["매출"] + Q["20262Q"]["매출"] + Q3["rev"], op=Q["20261Q"]["영업이익"] + Q["20262Q"]["영업이익"] + Q3["op"],
           nic=Q["20261Q"]["지배순이익"] + Q["20262Q"]["지배순이익"] + Q3["nic"])
EQ_2Q26 = Q["20262Q"]["지배자본"]
EQ_3Q26 = EQ_2Q26 + NEW_AMT + Q3["nic"]               # 증자 비용·기타포괄손익 미반영(확인 필요: 3Q26 분기보고서)
DEBT_2Q26 = dict(st=83867, lt=70281, cash=26930, sti=3617)   # 반기보고서 연결재무상태표 '차입금'·'장기차입금'
NETDEBT = DEBT_2Q26["st"] + DEBT_2Q26["lt"] - DEBT_2Q26["cash"] - DEBT_2Q26["sti"] - (NEW_AMT - 2636) - 2636 * 0  # 증자 대금 중 시설자금은 아직 현금
NETDEBT = DEBT_2Q26["st"] + DEBT_2Q26["lt"] - DEBT_2Q26["cash"] - DEBT_2Q26["sti"] - NEW_AMT
NCI = 27580
DA_TTM = 7710 + 627                                    # stock_db kor_fs 3Q25~2Q26 유형·무형 상각비
FIN = dict(nonop=-2400, tax=0.22, da=[8500, 8800, 9100])   # 영업외(이자 등) 연간, 법인세율, D&A 2026~2028E

SC = {"보수": dict(op4q=500, op27=4500, op28=5500, roe="2027"), "기본": dict(op4q=1000, op27=7000, op28=8500, roe="2028"),
      "낙관": dict(op4q=1500, op27=9500, op28=11500, roe="1622")}


def forecast(s):
    rows = []
    q4_ni = (s["op4q"] + FIN["nonop"] / 4) * (1 - FIN["tax"])
    ni26 = YTD["nic"] + q4_ni
    eq = EQ_3Q26 + q4_ni
    r = dict(year="2026", op=YTD["op"] + s["op4q"], ni=ni26, eq_end=eq, q4_ni=q4_ni)
    r["roe"] = ni26 / ((HIST["2025"]["eqc"] + eq) / 2); r["bps"] = eq * 1e8 / SH; r["ebitda"] = r["op"] + FIN["da"][0]
    rows.append(r)
    for i, (y, op) in enumerate((("2027", s["op27"]), ("2028", s["op28"])), 1):
        ni = (op + FIN["nonop"]) * (1 - FIN["tax"])
        e2 = eq + ni
        rows.append(dict(year=y, op=op, ni=ni, eq_end=e2, roe=ni / ((eq + e2) / 2), bps=e2 * 1e8 / SH, ebitda=op + FIN["da"][i]))
        eq = e2
    return rows


B_OWN = beta_kr("009830", ASOF, 3)
BETA = B_OWN["blume"]
COE = RF + BETA * MRP
BAND = band(px["종가"], Q, SH, ASOF, start="2021-05-31")

SCEN = {}
for k, s in SC.items():
    f = forecast(s)
    roe_n = {"2027": f[1]["roe"], "2028": f[2]["roe"], "1622": ROE_1622}[s["roe"]]
    pb_a = max(gordon_pbr(roe_n, COE, G), 0.0)
    pb_b = BAND["mean"] + {"보수": -1, "기본": 0, "낙관": 1}[k] * BAND["sd"]
    bps = f[0]["bps"]
    va, vb = pb_a * bps, pb_b * bps
    tp = (va + vb) / 2
    SCEN[k] = dict(rows=f, roe_n=roe_n, pb_a=pb_a, pb_b=pb_b, bps=bps, va=va, vb=vb, tp=tp, upside=tp / PRICE - 1)
B = SCEN["기본"]
TP = int(round(B["tp"], -2))
UP = TP / PRICE - 1
RATING = rating_of(UP)
BPS_NOW = EQ_3Q26 * 1e8 / SH
PBR_NOW = PRICE / BPS_NOW
EV = MCAP + NETDEBT + NCI
EVE = dict(ttm=EV / ((Q["20253Q"]["영업이익"] + Q["20254Q"]["영업이익"] + Q["20261Q"]["영업이익"] + Q["20262Q"]["영업이익"]) + DA_TTM),
           e26=EV / B["rows"][0]["ebitda"], e27=EV / B["rows"][1]["ebitda"])
# 목표주가가 뜻하는 2027E EV/EBITDA
EVE["tp27"] = (TP * SH / 1e8 + NETDEBT + NCI) / B["rows"][1]["ebitda"]
# 증자 희석: 증자 전 BPS vs 후
BPS_PRE = EQ_2Q26 * 1e8 / (SH_OLD + SH_PREF)
SENS = dict(roe=[0.02, 0.035, 0.05, 0.065, 0.08], beta=[0.6, 0.7, 0.8, 0.9, 1.0])
SENS["coe"] = [RF + b * MRP for b in SENS["beta"]]
SENS["v"] = [[(max(gordon_pbr(r, c, G), 0) * B["bps"] + B["vb"]) / 2 for c in SENS["coe"]] for r in SENS["roe"]]

R = dict(asof=ASOF, price=PRICE, price_pref=PRICE_PREF, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, sh_com=SH_COM, sh_pref=SH_PREF,
         sh_old=SH_OLD, new_sh=NEW_SH, new_amt=NEW_AMT, issue_px=ISSUE_PX, plan_px=PLAN_PX, dilution=DILUTION, hi52=HI52, lo52=LO52,
         hist=HIST, roe=ROE, roe_1622=ROE_1622, roe_1625=ROE_1625, q={k: Q[k] for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q")},
         q3=Q3, ytd=YTD, eq_2q26=EQ_2Q26, eq_3q26=EQ_3Q26, bps_now=BPS_NOW, bps_pre=BPS_PRE, pbr_now=PBR_NOW, netdebt=NETDEBT, nci=NCI,
         debt=DEBT_2Q26, ev=EV, eve=EVE, da_ttm=DA_TTM, fin=FIN, rf=RF, mrp=MRP, g=G, beta=B_OWN, coe=COE, band=BAND, scen=SCEN,
         sens=SENS, scen_assump=SC)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} 시총 {MCAP:,.0f} BPS {BPS_NOW:,.0f} PBR {PBR_NOW:.2f} 베타 {BETA:.2f} COE {COE:.4f} 밴드 {BAND['mean']:.2f}±{BAND['sd']:.2f}")
    print("ROE", {k: round(v, 3) for k, v in ROE.items()}, "1622", round(ROE_1622, 3), "1625", round(ROE_1625, 3))
    for k, v in SCEN.items():
        print(k, f"ROEn {v['roe_n']:.3f} pbA {v['pb_a']:.2f} pbB {v['pb_b']:.2f} BPS {v['bps']:,.0f} A {v['va']:,.0f} B {v['vb']:,.0f} TP {v['tp']:,.0f} {v['upside']:+.1%}",
              [(r['year'], round(r['op']), round(r['ni']), round(r['roe'], 3)) for r in v['rows']])
    print("TP", TP, RATING, f"{UP:+.1%}", "EV", round(EV), {k: round(v, 1) for k, v in EVE.items()}, "BPS pre", round(BPS_PRE))
