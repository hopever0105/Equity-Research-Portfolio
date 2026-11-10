"""맥쿼리인프라(088980) 밸류에이션 모델 — 2026-11-06 재조사. 단위: 억원(주당·비율 제외). 실행: python valuation/맥쿼리인프라/model.py
원래 리포트: 2026-05-13 BUY 14,000원(당시 11,220원). 기준일 2026-11-06(금) · 기준주가 11-06 종가(네이버 기반 FinanceDataReader;
  stock_db에는 이 종목 이력이 2주뿐이라 쓰지 않음).
자료: MKIF 3Q26 IR 자료·분기 자산운용보고서(2026-10-30, mkif.com) → docs/, 분배금 이력(IR 부록), 국고채 10년(ECOS) → tools/macro_2026-11-06.json.
     증권사 자료는 가정 교차확인에만: KB증권(2026-06-30, 목표 13,000원, 2026·2027 DPS 700원), 삼성증권(2026-04-03, 목표 13,600원).
방법: A. 배당할인모형(DDM, 2H26~2030 명시 + 영구성장) 60% + B. 배당수익률 스프레드 밴드(국고10Y + 2017-03~ 평균 스프레드) 40%.
출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.report_kit import rating_of

ASOF = "2026-11-06"
ORIG = dict(date="2026-05-13", rating="BUY", tp=14000, px=11220, dps26=760,
            method="DDM·배당수익률 밴드 병행(증권사 NPV 목표가 참고)")
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-06.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100                     # 3.853%
MRP = 0.07

# ───────────────────────── 시세 (네이버 기반 FDR, 2016~)
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["date"], "Close"])
SH = 478_921_993                                      # 발행주식수 (2026-09말 자본금 3조 2,972억 ÷ 액면 기준, 원래 리포트와 같음)
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적 (IR 3Q26, 단독·미감사, 백만원 → 억원)
Q3 = dict(rev=754.33, int_inc=713.09, div_inc=41.22, exp=168.73, fee=105.48, int_exp=51.15, ni=585.60, eps=122,
          rev_p=774.62, ni_p=599.81, eps_p=125)
M9 = dict(rev=3354.54, int_inc=2116.71, div_inc=1237.72, exp=518.44, fee=339.01, int_exp=144.50, ni=2836.10, eps=592,
          rev_p=3543.67, div_inc_p=1430.08, ni_p=3035.19, eps_p=634)
BS = {"2025-12": dict(assets=54807.90, invest=46246.89, loans=24391.51, equity_sec=21606.53, int_recv=8516.23, bonds=3497.23, ltd=1070.00,
                      liab=4744.06, cap=32972.09),
      "2026-09": dict(assets=55450.31, invest=45802.89, loans=23898.41, equity_sec=21623.56, int_recv=9606.71, bonds=3511.53, ltd=2380.00,
                      liab=6046.50, cap=32972.09)}
for v in BS.values():
    v["equity"] = v["assets"] - v["liab"]; v["debt"] = v["bonds"] + v["ltd"]
DEBT_LIMIT = 32972.09                                  # 개정 민투법: 자본금의 100%
DEBT_COMMIT = 9891                                     # 약정 9,891억 중 5,898억 인출
# 분배금 이력 (원/주, IR 부록) — 연간
DPS_HIST = {2016: 400, 2017: 540, 2018: 622, 2019: 700, 2020: 720, 2021: 750, 2022: 770, 2023: 775, 2024: 760, 2025: 760}
DPS_1H26 = 350
# 포트폴리오 (2026-06-30, 투자금액 십억원, mkif.com)
PORT = [("인천대교", 295.4, "유료도로"), ("영산클린에너지(해양에너지)", 322.5, "도시가스"), ("보문클린에너지(서라벌)", 87.1, "도시가스"),
        ("그린디지털인프라(하남 데이터센터)", 423.0, "데이터센터"), ("비엔씨티(부산신항 2-3)", 259.4, "항만"), ("씨엔씨티에너지", 183.2, "도시가스"),
        ("동서울지하도로(건설중)", 214.7, "유료도로"), ("천안논산고속도로", 197.1, "유료도로"), ("서울춘천고속도로", 166.0, "유료도로"),
        ("경수고속도로(용인서울)", 151.1, "유료도로"), ("인천김포고속도로", 128.1, "유료도로"), ("부산신항2배후도로", 110.7, "유료도로"),
        ("마창대교", 112.8, "유료도로"), ("동북선 도시철도(건설중)", 82.7, "철도"), ("신공항하이웨이(인천공항고속도로)", 75.3, "유료도로"),
        ("광주순환도로투자", 74.6, "유료도로"), ("수정산투자", 47.1, "유료도로"), ("광주순환도로", 28.9, "유료도로"), ("우면산인프라웨이", 20.3, "유료도로")]
PORT_TYPE = {}
for _, v, t in PORT:
    PORT_TYPE[t] = PORT_TYPE.get(t, 0) + v

# ───────────────────────── 할인율
BETA_RAW, BETA_BLUME = 0.003, 0.332                    # 3년 주간, KOSPI 대비 (scratch beta_run, FDR 종가)
COE = RF + BETA_BLUME * MRP                            # 6.18%

# ───────────────────────── 시나리오 (2H26 분배금, 2027, 2028~2030, 영구성장, COE 가산)
SC = {"보수": dict(d2h26=340, d27=680, d28=700, d30=700, g=0.0, dcoe=0.005, sp=+1),
      "기본": dict(d2h26=350, d27=700, d28=740, d30=760, g=0.01, dcoe=0.0, sp=0),
      "낙관": dict(d2h26=350, d27=740, d28=770, d30=790, g=0.015, dcoe=-0.003, sp=-1)}
T0 = pd.Timestamp(ASOF)


def dps_path(s):
    """연도별 연간 분배금. 2H26은 2027-03 지급(기준일부터 0.35년). 2027 이후 반기 지급을 연 중간(해당연도 9월)으로 근사."""
    d29 = (s["d28"] + s["d30"]) / 2
    return [("2H26", s["d2h26"], 0.35), ("2027", s["d27"], 1.0), ("2028", s["d28"], 2.0), ("2029", d29, 3.0), ("2030", s["d30"], 4.0)]


def ddm(s, coe=None):
    k = (coe if coe is not None else COE) + s["dcoe"]
    path = dps_path(s)
    pv = sum(d / (1 + k) ** t for _, d, t in path)
    tv = path[-1][1] * (1 + s["g"]) / (k - s["g"])
    pv_tv = tv / (1 + k) ** path[-1][2]
    return pv + pv_tv, pv, pv_tv, k


# ───────────────────────── B. 배당수익률 스프레드 밴드
SPR = pd.read_csv(HERE / "yield_spread_monthly.csv", index_col=0, parse_dates=True)
S17 = SPR[SPR.index >= "2017-03-01"]["spread"]
SP_MEAN, SP_SD = float(S17.mean()), float(S17.std())
SP_NOW = DPS_HIST[2025] / PRICE * 100 - RF * 100
SP_NOW_700 = 700 / PRICE * 100 - RF * 100


def band_val(s):
    sp = SP_MEAN + s["sp"] * SP_SD
    y = RF * 100 + sp
    fwd = s["d27"]                                       # 향후 1년(2H26 + 1H27) ≈ 2027 연간 분배금
    return fwd / (y / 100), y, sp


OUT = {}
for k_, s in SC.items():
    va, pv, pvtv, k = ddm(s)
    vb, y, sp = band_val(s)
    OUT[k_] = dict(va=va, pv=pv, pv_tv=pvtv, coe=k, vb=vb, fair_yield=y, spread=sp, tp=0.6 * va + 0.4 * vb, path=dps_path(s))
    OUT[k_]["upside"] = OUT[k_]["tp"] / PRICE - 1
B = OUT["기본"]
TP = int(round(B["tp"], -2))
UP = TP / PRICE - 1
RATING = rating_of(UP)

# 민감도: COE × 영구성장 (A만), 2027 DPS × 적정 스프레드 (B만)
SENS_A = dict(coe=[0.055, 0.0618, 0.065, 0.07, 0.075], g=[0.0, 0.005, 0.01, 0.015])
SENS_A["v"] = [[ddm(dict(SC["기본"], g=g, dcoe=0.0), c)[0] for c in SENS_A["coe"]] for g in SENS_A["g"]]
SENS_B = dict(dps=[660, 680, 700, 720, 760], sp=[SP_MEAN - SP_SD, SP_MEAN - SP_SD / 2, SP_MEAN, SP_MEAN + SP_SD / 2, SP_MEAN + SP_SD])
SENS_B["v"] = [[d / ((RF * 100 + sp) / 100) for sp in SENS_B["sp"]] for d in SENS_B["dps"]]
# 목표가 전체 민감도: 2027 DPS × COE
SENS_T = dict(dps=[660, 700, 740, 760], coe=[0.055, 0.0618, 0.07])
SENS_T["v"] = [[0.6 * ddm(dict(SC["기본"], d27=d, d28=d * 740 / 700, d30=d * 760 / 700), c)[0] + 0.4 * d / ((RF * 100 + SP_MEAN) / 100)
                for c in SENS_T["coe"]] for d in SENS_T["dps"]]

# 지표
DY_TRAIL = 760 / PRICE
DY_FWD = 700 / PRICE
EPS_ANN = M9["eps"] / 3 * 4                             # 9M EPS 연환산 (분배 재원 확인용)
NAV_PS = BS["2026-09"]["equity"] * 1e8 / SH
PBR = PRICE / NAV_PS
TP_YIELD = 700 / TP

R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, hi52=HI52, lo52=LO52, px_orig=PX_ORIG,
         chg_since=PRICE / PX_ORIG - 1, orig=ORIG, rf=RF, mrp=MRP, beta_raw=BETA_RAW, beta=BETA_BLUME, coe=COE,
         q3=Q3, m9=M9, bs=BS, debt_limit=DEBT_LIMIT, debt_commit=DEBT_COMMIT, dps_hist=DPS_HIST, dps_1h26=DPS_1H26,
         port=PORT, port_type=PORT_TYPE, sp_mean=SP_MEAN, sp_sd=SP_SD, sp_now=SP_NOW, sp_now_700=SP_NOW_700,
         spread_series={str(k.date()): float(v) for k, v in SPR["spread"].items()},
         yld_series={str(k.date()): float(v) for k, v in SPR["yld"].items()}, ktb_series={str(k.date()): float(v) for k, v in SPR["ktb"].items()},
         scen=OUT, scen_assump=SC, sens_a=SENS_A, sens_b=SENS_B, sens_t=SENS_T, dy_trail=DY_TRAIL, dy_fwd=DY_FWD,
         eps_ann=EPS_ANN, nav_ps=NAV_PS, pbr=PBR, tp_yield=TP_YIELD,
         refs=[("KB증권", "2026-06-30", "Buy", 13000, "COE 상승·분배금 감소로 하향, 2026·2027 DPS 700원, 2H27~2028 회복"),
               ("삼성증권", "2026-04-03", "Buy", 13600, "Corporate day, 차입여력 확대로 유상증자 위험 감소, 2026 EPS 722원")])
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} (05-13 {PX_ORIG:,.0f}, {PRICE/PX_ORIG-1:+.1%}) 52주 {HI52:,.0f}/{LO52:,.0f} 시총 {MCAP:,.0f}억 COE {COE:.4f}")
    print(f"스프레드 평균 {SP_MEAN:.2f} σ {SP_SD:.2f} 현재(760) {SP_NOW:.2f} (700) {SP_NOW_700:.2f}  NAV/주 {NAV_PS:,.0f} PBR {PBR:.2f}")
    for k_, v in OUT.items():
        print(k_, f"A {v['va']:,.0f} (TV비중 {v['pv_tv']/v['va']:.0%}, k {v['coe']:.4f}) B {v['vb']:,.0f} (적정수익률 {v['fair_yield']:.2f}%) TP {v['tp']:,.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "TP 기준 수익률", f"{TP_YIELD:.2%}")
