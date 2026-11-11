"""환율전략 — 모형 강건성(사양별 적정환율)과 표본 밖 백테스트(랜덤워크 대비). 실행: python valuation/환율전략/backtest.py (model.py 먼저)
백테스트: 2022-12부터 매월, 그 시점까지의 데이터로만 회귀를 다시 추정(확장 창)하고 h = 3·6·12개월 뒤 원/달러를 예측한다.
  RW  : 지금 환율 그대로(랜덤워크)
  EC  : 거시 변수는 그대로라고 보고, 지금 괴리(잔차)가 ρ^h 만큼만 남는다고 예측 — 실제로 쓸 수 있는 예측
  ORC : 미래 거시 변수의 '실제값'을 안다고 가정(정답 입력) — 경제전망을 완벽히 맞혔을 때의 상한
주의: 최종 6변수는 전체 표본으로 고른 것이라 변수 선택 단계의 미래정보가 섞여 있다(→ 처음 판 3변수·2변수 사양도 같이 시험).
출력: backtest.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import importlib.util
spec = importlib.util.spec_from_file_location("fxmodel", HERE / "model.py"); MDL = importlib.util.module_from_spec(spec); spec.loader.exec_module(MDL)
CAND, Y, NOWX, vifs, FX = MDL.CAND, MDL.Y, MDL.NOWX, MDL.vifs, MDL.FX

SPECS = {"처음 판(달러·위안·장기금리차)": ["ln_dxy", "ln_cny", "lsp"], "2변수(달러·장기금리차)": ["ln_dxy", "lsp"],
         "최종 6변수": MDL.FINAL, "최종 + 경상수지": MDL.FINAL + ["ca12"], "전체 10변수": list(CAND.columns)}

rob = {}
for k, cols in SPECS.items():
    m = sm.OLS(Y, sm.add_constant(CAND[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    fair = float(np.exp(m.params["const"] + sum(m.params[c] * NOWX[c] for c in cols)))
    rob[k] = dict(fair=fair, gap=float(np.log(FX / fair)), r2=float(m.rsquared), vif=float(max(vifs(cols).values())), n=len(cols),
                  sig=int((m.pvalues.drop("const") < 0.10).sum()))

idx = CAND.index
origins = [t for t in idx if t >= pd.Period("2022-12", "M")]
res = {}
for k in ["처음 판(달러·위안·장기금리차)", "2변수(달러·장기금리차)", "최종 6변수"]:
    cols = SPECS[k]; out = {h: dict(rw=[], ec=[], orc=[], dates=[]) for h in (3, 6, 12)}
    for t in origins:
        tr = idx[idx <= t]
        m = sm.OLS(Y.loc[tr], sm.add_constant(CAND.loc[tr, cols])).fit()
        r = m.resid; rho = float(np.corrcoef(r.values[1:], r.values[:-1])[0, 1])
        e_t = float(r.iloc[-1]); y_t = float(Y.loc[t])
        for h in (3, 6, 12):
            th = t + h
            if th not in idx: continue
            y_h = float(Y.loc[th])
            ec = y_t - (1 - rho ** h) * e_t
            orc = float(m.params["const"] + (CAND.loc[th, cols] * m.params[cols]).sum()) + rho ** h * e_t
            out[h]["rw"].append(y_h - y_t); out[h]["ec"].append(y_h - ec); out[h]["orc"].append(y_h - orc); out[h]["dates"].append(str(t))
    summ = {}
    for h, o in out.items():
        rw, ec, orc = (np.array(o[x]) for x in ("rw", "ec", "orc"))
        rmse = lambda a: float(np.sqrt((a ** 2).mean()) * 100)
        summ[h] = dict(n=len(rw), rw=rmse(rw), ec=rmse(ec), orc=rmse(orc), ec_win=float((np.abs(ec) < np.abs(rw)).mean()), orc_win=float((np.abs(orc) < np.abs(rw)).mean()),
                       ec_ratio=rmse(ec) / rmse(rw), orc_ratio=rmse(orc) / rmse(rw))
    res[k] = summ

(HERE / "backtest.json").write_text(json.dumps(dict(robust=rob, backtest=res, origins=[str(origins[0]), str(origins[-1])]), ensure_ascii=False, indent=1), encoding="utf-8")
if __name__ == "__main__":
    for k, v in rob.items(): print(f"{k:24s} fair {v['fair']:.0f} gap {v['gap']:+.1%} R2 {v['r2']:.2f} VIF {v['vif']:.1f} sig {v['sig']}/{v['n']}")
    for k, s in res.items():
        for h, v in s.items(): print(k, h, {a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()})
