"""에이피알(278470) 밸류에이션 모델 (신규). 단위: 억원(주당·배수·비율 제외). 실행: python valuation/에이피알/model.py
기준일 2026-11-04(수) · 기준주가 직전 거래일 2026-11-03 종가(stock_db). 그날까지 공개된 공시만:
  2026 반기보고서(08-14), 3Q26 연결 영업(잠정)실적(10-30), 자회사 에이피알팩토리 흡수합병 결정(09-09), 중간배당(07-16).
방법: A. DCF(FCFF, 2027~2036 성장 감속 + 마진 정상화) 50% + B. 자기 PER 밴드(상장 2024-02 이후 TTM PER 평균) × 2027E EPS 50%.
      교차확인: 같은 날 K-뷰티 피어 PER(peers_kr.csv). 증권사 목표주가는 쓰지 않음. 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr

ASOF = "2026-11-03"
px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str}, parse_dates=["날짜"]).set_index("날짜")
px = px[px.index <= ASOF]
PRICE = float(px["종가"].iloc[-1])                                   # 246,500
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["고가"].max()), float(w52["저가"].min())
HI52_D, LO52_D = str(w52["고가"].idxmax().date()), str(w52["저가"].idxmin().date())
SH = 37_438_155                                                       # 발행주식 = 유통주식(자기주식 0, 2026 반기보고서)
MCAP = PRICE * SH / 1e8

# ───────────────────────── 분기 실적 (DART 연결, 억원). 3Q26은 잠정실적(10-30)
fs = pd.read_csv(HERE / "fs_summary_2026-11-03.csv").set_index("기간")
Q = {}
for y in range(2021, 2027):
    for q in ("1Q", "2Q", "3Q"):
        k = f"{y}{q}"
        if k in fs.index:
            Q[k] = dict(rev=fs.loc[k, "매출"], op=fs.loc[k, "영업이익"], ni=fs.loc[k, "지배순이익"])
    if f"{y}FY" in fs.index:
        Q[f"{y}4Q"] = {m: fs.loc[f"{y}FY", c] - sum(Q[f"{y}{q}"][m] for q in ("1Q", "2Q", "3Q"))
                       for m, c in (("rev", "매출"), ("op", "영업이익"), ("ni", "지배순이익"))}
Q["20263Q"] = dict(rev=7731.15, op=1606.40, ni=1101.88)                # 잠정(10-30)
ANN = {str(y): {m: sum(Q[f"{y}{q}"][m] for q in ("1Q", "2Q", "3Q", "4Q")) for m in ("rev", "op", "ni")} for y in (2023, 2024, 2025)}
EQ_2Q26 = float(fs.loc["20262Q", "지배자본"]); CASH_2Q26 = float(fs.loc["20262Q", "현금"])
EQ_2025 = float(fs.loc["2025FY", "지배자본"])
TTM_NI = sum(Q[k]["ni"] for k in ("20254Q", "20261Q", "20262Q", "20263Q"))
TTM_OP = sum(Q[k]["op"] for k in ("20254Q", "20261Q", "20262Q", "20263Q"))
TTM_REV = sum(Q[k]["rev"] for k in ("20254Q", "20261Q", "20262Q", "20263Q"))
PER_TTM = MCAP / TTM_NI
PBR = MCAP / EQ_2Q26
ROE_TTM = TTM_NI / ((EQ_2025 + EQ_2Q26) / 2)
NI_RATIO = sum(Q[f"2026{q}"]["ni"] for q in ("1Q", "2Q", "3Q")) / sum(Q[f"2026{q}"]["op"] for q in ("1Q", "2Q", "3Q"))  # 9M26 순이익/영업이익 0.733

# 순현금: 2Q26 현금 + 단기금융자산 - 금융부채(stock_db kor_fs, peers_kr.csv와 같은 값)
peers = pd.read_csv(HERE / "peers_kr.csv", dtype={"code": str})
me = peers[peers["code"] == "278470"].iloc[0]
NET_CASH = float(me["cash"] + me["sti"] - me["fdebt_c"] - me["fdebt_nc"])

# ───────────────────────── COE
RF = float(pd.read_csv(HERE / "rf_ktb10y.csv")["value"].iloc[-1]) / 100        # 국고10Y 2026-11-03 4.001%
BETA = beta_kr("278470", ASOF, 3)
MRP = 0.07
COE = RF + BETA["blume"] * MRP
TAX = 0.24
ROIC = 0.40                                                            # 재투자율 = 성장률 ÷ ROIC (2025 세후영업이익 ÷ 영업투하자본 근사, 3장 표)


def project(g27, opm27, opm_t, g_path_tail=(0.22, 0.16, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03), q4_uplift=1.15):
    """2026E = 9M 실적 + 4Q26E(3Q26 × 계절 상향). 2027E~2036E 매출 감속, 영업이익률은 opm27 → opm_t 선형."""
    q4 = dict(rev=Q["20263Q"]["rev"] * q4_uplift)
    q4["op"] = q4["rev"] * Q["20263Q"]["op"] / Q["20263Q"]["rev"]
    q4["ni"] = q4["op"] * NI_RATIO
    y26 = {m: sum(Q[f"2026{q}"][m] for q in ("1Q", "2Q", "3Q")) + q4[m] for m in ("rev", "op", "ni")}
    gs = [g27] + list(g_path_tail)
    opms = list(np.linspace(opm27, opm_t, len(gs)))
    rows, rev = [], y26["rev"]
    for i, (g, m) in enumerate(zip(gs, opms)):
        rev *= 1 + g
        op = rev * m; nopat = op * (1 - TAX); fcf = nopat * (1 - g / ROIC)
        rows.append(dict(year=2027 + i, g=g, rev=rev, opm=m, op=op, ni=op * (1 - TAX) * 1.0 + 0, nopat=nopat, fcf=fcf))
    return y26, q4, rows


def dcf(rows, wacc, g=0.03):
    pv = sum(r["fcf"] / (1 + wacc) ** (i + 1 - 10 / 12) for i, r in enumerate(rows))      # 기준일 11월 → 2027년 현금흐름은 약 1.2년 뒤 중간
    tv = rows[-1]["fcf"] * (1 + g) / (wacc - g) / (1 + wacc) ** (len(rows) - 10 / 12)
    return (pv + tv + NET_CASH) * 1e8 / SH, pv, tv


# ───────────────────────── B. 자기 PER 밴드 (TTM 지배순이익은 보고서 접수일부터 반영)
per = pd.read_csv(HERE / "dart_periodic.csv", dtype=str)
ttm_pts = []
order = [f"{y}{q}" for y in range(2021, 2027) for q in ("1Q", "2Q", "3Q", "4Q")]
grw_pts = []
ttm_of = lambda i: sum(Q[order[j]]["ni"] for j in range(i - 3, i + 1))
for _, r in per.iterrows():
    nm = r["report_nm"]
    if "(" not in nm or "정정" in nm:
        continue
    y, m = nm[nm.find("(") + 1: nm.find("(") + 5], nm[nm.find(".") + 1: nm.find(".") + 3]
    k = f"{y}{ {'03': '1Q', '06': '2Q', '09': '3Q', '12': '4Q'}[m] }".replace(" ", "")
    i = order.index(k) if k in order else -1
    if i < 3 or any(order[j] not in Q for j in range(i - 7 if i >= 7 else i - 3, i + 1)):
        continue
    ttm_pts.append((pd.Timestamp(r["rcept_dt"]), ttm_of(i)))
    if i >= 7:
        grw_pts.append((pd.Timestamp(r["rcept_dt"]), ttm_of(i) / ttm_of(i - 4) - 1))
i3 = order.index("20263Q")
ttm_pts.append((pd.Timestamp("2026-10-30"), TTM_NI))                   # 3Q26 잠정
grw_pts.append((pd.Timestamp("2026-10-30"), TTM_NI / ttm_of(i3 - 4) - 1))
ttm = pd.Series(dict(ttm_pts)).sort_index(); grw = pd.Series(dict(grw_pts)).sort_index()
wk = px["종가"].resample("W-FRI").last()
wk = wk[wk.index <= pd.Timestamp(ASOF) + pd.Timedelta(days=6)]
band_all = (wk * SH / 1e8 / ttm.reindex(wk.index, method="ffill")).dropna()
# 자기 PER–이익성장률 회귀: 주간 TTM PER = a + b × (그때 알려진 TTM 지배순이익 YoY)
gw = grw.reindex(band_all.index, method="ffill").dropna()
REG_B, REG_A = np.polyfit(gw.values, band_all.loc[gw.index].values, 1)
REG_R2 = float(np.corrcoef(gw.values, band_all.loc[gw.index].values)[0, 1] ** 2)
REG_N = int(len(gw)); REG_GMIN, REG_GMAX = float(gw.min()), float(gw.max())
pe_at = lambda g: float(REG_A + REG_B * min(max(g, REG_GMIN), REG_GMAX))   # 표본 밖은 끝값으로 자름
# 상장 초기(2024)는 이익 규모가 지금의 1/4이라 배수가 40~64배로 높았다 → 지금 이익 규모와 성장 국면인 최근 1년만 쓴다
band = band_all[band_all.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
BM, BSD = float(band.mean()), float(band.std())
BM_ALL = float(band_all.mean())
RUNRATE_G = Q["20263Q"]["rev"] * 1.15 * 4 / (sum(Q[f"2026{q}"]["rev"] for q in ("1Q", "2Q", "3Q")) + Q["20263Q"]["rev"] * 1.15) - 1

# 2027E 성장: 4Q26E 분기 매출이 그대로만 가도 +18%(연환산 효과). 기본은 여기에 분기 성장 소폭(+1%/분기) → +20%
SCN = {"보수": dict(g27=0.08, opm27=0.18, opm_t=0.15, per_k=-1, wacc_add=0.01),
       "기본": dict(g27=0.20, opm27=0.20, opm_t=0.17, per_k=0, wacc_add=0.0),
       "낙관": dict(g27=0.35, opm27=0.23, opm_t=0.20, per_k=0.5, wacc_add=-0.005)}
OUT = {}
for k, s in SCN.items():
    y26, q4, rows = project(s["g27"], s["opm27"], s["opm_t"])
    wacc = COE + s["wacc_add"]
    va, pv, tv = dcf(rows, wacc)
    eps27 = rows[0]["op"] * NI_RATIO * 1e8 / SH
    eps26 = y26["ni"] * 1e8 / SH
    g_eps = eps27 / eps26 - 1
    pe_b = (1 - 0.03 / ROIC) / (wacc - 0.03)          # 정상 상태 적정 PER(성장 3%, 재투자율 g/ROIC) — 고성장 구간 가치는 A가 담음
    vb = pe_b * eps27
    OUT[k] = dict(y26=y26, q4=q4, rows=rows, wacc=wacc, va=va, pv=pv, tv=tv, eps26=eps26, eps27=eps27, g_eps=g_eps, pe_b=pe_b, vb=vb,
                  tp=0.5 * va + 0.5 * vb)
TP = int(round(OUT["기본"]["tp"] / 1000) * 1000)
UP = TP / PRICE - 1
RATING = "BUY" if UP >= .15 else ("HOLD" if UP >= -.05 else "SELL")
B0 = OUT["기본"]

# 민감도
y26b, _, rows_b = project(0.20, 0.20, 0.17)
waccs = [COE - 0.01, COE - 0.005, COE, COE + 0.01, COE + 0.02]
gts = [0.02, 0.025, 0.03, 0.035]
SENS_W = [[dcf(rows_b, w, g)[0] for w in waccs] for g in gts]
g27s = [0.15, 0.20, 0.30, 0.40, 0.50]; opms = [0.18, 0.20, 0.22, 0.24]
def tp_of(g, m):
    y26, _, rows = project(g, m, m - 0.03)
    e27 = rows[0]["op"] * NI_RATIO * 1e8 / SH
    return 0.5 * dcf(rows, COE)[0] + 0.5 * (1 - 0.03 / ROIC) / (COE - 0.03) * e27


SENS_G = [[tp_of(g, m) for g in g27s] for m in opms]

R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, hi52=HI52, lo52=LO52, hi52_d=HI52_D, lo52_d=LO52_D,
         sh=SH, mcap=MCAP, q=Q, ann=ANN, eq_2q26=EQ_2Q26, eq_2025=EQ_2025, cash_2q26=CASH_2Q26, net_cash=NET_CASH,
         ttm=dict(rev=TTM_REV, op=TTM_OP, ni=TTM_NI), per_ttm=PER_TTM, pbr=PBR, roe_ttm=ROE_TTM, ni_ratio=NI_RATIO,
         rf=RF, beta=BETA, mrp=MRP, coe=COE, tax=TAX, roic=ROIC,
         band=dict(mean=BM, sd=BSD, min=float(band.min()), max=float(band.max()), mean_all=BM_ALL,
                   series={str(k.date()): float(v) for k, v in band_all.items()}), runrate_g=RUNRATE_G,
         reg=dict(a=float(REG_A), b=float(REG_B), r2=REG_R2, n=REG_N, gmin=REG_GMIN, gmax=REG_GMAX,
                  pts={str(k.date()): float(v) for k, v in grw.items()}),
         scen={k: dict(tp=v["tp"], va=v["va"], vb=v["vb"], pe_b=v["pe_b"], eps27=v["eps27"], eps26=v["eps26"], g_eps=v["g_eps"], wacc=v["wacc"], y26=v["y26"], q4=v["q4"],
                       rows=v["rows"], pv=v["pv"], tv=v["tv"], upside=v["tp"] / PRICE - 1) for k, v in OUT.items()},
         scen_assump=SCN, sens_w=dict(wacc=waccs, g=gts, v=SENS_W), sens_g=dict(g27=g27s, opm=opms, v=SENS_G),
         peers=peers.to_dict("records"))
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:,.0f} mcap {MCAP:,.0f} TTM NI {TTM_NI:,.0f} PER {PER_TTM:.1f} PBR {PBR:.1f} ROE {ROE_TTM:.1%} netcash {NET_CASH:,.0f}")
    print("beta", BETA, "COE", round(COE, 4), "band", round(BM, 1), round(BSD, 1), round(band.min(), 1), round(band.max(), 1))
    for k, v in OUT.items():
        print(k, "2026E", {m: round(x) for m, x in v["y26"].items()}, "EPS27", round(v["eps27"]), "A", round(v["va"]), "B", round(v["vb"]), f"PE {v['pe_b']:.1f}", "TP", round(v["tp"]),
              f"TV share {v['tv']/(v['pv']+v['tv']):.0%}")
    print("TP", TP, f"{UP:+.1%}", RATING)
    print("reg PER = %.1f + %.1f*g  R2 %.2f n %d g[%.2f,%.2f]" % (REG_A, REG_B, REG_R2, REG_N, REG_GMIN, REG_GMAX), {k: round(v, 2) for k, v in grw.items()})
    for k, v in OUT.items():
        print(k, "eps26", round(v["eps26"]), "eps27", round(v["eps27"]), f"g {v['g_eps']:+.1%}", f"PE {v['pe_b']:.1f}")
