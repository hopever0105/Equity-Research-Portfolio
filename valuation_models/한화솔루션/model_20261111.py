"""한화솔루션(009830) 후속 리포트 모델 — 원래 리포트 2026-11-06(BUY 30,300원) 이후 재조사. 단위: 억원(주당·배수·비율 제외).
실행: python valuation/한화솔루션/model_20261111.py → results_20261111.json
기준일 2026-11-11(수) · 기준주가 11-11 종가(네이버 기반 FinanceDataReader, price_fdr.csv). 우선주 009835 같은 날 종가.
반영한 자료: 원래 리포트의 공시 전부(2016~2025 사업보고서, 1Q·2Q26, 3Q26 잠정실적 10-29, 유상증자·불성실공시·소각·여천NCC 재편)
  + 3Q26 실적 컨퍼런스콜(10-29) 발언(보도), 3Q26 이후 증권사 리뷰 4건(삼성·교보·미래에셋·신한, 10-30) — refs/news_after_3Q26_20261112.txt
  + IR 개최 안내(11-11, 내용 변화 없음). 3Q26 분기보고서는 기준일까지 미제출.
방법(원래 리포트와 같음): A. 적정 PBR (정상 ROE − g)/(COE − g) × 2026E말 BPS 50% + B. 자기 PBR 밴드(2021-05~) 평균 × 2026E말 BPS 50%.
바꾼 가정: 4Q26E·2027E·2028E 영업이익을 부문 드라이버(모듈 가격·EPC·AMPC·주택용·케미칼)로 다시 쌓음, 국고채·베타·밴드를 11-11로 갱신.
증권사 목표주가는 가중평균에 넣지 않고 교차확인 표에만 둔다.
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.beta import beta_kr
from valuation.tools.report_kit import rating_of
from valuation.tools.simple_val import hist, band, gordon_pbr

ASOF = "2026-11-11"
ORIG = dict(date="2026-11-06", rating="BUY", tp=30300, price=25800, op4q=1000, op27=7000, op28=8500, rf=0.03887, beta=0.70,
            coe=0.0881, band_mean=0.95, roe_n=0.041, pb_a=0.31, bps=48228)
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-11.json").read_text(encoding="utf-8"))
RF, MRP, G = MAC["ktb10y"]["value"] / 100, 0.07, 0.02

px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
px = px[px.index <= ASOF]
CLOSE = px["Close"].astype(float)
PRICE = float(CLOSE.iloc[-1])
PRICE_PREF = 15370.0                                   # 009835, 2026-11-11 종가(FDR)
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["High"].max()), float(w52["Low"].min())

SH_OLD = 171_892_536
NEW_SH, NEW_AMT, ISSUE_PX, PLAN_PX = 53_000_000, 11713, 22100, 27900
SH_COM = SH_OLD + NEW_SH
SH_PREF = 2_544_616
SH = SH_COM + SH_PREF
MCAP = (PRICE * SH_COM + PRICE_PREF * SH_PREF) / 1e8
DILUTION = NEW_SH / SH_OLD

FY, Q = hist("한화솔루션", "2026-11-06")              # 기준일까지 새 정기보고서 없음 → 같은 요약표
OLD = {2016: (92588, 7792, 7553, 52849), 2017: (93418, 7564, 8247, 60151), 2018: (90460, 3543, 1867, 60900),
       2019: (95033, 3783, -2376, 57282), 2020: (91950, 5942, 3091, 59291)}
HIST = {str(y): dict(rev=v[0], op=v[1], nic=v[2], eqc=v[3]) for y, v in OLD.items()}
for y in ("2021", "2022", "2023", "2024", "2025"):
    HIST[y] = dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], nic=FY[y]["지배순이익"], eqc=FY[y]["지배자본"])
ROE, prev = {}, None
for y in sorted(HIST):
    e = HIST[y]["eqc"]
    ROE[y] = HIST[y]["nic"] / ((prev + e) / 2) if prev else HIST[y]["nic"] / e
    prev = e
ROE_1622 = sum(ROE[str(y)] for y in range(2016, 2023)) / 7
ROE_1625 = sum(ROE[str(y)] for y in range(2016, 2026)) / 10

# 3Q26 잠정(10-29) + 부문(컨퍼런스콜·보도)
Q3 = dict(rev=39486, op=905, ni=685, nic=573)
SEG3Q = dict(renew_rev=21632, renew_op=1051, chem_rev=13426, chem_op=-447, adv_rev=2919, adv_op=389,
             resi_op=812, epc_op=-576, ampc=2118, mod_gw=2.0, us_gw=1.6, equity_loss=-880, other_nonop=1716)
YTD = dict(rev=Q["20261Q"]["매출"] + Q["20262Q"]["매출"] + Q3["rev"], op=Q["20261Q"]["영업이익"] + Q["20262Q"]["영업이익"] + Q3["op"],
           nic=Q["20261Q"]["지배순이익"] + Q["20262Q"]["지배순이익"] + Q3["nic"])
EQ_2Q26 = Q["20262Q"]["지배자본"]
EQ_3Q26 = EQ_2Q26 + NEW_AMT + Q3["nic"]
DEBT_2Q26 = dict(st=83867, lt=70281, cash=26930, sti=3617)
NETDEBT = DEBT_2Q26["st"] + DEBT_2Q26["lt"] - DEBT_2Q26["cash"] - DEBT_2Q26["sti"] - NEW_AMT
NCI = 27580
DA_TTM = 7710 + 627
FIN = dict(nonop=-2400, tax=0.22, da=[8500, 8800, 9100])
TARIFF_REFUND_2Q = 900                                 # 2Q26 관세 환급(일회성, 교보·컨퍼런스콜)

# 영업이익 드라이버 (억원, 2026E 기초 대비 증감). 기초 = 2026E 영업이익 − 2Q 관세 환급
DRV = {
    "기본": dict(op4q=800, price=(1500, 2000), epc=(1000, 1500), ampc=(1000, 1500), resi=(500, 800), chem=(0, 500)),
    "보수": dict(op4q=500, price=(500, 500), epc=(300, 800), ampc=(500, 800), resi=(200, 300), chem=(-300, 0)),
    "낙관": dict(op4q=1200, price=(2500, 3500), epc=(1200, 1500), ampc=(1500, 2000), resi=(800, 1000), chem=(200, 700)),
}
# 낙관 2027E ≈ 1.1조, 2028E ≈ 1.35조(회사가 2026-04 증권신고서에 낸 2027 목표 1조 3,527억을 1년 늦게 달성) · 보수 2027E 6,000억 · 2028E 7,000억대
DRV_NOTE = {
    "price": "미국 모듈 신규 계약 ASP +10% 이상(232조·최소수입가격 12-04 시행). 1H27은 기존 계약·재고로 제한 → 2027 반년 효과, 2028 전체 효과에서 미국산 셀 공급 증가로 프리미엄 일부 축소",
    "epc": "3Q26 EPC·개발자산 영업손실 576억(공기 지연·인력비) → 연말 완공 후 2027 손실 절반, 2028 대부분 해소",
    "ampc": "카터스빌 잉곳~모듈 통합 생산 확대로 첨단제조 생산세액공제 증가(2026 연간 9,000억대 중반, 4Q부터 증가)",
    "resi": "주택용 에너지(TPO) 계약 → 설치 3~5개월 시차로 매출 인식, 3Q 812억",
    "chem": "케미칼 2026 연간 손익분기 근처 → 2027 손익분기, 2028 여수 NCC 통합 효과",
}


def forecast(k):
    d = DRV[k]
    op26 = YTD["op"] + d["op4q"]
    base = op26 - TARIFF_REFUND_2Q
    op27 = base + sum(d[x][0] for x in ("price", "epc", "ampc", "resi", "chem"))
    op28 = base + sum(d[x][1] for x in ("price", "epc", "ampc", "resi", "chem"))
    rows = []
    q4_ni = (d["op4q"] + FIN["nonop"] / 4) * (1 - FIN["tax"])
    ni26 = YTD["nic"] + q4_ni
    eq = EQ_3Q26 + q4_ni
    r = dict(year="2026", op=op26, ni=ni26, eq_end=eq, q4_ni=q4_ni, base=base)
    r["roe"] = ni26 / ((HIST["2025"]["eqc"] + eq) / 2); r["bps"] = eq * 1e8 / SH; r["ebitda"] = r["op"] + FIN["da"][0]
    rows.append(r)
    for i, (y, op) in enumerate((("2027", op27), ("2028", op28)), 1):
        ni = (op + FIN["nonop"]) * (1 - FIN["tax"])
        e2 = eq + ni
        rows.append(dict(year=y, op=op, ni=ni, eq_end=e2, roe=ni / ((eq + e2) / 2), bps=e2 * 1e8 / SH, ebitda=op + FIN["da"][i]))
        eq = e2
    return rows


B_OWN = beta_kr("009830", ASOF, 3)
BETA = B_OWN["blume"]
COE = RF + BETA * MRP
BAND = band(CLOSE, Q, SH, ASOF, start="2021-05-31")

ROE_KEY = {"보수": "2027", "기본": "2028", "낙관": "1622"}
SCEN = {}
for k in DRV:
    f = forecast(k)
    roe_n = {"2027": f[1]["roe"], "2028": f[2]["roe"], "1622": ROE_1622}[ROE_KEY[k]]
    pb_a = max(gordon_pbr(roe_n, COE, G), 0.0)
    pb_b = BAND["mean"] + {"보수": -1, "기본": 0, "낙관": 1}[k] * BAND["sd"]
    bps = f[0]["bps"]
    va, vb = pb_a * bps, pb_b * bps
    tp = (va + vb) / 2
    SCEN[k] = dict(rows=f, roe_n=roe_n, pb_a=pb_a, pb_b=pb_b, bps=bps, va=va, vb=vb, tp=tp, upside=tp / PRICE - 1)
B = SCEN["기본"]
TP = int(round(B["tp"], -2))
UP = TP / PRICE - 1
RATING = rating_of(UP)
BPS_NOW = EQ_3Q26 * 1e8 / SH
PBR_NOW = PRICE / BPS_NOW
EV = MCAP + NETDEBT + NCI
EVE = dict(ttm=EV / ((Q["20253Q"]["영업이익"] + Q["20254Q"]["영업이익"] + Q["20261Q"]["영업이익"] + Q["20262Q"]["영업이익"]) + DA_TTM),
           e26=EV / B["rows"][0]["ebitda"], e27=EV / B["rows"][1]["ebitda"])
EVE["tp27"] = (TP * SH / 1e8 + NETDEBT + NCI) / B["rows"][1]["ebitda"]
BPS_PRE = EQ_2Q26 * 1e8 / (SH_OLD + SH_PREF)
SENS = dict(roe=[0.03, 0.045, 0.06, 0.075, 0.09], beta=[0.6, 0.7, 0.8, 0.9, 1.0])
SENS["coe"] = [RF + b * MRP for b in SENS["beta"]]
SENS["v"] = [[(max(gordon_pbr(r, c, G), 0) * B["bps"] + B["vb"]) / 2 for c in SENS["coe"]] for r in SENS["roe"]]
# 2028E 영업이익 × 정상 ROE 민감도(밴드 고정)
SENS_OP = [6000, 8000, 10000, 11000, 12000, 14000]
SENS["op28"] = []
for op in SENS_OP:
    ni = (op + FIN["nonop"]) * (1 - FIN["tax"])
    e27 = B["rows"][1]["eq_end"]
    roe = ni / ((e27 + e27 + ni) / 2)
    SENS["op28"].append(dict(op=op, roe=roe, tp=(max(gordon_pbr(roe, COE, G), 0) * B["bps"] + B["vb"]) / 2))

# 교차확인: 3Q26 이후 증권사 목표주가(가중평균에 넣지 않음)
BROKERS = [("삼성증권", "2026-10-30", "매수", 41000, 32000), ("교보증권", "2026-10-30", "매수", 40000, 33000),
           ("미래에셋증권", "2026-10-30", "매수", 38000, 33000), ("신한투자증권", "2026-10-30", "매수", 40000, 34000)]
CHG = PRICE / ORIG["price"] - 1

R = dict(asof=ASOF, orig=ORIG, chg_since=CHG, price=PRICE, price_pref=PRICE_PREF, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH,
         sh_com=SH_COM, sh_pref=SH_PREF, sh_old=SH_OLD, new_sh=NEW_SH, new_amt=NEW_AMT, issue_px=ISSUE_PX, plan_px=PLAN_PX,
         dilution=DILUTION, hi52=HI52, lo52=LO52, hist=HIST, roe=ROE, roe_1622=ROE_1622, roe_1625=ROE_1625,
         q={k: Q[k] for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q")}, q3=Q3, seg3q=SEG3Q, ytd=YTD,
         eq_2q26=EQ_2Q26, eq_3q26=EQ_3Q26, bps_now=BPS_NOW, bps_pre=BPS_PRE, pbr_now=PBR_NOW, netdebt=NETDEBT, nci=NCI, debt=DEBT_2Q26,
         ev=EV, eve=EVE, da_ttm=DA_TTM, fin=FIN, tariff_refund=TARIFF_REFUND_2Q, drv=DRV, drv_note=DRV_NOTE, rf=RF, mrp=MRP, g=G,
         beta=B_OWN, coe=COE, band=BAND, scen=SCEN, sens=SENS, brokers=BROKERS, macro=MAC)
(HERE / "results_20261111.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} ({CHG:+.1%} vs 11-06) 시총 {MCAP:,.0f} BPS {BPS_NOW:,.0f} PBR {PBR_NOW:.2f} 베타 {BETA:.2f} raw {B_OWN['raw']:.2f} "
          f"COE {COE:.4f} 밴드 {BAND['mean']:.2f}±{BAND['sd']:.2f} 52주 {HI52:,.0f}/{LO52:,.0f}")
    for k, v in SCEN.items():
        print(k, f"ROEn {v['roe_n']:.3f} pbA {v['pb_a']:.2f} pbB {v['pb_b']:.2f} BPS {v['bps']:,.0f} A {v['va']:,.0f} B {v['vb']:,.0f} TP {v['tp']:,.0f} {v['upside']:+.1%}",
              [(r['year'], round(r['op']), round(r['ni']), round(r['roe'], 3)) for r in v['rows']])
    print("TP", TP, RATING, f"{UP:+.1%}", "EV/EBITDA", {k: round(v, 1) for k, v in EVE.items()})
    print("op28 sens", [(s['op'], round(s['roe'], 3), round(s['tp'])) for s in SENS["op28"]])
