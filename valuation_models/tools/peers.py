"""피어 배수 계산 (stock_db kor_fs 분기값 TTM 합산 + kor_ticker 시총). 억원 단위.
사용: python valuation_models/tools/peers.py 출력csv 기준일 코드1:이름1 코드2:이름2 ..."""
import sys, pymysql
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def conn():
    env = dict(l.split("=", 1) for l in (ROOT / "quant/.env").read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
    return pymysql.connect(host=env["DB_HOST"], user=env["DB_USER"], password=env["DB_PASSWORD"], database=env["DB_NAME"], charset="utf8mb4")

QTRS = ["2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"]
FLOW = {"op": "영업이익", "ni": "(지배주주지분)당기순이익", "dep": "유형자산감가상각비", "amo": "기타무형자산상각비", "rev": "매출액(수익)"}
STOCK = {"cash": "현금및현금성자산", "sti": "단기금융자산", "fdebt_c": "유동금융부채", "fdebt_nc": "비유동금융부채", "nci": "비지배주주지분", "eq": "지배주주지분"}

def one(cur, code, name, asof):
    r = {"code": code, "name": name}
    for k, acc in FLOW.items():
        cur.execute("SELECT `기준일`,`값` FROM kor_fs WHERE `종목코드`=%s AND `계정`=%s AND `공시구분`='q' AND `기준일` IN %s", (code, acc, QTRS))
        v = dict(cur.fetchall())
        r[k] = sum(float(x) for x in v.values() if x is not None) if len(v) == 4 else None
    for k, acc in STOCK.items():
        cur.execute("SELECT `값` FROM kor_fs WHERE `종목코드`=%s AND `계정`=%s AND `기준일`='2026-06-30' ORDER BY `공시구분` LIMIT 1", (code, acc))
        x = cur.fetchone(); r[k] = float(x[0]) if x and x[0] is not None else 0.0
    cur.execute("SELECT SUM(`시가총액`),MAX(`종가`) FROM kor_ticker WHERE `기준일`=%s AND (`종목명`=%s OR `종목명` LIKE %s)", (asof, name, name + "우%"))
    mc, px = cur.fetchone(); r["mcap"] = float(mc) / 1e8; r["px"] = px
    r["ebitda"] = (r["op"] or 0) + (r["dep"] or 0) + (r["amo"] or 0)
    r["netdebt"] = r["fdebt_c"] + r["fdebt_nc"] - r["cash"] - r["sti"]
    r["ev"] = r["mcap"] + r["netdebt"] + r["nci"]
    r["PER"] = r["mcap"] / r["ni"] if r["ni"] and r["ni"] > 0 else None
    r["PBR"] = r["mcap"] / r["eq"] if r["eq"] else None
    r["EV/EBITDA"] = r["ev"] / r["ebitda"] if r["ebitda"] else None
    r["EV/Sales"] = r["ev"] / r["rev"] if r["rev"] else None
    r["OPM"] = r["op"] / r["rev"] if r["rev"] else None
    return r

if __name__ == "__main__":
    out, asof, pairs = sys.argv[1], sys.argv[2], sys.argv[3:]
    c = conn(); cur = c.cursor()
    df = pd.DataFrame([one(cur, *p.split(":"), asof) for p in pairs])
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(df.round(2).to_string())

