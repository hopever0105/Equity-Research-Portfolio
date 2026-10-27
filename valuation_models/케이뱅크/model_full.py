"""케이뱅크(279570) 전체 리포트용 모델 — 2026E ~ 2028E 이익 추정 + 잔여이익모델(RIM) + PBR–ROE 회귀.
model.py(약식 노트: 지속 ROE 가정 하나로 평가)와 달리, 대출 · 금리 · 대손 · 판관비를 직접 추정해 ROE 경로를 만들고 그 경로로 평가한다.
단위: 억원(비율·주당 제외). 실행: python valuation/케이뱅크/model_full.py  → results_full.json

실적 확인값(2026 반기보고서 '자금조달 및 운용 현황', '부문별 영업실적', '자산건전성', 투자설명서 2026-02-04)
- 평균잔액 대출금 2024 154,954(5.04%) · 2025 174,319(4.53%) · 1H26 189,063(4.52%, 연환산)
- 평균잔액 수익성자금 2024 235,669(4.59%) · 2025 292,034(3.90%) · 1H26 295,051(3.93%)
- 평균잔액 원가성자금(예수금 등) 2024 215,560(2.72%) · 2025 270,863(2.52%) · 1H26 271,858(2.40%)
- 충당금적립전이익 2024 3,864 · 2025 3,310 · 1H26 1,642 / 제충당금전입−환입 2024 2,536 · 2025 2,174 · 1H26 1,047
- 판매비와관리비 2024 1,826 · 2025 2,279 · 1H26 1,155 / 순이자이익 2024 4,815 · 2025 4,442 · 1H26 2,530
- 총여신(기말) 2024 162,670 · 2025 183,787 · 2Q26 197,857 / 고정이하여신비율 0.82 · 0.57 · 0.59% / 연체율 0.90 · 0.60 · 0.60%
- 두나무(업비트) 가상자산 예금 FY2025 58,327(전체 수신의 20.5%), 3Q25 74,883(24.6%), 2021말 52.9% / 펌뱅킹 수수료 FY2025 188억
"""
import json
from pathlib import Path

import numpy as np

import model as M          # 같은 폴더의 약식 모델(기준 데이터 · 회귀 · 카카오뱅크 값 재사용)

HERE = Path(__file__).resolve().parent

HIST = {   # 연도: (평균대출, 대출이율, 평균수익성자금, 수익성자금이율, 평균원가성자금, 조달이율, NII, 기타순이익X, 판관비, 순충당금, 순이익)
    2024: (154_954, .0504, 235_669, .0459, 215_560, .0272, 4_815, 875, 1_826, 2_536, 1_280.53),
    2025: (174_319, .0453, 292_034, .0390, 270_863, .0252, 4_442, 1_147, 2_279, 2_174, 1_126.09),
}
H1_26 = dict(nii=2_530, x=267, sga=1_155, prov=1_047, ni=600.75, loan_avg=189_063, earn_avg=295_051, fund_avg=271_858)
LOAN_2Q26, LOAN_2025 = 197_857, 183_787
VASP = dict(dep=58_327, share=0.205, fee=188)   # FY2025

# 시나리오 가정 (연간). 2026E 하반기는 연간값에서 상반기 실적을 뺀 값이 된다.
#   g: 총여신 증가율(기말), yL: 대출이율, yO: 대출 외 수익성자금 이율, cF: 조달이율, x: 비이자·기타 순이익(억),
#   sga_g: 판관비 증가율, cc: 순충당금/평균대출, tax: 실효세율, roe_lt: 2029년 이후 장기 ROE(서서히 수렴), w_plat: 카카오 프리미엄 반영
SC = {
    "보수": dict(g=[.10, .08, .07], yL=[.0445, .0430, .0420], yO=[.0275, .0262, .0257], cF=[.0237, .0228, .0225],
                 x=[600, 650, 700], sga_g=[.04, .08, .07], cc=[.0112, .0110, .0108], tax=[.01, .15, .22], roe_lt=.06, w_plat=0.0),
    "기본": dict(g=[.12, .11, .10], yL=[.0448, .0435, .0428], yO=[.0278, .0268, .0262], cF=[.0236, .0225, .0220],
                 x=[650, 800, 900], sga_g=[.03, .07, .06], cc=[.0110, .0105, .0100], tax=[.01, .10, .15], roe_lt=.08, w_plat=0.5),
    "낙관": dict(g=[.13, .14, .13], yL=[.0450, .0442, .0438], yO=[.0280, .0272, .0268], cF=[.0235, .0222, .0215],
                 x=[700, 950, 1100], sga_g=[.03, .06, .05], cc=[.0105, .0095, .0090], tax=[.01, .10, .20], roe_lt=.10, w_plat=1.0),
}
COE, G = 0.10, 0.025
PB_FLOOR = 0.35
YEARS = [2026, 2027, 2028]


