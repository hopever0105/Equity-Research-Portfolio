"""채권전망 — 국고채 3·10·30년, 회사채 AA- 3년 12개월 전망과 만기 전략 (2026-11-18 기준, 신규, ETF & Macro 둘째 편).
실행: python valuation/채권전망/model.py
자료: ECOS 월별(국고채 10년·3년, 기준금리, CD 91일, 소비자물가) → 환율전략/ecos_monthly.csv 재사용(2014-01~2026-10),
     yfinance 월평균(미국채 10년 ^TNX, 3개월 ^IRX, VIX, WTI) → 환율전략/market_daily*.csv 재사용, FRED 연방기금금리,
     일별 현재값(2024-01~2026-11-17: 국고 3·10·30년, 회사채 AA- 3년, CD 91일(ECOS) + 미국채 3개월·5·10·30년(yfinance)) → rates_daily.csv.
방법(2026-11-18 본인 OK):
  A. 기대가설 + 기간프리미엄: 12개월 뒤 국고 3년 = 시나리오별 기준금리 + 3년 기간프리미엄(2015-01~2026-10 국고3년 − 기준금리 평균)
  B. 월별 회귀: 국고 10년 ~ 후보 6개(기준금리, 물가 전년비, 미국채 10년, 미국채 3개월, ln VIX, ln WTI)
     → VIF > 10 제거 → HAC(Newey-West 6개월) p > 0.10 하나씩 제거 → 표본 밖 점검(2015~2022 추정, 2023-01~2026-10 예측) → 시나리오 입력
  C. 시나리오별 12개월 총수익 = 이자(캐리) + 롤다운 − 듀레이션 × 금리 변화 + ½ × 볼록성 × 금리 변화², 확률가중
출력: results.json, regression_monthly.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor as vif_f

HERE = Path(__file__).resolve().parent
FX = HERE.parents[0] / "환율전략"
sys.path.insert(0, str(HERE.parents[1]))

ASOF = "2026-11-18"
NOW_D = "2026-11-17"                                         # 일별 금리 마지막 값(11-18 ECOS 값은 다음 영업일 공개)

# ───────────────────────── 자료
E = pd.read_csv(FX / "ecos_monthly.csv", index_col=0); E.index = pd.PeriodIndex(E.index, freq="M")
D = pd.concat([pd.read_csv(FX / "market_daily.csv", index_col=0, parse_dates=True), pd.read_csv(FX / "market_daily2.csv", index_col=0, parse_dates=True)], axis=1)
M = D.resample("ME").mean(); M.index = M.index.to_period("M")
ff = pd.read_csv(FX / "fred_FEDFUNDS.csv"); ff.index = pd.PeriodIndex(pd.to_datetime(ff.iloc[:, 0]), freq="M"); FFR = ff.iloc[:, 1].astype(float)
RD = pd.read_csv(HERE / "rates_daily.csv", index_col=0, parse_dates=True)
RD = RD[RD.index <= NOW_D]
NOW = RD.iloc[-1]
KTB3, KTB10, KTB30, AA3, CD91 = (float(NOW[k]) for k in ("ktb3", "ktb10", "ktb30", "aa3", "cd91"))
UST10, UST3M, UST5 = float(NOW["us10y"]), float(NOW["us3m"]), float(NOW["us5y"])
BASE = float(E["base"].dropna().iloc[-1])
CPI_YOY = E["cpi_kr"].pct_change(12, fill_method=None) * 100
INF_NOW = float(CPI_YOY.dropna().iloc[-1]); INF_M = str(CPI_YOY.dropna().index[-1])
VIX_NOW, WTI_NOW = float(D["^VIX"].dropna().iloc[-1]), float(D["CL=F"].dropna().iloc[-1])
BASE_HIST = E["base"].dropna()
BASE_CHG = [(str(i), float(v)) for i, v in BASE_HIST[BASE_HIST.diff() != 0].loc["2024-01":].items()]

# 스프레드와 그 역사
TP3 = (E["ktb3"] - E["base"]).loc["2015-01":"2026-10"]
TP3_MEAN, TP3_SD = float(TP3.mean()), float(TP3.std())
TP3_Q75 = float(TP3.quantile(.75))
SLOPE = (E["ktb10"] - E["ktb3"]).loc["2015-01":"2026-10"]
CRED = (RD["aa3"] - RD["ktb3"])
CRED_MEAN, CRED_MAX = float(CRED.mean()), float(CRED.max())
KRUS = KTB10 - UST10

# ───────────────────────── B. 월별 회귀
df = pd.DataFrame({"ktb10": E["ktb10"], "base": E["base"], "inf": CPI_YOY, "ust10": M["^TNX"], "ust3m": M["^IRX"],
                   "ln_vix": np.log(M["^VIX"]), "ln_wti": np.log(M["CL=F"].clip(lower=10))}).loc["2015-01":"2026-10"].dropna()
NAMES = {"base": "한은 기준금리", "inf": "소비자물가 전년비", "ust10": "미국채 10년", "ust3m": "미국채 3개월", "ln_vix": "ln VIX(위험회피)", "ln_wti": "ln WTI(유가)"}
Y = df["ktb10"]; CAND = df.drop(columns="ktb10")


def vifs(cols, X=CAND):
    Xc = sm.add_constant(X[cols]).values
    return {c: float(vif_f(Xc, i + 1)) for i, c in enumerate(cols)}


def ols(cols, y=Y, X=CAND, lags=6):
    return sm.OLS(y, sm.add_constant(X[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})


ALL = list(CAND.columns)
VIF_ALL = vifs(ALL)
FULL = ols(ALL)
STEPS = []
cols = list(ALL)
while max(vifs(cols).values()) > 10:
    v = vifs(cols); c = max(v, key=v.get); cols.remove(c); STEPS.append((c, "VIF", v[c]))
while True:
    m = ols(cols); p = m.pvalues.drop("const")
    if p.max() <= 0.10:
        break
    c = p.idxmax(); cols.remove(c); STEPS.append((c, "p값", float(p[c])))
FINAL = cols
MOD = ols(FINAL)
VIF_FINAL = vifs(FINAL)
RES = MOD.resid; SD = float(RES.std(ddof=len(FINAL) + 1)); R2 = float(MOD.rsquared)

# 표본 밖 점검: 2015~2022 로 추정 → 2023-01~2026-10 예측(실제 설명변수 사용) vs 전월 값 그대로(랜덤워크)
tr, te = df.loc[:"2022-12"], df.loc["2023-01":]
MOD_TR = sm.OLS(tr["ktb10"], sm.add_constant(tr[FINAL])).fit()
pred = MOD_TR.predict(sm.add_constant(te[FINAL], has_constant="add"))
OOS_RMSE = float(np.sqrt(((pred - te["ktb10"]) ** 2).mean()))
RW_RMSE = float(np.sqrt((te["ktb10"].diff().dropna() ** 2).mean()))
OOS_BIAS = float((pred - te["ktb10"]).mean())

NOWX = {"base": BASE, "inf": INF_NOW, "ust10": UST10, "ust3m": UST3M, "ln_vix": np.log(VIX_NOW), "ln_wti": np.log(WTI_NOW)}


def fit10(x):
    return float(MOD.params["const"] + sum(MOD.params[c] * x[c] for c in FINAL))


FAIR10 = fit10(NOWX)
RESID_NOW = KTB10 - FAIR10
RESID_KEEP = 0.5
CONTRIB = {c: float(MOD.params[c] * (NOWX[c] - CAND[c].loc["2025-01":"2025-12"].mean())) for c in FINAL}

# ───────────────────────── 시나리오 (12개월 뒤, 2027-11)
SC = {"인상(물가 재상승)": dict(p=0.30, base=3.25, tp=None, inf=3.0, ust10=5.25, ust3m=4.40, vix=22.0, wti=95.0, cred=0.76,
                          why="물가 3%대 재상승·원화 약세로 한은이 한 번 더 인상(3.25%), 미국채 10년 5%대 유지"),
      "동결(기본)": dict(p=0.50, base=3.00, tp=None, inf=2.4, ust10=4.75, ust3m=4.00, vix=18.0, wti=82.0, cred=0.60,
                     why="두 번 올린 뒤 3.00% 동결, 물가 2%대 중반으로 둔화, 미국채 10년 4.75%"),
      "인하(경기 둔화)": dict(p=0.20, base=2.75, tp=None, inf=2.0, ust10=4.25, ust3m=3.50, vix=25.0, wti=72.0, cred=0.50,
                        why="경기 둔화로 한 번 인하(2.75%), 물가 목표(2%) 근처, 미국 금리 하락")}
SC["인상(물가 재상승)"]["tp"] = KTB3 - BASE                   # 인상기에는 기간프리미엄이 지금 수준(평균보다 높게) 유지된다고 본다
SC["동결(기본)"]["tp"] = TP3_MEAN
SC["인하(경기 둔화)"]["tp"] = TP3_MEAN
for k, s in SC.items():
    s["ktb3"] = s["base"] + s["tp"]                                                           # A
    x = {"base": s["base"], "inf": s["inf"], "ust10": s["ust10"], "ust3m": s["ust3m"], "ln_vix": np.log(s["vix"]), "ln_wti": np.log(s["wti"])}
    s["ktb10"] = fit10(x) + RESID_KEEP * RESID_NOW                                            # B
    s["ktb30"] = s["ktb10"] + (KTB30 - KTB10)
    s["aa3"] = s["ktb3"] + s["cred"]
EXP3 = sum(s["p"] * s["ktb3"] for s in SC.values())
EXP10 = sum(s["p"] * s["ktb10"] for s in SC.values())


# ───────────────────────── C. 12개월 총수익
def dur_conv(y, T, f=2):
    """액면(쿠폰 = 수익률) 채권의 수정듀레이션·볼록성, 반기 이표."""
    c = y / 100 / f; n = int(T * f); t = np.arange(1, n + 1) / f
    cf = np.full(n, c); cf[-1] += 1
    df_ = (1 + c) ** (-np.arange(1, n + 1))
    pv = cf * df_; P = pv.sum()
    mac = (t * pv).sum() / P
    conv = (pv * t * (t + 1 / f)).sum() / P / (1 + c) ** 2
    return mac / (1 + c), conv


def y_at(T, curve):
    """현재 곡선(CD 0.25년, 3·10·30년) 선형 보간."""
    xs, ys = [0.25, 3, 10, 30], [curve["cd"], curve["k3"], curve["k10"], curve["k30"]]
    return float(np.interp(T, xs, ys))


CUR = dict(cd=CD91, k3=KTB3, k10=KTB10, k30=KTB30)
INST = {"국고 3년": dict(T=3, y=KTB3, key="ktb3", spread=0.0), "국고 10년": dict(T=10, y=KTB10, key="ktb10", spread=0.0),
        "국고 30년": dict(T=30, y=KTB30, key="ktb30", spread=0.0), "회사채 AA- 3년": dict(T=3, y=AA3, key="aa3", spread=AA3 - KTB3)}
TR = {}
for name, ins in INST.items():
    T, y0 = ins["T"], ins["y"]
    roll = y_at(T, CUR) - y_at(T - 1, CUR)                 # 1년 지나 만기가 짧아지며 생기는 금리 하락분
    D1, C1 = dur_conv(y0, T - 1)
    row = dict(y0=y0, roll_bp=roll * 100, dur=D1, conv=C1, sc={})
    for k, s in SC.items():
        dy = (s[ins["key"]] - y0) - roll                   # 1년 뒤 같은 채권(만기 T−1)의 금리 변화
        ret = y0 / 100 - D1 * dy / 100 + 0.5 * C1 * (dy / 100) ** 2
        row["sc"][k] = dict(y1=s[ins["key"]], dy=dy, ret=ret)
    row["exp"] = sum(SC[k]["p"] * v["ret"] for k, v in row["sc"].items())
    row["worst"] = min(v["ret"] for v in row["sc"].values())
    row["vs_cash"] = row["exp"] - CD91 / 100
    TR[name] = row

# 민감도: 국고 10년 12개월 금리(기본 시나리오에서 기준금리 × 미국채 10년)
b_list = [2.75, 3.00, 3.25]; u_list = [4.25, 4.50, 4.75, 5.00, 5.25]
SENS = dict(base=b_list, ust=u_list, v=[[fit10(dict(NOWX, base=b, ust10=u, inf=2.4)) + RESID_KEEP * RESID_NOW for u in u_list] for b in b_list])

# 결론(비중): 안정적 자산배분 기준 — 나쁜 시나리오(인상)에서도 현금(CD 91일)만큼 버는지 본다
VIEW = {}
for name, r in TR.items():
    if r["vs_cash"] > 0.01 and r["worst"] >= CD91 / 100:
        VIEW[name] = "비중 확대"
    elif r["vs_cash"] > 0 and r["worst"] >= CD91 / 100 - 0.02:
        VIEW[name] = "중립"
    else:
        VIEW[name] = "비중 축소"

tab = lambda m: {c: dict(coef=float(m.params[c]), p=float(m.pvalues[c]), t=float(m.tvalues[c])) for c in m.params.index if c != "const"}
R = dict(asof=ASOF, now_d=NOW_D, ktb3=KTB3, ktb10=KTB10, ktb30=KTB30, aa3=AA3, cd91=CD91, ust10=UST10, ust3m=UST3M, ust5=UST5, base=BASE,
         inf=INF_NOW, inf_m=INF_M, vix=VIX_NOW, wti=WTI_NOW, base_chg=BASE_CHG, krus=KRUS,
         tp3_mean=TP3_MEAN, tp3_sd=TP3_SD, tp3_q75=TP3_Q75, tp3_now=KTB3 - BASE, slope_mean=float(SLOPE.mean()), slope_now=KTB10 - KTB3,
         cred_mean=CRED_MEAN, cred_max=CRED_MAX, cred_now=AA3 - KTB3,
         hi52={k: float(RD[k].iloc[-250:].max()) for k in ("ktb3", "ktb10")}, lo52={k: float(RD[k].iloc[-250:].min()) for k in ("ktb3", "ktb10")},
         names=NAMES, vif_all=VIF_ALL, full=tab(FULL), steps=STEPS, final=FINAL, model=tab(MOD), const=float(MOD.params["const"]), vif_final=VIF_FINAL,
         r2=R2, n=int(MOD.nobs), sd=SD, oos_rmse=OOS_RMSE, rw_rmse=RW_RMSE, oos_bias=OOS_BIAS, nowx={k: float(v) for k, v in NOWX.items()},
         fair10=FAIR10, resid_now=RESID_NOW, resid_keep=RESID_KEEP, contrib=CONTRIB,
         scen=SC, exp3=EXP3, exp10=EXP10, tr=TR, view=VIEW, sens=SENS,
         tp3_series={str(k): float(v) for k, v in TP3.items()}, slope_series={str(k): float(v) for k, v in SLOPE.items()},
         base_series={str(k): float(v) for k, v in E["base"].loc["2015-01":].items()}, ktb3_series={str(k): float(v) for k, v in E["ktb3"].loc["2015-01":].items()},
         ktb10_series={str(k): float(v) for k, v in E["ktb10"].loc["2015-01":].items()})
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
pd.DataFrame({"ktb10": Y, "fitted": MOD.fittedvalues, "resid": RES}).to_csv(HERE / "regression_monthly.csv")

if __name__ == "__main__":
    print(f"국고 3/10/30 {KTB3}/{KTB10}/{KTB30} AA- {AA3} CD {CD91} 기준 {BASE} 물가 {INF_NOW:.1f}({INF_M}) 미국 10Y {UST10:.2f} 3M {UST3M:.2f}")
    print(f"3년-기준 {KTB3-BASE:.2f} (평균 {TP3_MEAN:.2f} sd {TP3_SD:.2f}) 10-3 {KTB10-KTB3:.2f} (평균 {SLOPE.mean():.2f}) 신용 {AA3-KTB3:.2f} (평균 {CRED_MEAN:.2f}, 최대 {CRED_MAX:.2f})")
    print("VIF all", {k: round(v, 1) for k, v in VIF_ALL.items()}); print("steps", [(a, b, round(c, 3)) for a, b, c in STEPS])
    print(MOD.summary().tables[1]); print(f"R2 {R2:.3f} n {int(MOD.nobs)} sd {SD:.3f} OOS RMSE {OOS_RMSE:.3f} RW {RW_RMSE:.3f} bias {OOS_BIAS:+.3f}")
    print(f"10년 적정 {FAIR10:.3f} 잔차 {RESID_NOW:+.3f}")
    for k, s in SC.items():
        print(k, f"3Y {s['ktb3']:.2f} 10Y {s['ktb10']:.2f} 30Y {s['ktb30']:.2f} AA- {s['aa3']:.2f}")
    print(f"기대 3Y {EXP3:.2f} 10Y {EXP10:.2f}")
    for n, r in TR.items():
        print(n, f"y0 {r['y0']:.2f} roll {r['roll_bp']:.0f}bp D {r['dur']:.2f}", {k: round(v["ret"] * 100, 2) for k, v in r["sc"].items()}, f"기대 {r['exp']*100:.2f}% 최악 {r['worst']*100:.2f}% 현금대비 {r['vs_cash']*100:+.2f}%p", VIEW[n])
