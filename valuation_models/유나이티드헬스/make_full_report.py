"""유나이티드헬스_리서치리포트_20261109.docx/.pdf — 2026-10-15 리포트를 2026-11-09 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_yf.csv. 실행: python valuation/유나이티드헬스/make_full_report.py
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
A_, Qk, Q3, Y9, GD, RK = K["annual"], K["quarterly"], K["q3_26"], K["ytd_9m26"], K["guidance_2026"], K["risks"]
MB = Q3["members_k"]
b = lambda x: f"${x/1e3:,.1f}B"
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
usd = lambda x: f"${x:,.0f}"
u2 = lambda x: f"${x:,.2f}"

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / "full_price.png", "최근 2년 종가($), 기준일 2026-11-09", unit="$", alt=[(L["tp"], "보수"), (H["tp"], "낙관")])
ql = ["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"]
bar_chart(ql, [("매출($B)", [Qk["revenue"][q] / 1e3 for q in ql], "#1F3864")], HERE / "full_q.png",
          "분기 매출($B)과 영업이익률(GAAP)", line=("영업이익률", [Qk["op_income"][q] / Qk["revenue"][q] for q in ql]), ylab="$B")
yrs = ["2023A", "2024A", "2025A", "2026E", "2027E", "2028E", "2029E"]
eps = [A_["eps_diluted"][y] for y in ("2023", "2024", "2025")] + [r["eps"] for r in FB[:4]]
bar_chart(yrs, [("EPS($)", eps, "#1F3864")], HERE / "full_earn.png", "주당순이익($, 2023~25 GAAP · 2026E~ 조정) — 음영은 추정(기본)", est_from=3,
          line=("EPS 증가율", [0.0] + [eps[i] / eps[i - 1] - 1 for i in range(1, len(eps))]))
football_chart([("A. DCF(FCFE, 자기자본비용 %.1f%%)" % (R["coe"] * 100), L["va"], B["va"], H["va"]), ("B. 2027E EPS × 피어 선행 PER", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 50 : B 50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$")

SUB = "가이던스 세 번 상향, 의료비율 개선 — 그러나 회복은 이미 주가에, 별점·조사는 아직 가격 밖에"
MKT = [["현재주가 (2026.11.09 종가)", u2(PRICE)], ["시가총액", b(R["mcap"])], ["총차입 (9월말)", b(R["debt"])],
       ["52주 최고 / 최저 (장중)", f"{u2(R['hi52'])} / {u2(R['lo52'])}"], ["PER (2026E 조정, 가이던스 하한)", f"{R['per26_now']:.1f}배"],
       ["PER (2027E 기본)", f"{R['per27_now']:.1f}배"], ["관리의료 피어 선행 PER 중앙값", f"{R['fpe_med']:.1f}배"],
       ["3Q26 의료비율", pc(Q3["mcr"])], ["배당수익률 ($2.32 × 4)", pc(R["div_yield"])], ["원래 리포트 (2026.10.15)", f"{O['rating']} · {usd(O['tp'])}"]]
ALT = [f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]

rp = Rep("헬스케어 보험 (메디케어·Optum)", "2026년 11월 9일")
rp.cover("유나이티드헬스 (UnitedHealth Group, NYSE: UNH)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, $M)")
rows = [["항목", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출"] + [f0(A_["revenue"][y]) for y in ("2023", "2024", "2025")] + ["-", "-", "-"],
        ["영업이익"] + [f0(A_["op_income"][y]) for y in ("2023", "2024", "2025")] + ["-", "-", "-"],
        ["순이익 (GAAP / 조정 추정)"] + [f0(A_["net_income"][y]) for y in ("2023", "2024", "2025")] + [f0(r["ni"]) for r in FB[:3]],
        ["희석 EPS ($)"] + [f"{A_['eps_diluted'][y]:.2f}" for y in ("2023", "2024", "2025")] + [f"{r['eps']:.2f}" for r in FB[:3]],
        ["EPS 증가율"] + ["-", pc(A_["eps_diluted"]["2024"] / A_["eps_diluted"]["2023"] - 1), pc(A_["eps_diluted"]["2025"] / A_["eps_diluted"]["2024"] - 1)] + [pc(r["g"]) for r in FB[:3]],
        ["영업현금흐름"] + [f0(A_["cfo"][y]) for y in ("2023", "2024", "2025")] + ["-", "-", "-"]]
rp.table(rows, [26, 12, 12, 12, 12, 13, 13], hl_cols=(4, 5, 6),
         note="자료: SEC 10-K·10-Q·8-K. 2026E = 회사 조정 EPS 가이던스 하한 $20.50(10-13, '이상'). 2026E 이후는 조정 EPS 기준이라 2025년 GAAP EPS와 증가율 비교에 주의. 매출은 가입자 구조조정 중이라 추정하지 않았다.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", f"회복은 숫자로 확인 — 9M 의료비율 {pc(Q3['mcr_9m'])}(전년 {pc(Q3['mcr_9m25'])}), 9M EPS ${Y9['eps']:.2f}(전년 ${Y9['eps_9m25']:.2f})",
              ["2026 조정 EPS 가이던스: 1월 $17.75 이상 → 1Q 후 $18.25 이상 → 7월 $19.50~20.00 → 10월 $20.50 이상",
               "Optum Health 가치기반진료 시장 정리, 가입자를 줄이며 가격을 올리는 구조조정이 이익률을 끌어올렸다"])
rp.thesis_box("②", "그러나 2027~2028년 성장에는 걸림돌이 있다",
              [f"2027 메디케어 어드밴티지 별점: {RK['stars_2027']}",
               f"상업보험 의료비 추세 높음(회사 언급), {RK['texas_ag']}, DOJ 조사 계속"])
rp.thesis_box("③", f"현재가는 2027E EPS의 {R['per27_now']:.1f}배 — 관리의료 피어 중앙값 {R['fpe_med']:.1f}배",
              [f"엘레번스·시그나·CVS·휴매나·센틴·몰리나의 선행 PER {min(R['fpe'].values()):.1f}~{max(R['fpe'].values()):.1f}배(11-09)",
               f"DCF(자기자본비용 {pc(R['coe'])})는 현재가보다 높지만, 현재가가 내포한 자기자본비용은 {pc(R['implied_g'])}(베타 약 {(R['implied_g']-R['ust'])/0.05:.1f} 수준) — 시장은 규제 위험을 더 높게 본다"])
rp.para(f"▶ 결론: 목표주가 {usd(TP)}(A. DCF {usd(B['va'])} × 50% + B. 2027E 조정 EPS ${FB[1]['eps']:.2f} × {B['mult']:.1f}배 {usd(B['vb'])} × 50%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(10-15, {O['rating']} {usd(O['tp'])}) 뒤 주가는 10-22 {u2(R['hi_since'])}까지 올랐다가 {u2(PRICE)}로 돌아왔다. 3분기 회복은 원래 리포트에 이미 반영된 사실이고, "
        "그 뒤 새로 확인된 것은 별점 하락·조사의 지속이다. 자체 이익 추정과 피어 배수로 다시 계산하면 상승여력이 BUY 기준(15%)에 못 미친다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.para("유나이티드헬스는 미국 최대 건강보험·의료서비스 회사다. UnitedHealthcare(상업보험·메디케어 어드밴티지·메디케이드)와 Optum(Optum Health 진료·가치기반진료, Optum Insight 데이터·IT, Optum Rx 약국급여관리)으로 나뉜다. "
        "2025년 CEO 교체·실적 전망 철회·DOJ 조사로 주가가 크게 내렸고, 2026년은 가격 인상과 가입자 축소로 마진을 되찾는 해다.")
rp.table([["UnitedHealthcare 가입자 (천 명)", "2026-09-30", "2025-09-30", "증감"],
          ["상업보험 위험인수형", f0(MB["commercial_risk"][0]), f0(MB["commercial_risk"][1]), pc(MB["commercial_risk"][0] / MB["commercial_risk"][1] - 1)],
          ["상업보험 수수료형(ASO)", f0(MB["commercial_fee"][0]), f0(MB["commercial_fee"][1]), pc(MB["commercial_fee"][0] / MB["commercial_fee"][1] - 1)],
          ["메디케어 어드밴티지", f0(MB["medicare_advantage"][0]), f0(MB["medicare_advantage"][1]), pc(MB["medicare_advantage"][0] / MB["medicare_advantage"][1] - 1)],
          ["메디케이드", f0(MB["medicaid"][0]), f0(MB["medicaid"][1]), pc(MB["medicaid"][0] / MB["medicaid"][1] - 1)]],
         [34, 22, 22, 22], note="자료: 10-Q 3Q26. 위험을 지는 가입자는 10% 줄이고, 수수료만 받는 가입자는 늘렸다 — 이익의 질을 높이는 방향.")
rp.h2("1-1. 원래 리포트 이후 주요 사건")
rp.table([["날짜", "사건", "내용"],
          ["2026-10-14", "원래 리포트 기준", f"종가 {u2(R['px_orig'])}(10-14 하루 +4.7%)"],
          ["2026-10-22", "주가 고점", f"종가 {u2(R['hi_since'])}"],
          ["2026-11-03", "10-Q 3Q26", "가입자·의료비 추세·조사 현황 공시. 2027 보험 설계에 높은 의료비 추세 반영"],
          ["2026-11-03", "이사 선임", "Madeline Bell 독립이사(8-K 11-09)"],
          ["2026-11-09", "기준일", f"종가 {u2(PRICE)}, 관리의료 피어는 같은 기간(10-13 이후) −3%~+5%"]],
         [15, 20, 65], note="자료: SEC 8-K·10-Q, yfinance 종가.")

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("3Q26 매출", b(Qk["revenue"]["3Q26"]), "−0.4%"), ("3Q26 조정 EPS", f"${Qk['adj_eps']['3Q26']:.2f}", f"전년 ${Qk['adj_eps']['3Q25']:.2f}"),
              ("3Q26 의료비율", pc(Q3["mcr"]), f"전년 {pc(Q3['mcr_3q25'])}"), ("3Q26 영업현금", b(Q3["cfo"]), "순이익의 1.2배")])
rp.img(HERE / "full_q.png", W)
rp.para(f"3분기 영업이익률은 {pc(Q3['op_margin'])}(전년 3.8%)로 올랐다. 다만 원래 리포트에서 짚었듯 의료비율 개선의 일부(약 $610M, 0.7%p)는 과거 기간 준비금 환입이다. "
        f"9개월 GAAP EPS ${Y9['eps']:.2f}에 가이던스(GAAP $19.50 이상)를 더하면 4분기 GAAP EPS는 약 ${19.50 - Y9['eps']:.2f} 이상이다 — 4분기는 계절적으로 의료비가 가장 많은 분기다.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 2026년은 '회복', 2027년부터는 '성장'을 증명해야")
rp.para("회사는 2027년부터 조정 EPS 연 13~16% 성장으로 돌아간다고 밝혔다(3분기 컨퍼런스콜). 이 리포트는 기본 시나리오에서 2027년 +12%, 2028년 +9%로 하한보다 낮게 잡았다. "
        "근거는 ① 2027 별점 하락이 2028년 품질 보너스 매출을 줄이고, ② 상업보험 의료비 추세가 높으며, ③ 메디케이드는 2026년이 바닥이라는 회사 설명뿐 회복 속도가 확인되지 않았기 때문이다.")
rp.h2("Thesis 2. 가입자를 줄여 마진을 산다")
rp.para(f"위험인수형 상업보험(−10%)·메디케어 어드밴티지(−10%)·메디케이드(−10%) 가입자를 함께 줄이고 수수료형(+3%)을 늘렸다. UnitedHealthcare 3분기 매출은 ${Q3['uhc_revenue'][0]/1e3:.1f}B로 전년보다 1% 줄었지만 이익은 늘었다. "
        "이런 구조조정은 마진 회복에는 좋지만, 매출 성장률을 낮춰 2027년 이후 EPS 성장의 상단을 제한한다.")
rp.h2("Thesis 3. 피어와 비교한 가격")
pe = R["peers"]
rp.table([["회사", "선행 PER", "EV/EBITDA", "매출 성장"]] +
         [[pe[t]["shortName"].strip()[:30], f"{pe[t]['forwardPE']:.1f}", f"{pe[t]['enterpriseToEbitda']:.1f}", pc(pe[t]["revenueGrowth"])] for t in pe] +
         [["중앙값", f"{R['fpe_med']:.1f}", "", ""], ["유나이티드헬스 (현재가, 2027E 기본)", f"{R['per27_now']:.1f}", "-", "−0.4% (3Q)"]],
         [40, 20, 20, 20], hl_rows=(len(pe) + 2,), note="자료: yfinance(2026-11-10 조회 = 11-09 종가 기준). 휴매나·몰리나는 이익이 눌려 있어 PER이 높다. 유나이티드헬스 줄은 이 리포트 추정.")
rp.para(f"유나이티드헬스는 Optum(데이터·약국·진료)을 가진 수직계열 회사라 순수 보험사보다 높은 배수를 받아 왔다. 낙관 시나리오는 이 프리미엄을 피어 상위 25%({R['mult']['1']:.1f}배)로 반영했다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.img(HERE / "full_earn.png", W)
pick = [FB[0], FB[1], FB[2], FB[3], FB[4], FB[-1]]
rp.table([["항목 (기본)", "2026E", "2027E", "2028E", "2029E", "2030E", "2036E"],
          ["조정 EPS ($)"] + [f"{r['eps']:.2f}" for r in pick], ["EPS 증가율", "+55%"] + [pc(r["g"]) for r in pick[1:]],
          ["조정 순이익 ($M)"] + [f0(r["ni"]) for r in pick], ["FCFE ($M, 순이익 × 90%)", "-"] + [f0(r["fcfe"]) for r in pick[1:]]],
         [26, 12, 12, 12, 12, 12, 14], hl_rows=(1,))
rp.table([["가정", "보수", "기본", "낙관"],
          ["2027 / 2028 EPS 증가율", *[f"{pc(SA[k]['g27'],0)} / {pc(SA[k]['g28'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2029년 증가율 (2036년 3%로 수렴)", *[pc(SA[k]["g_late0"], 0) for k in ("보수", "기본", "낙관")]],
          ["2027E 조정 EPS", *[f"${S[k]['rows'][1]['eps']:.2f}" for k in ("보수", "기본", "낙관")]],
          ["피어 선행 PER", *[f"{S[k]['mult']:.1f}배" for k in ("보수", "기본", "낙관")]]], [30, 23, 23, 24],
         note="낙관 = 회사 목표(13~16%) 그대로. 보수 = 별점·조사 영향으로 2028년 성장 4%. 피어 배수: 보수 하위 25%, 기본 중앙값, 낙관 상위 25%.")

rp.h1("5. 밸류에이션 (Valuation)")
rp.table([["항목", "값", "근거"], ["미국채 10년", pc(R["ust"], 2), "2026-11-09 (yfinance ^TNX)"],
          ["베타", f"{R['beta']['blume']:.2f}", f"S&P500(SPY) 대비 2년 주간 원베타 {R['beta']['raw']:.2f}, Blume 조정(5년도 0.55로 같음)"],
          ["주식위험프리미엄", "5.0%", "미국 종목 공통"], ["자기자본비용", pc(R["coe"], 2), "보험사라 부채를 영업의 일부로 보고 주주 기준으로 할인"],
          ["FCFE / 순이익", "90%", "영업현금은 순이익의 약 1.2배지만 법정자본·인수 재투자를 뺌"], ["영구성장률", "3.0%", "미국 공통"]], [24, 14, 62])
rp.h2("5-1. A. DCF (FCFE)")
rp.para(f"4Q26~2036 FCFE 현재가치 {b(B['pv'])} + 영구가치 {b(B['tv'])} ÷ 희석주식 {R['sh_dil']:.0f}백만주 = **{usd(B['va'])}**. 현재가 {u2(PRICE)}를 맞추는 자기자본비용은 {pc(R['implied_g'])}다.")
rp.h2("5-2. B. 2027E 조정 EPS × 피어 선행 PER")
sb = R["sens_b"]
rp.para(f"2027E 조정 EPS ${FB[1]['eps']:.2f} × 관리의료 피어 중앙값 {B['mult']:.1f}배 = **{usd(B['vb'])}**.")
rp.table([["2027 EPS 증가율 \\ PER"] + [f"{p:.1f}배" for p in sb["per"]]] + [[pc(g, 0)] + [usd(x) for x in row] for g, row in zip(sb["g"], sb["v"])],
         [28, 18, 18, 18, 18], note="B 값($). 17배는 현재가 수준 배수 참고용.")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. DCF", "50%", usd(L["va"]), usd(B["va"]), usd(H["va"])],
          ["B. PER", "50%", f"{usd(L['vb'])} ({L['mult']:.1f}배)", f"{usd(B['vb'])} ({B['mult']:.1f}배)", f"{usd(H['vb'])} ({H['mult']:.1f}배)"],
          ["목표주가", "", usd(L["tp"]), f"{usd(B['tp'])} → {usd(TP)}", usd(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [22, 10, 22, 24, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-4. 민감도 — 2027 EPS 증가율 × 자기자본비용 (목표주가)")
sn = R["sens"]
rp.table([["2027 증가율 \\ 자기자본비용"] + [pc(c) for c in sn["coe"]]] + [[pc(g, 0)] + [usd(x) for x in row] for g, row in zip(sn["g"], sn["v"])],
         [28, 18, 18, 18, 18], note="A·B 모두 2027 증가율을 바꿔 다시 계산(B 배수는 중앙값 고정).")
rp.h2("5-5. 교차확인 — 애널리스트 목표가")
rp.table([["구분", "내용"], ["3Q 실적 직후 1개월(9/15~10/15) 10건", "평균 $466, 범위 $402(TD Cowen) ~ $529(Morgan Stanley)"],
          ["의견 분포", "Buy 20 · Hold 8 (MarketBeat, 10월 중순)"], ["상향 / 하향", "상향 Piper·Goldman, 하향 TD Cowen·Baird·Barclays"]],
         [36, 64], note="자료: 원래 리포트(2026-10-15)에서 정리한 StockAnalysis·TipRanks·Benzinga·MarketBeat 집계. 목표가 계산에 넣지 않았다.")

rp.h1("6. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "회사 목표 달성", "2027년부터 EPS 13~16% 성장이 그대로 나오면", f"낙관 {usd(H['tp'])}"],
          ["상방", "자사주 확대", "7월 한도 확대 이후 3분기 $1.4B 매입 — 속도가 붙으면", "주당 이익"],
          ["하방", "별점 하락", "2027 별점으로 2028년 품질 보너스 감소", f"보수 {usd(L['tp'])}"],
          ["하방", "조사·소송", "DOJ 형사·민사 조사, 텍사스 AG 조사 — 벌금·영업 제한", "배수 하락"],
          ["하방", "의료비 추세", "상업보험 의료비 추세가 가격 인상보다 빠르면", "의료비율"]], [8, 20, 48, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {usd(TP)} (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {usd(TP)} · 보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"],
          ["확인할 일정", "① 4Q26 실적·2027 가이던스(1월) ② 2028 메디케어 어드밴티지 요율 예고안(2027년 초) ③ DOJ·텍사스 AG 조사 진행"],
          ["결론", f"회복은 진짜지만 현재가 {u2(PRICE)}는 2027E EPS의 {R['per27_now']:.0f}배로 피어보다 높고, 자체 계산 상승여력은 {UP*100:+.1f}%다. 회사 목표(13~16%)가 확인될 때까지 {RATING}."]], [20, 80])
rp.since("8", "2026-10-15",
         [["항목", "원래 리포트 (2026-10-15)", "재조사 (2026-11-09)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {usd(O['tp'])}", f"{RATING} / {usd(TP)} (기준주가 {u2(PRICE)})"],
          ["주가", f"{u2(R['px_orig'])} (10-14 종가)", f"{u2(PRICE)} ({R['chg_since']*100:+.1f}%, 10-22 고점 {u2(R['hi_since'])})"],
          ["실적·가이던스", "3Q26 조정 EPS $4.69, 2026 $20.50 이상", "같음(새 실적 없음). 10-Q로 가입자 감소·의료비 추세 확인"],
          ["평가 방법", O["method"], "A. DCF(FCFE) 50 + B. 2027E 조정 EPS × 관리의료 피어 선행 PER 50"],
          ["대안 시나리오", "-", f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]],
         ["원래 리포트 작성 하루 전(10-13)에 3분기 실적이 나와, 그 뒤 새 실적은 없다. 11-03 10-Q에서 위험인수형 가입자 10% 감소와 높은 의료비 추세, 조사 현황이 확인됐다.",
          "주가는 10-22 $425까지 오른 뒤 원래 리포트 때 수준($398)으로 돌아왔다.", "미국채 10년 4.86%(11-09)."],
         ["목표가를 자체 추정(FCFE DCF)과 관리의료 피어 배수로만 계산했다. 증권사 목표가는 교차확인 표로만 두고, 근거 없는 정성 조정(−2%)은 쓰지 않는다.",
          "2027년 EPS 증가율을 회사 목표 하한(13%)보다 낮은 12%로 두고, 목표를 그대로 쓰는 경우는 낙관 시나리오로 따로 보였다."],
         f"{usd(O['tp'])} → {usd(TP)}. 회사 실적은 그대로지만, 자체 이익 추정과 피어 배수로 다시 계산하면 상승여력이 {UP*100:+.1f}%라 BUY 기준(15%)에 못 미친다. 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K 실적 보도자료), yfinance(시세·미국채·피어 배수), 원래 리포트에서 정리한 증권사 목표가 집계를 바탕으로 작성한 개인 분석 자료입니다. "
              "증권사 목표가는 교차확인에만 썼습니다.")
out = HERE / "유나이티드헬스_리서치리포트_20261109.docx"
rp.doc.save(out); print(out); to_pdf(out)
