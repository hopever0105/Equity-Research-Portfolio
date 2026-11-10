"""오리온(271560) 밸류에이션 모델. 단위: 억원(주당·배수 제외). 실행: python valuation/오리온/model.py
출력: results.json (보고서·민감도용). 모든 가정은 ASSUMP 에 모아 둠. 출처는 주석.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

# ───────────────────────── 기준 데이터 (확인값)
PRICE = 112_600            # 2026-10-22 KRX 종가(pykrx adjusted=False, 시총 4,450,941,528,800원과 일치). 112,400은 수정주가(Naver)
SHARES = 39_528_788        # 사업보고서(2025.12) 유통주식수 = 자기주식 7,344주 소각(2026-06-23 예정) 후 발행주식수
MCAP = PRICE * SHARES / 1e8
FY25 = dict(rev=33_324.4, op=5_582.6, da=1_620 + 26.6, ni_parent=3_827.0, capex=1_225.6 + 237.6)  # DART 사업보고서, DB 유형자산감가상각비 1,619.55
H1_26 = dict(rev=18_239.4, op=2_980.4, ni=2_134.1)  # DART 반기(누적): 매출 1,823,941백만, 영업이익 298,043백만
H1_25 = dict(rev=15_789.4, op=2_528.3)
# 2026-06-30 연결재무상태표 (DART 반기)
BS = dict(cash=6_632.9, deposit=6_979.2, fvpl=50.0, borrowing=0.0,       # 차입금: FY25 단기차입금 0(2024 6.5억 상환), 반기 BS 차입금 항목 없음
          lease=272.2 + 1_223.3,                                           # 유동 272.2 + 비유동 1,223.3 (FY25말 355 → 급증, 원인 확인 필요)
          equity_method=6_845.5, nci=1_151.3)
INTERIM_DIV = 1_750 * SHARES / 1e8   # 분기배당 1,750원, 기준일 7/21(주가는 배당락 후), 지급 8/6 → 6/30 현금에서 차감
HIST_PER = {2021: 15.9, 2022: 12.9, 2023: 12.2, 2024: 7.7, 2025: 10.9}  # 연말 종가/지배순이익, 주식수 고정

# ───────────────────────── 월별 잠정실적(4개 법인 순매출 합, 영업이익 합) → 26E 도출
m = pd.read_csv(HERE / "monthly_provisional.csv")
m = m.set_index(m.rcept_dt.astype(str))
def ssum(keys, col): return float(sum(m.loc[k, col] for k in keys))
M25 = ["20250225", "20250318", "20250415", "20250520", "20250617", "20250715", "20250819", "20250916", "20251021", "20251118", "20251216"]  # 2025.1~11월
M26 = ["20260225", "20260313", "20260421", "20260515", "20260616", "20260709", "20260807", "20260910", "20261013"]  # 2026.1~9월
sales25_4c = {k: m.loc[k, "m_tot"] for k in M25}
op25_4c = {k: m.loc[k, ["op_kr", "op_cn", "op_vn", "op_ru"]].sum() for k in M25}
sales26_4c = {k: m.loc[k, "m_tot"] for k in M26}
op26_4c = {k: m.loc[k, ["op_kr", "op_cn", "op_vn", "op_ru"]].sum() for k in M26}
ratio_s = H1_26["rev"] / sum(list(sales26_4c.values())[:6])     # 연결/4법인합 매출 비율(1H26 실측)
ratio_s25 = H1_25["rev"] / sum(list(sales25_4c.values())[:6])
ratio_o = H1_26["op"] / sum(list(op26_4c.values())[:6])         # 연결/4법인합 영업이익 비율
FY25_OP_4C = 1868 + 2417 + 965 + 465                            # 2026-02-05 공시 연간 국가별 영업이익 합
dec25_sales_4c = FY25["rev"] / ratio_s25 - sum(sales25_4c.values())   # 12월 역산(공시 없음)
q4_25_sales_4c = sum(list(sales25_4c.values())[-2:]) + dec25_sales_4c
dec25_op_4c = FY25_OP_4C - sum(op25_4c.values())
q4_25_op_4c = sum(list(op25_4c.values())[-2:]) + dec25_op_4c
nine_s26 = sum(sales26_4c.values()); nine_s25 = sum(list(sales25_4c.values())[:9])
nine_o26 = sum(op26_4c.values());   nine_o25 = sum(list(op25_4c.values())[:9])
q3_s26 = sum(list(sales26_4c.values())[6:9]); q3_s25 = sum(list(sales25_4c.values())[6:9])

# ───────────────────────── 시나리오 가정
ASSUMP = {
    "보수": dict(q4_yoy=0.03, q4_opm=0.165, g=[0.04, 0.03, 0.03, 0.03, 0.03], opm=0.155, wacc=0.085, tg=0.015,
               per=10.0, ev_ebitda=4.0, dcf_exit=5.0, equity_method=[-690, -690, -690, -690, -690, -690]),
    "기본": dict(q4_yoy=0.07, q4_opm=0.175, g=[0.07, 0.06, 0.05, 0.05, 0.04], opm=0.165, wacc=0.080, tg=0.020,
               per=12.5, ev_ebitda=5.0, dcf_exit=7.0, equity_method=[-690, -400, -400, -400, -400, -400]),
    "낙관": dict(q4_yoy=0.10, q4_opm=0.185, g=[0.09, 0.08, 0.07, 0.06, 0.05], opm=0.175, wacc=0.075, tg=0.025,
               per=14.5, ev_ebitda=6.2, dcf_exit=9.4, equity_method=[-690, -150, -150, -150, -150, -150]),
}
COMMON = dict(tax=0.27,            # FY25 유효세율 28.5%(원천세 포함) → 27%
              da_pct=0.048,        # FY25 4.9%, 1H26 약 4.7%
              capex_maint=0.040,   # FY25 설비투자 4.4%
              nwc_pct=0.03,        # 매출 증가분 대비
              fin_yield=0.035,     # 현금+예치금 수익률(1H26 순금융수익 424억/반기 중 FX 포함)
              nci_pct=0.02,        # FY25 2.0%
              payout=0.40,         # 배당성향 36.2%(FY25) → 40% 가정(분기배당 도입)
              program_2h26=1300, program_27=2600, program_28=1739)  # 기업가치제고계획: 진천4,600·하노이3 1,300·트베르2,400(총 8,300억), 5월 공정율 36/57/11% → 잔여 5,639억 배분
WEIGHTS = {"DCF": 0.25, "PER": 0.45, "EV/EBITDA": 0.30}   # 근거: 보고서 3장 (DCF 영구가치 비중 >75%, 시장 내재 할인율과 괴리)


def run(name, a, c=COMMON, wacc=None, tg=None, per=None, eps_mult=1.0, exit_mult=None):
    wacc = a["wacc"] if wacc is None else wacc
    tg = a["tg"] if tg is None else tg
    per = a["per"] if per is None else per
    # 26E
    q4_s = q4_25_sales_4c * (1 + a["q4_yoy"])
    s26_4c = nine_s26 + q4_s
    rev26 = (nine_s26 * ratio_s) + q4_s * ratio_s
    op26 = (nine_o26 + q4_s * a["q4_opm"]) * ratio_o
    rev = [rev26]; op = [op26]
    for g in a["g"]:
        rev.append(rev[-1] * (1 + g)); op.append(rev[-1] * a["opm"])          # 27E~31E
    yrs = [2026, 2027, 2028, 2029, 2030, 2031]
    da = [r * c["da_pct"] for r in rev]
    capex = []
    for i, r in enumerate(rev):
        prog = {1: c["program_27"], 2: c["program_28"]}.get(i, 0)
        capex.append(r * c["capex_maint"] + prog)
    # 2026E 설비투자: 1H26 실적(유형 1,686+무형 51) + 2H 정상 + 프로그램
    h2_rev = rev26 - H1_26["rev"]; h2_op = op26 - H1_26["op"]
    capex_h2 = h2_rev * c["capex_maint"] + c["program_2h26"]
    capex[0] = 1_686.2 + 50.6 + capex_h2
    nwc = [0] + [(rev[i] - rev[i - 1]) * c["nwc_pct"] for i in range(1, 6)]
    fcff = [op[i] * (1 - c["tax"]) + da[i] - capex[i] - nwc[i] for i in range(6)]
    # 2H26 FCFF → 2026-12-31 순현금
    fcff_h2 = h2_op * (1 - c["tax"]) + h2_rev * c["da_pct"] - capex_h2 - h2_rev * 0.0
    gross_cash = BS["cash"] + BS["deposit"] + BS["fvpl"]
    cash_1231 = gross_cash - INTERIM_DIV + fcff_h2
    # DCF: 2026-12-31 시점 가치(2027E~2031E FCFF + TV)
    pv = sum(fcff[i] / (1 + wacc) ** i for i in range(1, 6))
    tv_fcff = op[5] * (1 - c["tax"]) * (1 + tg) + da[5] * (1 + tg) - da[5] * (1 + tg) * 1.05 - rev[5] * tg * c["nwc_pct"]
    tv = tv_fcff / (wacc - tg); pv_tv = tv / (1 + wacc) ** 5
    ev_dcf = pv + pv_tv
    bridge = cash_1231 - BS["borrowing"] - BS["lease"] + BS["equity_method"] - BS["nci"]
    eq_dcf = ev_dcf + bridge
    ebitda31 = op[5] + da[5]
    tv_mult = tv / ebitda31                                          # DCF가 내포하는 영구가치 EV/EBITDA
    # 목표가에 쓰는 DCF = 출구배수 방식(잔존가치 = 2031E EBITDA × 출구배수). 영구성장 방식(tp_dcf_pg)은 교차확인.
    xm = a["dcf_exit"] if exit_mult is None else exit_mult
    pv_tv_x = xm * ebitda31 / (1 + wacc) ** 5
    ev_dcf_x = pv + pv_tv_x
    tp_dcf = (ev_dcf_x + bridge) * 1e8 / SHARES
    # 순이익·EPS
    ni = []; cash = cash_1231
    for i, y in enumerate(yrs):
        fin = 850 if i == 0 else cash * c["fin_yield"]
        pre = op[i] + fin + a["equity_method"][i]
        taxb = max(pre - a["equity_method"][i], 0) * c["tax"]         # 지분법 손실은 비용 불인정 가정
        n = (pre - taxb) * (1 - c["nci_pct"]); ni.append(n)
        if i >= 1:
            cash += ni[i] + da[i] - capex[i] - nwc[i] - n * c["payout"]
    eps = [n * 1e8 / SHARES for n in ni]
    tp_per = eps[1] * eps_mult * per                                # 12M fwd = 2027E EPS
    # EV/EBITDA (2026E EBITDA)
    ebitda26 = op[0] + da[0]
    ev_mult = a["ev_ebitda"] * ebitda26
    eq_mult = ev_mult + bridge
    tp_ev = eq_mult * 1e8 / SHARES
    tp_dcf_pg = eq_dcf * 1e8 / SHARES
    tp = WEIGHTS["DCF"] * tp_dcf + WEIGHTS["PER"] * tp_per + WEIGHTS["EV/EBITDA"] * tp_ev
    return dict(name=name, rev=rev, op=op, da=da, capex=capex, nwc=nwc, fcff=fcff, ni=ni, eps=eps,
                opm=[op[i] / rev[i] for i in range(6)], ebitda26=ebitda26, fcff_h2=fcff_h2, cash_1231=cash_1231,
                bridge=bridge, pv=pv, pv_tv=pv_tv, tv_share=pv_tv_x / ev_dcf_x, tv_share_pg=pv_tv / ev_dcf, ev_dcf=ev_dcf, ev_dcf_x=ev_dcf_x, eq_dcf=eq_dcf, dcf_exit=xm,
                tv_mult=tv_mult, ebitda31=ebitda31, tv=tv,
                tp_dcf=tp_dcf, tp_dcf_pg=tp_dcf_pg, tp_per=tp_per, tp_ev=tp_ev, tp=tp, upside=tp / PRICE - 1, wacc=wacc, tg=tg, per=per)


def rating(up):
    return "Buy" if up >= 0.15 else ("Hold" if up >= -0.05 else "Sell")


# 출처: Rf·Kd = 한국은행 ECOS 817Y002(시장금리 일별) 2026-10-22: 국고채(10년) 4.152%, 회사채(3년, AA-, 민평) 4.516%
#       ERP = Damodaran ctryprem(2026-01 판): Korea 4.87%, China 5.14%, Vietnam 8.13%, Russia 8.13% (성숙시장 4.23%)
RF, KD_PRE = 0.04152, 0.04516
ERP = {"한국": 0.0487, "중국": 0.0514, "베트남": 0.0813, "러시아": 0.0813}
# 매출 비중: 2026.1~9월 4개 법인 순매출(한국 8,800 · 중국 11,717 · 베트남 3,983 · 러시아 3,047, 합 27,547)
MIX = {"한국": 8800 / 27547, "중국": 11717 / 27547, "베트남": 3983 / 27547, "러시아": 3047 / 27547}


def wacc_table(country_adj=True, beta=0.70, tax=0.25, dv=0.05):
    erp = sum(MIX[k] * ERP[k] for k in MIX) if country_adj else ERP["한국"]
    ke = RF + beta * erp; kd = KD_PRE * (1 - tax)
    return dict(country_adj=country_adj, rf=RF, erp=erp, beta=beta, ke=ke, kd_pre=KD_PRE, tax=tax, kd_post=kd, dv=dv,
                wacc=(1 - dv) * ke + dv * kd)


if __name__ == "__main__":
    out = {"price": PRICE, "shares": SHARES, "mcap": MCAP, "scen": {}, "wacc_calc": wacc_table(True), "wacc_calc_noadj": wacc_table(False),
           "mix": MIX, "erp": ERP, "weights": WEIGHTS,
           "rev_build": dict(ratio_s=ratio_s, ratio_o=ratio_o, nine_s26=nine_s26, nine_s25=nine_s25, nine_o26=nine_o26, nine_o25=nine_o25,
                             q3_s26=q3_s26, q3_s25=q3_s25, q4_25_sales_4c=q4_25_sales_4c, dec25_sales_4c=dec25_sales_4c,
                             q4_25_op_4c=q4_25_op_4c, dec25_op_4c=dec25_op_4c),
           "bs": BS, "interim_div": INTERIM_DIV, "hist_per": HIST_PER}
    for k, a in ASSUMP.items():
        out["scen"][k] = run(k, a)
    b = ASSUMP["기본"]; base = out["scen"]["기본"]
    # 민감도 1: WACC × 영구성장률 → DCF 주당가치
    ws = [0.070, 0.075, 0.080, 0.085, 0.090]; gs = [0.010, 0.015, 0.020, 0.025, 0.030]
    out["sens_dcf"] = {"wacc": ws, "g": gs, "tp": [[run("x", b, wacc=w, tg=g)["tp_dcf_pg"] for g in gs] for w in ws]}
    # 민감도 1b: 출구배수 방식 DCF (영구성장 대신 2031E EBITDA × 출구 EV/EBITDA), WACC × 출구배수
    xm = [5.0, 7.0, round(base["tv_mult"], 1)]
    out["sens_exit"] = {"wacc": ws, "mult": xm, "ebitda31": base["ebitda31"],
                        "tp": [[run("x", b, wacc=w, exit_mult=m)["tp_dcf"] for m in xm] for w in ws]}
    # 민감도 2: PER × 2027E EPS(기본 대비 -10%~+10%) → PER법 주당가치
    pers = [10.0, 11.0, 12.5, 14.0, 15.0]; ems = [0.90, 0.95, 1.00, 1.05, 1.10]
    out["sens_per"] = {"per": pers, "eps_mult": ems, "eps_base": base["eps"][1],
                       "tp": [[base["eps"][1] * em * p for em in ems] for p in pers]}
    # 민감도 3: 종합 목표가 WACC × PER
    out["sens_total"] = {"wacc": ws, "per": pers, "tp": [[run("x", b, wacc=w, per=p)["tp"] for p in pers] for w in ws]}
    # 역산 DCF: 현재가(112,600원)가 내포하는 할인율(기본 시나리오 현금흐름 고정, g=2%)
    lo, hi = 0.08, 0.30
    for _ in range(60):
        mid = (lo + hi) / 2
        if run("x", b, wacc=mid)["tp_dcf_pg"] > PRICE: lo = mid
        else: hi = mid
    out["implied_wacc"] = mid
    # 국가위험 가산 유무별 DCF (기본 시나리오 현금흐름, WACC만 교체)
    wa, wb = out["wacc_calc_noadj"]["wacc"], out["wacc_calc"]["wacc"]
    ra, rb = run("A", b, wacc=wa), run("B", b, wacc=wb)
    out["dcf_cases"] = {"가산없음": dict(wacc=wa, tp_dcf=ra["tp_dcf"], tp_dcf_pg=ra["tp_dcf_pg"], tv_share=ra["tv_share"], tv_share_pg=ra["tv_share_pg"], tp=ra["tp"]),
                        "가산있음": dict(wacc=wb, tp_dcf=rb["tp_dcf"], tp_dcf_pg=rb["tp_dcf_pg"], tv_share=rb["tv_share"], tv_share_pg=rb["tv_share_pg"], tp=rb["tp"])}
    # 역산: (a) 현재가를 맞추는 영구성장률(WACC 8.0%), (b) 현재가를 맞추는 FCFF 전체 축소율
    lo, hi = -0.30, 0.03
    for _ in range(60):
        mid = (lo + hi) / 2
        if run("x", b, tg=mid)["tp_dcf_pg"] < PRICE: lo = mid
        else: hi = mid
    out["implied_tg"] = mid
    base_ev = base["ev_dcf"]; need_ev = MCAP - base["bridge"]
    out["implied_fcff_factor"] = need_ev / base_ev     # 시장가가 내포하는 EV / 영구성장 DCF EV
    out["implied_fcff_factor_x"] = need_ev / base["ev_dcf_x"]   # 시장가가 내포하는 EV / 출구배수 DCF EV
    # FCFF 겹침 점검: DCF 현금흐름 기간 vs 브리지에 들어간 현금 기간
    out["overlap_check"] = dict(dcf_years=[2027, 2028, 2029, 2030, 2031], bridge_cash_asof="2026-06-30 잔액 + 2H26E FCFF(2026-07~12) − 8월 분기배당",
                                dcf_includes_2h26=False, double_count=False)
    # 현재 배수(기준가 112,600 / 시총 기준)
    base0 = out["scen"]["기본"]
    # 현재 배수(기준가 112,600 / 시총 기준)
    base0 = out["scen"]["기본"]
    out["now"] = dict(per_26=PRICE / base0["eps"][0], per_27=PRICE / base0["eps"][1],
                      ev_ebitda_26=(MCAP - base0["bridge"] - 0) / base0["ebitda26"] if False else (MCAP - (base0["cash_1231"] - BS["lease"] + BS["equity_method"] - BS["nci"])) / base0["ebitda26"],
                      pbr=MCAP / 40_655.5, dy=3500 / PRICE)
    # 가중치 민감도(기본 시나리오): DCF 비중이 목표가에 미치는 영향
    out["tp_by_weight"] = {}
    for wd in (0.0, 0.25, 0.4):
        rest = 1 - wd; wp = rest * WEIGHTS["PER"] / (WEIGHTS["PER"] + WEIGHTS["EV/EBITDA"]); we = rest - wp
        out["tp_by_weight"][f"DCF {int(wd*100)}%"] = dict(
            per_w=wp, ev_w=we, tp={k: wd * v["tp_dcf"] + wp * v["tp_per"] + we * v["tp_ev"] for k, v in out["scen"].items()})
    out["rating"] = {k: rating(v["upside"]) for k, v in out["scen"].items()}
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in out["scen"].items():
        print(k, "매출26E %.0f(%.1f%%) OP26E %.0f EPS26/27 %.0f/%.0f | DCF %.0f PER %.0f EV %.0f -> TP %.0f (%+.1f%%) TV비중 %.0f%%" % (
            v["rev"][0], (v["rev"][0] / FY25["rev"] - 1) * 100, v["op"][0], v["eps"][0], v["eps"][1], v["tp_dcf"], v["tp_per"], v["tp_ev"],
            v["tp"], v["upside"] * 100, v["tv_share"] * 100))
    print("bridge %.0f cash1231 %.0f fcff_h2 %.0f ratio_s %.4f ratio_o %.4f dec25 %.0f" % (
        base["bridge"], base["cash_1231"], base["fcff_h2"], ratio_s, ratio_o, dec25_sales_4c))
    print("WACC", wacc_table())
