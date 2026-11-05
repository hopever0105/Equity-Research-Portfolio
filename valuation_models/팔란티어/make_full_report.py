"""팔란티어_리서치리포트_20261105.docx/.pdf — 2026-08-11 리포트를 2026-11-05 기준으로 다시 조사한 후속 리포트.
서식은 valuation/tools/report_kit.py. 입력: results.json(model.py), price_db.csv. 실행: python valuation/팔란티어/make_full_report.py
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
PRICE, TP, UP, RATING = R["price"], R["tp"], R["upside"], R["rating"]
K = R["key"]; A = K["annual"]; Q = K["quarterly"]; PR = K["press_release_3Q26"]; O = R["orig"]; T = R["ttm"]
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
bn = lambda x: f"${x/1e3:,.2f}B"

px = pd.read_csv(HERE / "price_db.csv", parse_dates=["날짜"]).set_index("날짜")
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["pxdate"])]
price_chart(list(p2.index), list(p2["종가"]), TP, HERE / "full_price.png", "최근 2년 종가($), 기준 2026-11-04", unit="$", alt=[(H["tp"], "낙관")])
qs = ["3Q24", "4Q24", "1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"]
prev = {"3Q24": 558.2, "4Q24": 608.4, "1Q25": 634.3, "2Q25": 678.1, "3Q25": 725.5, "4Q25": 827.5, "1Q26": 883.9, "2Q26": 1003.7, "3Q26": 1181.1}
bar_chart(qs, [("매출($M)", [Q["revenue"][k] for k in qs], "#1F3864")], HERE / "full_q.png", "분기 매출($M)과 YoY 성장률 — 9분기 연속 가속",
          line=("YoY", [Q["revenue"][k] / prev[k] - 1 for k in qs]))
yrs = ["2024A", "2025A", "2026E"] + [f"{r['year']}E" for r in B["rows"][:4]]
revs = [A["revenue"]["2024"], A["revenue"]["2025"], R["rev26"]] + [r["rev"] for r in B["rows"][:4]]
fcfs = [A["cfo"]["2024"] - A["capex"]["2024"] - A["sbc"]["2024"], A["cfo"]["2025"] - A["capex"]["2025"] - A["sbc"]["2025"], R["rev26"] * R["m26"]] + [r["fcf"] for r in B["rows"][:4]]
bar_chart(yrs, [("매출($B)", [x / 1e3 for x in revs], "#1F3864"), ("FCF − 주식보상($B)", [x / 1e3 for x in fcfs], "#8FAADC")], HERE / "full_earn.png",
          "매출과 FCF − 주식보상($B) — 음영은 추정(기본)", est_from=2, line=("FCF−SBC 마진", [f / r for f, r in zip(fcfs, revs)]))
football_chart([("A. DCF (FCF − SBC)", L["va"], B["va"], H["va"]), ("B. 출구 배수 (2030E)", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 70 · B 30)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$", xlabel="주당 가치($) · 막대=보수~낙관, 점=기본")

SUB = f"3분기 매출 +96%, 가이던스 상향 — 그래도 현재가는 10년 매출 연 {R['implied']['cagr']*100:.0f}% 성장을 가정한다"
MKT = [["현재주가 (2026.11.04 종가)", f"${PRICE:,.2f}"], ["시가총액 (발행 24.10억주)", f"${R['mcap']/1e3:,.1f}B"], ["희석 주식수 (3Q26 가중평균)", f"{R['sh_dil']/1e3:.3f}B주"],
       ["52주 최고 / 최저 (장중)", f"${R['hi52']:,.2f} / ${R['lo52']:,.2f}"], ["순현금 (현금 + 유가증권, 무차입)", bn(R["net_cash"])],
       ["EV / 2026E 매출", f"{R['ev_rev26']:.1f}배"], [f"PER (TTM 희석 EPS ${T['eps_diluted']:.2f})", f"{R['per_ttm']:.0f}배"],
       ["PBR (3Q26 자본 $11.23B)", f"{R['pbr']:.1f}배"], ["3Q26 매출 성장률", "+96% YoY"], ["Rule of 40 (3Q26, 회사 발표)", "158"],
       ["원래 리포트 (2026.08.11)", f"{O['rating']} · ${O['tp']}"]]
ALT = [f"보수 ${L['tp']:,.0f} · 낙관 ${H['tp']:,.0f}"]

rp = Rep("소프트웨어 (Enterprise AI Platform)", "2026년 11월 5일")
rp.cover("팔란티어 테크놀로지스 (NASDAQ: PLTR)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, 단위: $M)")
r4 = B["rows"][:3]
rp.table([["항목 ($M)", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E", "2029E"],
          ["매출액", *[f0(A["revenue"][y]) for y in ("2023", "2024", "2025")], f0(R["rev26"])] + [f0(r["rev"]) for r in r4],
          ["매출 성장률", "+16.7%", pc(A["revenue"]["2024"] / A["revenue"]["2023"] - 1), pc(A["revenue"]["2025"] / A["revenue"]["2024"] - 1), pc(R["rev26"] / A["revenue"]["2025"] - 1)] + [pc(r["g"]) for r in r4],
          ["GAAP 영업이익", *[f0(A["gaap_op_income"][y]) for y in ("2023", "2024", "2025")], "-", "-", "-", "-"],
          ["GAAP 순이익", *[f0(A["net_income"][y]) for y in ("2023", "2024", "2025")], "-", "-", "-", "-"],
          ["주식보상 (SBC)", *[f0(A["sbc"][y]) for y in ("2023", "2024", "2025")], f0(R["sbc26"]), "-", "-", "-"],
          ["FCF − SBC", *[f0(A["cfo"][y] - A["capex"][y] - A["sbc"][y]) for y in ("2023", "2024", "2025")], f0(R["rev26"] * R["m26"])] + [f0(r["fcf"]) for r in r4],
          ["FCF − SBC 마진", *[pc((A["cfo"][y] - A["capex"][y] - A["sbc"][y]) / A["revenue"][y]) for y in ("2023", "2024", "2025")], pc(R["m26"])] + [pc(r["m"]) for r in r4]],
         [20, 11, 11, 11, 11, 12, 12, 12], hl_cols=(4, 5, 6, 7),
         note="자료: SEC 10-K FY2025, 10-Q 3Q26. 2026E 매출은 회사 가이던스 중간값($8.530~8.534B), FCF는 조정 FCF 가이던스 중간값 $4.9B에서 SBC를 뺀 값. 2027E 이후 본 리포트 추정.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", "3Q26 매출 +96%, 미국 상업 +148% — 미국 상업이 처음으로 미국 정부를 넘었다",
              [f"3Q26 매출 ${Q['revenue']['3Q26']/1e3:.3f}B(분기 첫 $2B 돌파): 미국 상업 ${PR['us_commercial']}M, 미국 정부 ${PR['us_government']}M(+96%)",
               f"2026 매출 가이던스 $8.150~8.158B → $8.530~8.534B(+91%), 조정 FCF $4.5~4.7B → $4.8~5.0B로 상향"])
rp.thesis_box("②", f"그러나 주식보상도 빨라졌다 — 3Q26 ${Q['sbc']['3Q26']:.0f}M(매출의 {Q['sbc']['3Q26']/Q['revenue']['3Q26']*100:.0f}%)",
              [f"SBC 최근 4분기 ${R['sbc_ttm']:,.0f}M로 원래 리포트 때($836M)보다 18% 늘었다. 희석 주식수는 발행주식보다 {(R['sh_dil']-R['sh_out']):.0f}백만주 많다",
               f"주주 입장의 현금흐름(조정 FCF − SBC)은 2026E 마진 {pc(R['m26'])}"])
rp.thesis_box("③", f"현재가는 10년 매출 연 {R['implied']['cagr']*100:.0f}% 성장을 가정한다 — 기본 추정은 {R['base_cagr']*100:.0f}%",
              [f"WACC {pc(R['wacc'],2)}(UST 10년 {pc(R['ust'],2)} + 베타 {R['beta']['blume']:.2f} × 5%)에서 현재가를 맞추려면 2035년 매출이 ${R['implied']['rev2035']/1e3:,.0f}B가 돼야 한다",
               "기본 추정(2027 +55% → 2035 +10%)도 소프트웨어 역사에서 드문 경로다. 그 위를 시장이 이미 사고 있다"])
rp.para(f"▶ 결론: 목표주가 ${TP:,}(A. DCF ${B['va']:,.0f} 70% · B. 출구 배수 ${B['vb']:,.0f} 30%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(08-11, {O['rating']} ${O['tp']}) 이후 실적과 가이던스는 더 좋아졌고, 주가는 10월 ${R['hi_since']:.0f}까지 올랐다가 실적 발표 뒤 ${PRICE:.0f}로 돌아왔다. "
        f"성장 경로를 20% 높이고 장기 마진 40%를 가정한 낙관도 ${H['tp']:,.0f}으로 현재가보다 낮다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.h2("1-1. 사업 소개")
rp.para("팔란티어(2003년 설립)는 데이터 통합·AI 소프트웨어 기업이다. 정부·정보기관용 Gotham, 기업용 Foundry, 배포 플랫폼 Apollo, 2023년 출시한 AI 플랫폼 AIP를 판다. "
        "2020년 9월 직상장했고 2024년 9월 S&P500에 편입됐다. 고객사 실제 데이터로 AI를 구현해 보이는 'AIP 부트캠프'로 시범 사용을 본계약으로 바꾸는 영업이 특징이다. "
        "3Q26 보도자료에서 회사는 '소버린 AI(Sovereign AI)'를 성장 동력으로 내세웠다.")
rp.h2("1-2. 3Q26 매출 구성")
rp.table([["구분", "3Q26 ($M)", "YoY", "비고"],
          ["미국 상업", f0(PR["us_commercial"]), "+148%", f"QoQ +29%. 미국 상업 잔여계약가치(RDV) ${PR['us_comm_rdv']/1e3:.2f}B(+79%)"],
          ["미국 정부", f0(PR["us_government"]), "+96%", "QoQ +18%"],
          ["미국 합계", f0(PR["us_revenue"]), "+119%", f"전체의 {PR['us_revenue']/Q['revenue']['3Q26']*100:.0f}%"],
          ["해외 (정부 + 상업)", f0(Q["revenue"]["3Q26"] - PR["us_revenue"]), "-", "미국보다 성장 낮음"],
          ["전체", f0(Q["revenue"]["3Q26"]), "+96%", f"TCV ${PR['tcv']/1e3:.2f}B(+6%), $1M 이상 계약 {PR['deals_1m']}건"]],
         [22, 14, 12, 52], hl_rows=(5,), note="자료: 8-K 3Q26 실적 보도자료(2026-11-02), 10-Q 3Q26.")
rp.h2("1-3. 주식 구조")
rp.table([["항목", "내용"], ["발행주식 (2026-10-26)", f"{R['sh_out']/1e3:.3f}B주 (Class A 2,306.7 · B 101.8 · F 1.0백만주)"],
          ["희석 주식 (3Q26 가중평균)", f"{R['sh_dil']/1e3:.3f}B주 — 주당가치 계산에 사용"],
          ["Class F", "창업진에게 이사회 통제에 준하는 의결권"]], [30, 70], note="자료: 10-Q 3Q26 표지.")

rp.h1("2. 실적 분석 (Performance Review)")
rp.h2("2-1. 3Q26 — 매출 +96%, GAAP 영업이익률 47%")
rp.kpi_tiles([("3Q26 매출", f"${Q['revenue']['3Q26']:,.0f}M", "+96% YoY"), ("GAAP 영업이익", f"${Q['gaap_op_income']['3Q26']:,.0f}M", "마진 47%"),
              ("조정 영업이익", f"${PR['adj_op_income']:,.0f}M", "마진 62%"), ("GAAP 순이익", f"${Q['net_income']['3Q26']:,.0f}M", "희석 EPS $0.44")])
rp.img(HERE / "full_q.png", W)
rp.para(f"분기 매출 YoY 성장률이 2024년 3분기 30%에서 2026년 3분기 96%까지 9분기 연속 올랐다. 4Q26 가이던스 매출 ${R['rev_4q']:,.0f}M은 전년 4분기보다 88% 많다. "
        f"GAAP 영업이익 ${Q['gaap_op_income']['3Q26']:,.0f}M과 조정 영업이익 ${PR['adj_op_income']:,.0f}M의 차이(${PR['adj_op_income']-Q['gaap_op_income']['3Q26']:,.0f}M)는 대부분 주식보상이다.")
rp.h2("2-2. 재무상태 — 무차입, 현금성 자산 $10.6B")
b = K["balance_2026_09_30"]; b0 = K["balance_2025_12_31"]
rp.table([["항목 ($M)", "2025-12-31", "2026-09-30"], ["현금", f0(b0["cash"]), f0(b["cash"])], ["유가증권", f0(b0["marketable_securities"]), f0(b["marketable_securities"])],
          ["자기자본", f0(b0["equity"]), f0(b["equity"])]], [40, 30, 30], note="자료: 10-Q 3Q26(2026-11-03 제출). 차입금 없음.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 성장의 질은 최상위 — Rule of 40 158")
rp.para(f"Rule of 40은 매출 성장률과 이익률의 합이 40을 넘으면 우량 소프트웨어로 본다. 회사 발표 3Q26 점수는 158이다. SEC 공시로 직접 계산한 최근 4분기 값도 "
        f"매출 성장 {pc(T['revenue']/T['revenue_prev']-1,0)} + FCF 마진 {pc(R['pltr_fcf_m'],0)} = 약 {R['pltr_r40']*100:.0f}로, 비교한 ServiceNow·Palo Alto(50~60)의 두 배를 넘는다.")
rp.h2("Thesis 2. 주주가 실제로 받는 현금은 '조정 FCF − 주식보상'")
rp.para(f"조정 FCF는 주식보상을 더한 값이다. 주식보상은 현금이 나가지 않지만 주식 수를 늘려 기존 주주 몫을 줄인다. 그래서 본 리포트는 FCF에서 SBC를 뺀 값으로 할인한다. "
        f"2026E 기준 {pc(R['m26'])}이며, 장기적으로 법인세가 정상화되면 35% 안팎으로 수렴한다고 본다(기본).")
rp.img(HERE / "full_earn.png", W)
rp.h2("Thesis 3. 가격이 가정하는 미래 — 역DCF")
rp.para(f"같은 WACC·마진에서 현재가 ${PRICE:,.2f}를 맞추려면 기본 성장 경로의 {R['implied']['gm']:.2f}배가 필요하다. 즉 2026~2035년 매출이 연 {R['implied']['cagr']*100:.0f}% 늘어 "
        f"2035년 ${R['implied']['rev2035']/1e3:,.0f}B가 돼야 한다(기본 ${B['rows'][-1]['rev']/1e3:,.0f}B). 현재 시가총액 ${R['mcap']/1e3:,.0f}B.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.para(f"2026E는 회사 가이던스 중간값. 2027E 성장률 55%는 4Q26 가이던스를 연환산만 해도 +{R['runrate_g']*100:.0f}%이고, 최근 분기 성장(QoQ +20%)이 분기 9% 수준으로 느려진다고 본 값이다. "
        "이후 40 → 30 → 25 → 20 → 17 → 14 → 12 → 10%(2035E). FCF − SBC 마진은 2026E에서 2035E 35%로 선형(세율 정상화). 회사는 다년 가이던스를 주지 않아 모두 본 리포트 가정이다.")
rows = [["항목 ($M, 기본)", "2026E"] + [f"{r['year']}E" for r in B["rows"][:5]],
        ["매출액", f0(R["rev26"])] + [f0(r["rev"]) for r in B["rows"][:5]],
        ["성장률", pc(R["rev26"] / A["revenue"]["2025"] - 1)] + [pc(r["g"]) for r in B["rows"][:5]],
        ["FCF − SBC 마진", pc(R["m26"])] + [pc(r["m"]) for r in B["rows"][:5]],
        ["FCF − SBC", f0(R["rev26"] * R["m26"])] + [f0(r["fcf"]) for r in B["rows"][:5]]]
rp.table(rows, [22, 13, 13, 13, 13, 13, 13], hl_rows=(4,))
rp.h2("시나리오별 핵심 가정")
rp.table([["가정", "보수", "기본", "낙관"], ["성장 경로 (기본 대비)", "× 0.8", "× 1.0", "× 1.2"],
          ["2035E FCF − SBC 마진", "30%", "35%", "40%"], ["2030E 매출 ($B)", *[f"{S[k]['r30']['rev']/1e3:,.1f}" for k in ("보수", "기본", "낙관")]],
          ["2035E 매출 ($B)", *[f"{S[k]['rows'][-1]['rev']/1e3:,.1f}" for k in ("보수", "기본", "낙관")]]], [34, 22, 22, 22])

rp.h1("5. 밸류에이션 (Valuation)")
rp.para("① DCF(FCF − SBC, 70%)와 ② 출구 배수법(30%)을 가중했다. ②는 성장률이 지금의 ServiceNow·Palo Alto 수준(20~25%)으로 내려올 2030E에, 두 회사가 오늘 받는 EV/(FCF − SBC) 배수를 "
        "적용해 그때의 기업가치를 구하고 할인한다. 증권사 목표주가·컨센서스는 쓰지 않는다.")
bt = R["beta"]
rp.h2("5-1. 할인율")
rp.table([["항목", "값", "근거"], ["무위험이자율", pc(R["ust"], 2), "미국채 10년, 2026-11-04"],
          ["베타", f"{bt['blume']:.2f}", f"주간 수익률 2년 SPY 대비 원베타 {bt['raw']:.2f} → Blume 조정"],
          ["주식위험프리미엄", "5.0%", "가정"], ["WACC", pc(R["wacc"], 2), "무차입 → 자기자본비용"]], [20, 12, 68],
         note="대형 소프트웨어 평균 베타(1.1~1.3)로 낮추면 WACC 10~11% — 5-4절 민감도에서 봐도 현재가에 못 미친다.")
rp.h2("5-2. B. 출구 배수 — 같은 날 피어")
pr = [["회사", "시가총액 ($B)", "매출 성장", "FCF 마진", "EV/매출", "EV/(FCF − SBC)"]]
for t, v in R["peers"].items():
    pr.append([f"{v['name']} ({t})", f"{v['mcap']/1e3:,.1f}", pc(v["g"]), pc(v["fcf_m"]), f"{v['ev_rev']:.1f}", f"{v['ev_fs']:.1f}"])
pr.append(["팔란티어 (현재가)", f"{R['mcap']/1e3:,.1f}", pc(T["revenue"] / T["revenue_prev"] - 1), pc(R["pltr_fcf_m"]), f"{R['ev']/T['revenue']:.1f}",
           f"{R['ev']/(T['cfo']-T['capex']-T['sbc']):.0f}"])
rp.table(pr, [26, 14, 14, 14, 14, 18], hl_rows=(3,),
         note=f"자료: SEC XBRL(최근 4분기), stock_db 11-04 종가. 출구 배수 = 두 회사 평균 {R['exit']:.1f}배.")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. DCF (FCF − SBC)", "70%", f"${L['va']:,.1f}", f"${B['va']:,.1f}", f"${H['va']:,.1f}"],
          ["B. 출구 배수 (2030E × {:.0f}배)".format(R["exit"]), "30%", f"${L['vb']:,.1f}", f"${B['vb']:,.1f}", f"${H['vb']:,.1f}"],
          ["목표주가", "", f"${L['tp']:,.0f}", f"${B['tp']:,.1f} → ${TP:,}", f"${H['tp']:,.0f}"],
          ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [30, 10, 20, 20, 20], hl_rows=(3,), note=f"A의 영구가치 비중 {B['tv']/(B['pv']+B['tv'])*100:.0f}%(기본). 투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-4. 민감도")
s = R["sens"]
rp.table([["장기 마진 × WACC"] + [pc(w, 1) for w in s["wacc"]]] + [[pc(m, 0)] + [f"${x:,.0f}" for x in row] for m, row in zip(s["m_t"], s["v"])],
         [20, 13, 13, 13, 13, 14, 14], note="목표주가($, A 70 · B 30, 기본 성장).")
s = R["sens_g"]
rp.table([["성장 경로 × WACC"] + [pc(w, 1) for w in s["wacc"]]] + [[f"× {g:.1f}"] + [f"${x:,.0f}" for x in row] for g, row in zip(s["gm"], s["v"])],
         [20, 13, 13, 13, 13, 14, 14], note="목표주가($, 장기 마진 35%). WACC 9~10%와 성장 1.5배가 함께 맞아야 현재가 근처에 온다.")

rp.h1("6. 리스크 분석 (Risk Analysis)")
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "성장 지속", "2027년에도 +60% 이상, 미국 상업 RDV 성장 유지", "성장 × 1.2 → 낙관"],
          ["상방", "할인율 하락", "대형주로 변동성이 줄어 베타가 1.3 수준으로", "WACC 11% → 민감도표"],
          ["하방", "성장 감속", "TCV 증가율이 +6%로 둔화 — 신규 계약이 매출 성장보다 느리다", "성장 × 0.8 → 보수"],
          ["하방", "정부 예산", "미국 정부 매출 41%(3Q26), 예산·정권 변수", "성장률·마진"],
          ["하방", "주식보상 희석", f"SBC 3Q26 매출의 {Q['sbc']['3Q26']/Q['revenue']['3Q26']*100:.0f}%, 최근 4분기 +18%", "FCF − SBC 마진"],
          ["하방", "경쟁", "프런티어 AI 랩·대형 클라우드의 기업용 AI 진출", "장기 마진"]], [8, 18, 50, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"], ["투자의견 / 목표주가", f"{RATING} / ${TP:,} (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본 ${TP:,} · 보수 ${L['tp']:,.0f} · 낙관 ${H['tp']:,.0f}"],
          ["재검토 조건", "① 4Q26 실적(가이던스 매출 $2.65B) ② 2027년 첫 가이던스(성장률 50% 이상인지) ③ TCV·SBC 추이"],
          ["결론", "실적은 원래 리포트 이후 더 좋아졌다. 그러나 현재가는 10년간 연 34% 성장이라는 전례 없는 경로를 이미 가격에 넣었고, 낙관 시나리오도 현재가에 못 미쳐 "
                   f"{RATING}. 실적이 아니라 가격이 문제라는 판단이다."]], [20, 80])

rp.since("8", "2026-08-11",
         [["항목", "원래 리포트 (2026-08-11)", "재조사 (2026-11-05)"],
          ["투자의견 / 목표주가", f"{O['rating']} / ${O['tp']}", f"{RATING} / ${TP:,} (기준주가 ${PRICE:,.2f})"],
          ["주가", f"${R['px_orig']:,.2f} (08-10 종가)", f"${PRICE:,.2f} ({R['chg_since']*100:+.1f}%, 사이 최고 ${R['hi_since']:.0f})"],
          ["평가 방법", O["method"], "A. DCF(FCF − SBC) 70 + B. 출구 배수 30"],
          ["2026 가이던스 (매출 / 조정 FCF)", f"${O['guide_rev'][0]/1e3:.3f}~{O['guide_rev'][1]/1e3:.3f}B / ${O['guide_fcf'][0]/1e3:.1f}~{O['guide_fcf'][1]/1e3:.1f}B",
           f"${K['press_release_3Q26']['guide_FY26']['revenue'][0]/1e3:.3f}~{K['press_release_3Q26']['guide_FY26']['revenue'][1]/1e3:.3f}B / $4.8~5.0B"],
          ["할인율", f"WACC {O['wacc']}", f"WACC {pc(R['wacc'],2)} (UST {pc(R['ust'],2)} + 실측 베타 {bt['blume']:.2f} × 5%)"],
          ["대안 시나리오", f"Bull ${O['bull']} / Bear ${O['bear']}", f"보수 ${L['tp']:,.0f} · 낙관 ${H['tp']:,.0f}"]],
         [f"3Q26 실적(11-02): 매출 ${Q['revenue']['3Q26']:,.0f}M(+96%), 미국 상업 +148%로 처음 미국 정부를 넘었다. GAAP 순이익 ${Q['net_income']['3Q26']:,.0f}M.",
          "2026 가이던스 상향: 매출 $8.15B → $8.53B, 조정 FCF $4.6B → $4.9B(중간값). 4Q26 매출 가이던스 $2.65B(+88%).",
          f"주식보상: 최근 4분기 $836M → ${R['sbc_ttm']:,.0f}M(+18%), 3Q26 매출의 {Q['sbc']['3Q26']/Q['revenue']['3Q26']*100:.0f}%.",
          f"신규 계약: 3Q26 TCV ${PR['tcv']/1e3:.2f}B로 +6% — 매출 성장(+96%)보다 크게 느리다.",
          f"주가: ${R['px_orig']:.2f} → 10-09 ${R['hi_since']:.0f}(사이 최고) → ${PRICE:.2f}. 미국채 10년 {O['ust']:.2f}% → {pc(R['ust'],2)}.",
          f"피어: ServiceNow 주가가 10-29 하루에 27% 내려 EV/(FCF − SBC)가 {R['peers']['NOW']['ev_fs']:.0f}배로 낮아졌다."],
         ["실적 변동이 커 증권사 컨센서스가 분기마다 크게 움직여, 목표가 산정은 회사 공시로 직접 계산하는 방법만 쓴다. 컨센서스와 정성 조정은 두지 않는다.",
          "조정 FCF와 주식보상이 함께 커져, 주주 현금흐름을 'FCF − SBC'로 보고 DCF(70%)를 중심에 둔다.",
          "EV/매출 배수 대신, 성장률이 성숙 피어 수준이 되는 2030E에 같은 날 피어의 EV/(FCF − SBC)를 적용하는 출구 배수법(30%)으로 바꿨다.",
          f"할인율은 기준일 미국채 10년과 실측 베타(2년 주간, Blume {bt['blume']:.2f})로 다시 계산했다. 2027E 성장률은 4Q26 가이던스를 반영해 55%로 둔다."],
         f"${O['tp']} → ${TP:,}. 가이던스 상향으로 2026E 매출과 FCF는 올랐지만, 컨센서스·정성 조정을 빼고 실측 베타 할인율과 주식보상 차감을 쓴 자체 방법으로 계산하면 "
         f"주당가치는 현재가보다 크게 낮다. 상승여력이 {UP*100:+.1f}%라 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K, XBRL companyfacts), 미국채 10년(yfinance ^TNX), 시세 DB(stock_db us_price)를 바탕으로 작성한 개인 분석 자료입니다.")
out = HERE / "팔란티어_리서치리포트_20261105.docx"
rp.doc.save(out); print(out); to_pdf(out)
