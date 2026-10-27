"""케이뱅크(279570) 밸류에이션 모델. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/케이뱅크/model.py
기준일 2026-10-27 · 기준주가 2026-10-26 종가 5,110원(stock_db kor_price).
출력: results.json (보고서·민감도용). 모든 가정은 ASSUMP 에 모아 둠. 출처는 주석.
방법: A. 초과자본 분리 적정 PBR 50% + B. PBR–ROE 회귀(국내 상장 은행 7곳 + 카카오뱅크 플랫폼 프리미엄) 50%.
교차확인: 공모가 산정식(투자설명서 2026-02-04)을 지금 숫자로 단계별 재계산. 증권사 목표가는 쓰지 않음.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

# ───────────────────────── 기준 데이터 (확인값)
px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str})
PRICE = float(px.iloc[-1]["종가"])                  # 5,110 (2026-10-26)
PRICE_DATE = str(px.iloc[-1]["날짜"])[:10]
IPO_PX = 8_300                                      # 확정공모가 (발행조건확정 증권신고서 2026-02-12)
SHARES = 405_695_151                                # 발행주식총수 (2026 반기보고서 주식총수현황)
OPTIONS = 1_840_135                                 # 미행사 주식매수선택권 (투자설명서, 공모가 산정과 같은 기준)
DIL = SHARES + OPTIONS                              # 407,535,286 = 공모가 산정 시 주식수
MCAP = PRICE * SHARES / 1e8

# DART 재무 (별도, 억원)
NI = {"2023": 128.12, "2024": 1280.53, "2025": 1126.09, "1H25": 842.48, "1H26": 600.75, "1Q26": 332.06, "2Q26": 268.70}
NI_TTM = NI["2025"] - NI["1H25"] + NI["1H26"]       # 884.4
EQ = {"3Q25": 21922.68, "2Q25": 21822.50, "4Q25": 21717.66, "2Q26": 24408.77}   # 자본총계
AT1 = 998.94                                        # 신종자본증권 (2025 상각형 조건부자본증권, 2Q26 BS)
CE = {k: v - AT1 for k, v in EQ.items()}            # 보통주 자본
CE_NOW = CE["2Q26"]                                 # 23,409.8
ROE_TTM = NI_TTM / ((CE["2Q25"] + CE["2Q26"]) / 2)
BPS = CE_NOW * 1e8 / SHARES

# 자본적정성 (2026 반기보고서 BIS 표, 억원)
CET1, RWA = 22_773, 125_972
CET1_TARGET = 0.13                                  # 인터넷은행 3사 평균 CET1 수준을 감안한 정상 자본 가정
EXCESS = CET1 - CET1_TARGET * RWA                   # 6,396.6
CORE = CE_NOW - EXCESS                              # 17,013.2
EXCESS_YIELD = 0.025                                # 초과자본(국공채·예치 운용) 세후 수익률 가정

# 무위험이자율: 한국은행 ECOS 817Y002 국고채 10년
rf = pd.read_csv(HERE / "rf_ktb10y.csv")
RF = float(rf.iloc[-1]["value"]) / 100              # 4.074% (2026-10-26)

# 피어: 국내 상장 은행·금융지주 7곳 (valuation/tools/peers.py, kor_fs 최근 4분기 지배순이익 합, 6월말 지배지분, 10/22 시총)
peers = pd.read_csv(HERE / "peers_kr.csv", dtype={"code": str})
banks = peers[~peers.code.isin(["323410", "279570"])].copy()
banks["roe"] = banks["ni"] / banks["eq"]
banks["pbr"] = banks["mcap"] / banks["eq"]
SLOPE, ICPT = np.polyfit(banks.roe, banks.pbr, 1)
R2 = float(np.corrcoef(banks.roe, banks.pbr)[0, 1] ** 2)
# 카카오뱅크 (DART 별도: 2025 순이익 4,802.8억 · 1H25 2,636.7억 · 1H26 3,280.5억, 2Q26 자본총계 66,766.4억, 10/22 시총 95,662.7억)
KAKAO = dict(ni=4802.80 - 2636.73 + 3280.48, eq=66766.44, mcap=95662.65)
KAKAO["roe"] = KAKAO["ni"] / KAKAO["eq"]; KAKAO["pbr"] = KAKAO["mcap"] / KAKAO["eq"]
KAKAO["line"] = ICPT + SLOPE * KAKAO["roe"]
KAKAO["premium"] = KAKAO["pbr"] - KAKAO["line"]      # 은행 회귀선 위 플랫폼 프리미엄(배)

# ───────────────────────── 시나리오 가정
ASSUMP = {
    "보수": dict(roe=0.06, coe=0.110, g=0.020, xm=0.8, w_plat=0.0),
    "기본": dict(roe=0.08, coe=0.100, g=0.025, xm=1.0, w_plat=0.5),
    "낙관": dict(roe=0.10, coe=0.095, g=0.030, xm=1.0, w_plat=1.0),
}
# roe = 핵심자본(정상 CET1 13%) 지속 ROE. xm = 초과자본 평가 배수. w_plat = 카카오뱅크 플랫폼 프리미엄 반영 비율
WEIGHTS = {"A": 0.5, "B": 0.5}


def fwd_roe(roe):
    """보통주 자본 전체 기준 ROE = 핵심자본 ROE와 초과자본 운용수익의 가중."""
    return (roe * CORE + EXCESS_YIELD * EXCESS) / CE_NOW


def val_a(roe, coe, g, xm):
    pb = (roe - g) / (coe - g)
    return (CORE * pb + EXCESS * xm) * 1e8 / DIL, pb


def val_b(roe, w_plat):
    r = fwd_roe(roe)
    pb = ICPT + SLOPE * r + w_plat * KAKAO["premium"]
    return CE_NOW * pb * 1e8 / DIL, pb, r


def run(name, a, **kw):
    a = {**a, **kw}
    va, pb_core = val_a(a["roe"], a["coe"], a["g"], a["xm"])
    vb, pb_b, r = val_b(a["roe"], a["w_plat"])
    tp = WEIGHTS["A"] * va + WEIGHTS["B"] * vb
    return dict(name=name, **a, pb_core=pb_core, va=va, vb=vb, pb_b=pb_b, fwd_roe=r, tp=tp,
                pbr_tp=tp * DIL / (CE_NOW * 1e8), upside=tp / PRICE - 1)


def rating(up):
    return "BUY" if up >= 0.15 else ("HOLD" if up >= -0.05 else "SELL")


def ipo_steps():
    """공모가 산정식 {자본총계 × 비교 PBR + 신주 공모금액} ÷ 잠재주식수 를 한 단계씩 바꿔 본다."""
    # 원문 적정 시가총액 4,192,386백만원 = 2,192,268 × PBR + 249,000 → 표기 1.80은 반올림값, 역산 1.7988
    eq0, cash = 21922.68, 2490.0
    pbr0 = (41923.86 - cash) / eq0
    s = []
    s.append(("① 주관사 원식 (3Q25 자본총계 × PBR 1.80)", (eq0 * pbr0 + cash) * 1e8 / DIL, "카카오뱅크 1.54 · 라쿠텐뱅크 조정 2.05 평균"))
    s.append(("② 신종자본증권 999억 제외 (보통주 자본)", ((eq0 - AT1) * pbr0 + cash) * 1e8 / DIL, "AT1은 보통주주 몫이 아님"))
    s.append(("③ 비교 PBR을 카카오뱅크 현재값으로", ((eq0 - AT1) * KAKAO["pbr"] + cash) * 1e8 / DIL, f"카카오뱅크 PBR {KAKAO['pbr']:.2f}x (10/22)"))
    s.append(("④ 공모 후 실제 자본(2Q26 보통주)으로", CE_NOW * KAKAO["pbr"] * 1e8 / DIL, "공모자금이 자본에 이미 포함"))
    adj = ROE_TTM / KAKAO["roe"]
    s.append(("⑤ ROE 차이 반영 (PBR × 케이뱅크/카카오 ROE)", CE_NOW * KAKAO["pbr"] * adj * 1e8 / DIL,
              f"ROE {ROE_TTM*100:.1f}% vs {KAKAO['roe']*100:.1f}% → PBR {KAKAO['pbr']*adj:.2f}x"))
    return [dict(step=a, value=b, note=c) for a, b, c in s]


if __name__ == "__main__":
    out = {"base_date": "2026-10-27", "price_date": PRICE_DATE, "price": PRICE, "ipo_px": IPO_PX, "shares": SHARES,
           "options": OPTIONS, "dil": DIL, "mcap": MCAP, "ni": NI, "ni_ttm": NI_TTM, "eq": EQ, "at1": AT1, "ce_now": CE_NOW,
           "bps": BPS, "pbr_now": PRICE / BPS, "roe_ttm": ROE_TTM, "cet1": CET1, "rwa": RWA, "cet1_ratio": CET1 / RWA,
           "cet1_target": CET1_TARGET, "excess": EXCESS, "core": CORE, "excess_yield": EXCESS_YIELD, "rf": RF,
           "weights": WEIGHTS, "reg": dict(slope=SLOPE, icpt=ICPT, r2=R2), "kakao": KAKAO,
           "banks": banks[["code", "name", "roe", "pbr", "mcap", "eq", "ni"]].to_dict("records"), "scen": {}}
    for k, a in ASSUMP.items():
        out["scen"][k] = run(k, a)
    b = ASSUMP["기본"]; base = out["scen"]["기본"]
    out["rating"] = {k: rating(v["upside"]) for k, v in out["scen"].items()}
    out["ipo_steps"] = ipo_steps()
    # 민감도 1: 핵심자본 ROE × COE → A 주당가치
    roes = [0.05, 0.06, 0.07, 0.08, 0.09, 0.10]; coes = [0.09, 0.095, 0.10, 0.105, 0.11]
    out["sens_roe_coe"] = {"roe": roes, "coe": coes, "va": [[val_a(r, c, b["g"], b["xm"])[0] for c in coes] for r in roes]}
    # 민감도 2: 핵심자본 ROE × 플랫폼 프리미엄 반영 비율 → 목표가
    ws = [0.0, 0.25, 0.5, 0.75, 1.0]
    out["sens_roe_plat"] = {"roe": roes, "w": ws, "tp": [[run("x", b, roe=r, w_plat=w)["tp"] for w in ws] for r in roes]}
    # 역산: 현재가·공모가를 정당화하는 핵심자본 ROE (기본 COE·g·xm·w_plat 고정)
    def solve(target):
        lo, hi = 0.0, 0.30
        for _ in range(60):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if run("x", b, roe=m)["tp"] < target else (lo, m)
        return m
    out["implied"] = dict(roe_at_price=solve(PRICE), roe_at_ipo=solve(IPO_PX))
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

    print(f"price {PRICE:,.0f} ({PRICE_DATE}) mcap {MCAP:,.0f}억 BPS {BPS:,.0f} PBR {PRICE/BPS:.2f} ROE_TTM {ROE_TTM*100:.2f}% CET1 {CET1/RWA*100:.2f}% excess {EXCESS:,.0f} core {CORE:,.0f} rf {RF*100:.2f}%")
    print(f"reg PBR = {ICPT:.3f} + {SLOPE:.2f}*ROE (R2 {R2:.2f}) kakao ROE {KAKAO['roe']*100:.1f}% PBR {KAKAO['pbr']:.2f} line {KAKAO['line']:.2f} premium {KAKAO['premium']:.2f}")
    print(banks[["name", "roe", "pbr"]].round(3).to_string())
    for k, v in out["scen"].items():
        print(f"{k}: A {v['va']:,.0f} (핵심 PBR {v['pb_core']:.2f}) | B {v['vb']:,.0f} (PBR {v['pb_b']:.2f}, ROE {v['fwd_roe']*100:.1f}%) -> TP {v['tp']:,.0f} ({v['upside']*100:+.1f}%) PBR {v['pbr_tp']:.2f} {out['rating'][k]}")
    for s in out["ipo_steps"]:
        print(f"{s['step']}: {s['value']:,.0f}  {s['note']}")
    print("implied", {k: round(v * 100, 2) for k, v in out["implied"].items()})