def forecast(a):
    """평균잔액 × 이율로 순이자이익을 만들고, 충당금 · 판관비 · 세금을 빼 순이익과 보통주 ROE 경로를 만든다."""
    loan_end_prev = LOAN_2025
    earn_prev, fund_prev = H1_26["earn_avg"], H1_26["fund_avg"]
    ce = M.CE["4Q25"]                       # 2025말 보통주 자본(신종자본 차감)
    sga_prev = HIST[2025][8]
    out = []
    for i, y in enumerate(YEARS):
        loan_end = loan_end_prev * (1 + a["g"][i])
        L = (loan_end_prev + loan_end) / 2
        # 대출 외 수익성자금은 2026 평잔 수준에서 대출 증가분의 절반만큼 줄어든다(초과 유동성을 대출로 전환)
        earn = earn_prev + (L - (H1_26["loan_avg"] if i == 0 else out[-1]["L"])) * 0.5
        fund = fund_prev + (earn - earn_prev) * 0.9
        O = earn - L
        nii = L * a["yL"][i] + O * a["yO"][i] - fund * a["cF"][i]
        sga = sga_prev * (1 + a["sga_g"][i]) if i else max(H1_26["sga"] * 2 * (1 + a["sga_g"][i] / 2), sga_prev)
        prov = L * a["cc"][i]
        ppop = nii + a["x"][i] - sga
        pbt = ppop - prov
        ni = pbt * (1 - a["tax"][i])
        if y == 2026:   # 공모 신주(2,490억, 발행비 차감 순증 약 2,451억)가 1Q26에 들어옴
            ce_beg = ce
            ce = ce + 2_451 + ni
        else:
            ce_beg = ce
            ce = ce + ni
        out.append(dict(year=y, loan_end=loan_end, L=L, earn=earn, fund=fund, nii=nii, nim=nii / earn, x=a["x"][i], sga=sga,
                        cir=sga / (nii + a["x"][i]), ppop=ppop, prov=prov, cc=a["cc"][i], pbt=pbt, ni=ni, ce=ce,
                        roe=ni / ((ce_beg + ce) / 2), bps=ce * 1e8 / M.DIL, eps=ni * 1e8 / M.DIL))
        loan_end_prev, earn_prev, fund_prev, sga_prev = loan_end, earn, fund, sga
    return out


def rim(f, roe_lt, coe=COE, g=G):
    """잔여이익모델: 2Q26 보통주 자본 + 2026H2 ~ 2028E 잔여이익 현재가치 + 2029년 이후 (장기 ROE − COE) 잔여이익 영구가치.
    2026E는 하반기 몫(연간의 절반)만 반영. 평가기준일 2026-10-27 ≈ 2026 말까지 0.18년 → 단순화해 연말 할인."""
    bv = M.CE_NOW
    pv = 0.0
    ce_prev = M.CE_NOW
    for i, r in enumerate(f):
        ni = r["ni"] - H1_26["ni"] if i == 0 else r["ni"]
        ri = ni - coe * ce_prev
        pv += ri / (1 + coe) ** (i + 0.5)
        ce_prev = ce_prev + ni
    # 2029년 이후: ROE가 장기 ROE로 바로 수렴한다고 보고 고든 성장
    ri_t = (roe_lt - coe) * ce_prev
    tv = ri_t / (coe - g) / (1 + coe) ** (len(f) - 0.5)
    v = (bv + pv + tv) * 1e8 / M.DIL
    return v, dict(bv=bv, pv=pv, tv=tv)


