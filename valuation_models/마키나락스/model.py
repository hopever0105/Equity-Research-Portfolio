"""마키나락스(477850) 밸류에이션 모델 — 2026-11-05 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/마키나락스/model.py
원래 리포트: 2026-08-10 HOLD 30,000원. 이번 기준일 2026-11-05 · 기준주가 2026-11-05 종가(stock_db).
반영한 자료: 증권신고서(2025A 실적·2026E~2030E 회사 추정), 1Q26 분기보고서(05-28), 2Q26 반기보고서(08-14: 1H 실적·수주잔고·공모자금),
  단일판매·공급계약(08-26, 23.5억), 국책과제 선정(10-13, 당사 정부지원 16억).
방법: A. DCF(FCFF, 2026~2035) 60% — 매출 = 회사 추정 × 달성률, 비용 = 회사 추정 × (고정 50% + 변동 50% × 달성률)
         달성률 = 2026E 매출(1H 실제 + 6월말 수주잔고 중 연내 인식분 + 8월 신규 계약 인식분) ÷ 회사 추정 225억
      B. 공모가 산식 재계산 40% — 2028E 순이익(같은 달성률) × 같은 날 피어 PER 중앙값, COE로 기준일까지 할인
      증권사 목표주가는 쓰지 않음. 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr
from valuation.tools.price import conn

ASOF = "2026-11-05"
ORIG = dict(date="2026-08-10", rating="HOLD", tp=30000, method="DCF 30% · PSR 22배 40% · 피어 PER 역산 30% (+12% 정성 조정)",
            earn="증권신고서 회사 추정", bull=38020, bear=15208)
MAC = json.loads((HERE.parents[0] / "tools" / f"macro_{ASOF}.json").read_text(encoding="utf-8"))

px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str}, parse_dates=["날짜"]).set_index("날짜")
px = px[px.index <= ASOF]
PRICE = float(px["종가"].iloc[-1])
PX_ORIG = float(px.loc[ORIG["date"], "종가"])
CHG_SINCE = PRICE / PX_ORIG - 1
HI, LO = float(px["고가"].max()), float(px["저가"].min())
HI_D, LO_D = str(px["고가"].idxmax().date()), str(px["저가"].idxmin().date())
IPO_PRICE = 15_000
SH = 17_754_736                                                       # 자본금 8,877,368,000 ÷ 액면 500 (2Q26)
MCAP = PRICE * SH / 1e8

# 증권신고서 실적·회사 추정 (억원)
HIST = {"2023": dict(rev=52, op=-112, ni=-183), "2024": dict(rev=83, op=-109, ni=-61), "2025": dict(rev=115, op=-80, ni=-138)}
CO = {2026: dict(rev=225, op=-23), 2027: dict(rev=374, op=49), 2028: dict(rev=587, op=159), 2029: dict(rev=822, op=314), 2030: dict(rev=1067, op=490)}
for v in CO.values():
    v["cost"] = v["rev"] - v["op"]
NOL = 653

# 2026 실적 (연결, 억원) — 1Q26 분기보고서, 2Q26 반기보고서
Q = {"1Q26": dict(rev=30.35, op=-24.33, ni=-23.74), "2Q26": dict(rev=39.97, op=-17.71, ni=-15.20)}
raw = pd.read_csv(HERE / "dart_fs_raw.csv", dtype=str)


def acc(rp, ids, sj):
    d = raw[(raw.year == "2026") & (raw.reprt == rp) & raw.account_id.isin(ids) & raw.sj_div.isin(sj)]
    return float(str(d.iloc[0]["thstrm_amount"]).replace(",", "")) / 1e8 if len(d) else np.nan


for lab, rp in (("1Q26", "11013"), ("2Q26", "11012")):
    Q[lab]["rev"] = acc(rp, ["ifrs-full_Revenue"], ["IS", "CIS"]) if not np.isnan(acc(rp, ["ifrs-full_Revenue"], ["IS", "CIS"])) else Q[lab]["rev"]
    Q[lab]["op"] = acc(rp, ["dart_OperatingIncomeLoss"], ["IS", "CIS"])
    Q[lab]["ni"] = acc(rp, ["ifrs-full_ProfitLoss"], ["IS", "CIS"])
H1 = {k: Q["1Q26"][k] + Q["2Q26"][k] for k in ("rev", "op", "ni")}
EQ_2Q = acc("11012", ["ifrs-full_EquityAttributableToOwnersOfParent", "ifrs-full_Equity"], ["BS"])
BS_2Q = dict(cash=441.09, sti=23.00, debt=20.00, lease=3.51 + 1.97)  # 반기보고서 요약연결재무정보
IPO_NET = 383.92                                                     # 공모 조달 38,392백만원(05-14 납입), 6월말 사용 2.17억
BACKLOG = dict(total=236.87, delivered=88.84, remain=147.77, os=10.98, sol=45.02, rnd=61.77)   # 2026-06-30 수주잔고(억원)
NEW_ORDER = dict(amt=23.5, start="2026-08-18", end="2027-12-31")    # 08-26 단일판매·공급계약 (2025 매출의 20.5%)
GOV = dict(amt=16.0, start="2026-10-13", end="2029-12-31")          # 10-13 국책과제, 당사 배정 정부지원 연구개발비

# 기준일 순현금 = 6월말 순현금 − 7/1~11/5 영업손실(1H 월평균 지속 가정)
BURN_M = -H1["op"] / 6
MONTHS = (pd.Timestamp(ASOF) - pd.Timestamp("2026-06-30")).days / 30.4
NET_CASH = BS_2Q["cash"] + BS_2Q["sti"] - BS_2Q["debt"] - BS_2Q["lease"] - BURN_M * MONTHS

# COE: 상장 6개월이라 자기 베타 대신 국내 상장 SW 피어 3사(KOSDAQ 대비 2년 주간) 블룸 베타 평균
PEER_B = {c: beta_kr(c, ASOF, 2, "^KQ11") for c in ("096250", "459100", "413640")}
BETA = float(np.mean([b["blume"] for b in PEER_B.values()]))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07
COE = RF + BETA * MRP
TAX = 0.22
FIX = 0.5

# 피어 PER (기준일 종가로 시총 갱신, 2025 지배순이익 stock_db kor_fs)
pk = pd.read_csv(HERE / "peers_kr_0810.csv", dtype={"code": str}).set_index("code")
NI25 = {"041590": 3, "096250": 18, "459100": 19, "413640": 24}
c = conn()
PEERS = {}
for code, ni in NI25.items():
    p_now = float(pd.read_sql("SELECT `종가` FROM kor_price WHERE `종목코드`=%s AND `날짜`<=%s ORDER BY `날짜` DESC LIMIT 1", c, params=[code, ASOF]).iloc[0, 0])
    p_old = float(pk.loc[code, "px"])
    mc = float(pk.loc[code, "mcap"]) * p_now / p_old
    PEERS[pk.loc[code, "name"]] = dict(code=code, px=p_now, px_old=p_old, mcap=mc, ni=ni, per=mc / ni, chg=p_now / p_old - 1)
PEER_PER = float(np.median([v["per"] for v in PEERS.values()]))


def rev26(conv, new_share=None):
    """2026E 매출 = 1H 실제 + 6월말 수주잔고 × 연내 인식률 + 08월 신규 계약 × 기간 비례(08-18~12-31 / 전체)."""
    ns = new_share if new_share is not None else (pd.Timestamp("2026-12-31") - pd.Timestamp(NEW_ORDER["start"])).days / \
        (pd.Timestamp(NEW_ORDER["end"]) - pd.Timestamp(NEW_ORDER["start"])).days
    return H1["rev"] + BACKLOG["remain"] * conv + NEW_ORDER["amt"] * ns


def project(ach, tail=(0.20, 0.15, 0.12, 0.10, 0.08)):
    rows, nol = [], NOL
    for y in range(2026, 2031):
        cc = CO[y]
        rev = cc["rev"] * ach
        cost = cc["cost"] * (FIX + (1 - FIX) * ach)
        rows.append(dict(year=y, rev=rev, cost=cost, op=rev - cost))
    m = rows[-1]["op"] / rows[-1]["rev"]
    rev = rows[-1]["rev"]
    for i, g in enumerate(tail):
        rev *= 1 + g
        rows.append(dict(year=2031 + i, rev=rev, cost=rev * (1 - m), op=rev * m))
    for r in rows:
        taxable = r["op"]
        if taxable > 0 and nol > 0:
            use = min(nol, taxable); nol -= use; taxable -= use
        elif taxable < 0:
            nol += -taxable; taxable = 0
        r["tax"] = max(taxable, 0) * TAX
        r["ni"] = r["op"] - r["tax"]
        r["fcf"] = r["ni"]
        r["opm"] = r["op"] / r["rev"]
    return rows


def dcf(rows, wacc, g=0.03):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    pv = 0
    for i, r in enumerate(rows):
        cf = r["fcf"] * (t0 if i == 0 else 1)
        pv += cf / (1 + wacc) ** ((t0 / 2) if i == 0 else (t0 + i - 0.5))
    tv = rows[-1]["fcf"] * (1 + g) / (wacc - g) / (1 + wacc) ** (t0 + len(rows) - 1)
    return (pv + tv + NET_CASH) * 1e8 / SH, pv, tv


def ipo_formula(rows, per=None, disc=None):
    ni28 = [r for r in rows if r["year"] == 2028][0]["ni"]
    t = (pd.Timestamp("2028-12-31") - pd.Timestamp(ASOF)).days / 365
    return ni28 * (per or PEER_PER) / (1 + (disc or COE)) ** t * 1e8 / SH, ni28, t


SCN = {"보수": dict(conv=0.45), "기본": dict(conv=0.60), "낙관": dict(conv=0.75)}
OUT = {}
for k, s in SCN.items():
    r26 = rev26(s["conv"])
    ach = r26 / CO[2026]["rev"]
    rows = project(ach)
    va, pv, tv = dcf(rows, COE)
    vb, ni28, t = ipo_formula(rows)
    OUT[k] = dict(conv=s["conv"], rev26=r26, ach=ach, rows=rows, va=va, pv=pv, tv=tv, vb=vb, ni28=ni28,
                  tp=0.6 * max(va, 0) + 0.4 * max(vb, 0))
TP = int(round(OUT["기본"]["tp"] / 100) * 100)
UP = TP / PRICE - 1
RATING = "BUY" if UP >= .15 else ("HOLD" if UP >= -.05 else "SELL")
FULL = project(1.0); V_FULL = 0.6 * dcf(FULL, COE)[0] + 0.4 * ipo_formula(FULL)[0]
IMPLIED_ACH = None
for a in np.arange(0.3, 1.6, 0.01):
    rr = project(a)
    if 0.6 * dcf(rr, COE)[0] + 0.4 * ipo_formula(rr)[0] >= PRICE:
        IMPLIED_ACH = float(a); break
CASH_PS = NET_CASH * 1e8 / SH

achs = [0.5, 0.6, OUT["기본"]["ach"], 0.8, 0.9, 1.0]
waccs = [COE - 0.01, COE, COE + 0.01, COE + 0.02]
SENS = [[0.6 * dcf(project(a), w)[0] + 0.4 * ipo_formula(project(a), disc=w)[0] for w in waccs] for a in achs]

R = dict(asof=ASOF, orig=ORIG, px_orig=PX_ORIG, chg_since=CHG_SINCE, price=PRICE, tp=TP, upside=UP, rating=RATING,
         hi=HI, lo=LO, hi_d=HI_D, lo_d=LO_D, ipo_price=IPO_PRICE, sh=SH, mcap=MCAP, net_cash=NET_CASH, cash_ps=CASH_PS, burn_m=BURN_M,
         hist=HIST, co=CO, nol=NOL, q=Q, h1=H1, eq_2q=EQ_2Q, bs_2q=BS_2Q, ipo_net=IPO_NET, backlog=BACKLOG, new_order=NEW_ORDER, gov=GOV,
         rf=RF, beta=BETA, peer_beta={k: v["blume"] for k, v in PEER_B.items()}, mrp=MRP, coe=COE, tax=TAX, fix=FIX,
         peers=PEERS, peer_per=PEER_PER,
         scen={k: dict(conv=v["conv"], rev26=v["rev26"], ach=v["ach"], tp=v["tp"], va=v["va"], vb=v["vb"], ni28=v["ni28"], pv=v["pv"], tv=v["tv"],
                       rows=v["rows"], upside=v["tp"] / PRICE - 1) for k, v in OUT.items()},
         v_full=V_FULL, implied_ach=IMPLIED_ACH, sens=dict(ach=achs, wacc=waccs, v=SENS))
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"price {PRICE:,.0f} (08-10 {PX_ORIG:,.0f}, {CHG_SINCE:+.1%}) mcap {MCAP:,.0f} netcash {NET_CASH:,.1f} ({CASH_PS:,.0f}/sh) beta {BETA:.3f} COE {COE:.4f} peerPER {PEER_PER:.1f}")
    print("H1", {k: round(v, 1) for k, v in H1.items()}, "EQ", round(EQ_2Q, 1))
    for n, v in PEERS.items():
        print(n, round(v["px"]), f"{v['chg']:+.1%}", round(v["per"], 1))
    for k, v in OUT.items():
        print(k, v["conv"], "rev26", round(v["rev26"], 1), "ach", round(v["ach"], 3), "A", round(v["va"]), "B", round(v["vb"]), "NI28", round(v["ni28"], 1), "TP", round(v["tp"]))
    print("TP", TP, f"{UP:+.1%}", RATING, "full", round(V_FULL), "implied ach", IMPLIED_ACH)
