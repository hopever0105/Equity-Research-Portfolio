"""환율전략 — 원/달러 거시 적정환율·12개월 전망·헤지 전략 (2026-11-09 기준, 신규). 실행: python valuation/환율전략/model.py
자료: ECOS 월별(국고채 10년·3년, 기준금리, CD 91일, 소비자물가, 경상수지) → ecos_monthly.csv (tools/ecos_m.py),
     FRED(미국 CPI·연방기금금리·실업률) → fred_*.csv, yfinance 일별(원/달러·달러인덱스·위안·엔·미국채 10년·3개월물·코스피·S&P500·VIX·WTI) → market_daily*.csv.
     경제전망: 연준 SEP(2026-09-16, 원문 확인) 2027 정책금리 4.1%·성장 2.4%·PCE 2.3%, 한국은행(2026-08, 언론 보도) 2027 성장 2.9%.
방법(2026-11-10 본인 지시로 거시 변수·VIF 반영):
  1) 후보 10개: ln 달러인덱스, ln 위안, 장기금리차(국고10Y−미국채10Y), 단기금리차(한은 기준금리−연방기금금리), 물가차(한국−미국 CPI 전년비),
     ln VIX(위험회피), ln WTI(교역조건), 경상수지 12개월 합, ln(코스피/S&P500)(주식자금), 미국 실업률(경기)
  2) VIF > 10 변수 제거 → 3) HAC(Newey-West, 6개월) p > 0.10 변수를 하나씩 제거(경상수지는 부호가 이론과 반대라 제외)
  4) 잔차 ADF 검정(공적분 여부), 1차 차분 회귀로 부호 확인 → 5) 시나리오 = 경제전망 입력값 × 최종 회귀식 × 잔차 절반 유지
  B. 상대 PPP는 장기 기준으로만. 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor as vif_f
from statsmodels.tsa.stattools import adfuller

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

ASOF = "2026-11-09"
E = pd.read_csv(HERE / "ecos_monthly.csv", index_col=0); E.index = pd.PeriodIndex(E.index, freq="M")


def fred(s):
    x = pd.read_csv(HERE / f"fred_{s}.csv"); x.index = pd.PeriodIndex(pd.to_datetime(x.iloc[:, 0]), freq="M")
    return x.iloc[:, 1].astype(float).groupby(level=0).mean()


CPIU, FFR, UR = fred("CPIAUCSL"), fred("FEDFUNDS"), fred("UNRATE")
D = pd.concat([pd.read_csv(HERE / "market_daily.csv", index_col=0, parse_dates=True), pd.read_csv(HERE / "market_daily2.csv", index_col=0, parse_dates=True)], axis=1)
D = D[D.index <= ASOF]
M = D.resample("ME").mean(); M.index = M.index.to_period("M")
NOW = D.ffill().iloc[-1]
FX, DXY, CNY, UST, TB3, KOSPI, SPX, VIX, WTI = (float(NOW[k]) for k in ["KRW=X", "DX-Y.NYB", "CNY=X", "^TNX", "^IRX", "^KS11", "^GSPC", "^VIX", "CL=F"])
KTB = 3.863                                            # ECOS 일별 국고채 10년 2026-11-09 (tools/macro_2026-11-09.json)
BASE_KR = float(E["base"].dropna().iloc[-1]); FF = float(FFR.iloc[-1]); CD91 = float(E["cd91"].dropna().iloc[-1])
INF_KR = float(E["cpi_kr"].pct_change(12, fill_method=None).dropna().iloc[-1] * 100); INF_US = float(CPIU.pct_change(12, fill_method=None).dropna().iloc[-1] * 100)
CA12 = float(E["ca"].dropna().iloc[-12:].sum()) / 1e5; CA12_PREV = float(E["ca"].dropna().iloc[-24:-12].sum()) / 1e5
UR_NOW = float(UR.iloc[-1])

df = pd.DataFrame({"fx": M["KRW=X"], "dxy": M["DX-Y.NYB"], "cny": M["CNY=X"], "ust": M["^TNX"], "ktb": E["ktb10"], "base": E["base"], "ff": FFR,
                   "infd": E["cpi_kr"].pct_change(12, fill_method=None) * 100 - CPIU.pct_change(12, fill_method=None) * 100,
                   "vix": M["^VIX"], "wti": M["CL=F"], "ca12": E["ca"].rolling(12).sum() / 1e5, "rel": M["^KS11"] / M["^GSPC"], "ur": UR}).loc["2015-01":"2026-10"]
NAMES = {"ln_dxy": "ln 달러인덱스", "ln_cny": "ln 위안/달러", "lsp": "장기금리차(국고10Y−미국채10Y)", "ssp": "단기금리차(기준금리−연방기금)", "infd": "물가차(한국−미국 CPI)",
         "ln_vix": "ln VIX(위험회피)", "ln_wti": "ln WTI(유가)", "ca12": "경상수지 12개월($100B)", "ln_rel": "ln 코스피/S&P500", "ur": "미국 실업률"}
CAND = pd.DataFrame({"ln_dxy": np.log(df.dxy), "ln_cny": np.log(df.cny), "lsp": df.ktb - df.ust, "ssp": df.base - df.ff, "infd": df.infd,
                     "ln_vix": np.log(df.vix), "ln_wti": np.log(df.wti.clip(lower=10)), "ca12": df.ca12, "ln_rel": np.log(df.rel), "ur": df.ur}).dropna()
Y = np.log(df.fx.reindex(CAND.index))


def vifs(cols):
    Xc = sm.add_constant(CAND[cols]).values
    return {c: float(vif_f(Xc, i + 1)) for i, c in enumerate(cols)}


def ols(cols, y=Y, X=CAND, lags=6):
    return sm.OLS(y, sm.add_constant(X[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})


ALL = list(CAND.columns)
VIF_ALL = vifs(ALL)
FULL = ols(ALL)
STEPS = []
cols = [c for c in ALL]
while max(vifs(cols).values()) > 10:
    v = vifs(cols); c = max(v, key=v.get); cols.remove(c); STEPS.append((c, "VIF", v[c]))
cols.remove("ca12"); STEPS.append(("ca12", "부호", float(FULL.params["ca12"])))   # 흑자↑ → 원화 약세: 이론과 반대(해외투자 유출과 겹침)
while True:
    m = ols(cols); p = m.pvalues.drop("const")
    if p.max() <= 0.10: break
    c = p.idxmax(); cols.remove(c); STEPS.append((c, "p값", float(p[c])))
FINAL = cols
MOD = ols(FINAL)
VIF_FINAL = vifs(FINAL)
RES = MOD.resid; SD = float(RES.std(ddof=len(FINAL) + 1)); R2 = float(MOD.rsquared); ADF_P = float(adfuller(RES)[1])
RHO = float(np.corrcoef(RES.values[1:], RES.values[:-1])[0, 1])
DIFF = sm.OLS(Y.diff().dropna(), sm.add_constant(CAND[FINAL].diff().dropna())).fit(cov_type="HAC", cov_kwds={"maxlags": 3})

NOWX = {"ln_dxy": np.log(DXY), "ln_cny": np.log(CNY), "lsp": KTB - UST, "ssp": BASE_KR - FF, "infd": INF_KR - INF_US,
        "ln_vix": np.log(VIX), "ln_wti": np.log(WTI), "ca12": CA12, "ln_rel": np.log(KOSPI / SPX), "ur": UR_NOW}


def fit(x):
    return float(np.exp(MOD.params["const"] + sum(MOD.params[c] * x[c] for c in FINAL)))


def xs(s):
    return {"ln_dxy": np.log(s["dxy"]), "ln_cny": np.log(s["cny"]), "lsp": s["lsp"], "ssp": s["ssp"], "infd": s["infd"], "ln_vix": np.log(s["vix"]),
            "ln_wti": np.log(s["wti"]), "ca12": CA12, "ln_rel": np.log(s["rel"]), "ur": s["ur"]}


FAIR_A = fit(NOWX)
BAND = (FAIR_A * np.exp(-SD), FAIR_A * np.exp(SD))
RESID_NOW = float(np.log(FX / FAIR_A))
RESID_KEEP = 0.5
REF = CAND.loc["2025-01":"2025-12", FINAL].mean()
CONTRIB = {c: float(MOD.params[c] * (NOWX[c] - REF[c])) for c in FINAL}

cpi = pd.DataFrame({"kr": E["cpi_kr"], "us": CPIU}).dropna()
base = slice("2015-01", "2019-12")
ratio = cpi["kr"] / cpi["us"]
FX_BASE = float(M["KRW=X"].loc[base].mean()); R_BASE = float(ratio.loc[base].mean())
FAIR_B = FX_BASE * float(ratio.iloc[-1]) / R_BASE
PPP_SERIES = (FX_BASE * ratio / R_BASE).loc["2015-01":]

OUTLOOK = dict(fed_2027=4.1, fed_range="3.1~4.4", us_gdp_2027=2.4, us_pce_2027=2.3, us_pce_2026=3.7, kr_gdp_2027=2.9, kr_gdp_2026=3.3)
SC = {"원화 약세(경기 둔화·위험회피)": dict(p=0.35, dxy=106.0, cny=7.00, lsp=-1.5, ssp=-1.6, infd=-0.5, vix=30.0, wti=95.0, rel=0.55, ur=4.6,
                                        why="연준 4.4%까지 추가 인상(SEP 범위 상단)·한은 인하, 반도체 경기 꺾임·코스피 추가 하락, 중동 유가 재상승으로 위험회피"),
      "기본(연준 고금리 유지·한국 완만한 둔화)": dict(p=0.45, dxy=101.0, cny=6.70, lsp=-1.0, ssp=-1.1, infd=0.0, vix=20.0, wti=82.0, rel=0.67, ur=4.1,
                                            why="연준 4.1% 유지(SEP 중앙값), 한은 3.0% 동결, 한국 성장 2.9%에서 둔화, 유가 소폭 하락"),
      "원화 강세(달러 약세·위험선호)": dict(p=0.20, dxy=96.0, cny=6.45, lsp=-0.5, ssp=-0.6, infd=0.3, vix=15.0, wti=72.0, rel=0.80, ur=4.0,
                                     why="미국 물가 안정으로 연준 인하 재개(SEP 하단 3.1%), 달러 약세·위안 강세, 코스피 회복")}
for k, s in SC.items():
    s["fx"] = fit(xs(s)) * np.exp(RESID_KEEP * RESID_NOW)
    s["chg"] = s["fx"] / FX - 1
EXP = sum(s["fx"] * s["p"] for s in SC.values())
KB = "기본(연준 고금리 유지·한국 완만한 둔화)"
BASEFX = SC[KB]["fx"]

HEDGE = (CD91 - TB3) / 100
FWD = FX * (1 + CD91 / 100) / (1 + TB3 / 100)
HEDGE_TABLE = [[k, s["fx"], s["chg"], s["chg"] - HEDGE] for k, s in SC.items()]
EXP_CHG = EXP / FX - 1

dxys = [96, 99, 101, 103, 106]; vixs = [15, 20, 25, 30, 35]
SENS = dict(dxy=dxys, vix=vixs, v=[[fit(xs(dict(SC[KB], dxy=d, vix=v))) * np.exp(RESID_KEEP * RESID_NOW) for d in dxys] for v in vixs])

YR = M["KRW=X"].groupby(M.index.year).mean()
W52 = D["KRW=X"].dropna().iloc[-260:]
CORR = D[["KRW=X", "DX-Y.NYB", "JPY=X", "CNY=X", "^KS11", "^VIX"]].resample("W").last().pct_change(fill_method=None).dropna().iloc[-104:].corr()["KRW=X"].to_dict()
VIEW = "원화 강세" if BASEFX / FX - 1 < -0.03 else ("원화 약세" if BASEFX / FX - 1 > 0.03 else "중립(박스권)")

tab = lambda m: {c: dict(coef=float(m.params[c]), p=float(m.pvalues[c]), t=float(m.tvalues[c])) for c in m.params.index if c != "const"}
R = dict(asof=ASOF, fx=FX, dxy=DXY, cny=CNY, ust=UST, ktb=KTB, tb3=TB3, cd91=CD91, base_kr=BASE_KR, ff=FF, ff_date=str(FFR.index[-1]), inf_kr=INF_KR, inf_us=INF_US,
         vix=VIX, wti=WTI, kospi=KOSPI, spx=SPX, ur=UR_NOW, ca12=CA12, ca12_prev=CA12_PREV, ca_last=float(E["ca"].dropna().iloc[-1]),
         names=NAMES, vif_all=VIF_ALL, full=tab(FULL), full_r2=float(FULL.rsquared), steps=STEPS, final=FINAL, model=tab(MOD), const=float(MOD.params["const"]), vif_final=VIF_FINAL,
         r2=R2, n=int(MOD.nobs), sd=SD, adf_p=ADF_P, rho=RHO, diff=tab(DIFF), diff_r2=float(DIFF.rsquared), nowx={k: float(v) for k, v in NOWX.items()},
         fair_a=FAIR_A, band=BAND, resid_now=RESID_NOW, resid_keep=RESID_KEEP, contrib=CONTRIB, fair_b=FAIR_B, fx_base=FX_BASE,
         cpi_kr_chg=float(cpi["kr"].iloc[-1] / cpi["kr"].loc[base].mean() - 1), cpi_us_chg=float(cpi["us"].iloc[-1] / cpi["us"].loc[base].mean() - 1),
         outlook=OUTLOOK, scen=SC, kb=KB, exp=EXP, exp_chg=EXP_CHG, base=BASEFX, view=VIEW, hedge=HEDGE, fwd=FWD, breakeven=FX * (1 + HEDGE), hedge_table=HEDGE_TABLE,
         sens=SENS, yr={int(k): float(v) for k, v in YR.items()}, hi52=float(W52.max()), hi52_d=str(W52.idxmax().date()), lo52=float(W52.min()),
         ytd_avg=float(D["KRW=X"].loc["2026"].mean()), chg_3m=FX / float(D["KRW=X"].dropna().loc[:"2026-08-09"].iloc[-1]) - 1, corr=CORR,
         ktb_hist={str(k): float(v) for k, v in E["ktb10"].loc["2025-09":].items()}, ca_hist={str(k): float(v) for k, v in E["ca"].dropna().loc["2025-01":].items()})
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
pd.DataFrame({"fx": np.exp(Y), "fitted": np.exp(MOD.fittedvalues), "resid": RES}).to_csv(HERE / "regression_monthly.csv")
PPP_SERIES.to_csv(HERE / "ppp_monthly.csv")

if __name__ == "__main__":
    print(f"FX {FX:.1f} DXY {DXY:.2f} CNY {CNY:.3f} lsp {KTB-UST:+.2f} ssp {BASE_KR-FF:+.2f} infd {INF_KR-INF_US:+.2f} VIX {VIX:.1f} WTI {WTI:.1f} rel {KOSPI/SPX:.3f} UR {UR_NOW}")
    print("VIF all", {k: round(v, 1) for k, v in VIF_ALL.items()})
    print("steps", [(a, b, round(c, 3)) for a, b, c in STEPS])
    print(MOD.summary().tables[1]); print(f"R2 {R2:.3f} n {int(MOD.nobs)} sd {SD:.3f} ADF p {ADF_P:.3f} rho {RHO:.2f} VIF {({k: round(v,1) for k,v in VIF_FINAL.items()})}")
    print("diff", {k: (round(v['coef'], 3), round(v['p'], 3)) for k, v in tab(DIFF).items()}, round(DIFF.rsquared, 2))
    print(f"fair {FAIR_A:.0f} band {BAND[0]:.0f}~{BAND[1]:.0f} resid {RESID_NOW:+.1%} PPP {FAIR_B:.0f} contrib {({k: round(v,3) for k,v in CONTRIB.items()})}")
    for k, s in SC.items(): print(k, f"{s['fx']:.0f} {s['chg']:+.1%} p{s['p']}")
    print(f"exp {EXP:.0f} {EXP_CHG:+.1%} view {VIEW} hedge {HEDGE:+.2%} fwd {FWD:.0f}")
