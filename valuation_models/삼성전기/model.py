"""삼성전기(009150) 밸류에이션 모델 — 2026-11-06 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/삼성전기/model.py
원래 리포트: 2026-10-14 BUY 2,030,000원(증권사 목표가·PER 30배 Bear 등 종합). 기준일 2026-11-06 · 기준주가 2026-11-06 종가(stock_db).
반영한 자료: 2021~2025 사업보고서, 1Q26 분기·2Q26 반기보고서(연결), 3Q26 영업(잠정)실적(10-28), 장래사업·경영계획(07-02 세종 8조, 07-03 부산 15조),
  신규시설투자(09-28 패키지기판 4.27조), 글라셈 출자(11-05 정정, 3,191억·66.2%), 기업가치 제고 계획(03-19), 기업지배구조보고서(06-01).
방법: 이익이 빠르게 늘고 대규모 증설이 겹친 구간이라 PBR(고든)보다 이익 배수로 본다.
      A. 2027E 지배 EPS × 자기 PER 밴드(최근 4분기 지배 EPS 기준, 2021-05~2026-10) 평균 50%
      B. 2027E 지배 EPS × 국내 기판·부품 동종사 PER 중앙값(이수페타시스·대덕전자·삼화콘덴서·LG이노텍, 최근 4분기) 50%.
      교차확인: 적정 PBR(고든), EV/EBITDA. 증권사 목표주가는 쓰지 않음. 출력: results.json
"""
import json
import statistics
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr
from valuation.tools.report_kit import rating_of
from valuation.tools.simple_val import hist, band, gordon_pbr

ASOF = "2026-11-06"
ORIG = dict(date="2026-10-14", rating="BUY", tp=2030000, px=1376000, method="증권사 목표가·2027E EPS × PER 배수 종합", bull=3200000, bear=1110000)
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-05.json").read_text(encoding="utf-8"))
RF, MRP, G = MAC["ktb10y"]["value"] / 100, 0.07, 0.02

px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str}, parse_dates=["날짜"]).set_index("날짜")
px = px[px.index <= ASOF]
PRICE = float(px["종가"].iloc[-1])
PRICE_PREF = 314500.0
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["고가"].max()), float(w52["저가"].min())
PX_ORIG = float(px.loc["2026-10-13", "종가"])
SH_COM, SH_PREF = 74_693_722, 2_906_976
SH = SH_COM + SH_PREF
MCAP = (PRICE * SH_COM + PRICE_PREF * SH_PREF) / 1e8