def reg_value(roe, w):
    pb = M.ICPT + M.SLOPE * roe + w * M.KAKAO["premium"]
    pb = max(pb, PB_FLOOR)     # 회귀선은 ROE 4% 아래에서 0에 가까워지므로, 표본 최저 PBR(BNK 0.39)보다 조금 낮은 0.35를 바닥으로 둔다
    return M.CE_NOW * pb * 1e8 / M.DIL, pb


def run(name, a):
    f = forecast(a)
    v_rim, parts = rim(f, a["roe_lt"])
    roe27 = f[1]["roe"]
    v_reg, pb = reg_value(roe27, a["w_plat"])
    tp = 0.5 * v_rim + 0.5 * v_reg
    return dict(name=name, f=f, rim=v_rim, rim_parts=parts, reg=v_reg, reg_pb=pb, roe27=roe27, tp=tp,
                upside=tp / M.PRICE - 1, pbr_tp=tp * M.DIL / (M.CE_NOW * 1e8), assump=a)


def vasp_sens():
    """업비트(두나무) 예치금 관련 민감도. VASP 예치금 이용료율·운용 스프레드는 공시되지 않아 가정값별로 표시."""
    rows = []
    for spread in (0.005, 0.010, 0.015):
        lost = VASP["dep"] * spread + VASP["fee"]          # 예치금 운용 스프레드 + 펌뱅킹 수수료
        rows.append(dict(spread=spread, lost_pbt=lost, lost_ps=lost * (1 - 0.20) * 1e8 / M.DIL))
    rate = [dict(bp=bp, d_pbt=-VASP["dep"] * bp / 1e4) for bp in (10, 25, 50)]
    return dict(exit=rows, rate=rate)


if __name__ == "__main__":
    res = {k: run(k, a) for k, a in SC.items()}
    b = res["기본"]
    # 민감도: 장기 ROE × COE → RIM 주당가치 (기본 이익 경로)
    roes, coes = [0.06, 0.07, 0.08, 0.09, 0.10], [0.09, 0.095, 0.10, 0.105, 0.11]
    sens_rim = [[rim(b["f"], r, c)[0] for c in coes] for r in roes]
    # 민감도: 2027E 신용비용 × 총여신 증가율 → 2027E ROE
    ccs, gs = [0.009, 0.010, 0.011, 0.012, 0.013], [0.08, 0.10, 0.12, 0.14]
    sens_roe = [[forecast({**SC["기본"], "cc": [SC["기본"]["cc"][0], c, c], "g": [SC["기본"]["g"][0], g, g]})[1]["roe"] for g in gs] for c in ccs]
    out = dict(base_date="2026-10-27", price=M.PRICE, ipo_px=M.IPO_PX, dil=M.DIL, ce_now=M.CE_NOW, coe=COE, g=G,
               scen={k: v for k, v in res.items()}, rating={k: ("BUY" if v["upside"] >= .15 else "HOLD" if v["upside"] >= -.05 else "SELL") for k, v in res.items()},
               sens_rim=dict(roe=roes, coe=coes, v=sens_rim), sens_roe=dict(cc=ccs, g=gs, roe=sens_roe), vasp=vasp_sens(),
               hist={y: dict(zip(["L", "yL", "earn", "yE", "fund", "cF", "nii", "x", "sga", "prov", "ni"], v)) for y, v in HIST.items()},
               h1=H1_26, loan=dict(y2024=162_670, y2025=LOAN_2025, q2_26=LOAN_2Q26), vasp_base=VASP)
    (HERE / "results_full.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    for k, v in res.items():
        f = v["f"]
        print(k, " | ".join(f"{r['year']}E NII {r['nii']:,.0f} NIM {r['nim']*100:.2f}% PPOP {r['ppop']:,.0f} 충당 {r['prov']:,.0f} NI {r['ni']:,.0f} ROE {r['roe']*100:.1f}%" for r in f))
        print(f"   RIM {v['rim']:,.0f} (BV {v['rim_parts']['bv']:,.0f} PV {v['rim_parts']['pv']:,.0f} TV {v['rim_parts']['tv']:,.0f}) | 회귀 {v['reg']:,.0f} (PBR {v['reg_pb']:.2f}, ROE27 {v['roe27']*100:.1f}%) -> TP {v['tp']:,.0f} ({v['upside']*100:+.1f}%) {out['rating'][k]}")
    print("vasp", out["vasp"])
