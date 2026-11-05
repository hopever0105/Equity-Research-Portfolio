"""SEC EDGAR 수집 도구 (재사용용, 해외 종목).
- companyfacts(XBRL 전 항목)와 submissions(공시 목록)를 받아 저장하고,
  기준일까지 '제출된' 값만 골라 분기·연간 표로 정리한다(그 뒤 공시로 결론 바꾸지 않기).
사용: python -m valuation.tools.sec 팔란티어 PLTR 2026-08-11
주의: SEC는 연락처(이메일)가 없는 User-Agent를 'Undeclared Automated Tool'로 막는다(2026-11-04 확인).
      UA에 본인 연락처를 넣고 실행하거나, 막히면 앱 브라우저에서 data.sec.gov companyfacts를 열어 같은 필터(filed<=기준일)로 뽑는다.
"""
import json, sys, time
from pathlib import Path
import requests, pandas as pd

BASE = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "job-research-portfolio github.com/hopever0105", "Accept-Encoding": "gzip, deflate"}

TAGS = {
    "rev": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "gp": ["GrossProfit"],
    "op": ["OperatingIncomeLoss"],
    "ni": ["NetIncomeLoss"],
    "eps_d": ["EarningsPerShareDiluted"],
    "sbc": ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "da": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "mkt_sec": ["MarketableSecuritiesCurrent", "ShortTermInvestments", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"],
    "assets": ["Assets"],
    "liab": ["Liabilities"],
    "equity": ["StockholdersEquity"],
    "debt_c": ["ConvertibleNotesPayableCurrent", "DebtCurrent", "LongTermDebtCurrent"],
    "debt_nc": ["ConvertibleNotesPayable", "LongTermDebtNoncurrent", "ConvertibleDebtNoncurrent", "LongTermDebt"],
    "shares": ["dei:EntityCommonStockSharesOutstanding"],
    "dil_sh": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
}


def cik(ticker):
    r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=UA, timeout=60).json()
    for v in r.values():
        if v["ticker"].upper() == ticker.upper():
            return str(v["cik_str"]).zfill(10)


def companyfacts(c, out):
    r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{c}.json", headers=UA, timeout=120)
    r.raise_for_status()
    (out / "sec_companyfacts.json").write_bytes(r.content)
    return r.json()


def submissions(c, out):
    r = requests.get(f"https://data.sec.gov/submissions/CIK{c}.json", headers=UA, timeout=60).json()
    rec = r["filings"]["recent"]
    d = pd.DataFrame({k: rec[k] for k in ["form", "filingDate", "reportDate", "accessionNumber", "primaryDocument", "items"]})
    d.to_csv(out / "sec_filings.csv", index=False, encoding="utf-8-sig")
    return d


def facts_table(facts, asof):
    """기준일까지 제출(filed<=asof)된 값만. 같은 기간은 가장 늦게 제출된 값(정정 반영)."""
    rows = []
    for key, tags in TAGS.items():
        for tag in tags:
            ns, t = tag.split(":") if ":" in tag else ("us-gaap", tag)
            node = facts["facts"].get(ns, {}).get(t)
            if not node:
                continue
            for unit, vals in node["units"].items():
                for v in vals:
                    if v["filed"] > asof:
                        continue
                    rows.append(dict(key=key, tag=tag, unit=unit, start=v.get("start"), end=v["end"], val=v["val"],
                                     fy=v.get("fy"), fp=v.get("fp"), form=v.get("form"), filed=v["filed"], accn=v["accn"]))
    d = pd.DataFrame(rows)
    if d.empty:
        return d
    d["start"] = pd.to_datetime(d["start"]); d["end"] = pd.to_datetime(d["end"])
    d["days"] = (d["end"] - d["start"]).dt.days
    d = d.sort_values("filed").drop_duplicates(["key", "tag", "start", "end"], keep="last")
    return d


def quarterly(d):
    """흐름 항목은 3개월(80~100일) 값. 10-K만 있는 4분기는 연간-9개월 누적으로 계산."""
    flow = d[d["days"].notna()].copy()
    out = {}
    for key in flow["key"].unique():
        f = flow[flow["key"] == key]
        tag = f.groupby("tag")["end"].max().idxmax()      # 가장 최근까지 이어지는 태그
        f = f[f["tag"] == tag]
        q = f[(f["days"] >= 80) & (f["days"] <= 100)].set_index("end")["val"]
        ann = f[(f["days"] >= 350) & (f["days"] <= 380)]
        for _, a in ann.iterrows():
            if a["end"] in q.index:
                continue
            n9 = f[(f["start"] == a["start"]) & (f["days"] >= 260) & (f["days"] <= 285)]
            if len(n9):
                q.loc[a["end"]] = a["val"] - n9["val"].iloc[-1]
        out[key] = q.sort_index()
    return pd.DataFrame(out).sort_index()


def annual(d):
    flow = d[(d["days"] >= 350) & (d["days"] <= 380)]
    out = {}
    for key in flow["key"].unique():
        f = flow[flow["key"] == key]
        tag = f.groupby("tag")["end"].max().idxmax()
        out[key] = f[f["tag"] == tag].set_index("end")["val"]
    return pd.DataFrame(out).sort_index()


def balance(d):
    inst = d[d["start"].isna()]
    out = {}
    for key in inst["key"].unique():
        f = inst[inst["key"] == key]
        tag = f.groupby("tag")["end"].max().idxmax()
        out[key] = f[f["tag"] == tag].set_index("end")["val"]
    return pd.DataFrame(out).sort_index()


def filing_text(c, accn, doc, out_dir):
    """공시 본문(8-K 보도자료 등) 받아 태그 제거 텍스트로 저장."""
    import re
    url = f"https://www.sec.gov/Archives/edgar/data/{int(c)}/{accn.replace('-', '')}/{doc}"
    r = requests.get(url, headers=UA, timeout=120)
    s = r.content.decode("utf-8", "ignore")
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"</(tr|p|div|table)>", "\n", s, flags=re.I)
    s = re.sub(r"</t[dh]>", " | ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&nbsp;|&#160;", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    p = Path(out_dir) / f"{accn}_{doc}.txt"
    p.write_text(s, encoding="utf-8")
    return p


def index_docs(c, accn):
    url = f"https://www.sec.gov/Archives/edgar/data/{int(c)}/{accn.replace('-', '')}/index.json"
    return [i["name"] for i in requests.get(url, headers=UA, timeout=60).json()["directory"]["item"]]


def collect(name, ticker, asof):
    out = BASE / name
    out.mkdir(parents=True, exist_ok=True)
    c = cik(ticker); time.sleep(0.3)
    facts = companyfacts(c, out); time.sleep(0.3)
    subs = submissions(c, out)
    d = facts_table(facts, asof)
    d.to_csv(out / "sec_facts_asof.csv", index=False, encoding="utf-8-sig")
    quarterly(d).to_csv(out / "sec_quarterly.csv", encoding="utf-8-sig")
    annual(d).to_csv(out / "sec_annual.csv", encoding="utf-8-sig")
    balance(d).to_csv(out / "sec_balance.csv", encoding="utf-8-sig")
    (out / "corp.json").write_text(json.dumps({"cik": c, "ticker": ticker, "name": name, "asof": asof}, ensure_ascii=False))
    return c, subs


if __name__ == "__main__":
    name, ticker, asof = sys.argv[1], sys.argv[2], sys.argv[3]
    c, subs = collect(name, ticker, asof)
    print(c, len(subs))
