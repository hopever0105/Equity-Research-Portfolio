"""서진시스템(178320) 밸류에이션 모델 — 2026-11-18 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/서진시스템/model.py
원래 리포트: 2026-08-24 BUY 49,000원. 기준일 2026-11-18(수) · 기준주가 11-18 종가(네이버 기반 FinanceDataReader).
자료: DART 연결재무제표(2021~3Q26) → fs_summary_2026-11-18.csv, 3Q26 분기보고서(11-13: 부문 매출·차입금·외환손익·중단영업),
     전환사채 발행(08-24 4건, 11-06 2건, 11-09 정정), 베트남 법인 일부 사업 중단(09-30), Bloom Energy 공급계약(10-12).
     피어 배수: tools/peers.py → peers_20261117.csv(2Q26까지 4개 분기 합).
방법(2026-11-18 본인 OK): A. 2027E EBITDA × EV/EBITDA 8배 − 순차입 → 완전희석 주식수 60% + B. 2027E BPS × 자기 PBR 밴드 중앙값 40%.
'BUY가 되기 위한 조건'(재조사 원칙 8)은 목표가와 따로 계산. 증권사 목표주가는 쓰지 않음. 출력: results.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr
from valuation.tools.report_kit import rating_of
from valuation.tools.simple_val import hist, band
from valuation.tools.buy_cond import buy_price, solve_min, cond_price

ASOF = "2026-11-18"
ORIG = dict(date="2026-08-24", rating="BUY", tp=49000, method="EV/EBITDA·PBR 종합")
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-17.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07
TAX = 0.20
W_A, W_B = 0.6, 0.4

# ───────────────────────── 시세
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["date"], "Close"])
HI_SINCE = float(px.loc[ORIG["date"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["date"]:ASOF, "Close"].idxmax().date())
SH = 63_723_489                                            # 2026-09-30 유통주식수(3Q26 분기보고서)
SH_BEGIN = 55_873_279                                      # 2026 기초
CB = [("39~42회 (2026-08)", 2000, 1000, "30,391~36,950"), ("44~45회 (2026-11)", 1200, 600, "30,391~36,950")]   # (회차, 금액, 그중 자본 인정 영구형, 전환가)
CB_SHARES = 9_500_000                                      # 전부 전환 시 신주 약 950만주
SH_FD = SH + CB_SHARES                                     # 완전희석 약 7,322만주
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적·재무
FY, Q = hist("서진시스템", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
M9 = {k: Q["20261Q"][k] + Q["20262Q"][k] + Q["20263Q"][k] for k in ("매출", "영업이익", "세전이익", "지배순이익")}
M9P = {k: Q["20251Q"][k] + Q["20252Q"][k] + Q["20253Q"][k] for k in ("매출", "영업이익", "세전이익", "지배순이익")}
DEBT = dict(short=7157, current_lt=3096, long=2800)
DEBT_3Q = sum(DEBT.values())                               # 13,053
CASH_3Q = Q["20263Q"]["현금"]
NET_DEBT = 12640.0                                         # 9월 말 (본인 OK 제안값, 11월 영구형 CB 600억은 자본)
EQ_3Q = Q["20263Q"]["지배자본"]
SEG_9M = dict(semi=5633, ess=4401, ess_exp=1079, tel=1013)                 # 9M26 부문 매출(억원)
SEG_25 = dict(semi=2913, ess=3978, ess_exp=11, tel=1316)
Q3_ITEMS = dict(fx_trans=760, fx_diff=208, interest=256, disc=-1035, disc_rev25=942, da=355)
BLOOM = dict(amt=1064, start="2026-10-08", end="2027-12-23", pct_rev25=10.0)

# ───────────────────────── 할인율 (참고: 자기자본비용)
BETA = beta_kr("178320", ASOF, 2, "^KQ11")
COE = RF + BETA["blume"] * MRP

PEER = pd.read_csv(HERE / "peers_20261117.csv")
PEER = PEER[PEER["name"].isin(["원익QnC", "미코", "비에이치아이", "씨에스윈드"])][["name", "PER", "PBR", "EV/EBITDA", "EV/Sales", "OPM"]]
PEER_EVE_MED = float(PEER["EV/EBITDA"].median())

pser = px["Close"].astype(float)
PBAND = band(pser, Q, SH, ASOF, start="2022-03-31", kind="pbr")
pb = pd.Series(PBAND["series"]); PBAND["median"] = float(pb.median()); PBAND["q25"] = float(pb.quantile(.25)); PBAND["q75"] = float(pb.quantile(.75))

# ───────────────────────── 추정 (2026-11-18 본인 OK 제안값)
SC = {"보수": dict(q4=4800, q4m=0.04, rev27=18000, ebitda27=2800, mult=6.0, pbr="q25"),
      "기본": dict(q4=5300, q4m=0.068, rev27=20000, ebitda27=3300, mult=8.0, pbr="median"),
      "낙관": dict(q4=5800, q4m=0.08, rev27=22000, ebitda27=3800, mult=10.0, pbr="q75")}
DA_27 = Q3_ITEMS["da"] * 4                                 # 3Q26 감가상각 355억 × 4
INT_27 = Q3_ITEMS["interest"] * 4                          # 3Q26 이자비용 256억 × 4


def forecast(s):
    rev26 = M9["매출"] + s["q4"]; op26 = M9["영업이익"] + s["q4"] * s["q4m"]
    op27 = s["ebitda27"] - DA_27
    ni27 = (op27 - INT_27) * (1 - TAX)
    eq27 = EQ_3Q + 600 + ni27                              # 11월 영구형 CB 600억(자본) + 2027 순이익, 4Q26 순이익은 0으로 둠(환율 손익 불확실)
    eq27_fd = eq27 + 1600                                  # 부채로 잡힌 CB(8월 1,000억 + 11월 600억)까지 전환되면
    return dict(rev26=rev26, op26=op26, rev27=s["rev27"], ebitda27=s["ebitda27"], op27=op27, ni27=ni27,
                eq27=eq27, bps27_fd=eq27_fd * 1e8 / SH_FD, eps27_fd=ni27 * 1e8 / SH_FD)


def value(s):
    f = forecast(s)
    va = (f["ebitda27"] * s["mult"] - NET_DEBT) * 1e8 / SH_FD
    pbr = PBAND[s["pbr"]] if isinstance(s["pbr"], str) else s["pbr"]
    vb = f["bps27_fd"] * pbr
    return dict(f=f, mult=s["mult"], pbr=pbr, va=va, vb=vb, tp=W_A * va + W_B * vb)


OUT = {k: value(s) for k, s in SC.items()}
for v in OUT.values():
    v["upside"] = v["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -2))
UP = TP / PRICE - 1
RATING = rating_of(UP)

mult_list = [5.0, 6.0, 8.0, 10.0, 12.0]
e_list = [2800, 3300, 3800]
SENS_P = dict(mult=mult_list, e=e_list, v=[[value(dict(SC["기본"], ebitda27=e, mult=m))["tp"] for m in mult_list] for e in e_list])
nd_list = [10640, 11640, 12640, 13640]
SENS_N = dict(nd=nd_list, mult=[6.0, 8.0, 10.0], v=[[(3300 * m - nd) * 1e8 / SH_FD for nd in nd_list] for m in [6.0, 8.0, 10.0]])

# ───────────────────────── BUY가 되기 위한 조건
BUYP = buy_price(PRICE)
need_mult = solve_min(lambda m: value(dict(SC["기본"], mult=m))["tp"], 3, 40, BUYP)
need_e = solve_min(lambda e: value(dict(SC["기본"], ebitda27=e))["tp"], 1000, 20000, BUYP)
need_nd = None
for nd in range(12640, -1, -100):                          # 순차입이 얼마로 줄면 (EBITDA·배수 기본 그대로)
    va = (3300 * 8 - nd) * 1e8 / SH_FD
    if W_A * va + W_B * Bs["vb"] >= BUYP:
        need_nd = nd; break
BUY = dict(buy_price=BUYP, need_mult=need_mult, need_ebitda27=need_e, need_net_debt=need_nd, peer_eve_med=PEER_EVE_MED,
           ebitda_q3=387 + Q3_ITEMS["da"],
           cond=[dict(cond="지금 추정(기본) 그대로", px=cond_price(Bs["tp"])),
                 dict(cond="분기 EBITDA 950억 이상 2개 분기 연속 + 순차입 1조 원 아래로(낙관 경로)", px=cond_price(OUT["낙관"]["tp"]))])

R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, sh_begin=SH_BEGIN, sh_fd=SH_FD, cb=CB, cb_shares=CB_SHARES,
         hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], ni=FY[y]["지배순이익"], eq=FY[y]["지배자본"]) for y in YRS},
         q={k: dict(rev=Q[k]["매출"], op=Q[k]["영업이익"], pti=Q[k]["세전이익"], ni=Q[k]["지배순이익"]) for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q")},
         m9=M9, m9p=M9P, debt=DEBT, debt_3q=DEBT_3Q, cash=CASH_3Q, net_debt=NET_DEBT, eq_3q=EQ_3Q, seg_9m=SEG_9M, seg_25=SEG_25, q3_items=Q3_ITEMS, bloom=BLOOM,
         rf=RF, mrp=MRP, beta=BETA, coe=COE, w=(W_A, W_B), pband=PBAND, peer=PEER.to_dict("records"), peer_eve_med=PEER_EVE_MED,
         da27=DA_27, int27=INT_27, scen=OUT, scen_assump=SC, sens_p=SENS_P, sens_n=SENS_N, buy=BUY,
         pbr=MCAP / EQ_3Q, eve_27_now=(PRICE * SH_FD / 1e8 + NET_DEBT) / 3300)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} (08-24 {PX_ORIG:,.0f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:,.0f} {HI_SINCE_D}) 시총 {MCAP:,.0f}억 52주 {HI52:,.0f}/{LO52:,.0f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} COE {COE:.4f} 순차입 {NET_DEBT:,.0f} PBR {MCAP/EQ_3Q:.2f} PBR밴드 중앙 {PBAND['median']:.2f} q25 {PBAND['q25']:.2f} q75 {PBAND['q75']:.2f} 피어 EV/EBITDA 중앙 {PEER_EVE_MED:.1f}")
    for k, v in OUT.items():
        f = v["f"]
        print(k, f"26E {f['rev26']:,.0f}/{f['op26']:,.0f} 27E EBITDA {f['ebitda27']:,.0f} NI {f['ni27']:,.0f} BPS(fd) {f['bps27_fd']:,.0f} A {v['va']:,.0f} B {v['vb']:,.0f} ({v['pbr']:.2f}배) TP {v['tp']:,.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}")
    print("BUY", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in BUY.items() if k != "cond"}, [round(c["px"], -2) for c in BUY["cond"]])
