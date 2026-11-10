"""미국·해외 피어 배수 (재사용용). yfinance info의 시가총액·EV·EBITDA·선행 PER·EPS를 저장한다.
주의: info는 '조회 시점' 값이다. 주말·휴장일에 조회하면 직전 거래일 종가 기준이 된다(2026-11-08 조회 = 11-06 종가).
사용: python valuation/tools/peers_us.py <출력 json> <티커1> <티커2> ...
"""
import json
import sys
from pathlib import Path

import yfinance as yf

KEYS = ["shortName", "currency", "currentPrice", "marketCap", "enterpriseValue", "ebitda", "totalRevenue", "trailingPE", "forwardPE",
        "trailingEps", "forwardEps", "enterpriseToEbitda", "enterpriseToRevenue", "revenueGrowth", "earningsGrowth", "ebitdaMargins"]

if __name__ == "__main__":
    out, ticks = Path(sys.argv[1]), sys.argv[2:]
    res = {}
    for t in ticks:
        try:
            info = yf.Ticker(t).info
            res[t] = {k: info.get(k) for k in KEYS}
        except Exception as e:
            res[t] = {"error": str(e)}
        print(t, {k: res[t].get(k) for k in ("shortName", "enterpriseToEbitda", "forwardPE", "trailingPE", "revenueGrowth")})
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
