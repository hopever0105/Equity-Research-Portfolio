"""현대자동차(005380) 밸류에이션 모델. 단위: 조원(주당·배수·환율 제외). 실행: python valuation/현대차/model.py
기준일 2026-10-06(원본 리포트 작성일) · 기준주가 2026-10-02 종가 347,000원(10/5 대체공휴일 휴장).
출력: results.json (보고서·민감도용). 모든 가정은 ASSUMP 에 모아 둠. 출처는 주석.
방법: PER(2027E EPS) 50% + PBR(2026E말 BPS) 50%. 증권사 목표가·현재가는 목표가 계산에 넣지 않음.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

# ───────────────────────── 기준 데이터 (확인값)
PX = json.loads((HERE / "px_20261002.json").read_text(encoding="utf-8"))
PRICE = PX["005380"]["close"]                      # 347,000 (stock_db kor_price 2026-10-02)
PREF_PX = {"우선주": PX["005385"]["close"], "2우선주B": PX["005387"]["close"], "3우선주B": PX["005389"]["close"]}  # Naver(FDR) 10/2
# 유통주식수: DART 주식총수현황(2026 반기) 보통 202,416,066 · 우선 59,418,010
#  - 7/31 임원보상 자기주식 처분 2,747주(주요사항보고서 2026-07-23) → 보통 +2,747
#  - 8/31 자기주식 소각(보통 1,291,274 · 우선 1,214,332, 2026-08-26 공시)은 자기주식이라 유통주식수 불변
COMMON = 202_416_066 + 2_747
PREF = {"우선주": 22_839_037, "2우선주B": 34_257_047, "3우선주B": 2_321_926}   # 2Q 배당총액 ÷ 2,500원 (2026-07-23 배당결정 공시)
SHARES = COMMON + sum(PREF.values())               # EPS·BPS 분모 = 보통주 + 우선주 (국내 관행)
MCAP = (COMMON * PRICE + sum(PREF[k] * PREF_PX[k] for k in PREF)) / 1e12

# DART 연결 (조원). 분기 = 누적 차감
Q = {  # rev, op, ni_p(지배순이익)
    "3Q25": (46.721448, 2.537266, 2.261353),
    "4Q25": (186.254472 - 139.415886, 11.467851 - 9.772472, 9.445987 - 8.416950),
    "1Q26": (45.938886, 2.514686, 2.335346),
    "2Q26": (49.215328, 2.850888, 2.520851),
}
H1_26 = dict(rev=95.154214, op=5.365574, ni_p=4.856197)
FY = {2023: (162.6636, 15.1269, 11.96172), 2024: (175.231153, 14.239592, 12.526691), 2025: (186.254472, 11.467851, 9.445987)}
EQ_P_2Q26 = 122.327997      # 2026-06-30 지배기업소유주지분
DPS_Q = 2_500               # 분기배당(2Q 결정 2026-07-23, 9/30 지급). 3Q도 같은 금액 가정
# 지배순이익/영업이익 전환비율: FY23 0.79 · FY24 0.88 · FY25 0.82 · 1H26 0.91 평균 (지분법이익·금융손익·세금·비지배 포함)
CONV = sum([FY[y][2] / FY[y][1] for y in (2023, 2024, 2025)] + [H1_26["ni_p"] / H1_26["op"]]) / 4

# 환율: 한국은행 ECOS 731Y001 원/달러 매매기준율(일별) → 분기 평균
fx = pd.read_csv(HERE / "fx_usdkrw.csv"); fx["d"] = pd.to_datetime(fx["date"].astype(str))
FXQ = fx.set_index("d")["value"].resample("QE").mean()
FX_SPOT = float(fx[fx.d <= "2026-10-02"].iloc[-1]["value"])            # 1,359.6
FX_Q = {f"{d.quarter}Q{str(d.year)[2:]}": round(float(v), 1) for d, v in FXQ.items()}
FX26 = (FX_Q["1Q26"] + FX_Q["2Q26"] + FX_Q["3Q26"] + FX_SPOT) / 4        # 2026 평균(4Q = 10/2 현물 유지 가정)
# 환율 민감도: 2Q26 IR 영업이익 증감 요인 '환율 +2,380억(평균 1,502원, +7.0% YoY)' → 1%당 분기 340억 → 연 1,360억
FX_SENS = 0.238 / 7.0 * 4    # 조원 / 원화약세 1% / 연

# 과거 연말 배수 (stock_db 연말 종가, DART 지배순이익·지배지분, 연말 유통주식수 보통+우선)
hist = pd.read_csv(HERE / "hist_annual.csv")
sh = pd.read_csv(HERE / "shares_hist.csv", dtype=str)
sh = sh[(sh.se == "합계") & (sh.reprt == "11011")].assign(year=lambda x: x.year.astype(int),
                                                          out=lambda x: x.outstanding.str.replace(",", "").astype(float))
hist = hist.merge(sh[["year", "out"]], on="year")
hist["eps"] = hist.ni_p / hist.out; hist["bps"] = hist.eq_p / hist.out
hist["per"] = hist.px / hist.eps; hist["pbr"] = hist.px / hist.bps; hist["roe"] = hist.ni_p / hist.eq_p

# ───────────────────────── 시나리오 가정
ASSUMP = {
    "보수": dict(q3_rev=44.5, q3_op=2.2, q4_rev=47.0, q4_op=2.6, g27=0.01, opm27=0.056, fx27=1_300, per=6.5, pbr=0.55),
    "기본": dict(q3_rev=45.5, q3_op=2.4, q4_rev=48.5, q4_op=2.9, g27=0.03, opm27=0.063, fx27=1_360, per=8.0, pbr=0.70),
    "낙관": dict(q3_rev=46.5, q3_op=2.5, q4_rev=49.5, q4_op=3.1, g27=0.04, opm27=0.070, fx27=1_420, per=9.5, pbr=0.85),
}
# opm27 = 환율 중립(2026 평균 환율 FX26 기준) 영업이익률. 2027E 환율 효과는 FX_SENS로 따로 더함.
WEIGHTS = {"PER": 0.5, "PBR": 0.5}

# ───────────────────────── 로봇(보스턴다이내믹스, BD) 가치 — 본업 가치에 더하는 SOTP 항목
# 지분 구조(2026 반기보고서): 현대차 직접 보유 없음('-'), 계열회사 지분 합계 68%.
#   현대차의 관계기업 'HMG Global LLC'(신사업 투자·관리, 미국) 지분 49.50%, 장부가 2,851,008백만원.
#   → 현대차 실질 지분 = 49.5% × 68% = 33.7% (그룹 68%가 모두 HMG Global 경유라는 가정: 상한, 확인 필요)
# 이중계산 방지: HMG Global 장부가는 이미 BPS에, BD 손실은 지분법손익으로 EPS에 들어 있음
#   → 더하는 값 = 실질 지분 × BD 가치 − HMG Global 장부가(전부 BD라고 보고 차감, 보수적)
# BD 100% 가치(조원): 보수 = 2026-06 풋옵션 매입가 환산(9.65%에 3.25억달러 → 약 5.2조, 글로벌이코노믹 2026-06-19 로이터 인용)
#                     낙관 = 증권가 상장 기대가치 하단 30조(NH·국민일보·이데일리 종합)
#                     기본 = 두 값의 기하평균(거래 증거와 시장 기대의 중간, 약 12.5조)
ROBOT = dict(hmg_global=0.495, group_bd=0.68, book=2.851008)
ROBOT["look"] = ROBOT["hmg_global"] * ROBOT["group_bd"]
BD_VALUE = {"보수": 5.2, "기본": round((5.2 * 30) ** 0.5, 1), "낙관": 30.0}


def robot_ps(bd_value, look=None):
    look = ROBOT["look"] if look is None else look
    return (look * bd_value - ROBOT["book"]) * 1e12 / SHARES


def run(name, a, per=None, pbr=None, fx27=None, eps_mult=1.0, opm27=None, bd=None):
    per = a["per"] if per is None else per
    pbr = a["pbr"] if pbr is None else pbr
    fx27 = a["fx27"] if fx27 is None else fx27
    opm27 = a["opm27"] if opm27 is None else opm27
    rev26 = H1_26["rev"] + a["q3_rev"] + a["q4_rev"]
    op26 = H1_26["op"] + a["q3_op"] + a["q4_op"]
    ni_2h = (a["q3_op"] + a["q4_op"]) * CONV
    ni26 = H1_26["ni_p"] + ni_2h
    div_2h = 2 * DPS_Q * SHARES / 1e12                     # 2Q(9/30 지급) + 3Q(10월 결정 가정)
    eq26 = EQ_P_2Q26 + ni_2h - div_2h
    rev27 = rev26 * (1 + a["g27"])
    fx_chg = (fx27 / FX26 - 1) * 100
    fx_eff = FX_SENS * fx_chg
    op27 = rev27 * opm27 + fx_eff
    ni27 = op27 * CONV
    eps26 = ni26 * 1e12 / SHARES; eps27 = ni27 * 1e12 / SHARES * eps_mult
    bps26 = eq26 * 1e12 / SHARES
    tp_per = eps27 * per; tp_pbr = bps26 * pbr
    tp_core = WEIGHTS["PER"] * tp_per + WEIGHTS["PBR"] * tp_pbr      # 본업(자동차·금융·관계사)
    bd = BD_VALUE.get(name, BD_VALUE["기본"]) if bd is None else bd
    tp_robot = robot_ps(bd)
    tp = tp_core + tp_robot
    # roe27 평균자본 = 2026E말 지배지분 + 2027E 순이익 중 유보분(총주주환원 35% 가정)의 절반
    return dict(name=name, rev26=rev26, op26=op26, opm26=op26 / rev26, ni26=ni26, eps26=eps26, eq26=eq26, bps26=bps26,
                rev27=rev27, op27=op27, opm27_rep=op27 / rev27, fx27=fx27, fx_chg=fx_chg, fx_eff=fx_eff, ni27=ni27, eps27=eps27,
                roe27=ni27 / (eq26 + ni27 * (1 - 0.35) / 2), per=per, pbr=pbr, tp_per=tp_per, tp_pbr=tp_pbr,
                tp_core=tp_core, bd=bd, tp_robot=tp_robot, tp=tp, upside=tp / PRICE - 1)


def rating(up):
    return "BUY" if up >= 0.15 else ("HOLD" if up >= -0.05 else "SELL")


if __name__ == "__main__":
    out = {"base_date": "2026-10-06", "price_date": PX["005380"]["date"], "price": PRICE, "pref_px": PREF_PX,
           "common": COMMON, "pref": PREF, "shares": SHARES, "mcap": MCAP, "conv": CONV,
           "fx_q": FX_Q, "fx_spot": FX_SPOT, "fx26": FX26, "fx_sens": FX_SENS, "weights": WEIGHTS,
           "q": {k: dict(rev=v[0], op=v[1], opm=v[1] / v[0], ni_p=v[2]) for k, v in Q.items()},
           "fy": {y: dict(rev=v[0], op=v[1], opm=v[1] / v[0], ni_p=v[2]) for y, v in FY.items()},
           "hist": hist[["year", "px", "eps", "bps", "per", "pbr", "roe"]].to_dict("records"), "scen": {}}
    for k, a in ASSUMP.items():
        out["scen"][k] = run(k, a)
    b = ASSUMP["기본"]; base = out["scen"]["기본"]
    # 현재 배수 (기준가 347,000)
    ttm = sum(v[2] for v in Q.values())
    out["now"] = dict(ttm_ni=ttm, per_ttm=PRICE / (ttm * 1e12 / SHARES), pbr_2q=PRICE / (EQ_P_2Q26 * 1e12 / SHARES),
                      per_26=PRICE / base["eps26"], per_27=PRICE / base["eps27"], pbr_26=PRICE / base["bps26"],
                      dy=DPS_Q * 4 / PRICE, roe_ttm=ttm / EQ_P_2Q26)
    h = hist[hist.year != 2020]
    out["hist_stats"] = dict(per_med=float(h.per.median()), per_mean=float(h.per.mean()), pbr_med=float(hist.pbr.median()),
                             pbr_mean=float(hist.pbr.mean()), pbr_min=float(hist.pbr.min()), pbr_max=float(hist.pbr.max()))
    # 민감도 1: 2027E 환율 × 목표 PER → 목표가 (PBR 0.70 고정)
    fxs = [1_250, 1_300, 1_360, 1_420, 1_500]; pers = [6.5, 7.0, 8.0, 9.0, 9.5]
    out["sens_fx_per"] = {"fx": fxs, "per": pers, "tp": [[run("x", b, fx27=f, per=p)["tp"] for p in pers] for f in fxs],
                          "eps": [run("x", b, fx27=f)["eps27"] for f in fxs]}
    # 민감도 2: 목표 PER × 목표 PBR → 목표가
    pbrs = [0.55, 0.60, 0.70, 0.80, 0.85]
    out["sens_per_pbr"] = {"per": pers, "pbr": pbrs, "tp": [[run("x", b, per=p, pbr=q)["tp"] for q in pbrs] for p in pers]}
    # 민감도 3: 2027E 영업이익률(환율 중립) × 환율 → 2027E EPS
    opms = [0.056, 0.060, 0.063, 0.067, 0.070]
    out["sens_opm_fx"] = {"opm": opms, "fx": fxs, "eps": [[run("x", b, opm27=o, fx27=f)["eps27"] for f in fxs] for o in opms]}
    # 역산: 현재가 347,000원을 정당화하는 조건
    out["implied"] = dict(
        per_on_27=PRICE / base["eps27"],
        pbr_on_26=PRICE / base["bps26"],
        # PER 8.0x·PBR 0.70x 고정 시 필요한 2027E EPS → 환율 중립 영업이익률
        eps_need=(PRICE - 0.5 * base["tp_pbr"] - base["tp_robot"]) / (0.5 * b["per"]))
    # 로봇: 기준주가·고점이 내포하는 BD 100% 가치 (본업 가치는 기본 시나리오로 고정)
    bd_implied = lambda p: ((p - base["tp_core"]) * SHARES / 1e12 + ROBOT["book"]) / ROBOT["look"]
    out["robot"] = dict(ROBOT, bd_value=BD_VALUE, ps={k: robot_ps(v) for k, v in BD_VALUE.items()},
                        implied_bd_at_price=bd_implied(PRICE), implied_bd_at_peak=bd_implied(750_000), peak=750_000,
                        sens={"bd": [5.2, 12.5, 30.0, 60.0, 134.0], "look": [0.25, ROBOT["look"], 0.45],
                              "ps": [[robot_ps(v, l) for l in [0.25, ROBOT["look"], 0.45]] for v in [5.2, 12.5, 30.0, 60.0, 134.0]]})
    ni_need = out["implied"]["eps_need"] * SHARES / 1e12
    out["implied"]["opm_need"] = (ni_need / CONV - base["fx_eff"]) / base["rev27"]
    # 교차확인: 상장 관계기업 지분 시가 (2026 반기보고서 지분율 × 발행주식 × 10/2 종가)
    stakes = {"기아": (0.3517, 390_412_998, PX["000270"]["close"]), "현대건설": (0.2095, 111_355_765, PX["000720"]["close"]),
              "현대위아": (0.2535, 27_195_083, PX["011210"]["close"])}
    sv = {k: r * n * p / 1e12 for k, (r, n, p) in stakes.items()}
    out["stakes"] = dict(value=sv, total=sum(sv.values()), share_of_mcap=sum(sv.values()) / MCAP,
                         per_share=sum(sv.values()) * 1e12 / SHARES, book_kia=22.805024)
    out["rating"] = {k: rating(v["upside"]) for k, v in out["scen"].items()}
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    for k, v in out["scen"].items():
        print(k, "26E 매출 %.1f OP %.2f(%.1f%%) EPS %.0f BPS %.0f | 27E OP %.2f(환율 %+.2f) EPS %.0f | PER %.0f PBR %.0f 본업 %.0f + 로봇 %.0f(BD %.1f조) -> TP %.0f (%+.1f%%) %s" % (
            v["rev26"], v["op26"], v["opm26"] * 100, v["eps26"], v["bps26"], v["op27"], v["fx_eff"], v["eps27"],
            v["tp_per"], v["tp_pbr"], v["tp_core"], v["tp_robot"], v["bd"], v["tp"], v["upside"] * 100, out["rating"][k]))
    print("robot", {k: v for k, v in out["robot"].items() if k != "sens"})
    print("CONV %.3f FX26 %.1f spot %.1f sens %.3f MCAP %.2f now" % (CONV, FX26, FX_SPOT, FX_SENS, MCAP), out["now"])
    print("hist", out["hist_stats"]); print("implied", out["implied"]); print("stakes", out["stakes"])
