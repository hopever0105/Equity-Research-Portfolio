"""dart_fs_raw.csv -> 주요 계정 요약표 (재사용용).
- 기준일(asof)까지 '접수된' 보고서만 쓴다(정기공시 목록 rcept_dt로 확인).
- 분기 흐름값은 thstrm_amount(3개월) 우선, 사업보고서는 연간값.
사용: python -m valuation.tools.fs_summary 대한항공 2026-05-13
"""
import sys
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RP = {"11013": "1Q", "11012": "2Q", "11014": "3Q", "11011": "FY"}
ACC = {
    "매출": ["ifrs-full_Revenue", "ifrs_Revenue"],
    "영업이익": ["dart_OperatingIncomeLoss"],
    "세전이익": ["ifrs-full_ProfitLossBeforeTax"],
    "당기순이익": ["ifrs-full_ProfitLoss"],
    "지배순이익": ["ifrs-full_ProfitLossAttributableToOwnersOfParent"],
    "자산": ["ifrs-full_Assets"],
    "부채": ["ifrs-full_Liabilities"],
    "자본": ["ifrs-full_Equity"],
    "지배자본": ["ifrs-full_EquityAttributableToOwnersOfParent"],
    "현금": ["ifrs-full_CashAndCashEquivalents"],
    "영업CF": ["ifrs-full_CashFlowsFromUsedInOperatingActivities"],
    "유형자산취득": ["ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"],
    "감가상각": ["ifrs-full_AdjustmentsForDepreciationExpense", "dart_DepreciationExpenseOfPropertyPlantAndEquipment"],
}


def num(x):
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


def summary(name, asof):
    d = pd.read_csv(BASE / name / "dart_fs_raw.csv", dtype=str)
    lst = pd.read_csv(BASE / name / "dart_periodic.csv", dtype=str)
    ok = set()
    for _, r in lst.iterrows():
        if r["rcept_dt"] > asof.replace("-", ""):
            continue
        nm = r["report_nm"]
        y = nm[nm.find("(") + 1: nm.find("(") + 5] if "(" in nm else None
        m = nm[nm.find(".") + 1: nm.find(".") + 3] if "(" in nm else None
        if "사업보고서" in nm:
            ok.add((y, "11011"))
        elif "반기보고서" in nm:
            ok.add((y, "11012"))
        elif "분기보고서" in nm:
            ok.add((y, "11013" if m == "03" else "11014"))
    rows = []
    for (y, rp, fsd), g in d.groupby(["year", "reprt", "fs_div"]):
        if (y, rp) not in ok:
            continue
        rec = {"기간": f"{y}{RP[rp]}", "fs_div": fsd}
        for k, ids in ACC.items():
            s = g[g["account_id"].isin(ids)]
            if k in ("영업CF", "유형자산취득", "감가상각"):
                s = s[s["sj_div"] == "CF"]
            elif k in ("매출", "영업이익", "세전이익", "당기순이익", "지배순이익"):
                s = s[s["sj_div"].isin(["IS", "CIS"])]
            else:
                s = s[s["sj_div"] == "BS"]
            if s.empty:
                continue
            v = num(s.iloc[0]["thstrm_amount"])
            rec[k] = v / 1e8 if v is not None else None
        rows.append(rec)
    out = pd.DataFrame(rows).sort_values("기간")
    out.to_csv(BASE / name / f"fs_summary_{asof}.csv", index=False, encoding="utf-8-sig")
    return out, sorted(ok)


if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    o, ok = summary(sys.argv[1], sys.argv[2])
    print(o.round(0).to_string(index=False))
