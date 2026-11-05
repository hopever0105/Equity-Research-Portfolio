"""주간 수익률 베타 (재사용용). Blume 조정 = 0.67 × 원베타 + 0.33.
- 국내: 종목은 stock_db kor_price, 지수는 yfinance(^KS11 KOSPI, ^KQ11 KOSDAQ). KRX 요청 없음.
- 미국: 종목·지수 모두 stock_db us_price(SPY).
사용: from valuation.tools.beta import beta_kr, beta_us
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from valuation.tools.price import conn


def _beta(s, m):
    d = pd.concat([s, m], axis=1).dropna()
    r = d.resample("W-FRI").last().pct_change().dropna()
    x, y = r.iloc[:, 1].values, r.iloc[:, 0].values
    b = np.cov(y, x)[0, 1] / np.var(x, ddof=1)
    return dict(raw=float(b), blume=float(.67 * b + .33), n=int(len(r)), start=str(r.index[0].date()), end=str(r.index[-1].date()))


def beta_kr(code, end, years=3, index="^KS11"):
    import yfinance as yf
    start = (pd.Timestamp(end) - pd.DateOffset(years=years)).strftime("%Y-%m-%d")
    p = pd.read_sql("SELECT `날짜`,`종가` FROM kor_price WHERE `종목코드`=%s AND `날짜` BETWEEN %s AND %s ORDER BY `날짜`",
                    conn(), params=[code, start, end])
    s = p.set_index(pd.to_datetime(p["날짜"]))["종가"].astype(float)
    ix = yf.download(index, start=start, end=(pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), progress=False, auto_adjust=True)["Close"]
    ix = ix.iloc[:, 0] if hasattr(ix, "columns") else ix
    ix.index = pd.to_datetime(ix.index).tz_localize(None)
    return _beta(s, ix)


def beta_us(ticker, end, years=2, index="SPY"):
    start = (pd.Timestamp(end) - pd.DateOffset(years=years)).strftime("%Y-%m-%d")
    q = "SELECT `날짜`,`수정종가` FROM us_price WHERE `티커`=%s AND `날짜` BETWEEN %s AND %s ORDER BY `날짜`"
    c = conn()
    a = pd.read_sql(q, c, params=[ticker, start, end]); b = pd.read_sql(q, c, params=[index, start, end])
    s = a.set_index(pd.to_datetime(a["날짜"]))["수정종가"].astype(float); m = b.set_index(pd.to_datetime(b["날짜"]))["수정종가"].astype(float)
    return _beta(s, m)


if __name__ == "__main__":
    print(beta_us("PLTR", "2026-08-10"), beta_us("LITE", "2026-08-19"))
    print(beta_kr("003490", "2026-05-13"), beta_kr("278470", "2026-11-03"))
    for c in ["041590", "096250", "459100", "413640"]:
        print(c, beta_kr(c, "2026-08-07", 2, "^KQ11"))
