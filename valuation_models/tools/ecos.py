"""한국은행 ECOS 일별 시계열 수집 (재사용용). 키 없이 'sample' 키(요청당 10행)로 10일 단위로 나눠 받는다.
사용: python -m valuation_models.tools.ecos 731Y001 0000001 20250101 20261006 out.csv   (원/달러 매매기준율)
      817Y002 010210000 = 국고채(10년)
"""
import sys, time
from datetime import date, timedelta
import requests, pandas as pd

URL = "https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/1/10/{stat}/D/{b}/{e}/{item}"


def daily(stat, item, bgn, end, key="sample"):
    d0 = date(int(bgn[:4]), int(bgn[4:6]), int(bgn[6:]))
    d1 = date(int(end[:4]), int(end[4:6]), int(end[6:]))
    rows = []
    while d0 <= d1:
        e = min(d0 + timedelta(days=9), d1)   # 10일 안에는 영업일이 10개를 넘지 않음
        r = requests.get(URL.format(key=key, stat=stat, b=d0.strftime("%Y%m%d"), e=e.strftime("%Y%m%d"), item=item), timeout=30).json()
        for x in r.get("StatisticSearch", {}).get("row", []):
            rows.append(dict(name=x["ITEM_NAME1"], date=x["TIME"], value=float(x["DATA_VALUE"])))
        d0 = e + timedelta(days=1)
        time.sleep(0.2)
    return pd.DataFrame(rows).drop_duplicates("date")


if __name__ == "__main__":
    stat, item, b, e, out = sys.argv[1:6]
    daily(stat, item, b, e).to_csv(out, index=False, encoding="utf-8-sig")
