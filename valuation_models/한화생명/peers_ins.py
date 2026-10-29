"""보험 피어 배수 (기준일 2026-10-01). DART 연결재무제표 + 주식총수 API + stock_db 종가. 억원 단위.
- 보통주자본 = 지배주주지분 - 신종자본증권 (자본으로 인정되는 채무증권은 보통주 몫이 아님)
- TTM 순이익(지배) = 2025 연간 + 2026 상반기 - 2025 상반기(2026 반기보고서의 소급 재작성 비교표시 값)
사용: python valuation/한화생명/peers_ins.py
"""
import json, time, warnings
from pathlib import Path
import pandas as pd, requests
from valuation.tools import dart
from valuation.tools.price import conn

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
ASOF = "2026-10-01"
PEERS = [("088350", "한화생명", "생보"), ("032830", "삼성생명", "생보"), ("085620", "미래에셋생명", "생보"),
         ("000370", "한화손해보험", "손보"), ("000810", "삼성화재", "손보"), ("005830", "DB손해보험", "손보"),
         ("001450", "현대해상", "손보")]


def num(s):
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def pick(d, sj, names, col="thstrm_amount"):
    for n in names:
        x = d[(d.sj_div.isin(sj)) & (d.account_nm.str.strip() == n)]
        if len(x):
            return num(x.iloc[0][col])
    return None


def ni_ctrl(d, prior=False):
    # 손익계산서의 '지배기업의 소유주(지배주주)' 귀속 당기순이익. 포괄손익 행과 이름이 같은 회사는 순서상 마지막 것을 쓴다
    x = d[(d.sj_div.isin(["CIS", "IS"])) & (d.account_nm.str.contains("지배기업|지배주주|소유주", regex=True))
          & (~d.account_nm.str.contains("비지배|포괄", regex=True))]
    col = "thstrm_add_amount" if d.reprt.iloc[0] in ("11012", "11014") and "thstrm_add_amount" in d and x["thstrm_add_amount"].notna().any() else "thstrm_amount"
    if prior:  # 같은 보고서의 전기 누적(소급 재작성된 비교표시 값)
        col = "frmtrm_add_amount" if col == "thstrm_add_amount" else "frmtrm_amount"
    v = [num(a) for a in x[col]]
    v = [a for a in v if a is not None]
    return v[-1] if v else None


def shares(corp):
    r = requests.get(f"{dart.API}/stockTotqySttus.json", params=dict(crtfc_key=dart.key(), corp_code=corp,
                     bsns_year="2026", reprt_code="11012"), timeout=60).json()
    tot = [x for x in r.get("list", []) if x.get("se") in ("합계", "보통주")]
    com = next(x for x in tot if x["se"] == "보통주")
    return num(com["distb_stock_co"]), num(com["istc_totqy"])


def main():
    px = pd.read_sql("SELECT `종목코드`,`종가` FROM kor_price WHERE `날짜`=%s", conn(), params=[ASOF])
    px = dict(zip(px["종목코드"].astype(str).str.zfill(6), px["종가"]))
    rows = []
    for code, name, grp in PEERS:
        corp, _ = dart.corp_code(code)
        h26, y25 = dart.fs(corp, "2026", "11012"), dart.fs(corp, "2025", "11011")
        time.sleep(0.3)
        eq = pick(h26, ["BS"], ["지배기업의 소유주에게 귀속되는 자본", "지배주주지분", "지배기업지분", "지배기업 소유주지분", "지배기업소유주지분"])
        hyb = pick(h26, ["BS"], ["신종자본증권"]) or 0.0
        eq25 = pick(y25, ["BS"], ["지배기업의 소유주에게 귀속되는 자본", "지배주주지분", "지배기업지분", "지배기업 소유주지분", "지배기업소유주지분"])
        hyb25 = pick(y25, ["BS"], ["신종자본증권"]) or 0.0
        h25 = ni_ctrl(h26, prior=True)
        if h25 is None:  # 비교표시 누적값이 비어 있으면 2025 반기보고서 값
            h25 = ni_ctrl(dart.fs(corp, "2025", "11012"))
        ttm = ni_ctrl(y25) + ni_ctrl(h26) - h25
        out_sh, iss_sh = shares(corp)
        p = px[code]
        ce, ce25 = (eq - hyb) / 1e8, (eq25 - hyb25) / 1e8
        mcap = p * out_sh / 1e8
        rows.append(dict(code=code, name=name, grp=grp, px=p, shares_out=out_sh, shares_issued=iss_sh, mcap=mcap,
                         eq_ctrl=eq / 1e8, hybrid=hyb / 1e8, common_eq=ce, ni_ttm=ttm / 1e8,
                         PBR=mcap / ce, PER=mcap / (ttm / 1e8), ROE=(ttm / 1e8) / ((ce + ce25) / 2)))
        print(name, "ok")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "peers_ins.csv", index=False, encoding="utf-8-sig")
    print(df[["name", "px", "mcap", "common_eq", "ni_ttm", "PBR", "PER", "ROE"]].round(3).to_string())


if __name__ == "__main__":
    main()
