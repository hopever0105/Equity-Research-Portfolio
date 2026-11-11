"""록히드마틴_리서치리포트_20261109.docx/.pdf — 2026-09-29 리포트를 2026-11-09 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_yf.csv. 실행: python valuation/록히드마틴/make_full_report.py
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
A_, Qk, Y9, SG, P3, GD = K["annual"], K["quarterly"], K["ytd_9m"], K["segments_3q26"], K["q3_26_press"], K["guidance_2026"]
GC, GJ = GD["current_20261022"], GD["july"]
b = lambda x: f"${x/1e3:,.1f}B"
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
usd = lambda x: f"${x:,.0f}"
u2 = lambda x: f"${x:,.2f}"
rg = lambda x, fmt=f0: f"{fmt(x[0])}~{fmt(x[1])}"

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / "full_price.png", "최근 2년 종가($), 기준일 2026-11-09", unit="$", alt=[(L["tp"], "보수")])
ql = ["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"]
bar_chart(ql, [("매출($B)", [Qk["revenue"][q] / 1e3 for q in ql], "#1F3864")],
          HERE / "full_q.png", "분기 매출($B)과 영업이익률(GAAP)", line=("영업이익률", [Qk["op_income"][q] / Qk["revenue"][q] for q in ql]), ylab="$B")
yrs = ["2023A", "2024A", "2025A", "2026E", "2027E", "2028E"]
revs = [A_["revenue"][y] for y in ("2023", "2024", "2025")] + [r["rev"] for r in FB[:3]]
bar_chart(yrs, [("매출($B)", [v / 1e3 for v in revs], "#1F3864")], HERE / "full_earn.png", "연간 매출($B)과 성장률 — 음영은 추정(기본, 2026E = 가이던스 중간값)", est_from=3,
          line=("매출 성장률", [0.0] + [revs[i] / revs[i - 1] - 1 for i in range(1, len(revs))]))
football_chart([("A. DCF (WACC %.1f%%)" % (R["wacc"] * 100), L["va"], B["va"], H["va"]), ("B. 2027E EPS × 방산 피어 선행 PER", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 50 : B 50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$")

SUB = f"수주잔고 {b(R['backlog'])}·가이던스 2분기 연속 상향 — 2027E 이익의 {R['per27_now']:.0f}배, 방산 피어({R['fpe_med']:.0f}배)보다 싸다"
MKT = [["현재주가 (2026.11.09 종가)", u2(PRICE)], ["시가총액", b(R["mcap"])], ["순차입 (9월말)", b(R["net_debt"])],
       ["52주 최고 / 최저 (장중)", f"{u2(R['hi52'])} / {u2(R['lo52'])}"], ["PER (2026E 가이던스)", f"{R['per26_now']:.1f}배"],
       ["PER (2027E 기본)", f"{R['per27_now']:.1f}배"], ["방산 피어 선행 PER 중앙값", f"{R['fpe_med']:.1f}배"],
       ["FCF 수익률 (2026E)", pc(R["fcf_yield"])], ["수주잔고 (9월말)", b(R["backlog"])], ["원래 리포트 (2026.09.29)", f"{O['rating']} · {usd(O['tp'])}"]]
ALT = [f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]

rp = Rep("글로벌 방위산업 (F-35·미사일)", "2026년 11월 9일")
rp.cover("록히드마틴 (Lockheed Martin, NYSE: LMT)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, $M)")
rows = [["항목", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출"] + [f0(A_["revenue"][y]) for y in ("2023", "2024", "2025")] + [f0(r["rev"]) for r in FB[:3]],
        ["영업이익"] + [f0(A_["op_income"][y]) for y in ("2023", "2024", "2025")] + [f0(r["op"]) for r in FB[:3]],
        ["영업이익률"] + [pc(A_["op_income"][y] / A_["revenue"][y]) for y in ("2023", "2024", "2025")] + [pc(r["op"] / r["rev"]) for r in FB[:3]],
        ["순이익"] + [f0(A_["net_income"][y]) for y in ("2023", "2024", "2025")] + [f0(r["ni"]) for r in FB[:3]],
        ["희석 EPS ($)"] + [f"{A_['eps_diluted'][y]:.2f}" for y in ("2023", "2024", "2025")] + [f"{r['eps']:.2f}" for r in FB[:3]],
        ["수주잔고 (연말)"] + [f0(A_["backlog_ye"][y]) for y in ("2023", "2024", "2025")] + [f"{f0(R['backlog'])} (9월)", "-", "-"]]
rp.table(rows, [24, 12, 12, 12, 14, 13, 13], hl_cols=(4, 5, 6),
         note="자료: SEC 10-K·10-Q·8-K. 2026E = 회사 가이던스 중간값(10-22: 매출 $80~82B, EPS $30.35~30.75). 영업이익 = 부문이익 + FAS/CAS 연금 조정 + 무형자산 상각·기타.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", f"수주잔고 {b(R['backlog'])} — 한 분기에 +27%, 매출의 {R['backlog']/R['rev26']:.1f}년치",
              [f"PAC-3 MSE 요격미사일 다년 생산계약 {b(P3['pac3_mse_multiyear'])}가 잔고에 들어왔다. Missiles and Fire Control 3Q 매출 +24%",
               "네 사업부문 모두 성장, 3Q 매출 +11%·EPS $7.97(+15%), 배당 24년 연속 인상"])
rp.thesis_box("②", "2026 가이던스 2분기 연속 상향 — FCF $7.8~8.0B",
              [f"매출 {rg(GJ['sales'])} → {rg(GC['sales'])}, EPS ${GJ['eps'][0]}~{GJ['eps'][1]} → ${GC['eps'][0]}~{GC['eps'][1]}, FCF ${GJ['fcf'][0]/1e3:.1f}~{GJ['fcf'][1]/1e3:.1f}B → ${GC['fcf'][0]/1e3:.1f}~{GC['fcf'][1]/1e3:.1f}B",
               f"9개월 부문 이익 {b(Y9['2026']['seg_op'])}(전년 {b(Y9['2025']['seg_op'])}) — 2025년 프로그램 손실 기저"])
rp.thesis_box("③", f"현재가는 2027E EPS의 {R['per27_now']:.1f}배 — 방산 피어 중앙값 {R['fpe_med']:.1f}배보다 낮다",
              [f"제너럴다이내믹스·노스롭그루먼·RTX·L3해리스·헌팅턴잉걸스 선행 PER {min(R['fpe'].values()):.1f}~{max(R['fpe'].values()):.1f}배(11-09)",
               f"FCF 수익률 {pc(R['fcf_yield'])}. 베타가 낮아(Blume {R['beta']['blume']:.2f}) 자본비용 {pc(R['wacc'])} — DCF 가치가 크다"])
rp.para(f"▶ 결론: 목표주가 {usd(TP)}(A. DCF {usd(B['va'])} × 50% + B. 2027E EPS ${FB[1]['eps']:.2f} × {B['mult']:.1f}배 {usd(B['vb'])} × 50%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(09-29, {O['rating']} {usd(O['tp'])}) 뒤 3분기 실적과 가이던스 상향으로 주가는 10-29 {u2(R['hi_since'])}까지 올랐다가 {u2(PRICE)}로 내렸다. "
        f"보수 시나리오(F-35 Lot 20 협상 손실·마진 정체)도 {usd(L['tp'])}로 현재가 위다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.para("록히드마틴은 세계 최대 방산 회사로, 매출 대부분이 미국 정부(국방부)와 미국 정부를 통한 해외 판매에서 나온다. 사업부문은 Aeronautics(F-35·F-16·C-130), "
        "Missiles and Fire Control(PAC-3·THAAD·GMLRS·PrSM), Rotary and Mission Systems(시코르스키 헬기·이지스·레이더), Space(위성·미사일 방어·전략미사일) 네 개다.")
rp.table([["부문 (3Q26)", "매출", "증가율", "영업이익", "9M 마진", "내용"]] +
         [[k, b(v["sales"]), pc(v["growth"], 0), b(v["op"]), pc(v["m9"]), v["note"]] for k, v in SG.items()],
         [24, 11, 9, 11, 10, 35], note="자료: 8-K 3Q26 보도자료(10-22).")
rp.h2("1-1. 원래 리포트 이후 주요 사건")
rp.table([["날짜", "사건", "내용"],
          ["2026-09-28", "원래 리포트 기준", f"종가 {u2(R['px_orig'])}"],
          ["2026-10-22", "3Q26 실적·가이던스 상향", f"매출 $20.7B, EPS $7.97, 수주잔고 $292B. 주가 {(R['px_earn']/R['px_pre']-1)*100:+.1f}%"],
          ["2026-10-22", "F-35 Lot 20", "Lot 20 이상 생산계약 정부와 협상 중. 3분기부터 선행계약 승인·자금 한도를 넘는 비용 발생(보도자료)"],
          ["2026-10-29", "주가 고점", f"종가 {u2(R['hi_since'])}"],
          ["2026-11-04~06", "주가 하락", "3거래일 −11%($639 → $567), 같은 기간 S&P500 −2.5%"],
          ["2026-11-09", "기준일", f"종가 {u2(PRICE)}"]],
         [15, 22, 63], note="자료: SEC 8-K, yfinance 종가.")
rp.h2("1-2. 재무 상태 (2026-09-27)")
bb = K["balance_20260927"]
rp.table([["항목", "금액", "의미"], ["현금", b(bb["cash"]), "연초 $4.1B"], ["차입", b(R["debt"]), "만기 1년 내 차입 없음"],
          ["순차입", b(R["net_debt"]), f"시가총액의 {R['net_debt']/R['mcap']:.1%}"], ["자기자본", b(bb["equity"]), "과거 자사주로 작음, 이익 누적으로 회복 중"],
          ["발행주식", f"{R['sh_out']:.1f}백만주", "10-19 기준"]], [22, 18, 60])

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("3Q26 매출", b(Qk["revenue"]["3Q26"]), "+11%"), ("3Q26 EPS", f"${Qk['eps_diluted']['3Q26']:.2f}", f"전년 ${Qk['eps_diluted']['3Q25']:.2f}"),
              ("3Q26 FCF", "$3.0B", "영업현금 $3.4B"), ("수주잔고", b(R["backlog"]), "분기 +27%")])
rp.img(HERE / "full_q.png", W)
rp.table([["2026 가이던스", "7월", "10-22 (상향)"],
          ["매출", f"${rg(GJ['sales'])}", f"${rg(GC['sales'])}"], ["부문 영업이익", f"${rg(GJ['seg_op'])}", f"${rg(GC['seg_op'])}"],
          ["희석 EPS", f"${GJ['eps'][0]}~{GJ['eps'][1]}", f"${GC['eps'][0]}~{GC['eps'][1]}"], ["영업현금흐름", f"${rg(GJ['cfo'])}", f"${rg(GC['cfo'])}"],
          ["FCF", f"${rg(GJ['fcf'])}", f"${rg(GC['fcf'])}"]], [34, 33, 33], note="자료: 8-K 3Q26 보도자료. 단위 $M(EPS 제외).")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 미사일 증산이 성장을 이끈다")
rp.para(f"Missiles and Fire Control 3분기 매출은 +24%로, PAC-3·THAAD(+$480M)와 GMLRS·PrSM(+$330M) 증산이 이끌었다. PAC-3 MSE 다년계약 {b(P3['pac3_mse_multiyear'])}로 "
        "생산 물량이 몇 년치 확보됐다. 이 부문은 마진이 14%로 회사 평균(약 10.6%)보다 높아, 비중이 커지면 전체 마진도 오른다. 이 리포트는 2027년 부문 마진 10.8%, 장기 11.0%를 기본으로 잡았다.")
rp.h2("Thesis 2. 2025년 손실 기저, 이익 정상화")
rp.para(f"2025년 2분기 프로그램 손실로 EPS가 $1.46까지 내려갔다. 2026년 9개월 EPS는 ${Y9['2026']['eps']:.2f}로 전년 ${Y9['2025']['eps']:.2f}보다 43% 늘었다. "
        f"Aeronautics 마진은 6.0% → 9.1%, Rotary and Mission Systems는 6.7% → 10.8%로 회복했다. 2026E EPS ${R['eps26']:.2f}(가이던스 중간값)는 2023년 $27.55를 넘는 최고치다.")
rp.h2("Thesis 3. 피어와 비교한 가격")
pe = R["peers"]
rp.table([["회사", "선행 PER", "EV/EBITDA", "매출 성장"]] +
         [[pe[t]["shortName"].strip()[:30], f"{pe[t]['forwardPE']:.1f}", f"{pe[t]['enterpriseToEbitda']:.1f}", pc(pe[t]["revenueGrowth"])] for t in pe] +
         [["중앙값", f"{R['fpe_med']:.1f}", f"{R['eveb_med']:.1f}", ""], ["록히드마틴 (현재가, 2027E 기본)", f"{R['per27_now']:.1f}", f"{R['ev_ebitda_lmt']:.1f}", "+11% (3Q)"]],
         [40, 20, 20, 20], hl_rows=(len(pe) + 2,), note="자료: yfinance(2026-11-10 조회 = 11-09 종가 기준). 보잉은 상업용 항공기 회복 중이라 배수가 의미 없어 제외. 록히드마틴 EV/EBITDA는 yfinance 최근 4분기.")
rp.para(f"록히드마틴은 방산 피어 가운데 PER이 낮은 편이다. 성장률(3Q +11%)은 피어와 비슷한데 2027E 기준 {R['per27_now']:.1f}배다. "
        "F-35 계약 협상과 2024~2025년 반복된 프로그램 손실이 할인 요인이다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.img(HERE / "full_earn.png", W)
pick = [FB[0], FB[1], FB[2], FB[4], FB[-1]]
rp.table([["항목 (기본, $M)", "2026E", "2027E", "2028E", "2030E", "2036E"],
          ["매출"] + [f0(r["rev"]) for r in pick], ["매출 성장률", pc(FB[0]["rev"] / A_["revenue"]["2025"] - 1)] + [pc(r["g"]) for r in pick[1:]],
          ["부문 영업이익"] + [f0(r["segop"]) for r in pick], ["부문 마진"] + [pc(r["m"]) for r in pick],
          ["순이익"] + [f0(r["ni"]) for r in pick], ["FCFF"] + [f0(r["fcff"]) for r in pick], ["희석 EPS ($)"] + [f"{r['eps']:.2f}" for r in pick]],
         [24, 15, 15, 15, 15, 16], hl_rows=(3,))
rp.para(f"영업이익 = 부문이익 + FAS/CAS 연금 조정 ${R['fas']/1e3:.2f}B(2026 가이던스, 고정) + 무형자산 상각·기타 ${R['unalloc']/1e3:.2f}B. 영업외 손익 ${R['nonop']/1e3:.2f}B는 2026 가이던스 EPS에 맞춰 역산해 고정했다. "
        f"세율 17%, 희석주식 연 1% 감소. FCFF = 순이익 × 현금전환율(기본 100%, 2026E 가이던스는 {pc(R['fcf_conv'],0)}) + 세후 이자.")
rp.table([["가정", "보수", "기본", "낙관"],
          ["2027 / 2028 매출 성장", *[f"{pc(SA[k]['g27'],0)} / {pc(SA[k]['g28'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2027 부문 마진 / 장기", *[f"{pc(SA[k]['m27'])} / {pc(SA[k]['m_lt'])}" for k in ("보수", "기본", "낙관")]],
          ["2029년 성장률 (2036년 3%로 수렴)", *[pc(SA[k]["g_late0"]) for k in ("보수", "기본", "낙관")]],
          ["현금전환율 (FCF/순이익)", *[pc(SA[k]["conv"], 0) for k in ("보수", "기본", "낙관")]],
          ["방산 피어 선행 PER", *[f"{S[k]['mult']:.1f}배" for k in ("보수", "기본", "낙관")]]], [30, 23, 23, 24],
         note="보수 = F-35 Lot 20 협상 지연으로 2027년 마진 9.5%. 낙관 = 미사일 증산이 계획대로. 피어 배수: 보수 하위 25%, 기본 중앙값, 낙관 상위 25%.")

rp.h1("5. 밸류에이션 (Valuation)")
rp.table([["항목", "값", "근거"], ["미국채 10년", pc(R["ust"], 2), "2026-11-09 (yfinance ^TNX)"],
          ["베타", f"{R['beta']['blume']:.2f}", f"S&P500(SPY) 대비 2년 주간 원베타 {R['beta']['raw']:.2f}, Blume 조정"],
          ["주식위험프리미엄", "5.0%", "미국 종목 공통"], ["자기자본비용", pc(R["coe"], 2), ""],
          ["세후 타인자본비용 / 부채 비중", f"{pc(R['kd'],2)} / {pc(R['wd'])}", ""], ["WACC", pc(R["wacc"], 2), ""], ["영구성장률", "3.0%", "미국 공통"]], [26, 18, 56])
rp.h2("5-1. A. DCF")
rp.para(f"4Q26~2036 FCFF 현재가치 {b(B['pv'])} + 영구가치 {b(B['tv'])} − 순차입 {b(R['net_debt'])} ÷ 희석주식 {R['sh_dil']:.1f}백만주 = **{usd(B['va'])}**. "
        f"영구가치 비중이 {B['tv']/(B['pv']+B['tv']):.0%}로 커서 WACC·영구성장률에 민감하다(5-4).")
rp.h2("5-2. B. 2027E EPS × 방산 피어 선행 PER")
rp.para(f"2027E EPS ${FB[1]['eps']:.2f} × 피어 중앙값 {B['mult']:.1f}배 = **{usd(B['vb'])}**.")
sb = R["sens_b"]
rp.table([["2027 부문 마진 \\ PER"] + [f"{p:.1f}배" for p in sb["per"]]] + [[pc(m)] + [usd(x) for x in row] for m, row in zip(sb["m"], sb["v"])],
         [28, 24, 24, 24], note="B 값($).")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. DCF", "50%", usd(L["va"]), usd(B["va"]), usd(H["va"])],
          ["B. PER", "50%", f"{usd(L['vb'])} ({L['mult']:.1f}배)", f"{usd(B['vb'])} ({B['mult']:.1f}배)", f"{usd(H['vb'])} ({H['mult']:.1f}배)"],
          ["목표주가", "", usd(L["tp"]), f"{usd(B['tp'])} → {usd(TP)}", usd(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [22, 10, 22, 24, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-4. 민감도 — 영구성장률 × WACC (목표주가)")
sn = R["sens"]
rp.table([["영구성장 \\ WACC"] + [pc(w) for w in sn["wacc"]]] + [[pc(g_)] + [usd(x) for x in row] for g_, row in zip(sn["g"], sn["v"])],
         [25, 18, 19, 19, 19], note="B는 기본값 고정. WACC를 2%p 올리고(8.9%) 영구성장 2%로 낮춰도 현재가 근처다.")
rp.h2("5-5. 교차확인 — 애널리스트 목표가 (3Q26 실적 이후)")
rp.table([["기관", "의견", "목표가 (이전)"], ["Citi", "Buy", "$706 ($691)"], ["UBS", "Buy", "$692 ($653)"], ["TD Cowen", "Buy", "$610 ($560)"],
          ["RBC", "Sector Perform", "$600 ($550)"], ["Barclays", "Equal Weight", "$560 ($554)"]],
         [34, 33, 33], note="자료: TipRanks(The Fly)·Stocktwits·TIKR 기사(10월 말). 모두 상향, 범위 $560~706. 이 리포트 목표가는 범위 위에 있다 — 차이는 낮은 베타로 계산한 DCF(A)에서 나온다. 목표가 계산에 넣지 않았다.")

rp.h1("6. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "미사일 추가 다년계약", "THAAD·PrSM 등 다년계약이 이어지면 성장률 상향", f"낙관 {usd(H['tp'])}"],
          ["상방", "자사주 재개", "1Q26 자사주 매입 0 — FCF $8B로 재개 여력", "주당가치"],
          ["하방", "F-35 Lot 20 협상", "승인·자금 없이 비용이 늘면 손실·현금 지연(보도자료 경고)", f"보수 {usd(L['tp'])}"],
          ["하방", "고정가 개발계약 손실", "2024~2025년처럼 프로그램 손실이 반복되면", "마진"],
          ["하방", "할인율", "베타·금리가 오르면 DCF 가치가 크게 줄어든다(TV 비중 약 70%)", "5-4 표"]], [8, 22, 46, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {usd(TP)} (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {usd(TP)} · 보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"],
          ["확인할 일정", "① F-35 Lot 20~22 생산계약 체결 ② 4Q26 실적·2027 가이던스(1월) ③ 2027 국방예산"],
          ["결론", f"수주잔고와 가이던스가 함께 올랐고, 2027E PER {R['per27_now']:.1f}배는 방산 피어보다 낮다. 낮은 자본비용을 쓴 현금흐름 가치도 현재가보다 높다. 원래 의견 {O['rating']}를 유지하고 목표가를 올린다."]], [20, 80])
rp.since("8", "2026-09-29",
         [["항목", "원래 리포트 (2026-09-29)", "재조사 (2026-11-09)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {usd(O['tp'])}", f"{RATING} / {usd(TP)} (기준주가 {u2(PRICE)})"],
          ["주가", f"{u2(R['px_orig'])} (09-28 종가)", f"{u2(PRICE)} ({R['chg_since']*100:+.1f}%, 10-29 고점 {u2(R['hi_since'])})"],
          ["실적", "2Q26까지 (EPS $7.94)", "3Q26 매출 $20.7B(+11%), EPS $7.97, 수주잔고 $292B"],
          ["2026 가이던스", "EPS $29.95~30.65, FCF $7.0~7.2B", "EPS $30.35~30.75, FCF $7.8~8.0B"],
          ["평가 방법", O["method"], "A. DCF(FCFF) 50 + B. 2027E EPS × 방산 피어 선행 PER 50"],
          ["대안 시나리오", "-", f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]],
         ["3Q26(10-22): 매출·EPS가 예상을 넘었고, 2026 가이던스를 두 분기 연속 올렸다. 실적 발표일 주가 +7%.",
          "수주잔고가 한 분기에 $230.4B → $292.0B로 늘었다(PAC-3 MSE 다년계약 $52.5B).",
          "F-35 Lot 20 이상 생산계약은 아직 협상 중이고, 3분기부터 선행계약 한도를 넘는 비용이 생겼다.",
          "애널리스트 목표가는 실적 뒤 모두 올랐다($560~706). 미국채 10년 4.86%(11-09)."],
         ["목표가를 자체 추정(DCF)과 방산 피어 배수로만 계산했다. 애널리스트 목표가는 교차확인 표로만 둔다.",
          "2026E는 회사 가이던스 중간값, 2027년 이후는 부문 마진과 수주잔고로 추정했다.",
          "F-35 협상 위험은 보수 시나리오(2027년 마진 9.5%)로 따로 보였다."],
         f"{usd(O['tp'])} → {usd(TP)}. 수주와 가이던스가 원래 기대보다 좋아졌고, 자체 현금흐름 가치와 피어 배수 모두 현재가보다 높다. "
         f"상승여력 {UP*100:+.1f}%로 {RATING}를 유지한다.")
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K 실적 보도자료), yfinance(시세·미국채·피어 배수), 언론에 보도된 애널리스트 의견(TipRanks, Stocktwits, TIKR)을 바탕으로 작성한 개인 분석 자료입니다. "
              "애널리스트 목표가는 교차확인에만 썼습니다.")
out = HERE / "록히드마틴_리서치리포트_20261109.docx"
rp.doc.save(out); print(out); to_pdf(out)
