"""대한항공(003490) 밸류에이션 모델 — 2026-11-05 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/대한항공/model.py
원래 리포트: 2026-05-13 BUY 30,900원. 이번 기준일 2026-11-05 · 기준주가 2026-11-05 종가(stock_db).
반영한 자료(기준일까지 공시): 2025 사업보고서, 1Q26 분기보고서(05-15), 2Q26 반기보고서(08-14, 연결),
  2Q26·3Q26 영업(잠정)실적(별도, 07-13·10-15), 소규모합병 이사회 승인(08-12, 합병비율 1:0.2736432 유지),
  자기주식 소각(08-12, 보통 52주·우선 3주), 아시아나항공 2Q26 반기보고서(지배자본), 대한항공씨앤디서비스 자금보충약정(10-30 정정).
시장: 국고채 10년(ECOS)·WTI·원달러(yfinance) — valuation/tools/macro_2026-11-05.json.
방법: A. 적정 PBR (정상 ROE − g)/(COE − g) × 2026E말 합병 후 BPS 50% + B. 자기 PBR 밴드(2021-06~2026-10) 평균 50%.
      교차확인: EV/EBITDA. 증권사 목표주가는 쓰지 않음. 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr

ASOF = "2026-11-05"
ORIG = dict(date="2026-05-13", rating="BUY", tp=30900, price_txt="26,800원",
            method="PBR 2027E × 1.07배 50% · EV/EBITDA 5.5배 35% · PBR 2026E × 0.9배 15%",
            earn="증권사 추정 범위(2026F·2027F)", oil=101.2, rf=0.04044, bull=40000, bear=20000)
MAC = json.loads((HERE.parents[0] / "tools" / f"macro_{ASOF}.json").read_text(encoding="utf-8"))

# ───────────────────────── 시세
px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str}, parse_dates=["날짜"]).set_index("날짜")
px = px[px.index <= ASOF]
PRICE = float(px["종가"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["고가"].max()), float(w52["저가"].min())
PX_ORIG = float(px.loc[ORIG["date"], "종가"])
CHG_SINCE = PRICE / PX_ORIG - 1

# ───────────────────────── 주식수 (08-25 자기주식 소각 후)
SH_COMMON = 368_220_609
SH_PREF = 1_110_791
SH_PRE = SH_COMMON + SH_PREF          # 369,331,400
NEW_SH = 20_337_721                   # 합병 신주 (합병기일 2026-12-16)
SH_POST = SH_PRE + NEW_SH             # 389,669,121
MCAP = PRICE * SH_PRE / 1e8

# ───────────────────────── DART 연결
raw = pd.read_csv(HERE / "dart_fs_raw.csv", dtype=str)
per = pd.read_csv(HERE / "dart_periodic.csv", dtype=str)


def acc(year, rp, ids, sj=None, col="thstrm_amount", fsd="CFS"):
    d = raw[(raw["year"] == str(year)) & (raw["reprt"] == rp) & (raw["fs_div"] == fsd) & (raw["account_id"].isin(ids))]
    if sj:
        d = d[d["sj_div"].isin(sj)]
    if d.empty:
        return np.nan
    v = str(d.iloc[0][col]).replace(",", "")
    return float(v) / 1e8 if v not in ("", "nan", "-") else np.nan


IDS = dict(rev=["ifrs-full_Revenue"], op=["dart_OperatingIncomeLoss"], ni=["ifrs-full_ProfitLoss"],
           nic=["ifrs-full_ProfitLossAttributableToOwnersOfParent"], eqc=["ifrs-full_EquityAttributableToOwnersOfParent"],
           eq=["ifrs-full_Equity"], nci=["ifrs-full_NoncontrollingInterests"], cap=["ifrs-full_IssuedCapital"],
           cash=["ifrs-full_CashAndCashEquivalents"], cfo=["ifrs-full_CashFlowsFromUsedInOperatingActivities"],
           pbt=["ifrs-full_ProfitLossBeforeTax"], fc=["ifrs-full_FinanceCosts"])
FLOW = ("rev", "op", "ni", "nic", "pbt", "fc")


def sj_of(k):
    return ["IS", "CIS"] if k in FLOW else (["CF"] if k == "cfo" else ["BS"])


HIST = {str(y): {k: acc(y, "11011", v, sj_of(k)) for k, v in IDS.items()} for y in range(2021, 2026)}
# 2026 분기(연결): 1Q 3개월, 2Q 3개월 + 상반기 누계
Q = {}
for lab, y, rp in (("1Q25", 2025, "11013"), ("2Q25", 2025, "11012"), ("1Q26", 2026, "11013"), ("2Q26", 2026, "11012")):
    Q[lab] = {k: acc(y, rp, v, sj_of(k)) for k, v in IDS.items()}
H1_26 = {k: Q["1Q26"][k] + Q["2Q26"][k] for k in FLOW}
H1_25 = {k: Q["1Q25"][k] + Q["2Q25"][k] for k in FLOW}
EQC_2Q26 = Q["2Q26"]["eqc"]                                          # 105,125억 (2026-06-30 지배자본)

# 별도 잠정실적 (억원) — 2Q26 07-13, 3Q26 10-15 공시
SEP = {"1Q26": dict(rev=45151, op=5169, pbt=3221, ni=2427), "2Q26": dict(rev=50199, op=2618, pbt=-973, ni=-973),
       "3Q26": dict(rev=50448, op=4212, pbt=12685, ni=9297), "3Q25": dict(rev=40085, op=3763, pbt=1454, ni=919)}
SEP_EQ_3Q26 = 120039                                                 # 별도 자본총계 2026-09-30 (잠정)

# 2025 사업보고서 원문 — 연료비·감가상각
DA_2025 = 28551.6
FUEL_2025 = 67419.6
FIN_NET_2025 = HIST["2025"]["pbt"] - HIST["2025"]["op"]              # △2,901
FUEL_BBL = 3050

# 2026-06-30 차입금 (연결재무상태표, 억원)
DEBT_2Q26 = dict(st=21181.0, cur_ltd=28457.4, cur_lease=22718.1, ltd=30292.6, bond=29810.5, lease=114005.9)
DEBT_2Q26_TOT = sum(DEBT_2Q26.values())
CASH_2Q26 = Q["2Q26"]["cash"]
STD_2Q26 = 28206.8                                                   # 단기금융상품
NETDEBT = DEBT_2Q26_TOT - CASH_2Q26 - STD_2Q26
DA_H1_26 = 14513.2 + 587.7                                           # 1H26 감가상각 + 무형자산상각

# ROE (지배, 연간)
ROE = {y: HIST[y]["nic"] / ((HIST[str(int(y) - 1)]["eqc"] + HIST[y]["eqc"]) / 2) for y in ["2022", "2023", "2024", "2025"]}
ROE_N_BASE = float(np.mean([ROE[y] for y in ["2023", "2024", "2025"]]))

# 아시아나 소수주주 몫 (합병 때 지배지분으로) — 아시아나 2Q26 반기보고서 지배자본
ASIANA_EQ_2025 = 7460.1
ASIANA_EQ_2Q26 = 1325.9
ASIANA_H1_NI = -6156.0                                               # 아시아나 1H26 지배순손익
ASIANA_H1_OP = -4086.4
KAL_OWN_ASIANA = 0.6388
NCI_ADD = ASIANA_EQ_2Q26 * (1 - KAL_OWN_ASIANA)

# ───────────────────────── COE
RF = MAC["ktb10y"]["value"] / 100
BETA = beta_kr("003490", ASOF, 3)
MRP = 0.07
COE = RF + BETA["blume"] * MRP
G = 0.02

# ───────────────────────── 시장 (유가·환율)
WH = pd.Series(MAC["wti_hist"]); WH.index = pd.to_datetime(WH.index)
OIL_2025 = MAC["wti_2025avg"]
OIL_SPOT = MAC["wti"]["value"]
OIL_3Y = MAC["wti_2023_25avg"]
OIL_H1_26 = float(WH["2026-01":"2026-06"].mean())
OIL_JUL_OCT = float(WH["2026-07":"2026-10"].mean())
OIL_H2_26 = (OIL_JUL_OCT * 4 + OIL_SPOT * 2) / 6                      # 7~10월 실제 평균 + 11~12월 현물
FX_SPOT = MAC["usdkrw"]["value"]

# 1H26 실적으로 '그 밖의 비용률' 다시 맞추기 (모델과 같은 식):
#   연료비 = 2025 연료비 반기분 × 물량(+3%) × 유가비, 유류할증료 = (연료비 − 2025 유가 기준 연료비) × 전가율 50%,
#   기본 매출 = 실제 매출 − 유류할증료, 그 밖의 비용률 = (매출 − 영업이익 − 연료비) ÷ 기본 매출
OTHER_2025 = (HIST["2025"]["rev"] - HIST["2025"]["op"] - FUEL_2025) / HIST["2025"]["rev"]
FF_H1 = FUEL_2025 / 2 * 1.03
FUEL_H1_26E = FF_H1 * OIL_H1_26 / OIL_2025
SUR_H1_26E = (FUEL_H1_26E - FF_H1) * 0.5
OTHER_H1_26 = (H1_26["rev"] - H1_26["op"] - FUEL_H1_26E) / (H1_26["rev"] - SUR_H1_26E)


def forecast(oil27, oil28, pass26, pass27, other_ratio, g_rev=(0.06, 0.04, 0.04), nonop_h2=None):
    """2026E = 1H26 실제(연결) + 2H26 추정. 2H26 영업외: 3Q26 별도 영업외손익(+8,473, 원화 강세 구간) + 4Q 2025년 평균 분기치.
    2027·2028E: 매출 = 기본성장 + 유류할증료 전가, 연료비 = 2025 연료비 × 물량 × 유가비, 그 밖의 비용률 고정."""
    nonop_h2 = (SEP["3Q26"]["pbt"] - SEP["3Q26"]["op"]) + FIN_NET_2025 / 4 if nonop_h2 is None else nonop_h2
    rows = []
    # 2H26
    rev_b = HIST["2025"]["rev"] / 2 * (1 + g_rev[0])
    ff = FUEL_2025 / 2 * 1.03
    fuel = ff * OIL_H2_26 / OIL_2025
    sur = (fuel - ff) * pass26
    rev_h2 = rev_b + sur
    op_h2 = rev_h2 - fuel - other_ratio * rev_b
    ni_h2 = (op_h2 + nonop_h2) * (1 - 0.24)
    nic_h2 = ni_h2 - ASIANA_H1_NI * 0 + 0                            # 아시아나 손실은 2H에도 연결에 포함(소수주주 몫 무시, 보수적)
    eq = EQC_2Q26 + nic_h2 + NCI_ADD
    ni26 = H1_26["nic"] + nic_h2
    rev26, op26 = H1_26["rev"] + rev_h2, H1_26["op"] + op_h2
    rows.append(dict(year=2026, oil=(OIL_H1_26 + OIL_H2_26) / 2, rev=rev26, fuel=FUEL_H1_26E + fuel, sur=sur, op=op26, opm=op26 / rev26,
                     ni=ni26, roe=ni26 / ((HIST["2025"]["eqc"] + eq) / 2), eq_end=eq, ebitda=op26 + DA_H1_26 * 2, bps=eq * 1e8 / SH_POST,
                     h2=dict(rev=rev_h2, op=op_h2, ni=nic_h2, oil=OIL_H2_26, nonop=nonop_h2)))
    rev_b, vol = HIST["2025"]["rev"] * (1 + g_rev[0]), 1.03
    for yr, gr, oilp, ps in ((2027, g_rev[1], oil27, pass27), (2028, g_rev[2], oil28, pass27)):
        rev_b *= 1 + gr; vol *= 1.03
        fuel_flat = FUEL_2025 * vol
        fuel = fuel_flat * oilp / OIL_2025
        sur = (fuel - fuel_flat) * ps
        rev = rev_b + sur
        op = rev - fuel - other_ratio * rev_b
        ni = (op + FIN_NET_2025) * (1 - 0.24)
        div = 750 * SH_POST / 1e8
        roe = ni / (eq + ni / 2)
        eq = eq + ni - div
        rows.append(dict(year=yr, oil=oilp, rev=rev, fuel=fuel, sur=sur, op=op, opm=op / rev, ni=ni, roe=roe, eq_end=eq,
                         ebitda=op + DA_H1_26 * 2 * (1.04 ** (yr - 2026)), bps=eq * 1e8 / SH_POST))
    return rows


# 기본: 그 밖의 비용률 = 1H26 실제(아시아나 손실 포함)로 다시 맞춘 값, 유가는 현물 → 3년 평균
OTHER_BASE = OTHER_H1_26
BASE = dict(oil=((OIL_SPOT + OIL_3Y) / 2, OIL_3Y), pas=(.5, .7), other=OTHER_BASE)
ROE_N_MODEL = forecast(*BASE["oil"], *BASE["pas"], BASE["other"])[2]["roe"]
SCN = {
    "보수": dict(oil=(95, 85), pas=(.4, .6), other=OTHER_BASE + 0.005, roe=None, band_k=-1),
    "기본": dict(oil=BASE["oil"], pas=BASE["pas"], other=OTHER_BASE, roe=None, band_k=0),
    "낙관": dict(oil=(OIL_3Y, OIL_3Y), pas=(.6, .8), other=OTHER_BASE - 0.01, roe=ROE_N_BASE, band_k=1),
}
for k, s in SCN.items():
    if s["roe"] is None:
        s["roe"] = forecast(*s["oil"], *s["pas"], s["other"])[2]["roe"]

# ───────────────────────── B. 자기 PBR 밴드 (지배 BPS는 보고서 접수일부터 반영)
bps_pts = []
for _, r in per.iterrows():
    nm = r["report_nm"]
    if "(" not in nm or "정정" in nm:
        continue
    y, m = nm[nm.find("(") + 1: nm.find("(") + 5], nm[nm.find(".") + 1: nm.find(".") + 3]
    rp = {"03": "11013", "06": "11012", "09": "11014", "12": "11011"}[m]
    eqc = acc(y, rp, IDS["eqc"], ["BS"]); cap = acc(y, rp, IDS["cap"], ["BS"])
    if np.isnan(eqc) or np.isnan(cap):
        continue
    bps_pts.append((pd.Timestamp(r["rcept_dt"]), eqc * 1e8 / (cap * 1e8 / 5000)))
bps = pd.Series(dict(bps_pts)).sort_index()
mclose = px["종가"].resample("ME").last()
band = (mclose / bps.reindex(mclose.index, method="ffill")).dropna()
band = band[(band.index >= "2021-06-30") & (band.index <= "2026-10-31")]
BM, BS = float(band.mean()), float(band.std())
BPS_NOW = EQC_2Q26 * 1e8 / SH_PRE
PBR_NOW = PRICE / BPS_NOW


# ───────────────────────── 가치 계산
def value(s):
    sc = SCN[s]
    rows = forecast(*sc["oil"], *sc["pas"], sc["other"])
    bps_t = rows[0]["bps"]                                           # 2026E말 합병 후 BPS
    pb_a = (sc["roe"] - G) / (COE - G)
    va = pb_a * bps_t
    pb_b = BM + sc["band_k"] * BS
    vb = pb_b * bps_t
    return dict(rows=rows, roe_n=sc["roe"], pb_a=pb_a, va=va, pb_b=pb_b, vb=vb, tp=0.5 * va + 0.5 * vb, bps_t=bps_t)


S = {k: value(k) for k in SCN}
TP = int(round(S["기본"]["tp"] / 100) * 100)
UP = TP / PRICE - 1
RATING = "BUY" if UP >= .15 else ("HOLD" if UP >= -.05 else "SELL")
BPS_T = S["기본"]["bps_t"]

# 교차확인: EV/EBITDA (2026E)
EB26 = S["기본"]["rows"][0]["ebitda"]
EV = MCAP + NETDEBT + Q["2Q26"]["nci"]
EV_EBITDA = EV / EB26
IMPL_EVEBITDA_TP = (TP * SH_POST / 1e8 + NETDEBT) / EB26

# 민감도
roes = [0.04, 0.05, ROE_N_MODEL, 0.08, 0.09, ROE_N_BASE]
coes = [COE - 0.02, COE - 0.01, COE, COE + 0.01, COE + 0.02]
SENS = [[0.5 * (r - G) / (c - G) * BPS_T + 0.5 * S["기본"]["vb"] for c in coes] for r in roes]
oils = [65, 75, 85, 95, 105]
SENS_OIL = [round(forecast(x, x, .5, .7, OTHER_BASE)[1]["op"]) for x in oils]

R = dict(asof=ASOF, orig=ORIG, px_orig=PX_ORIG, chg_since=CHG_SINCE, price=PRICE, tp=TP, upside=UP, rating=RATING,
         hi52=HI52, lo52=LO52, mcap=MCAP, sh_pre=SH_PRE, sh_post=SH_POST, sh_common=SH_COMMON, new_sh=NEW_SH,
         bps_now=BPS_NOW, bps_t=BPS_T, pbr_now=PBR_NOW, div_yield=750 / PRICE, eqc_2q26=EQC_2Q26,
         hist=HIST, q=Q, h1_26=H1_26, h1_25=H1_25, sep=SEP, sep_eq_3q26=SEP_EQ_3Q26, roe=ROE, roe_n_base=ROE_N_BASE,
         asiana=dict(eq_2025=ASIANA_EQ_2025, eq_2q26=ASIANA_EQ_2Q26, h1_ni=ASIANA_H1_NI, h1_op=ASIANA_H1_OP, nci_add=NCI_ADD),
         rf=RF, beta=BETA, mrp=MRP, coe=COE, g=G,
         oil=dict(y2025=OIL_2025, spot=OIL_SPOT, avg3y=OIL_3Y, h1_26=OIL_H1_26, jul_oct=OIL_JUL_OCT, h2_26=OIL_H2_26,
                  fuel_2025=FUEL_2025, bbl=FUEL_BBL, hist={str(k.date()): v for k, v in WH.items()}),
         fx=dict(spot=FX_SPOT, y2025=MAC["usdkrw_2025avg"], ytd=MAC["usdkrw_2026ytd"]),
         other=dict(y2025=OTHER_2025, h1_26=OTHER_H1_26, base=OTHER_BASE),
         debt=DEBT_2Q26, debt_tot=DEBT_2Q26_TOT, cash=CASH_2Q26, std=STD_2Q26, netdebt=NETDEBT, ebitda_26=EB26, ev=EV,
         ev_ebitda=EV_EBITDA, impl_ev_ebitda_tp=IMPL_EVEBITDA_TP, fin_net=FIN_NET_2025, roe_n_model=ROE_N_MODEL,
         band=dict(mean=BM, sd=BS, min=float(band.min()), max=float(band.max()), series={str(k.date()): float(v) for k, v in band.items()}),
         scen={k: dict(tp=v["tp"], va=v["va"], vb=v["vb"], pb_a=v["pb_a"], pb_b=v["pb_b"], roe_n=v["roe_n"], rows=v["rows"],
                       bps_t=v["bps_t"], upside=v["tp"] / PRICE - 1) for k, v in S.items()},
         scen_assump={k: dict(oil=v["oil"], pas=v["pas"], other=v["other"], roe=v["roe"], band_k=v["band_k"]) for k, v in SCN.items()},
         sens=dict(roe=roes, coe=coes, v=SENS), sens_oil=dict(oil=oils, op2027=SENS_OIL))
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:,.0f} (orig-date {PX_ORIG:,.0f}, {CHG_SINCE:+.1%})  BPS now {BPS_NOW:,.0f} 2026E post {BPS_T:,.0f}  PBR {PBR_NOW:.2f}")
    print("1H26", {k: round(v) for k, v in H1_26.items()}, "1H25", {k: round(v) for k, v in H1_25.items()})
    print("other ratio 2025", round(OTHER_2025, 4), "1H26", round(OTHER_H1_26, 4), "base", round(OTHER_BASE, 4))
    print("oil 2025", round(OIL_2025, 1), "H1", round(OIL_H1_26, 1), "Jul-Oct", round(OIL_JUL_OCT, 1), "spot", round(OIL_SPOT, 1), "3y", round(OIL_3Y, 1))
    print("beta", BETA, "COE", round(COE, 4), "RF", RF)
    print("band", round(BM, 3), round(BS, 3), round(band.min(), 2), round(band.max(), 2), len(band))
    for k, v in S.items():
        print(k, "roe", round(v["roe_n"], 4), round(v["pb_a"], 3), round(v["va"]), round(v["pb_b"], 3), round(v["vb"]), "TP", round(v["tp"]))
        for r in v["rows"]:
            print("   ", r["year"], round(r["oil"], 1), round(r["rev"]), round(r["op"]), f"{r['opm']:.1%}", round(r["ni"]), f"{r['roe']:.1%}", round(r["bps"]))
    print("TP", TP, f"{UP:+.1%}", RATING, "EV/EBITDA", round(EV_EBITDA, 2), "implied", round(IMPL_EVEBITDA_TP, 2), "netdebt", round(NETDEBT))
    print("sens oil", SENS_OIL)
