"""엑슨모빌_리서치리포트_20261109.docx/.pdf — 2026-09-07 리포트를 2026-11-09 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_yf.csv. 실행: python valuation/엑슨모빌/make_full_report.py
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
A_, Qk, Y9, SEG, SQ, P3, BB = K["annual"], K["quarterly"], K["ytd_9m"], K["segments_adj_9m"], K["segments_adj_q"], K["q3_26_press"], K["balance_20260930"]
b = lambda x: f"${x/1e3:,.1f}B"
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
usd = lambda x: f"${x:,.0f}"
u2 = lambda x: f"${x:,.2f}"

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / "full_price.png", "최근 2년 종가($), 기준일 2026-11-09", unit="$", alt=[(H["tp"], "낙관")])
ql = ["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"]
bar_chart(ql, [("매출($B)", [Qk["revenue"][q] / 1e3 for q in ql], "#1F3864")], HERE / "full_q.png",
          "분기 매출($B)과 순이익률(GAAP)", line=("순이익률", [Qk["net_income"][q] / Qk["revenue"][q] for q in ql]), ylab="$B")
yrs = ["2023A", "2024A", "2025A", "2026E", "2027E", "2028E", "2029E"]
eps = [A_["eps_diluted"][y] for y in ("2023", "2024", "2025")] + [r["eps"] for r in FB[:4]]
bar_chart(yrs, [("EPS($)", eps, "#1F3864")], HERE / "full_earn.png", "주당순이익($, 2023~25 GAAP · 2026E~ 조정) — 음영은 추정(기본)", est_from=3,
          line=("EPS 증가율", [0.0] + [eps[i] / eps[i - 1] - 1 for i in range(1, len(eps))]))
football_chart([("A. DCF (WACC %.1f%%)" % (R["wacc"] * 100), L["va"], B["va"], H["va"]), ("B. 2027E EPS × 피어 선행 PER", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 50 : B 50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$")

SUB = f"정제마진 사상 최고가 만든 이익 — 현재가는 정상 브렌트 ${R['implied_b']:.0f}가 영구히 이어진다고 전제한다"
MKT = [["현재주가 (2026.11.09 종가)", u2(PRICE)], ["시가총액", b(R["mcap"])], ["순차입 (9월말)", b(R["net_debt"])],
       ["52주 최고 / 최저 (장중)", f"{u2(R['hi52'])} / {u2(R['lo52'])}"], ["PER (2026E 조정)", f"{R['per26_now']:.1f}배"],
       ["PER (2027E 기본)", f"{R['per27_now']:.1f}배"], ["피어 선행 PER 중앙값", f"{R['fpe_med']:.1f}배"],
       ["브렌트 (11-09)", f"${R['brent_now']:.1f}"], ["배당수익률 (4Q $1.07 × 4)", pc(R["div_yield"])], ["원래 리포트 (2026.09.07)", f"{O['rating']} · {usd(O['tp'])}"]]
ALT = [f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]

rp = Rep("전통에너지 (석유·가스 메이저)", "2026년 11월 9일")
rp.cover("엑슨모빌 (ExxonMobil, NYSE: XOM)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, $M)")
rows = [["항목", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출"] + [f0(A_["revenue"][y]) for y in ("2023", "2024", "2025")] + ["-", "-", "-"],
        ["순이익 (GAAP / 조정 추정)"] + [f0(A_["net_income"][y]) for y in ("2023", "2024", "2025")] + [f0(r["adj"]) for r in FB[:3]],
        ["희석 EPS ($)"] + [f"{A_['eps_diluted'][y]:.2f}" for y in ("2023", "2024", "2025")] + [f"{r['eps']:.2f}" for r in FB[:3]],
        ["영업현금흐름"] + [f0(A_["cfo"][y]) for y in ("2023", "2024", "2025")] + ["-", "-", "-"],
        ["설비투자"] + [f0(A_["capex"][y]) for y in ("2023", "2024", "2025")] + ["-", f0(FB[1]["capex"]), f0(FB[2]["capex"])],
        ["브렌트 평균 ($/배럴)", "82.2", "79.8", f"{R['brent_25']:.1f}", f"{FB[0]['brent']:.1f}", f"{FB[1]['brent']:.0f}", f"{FB[2]['brent']:.1f}"]]
rp.table(rows, [26, 12, 12, 12, 12, 13, 13], hl_cols=(4, 5, 6),
         note="자료: SEC 10-K·10-Q·8-K, yfinance(브렌트 선물 근월물). 2026E = 9개월 조정이익 + 4분기 추정. 2026E 이후는 일회성 항목을 뺀 조정이익 기준. "
              "매출은 유가·제품가격을 그대로 따라가 추정하지 않았다.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", f"이익은 역대급 — 9M26 조정이익 {b(Y9['2026']['adj_earnings'])}(전년 {b(Y9['2025']['adj_earnings'])}), 3Q 조정 EPS ${Qk['adj_eps']['3Q26']:.2f}",
              [f"Energy Products(정유) 9개월 이익 {b(SEG['2026']['Energy Products'])}, 전년의 {SEG['2026']['Energy Products']/SEG['2025']['Energy Products']:.1f}배",
               f"3Q FCF {b(P3['fcf'])}, 주주환원 {b(P3['distributions'])}, 2027년 자사주 $20B 발표, 배당 44년 연속 인상"])
rp.thesis_box("②", "그 이익의 원인은 중동 정제설비 손실 — 오래가지 않는다",
              ["회사 10-Q: 호르무즈 공급 제한에도 정제설비 손실로 원유 수요가 줄어 유가는 10년 범위 안, 정제마진만 10년 범위를 넘은 역사적 고점",
               f"정유 정상 이익을 연 {b(R['ep_norm'])}로 두면 정상 조정이익은 약 {b(R['norm']['total'])}(브렌트 $75) — 2026E {b(R['adj26'])}의 {R['norm']['total']/R['adj26']:.0%}"])
rp.thesis_box("③", f"현재가는 정상 브렌트 ${R['implied_b']:.0f}를 전제 — 2025년 평균 ${R['brent_25']:.0f}",
              [f"2027E PER {R['per27_now']:.1f}배 vs 피어 선행 PER 중앙값 {R['fpe_med']:.1f}배(셰브론·쉘·토탈·BP·코노코·에퀴노르·EOG·옥시·발레로·마라톤·필립스66)",
               f"DCF(WACC {pc(R['wacc'])}, 영구성장 2%)로 현재가를 맞추려면 2029년 이후 브렌트가 ${R['implied_b']:.0f}로 유지되어야 한다"])
rp.para(f"▶ 결론: 목표주가 {usd(TP)}(A. DCF {usd(B['va'])} × 50% + B. 2027E 조정 EPS ${FB[1]['eps']:.2f} × {B['mult']:.1f}배 {usd(B['vb'])} × 50%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(09-07, {O['rating']} {usd(O['tp'])}) 뒤 브렌트는 10월 말 $117까지 올랐다가 $93로 내렸고, 주가도 10-30 {u2(R['hi_since'])} 고점에서 {u2(PRICE)}로 내렸다. "
        f"지금 이익의 상당 부분이 정제마진 급등에서 나왔다는 점을 반영하면 현재가는 높다. 낙관 시나리오(브렌트 2027 $95·장기 $85)도 {usd(H['tp'])}다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.para("엑슨모빌은 미국 최대 석유·가스 회사다. 2026년 7월 1일 텍사스 이전 합병으로 상장 회사가 ExxonMobil Holdings Corporation으로 바뀌었다(주식 1:1 교환, 티커 XOM 그대로). "
        "Upstream(원유·가스 생산: 가이아나·퍼미안·LNG), Energy Products(정유·연료), Chemical Products(석유화학), Specialty Products(윤활유·특수소재) 네 부문으로 이익을 보고한다.")
seg_names = [("Upstream", "원유·가스 생산", "가이아나·퍼미안·Golden Pass LNG 물량 증가, 중동 물량 손실"),
             ("Energy Products", "정유·연료", "미국 걸프 정제가동률 100%, 경유 생산 최대"),
             ("Chemical Products", "석유화학", "북미 원료 우위, 아시아·유럽 마진은 10년 범위 아래"),
             ("Specialty Products", "윤활유·특수소재", "윤활기유 마진 상승"), ("Corporate", "본사·금융", "")]
rp.table([["부문", "사업", "3Q26 조정이익", "9M26", "9M25", "특징"]] +
         [[k, d, f0(SQ["3Q26"][k]), f0(SEG["2026"][k]), f0(SEG["2025"][k]), n] for k, d, n in seg_names] +
         [["합계", "", f0(SQ["3Q26"]["total"]), f0(Y9["2026"]["adj_earnings"]), f0(Y9["2025"]["adj_earnings"]), ""]],
         [17, 13, 13, 11, 11, 35], hl_rows=(6,), note="자료: 8-K 3Q26 보도자료(10-30). 조정이익 = 일회성 항목을 뺀 이익(Non-GAAP), $M.")
rp.h2("1-1. 원래 리포트 이후 주요 사건")
rp.table([["날짜", "사건", "내용"],
          ["2026-09-04", "원래 리포트 기준", f"종가 {u2(R['px_orig'])}, 브렌트 약 $95"],
          ["2026-09-23~25", "회사채 발행", "FWP·424B2(사채 발행 공시), 8-K(8.01)"],
          ["2026-10-01", "의견 하향", "Wells Fargo 비중확대 → 중립(언론 보도)"],
          ["2026-10-16", "8-K (7.01)", "3Q 실적 영향 사전 공시. 정제마진 상승으로 3Q 이익 약 $4.5B 증가 예상(Goldman 인용 보도)"],
          ["2026-10-30", "3Q26 실적", f"조정 EPS ${Qk['adj_eps']['3Q26']:.2f}, FCF {b(P3['fcf'])}, 2027 자사주 $20B. 종가 {u2(R['hi_since'])}(최고)"],
          ["2026-11-02~05", "유가 하락", "브렌트 $117(10-30) → $98(11-05), 주가 −12%"],
          ["2026-11-09", "기준일", f"브렌트 ${R['brent_now']:.1f}, 종가 {u2(PRICE)}"]],
         [15, 18, 67], note="자료: SEC 공시 목록, yfinance(종가·브렌트), 언론 보도(TIKR·Stocktwits·24/7 Wall St).")
rp.h2("1-2. 재무 상태 (2026-09-30)")
rp.table([["항목", "금액", "의미"], ["현금", b(BB["cash"]), ""], ["총차입", b(R["debt"]), "연초 대비 순차입 약 $11B 감소(회사)"],
          ["순차입", b(R["net_debt"]), f"시가총액의 {R['net_debt']/R['mcap']:.1%}"], ["자기자본", b(BB["equity"]), ""],
          ["발행주식", f"{R['sh_out']:,.0f}백만주", "9월말, 1년에 약 3% 감소(자사주)"]], [22, 18, 60])

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("3Q26 조정이익", b(P3["fcf"] * 0 + SQ["3Q26"]["total"]), f"2Q {b(SQ['2Q26']['total'])}"), ("3Q26 조정 EPS", f"${Qk['adj_eps']['3Q26']:.2f}", f"GAAP ${Qk['eps_diluted']['3Q26']:.2f}"),
              ("3Q26 FCF", b(P3["fcf"]), f"영업현금 {b(P3['cfo'])}"), ("3Q 주주환원", b(P3["distributions"]), "배당 $4.3B + 자사주 $5.1B")])
rp.img(HERE / "full_q.png", W)
rp.para(f"9개월 조정이익 증가분 {b(Y9['2026']['adj_earnings'] - Y9['2025']['adj_earnings'])} 중 {b(SEG['2026']['Energy Products'] - SEG['2025']['Energy Products'])}가 정유(Energy Products)에서 나왔다. "
        f"Upstream은 브렌트 평균이 ${R['brent_9m25']:.0f} → ${R['brent_9m26']:.0f}로 올랐지만 중동 물량 손실로 {b(SEG['2026']['Upstream'] - SEG['2025']['Upstream'])} 늘어나는 데 그쳤다"
        f"(생산량 9M 4,534 vs 4,651천 배럴/일). 3분기에는 유가가 내려 Upstream 이익이 2분기보다 줄고 정유 이익이 두 배 이상 늘었다.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 정제마진 급등은 일시적이다")
rp.para("회사 10-Q는 3분기 시장을 '중동 정제설비를 쓸 수 없어 정제마진이 10년 범위를 넘는 역사적 고점'으로 설명한다. 같은 이유로 원유 수요는 줄어 유가는 10년 범위 안에 머물렀다. "
        "정제설비가 복구되거나 다른 지역 가동률이 오르면 정제마진은 내려간다. 이 리포트는 2027년 정유 이익을 $11B(2026E의 약 절반), 2028년 이후 정상 $6.5B로 잡았다. "
        "2025년(9개월 $4.0B, 연환산 약 $5.3B)보다 조금 높은 값으로, 구조적 원가절감과 미국 걸프 증설(보몬트)을 반영했다.")
rp.h2("Thesis 2. 사업의 질은 좋아졌다")
rp.para(f"가이아나·퍼미안·Golden Pass LNG 물량이 늘고, 2019년 이후 구조적 원가절감이 {b(P3['structural_savings_since_2019'])}에 이른다. Papua LNG 운영권 인수, 모잠비크 Rovuma 지분 50% 확대 합의도 발표했다. "
        f"이 리포트는 물량 증가를 연 {pc(R['vol_g'],0)}(2030년까지)로 넣었다. 브렌트 $1당 Upstream 연 이익은 약 {b(R['up_sens'])}로 추정했다(2025·2026년 9개월 실적 차이 ÷ 브렌트 차이).")
rp.h2("Thesis 3. 피어와 비교한 가격")
pe = R["peers"]
rp.table([["회사", "선행 PER", "EV/EBITDA", "매출 성장"]] +
         [[pe[t]["shortName"].strip()[:28], f"{pe[t]['forwardPE']:.1f}" if pe[t].get("forwardPE") else "-",
           f"{pe[t]['enterpriseToEbitda']:.1f}" if pe[t].get("enterpriseToEbitda") else "-", pc(pe[t]["revenueGrowth"]) if pe[t].get("revenueGrowth") is not None else "-"] for t in pe] +
         [["중앙값", f"{R['fpe_med']:.1f}", f"{R['eveb_med']:.1f}", ""], ["엑슨모빌 (현재가, 2027E 기본)", f"{R['per27_now']:.1f}", "-", ""]],
         [40, 20, 20, 20], hl_rows=(len(pe) + 2,), note="자료: yfinance(2026-11-10 조회 = 11-09 종가 기준). 정유사(발레로·마라톤·필립스66)는 엑슨모빌 이익의 정유 비중이 커져 포함했다. 엑슨모빌 줄은 이 리포트 추정.")
rp.para(f"시장은 고점 이익을 내는 석유 회사에 낮은 배수를 준다. 정유사는 6~8배, 유럽 메이저는 7~9배다. 엑슨모빌은 원래 피어보다 높은 배수를 받아 왔지만, "
        f"2027E 기준 {R['per27_now']:.1f}배는 피어 상위 25%({R['mult']['1']:.1f}배)보다도 높다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.img(HERE / "full_earn.png", W)
pick = [FB[1], FB[2], FB[3], FB[4], FB[-1]]
rp.table([["항목 (기본, $M)", "2027E", "2028E", "2029E", "2030E", "2036E"],
          ["브렌트 ($/배럴)"] + [f"{r['brent']:.1f}" for r in pick],
          ["Upstream"] + [f0(r["up"]) for r in pick], ["Energy Products"] + [f0(r["ep"]) for r in pick],
          ["화학 + 특수 + 본사"] + [f0(r["chem"] + r["spec"] + r["corp"]) for r in pick],
          ["조정이익"] + [f0(r["adj"]) for r in pick], ["FCFF (이익 + 감가상각 − 설비투자)"] + [f0(r["fcff"]) for r in pick],
          ["조정 EPS ($)"] + [f"{r['eps']:.2f}" for r in pick]], [28, 14, 14, 14, 14, 16], hl_rows=(5,))
rp.para(f"Upstream = (2025년 연환산 {b(R['up_base'])} + 브렌트 $1당 {b(R['up_sens'])} × (브렌트 − ${R['brent_9m25']:.0f})) × 물량 증가. 2026E 4분기 조정이익은 {b(R['q4'])}"
        f"(3분기에서 유가 변화 반영, 정유는 3분기의 80%)로 2026E 조정 EPS ${R['eps26']:.2f}다. 감가상각과 설비투자는 2027~2028년 연 $27~28B로 거의 같아 FCFF는 조정이익과 비슷하다.")
rp.table([["가정", "보수", "기본", "낙관"],
          ["2027 브렌트 / 정유 이익", *[f"${SA[k]['b27']} / {b(SA[k]['ep27'])}" for k in ("보수", "기본", "낙관")]],
          ["2029년 이후 브렌트 / 정유 이익", *[f"${SA[k]['b_lt']} / {b(SA[k]['ep_lt'])}" for k in ("보수", "기본", "낙관")]],
          ["2027E 조정 EPS", *[f"${S[k]['rows'][1]['eps']:.2f}" for k in ("보수", "기본", "낙관")]],
          ["피어 선행 PER", *[f"{S[k]['mult']:.1f}배" for k in ("보수", "기본", "낙관")]]], [30, 23, 23, 24],
         note="2028년은 2027년과 장기값의 중간. 피어 배수: 보수 하위 25%, 기본 중앙값, 낙관 상위 25%.")

rp.h1("5. 밸류에이션 (Valuation)")
rp.table([["항목", "값", "근거"], ["미국채 10년", pc(R["ust"], 2), "2026-11-09 (yfinance ^TNX)"],
          ["베타", f"{R['beta']['blume']:.2f}", f"S&P500 대비 5년 주간 원베타 {R['beta']['raw']:.2f}, Blume 조정. 2년 베타({R['beta2']['raw']:.2f})는 유가 충격이 시장과 반대로 움직인 기간이라 쓰지 않음"],
          ["주식위험프리미엄", "5.0%", "미국 종목 공통"], ["자기자본비용", pc(R["coe"], 2), ""],
          ["세후 타인자본비용 / 부채 비중", f"{pc(R['kd'],2)} / {pc(R['wd'])}", ""], ["WACC", pc(R["wacc"], 2), "베타 1.0이면 9.9%(민감도 표 마지막 열)"],
          ["영구성장률", "2.0%", "에너지 전환을 감안해 미국 공통 3%보다 낮게"]], [26, 16, 58])
rp.h2("5-1. A. DCF")
rp.para(f"4Q26~2036 FCFF 현재가치 {b(B['pv'])} + 영구가치 {b(B['tv'])} − 순차입 {b(R['net_debt'])} ÷ 희석주식 {R['sh_dil']:,.0f}백만주 = **{usd(B['va'])}**.")
rp.h2("5-2. B. 2027E 조정 EPS × 피어 선행 PER")
rp.para(f"2027E 조정 EPS ${FB[1]['eps']:.2f} × 피어 중앙값 {B['mult']:.1f}배 = **{usd(B['vb'])}**. 피어 선행 PER도 높은 2027년 이익 추정에 붙은 배수라 같은 기준끼리 비교한 값이다.")
se = R["sens_e"]
rp.table([["2027 브렌트 \\ 정유 이익"] + [b(e) for e in se["ep"]]] + [[f"${x}"] + [f"${v:.2f}" for v in row] for x, row in zip(se["b"], se["v"])],
         [28, 24, 24, 24], note="2027E 조정 EPS. 브렌트 $10 = EPS 약 $0.9, 정유 이익 $5B = EPS 약 $1.3.")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. DCF", "50%", usd(L["va"]), usd(B["va"]), usd(H["va"])],
          ["B. PER", "50%", f"{usd(L['vb'])} ({L['mult']:.1f}배)", f"{usd(B['vb'])} ({B['mult']:.1f}배)", f"{usd(H['vb'])} ({H['mult']:.1f}배)"],
          ["목표주가", "", usd(L["tp"]), f"{u2(B['tp'])} → {usd(TP)}", usd(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [22, 10, 22, 24, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-4. 민감도 — 정상 브렌트 × WACC (목표주가)")
sn = R["sens"]
rp.table([["정상 브렌트 \\ WACC"] + [pc(w) for w in sn["wacc"]]] + [[f"${x}"] + [usd(v) for v in row] for x, row in zip(sn["b"], sn["v"])],
         [25, 18, 19, 19, 19], note="B는 기본값 고정. 마지막 열은 베타 1.0(시장 평균) 기준.")
rp.h2("5-5. 교차확인 — 애널리스트 의견")
rp.table([["기관·출처", "날짜", "의견", "목표가"], ["Wells Fargo", "10-01", "Equal Weight(하향)", "-"], ["Goldman Sachs", "10-16", "-", "$169"],
          ["TIKR 집계 (34명)", "08-01", "평균", "약 $170"], ["24/7 Wall St", "11-02", "Hold", "-"]],
         [30, 20, 25, 25], note="자료: TIKR·Stocktwits·24/7 Wall St 기사. 3Q 실적 이후 목표가 변경은 확인된 것이 적다. 목표가 계산에 넣지 않았다.")

rp.h1("6. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "중동 공급 차질 장기화", "호르무즈 제한·정제설비 손실이 2028년 이후까지 이어지면", f"낙관 {usd(H['tp'])}"],
          ["상방", "자사주 $20B", "시가총액의 약 3%를 매년 사들임", "주당 이익"],
          ["상방", "LNG·가이아나", "Papua LNG·Rovuma·가이아나 추가 개발이 계획보다 빠르면", "물량"],
          ["하방", "정제마진 정상화", "중동 정제설비 복구 시 정유 이익이 2025년 수준(연 약 $5B)으로", f"보수 {usd(L['tp'])}"],
          ["하방", "유가 하락", "브렌트 $65면 정상 이익 약 $32B", "민감도 표"]], [8, 22, 46, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {usd(TP)} (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {usd(TP)} · 보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"],
          ["확인할 일정", "① 4Q26 실적·2027 계획(1월 말) ② 호르무즈·중동 정제설비 복구 ③ 2027년 설비투자·자사주 계획 발표"],
          ["결론", f"사업은 좋아졌지만 지금 이익은 정제마진 급등 덕이 크다. 정상 이익({b(R['norm']['total'])}, 브렌트 $75) 기준으로 보면 현재가는 정상 브렌트 ${R['implied_b']:.0f}를 전제한다. {RATING}."]], [20, 80])
rp.since("8", "2026-09-07",
         [["항목", "원래 리포트 (2026-09-07)", "재조사 (2026-11-09)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {usd(O['tp'])}", f"{RATING} / {usd(TP)} (기준주가 {u2(PRICE)})"],
          ["주가", f"{u2(R['px_orig'])} (09-04 종가)", f"{u2(PRICE)} ({R['chg_since']*100:+.1f}%, 10-30 고점 {u2(R['hi_since'])})"],
          ["실적", "2Q26까지 (조정 EPS $3.52)", f"3Q26 조정 EPS ${Qk['adj_eps']['3Q26']:.2f}, 9개월 조정이익 {b(Y9['2026']['adj_earnings'])}"],
          ["브렌트", "약 $95 (09-04)", f"${R['brent_now']:.1f} (10-30 약 $117 고점 뒤 하락)"],
          ["평가 방법", O["method"], "A. DCF(정상 이익) 50 + B. 2027E 조정 EPS × 피어 선행 PER 50"],
          ["대안 시나리오", "-", f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]],
         ["3Q26(10-30): 정유 이익이 $9.1B로 2분기의 두 배를 넘었고 FCF $19.1B, 2027년 자사주 $20B를 발표했다.",
          "회사 10-Q는 정제마진이 중동 정제설비 손실로 역사적 고점이고, 유가는 10년 범위 안이라고 설명했다.",
          "브렌트는 10월 말 $117에서 11-09 $93로 내렸고 주가도 고점 대비 12% 내렸다. 미국채 10년 4.86%(11-09)."],
         ["목표가를 자체 추정과 피어 배수로만 계산했다. 애널리스트 목표가는 교차확인 표로만 둔다.",
          "부문별 이익을 브렌트와 정제 이익으로 나눠 추정하고, 일시적 정제마진을 2028년까지 정상화했다.",
          "베타는 2년 대신 5년 값을 썼다(2년은 유가 충격으로 시장과 반대 움직임)."],
         f"{usd(O['tp'])} → {usd(TP)}. 이익은 원래 예상보다 커졌지만 그 원인이 일시적인 정제마진이다. 정상 이익 기준 DCF와 피어 배수로 다시 계산하면 현재가가 높다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K 실적 보도자료), yfinance(시세·브렌트·미국채·피어 배수), 언론에 보도된 애널리스트 의견(TIKR, Stocktwits, 24/7 Wall St)을 바탕으로 작성한 개인 분석 자료입니다. "
              "애널리스트 목표가는 교차확인에만 썼습니다.")
out = HERE / "엑슨모빌_리서치리포트_20261109.docx"
rp.doc.save(out); print(out); to_pdf(out)
