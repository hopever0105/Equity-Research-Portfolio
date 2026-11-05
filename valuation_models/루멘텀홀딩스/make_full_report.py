"""루멘텀홀딩스_리서치리포트_20261105.docx/.pdf — 2026-08-20 리포트를 2026-11-05 기준으로 다시 조사한 후속 리포트.
서식은 valuation/tools/report_kit.py. 입력: results.json(model.py), price_db.csv. 실행: python valuation/루멘텀홀딩스/make_full_report.py
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
K = R["key"]; A = K["annual"]; Q = K["quarterly"]; Q1 = Q["1Q FY27"]; M = K["merger"]; O = R["orig"]; G2 = K["guide_2Q_FY27"]
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
fs = lambda y: A["cfo"][y] - A["capex"][y] - A["sbc"][y]

px = pd.read_csv(HERE / "price_db.csv", parse_dates=["날짜"]).set_index("날짜")
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["pxdate"])]
price_chart(list(p2.index), list(p2["종가"]), TP, HERE / "full_price.png", "최근 2년 종가($), 기준 2026-11-04", unit="$",
            alt=[(R["deal"], "합병 가치"), (R["sa_base"], "단독 가치")])
qs = ["1Q FY26", "2Q FY26", "3Q FY26", "4Q FY26", "1Q FY27"]
bar_chart(qs, [("매출($M)", [Q["revenue"][q] for q in qs], "#1F3864")], HERE / "full_q.png",
          "분기 매출($M)과 Non-GAAP 영업이익률 — 5분기 연속 동반 상승", line=("Non-GAAP 영업이익률", [Q["nongaap_op_margin"][q] for q in qs]))
yrs = ["FY24", "FY25", "FY26"] + [f"FY{r['fy'] % 100}E" for r in B["rows"][:4]]
revs = [A["revenue"]["FY2024"], A["revenue"]["FY2025"], A["revenue"]["FY2026"]] + [r["rev"] for r in B["rows"][:4]]
bar_chart(yrs, [("매출($B)", [x / 1e3 for x in revs], "#1F3864")], HERE / "full_earn.png", "매출($B) — 음영은 추정(단독 기본)",
          est_from=3, line=("FCF - SBC 마진", [fs(y) / A["revenue"][y] for y in ("FY2024", "FY2025", "FY2026")] + [r["m"] for r in B["rows"][:4]]))
football_chart([("A. DCF (FCF - SBC)", L["va"], B["va"], H["va"]), ("B. 출구 배수 (FY2029E 매출)", L["vb"], B["vb"], H["vb"]),
                ("단독 가치 (A·B 50:50)", L["sa"], B["sa"], H["sa"]), ("합병 가치 (MRVL 4.5주)", R["deal"] * 120 / R["mrvl_px"], R["deal"], R["deal"] * 200 / R["mrvl_px"]),
                ("목표주가 (확률 가중)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$",
               xlabel="주당 가치($) · 막대=보수~낙관(합병 가치는 MRVL $120~200), 점=기본")

SUB = f"마벨이 주식 4.5주에 인수 — 주가는 이제 마벨 주가와 거래 완료 확률로 움직인다"
MKT = [["현재주가 (2026.11.04 종가)", f"${PRICE:,.2f}"], ["시가총액 (희석 1.009억주)", f"${R['mcap_dil']/1e3:,.1f}B"], ["발행주식 (10-28)", f"{R['sh_basic']:.1f}백만주"],
       ["52주 최고 / 최저 (장중)", f"${R['hi52']:,.2f} / ${R['lo52']:,.2f}"], ["현금 + 단기투자 (9월말)", f"${R['cash']/1e3:,.2f}B"],
       ["합병 조건", "LITE 1주 = MRVL 4.5주 (전액 주식)"], ["MRVL 종가 × 4.5", f"${R['mrvl_px']:.2f} × 4.5 = ${R['deal']:,.1f}"],
       ["합병 스프레드", f"{R['spread']*100:+.1f}%"], ["1Q FY27 매출 / Non-GAAP EPS", f"${Q1['nongaap_eps']:.2f} · ${Q['revenue']['1Q FY27']/1e3:.2f}B"],
       ["FY2027E EPS (자체) / PER", f"${R['eps27']:.2f} / {R['pe27']:.1f}배"], ["원래 리포트 (2026.08.20)", f"{O['rating']} · ${O['tp']:,}"]]
MKT[8] = ["1Q FY27 매출 / Non-GAAP EPS", f"${Q['revenue']['1Q FY27']/1e3:.2f}B / ${Q1['nongaap_eps']:.2f}"]
ALT = [f"보수 ${L['tp']:,.0f} · 낙관 ${H['tp']:,.0f}", f"단독 ${B['sa']:,.0f} · 합병 ${R['deal']:,.0f}"]

rp = Rep("광통신 (Photonics · 광부품)", "2026년 11월 5일")
rp.cover("루멘텀홀딩스 (NASDAQ: LITE)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, 회계연도 6월 말, 단위: $M)")
r3 = B["rows"][:3]
ng25, ng26 = A["nongaap"]["FY2025"], A["nongaap"]["FY2026"]
rp.table([["항목 ($M)", "FY2024", "FY2025", "FY2026", "FY2027E", "FY2028E", "FY2029E"],
          ["매출액", f0(A["revenue"]["FY2024"]), f0(A["revenue"]["FY2025"]), f0(A["revenue"]["FY2026"])] + [f0(r["rev"]) for r in r3],
          ["매출 성장률", pc(A["revenue"]["FY2024"] / A["revenue"]["FY2023"] - 1), pc(A["revenue"]["FY2025"] / A["revenue"]["FY2024"] - 1), pc(A["revenue"]["FY2026"] / A["revenue"]["FY2025"] - 1)] + [pc(r["g"]) for r in r3],
          ["GAAP 영업이익", f0(A["gaap_op_income"]["FY2024"]), f0(A["gaap_op_income"]["FY2025"]), f0(A["gaap_op_income"]["FY2026"]), "-", "-", "-"],
          ["Non-GAAP 영업이익률", "-", pc(ng25["op_margin"]), pc(ng26["op_margin"]), pc(R["opm27"]), "-", "-"],
          ["Non-GAAP EPS ($)", "-", f"{ng25['eps']:.2f}", f"{ng26['eps']:.2f}", f"{R['eps27']:.2f}", "-", "-"],
          ["FCF − SBC", f0(fs("FY2024")), f0(fs("FY2025")), f0(fs("FY2026"))] + [f0(r["fcf"]) for r in r3]],
         [22, 13, 13, 13, 13, 13, 13], hl_cols=(4, 5, 6),
         note="자료: SEC 10-K FY2026, 10-Q·8-K 1Q FY27. FY2027E는 1Q 실제 + 2Q 가이던스 중간 + 3Q·4Q 분기 +8%. FY2028E 이후 본 리포트 단독 추정.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", f"11-01 마벨과 합병계약 — LITE 1주당 MRVL 4.5주, 발표 당시 가치 ${M['implied_per_share_1028']:,}(+{M['premium_unaffected_1028']*100:.1f}%)",
              [f"전액 주식·고정 교환비율. 10-28 MRVL ${R['mrvl_1028']:.2f} 기준 주당 ${M['implied_per_share_1028']:,}, EV ${M['implied_ev_bn']}B. 완료 예상 2028년 상반기, 합병 후 LITE 주주 지분 33%",
               f"그 뒤 MRVL이 ${R['mrvl_px']:.2f}로 {R['mrvl_px']/R['mrvl_1028']-1:+.0%} 내려 합병 가치는 ${R['deal']:,.0f}. LITE 종가 ${PRICE:,.2f}는 그보다 {R['spread']*100:.1f}% 낮다"])
rp.thesis_box("②", f"실적은 원래 리포트 이후 더 좋아졌다 — 1Q FY27 매출 +{Q['revenue']['1Q FY27']/Q['revenue']['1Q FY26']*100-100:.0f}%, Non-GAAP 영업이익률 42.3%",
              [f"1Q 매출 ${Q['revenue']['1Q FY27']:,.1f}M(가이던스 $1.225~1.275B 상단 위), Non-GAAP EPS ${Q1['nongaap_eps']}. 2Q 가이던스 매출 $1.575~1.625B, 마진 45~46%",
               "두 번째 대형 NPO/CPO 수주(구매 약정 $5B 초과)와 OCS 수요 확대(보도자료)"])
rp.thesis_box("③", f"단독 가치 ${B['sa']:,.0f}와 합병 가치 ${R['deal']:,.0f}를 완료 확률 {B['p']*100:.0f}%로 가중",
              [f"단독: DCF ${B['va']:,.0f} · 피어 출구 배수 ${B['vb']:,.0f}(50:50). 합병: MRVL 종가 × 4.5. 규제로 무산되면 마벨이 $3.2B(주당 약 ${R['fee_reg_ps']:.0f})를 낸다",
               f"현재가는 기본 단독 가치 기준 완료 확률 약 {R['p_impl']*100:.0f}%만 반영한 값 — 시장은 마벨 주가 추가 하락과 규제 위험을 크게 본다"])
rp.para(f"▶ 결론: 목표주가 ${TP:,}({B['p']*100:.0f}% × 합병 가치 ${R['deal']:,.0f} + {100-B['p']*100:.0f}% × 단독 가치 ${B['sa']:,.0f}), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(08-20, {O['rating']} ${O['tp']:,}) 이후 실적은 더 좋아졌지만, 합병 발표로 주가는 마벨 주가에 묶였고 마벨이 10월 말 이후 크게 내리면서 LITE도 ${R['px_1028']:.0f}(10-28) → ${PRICE:.0f}로 내려왔다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.h2("1-1. 사업 소개")
rp.para("루멘텀(2015년 JDSU에서 분사, 캘리포니아 산호세)은 광통신·레이저 기업이다. 부품(Components) 부문은 데이터센터·통신용 레이저칩(EML 등)과 펌프 레이저, "
        "시스템(Systems) 부문은 광트랜시버 모듈(Cloud Light 인수), 광서킷스위치(OCS), 산업용 레이저를 판다. AI 데이터센터의 GPU 간 연결이 구리에서 광으로 바뀌면서 매출이 급증했다. "
        "회계연도는 6월 말에 끝난다(FY2027 1Q = 2026-06-28 ~ 2026-09-26).")
rp.h2("1-2. 마벨 합병계약 (2026-11-01 체결, 11-02 공시)")
rp.table([["항목", "내용"],
          ["구조", "마벨 자회사가 루멘텀을 흡수 → 루멘텀은 마벨 완전자회사. 전액 주식, 고정 교환비율 4.500"],
          ["가치 (발표 기준)", f"주당 약 ${M['implied_per_share_1028']:,} · EV ${M['implied_ev_bn']}B · 10-28(소문 전) 대비 프리미엄 {M['premium_unaffected_1028']*100:.1f}%"],
          ["합병 후 지분", "마벨 기존 주주 약 67%, 루멘텀 주주 약 33%(완전희석). 루멘텀 이사 3명(CEO 포함) 마벨 이사회 합류"],
          ["완료 조건 / 시점", f"{M['conditions']} / {M['close_expected']}"],
          ["해지 수수료", f"마벨→루멘텀 ${M['fee_marvell_to_lite']/1e3:.1f}B, 루멘텀→마벨 ${M['fee_lite_to_marvell']/1e3:.1f}B, 규제 무산 시 마벨→루멘텀 ${M['fee_regulatory_to_lite']/1e3:.1f}B"],
          ["시너지 (회사 발표)", f"{M['synergy_run_rate']}, 합병 후 첫해 마벨 Non-GAAP EPS 증가"],
          ["NVIDIA 우선주", M["preferred"]]],
         [22, 78], note="자료: 8-K(Item 1.01, 2026-11-02)와 Ex.99.1 공동 보도자료.")
rp.h2("1-3. 부문별 매출")
s1 = K["quarterly"]["1Q FY26 segments"]
rp.table([["부문 ($M)", "1Q FY26", "4Q FY26", "1Q FY27", "YoY"],
          ["부품 (Components)", f0(s1["components"]), "649", f"{Q1['components']:,.1f}", pc(Q1["components_yoy"])],
          ["시스템 (Systems)", f0(s1["systems"]), "357", f"{Q1['systems']:,.1f}", pc(Q1["systems_yoy"])],
          ["합계", f"{Q['revenue']['1Q FY26']:,.1f}", f"{Q['revenue']['4Q FY26']:,.1f}", f"{Q['revenue']['1Q FY27']:,.1f}", pc(Q['revenue']['1Q FY27'] / Q['revenue']['1Q FY26'] - 1)]],
         [24, 18, 18, 18, 22], hl_rows=(3,), note="자료: 8-K 1Q FY27 보도자료(2026-11-02).")

rp.h1("2. 실적 분석 (Performance Review)")
rp.h2("2-1. 1Q FY27 — 매출 +137%, Non-GAAP EPS $4.57")
rp.kpi_tiles([("1Q FY27 매출", f"${Q['revenue']['1Q FY27']:,.1f}M", f"QoQ +{Q['revenue']['1Q FY27']/Q['revenue']['4Q FY26']*100-100:.1f}%"),
              ("Non-GAAP 영업이익률", "42.3%", "4Q 36.6%"), ("Non-GAAP EPS", f"${Q1['nongaap_eps']}", f"GAAP ${Q1['eps_diluted']}"),
              ("2Q 가이던스 매출", "$1.575~1.625B", "마진 45~46%")])
rp.img(HERE / "full_q.png", W)
rp.para(f"5개 분기 연속으로 매출과 Non-GAAP 영업이익률이 함께 올랐다. GAAP 총이익률은 4Q 47.4% → 1Q 51.0%. 부품은 펌프 레이저가, 시스템은 OCS가 성장을 이끌었다. "
        f"다만 1Q 현금은 ${R['cash']/1e3:.2f}B로 4Q보다 $0.76B 줄었다(설비투자 ${Q1['capex']:.0f}M, 전환사채 상환 등).")
rp.h2("2-2. 현금흐름 — 설비투자가 매출의 18%")
rp.table([["항목 ($M)", "FY2024", "FY2025", "FY2026", "1Q FY27"], ["영업현금흐름", f0(A["cfo"]["FY2024"]), f0(A["cfo"]["FY2025"]), f0(A["cfo"]["FY2026"]), f0(Q1["cfo"])],
          ["설비투자", f0(A["capex"]["FY2024"]), f0(A["capex"]["FY2025"]), f0(A["capex"]["FY2026"]), f0(Q1["capex"])],
          ["주식보상", f0(A["sbc"]["FY2024"]), f0(A["sbc"]["FY2025"]), f0(A["sbc"]["FY2026"]), f0(Q1["sbc"])],
          ["FCF − SBC", f0(fs("FY2024")), f0(fs("FY2025")), f0(fs("FY2026")), f0(Q1["cfo"] - Q1["capex"] - Q1["sbc"])]], [30, 17, 17, 17, 19],
         note="자료: 10-K FY2026, 10-Q 1Q FY27. 1Q 주식보상은 $135M로 FY2026 연간($170M)의 80%에 이른다.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 고정 교환비율 — LITE 주가는 'MRVL × 4.5 − 스프레드'")
rp.para(f"교환비율이 고정이라 합병이 끝날 때 LITE 주주가 받는 것은 마벨 주식 4.5주다. 발표 당시(10-28 기준) 주당 ${M['implied_per_share_1028']:,}이던 가치는 MRVL이 ${R['mrvl_1028']:.0f} → ${R['mrvl_px']:.0f}로 내리면서 "
        f"${R['deal']:,.0f}가 됐다. LITE는 그보다 {R['spread']*100:.1f}% 낮게 거래된다. 완료까지 약 1.5년, 양사 주주총회와 규제 승인(HSR, 그 밖의 관할)이 남아 있어 스프레드가 크다.")
rp.h2("Thesis 2. 단독으로도 실적은 최상급 — 그러나 사이클 산업")
rp.para(f"1Q 실제와 2Q 가이던스를 이어 분기 8%씩 늘면 FY2027E 매출 ${R['rev27']/1e3:,.2f}B, Non-GAAP EPS 약 ${R['eps27']:.2f}(PER {R['pe27']:.1f}배)다. "
        f"FY2028E 매출은 4Q 연환산과 대형 NPO/CPO 수주를 감안해 ${R['rev28']/1e3:.1f}B로 둔다. FY2023 $1.77B → FY2024 $1.36B(−23%)처럼 재고조정만으로 매출이 줄 수 있어, "
        "FCF − SBC 마진은 FY27 20%(신규 팹 투자) → FY28 26% → 장기 24%(사이클 평균)로 둔다.")
rp.img(HERE / "full_earn.png", W)
rp.h2("Thesis 3. 피어 배수는 내렸다 — EV/매출 중앙값 10.7배")
pr = [["회사 (2026-11-04)", "종가 ($)", "시가총액 ($B)", "최근 분기 성장", "FCF 마진", "EV/매출"]]
for t, v in R["peers"].items():
    pr.append([f"{v['name']} ({t})", f"{v['price']:,.2f}", f"{v['mcap']/1e3:,.1f}", pc(v["g"]), pc(v["fcf_m"]), f"{v['ev_rev']:.1f}"])
pr.append(["루멘텀 (희석, TTM)", f"{PRICE:,.2f}", f"{R['mcap_dil']/1e3:,.1f}", pc(Q['revenue']['1Q FY27'] / Q['revenue']['1Q FY26'] - 1), "-", f"{R['ev']/R['ttm_rev']:.1f}"])
rp.table(pr, [26, 13, 14, 15, 14, 14], hl_rows=(5,), note=f"자료: SEC XBRL(최근 4분기), stock_db 11-04 종가. 중앙값 EV/매출 {R['exit']:.1f}배 — B의 출구 배수.")
rp.para("광통신 피어 주가가 10월 말 이후 일제히 내렸다(Coherent·Ciena·Marvell 10-28 대비 −19~−37%). 원래 리포트 때보다 업종 배수가 낮아져 B(출구 배수) 값도 낮아졌다.")

rp.h1("4. 실적 추정 (Earnings Forecast, 단독)")
rp.table([["FY2027E 분기 ($M)", "1Q (실제)", "2Q (가이던스)", "3Q", "4Q", "FY2027E"],
          ["매출", *[f0(x) for x in R["q27"]], f0(R["rev27"])], ["QoQ", f"+{R['q27'][0]/Q['revenue']['4Q FY26']*100-100:.0f}%", f"+{R['q27'][1]/R['q27'][0]*100-100:.0f}%", f"+{R['qg']*100:.0f}%", f"+{R['qg']*100:.0f}%", f"{R['rev27']/R['rev26']-1:+.0%} YoY"]],
         [24, 14, 14, 14, 14, 20], note="2Q는 가이던스 중간값($1.575~1.625B), 3Q·4Q는 분기 +8%로 감속.")
rows = [["항목 ($M, 기본)"] + [f"FY{r['fy']}E" for r in B["rows"][:6]],
        ["매출액"] + [f0(r["rev"]) for r in B["rows"][:6]], ["성장률"] + [pc(r["g"]) for r in B["rows"][:6]],
        ["FCF − SBC 마진"] + [pc(r["m"]) for r in B["rows"][:6]], ["FCF − SBC"] + [f0(r["fcf"]) for r in B["rows"][:6]]]
rp.table(rows, [22, 13, 13, 13, 13, 13, 13], hl_rows=(4,), note="FY2029E 이후 성장률 20·15·12·10·8·6·5·4%(FY2036E).")
rp.h2("시나리오별 핵심 가정")
rp.table([["가정", "보수", "기본", "낙관"], ["FY2028E 매출", "$7.5B", "$9.0B", "$10.5B"], ["FY2029E 이후 성장 (기본 대비)", "× 0.8", "× 1.0", "× 1.2"],
          ["장기 FCF − SBC 마진", "20%", "24%", "28%"], ["합병 완료 확률", "60%", "75%", "90%"],
          ["단독 가치 ($)", *[f0(S[k]["sa"]) for k in ("보수", "기본", "낙관")]]], [34, 22, 22, 22])

rp.h1("5. 밸류에이션 (Valuation)")
rp.para("합병계약이 체결돼 가치를 두 갈래로 계산한다. ① 단독 가치: DCF(FCF − SBC, FY2027~FY2036 + 영구성장 3%)와 FY2029E 매출 × 피어 4사 EV/매출 중앙값의 50:50. "
        "② 합병 가치: 마벨 주식 4.5주 × 마벨 11-04 종가. 목표주가는 완료 확률로 둘을 가중한다. 마벨 주가는 합병 대가 자체라 쓰지만, 마벨의 적정가는 따로 평가하지 않았다(마벨 주가 민감도로 대신). "
        "증권사 목표주가·컨센서스는 쓰지 않는다.")
bt = R["beta"]
rp.h2("5-1. 할인율")
rp.table([["항목", "값", "근거"], ["무위험이자율", pc(R["ust"], 2), "미국채 10년, 2026-11-04"],
          ["베타", f"{bt['blume']:.2f}", f"주간 수익률 2년 SPY 대비 원베타 {bt['raw']:.2f} → Blume 조정"], ["주식위험프리미엄", "5.0%", "가정"],
          ["WACC", pc(R["wacc"], 2), "순현금(전환사채는 희석 주식에 포함)"]], [20, 12, 68])
rp.h2("5-2. 종합 목표주가")
rp.table([["방법", "가중", "보수", "기본", "낙관"],
          ["A. DCF (FCF − SBC)", "단독 50%", f"${L['va']:,.0f}", f"${B['va']:,.0f}", f"${H['va']:,.0f}"],
          [f"B. 출구 배수 (FY29E × {R['exit']:.1f}배)", "단독 50%", f"${L['vb']:,.0f}", f"${B['vb']:,.0f}", f"${H['vb']:,.0f}"],
          ["단독 가치", "1 − p", f"${L['sa']:,.0f}", f"${B['sa']:,.0f}", f"${H['sa']:,.0f}"],
          ["합병 가치 (MRVL × 4.5)", "p", f"${R['deal']:,.0f}", f"${R['deal']:,.0f}", f"${R['deal']:,.0f}"],
          ["완료 확률 p", "", "60%", "75%", "90%"],
          ["목표주가", "", f"${L['tp']:,.0f}", f"${B['tp']:,.0f} → ${TP:,}", f"${H['tp']:,.0f}"], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [32, 12, 18, 20, 18], hl_rows=(6,), note=f"A의 영구가치 비중 {B['tv']/(B['pv']+B['tv'])*100:.0f}%(기본). 투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-3. 민감도")
s = R["sens"]
rp.table([["완료 확률 × MRVL 주가"] + [f"${m:,.0f}" for m in s["mrvl"]]] + [[pc(p, 0)] + [f"${x:,.0f}" for x in row] for p, row in zip(s["p"], s["v"])],
         [24, 15, 15, 15, 15, 16], note=f"목표주가($), 단독 가치 기본 ${B['sa']:,.0f} 고정. MRVL이 $140 아래로 가면 합병 가치가 단독 가치와 비슷해진다.")
s = R["sens_sa"]
rp.table([["장기 마진 × WACC (단독 가치)"] + [pc(w, 1) for w in s["wacc"]]] + [[pc(m, 0)] + [f"${x:,.0f}" for x in row] for m, row in zip(s["m_t"], s["v"])],
         [28, 18, 18, 18, 18], note="단독 가치($), FY2028E 매출 $9.0B.")

rp.h1("6. 리스크 분석 (Risk Analysis)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["하방", "마벨 주가 하락", "고정 교환비율이라 MRVL 1달러에 LITE 합병 가치 4.5달러", "민감도표"],
          ["하방", "규제·주주 승인", "HSR 등 규제 승인과 양사 주주총회, 완료까지 약 1.5년", f"무산 시 단독 가치 + 규제 해지 수수료 주당 약 ${R['fee_reg_ps']:.0f}"],
          ["하방", "AI 투자 사이클 둔화", "하이퍼스케일러 설비투자 조정 시 재고조정(FY2024 −23% 전례)", "단독 가치 하향"],
          ["상방", "실적 가속", "2Q 가이던스(+25% QoQ) 상회, NPO/CPO·OCS 매출화", "단독 가치·MRVL 동반 상향"],
          ["상방", "스프레드 축소", "규제 승인 진전 시 스프레드 14.7% → 축소", "현재가 → 합병 가치"]], [8, 18, 46, 28])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"], ["투자의견 / 목표주가", f"{RATING} / ${TP:,} (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본 ${TP:,} · 보수 ${L['tp']:,.0f} · 낙관 ${H['tp']:,.0f} · 단독 ${B['sa']:,.0f} · 합병 ${R['deal']:,.0f}"],
          ["재검토 조건", "① S-4 제출과 양사 주주총회 일정 ② HSR 등 규제 심사 진행 ③ 마벨 주가와 2Q FY27 실적"],
          ["결론", f"실적은 원래 리포트 이후 더 좋아졌지만, 이제 주가를 정하는 것은 마벨 주가와 거래 완료 가능성이다. 완료 확률 {B['p']*100:.0f}%로 가중한 가치가 현재가보다 {UP*100:.0f}% 높아 {RATING}. "
                   "규제 승인이 진전되면 스프레드 축소로 상향, 마벨 주가가 더 내리면 하향한다."]], [20, 80])

rp.since("8", "2026-08-20",
         [["항목", "원래 리포트 (2026-08-20)", "재조사 (2026-11-05)"],
          ["투자의견 / 목표주가", f"{O['rating']} / ${O['tp']:,}", f"{RATING} / ${TP:,} (기준주가 ${PRICE:,.2f})"],
          ["주가", f"${R['px_orig']:,.2f} (08-19 종가)", f"${PRICE:,.2f} ({R['chg_since']*100:+.1f}%, 10-28 ${R['px_1028']:,.0f})"],
          ["평가 방법", O["method"], "단독 가치(DCF 50 + 피어 출구 배수 50)와 합병 가치(MRVL × 4.5)를 완료 확률로 가중"],
          ["이익 추정", O["earn"], f"FY27E 매출 ${R['rev27']/1e3:.2f}B(1Q 실제 + 2Q 가이던스), EPS ${R['eps27']:.2f}"],
          ["기업 상황", "독립 상장사", "마벨 합병계약 체결(11-01), 완료 예상 2028년 상반기"],
          ["대안 시나리오", f"Bull ${O['bull']:,} / Bear ${O['bear']}", f"보수 ${L['tp']:,.0f} · 낙관 ${H['tp']:,.0f}"]],
         [f"합병: 11-01 마벨과 전액 주식 합병계약(LITE 1주 = MRVL 4.5주). 발표 가치 주당 ${M['implied_per_share_1028']:,}, 10-28 대비 프리미엄 23.9%, 완료 예상 2028년 상반기.",
          f"마벨 주가: 10-28 ${R['mrvl_1028']:.2f} → 11-04 ${R['mrvl_px']:.2f}({R['mrvl_px']/R['mrvl_1028']-1:+.0%}). 합병 가치가 ${R['deal']:,.0f}로 낮아졌고 LITE는 그보다 {R['spread']*100:.1f}% 아래에서 거래.",
          f"실적: 1Q FY27 매출 ${Q['revenue']['1Q FY27']:,.1f}M(+137%), Non-GAAP 영업이익률 42.3%, EPS $4.57 — 원래 리포트 때 1Q 가이던스(매출 $1.225~1.275B, EPS $4.05~4.35)를 넘었다.",
          "2Q FY27 가이던스: 매출 $1.575~1.625B, Non-GAAP 영업이익률 45~46%, EPS $5.90~6.20. 두 번째 대형 NPO/CPO 수주(구매 약정 $5B 초과).",
          "광통신 피어: Coherent·Ciena·Marvell이 10-28 대비 19~37% 하락, 피어 EV/매출 중앙값이 내려갔다.",
          f"금리: 미국채 10년 {O['ust']:.2f}% → {pc(R['ust'],2)}."],
         ["합병계약 체결로 주가가 마벨 주가에 묶여, 목표가를 '단독 가치'와 '합병 가치(MRVL × 4.5)'의 완료 확률 가중으로 바꿨다.",
          "단독 가치는 회사 공시로 직접 계산한다: DCF(FCF − SBC)와 FY2029E 매출 × 같은 날 피어 EV/매출 중앙값 50:50. 증권사 목표가는 합병 발표 뒤 의미가 바뀌어 쓰지 않는다.",
          "1Q 실적과 2Q 가이던스가 나와 FY2027E를 분기 실제·가이던스로 다시 쌓고, FY2028E 매출을 $9.0B로 올렸다. 장기 마진은 이익률 상승을 반영해 24%로 둔다.",
          "할인율은 기준일 미국채 10년과 실측 베타(2년 주간, Blume)로 다시 계산했다."],
         f"${O['tp']:,} → ${TP:,}. 실적과 FY2028E 매출 상향은 단독 가치를 올렸지만, 합병으로 가치의 대부분이 마벨 주식 4.5주에 묶였고 마벨 주가가 10월 말 이후 37% 내리면서 합병 가치가 ${R['deal']:,.0f}로 낮아졌다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K, XBRL companyfacts), 미국채 10년(yfinance ^TNX), 시세 DB(stock_db us_price)를 바탕으로 작성한 개인 분석 자료입니다.")
out = HERE / "루멘텀홀딩스_리서치리포트_20261105.docx"
rp.doc.save(out); print(out); to_pdf(out)
