"""재조사용 시장 데이터 (재사용용). 국고채 10년(ECOS), 미국채 10년·WTI·원달러(yfinance).
사용: python -m valuation.tools.macro 2026-11-05  → valuation/tools/macro_<날짜>.json
FRED는 2026-11-05 접속 지연으로 yfinance를 쓴다(^TNX = 미국채 10년 수익률 ×1, CL=F = WTI 근월물).
"""
import json
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from valuation.tools.ecos import daily

BASE = Path(__file__).resolve().parent


def last(sym, start, end):
    d = yf.download(sym, start=start, end=(pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), progress=False, auto_adjust=False)
    s = d["Close"].squeeze().dropna()
    return s


def collect(asof):
    out = {"asof": asof}
    k = daily("817Y002", "010210000", (pd.Timestamp(asof) - pd.Timedelta(days=20)).strftime("%Y%m%d"), asof.replace("-", ""))
    out["ktb10y"] = dict(date=str(k["date"].iloc[-1]), value=float(k["value"].iloc[-1]))
    for key, sym in (("ust10y", "^TNX"), ("wti", "CL=F"), ("usdkrw", "KRW=X")):
        s = last(sym, "2023-01-01", asof)
        out[key] = dict(date=str(s.index[-1].date()), value=float(s.iloc[-1]))
        if key == "wti":
            out["wti_hist"] = {str(i.date()): float(v) for i, v in s.resample("ME").mean().items()}
            out["wti_2025avg"] = float(s["2025"].mean())
            out["wti_2023_25avg"] = float(s["2023":"2025"].mean())
            out["wti_2026ytd"] = float(s["2026"].mean())
        if key == "usdkrw":
            out["usdkrw_2025avg"] = float(s["2025"].mean())
            out["usdkrw_2026ytd"] = float(s["2026"].mean())
    p = BASE / f"macro_{asof}.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    o = collect(sys.argv[1])
    print({k: v for k, v in o.items() if k != "wti_hist"})
