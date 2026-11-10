"""한미반도체(042700) 밸류에이션 모델 — 2026-11-06 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/한미반도체/model.py
원래 리포트: 2026-08-11 BUY 370,000원(당시 217,500원). 기준일 2026-11-06(금) · 기준주가 11-06 종가 163,300원
  (네이버 기반 FinanceDataReader. stock_db 11-06 값 156,500원은 장중 수집값이라 쓰지 않음).
자료: DART 연결재무제표(2021~2Q26) → fs_summary_2026-11-06.csv, 3Q26 연결 잠정실적(10-30), 수주 공시(09-29, 10-06), 8공장 취득(08-18),
     주식총수·자기주식(2026 반기보고서). 업종 자료는 가정 교차확인에만: 대신증권 '후공정도 멀리 봐도 된다'(10-12, 2027 하이닉스 TSV 캐파 +20%),
     한화투자증권 'Rubin 출하 확대, HBM4 성장의 시작'(10-13), iM증권 SK하이닉스(11-04, HBM 출하 2026E 17,703 → 2027E 23,984백만Gb, +35%).
방법: A. 12개월 선행 PER = 2027E EPS × 자기 PER 밴드 중앙값(2021-11~2026-10 월말, 최근 4분기 EPS 기준) 50%
     + B. DCF(FCFF 4Q26~2036 + 영구성장 3%) 50%. 증권사 목표주가는 쓰지 않음. 출력: results.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr
from valuation.tools.report_kit import rating_of
from valuation.tools.simple_val import hist, band

ASOF = "2026-11-06"
ORIG = dict(date="2026-08-11", rating="BUY", tp=370000, px=217500, method="PER 배수·시나리오 종합(증권사 추정 참고)")
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-06.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07
G_T = 0.03
TAX = 0.20

# ───────────────────────── 시세 (네이버 기반 FDR)
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
PRICE = float(px["Close"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())
PX_ORIG = float(px.loc[ORIG["date"], "Close"])
HI_SINCE = float(px.loc[ORIG["date"]:ASOF, "Close"].max()); HI_SINCE_D = str(px.loc[ORIG["date"]:ASOF, "Close"].idxmax().date())
SH_ISSUED, TREASURY = 95_312_200, 459_198              # 2026 반기보고서 주식총수
SH = SH_ISSUED - TREASURY                               # 94,853,002
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적
FY, Q = hist("한미반도체", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
Q3P = dict(매출=1810.14, 영업이익=908.03)               # 3Q26 잠정(10-30, 백만원 → 억원)
Q3P_PREV = dict(매출=Q["20253Q"]["매출"], 영업이익=Q["20253Q"]["영업이익"])
M9 = dict(매출=Q["20261Q"]["매출"] + Q["20262Q"]["매출"] + Q3P["매출"], 영업이익=Q["20261Q"]["영업이익"] + Q["20262Q"]["영업이익"] + Q3P["영업이익"])
M9P = {k: Q["20251Q"][k] + Q["20252Q"][k] + Q["20253Q"][k] for k in ("매출", "영업이익")}
NI_CONV = FY["2025"]["지배순이익"] / FY["2025"]["영업이익"]          # 2025 순이익/영업이익 0.85
ORDERS = [("2026-06", "SK하이닉스", "HBM4용 TC본더", 442, "원래 리포트 이전"), ("2026-09-28", "UTAC(태국)", "MSVP", 79, "단일판매공급계약"),
          ("2026-10-02", "삼성전기", "AI 반도체 기판용 대면적 MSVP", 245, "단일판매공급계약")]
CAPEX_PLANT8 = 560                                       # 8공장(인천 가좌동) 토지·건물, 잔금 2027-02

# ───────────────────────── 할인율
BETA = beta_kr("042700", ASOF, 3)
WACC = RF + BETA["blume"] * MRP                          # 무차입 → WACC = COE

# ───────────────────────── 추정
SC = {"보수": dict(q4=1900, q4m=0.45, g27=0.10, m27=0.40, g28=0.05, m_lt=0.25, per=-1),
      "기본": dict(q4=2100, q4m=0.48, g27=0.25, m27=0.45, g28=0.15, m_lt=0.30, per=0),
      "낙관": dict(q4=2300, q4m=0.50, g27=0.40, m27=0.48, g28=0.20, m_lt=0.35, per=1)}
G_LATE = [0.08, 0.07, 0.06, 0.05, 0.05, 0.04, 0.04, 0.03]   # 2029~2036


def forecast(s):
    rev26 = M9["매출"] + s["q4"]; op26 = M9["영업이익"] + s["q4"] * s["q4m"]
    rows = [dict(year=2026, rev=rev26, op=op26, opm=op26 / rev26)]
    rev = rev26 * (1 + s["g27"]); rows.append(dict(year=2027, rev=rev, op=rev * s["m27"], opm=s["m27"]))
    rev *= 1 + s["g28"]; m28 = s["m27"] - 0.01; rows.append(dict(year=2028, rev=rev, op=rev * m28, opm=m28))
    ms = np.linspace(m28, s["m_lt"], len(G_LATE) + 1)[1:]
    for i, (g, m) in enumerate(zip(G_LATE, ms)):
        rev *= 1 + g; rows.append(dict(year=2029 + i, rev=rev, op=rev * m, opm=float(m)))
    prev_rev = FY["2025"]["매출"]
    for r in rows:
        r["ni"] = r["op"] * NI_CONV; r["eps"] = r["ni"] * 1e8 / SH
        r["da"] = r["rev"] * 0.02
        r["capex"] = r["rev"] * 0.03 + (CAPEX_PLANT8 if r["year"] == 2027 else 0)
        r["dnwc"] = (r["rev"] - prev_rev) * 0.15
        r["fcff"] = r["op"] * (1 - TAX) + r["da"] - r["capex"] - r["dnwc"]
        prev_rev = r["rev"]
    return rows


NET_CASH = Q["20262Q"]["현금"]                            # 2026-06말 현금성자산(차입 없음). 단기금융상품은 확인 필요라 제외(보수적)


def dcf(rows, wacc):
    t0 = (pd.Timestamp("2026-12-31") - pd.Timestamp(ASOF)).days / 365
    r26 = rows[0]
    q4_share = (r26["rev"] - M9["매출"]) / r26["rev"]
    pv = r26["fcff"] * q4_share / (1 + wacc) ** (t0 / 2)
    for i, r in enumerate(rows[1:]):
        pv += r["fcff"] / (1 + wacc) ** (t0 + i + 0.5)
    tv = rows[-1]["fcff"] * (1 + G_T) / (wacc - G_T) / (1 + wacc) ** (t0 + len(rows) - 1)
    return (pv + tv + NET_CASH) * 1e8 / SH, pv, tv


# ───────────────────────── PER 밴드 (최근 4분기 지배 EPS, 월말)
pser = px["Close"].astype(float)
BAND = band(pser, Q, SH, ASOF, start="2021-11-30", kind="per")
bs = pd.Series(BAND["series"])
BAND["median"] = float(bs.median()); BAND["q25"] = float(bs.quantile(.25)); BAND["q75"] = float(bs.quantile(.75))
PER_BASE = BAND["median"]
PER_MAP = {-1: BAND["q25"], 0: BAND["median"], 1: BAND["q75"]}
REF_PER = [("CLSA (11-02 보도)", "2027~2028E EPS × 50배", 50.0), ("대신증권 (10-12)", "와이씨: 어드반테스트 2028E PER 44배 × (1−30%)", 31.0),
           ("대신증권 (10-12)", "국내 테스트 장비 업종 12개월 선행 평균", 20.0)]

OUT = {}
for k, s in SC.items():
    rows = forecast(s)
    per = PER_MAP[s["per"]]
    va = rows[1]["eps"] * per
    vb, pv, tv = dcf(rows, WACC)
    OUT[k] = dict(rows=rows, per=per, va=va, vb=vb, pv=pv, tv=tv, tp=(va + vb) / 2)
    OUT[k]["upside"] = OUT[k]["tp"] / PRICE - 1
Bs = OUT["기본"]
TP = int(round(Bs["tp"], -3))
UP = TP / PRICE - 1
RATING = rating_of(UP)

# 민감도: 2027 성장률 × 목표 PER (A + B 평균), 장기 마진 × WACC (B)
g_list = [0.10, 0.175, 0.25, 0.325, 0.40]
per_list = [20, 30, BAND["median"], 50]
SENS_G = dict(g=g_list, per=per_list, v=[])
for g in g_list:
    rr = forecast(dict(SC["기본"], g27=g)); vb_ = dcf(rr, WACC)[0]
    SENS_G["v"].append([(rr[1]["eps"] * p + vb_) / 2 for p in per_list])
w_list = [WACC - 0.02, WACC - 0.01, WACC, WACC + 0.01]
m_list = [0.25, 0.30, 0.35]
SENS_D = dict(wacc=w_list, m=m_list, v=[[dcf(forecast(dict(SC["기본"], m_lt=m)), w)[0] for w in w_list] for m in m_list])
# 현재가를 DCF만으로 설명하려면 필요한 2029~2036 연평균 성장률 (2027·2028·마진 경로는 기본 그대로)
IMPL = None
for gl in np.arange(0.03, 0.80, 0.005):
    G_SAVE = list(G_LATE)
    G_LATE[:] = [float(gl)] * len(G_SAVE)
    v = dcf(forecast(SC["기본"]), WACC)[0]
    G_LATE[:] = G_SAVE
    if v >= PRICE:
        IMPL = float(gl); break

TTM_NI = Q["20254Q"]["지배순이익"] + Q["20261Q"]["지배순이익"] + Q["20262Q"]["지배순이익"] + Q3P["영업이익"] * NI_CONV
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, sh_issued=SH_ISSUED, treasury=TREASURY,
         hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, hi_since=HI_SINCE, hi_since_d=HI_SINCE_D, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], ni=FY[y]["지배순이익"], eq=FY[y]["지배자본"], cash=FY[y]["현금"]) for y in YRS},
         q={k: dict(rev=Q[k]["매출"], op=Q[k]["영업이익"], ni=Q[k].get("지배순이익")) for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q")},
         q3p=Q3P, q3p_prev=Q3P_PREV, m9=M9, m9p=M9P, ni_conv=NI_CONV, orders=ORDERS, net_cash=NET_CASH, eq_2q26=Q["20262Q"]["지배자본"],
         rf=RF, mrp=MRP, beta=BETA, wacc=WACC, g_t=G_T, tax=TAX, band=BAND, ref_per=REF_PER,
         scen=OUT, scen_assump=SC, g_late=G_LATE, sens_g=SENS_G, sens_d=SENS_D, implied_g27=IMPL,
         ttm_ni=TTM_NI, per_ttm=MCAP / TTM_NI, pbr=MCAP / Q["20262Q"]["지배자본"], per_27_now=PRICE / Bs["rows"][1]["eps"])
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} (08-11 {PX_ORIG:,.0f} {PRICE/PX_ORIG-1:+.1%}, 이후 최고 {HI_SINCE:,.0f} {HI_SINCE_D}) 시총 {MCAP:,.0f}억 52주 {HI52:,.0f}/{LO52:,.0f}")
    print(f"beta {BETA['raw']:.2f}/{BETA['blume']:.2f} WACC {WACC:.4f} 순현금 {NET_CASH:,.0f} NI/OP {NI_CONV:.2f} PER밴드 평균 {BAND['mean']:.1f} 중앙 {BAND['median']:.1f} q25 {BAND['q25']:.1f} q75 {BAND['q75']:.1f} 현재 {BAND['now']:.1f}")
    print(f"9M 매출 {M9['매출']:,.0f} ({M9['매출']/M9P['매출']-1:+.1%}) OP {M9['영업이익']:,.0f}  TTM PER {MCAP/TTM_NI:.1f}")
    for k, v in OUT.items():
        r = v["rows"]
        print(k, f"26E {r[0]['rev']:,.0f}/{r[0]['op']:,.0f} 27E {r[1]['rev']:,.0f}/{r[1]['op']:,.0f} EPS27 {r[1]['eps']:,.0f} PER {v['per']:.1f} A {v['va']:,.0f} B {v['vb']:,.0f} (TV {v['tv']/(v['pv']+v['tv']):.0%}) TP {v['tp']:,.0f} {v['upside']:+.1%}")
    print("TP", TP, RATING, f"{UP:+.1%}", "현재가 내포 2027 성장률", IMPL, "현재가/27E EPS", round(PRICE / Bs["rows"][1]["eps"], 1))
