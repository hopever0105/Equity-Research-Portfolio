"""한국은행 ECOS 월별 시계열 (재사용용). 키 없이 'sample' 키(요청당 10행)로 10개월씩 나눠 받는다.
사용: from valuation.tools.ecos_m import monthly; monthly("721Y001", "5050000", "201501", "202610")
  721Y001 5050000 = 국고채 10년(월평균), 721Y001 2010000 = CD 91일, 901Y009 0 = 소비자물가 총지수, 301Y013 000000 = 경상수지(백만달러)
"""
import time
import requests, pandas as pd

URL = "https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/1/10/{stat}/M/{b}/{e}/{item}"


def monthly(stat, item, bgn, end, key="sample"):
    p = pd.period_range(pd.Period(bgn[:4] + "-" + bgn[4:], "M"), pd.Period(end[:4] + "-" + end[4:], "M"), freq="M")
    rows = []
    for i in range(0, len(p), 10):
        b, e = p[i].strftime("%Y%m"), p[min(i + 9, len(p) - 1)].strftime("%Y%m")
        r = requests.get(URL.format(key=key, stat=stat, b=b, e=e, item=item), timeout=30).json()
        for x in r.get("StatisticSearch", {}).get("row", []):
            rows.append(dict(name=x["ITEM_NAME1"], date=x["TIME"], value=float(x["DATA_VALUE"])))
        time.sleep(0.2)
    d = pd.DataFrame(rows).drop_duplicates("date")
    d.index = pd.PeriodIndex(d["date"], freq="M")
    return d
