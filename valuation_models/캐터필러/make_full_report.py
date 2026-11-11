"""캐터필러_리서치리포트_20261109.docx/.pdf — 2026-08-24 리포트를 2026-11-09 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_yf.csv. 실행: python valuation/캐터필러/make_full_report.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.report_kit import Rep, to_pdf, price_chart, football_chart, bar_chart, W

R = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
S = R["scen"]; B, L, H = S["기본"], S["보수"], S["낙관"]
PRICE, TP, UP, RATING, O, K = R["price"], R["tp"], R["upside"], R["rating"], R["orig"], R["key"]
SA = R["scen_assump"]; FB = B["rows"]
A_, Qk, P3, Y9, OL, BB = K["annual"], K["quarterly"], K["q3_26_press"], K["ytd_9m26"], K["outlook_2026_10q"], K["balance_20260930"]
SG = P3["segments"]
b = lambda x: f"${x/1e3:,.1f}B"
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
usd = lambda x: f"${x:,.0f}"

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / "full_price.png", "최근 2년 종가($), 기준일 2026-11-09", unit="$", alt=[(H["tp"], "낙관")])
ql = ["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"]
bar_chart(ql, [("매출($B)", [Qk["revenue"][q] / 1e3 for q in ql], "#1F3864")], HERE / "full_q.png",
          "분기 매출($B)과 영업이익률(GAAP)", line=("영업이익률", [Qk["op_income"][q] / Qk["revenue"][q] for q in ql]), ylab="$B")
yrs = ["2023A", "2024A", "2025A", "2026E", "2027E", "2028E"]
revs = [A_["revenue"][y] for y in ("2023", "2024", "2025")] + [r["rev"] for r in FB[:3]]
bar_chart(yrs, [("매출($B)", [v / 1e3 for v in revs], "#1F3864")],
          HERE / "full_earn.png", "연간 매출($B)과 성장률 — 음영은 추정(기본)", est_from=3,
          line=("매출 성장률", [0.0] + [revs[i] / revs[i - 1] - 1 for i in range(1, len(revs))]))
football_chart([("A. DCF (WACC %.1f%%)" % (R["wacc"] * 100), L["va"], B["va"], H["va"]), ("B. 2027E EPS × 피어 선행 PER", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 50 : B 50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$")

SUB = f"백로그 {b(R['backlog'])}·매출 +17% — 실적은 좋지만, 현재가는 2027E 이익의 {R['per27_now']:.0f}배로 기계 업종 평균({R['fpe_med']:.0f}배)보다 비싸다"
MKT = [["현재주가 (2026.11.09 종가)", usd(PRICE)], ["시가총액", b(R["mcap"])], ["MP&E 순차입 (9월말 + Fabick 인수)", b(R["net_debt"])],
       ["52주 최고 / 최저 (장중)", f"{usd(R['hi52'])} / {usd(R['lo52'])}"], ["PER (2026E 자체)", f"{R['per26_now']:.1f}배"],
       ["PER (2027E 기본)", f"{R['per27_now']:.1f}배"], ["피어 선행 PER 중앙값", f"{R['fpe_med']:.1f}배"],
       ["수주잔고 (9월말)", b(R["backlog"])], ["분기배당", "$1.63 (10월 유지)"], ["원래 리포트 (2026.08.24)", f"{O['rating']} · {usd(O['tp'])}"]]
ALT = [f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]

rp = Rep("산업재 (건설·광산·에너지 장비)", "2026년 11월 9일")
rp.cover("캐터필러 (Caterpillar, NYSE: CAT)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, $M)")
rows = [["항목", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출"] + [f0(A_["revenue"][y]) for y in ("2023", "2024", "2025")] + [f0(r["rev"]) for r in FB[:3]],
        ["영업이익"] + [f0(A_["op_income"][y]) for y in ("2023", "2024", "2025")] + [f0(r["op"]) for r in FB[:3]],
        ["영업이익률"] + [pc(A_["op_income"][y] / A_["revenue"][y]) for y in ("2023", "2024", "2025")] + [pc(r["op"] / r["rev"]) for r in FB[:3]],
        ["순이익"] + [f0(A_["net_income"][y]) for y in ("2023", "2024", "2025")] + [f0(r["ni"]) for r in FB[:3]],
        ["희석 EPS ($)"] + [f"{A_['eps_diluted'][y]:.2f}" for y in ("2023", "2024", "2025")] + [f"{r['eps']:.2f}" for r in FB[:3]]]
rp.table(rows, [24, 12, 12, 12, 13, 13, 14], hl_cols=(4, 5, 6),
         note="자료: SEC 10-K·10-Q·8-K. 2026E = 9개월 실적 + 4분기 추정(매출 +5%, 영업이익률 18.5%). 2026E 영업이익에는 IEEPA 관세 환급 $520M(일회성)이 들어 있고, "
              "2027E부터는 환급 없이 관세 비용 연 약 $2.2B가 이어진다고 봤다. 순이익 = (영업이익 + 영업외 $200M) × (1 − 23%).")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", f"실적은 좋다 — 3Q26 매출 {b(P3['revenue'])}(+17%), 조정 EPS ${P3['adj_eps']:.2f}, 수주잔고 사상 최대 {b(R['backlog'])}",
              [f"세 사업부문 모두 매출 +15~18%, Power & Energy 이익 +31%. 9개월 MP&E 잉여현금흐름 {b(Y9['mpe_fcf'])}(전년 {b(Y9['mpe_fcf_9m25'])})",
               "2026년 매출 '10%대 중후반' 성장 가이던스 유지. 데이터센터 발전기·가스 압축 수요가 계속 늘고 있다"])
rp.thesis_box("②", f"관세 비용 연 {b(OL['tariff_cost_ex_ieepa'])} — 실적 발표일 주가 {(R['px_earn']/R['px_pre_earn']-1)*100:+.1f}%",
              [f"4분기에도 관세 약 $600M. 올해 마진을 받친 IEEPA 관세 환급 {b(Y9['ieepa_recovery'])}은 4분기 가이던스에 없다",
               "4분기 건설장비는 딜러 재고 약 $1.6B 감소로 매출이 전년과 비슷할 전망 — 성장의 중심이 발전 부문으로 좁아진다"])
rp.thesis_box("③", f"현재가는 2027E EPS의 {R['per27_now']:.1f}배 — 피어 중앙값 {R['fpe_med']:.1f}배",
              [f"디어·커민스·파카·코마츠·볼보·AGCO·유나이티드렌탈스·이튼의 선행 PER 중앙값 {R['fpe_med']:.1f}배(11-09)",
               f"DCF(WACC {pc(R['wacc'])})로 현재가를 맞추려면 2036년 영업이익률이 {pc(R['implied_m'],0)}가 되어야 한다(최근 3년 17~20%)"])
rp.para(f"▶ 결론: 목표주가 {usd(TP)}(A. DCF {usd(B['va'])} × 50% + B. 2027E EPS ${FB[1]['eps']:.2f} × {B['mult']:.1f}배 {usd(B['vb'])} × 50%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(08-24, {O['rating']} {usd(O['tp'])}) 뒤 주가는 10-06 {usd(R['hi_since'])} 고점에서 {usd(PRICE)}까지 내렸지만, 자체 이익 추정과 피어 배수로 계산하면 아직 높다. "
        f"낙관 시나리오도 {usd(H['tp'])}로 현재가 아래다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.para("캐터필러는 세계 최대 건설·광산 장비 회사다. 2026년부터 사업부문 이름을 Power & Energy(옛 Energy & Transportation: 발전용 엔진·가스터빈(Solar Turbines)·가스 압축·철도), "
        "Construction Industries(굴착기·로더 등 건설장비), Resource Industries(광산 트럭·채굴 장비)로 쓰고, 장비 금융은 Financial Products(Cat Financial)가 맡는다. "
        "매출의 약 58%가 북미이고, 장비는 독립 딜러망을 통해 판다.")
rp.table([["부문 (3Q26)", "매출", "증가율", "부문이익", "특징"],
          ["Power & Energy", b(SG["Power & Energy"]["sales"]), pc(SG["Power & Energy"]["growth"], 0), b(SG["Power & Energy"]["profit"]), "데이터센터 발전·가스 압축, 이익 +31%, 증설 진행"],
          ["Construction Industries", b(SG["Construction Industries"]["sales"]), pc(SG["Construction Industries"]["growth"], 0), b(SG["Construction Industries"]["profit"]), "북미 +23%, 관세 비용의 약 50%가 이 부문"],
          ["Resource Industries", b(SG["Resource Industries"]["sales"]), pc(SG["Resource Industries"]["growth"], 0), b(SG["Resource Industries"]["profit"]), "구리·금 수요, 오일샌드, 그룹 사장 교체(11-01)"],
          ["Financial Products", b(SG["Financial Products"]["revenue"]), "+9%", b(SG["Financial Products"]["profit"]), "장비 금융, 부채는 고객 금융자산에 대응"]],
         [22, 12, 10, 12, 44], note="자료: 8-K 3Q26 보도자료(10-29). 부문이익은 본사 비용 배분 전.")
rp.h2("1-1. 원래 리포트 이후 주요 사건")
rp.table([["날짜", "사건", "내용"],
          ["2026-08-27", "8-K (1.01·2.03)", "중요 계약 체결·채무 발생 공시(첨부 계약서 12건)"],
          ["2026-10-06", "주가 고점", f"종가 {usd(R['hi_since'])}"],
          ["2026-10-07~20", "주가 −16%", "데이터센터 투자 지속성 우려가 이어지며 $863 → $725 (S&P500은 −1%)"],
          ["2026-10-15", "8-K (5.02)", "Resource Industries 그룹 사장 Denise Johnson 은퇴, Derrick York(전 Solar Turbines 사장) 11-01 선임"],
          ["2026-10-22", "AI 투자 우려", "전력 장비주 동반 하락(GE버노바 −10.6%), 캐터필러 −4.9%"],
          ["2026-10-29", "3Q26 실적", f"매출 $20.7B(+17%), 조정 EPS $7.20. 관세 비용 우려로 하루 {(R['px_earn']/R['px_pre_earn']-1)*100:+.1f}%"],
          ["2026-10-31", "딜러 인수", "John Fabick Tractor 인수 완료(현금 $1.24B + 유보 $0.165B)"],
          ["2026-11-05", "시장 급락", "S&P500 −4.4%, 캐터필러 −6.4%($591 → $554)"],
          ["2026-11-09", "반등", f"시장 반등(S&P500 +2.4%)과 함께 +7.2%, {usd(PRICE)}"]],
         [14, 20, 66], note="자료: SEC 8-K·10-Q, yfinance 종가, 언론 보도(Benzinga·TipRanks 10-29~30).")
rp.h2("1-2. 재무 상태 (2026-09-30)")
rp.table([["항목", "금액", "의미"], ["현금", b(BB["cash"]), "연초 $10.0B → 자사주·인수에 사용"],
          ["MP&E 차입", b(R["mpe_debt"]), "제조 부문 차입. 순차입은 Fabick 인수 반영 후 " + b(R["net_debt"])],
          ["Cat Financial 차입", b(BB["fp_debt_lt"] + BB["fp_debt_current"] + BB["fp_st_borrowings"]), "고객 할부·리스 자산의 재원 — 가치평가에서 순차입에 넣지 않음"],
          ["고객 선수금", b(BB["customer_advances"]), f"연초 {b(BB['customer_advances_2025'])}에서 증가(발전 장비 선금)"],
          ["자기자본", b(BB["equity"]), "9개월 자사주 $7.7B"], ["발행주식", f"{R['sh_out']:.1f}백만주", "9월말"]], [24, 16, 60])

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("3Q26 매출", b(P3["revenue"]), "+17% (물량 $2.2B, 가격 $0.7B)"), ("3Q26 영업이익률", pc(P3["op_margin"]), "전년 17.3%"),
              ("3Q26 조정 EPS", f"${P3['adj_eps']:.2f}", f"전년 ${P3['adj_eps_3q25']:.2f}"), ("9M MP&E FCF", b(Y9["mpe_fcf"]), f"전년 {b(Y9['mpe_fcf_9m25'])}")])
rp.img(HERE / "full_q.png", W)
rp.table([["2026 회사 전망 (10-Q, 11-04)", "내용"],
          ["매출 성장", "10%대 중후반 (유지) — 9개월 +21%, 4분기 'moderate' 성장"],
          ["관세 비용", "연 약 $2.2B(IEEPA 환급 제외), 4분기 약 $600M. 환급은 9개월 $520M, 4분기 전망에 미포함"],
          ["설비투자 / 구조조정", "약 $3.3B / 약 $300M"], ["실효세율", "23.0%(일회성 제외)"],
          ["4분기 부문별", "발전: 증설로 성장 / 건설: 딜러 재고 $1.6B 감소로 전년 수준 / 광산: 강한 성장"]], [34, 66], note="자료: 10-Q 3Q26 'Trends and Economic Conditions'.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 수요는 강하다 — 수주잔고 $78B")
rp.para(f"9월말 수주잔고 {b(R['backlog'])}는 한 분기에 $6.0B 늘었고, 이 중 {b(R['bl_12m'])}가 12개월 안에 매출이 된다(2026E 매출의 {R['bl_12m']/R['rev26']:.0%}). "
        "가장 많이 늘어난 부문은 Power & Energy다. 회사는 데이터센터용 발전기와 가스터빈, 가스 압축용 엔진 수요가 계속 늘고 있다고 밝혔다. "
        "따라서 2027년 매출이 줄어들 가능성은 낮다고 보고 기본 시나리오에서 +7%를 가정했다.")
rp.h2("Thesis 2. 그러나 마진은 정점 근처다")
rp.para(f"9개월 영업이익률 {pc(Y9['op_income']/Y9['revenue'])}에는 일회성 관세 환급 $520M(매출의 0.9%)이 들어 있다. 환급을 빼면 {pc((Y9['op_income']-Y9['ieepa_recovery'])/Y9['revenue'])}다. "
        "4분기에는 건설장비 물량 감소, 제조원가 상승, 관세 $600M가 겹친다(회사 전망). 캐터필러의 영업이익률은 2023~2024년 20% 안팎이 최고였고, "
        f"2025년에는 관세로 {pc(A_['op_income']['2025']/A_['revenue']['2025'])}까지 내려갔다. 이 리포트는 2027~2028년 19.5%, 장기 18.5%를 기본으로 잡았다.")
rp.h2("Thesis 3. 피어와 비교한 가격")
pe = R["peers"]
rp.table([["회사", "선행 PER", "EV/EBITDA", "매출 성장"]] +
         [[pe[t]["shortName"].strip()[:28], f"{pe[t]['forwardPE']:.1f}" if pe[t].get("forwardPE") else "-",
           f"{pe[t]['enterpriseToEbitda']:.1f}" if pe[t].get("enterpriseToEbitda") else "-", pc(pe[t]["revenueGrowth"]) if pe[t].get("revenueGrowth") is not None else "-"] for t in pe] +
         [["중앙값", f"{R['fpe_med']:.1f}", f"{R['eveb_med']:.1f}", ""], ["캐터필러 (현재가, 2027E 기본)", f"{R['per27_now']:.1f}", f"{R["ev"]/(FB[1]["op"]+FB[1]["rev"]*R["da"]):.1f}", "+17% (3Q)"]],
         [40, 20, 20, 20], hl_rows=(len(pe) + 2,), note="자료: yfinance(2026-11-10 조회 = 11-09 종가 기준). 선행 PER은 yfinance 추정 EPS 기준, EV/EBITDA는 최근 4분기. 캐터필러 줄은 이 리포트 추정(EV/EBITDA는 2027E).")
rp.para(f"캐터필러는 지난 1년 동안 데이터센터 수혜주로 묶이며 기계 업종보다 높은 배수를 받았다. 최근 5년 캐터필러의 선행 PER 중앙값은 약 16배였다(Zacks 인용). "
        f"지금도 2027E 기준 {R['per27_now']:.0f}배로 그 위에 있다. 발전 부문 비중(3Q 매출의 {SG['Power & Energy']['sales']/P3['revenue']:.0%})이 커진 점은 낙관 시나리오(피어 상위 25% {H['mult']:.1f}배)로 반영했다.")
rp.h2("Thesis 4. 주주환원은 그대로")
rp.para(f"9개월 동안 자사주 {b(Y9['buyback'])}, 배당 {b(Y9['dividends'])}를 썼다. 회사는 'MP&E 잉여현금흐름을 사실상 전부 주주에게 돌려준다'는 원칙과 A 등급 유지를 다시 밝혔고, "
        "10월 분기배당 $1.63을 유지했다. 이 리포트는 자사주로 희석주식 수가 연 1.5% 줄어든다고 가정했다(2025년 평균 472백만주 → 3Q26 461백만주).")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.img(HERE / "full_earn.png", W)
pick = [FB[0], FB[1], FB[2], FB[4], FB[-1]]
rp.table([["항목 (기본, $M)", "2026E", "2027E", "2028E", "2030E", "2036E"],
          ["매출"] + [f0(r["rev"]) for r in pick],
          ["매출 성장률", pc(FB[0]["rev"] / A_["revenue"]["2025"] - 1), pc(SA["기본"]["g27"], 0), pc(SA["기본"]["g28"], 0), pc(B["g_late"][1]), pc(B["g_late"][-1])],
          ["영업이익"] + [f0(r["op"]) for r in pick], ["영업이익률"] + [pc(r["op"] / r["rev"]) for r in pick],
          ["FCFF", "-"] + [f0(r["fcff"]) for r in pick[1:]], ["희석 EPS ($)"] + [f"{r['eps']:.2f}" for r in pick]],
         [24, 15, 15, 15, 15, 16], hl_rows=(3,))
rp.para(f"FCFF = 영업이익 × (1 − 23%) + 감가상각(매출 2.1%) − 설비투자(2027 4.0%, 2028 3.7%, 이후 3.5%) − 매출 증가분의 12%(운전자본). "
        f"2026E EPS ${FB[0]['eps']:.2f}에는 관세 환급이 들어 있어 2027E EPS ${FB[1]['eps']:.2f} 증가율이 낮아 보인다. 환급을 빼면 2026E EPS는 약 ${FB[0]['eps'] - 520*(1-R['tax'])/R['sh_dil']:.2f}다.")
rp.table([["가정", "보수", "기본", "낙관"],
          ["2027 / 2028 매출 성장", *[f"{pc(SA[k]['g27'],0)} / {pc(SA[k]['g28'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2027 / 2028 영업이익률", *[f"{pc(SA[k]['m27'])} / {pc(SA[k]['m28'])}" for k in ("보수", "기본", "낙관")]],
          ["장기 영업이익률 (2036)", *[pc(SA[k]["m_lt"]) for k in ("보수", "기본", "낙관")]],
          ["2029년 성장률 (2036년 3%로 수렴)", *[pc(SA[k]["g_late0"], 0) for k in ("보수", "기본", "낙관")]],
          ["피어 선행 PER", *[f"{S[k]['mult']:.1f}배" for k in ("보수", "기본", "낙관")]]], [30, 23, 23, 24],
         note="보수 = 건설·광산 경기 둔화(2028년 매출 정체), 낙관 = 발전 증설이 계획대로 매출로 이어지는 경우. 피어 배수: 보수 하위 25%, 기본 중앙값, 낙관 상위 25%.")

rp.h1("5. 밸류에이션 (Valuation)")
rp.table([["항목", "값", "근거"], ["미국채 10년", pc(R["ust"], 2), "2026-11-09 (yfinance ^TNX)"],
          ["베타", f"{R['beta']['blume']:.2f}", f"S&P500(SPY) 대비 2년 주간 원베타 {R['beta']['raw']:.2f}, Blume 조정"],
          ["주식위험프리미엄", "5.0%", "미국 종목 공통"], ["자기자본비용", pc(R["coe"], 2), ""],
          ["세후 타인자본비용 / 부채 비중", f"{pc(R['kd'],2)} / {pc(R['wd'])}", "MP&E 차입만(금융 부문 제외)"], ["WACC", pc(R["wacc"], 2), ""], ["영구성장률", "3.0%", ""]], [26, 18, 56])
rp.h2("5-1. A. DCF")
rp.para(f"4Q26~2036 FCFF 현재가치 {b(B['pv'])} + 영구가치 {b(B['tv'])} − MP&E 순차입 {b(R['net_debt'])} ÷ 희석주식 {R['sh_dil']:.0f}백만주 = **{usd(B['va'])}**. "
        "Cat Financial은 이익(세후)을 FCFF에 넣고, 그 차입은 고객 금융자산에 대응하므로 순차입에서 뺐다.")
rp.h2("5-2. B. 2027E EPS × 피어 선행 PER")
rp.para(f"2027E EPS ${FB[1]['eps']:.2f} × 피어 중앙값 {B['mult']:.1f}배 = **{usd(B['vb'])}**.")
sb = R["sens_b"]
rp.table([["2027 매출 성장 \\ PER"] + [f"{p:.1f}배" for p in sb["per"]]] + [[pc(g, 0)] + [usd(x) for x in row] for g, row in zip(sb["g"], sb["v"])],
         [25, 18, 19, 19, 19], note="B 값($). 22배는 현재가 수준 배수 참고용.")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. DCF", "50%", usd(L["va"]), usd(B["va"]), usd(H["va"])],
          ["B. PER", "50%", f"{usd(L['vb'])} ({L['mult']:.1f}배)", f"{usd(B['vb'])} ({B['mult']:.1f}배)", f"{usd(H['vb'])} ({H['mult']:.1f}배)"],
          ["목표주가", "", usd(L["tp"]), f"{usd(B['tp'])} → {usd(TP)}", usd(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [22, 10, 22, 24, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL. 경기 순환 업종이라 현금흐름(DCF)과 업종 배수(PER)를 같은 비중으로 둔다.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-4. 민감도 — 장기 영업이익률 × WACC (목표주가)")
sn = R["sens"]
rp.table([["장기 마진 \\ WACC"] + [pc(w) for w in sn["wacc"]]] + [[pc(m) ] + [usd(x) for x in row] for m, row in zip(sn["m"], sn["v"])],
         [25, 18, 19, 19, 19], note="B는 기본값 고정. WACC를 2%p 낮추고 장기 마진을 20.5%로 올려도 현재가에 못 미친다.")
rp.h2("5-5. 교차확인 — 애널리스트 목표가 (3Q26 실적 이후)")
rp.table([["기관", "날짜", "의견", "목표가 (이전)"]] + [[a, d, c, f"{usd(t)}" + (f" ({usd(p)})" if p else "")] for a, d, c, t, p in R["analysts"]],
         [30, 20, 20, 30], note="자료: TipRanks·Benzinga·MarketBeat 기사(10-29~30). 모두 인하 방향, 범위 $675~1,027. 목표가 계산에 넣지 않았다.")

rp.h1("6. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "발전 부문 재평가", "Power & Energy가 GE버노바처럼 전력 장비 배수(20배 이상)를 받으면", f"낙관 {usd(H['tp'])} 이상"],
          ["상방", "관세 환급·완화", "추가 IEEPA 환급이나 관세 인하로 연 $2.2B 비용이 줄면", "마진 +1~3%p"],
          ["하방", "AI 투자 속도 조절", "데이터센터 투자 축소 시 발전 부문 수주 둔화(10월 주가 하락 원인)", f"보수 {usd(L['tp'])}"],
          ["하방", "건설 경기", "딜러 재고 조정·렌탈 투자 둔화, 4분기 건설 매출 정체", "물량"],
          ["하방", "원가", "회사가 4분기 제조원가 상승을 전망", "마진"]], [8, 20, 48, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {usd(TP)} (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {usd(TP)} · 보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"],
          ["확인할 일정", "① 4Q26 실적·2027 전망(1월 말) ② 관세 정책·IEEPA 환급 ③ 발전 증설 진행과 Power & Energy 수주"],
          ["결론", f"수주잔고와 매출은 좋지만, 관세 비용이 이어지고 마진은 정점 근처다. 현재가는 2027E EPS의 {R['per27_now']:.0f}배로 피어보다 약 {R['per27_now']/R['fpe_med']-1:.0%} 비싸다. "
                   f"주가가 고점에서 {R['price']/R['hi_since']-1:.0%} 내렸지만 가격 기준으로 {RATING}."]], [20, 80])
rp.since("8", "2026-08-24",
         [["항목", "원래 리포트 (2026-08-24)", "재조사 (2026-11-09)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {usd(O['tp'])}", f"{RATING} / {usd(TP)} (기준주가 {usd(PRICE)})"],
          ["주가", f"{usd(R['px_orig'])} (08-21 종가)", f"{usd(PRICE)} ({R['chg_since']*100:+.1f}%, 10-06 고점 {usd(R['hi_since'])})"],
          ["실적", "2Q26까지", "3Q26 매출 $20.7B(+17%), 조정 EPS $7.20, 수주잔고 $78.1B"],
          ["2026 전망", "매출 10%대 중후반 성장", "같음(유지). 관세 비용 연 $2.2B, 4분기 $600M 명시"],
          ["평가 방법", O["method"], "A. DCF(MP&E FCFF) 50 + B. 2027E EPS × 피어 선행 PER 50"],
          ["대안 시나리오", "-", f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]],
         ["3Q26(10-29): 매출과 EPS는 예상을 넘었지만 관세 비용 전망으로 주가가 하루 −9% 내렸다. 수주잔고는 $72.1B → $78.1B.",
          "주가: 10-06 $863(최고) → 데이터센터 투자 우려로 10월 중순 $725 → 실적 발표 뒤 $647 → 11-05 시장 급락일 $554 → 11-09 $599.",
          "애널리스트 목표가는 실적 뒤 대부분 인하($675~1,027).", "Fabick 딜러 인수 완료(10-31), Resource Industries 사장 교체(11-01). 미국채 10년 4.86%(11-09)."],
         ["목표가를 자체 추정(DCF)과 피어 배수로만 계산했다. 애널리스트 목표가는 교차확인 표로만 둔다.",
          "일회성 IEEPA 관세 환급을 2027년 이후 마진에서 빼고, 관세 비용이 이어진다고 가정했다.",
          "피어 선행 PER(11-09, 8개사)로 시장이 기계·장비 업종에 주는 배수를 확인했다."],
         f"{usd(O['tp'])} → {usd(TP)}. 실적은 원래 기대만큼 좋았지만, 자체 이익 추정과 피어 배수로 다시 계산하면 현재가도 높다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K 실적 보도자료), yfinance(시세·미국채·피어 배수), 언론에 보도된 애널리스트 의견(TipRanks, Benzinga, MarketBeat)을 바탕으로 작성한 개인 분석 자료입니다. "
              "애널리스트 목표가는 교차확인에만 썼습니다.")
out = HERE / "캐터필러_리서치리포트_20261109.docx"
rp.doc.save(out); print(out); to_pdf(out)
