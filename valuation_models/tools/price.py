"""stock_db(kor_price) 조회 도구 (재사용용, KRX 요청 없음).
사용: python -m valuation_models.tools.price 마키나락스 477850 2026-05-01
"""
import sys
import warnings
from pathlib import Path

import pandas as pd
import pymysql

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]


def conn():
    env = dict(l.split("=", 1) for l in (ROOT / "quant" / ".env").read_text(encoding="utf-8").splitlines()
               if "=" in l and not l.startswith("#"))
    return pymysql.connect(host=env["DB_HOST"], user=env["DB_USER"], password=env["DB_PASSWORD"],
                           database=env["DB_NAME"], charset="utf8mb4")


def prices(codes, start):
    q = ",".join(["%s"] * len(codes))
    d = pd.read_sql(f"SELECT * FROM kor_price WHERE `종목코드` IN ({q}) AND `날짜` >= %s ORDER BY `날짜`",
                    conn(), params=list(codes) + [start])
    d["날짜"] = pd.to_datetime(d["날짜"])
    return d


if __name__ == "__main__":
    name, code, start = sys.argv[1], sys.argv[2], sys.argv[3]
    d = prices([code], start)
    d.to_csv(BASE / name / "price_db.csv", index=False, encoding="utf-8-sig")
    print(len(d), d["날짜"].min().date(), d["날짜"].max().date())