FY, Q = hist("삼성전기", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
ROE, prev = {}, None
for y in YRS:
    e = FY[y]["지배자본"]; ROE[y] = FY[y]["지배순이익"] / ((prev + e) / 2) if prev else FY[y]["지배순이익"] / e; prev = e
Q3 = dict(rev=37633, op=6910, ni=4850, nic=4687)       # 3Q26 잠정(10-28)
YTD = dict(rev=Q["20261Q"]["매출"] + Q["20262Q"]["매출"] + Q3["rev"], op=Q["20261Q"]["영업이익"] + Q["20262Q"]["영업이익"] + Q3["op"],
           nic=Q["20261Q"]["지배순이익"] + Q["20262Q"]["지배순이익"] + Q3["nic"])
CONV = YTD["nic"] / YTD["op"]                           # 1~3Q26 지배순이익 ÷ 영업이익
EQ_2Q26 = Q["20262Q"]["지배자본"]
DPS_2025, PAYOUT_2025 = 2350, 0.252
CAPEX = dict(sejong=80000, busan=150000, pkg=42700, pkg_ratio=0.436, glassem=3191, glassem_pct=0.662, capex_2025=FY["2025"].get("유형자산취득") or 14901)

SC = {"보수": dict(q4=1.00, g27=0.05, g28=0.10, band=-1), "기본": dict(q4=1.05, g27=0.20, g28=0.20, band=0),
      "낙관": dict(q4=1.10, g27=0.35, g28=0.25, band=1)}


def forecast(s):
    q4 = Q3["op"] * s["q4"]
    op26 = YTD["op"] + q4
    ni26 = YTD["nic"] + q4 * CONV
    op27 = q4 * 4 * (1 + s["g27"]); op28 = op27 * (1 + s["g28"])
    rows, eq = [], EQ_2Q26 + Q3["nic"] + q4 * CONV
    rows.append(dict(year="2026", op=op26, ni=ni26, eps=ni26 * 1e8 / SH, eq_end=eq, roe=ni26 / ((FY["2025"]["지배자본"] + eq) / 2), q4=q4))
    for y, op in (("2027", op27), ("2028", op28)):
        ni = op * CONV; e2 = eq + ni - rows[-1]["ni"] * 0.20
        rows.append(dict(year=y, op=op, ni=ni, eps=ni * 1e8 / SH, eq_end=e2, roe=ni / ((eq + e2) / 2)))
        eq = e2
    return rows


BETA = beta_kr("009150", ASOF, 3)
COE = RF + BETA["blume"] * MRP
BAND = band(px["종가"], Q, SH, ASOF, start="2021-05-31", kind="per")
_s = pd.Series(BAND["series"])
BAND.update(p25=float(_s.quantile(.25)), p50=float(_s.median()), p75=float(_s.quantile(.75)),
            mean_pre26=float(_s[_s.index < "2026-01-01"].mean()))
PEERS = pd.read_csv(HERE / "peers_kr.csv", dtype={"code": str})
PEER_SET = PEERS[PEERS["code"].isin(["007660", "353200", "001820", "011070"])]
PEER_PER = float(statistics.median([v for v in PEER_SET["PER"] if pd.notna(v)]))

SCEN = {}
for k, s in SC.items():
    f = forecast(s)
    eps = f[1]["eps"]
    # 2026년 급등기(PER 90~117배)로 표준편차가 커서 ±1σ 대신: 보수 = 중앙값, 기본 = 평균, 낙관 = 평균 + (평균 − 중앙값)
    pe_a = {-1: BAND["p50"], 0: BAND["mean"], 1: 2 * BAND["mean"] - BAND["p50"]}[s["band"]]
    pe_b = PEER_PER * {"보수": 0.85, "기본": 1.0, "낙관": 1.15}[k]
    va, vb = pe_a * eps, pe_b * eps
    tp = (va + vb) / 2
    SCEN[k] = dict(rows=f, eps=eps, pe_a=pe_a, pe_b=pe_b, va=va, vb=vb, tp=tp, upside=tp / PRICE - 1)
B = SCEN["기본"]
TP = int(round(B["tp"], -3))
UP = TP / PRICE - 1
RATING = rating_of(UP)
BPS_NOW = EQ_2Q26 * 1e8 / SH
PBR_NOW = PRICE / BPS_NOW
TTM_NI = Q["20254Q"]["지배순이익"] + Q["20261Q"]["지배순이익"] + Q["20262Q"]["지배순이익"] + Q3["nic"]
PER_TTM = MCAP / TTM_NI
# 고든 교차확인
PB_G = gordon_pbr(B["rows"][1]["roe"], COE, G)
V_G = PB_G * B["rows"][0]["eq_end"] * 1e8 / SH
# 현재가가 뜻하는 2027E 영업이익 (A·B 평균 배수 기준)
PE_MID = (B["pe_a"] + B["pe_b"]) / 2
OP27_IMPL = PRICE * SH / 1e8 / PE_MID / CONV
# 민감도: 2027E 영업이익 성장률 × 배수
SENS = dict(g=[0.0, 0.10, 0.20, 0.30, 0.40], pe=[18, 21, PE_MID, 27, 30])
q4b = B["rows"][0]["q4"]
SENS["v"] = [[q4b * 4 * (1 + g) * CONV * 1e8 / SH * pe for pe in SENS["pe"]] for g in SENS["g"]]
NET_CASH = 33144 + 179 - 27920 - 2024 - 929             # 2Q26 현금+단기금융 − 단기·장기차입금 − 리스부채
EBITDA26 = B["rows"][0]["op"] + 9306 + 407
R = dict(asof=ASOF, price=PRICE, price_pref=PRICE_PREF, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, sh_com=SH_COM, sh_pref=SH_PREF,
         hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], nic=FY[y]["지배순이익"], eqc=FY[y]["지배자본"]) for y in YRS}, roe=ROE,
         q={k: Q[k] for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q")}, q3=Q3, ytd=YTD, conv=CONV, eq_2q26=EQ_2Q26,
         bps_now=BPS_NOW, pbr_now=PBR_NOW, ttm_ni=TTM_NI, per_ttm=PER_TTM, dps_2025=DPS_2025, payout_2025=PAYOUT_2025, capex=CAPEX,
         rf=RF, mrp=MRP, beta=BETA, coe=COE, band=BAND, peer_per=PEER_PER, peers=PEER_SET[["name", "PER", "PBR", "OPM"]].to_dict("records"),
         scen=SCEN, pb_g=PB_G, v_g=V_G, pe_mid=PE_MID, op27_impl=OP27_IMPL, sens=SENS, net_cash=NET_CASH,
         ev_ebitda26=(MCAP - NET_CASH) / EBITDA26, scen_assump=SC)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} 시총 {MCAP:,.0f} PER ttm {PER_TTM:.1f} PBR {PBR_NOW:.2f} 베타 {BETA['blume']:.2f} COE {COE:.3f} PER밴드 {BAND['mean']:.1f}±{BAND['sd']:.1f} ({BAND['start']}~) 피어 {PEER_PER:.1f} conv {CONV:.3f}")
    for k, v in SCEN.items():
        print(k, f"EPS27 {v['eps']:,.0f} peA {v['pe_a']:.1f} peB {v['pe_b']:.1f} A {v['va']:,.0f} B {v['vb']:,.0f} TP {v['tp']:,.0f} {v['upside']:+.1%}",
              [(r['year'], round(r['op']), round(r['ni']), round(r['roe'], 3)) for r in v['rows']])
    print("TP", TP, RATING, f"{UP:+.1%}", "고든", round(PB_G, 2), round(V_G), "현재가 뜻하는 27E OP", round(OP27_IMPL), "EV/EBITDA26", round(R['ev_ebitda26'], 1))
