"""영원무역(111770) 밸류에이션 모델 — 2026-11-06 재조사. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/영원무역/model.py
원래 리포트: 2026-05-06 BUY 124,000원(증권사 컨센서스 기반). 이번 기준일 2026-11-06 · 기준주가 2026-11-06 종가(stock_db).
반영한 자료: 2025 사업보고서, 1Q26 분기·2Q26 반기보고서(연결), 기업가치 제고 계획(2025 이행현황, 08-11), 중간배당(08-11),
  기업지배구조보고서(06-01), Scott 지분 중재 정정공시(10-27). 3Q26 분기보고서는 기준일 현재 미제출.
방법: A. 적정 PBR (정상 ROE − g)/(COE − g) × 2026E말 BPS 50% + B. 자기 PBR 밴드(2021-05~2026-10) 평균 × 2026E말 BPS 50%.
      지배구조 할인 = 1 − 현재 PBR ÷ A의 적정 PBR. 증권사 목표주가는 쓰지 않음. 출력: results.json
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

ASOF = "2026-11-06"
ORIG = dict(date="2026-05-06", rating="BUY", tp=124000, px=81800, method="증권사 컨센서스·Bull/Bear 시나리오 종합",
            bull=160000, bear=95000)
MAC = json.loads((HERE.parents[0] / "tools" / "macro_2026-11-05.json").read_text(encoding="utf-8"))
RF = MAC["ktb10y"]["value"] / 100
MRP = 0.07
G = 0.02

# ───────────────────────── 시세·주식수
px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str}, parse_dates=["날짜"]).set_index("날짜")
px = px[px.index <= ASOF]
PRICE = float(px["종가"].iloc[-1])
w52 = px[px.index > pd.Timestamp(ASOF) - pd.Timedelta(days=365)]
HI52, LO52 = float(w52["고가"].max()), float(w52["저가"].min())
PX_ORIG = float(px.loc[ORIG["date"], "종가"]) if pd.Timestamp(ORIG["date"]) in px.index else ORIG["px"]
SH_ISSUED, TREASURY = 44_311_468, 1_751_356            # 중간배당 공시(08-11) 기준
SH = SH_ISSUED - TREASURY                               # 42,560,112
MCAP = PRICE * SH / 1e8

# ───────────────────────── 실적
FY, Q = hist("영원무역", ASOF)
YRS = ["2021", "2022", "2023", "2024", "2025"]
ROE = {}
prev = None
for y in YRS:
    e = FY[y]["지배자본"]
    ROE[y] = FY[y]["지배순이익"] / ((prev + e) / 2) if prev else FY[y]["지배순이익"] / e
    prev = e
H1 = {k: Q["2026" + "1Q"][k] + Q["20262Q"][k] for k in ("매출", "영업이익", "지배순이익", "세전이익")}
H1P = {k: Q["20251Q"][k] + Q["20252Q"][k] for k in ("매출", "영업이익", "지배순이익", "세전이익")}
H2P = {k: FY["2025"][k] - H1P[k] for k in ("매출", "영업이익", "지배순이익")}
EQ_2Q26 = Q["20262Q"]["지배자본"]
SEG = {"OEM": {"2024": 44059, "2025": 51671, "1H26": 27410}, "Scott": {"2024": 9537, "2025": 11223, "1H26": 6063},
       "기타": {"2024": 2014, "2025": 1918, "1H26": 785}, "조정": {"2024": -20432, "2025": -24176, "1H26": -12983}}
DIV = dict(d2025=1400, mid2025=700, mid2026=1050, payout2025=0.182, div_total_2025=596)     # 결산 1,400원(03-10), 중간 1,050원(08-11)
VALUEUP = dict(roe=0.10, pbr27=0.8, pbr30=1.0, payout=0.30, buyback=500, cg_target=0.80, cg_now=0.60)

# 시나리오: 2H26 매출 증가율, OPM, 2027·2028 매출 증가율, 순이익/영업이익
SC = {"보수": dict(g2h=0.03, opm=0.120, g27=0.03, g28=0.03, conv=0.92, band=-1),
      "기본": dict(g2h=0.08, opm=0.135, g27=0.06, g28=0.05, conv=0.95, band=0),
      "낙관": dict(g2h=0.12, opm=0.150, g27=0.08, g28=0.07, conv=0.98, band=1)}


def forecast(s):
    out = []
    # 2026E = 1H 실제 + 2H 추정
    rev2h = H2P["매출"] * (1 + s["g2h"]); op2h = rev2h * s["opm"]; ni2h = op2h * s["conv"]
    buy26 = VALUEUP["buyback"] / 2
    eq = EQ_2Q26 + ni2h - DIV["mid2026"] * SH / 1e8 - buy26
    sh = SH - buy26 * 1e8 / PRICE
    r26 = dict(year="2026", rev=H1["매출"] + rev2h, op=H1["영업이익"] + op2h, ni=H1["지배순이익"] + ni2h, eq_end=eq, sh=sh,
               h2=dict(rev=rev2h, op=op2h, ni=ni2h))
    r26["opm"] = r26["op"] / r26["rev"]; r26["roe"] = r26["ni"] / ((FY["2025"]["지배자본"] + eq) / 2); r26["bps"] = eq * 1e8 / sh
    r26["dps"] = r26["ni"] * VALUEUP["payout"] * 1e8 / sh
    out.append(r26)
    rev, prev_eq = r26["rev"], eq
    for y, g in (("2027", s["g27"]), ("2028", s["g28"])):
        rev = rev * (1 + g); op = rev * s["opm"]; ni = op * s["conv"]
        div = out[-1]["ni"] * VALUEUP["payout"] - DIV["mid2026"] * SH / 1e8 if y == "2027" else out[-1]["ni"] * VALUEUP["payout"]
        buy = VALUEUP["buyback"] / 2 if y == "2027" else 0
        eq = prev_eq + ni - div - buy
        sh = sh - buy * 1e8 / PRICE
        out.append(dict(year=y, rev=rev, op=op, opm=s["opm"], ni=ni, eq_end=eq, roe=ni / ((prev_eq + eq) / 2), bps=eq * 1e8 / sh, sh=sh,
                        dps=ni * VALUEUP["payout"] * 1e8 / sh))
        prev_eq = eq
    return out


# ───────────────────────── 할인율
B_OWN = beta_kr("111770", ASOF, 3)
B_OWN5 = beta_kr("111770", ASOF, 5)
B_PEER = {"화승엔터프라이즈": beta_kr("241590", ASOF, 3), "한세실업": beta_kr("105630", ASOF, 3)}
BETA = 1.0      # 실측 원베타가 0에 가까워(동종사도 0.02~0.10) 시장 평균 1.0을 쓴다
COE = RF + BETA * MRP

# ───────────────────────── 밴드
BAND = band(px["종가"], Q, SH, ASOF, start="2021-05-31")

SCEN = {}
for k, s in SC.items():
    f = forecast(s)
    roe_n = f[1]["roe"] if k != "보수" else min(f[1]["roe"], ROE["2025"])
    pb_a = gordon_pbr(roe_n, COE, G)
    pb_b = BAND["mean"] + s["band"] * BAND["sd"]
    bps = f[0]["bps"]
    va, vb = pb_a * bps, pb_b * bps
    tp = (va + vb) / 2
    SCEN[k] = dict(rows=f, roe_n=roe_n, pb_a=pb_a, pb_b=pb_b, bps=bps, va=va, vb=vb, tp=tp, upside=tp / PRICE - 1)
B = SCEN["기본"]
TP = int(round(B["tp"], -3))
UP = TP / PRICE - 1
RATING = rating_of(UP)
BPS_NOW = EQ_2Q26 * 1e8 / SH
PBR_NOW = PRICE / BPS_NOW
DISC = 1 - PBR_NOW / B["pb_a"]                         # 지배구조 할인

# 밸류업 목표 달성 시: PBR 0.8(2027) · 1.0(2030) × 2027E BPS
VU = dict(p27=VALUEUP["pbr27"] * B["rows"][1]["bps"], p30=VALUEUP["pbr30"] * B["rows"][1]["bps"])
DY = B["rows"][0]["dps"] / PRICE

# 민감도: 정상 ROE × 베타(COE)
SENS = dict(roe=[0.10, 0.115, 0.13, 0.145, 0.16], beta=[0.8, 0.9, 1.0, 1.1, 1.2])
SENS["coe"] = [RF + b * MRP for b in SENS["beta"]]
SENS["v"] = [[(gordon_pbr(r, c, G) * B["bps"] + B["vb"]) / 2 for c in SENS["coe"]] for r in SENS["roe"]]

# PER 교차확인
TTM_NI = sum(Q[k]["지배순이익"] for k in ("20253Q", "20254Q", "20261Q", "20262Q"))
R = dict(asof=ASOF, price=PRICE, tp=TP, upside=UP, rating=RATING, mcap=MCAP, sh=SH, sh_issued=SH_ISSUED, treasury=TREASURY,
         hi52=HI52, lo52=LO52, px_orig=PX_ORIG, chg_since=PRICE / PX_ORIG - 1, orig=ORIG,
         hist={y: dict(rev=FY[y]["매출"], op=FY[y]["영업이익"], nic=FY[y]["지배순이익"], eqc=FY[y]["지배자본"], cash=FY[y]["현금"]) for y in YRS},
         roe=ROE, h1=H1, h1p=H1P, h2p=H2P, q={k: Q[k] for k in ("20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q")},
         eq_2q26=EQ_2Q26, bps_now=BPS_NOW, pbr_now=PBR_NOW, seg=SEG, div=DIV, valueup=VALUEUP, vu=VU, div_yield_26e=DY,
         rf=RF, mrp=MRP, g=G, beta=BETA, beta_own=B_OWN, beta_own5=B_OWN5, beta_peer=B_PEER, coe=COE,
         band=BAND, scen=SCEN, sens=SENS, disc=DISC, ttm_ni=TTM_NI, per_ttm=MCAP / TTM_NI, per_tp_26=TP * SH / 1e8 / B["rows"][0]["ni"],
         scen_assump=SC)
(HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
if __name__ == "__main__":
    print(f"가격 {PRICE:,.0f} BPS {BPS_NOW:,.0f} PBR {PBR_NOW:.2f} COE {COE:.4f} 밴드 {BAND['mean']:.2f}±{BAND['sd']:.2f} 할인 {DISC:.1%}")
    for k, v in SCEN.items():
        print(k, f"ROEn {v['roe_n']:.3f} pbA {v['pb_a']:.2f} pbB {v['pb_b']:.2f} BPS {v['bps']:,.0f} A {v['va']:,.0f} B {v['vb']:,.0f} TP {v['tp']:,.0f} {v['upside']:+.1%}",
              [(r['year'], round(r['rev']), round(r['op']), round(r['ni']), round(r['roe'], 3)) for r in v['rows']])
    print("TP", TP, RATING, f"{UP:+.1%}", "DY26", f"{DY:.2%}", "VU", VU, "PER ttm", round(MCAP / TTM_NI, 1), "own beta", B_OWN["raw"], B_OWN5["raw"], {k: v["raw"] for k, v in B_PEER.items()})
