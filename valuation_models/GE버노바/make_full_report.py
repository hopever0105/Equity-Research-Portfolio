"""GE버노바_리서치리포트_20261106.docx/.pdf — 2026-09-01 리포트를 2026-11-06 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_yf.csv. 실행: python valuation/GE버노바/make_full_report.py
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
A_, Qk, P3, GD = K["annual"], K["quarterly"], K["q3_26_press"], K["guidance_2026_as_of_20261028"]
b = lambda x: f"${x/1e3:,.1f}B"
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
usd = lambda x: f"${x:,.0f}"

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / "full_price.png", "최근 2년 종가($), 기준일 2026-11-06", unit="$", alt=[(H["tp"], "낙관")])
ql = ["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"]
bar_chart(ql, [("매출($B)", [Qk["revenue"][q] / 1e3 for q in ql], "#1F3864")], HERE / "full_q.png",
          "분기 매출($B)과 영업이익률(GAAP)", line=("영업이익률", [Qk["op_income"][q] / Qk["revenue"][q] for q in ql]), ylab="$B")
yrs = ["2023A", "2024A", "2025A", "2026E", "2027E", "2028E"]
revs = [A_["revenue"][y] for y in ("2023", "2024", "2025")] + [r["rev"] for r in FB[:3]]
bar_chart(yrs, [("매출($B)", [v / 1e3 for v in revs], "#1F3864")],
          HERE / "full_earn.png", "연간 매출($B)과 성장률 — 음영은 추정(기본, 2026E = 회사 가이던스 중간값)", est_from=3,
          line=("매출 성장률", [0.0] + [revs[i] / revs[i - 1] - 1 for i in range(1, len(revs))]))
football_chart([("A. DCF (WACC %.1f%%)" % (R["wacc"] * 100), L["va"], B["va"], H["va"]), ("B. 2027E EBITDA × 피어 EV/EBITDA", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 60 : B 40)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$")

SUB = f"수주 $29B·백로그 $197B·가이던스 상향 — 사업은 최고조, 그러나 현재가는 2029~2036년에도 연 {R['implied_g']*100:.0f}% 성장을 요구한다"
MKT = [["현재주가 (2026.11.06 종가)", usd(PRICE)], ["시가총액", b(R["mcap"])], ["순현금 (9월말)", b(R["net_cash"])],
       ["52주 최고 / 최저 (장중)", f"{usd(R['hi52'])} / {usd(R['lo52'])}"], ["EV / 2026E 조정 EBITDA", f"{R['ev_ebitda26']:.1f}배"],
       ["EV / 2027E 조정 EBITDA (기본)", f"{R['ev_ebitda27']:.1f}배"], ["PER (2027E 기본)", f"{R['per27_now']:.1f}배"],
       ["백로그 (9월말)", b(R["backlog"])], ["피어 EV/EBITDA 중앙값", f"{R['eveb_med']:.1f}배"], ["원래 리포트 (2026.09.01)", f"{O['rating']} · {usd(O['tp'])}"]]
ALT = [f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]

rp = Rep("전력 인프라 (발전·전력망·풍력)", "2026년 11월 6일")
rp.cover("GE버노바 (GE Vernova, NYSE: GEV)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, $M)")
rows = [["항목", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출"] + [f0(A_["revenue"][y]) for y in ("2023", "2024", "2025")] + [f0(r["rev"]) for r in FB[:3]],
        ["영업이익 (GAAP)"] + [f0(A_["op_income"][y]) for y in ("2023", "2024", "2025")] + ["-", "-", "-"],
        ["조정 EBITDA"] + ["-", "-", "-"] + [f0(r["ebitda"]) for r in FB[:3]],
        ["조정 EBITDA 마진"] + ["-", "-", "-"] + [pc(r["m"]) for r in FB[:3]],
        ["순이익 (GAAP / 추정)"] + [f0(A_["net_income"][y]) for y in ("2023", "2024", "2025")] + [f0(r["ni"]) for r in FB[:3]],
        ["희석 EPS ($)"] + [f"{A_['eps_diluted'][y]:.2f}" for y in ("2023", "2024", "2025")] + [f"{r['eps']:.2f}" for r in FB[:3]]]
rp.table(rows, [24, 12, 12, 12, 13, 13, 14], hl_cols=(4, 5, 6),
         note="자료: SEC 10-K·10-Q·8-K. 2026E = 회사 가이던스 중간값(매출 $47.0B, 조정 EBITDA 마진 14%). 추정 순이익 = (EBITDA − 감가상각 매출 2.5%) × (1 − 21%), 일회성 제외. "
              "2025 순이익에는 세금 환입, 2026 1Q에는 Prolec GE 관련 일회성 이익이 있다.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", f"사업은 최고조 — 3Q26 수주 {b(P3['orders'])}(유기적 +96%), 백로그 {b(R['backlog'])}",
              [f"가스터빈 백로그+슬롯 예약 {P3['power']['gas_backlog_slot_gw']}GW → 연말 130GW 이상, 2026 가이던스 상향(매출 $46.5~47.5B, FCF $16~17B)",
               "자사주 매입 한도 $10B → $20B, Trench Group $9.0B 인수(전력망 장비), Fitch A− 상향"])
rp.thesis_box("②", "FCF $16~17B는 선수금 덕 — 정상 현금흐름은 그 절반 이하",
              [f"9월말 계약부채(선수금) {b(B_cl := K['balance_20260930']['contract_liab_current'])}, 1년 새 $25.5B 증가. 3Q FCF $5.4B 중 $5.3B가 운전자본(선수금)에서 나왔다(언론 보도)",
               f"이 리포트는 FCFF를 조정 EBITDA의 {pc(SA['기본']['conv'],0)}로 정상화했다 — 2027E FCFF {b(FB[1]['fcff'])}"])
rp.thesis_box("③", f"현재가는 2027E EBITDA의 {R['ev_ebitda27']:.0f}배 — 피어 중앙값 {R['eveb_med']:.0f}배",
              [f"이튼·버티브·지멘스에너지·슈나이더·허벨·히타치의 EV/EBITDA 중앙값 {R['eveb_med']:.1f}배, 선행 PER 중앙값 {R['fpe_med']:.1f}배(11-06)",
               f"DCF(WACC {pc(R['wacc'])})로 현재가를 맞추려면 2029~2036년 매출이 매년 {R['implied_g']*100:.0f}% 늘어야 한다"])
rp.para(f"▶ 결론: 목표주가 {usd(TP)}(A. DCF {usd(B['va'])} × 60% + B. 2027E EBITDA × {B['mult']:.1f}배 {usd(B['vb'])} × 40%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(09-01, {O['rating']} {usd(O['tp'])}) 이후 실적은 기대보다 좋았지만 주가는 10-06 {usd(R['hi_since'])} 고점 뒤 AI 투자 우려로 {usd(PRICE)}까지 내렸다. "
        f"그래도 현금흐름 기준으로는 비싸다. 낙관 시나리오도 {usd(H['tp'])}로 현재가 아래다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.para("GE버노바는 2024년 4월 제너럴일렉트릭(GE)에서 분사한 에너지 장비 회사다. Power(가스터빈·원전·수력, 서비스), Electrification(변압기·전력망·전력변환, Prolec GE 포함), "
        "Wind(육상·해상 풍력) 세 부문으로 나뉜다. 데이터센터와 전력망 투자로 가스터빈과 전력망 장비 수요가 몰리면서 수주와 가격이 함께 오르고 있다.")
rp.table([["부문 (3Q26)", "수주", "매출", "특징"],
          ["Power", b(P3["power"]["orders"]), b(P3["power"]["rev"]), "수주 +178%(유기적), 가스 장비 11GW 신규 계약, EBITDA 마진 +800bp"],
          ["Electrification", b(P3["electrification"]["orders"]), b(P3["electrification"]["rev"]), f"수주 −9%(전년 대형 수주 기저), 장비 백로그 {b(P3['electrification']['equip_backlog'])}"],
          ["Wind", b(P3["wind"]["orders"]), b(P3["wind"]["rev"]), "수주 +16%, Vineyard Wind 소송 모두 해결, 2026 EBITDA 손실 $4~5억"]],
         [18, 14, 14, 54], note="자료: 8-K 3Q26 보도자료(10-28).")
rp.h2("1-1. 원래 리포트 이후 주요 사건")
rp.table([["날짜", "사건", "내용"],
          ["2026-08", "신용등급", "Fitch A−로 상향(BBB+에서), 전망 안정적"],
          ["2026-08-27", "8-K (5.02)", "임원 변동 공시"],
          ["2026-10-06", "주가 고점", f"종가 {usd(R['hi_since'])}"],
          ["2026-10-22", "AI 투자 우려", "메타 실적 발표 뒤 데이터센터 투자 지속성 우려로 하루 약 −11%(언론 보도)"],
          ["2026-10-28", "3Q26 실적·가이던스 상향", "매출 $12.6B, 수주 $29.3B, 2026 FCF 가이던스 $16~17B로 상향"],
          ["2026-10", "자본배분", "자사주 한도 $20B(잔여 $10.1B), Trench Group $9.0B 인수 계약(2027년 말 완료 예정)"],
          ["2026-11-05", "시장 급락", "S&P500 −4.4%, GE버노바 −7.5%($832.83 → $770.51)"]],
         [14, 22, 64], note="자료: SEC 8-K, 실적 보도자료, yfinance 종가, 언론 보도.")
rp.h2("1-2. 재무 상태 (2026-09-30)")
bb = K["balance_20260930"]
rp.table([["항목", "금액", "의미"], ["현금(제한 현금 포함)", b(bb["cash_incl_restricted"]), "분기 +$3.6B"],
          ["차입", b(R["debt"]), "2026 1Q 장기채 발행 $2.6B (같은 분기 인수 지출 $4.9B)"], ["계약부채(선수금)", b(bb["contract_liab_current"]), "1년 새 +$25.5B — FCF의 원천"],
          ["자기자본", b(bb["equity"]), "자사주 매입으로 감소 추세"], ["발행주식", f"{R['sh_out']:.1f}백만주", "9월말"]], [26, 18, 56])

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("3Q26 매출", b(Qk["revenue"]["3Q26"]), "+27% (유기적 +18%)"), ("3Q26 조정 EBITDA", b(P3["adj_ebitda"]), f"마진 {pc(P3['adj_ebitda_margin'])}"),
              ("3Q26 희석 EPS", f"${Qk['eps_diluted']['3Q26']:.2f}", f"전년 ${Qk['eps_diluted']['3Q25']:.2f}"), ("3Q26 FCF", b(P3["fcf"]), "선수금 유입 포함")])
rp.img(HERE / "full_q.png", W)
rp.table([["2026 가이던스", "7월", "10-28 (상향)"],
          ["매출", "$45.5~46.5B", "$46.5~47.5B"], ["조정 EBITDA 마진", "12~14%", "13.5~14.5%"], ["FCF", "$11.5~12.5B", "$16~17B"],
          ["Power 유기적 성장 / 마진", "18~20% / 17~19%", "19~21% / 19~21%"]], [34, 33, 33], note="자료: 8-K 3Q26 보도자료.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 수요는 의심할 필요가 없다")
rp.para(f"9월말 백로그 {b(R['backlog'])}는 2026E 매출의 {R['backlog']/R['rev26']:.1f}년치다. 가스터빈은 2028년 이후 납기까지 차 있고, 경영진은 4분기 백로그가 $200B를 넘고 마진도 개선된다고 했다. "
        "HA 가스터빈은 2027년 말까지 400대 이상 출하가 예정돼 있다(실적 발표). 문제는 수요가 아니라 그 수요가 이미 얼마나 가격에 들어 있는가다.")
rp.h2("Thesis 2. 선수금이 만든 현금 — 정상 FCF로 봐야 한다")
rp.para(f"고객이 가스터빈 슬롯을 잡으려고 선금을 내면서 계약부채가 2025년 9월 $20.2B → 2026년 9월 {b(K['balance_20260930']['contract_liab_current'])}로 늘었다. 이 돈은 장비를 넘길 때 매출로 바뀌며 "
        "현금흐름에서는 되돌려진다. 그래서 2026 FCF 가이던스 $16~17B를 그대로 할인하면 가치가 부풀려진다. 이 리포트는 FCFF를 조정 EBITDA의 65%(세금·설비투자·운전자본 정상화)로 계산했다.")
rp.h2("Thesis 3. 피어와 비교한 가격")
pe = R["peers"]
rp.table([["회사", "EV/EBITDA", "선행 PER", "매출 성장"]] +
         [[pe[t]["shortName"].strip()[:28], f"{pe[t]['enterpriseToEbitda']:.1f}" if pe[t].get("enterpriseToEbitda") else "-",
           f"{pe[t]['forwardPE']:.1f}" if pe[t].get("forwardPE") else "-", pc(pe[t]["revenueGrowth"]) if pe[t].get("revenueGrowth") else "-"] for t in pe] +
         [["중앙값", f"{R['eveb_med']:.1f}", f"{R['fpe_med']:.1f}", ""], ["GE버노바 (현재가, 2027E 기본)", f"{R['ev_ebitda27']:.1f}", f"{R['per27_now']:.1f}", "+27% (3Q)"]],
         [40, 20, 20, 20], hl_rows=(len(pe) + 2,), note="자료: yfinance(2026-11-08 조회 = 11-06 종가 기준). EV/EBITDA는 최근 4분기, 선행 PER은 yfinance 추정 EPS 기준. GE버노바 줄은 이 리포트 추정.")

rp.h2("Thesis 4. 자본배분 — 자사주와 전력망 인수")
rp.para(f"9개월 동안 자사주 {b(K['ytd_9m26']['buyback'])}, 배당 {b(K['ytd_9m26']['dividends'])}를 썼고 이사회는 매입 한도를 $20B로 늘렸다. 2024년 12월 이후 평균 매입 단가는 약 $635다(회사 발표). "
        "Trench Group 인수($9.0B, 2028 EBITDA 기준 약 13배, 회사 설명)는 고압 전력망 장비를 넓힌다. 피어 EV/EBITDA(18.7배)보다 낮은 배수의 인수라 가치에 긍정적이지만, "
        "완료가 2027년 말이라 이 리포트 추정에는 넣지 않았다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.img(HERE / "full_earn.png", W)
pick = [FB[0], FB[1], FB[2], FB[4], FB[-1]]
rp.table([["항목 (기본, $M)", "2026E", "2027E", "2028E", "2030E", "2036E"],
          ["매출"] + [f0(r["rev"]) for r in pick], ["매출 성장률", "+23%", pc(SA["기본"]["g27"], 0), pc(SA["기본"]["g28"], 0), pc(R["g_late"][1], 0), pc(R["g_late"][-1])],
          ["조정 EBITDA"] + [f0(r["ebitda"]) for r in pick], ["조정 EBITDA 마진"] + [pc(r["m"]) for r in pick],
          ["FCFF (EBITDA × 65%)"] + [f0(r["fcff"]) for r in pick], ["희석 EPS ($)"] + [f"{r['eps']:.2f}" for r in pick]],
         [24, 15, 15, 15, 15, 16], hl_rows=(3,))
rp.para(f"2027E·2028E 매출 성장률은 백로그 소진 속도(연 매출의 4년치)와 Power 가이던스(유기적 19~21%)를 감안해 +15%·+12%로 잡았다. 2028E 매출 {b(FB[2]['rev'])}는 경영진 목표 'at least $56B'(언론 인용)보다 높고 "
        f"애널리스트 추정 약 $61B와 비슷하다. 2028E EPS ${FB[2]['eps']:.2f}는 컨센서스($36~37, TIKR 인용)보다 낮다 — 마진 가정(19%)이 보수적이기 때문이다.")
rp.table([["가정", "보수", "기본", "낙관"],
          ["2027 / 2028 매출 성장", *[f"{pc(SA[k]['g27'],0)} / {pc(SA[k]['g28'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2027 / 2028 EBITDA 마진", *[f"{pc(SA[k]['m27'])} / {pc(SA[k]['m28'])}" for k in ("보수", "기본", "낙관")]],
          ["장기 EBITDA 마진 (2036)", *[pc(SA[k]["m_lt"], 0) for k in ("보수", "기본", "낙관")]],
          ["현금전환율 (FCFF/EBITDA)", *[pc(SA[k]["conv"], 0) for k in ("보수", "기본", "낙관")]],
          ["피어 EV/EBITDA", *[f"{S[k]['mult']:.1f}배" for k in ("보수", "기본", "낙관")]]], [30, 23, 23, 24],
         note="피어 배수: 보수 하위 25%, 기본 중앙값, 낙관 상위 25%.")

rp.h1("5. 밸류에이션 (Valuation)")
rp.table([["항목", "값", "근거"], ["미국채 10년", pc(R["ust"], 2), "2026-11-06 (yfinance ^TNX)"],
          ["베타", f"{R['beta']['blume']:.2f}", f"S&P500(SPY) 대비 2년 주간 원베타 {R['beta']['raw']:.2f}, Blume 조정"],
          ["주식위험프리미엄", "5.0%", "미국 종목 공통"], ["WACC (= 자기자본비용)", pc(R["wacc"], 2), "순현금"], ["영구성장률", "3.0%", ""]], [22, 14, 64])
rp.h2("5-1. A. DCF")
rp.para(f"4Q26~2036 FCFF 현재가치 {b(B['pv'])} + 영구가치 {b(B['tv'])} + 순현금 {b(R['net_cash'])} ÷ 희석주식 {R['sh_dil']:.0f}백만주 = **{usd(B['va'])}**.")
sc_ = R["sens_c"]
rp.table([["현금전환율 \\ WACC"] + [pc(w) for w in sc_["wacc"]]] + [[pc(c, 0)] + [usd(x) for x in row] for c, row in zip(sc_["conv"], sc_["v"])],
         [25, 18, 19, 19, 19], note="A 값($).")
rp.h2("5-2. B. 2027E 조정 EBITDA × 피어 EV/EBITDA")
rp.para(f"2027E 조정 EBITDA {b(FB[1]['ebitda'])} × {B['mult']:.1f}배 + 순현금 {b(R['net_cash'])} = 주당 **{usd(B['vb'])}**. GE버노바의 성장률이 피어보다 높다는 점은 2027E(1년 뒤) EBITDA를 쓰는 것으로 반영했다.")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. DCF", "60%", usd(L["va"]), usd(B["va"]), usd(H["va"])],
          ["B. EV/EBITDA", "40%", f"{usd(L['vb'])} ({L['mult']:.1f}배)", f"{usd(B['vb'])} ({B['mult']:.1f}배)", f"{usd(H['vb'])} ({H['mult']:.1f}배)"],
          ["목표주가", "", usd(L["tp"]), f"{usd(B['tp'])} → {usd(TP)}", usd(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [22, 10, 22, 24, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-4. 민감도 — 장기 EBITDA 마진 × WACC (목표주가)")
sn = R["sens"]
rp.table([["장기 마진 \\ WACC"] + [pc(w) for w in sn["wacc"]]] + [[pc(m, 0)] + [usd(x) for x in row] for m, row in zip(sn["m"], sn["v"])],
         [25, 18, 19, 19, 19], note="B는 기본값 고정.")
rp.h2("5-5. 교차확인 — 애널리스트 목표가 (3Q26 실적 이후)")
rp.table([["기관", "날짜", "의견", "목표가 (이전)"]] + [[a, d, c, f"{usd(t)}" + (f" ({usd(p)})" if p else "")] for a, d, c, t, p in R["analysts"]],
         [30, 20, 20, 30], note="자료: Yahoo Finance 기사(10-30~11-03). 목표가는 모두 인하 방향. 산출 방법은 공개되지 않았다(기사 환산 NTM PER 52~61배). 목표가 계산에 넣지 않았다.")

rp.h1("6. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "가격 결정력 지속", "가스터빈 공급 부족이 2030년 이후까지 이어져 마진이 25%를 넘으면", f"낙관 {usd(H['tp'])}"],
          ["상방", "자사주 $20B", "남은 한도 $10.1B — 시가총액의 약 5%", "주당가치"],
          ["하방", "AI 투자 속도 조절", "10-22 메타 실적 뒤 하루 −11%처럼 데이터센터 투자 우려가 배수를 낮춤", f"보수 {usd(L['tp'])}"],
          ["하방", "가스 수주 단가", "4분기 kW당 가격 하락 언급(50Hz 비중 증가)", "마진"],
          ["하방", "Wind 손실", "2026 EBITDA 손실 $4~5억으로 확대", "마진"]], [8, 20, 48, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {usd(TP)} (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {usd(TP)} · 보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"],
          ["확인할 일정", "① 4Q26 실적·2027 가이던스(1월) ② 다음 Capital Markets Day와 2030 목표 ③ Trench 인수 승인"],
          ["결론", f"수주·백로그·가이던스 모두 좋지만, 현재가는 2027E EBITDA의 {R['ev_ebitda27']:.0f}배로 피어보다 약 {R['ev_ebitda27']/R['eveb_med']-1:.0%} 비싸고, 현금흐름으로는 장기 고성장 지속을 전제한다. "
                   f"사업이 아니라 가격 때문에 {RATING}."]], [20, 80])
rp.since("8", "2026-09-01",
         [["항목", "원래 리포트 (2026-09-01)", "재조사 (2026-11-06)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {usd(O['tp'])}", f"{RATING} / {usd(TP)} (기준주가 {usd(PRICE)})"],
          ["주가", f"{usd(R['px_orig'])} (08-28 종가)", f"{usd(PRICE)} ({R['chg_since']*100:+.1f}%, 10-06 고점 {usd(R['hi_since'])})"],
          ["실적", "2Q26까지", "3Q26 매출 $12.6B(+27%), 수주 $29.3B, 백로그 $196.7B"],
          ["2026 가이던스", "매출 $45.5~46.5B, FCF $11.5~12.5B", "매출 $46.5~47.5B, FCF $16~17B"],
          ["평가 방법", O["method"], "A. DCF(정상 FCFF) 60 + B. 2027E EBITDA × 피어 EV/EBITDA 40"],
          ["대안 시나리오", "-", f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]],
         ["3Q26(10-28): 매출·EPS가 시장 예상을 넘었고 2026 가이던스를 올렸다. 자사주 한도 $20B로 확대, Trench Group $9.0B 인수 발표.",
          "주가: 10-06 $1,029(최고) → 10-22 메타 실적 뒤 AI 투자 우려로 하루 −11% → 11-05 S&P500 −4.4% 급락일에 −7.5% → 11-06 $774.",
          "애널리스트들은 실적 후 목표가를 대부분 인하($1,000~1,400).", "미국채 10년 4.86%(11-06)."],
         ["목표가를 자체 추정과 피어 배수로만 계산했다. 애널리스트 목표가는 교차확인 표로만 둔다.",
          "선수금으로 부풀려진 FCF 대신 조정 EBITDA × 현금전환율 65%로 정상 FCFF를 썼다.",
          "피어 EV/EBITDA(11-06, 6개사)로 시장이 전력 장비에 주는 배수를 확인했다."],
         f"{usd(O['tp'])} → {usd(TP)}. 실적과 수주는 원래 기대보다 좋아졌지만, 정상 현금흐름 기준 DCF와 피어 배수로 다시 계산하면 현재가도 높다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K 실적 보도자료), yfinance(시세·미국채·피어 배수), 언론에 보도된 애널리스트 의견(Yahoo Finance, Investing.com 실적 발표 기록)을 바탕으로 작성한 개인 분석 자료입니다. "
              "애널리스트 목표가는 교차확인에만 썼습니다.")
out = HERE / "GE버노바_리서치리포트_20261106.docx"
rp.doc.save(out); print(out); to_pdf(out)
