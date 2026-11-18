"""원익IPS(240810) 밸류에이션 모델 — 2026-11-18 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/원익IPS/model.py
원래 리포트: 2026-08-12 BUY 165,000원. 기준일 2026-11-18(수) · 기준주가 11-18 종가(네이버 기반 FinanceDataReader).
자료: DART 연결재무제표(2021~3Q26) → fs_summary_2026-11-18.csv, 3Q26 분기보고서(11-16: 수주잔고·공정가치 금융자산), 3Q26 잠정(11-09),
     임시주총 결과(09-04), 자기주식 처분(09-15). 피어 배수: tools/peers.py → peers_semi_20261117.csv(2Q26까지 4개 분기 합).
방법(2026-11-18 본인 OK): A. 2027E EPS(영업이익 기준, 금융자산 평가손익 제외) × 피어 PER 중앙값 60% + B. DCF(FCFF) + 공정가치 금융자산 40%.
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
ORIG = dict(date="2026-08-12", rating="BUY", tp=165000, method="PER·DCF 종합")
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-17.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07
G_T = 0.02
TAX = 0.20
W_A, W_B = 0.6, 0.4

# ───────────────────────── 시세
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["date"], "Close"])
HI_SINCE = float(px.loc[ORIG["date"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["date"]:ASOF, "Close"].idxmax().date())
SH_ISSUED, TREASURY = 49_083_901, 376_755                  # 3Q26 분기보고서
SH = SH_ISSUED - TREASURY                                  # 48,707,146
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적
FY, Q = hist("원익IPS", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
M9 = {k: Q["20261Q"][k] + Q["20262Q"][k] + Q["20263Q"][k] for k in ("매출", "영업이익", "지배순이익")}
M9P = {k: Q["20251Q"][k] + Q["20252Q"][k] + Q["20253Q"][k] for k in ("매출", "영업이익", "지배순이익")}
CASH_3Q = Q["20263Q"]["현금"]
FVPL = 2412.0                                              # 당기손익-공정가치 금융자산 9월 말(연초 1,082억)
EQ_3Q = Q["20263Q"]["지배자본"]
BACKLOG = 6300.65                                          # 2026-09-30 수주잔고(반도체/Display 장비)
STOCK_COMP = dict(shares=51_456, people=1_431, date="2026-09-16")

# ───────────────────────── 할인율
BETA = beta_kr("240810", ASOF, 2, "^KQ11")
WACC = RF + BETA["blume"] * MRP                            # 무차입 → WACC = COE

# ───────────────────────── 피어 PER (TTM 2Q26)
PEER = pd.read_csv(HERE / "peers_semi_20261117.csv")
PEER = PEER[PEER["name"].isin(["원익IPS", "유진테크", "피에스케이", "테스", "이오테크닉스", "케이씨텍"])][["name", "PER", "PBR", "EV/EBITDA", "OPM"]]
PEER_PER_MED = float(PEER["PER"].median())

# ───────────────────────── 추정 (2026-11-18 본인 OK 제안값)
SC = {"보수": dict(q4=2700, q4m=0.13, g27=0.05, m27=0.12, g28=0.00, m_lt=0.10, per=16.0),
      "기본": dict(q4=3000, q4m=0.167, g27=0.15, m27=0.15, g28=0.05, m_lt=0.13, per=PEER_PER_MED),
      "낙관": dict(q4=3300, q4m=0.19, g27=0.25, m27=0.18, g28=0.10, m_lt=0.16, per=25.0)}
G_LATE = [0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.03, 0.02]   # 2029~2036
INT_INC = 60.0                                              # 현금 1,475억 이자수익
DA_R, CAPEX_R, NWC_R = 0.037, 0.035, 0.15                   # 2025 감가상각 340억 / 매출 9,098억 = 3.7%, 유형자산 취득 257억 = 2.8%


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
    return rows


def dcf(rows, wacc):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    r26 = rows[0]
    q4_share = (r26["rev"] - M9["매출"]) / r26["rev"]
    pv = r26["fcff"] * q4_share / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows[1:]):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + G_T) / (wacc - G_T) / (1 + wacc) ** (t0 + len(rows) - 1)
    return (pv + tv + CASH_3Q + FVPL) * 1e8 / SH, pv, tv


def value(s, wacc=None):
    rows = forecast(s)
    va = rows[1]["eps"] * s["per"]
    vb, pv, tv = dcf(rows, wacc or WACC)
    return dict(rows=rows, per=s["per"], va=va, vb=vb, pv=pv, tv=tv, tp=W_A * va + W_B * vb)


pser = px["Close"].astype(float)
PBAND = band(pser, Q, SH, ASOF, start="2022-03-31", kind="pbr")
pb = pd.Series(PBAND["series"]); PBAND["median"] = float(pb.median()); PBAND["q75"] = float(pb.quantile(.75))

OUT = {k: value(s) for k, s in SC.items()}
for v in OUT.values():
    v["upside"] = v["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -3))
UP = TP / PRICE - 1
RATING = rating_of(UP)

per_list = [14, 16, PEER_PER_MED, 22, 25]
m_list = [0.12, 0.15, 0.18]
SENS_P = dict(per=per_list, m=m_list, v=[[value(dict(SC["기본"], m27=m, per=p))["tp"] for p in per_list] for m in m_list])
w_list = [WACC - 0.02, WACC - 0.01, WACC, WACC + 0.01]
ml_list = [0.10, 0.13, 0.16]
SENS_D = dict(wacc=w_list, m=ml_list, v=[[dcf(forecast(dict(SC["기본"], m_lt=m)), w)[0] for w in w_list] for m in ml_list])

# ───────────────────────── BUY가 되기 위한 조건
BUYP = buy_price(PRICE)
need_per = solve_min(lambda p: value(dict(SC["기본"], per=p))["tp"], 10, 200, BUYP)
need_m27 = solve_min(lambda m: value(dict(SC["기본"], m27=m))["tp"], 0.10, 0.40, BUYP)        # 같은 매출일 때 필요한 2027 영업이익률
need_g27 = solve_min(lambda g: value(dict(SC["기본"], g27=g, m27=0.18))["tp"], 0, 3, BUYP)     # 영업이익률 18%일 때 필요한 2027 성장
rows_m = forecast(dict(SC["기본"], m27=need_m27)) if need_m27 else None
rows_g = forecast(dict(SC["기본"], g27=need_g27, m27=0.18)) if need_g27 is not None else None
PEAK = dict(rev=max(FY[y]["매출"] for y in YRS), op=max(FY[y]["영업이익"] for y in YRS), ni=max(FY[y]["지배순이익"] for y in YRS),
            rev_y=max(YRS, key=lambda y: FY[y]["매출"]), opm=max(FY[y]["영업이익"] / FY[y]["매출"] for y in YRS))
BUY = dict(buy_price=BUYP, need_per=need_per, base_eps27=Bs["rows"][1]["eps"],
           need_m27=need_m27, need_op27_m=rows_m[1]["op"] if rows_m else None,
           need_g27=need_g27, need_rev27=rows_g[1]["rev"] if rows_g else None, need_op27=rows_g[1]["op"] if rows_g else None,
           peak=PEAK, backlog=BACKLOG,
           cond=[dict(cond="지금 추정(기본) 그대로", px=cond_price(Bs["tp"])),
                 dict(cond="분기 매출 3,500억 이상 · 영업이익률 18% 이상 2개 분기 연속 + 수주잔고 6,300억 유지(낙관 경로)", px=cond_price(OUT["낙관"]["tp"]))])

TTM_OP = Q["20254Q"]["영업이익"] + M9["영업이익"]
TTM_NI = Q["20254Q"]["지배순이익"] + M9["지배순이익"]
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, sh_issued=SH_ISSUED, treasury=TREASURY,
         hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], ni=FY[y]["지배순이익"], eq=FY[y]["지배자본"]) for y in YRS},
         q={k: dict(rev=Q[k]["매출"], op=Q[k]["영업이익"], ni=Q[k]["지배순이익"]) for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q")},
         m9=M9, m9p=M9P, cash=CASH_3Q, fvpl=FVPL, eq_3q=EQ_3Q, backlog=BACKLOG, stock_comp=STOCK_COMP,
         rf=RF, mrp=MRP, beta=BETA, wacc=WACC, g_t=G_T, tax=TAX, w=(W_A, W_B), pband=PBAND, peer=PEER.to_dict("records"), peer_per_med=PEER_PER_MED,
         scen=OUT, scen_assump=SC, g_late=G_LATE, sens_p=SENS_P, sens_d=SENS_D, buy=BUY,
         ttm_op=TTM_OP, ttm_ni=TTM_NI, per_ttm=MCAP / TTM_NI, pbr=MCAP / EQ_3Q, per_27_now=PRICE / Bs["rows"][1]["eps"])
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} (08-12 {PX_ORIG:,.0f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:,.0f} {HI_SINCE_D}) 시총 {MCAP:,.0f}억 52주 {HI52:,.0f}/{LO52:,.0f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} WACC {WACC:.4f} 피어PER {PEER_PER_MED:.1f} PBR밴드 중앙 {PBAND['median']:.2f} PBR {MCAP/EQ_3Q:.2f}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"26E {r[0]['rev']:,.0f}/{r[0]['op']:,.0f} 27E {r[1]['rev']:,.0f}/{r[1]['op']:,.0f} EPS27 {r[1]['eps']:,.0f} A {v['va']:,.0f} B {v['vb']:,.0f} TP {v['tp']:,.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}")
    print("BUY", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in BUY.items() if k not in ("cond", "peak")}, [round(c["px"], -2) for c in BUY["cond"]])
