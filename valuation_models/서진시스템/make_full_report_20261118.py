"""서진시스템_리서치리포트_20261118.docx/.pdf — 2026-08-24 리포트를 2026-11-18 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_fdr.csv. 실행: python valuation/서진시스템/make_full_report_20261118.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools.report_kit import Rep, to_pdf, price_chart, football_chart, bar_chart, line_band_chart, W

R = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
S = R["scen"]; B, L, H = S["기본"], S["보수"], S["낙관"]
PRICE, TP, UP, RATING, O = R["price"], R["tp"], R["upside"], R["rating"], R["orig"]
HI, Q, SA, BY = R["hist"], R["q"], R["scen_assump"], R["buy"]
FB = B["f"]; WA, WB = R["w"]
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
YRS = ["2022", "2023", "2024", "2025"]
TAG = "20261118"
q3, q3p = Q["20263Q"], Q["20253Q"]
QI = R["q3_items"]; SG, SG25 = R["seg_9m"], R["seg_25"]; BL = R["bloom"]

px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / f"full_price_{TAG}.png", "최근 2년 종가(원), 기준일 2026-11-18", alt=[(H["tp"], "낙관")])
pb = pd.Series(R["pband"]["series"]); pb.index = pd.to_datetime(pb.index)
line_band_chart(list(pb.index), list(pb.values), R["pband"]["mean"], R["pband"]["sd"], HERE / f"full_band_{TAG}.png",
                f"서진시스템 PBR 밴드(월말 종가 ÷ 공시된 지배 BPS, 현재 주식수 기준 근사) — 중앙값 {R['pband']['median']:.1f}배", "PBR(배)")
ql = ["20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q"]
bar_chart(["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"],
          [("영업이익", [Q[k]["op"] for k in ql], "#1F3864"), ("세전이익", [Q[k]["pti"] for k in ql], "#8FAADC"), ("지배순이익", [Q[k]["ni"] for k in ql], "#C00000")],
          HERE / f"full_q_{TAG}.png", "분기 영업이익·세전이익·순이익(억원) — 영업은 흑자, 환율·이자·중단사업으로 순손실", ylab="억원")
bar_chart(["반도체장비", "ESS", "통신"], [("2025년 연간", [SG25["semi"], SG25["ess"], SG25["tel"]], "#8FAADC"), ("2026년 9개월", [SG["semi"], SG["ess"], SG["tel"]], "#1F3864")],
          HERE / f"full_seg_{TAG}.png", "부문별 매출(억원)", ylab="억원", figsize=(7.2, 2.0))
football_chart([("A. EV/EBITDA (2027E × 배수 − 순차입)", L["va"], B["va"], H["va"]), ("B. PBR (2027E BPS × 밴드)", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 60 · B 40)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / f"full_football_{TAG}.png")

SUB = f"3분기 영업흑자 전환, 그러나 차입 1.3조와 전환사채 3,200억 — BUY가 되려면 EV/EBITDA {BY['need_mult']:.1f}배가 필요하다"
MKT = [["현재주가 (2026.11.18 종가)", f"{PRICE:,.0f}원"], ["시가총액 (9월 말 주식수)", f"{R['mcap']/1e4:.1f}조원"],
       ["유통주식 / 완전희석", f"{R['sh']:,} / {R['sh_fd']:,}주"], ["52주 최고 / 최저 (장중)", f"{R['hi52']:,.0f} / {R['lo52']:,.0f}원"],
       ["EV / 2027E EBITDA", f"{R['eve_27_now']:.1f}배"], ["PBR (9월 말 지배자본)", f"{R['pbr']:.1f}배"],
       ["9M26 매출 / 영업이익", f"{f0(R['m9']['매출'])}억 / {f0(R['m9']['영업이익'])}억"], ["차입금 / 현금 (9월 말)", f"{f0(R['debt_3q'])}억 / {f0(R['cash'])}억"],
       ["전환사채 (8·11월)", "3,200억 (전환가 30,391~36,950원)"], ["원래 리포트 (2026.08.24)", f"{O['rating']} · {O['tp']:,}원"]]
ALT = [f"보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"]

rp = Rep("ESS·반도체 장비 부품 (EMS)", "2026년 11월 18일")
rp.cover("서진시스템 (178320 KS)", SUB, RATING, TP, PRICE, UP, "원", HERE / f"full_price_{TAG}.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, 연결 기준)")
rows = [["항목 (억원)", "2022A", "2023A", "2024A", "2025A", "2026E", "2027E"],
        ["매출액"] + [f0(HI[y]["rev"]) for y in YRS] + [f0(FB["rev26"]), f0(FB["rev27"])],
        ["영업이익"] + [f0(HI[y]["op"]) for y in YRS] + [f0(FB["op26"]), f0(FB["op27"])],
        ["EBITDA"] + ["-"] * 4 + ["-", f0(FB["ebitda27"])],
        ["지배주주 순이익"] + [f0(HI[y]["ni"]) for y in YRS] + ["-", f0(FB["ni27"])]]
rp.table(rows, [24, 12, 12, 12, 12, 14, 14], hl_cols=(5, 6),
         note=f"자료: DART 연결재무제표(계속사업 기준으로 재작성된 2026년 분기 포함). 2027E 영업이익 = EBITDA − 감가상각 {f0(R['da27'])}억(3Q26 × 4), 순이익 = (영업이익 − 이자 {f0(R['int27'])}억) × (1 − 20%). 2026E 순이익은 환율 손익 불확실로 표시하지 않음.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", "영업은 살아났다 — 3Q26 영업이익 387억, 매출 +196%",
              [f"9M26 반도체장비 매출 {f0(SG['semi'])}억(2025년 연간 {f0(SG25['semi'])}억의 {SG['semi']/SG25['semi']:.1f}배), ESS 수출 {f0(SG['ess_exp'])}억(2025년 연간 {f0(SG25['ess_exp'])}억)",
               f"Bloom Energy 연료전지(SOFC) 모듈·부품 공급계약 {f0(BL['amt'])}억({BL['start']} ~ {BL['end']}), 2025년 매출의 {BL['pct_rev25']:.0f}%"])
rp.thesis_box("②", f"하지만 순이익은 3Q26 {f0(q3['ni'])}억 적자 — 환율·이자·중단사업",
              [f"외화환산손실 {f0(QI['fx_trans'])}억 + 외환차손 {f0(QI['fx_diff'])}억, 이자비용 {f0(QI['interest'])}억, 베트남 일부 사업 중단손실 {f0(-QI['disc'])}억",
               f"차입금 {f0(R['debt_3q'])}억(단기 {f0(R['debt']['short'])}억), 현금 {f0(R['cash'])}억. 8·11월 전환사채 3,200억으로 주식이 최대 약 15% 늘 수 있다"])
rp.thesis_box("③", f"목표주가 {TP:,}원, {RATING} — 빚이 커서 배수 하나에 주가가 크게 움직인다",
              [f"2027E EBITDA {f0(FB['ebitda27'])}억 × 8배 − 순차입 {f0(R['net_debt'])}억 = {B['va']:,.0f}원, PBR {B['pbr']:.1f}배 {B['vb']:,.0f}원",
               f"BUY(+15%)에는 EV/EBITDA {BY['need_mult']:.1f}배(피어 중앙 {BY['peer_eve_med']:.1f}배) 또는 2027 EBITDA {f0(BY['need_ebitda27'])}억이 필요하다(6장)"])
rp.para(f"▶ 결론: 목표주가 {TP:,}원(A 60% · B 40%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. 원래 리포트(08-24, {O['rating']} {O['tp']:,}원) 이후 영업은 흑자로 돌아섰지만, "
        "차입과 전환사채가 늘면서 주주 몫의 가치가 줄었다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.h2("1-1. 사업 소개")
rp.para("서진시스템(178320)은 베트남 생산 기반의 금속 가공·조립 전문 기업으로, ESS(에너지저장장치) 함체·모듈, 반도체 장비 부품·모듈, 통신 장비를 만든다. "
        "고객이 설계한 제품을 대신 만들어 납품하는 구조라 고객 발주에 따라 매출이 크게 움직인다.")
rp.img(HERE / f"full_seg_{TAG}.png", W)
rp.h2("1-2. 원래 리포트 이후 주요 공시")
rp.table([["날짜", "공시", "내용"],
          ["2026-08-24", "전환사채 발행 (4건)", "39~42회 2,000억, 그중 1,000억은 자본으로 인정되는 영구형"],
          ["2026-09-30", "사업 일부 중단", "베트남 법인 생활가전·공작기계·중공업·휠 부문 중단(이 부문 2025년 매출 942억)"],
          ["2026-10-12", "단일판매·공급계약", f"Bloom Energy SOFC 모듈·부품 {f0(BL['amt'])}억, {BL['start']} ~ {BL['end']}"],
          ["2026-11-06·09", "전환사채 발행 (2건)·정정", "44~45회 1,200억, 그중 600억 영구형"],
          ["2026-11-13", "3Q26 분기보고서", f"영업이익 {f0(q3['op'])}억, 지배순이익 {f0(q3['ni'])}억(중단영업 손실 포함)"]],
         [14, 22, 64], note="자료: DART. 이 밖에 최대주주 주식담보 계약 정정 공시가 8~11월 여러 번 있었다.")
rp.h2("1-3. 주식 수")
rp.para(f"기초 {R['sh_begin']:,}주 → 9월 말 {R['sh']:,}주(전환사채 전환·신주인수권 행사 등). 8·11월 전환사채가 모두 전환되면 약 {R['cb_shares']:,}주가 더해져 완전희석 {R['sh_fd']:,}주다. "
        "목표가는 완전희석 주식수로 계산했다.")

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("3Q26 매출", f"{f0(q3['rev'])}억", f"{q3['rev']/q3p['rev']-1:+.0%} YoY"),
              ("3Q26 영업이익", f"{f0(q3['op'])}억", f"영업이익률 {q3['op']/q3['rev']*100:.1f}%"),
              ("3Q26 EBITDA", f"{f0(BY['ebitda_q3'])}억", f"감가상각 {f0(QI['da'])}억 포함"),
              ("3Q26 지배순이익", f"{f0(q3['ni'])}억", f"중단영업 {f0(QI['disc'])}억")])
rp.img(HERE / f"full_q_{TAG}.png", W)
rp.para(f"영업이익은 1Q26 {f0(Q['20261Q']['op'])}억 → 2Q26 {f0(Q['20262Q']['op'])}억 → 3Q26 {f0(q3['op'])}억으로 흑자 전환했다. 그러나 세전이익은 3Q26 {f0(q3['pti'])}억으로, "
        f"원/달러 변동에 따른 외화환산손실 {f0(QI['fx_trans'])}억과 이자비용 {f0(QI['interest'])}억이 영업이익을 넘어섰다. 여기에 사업 중단 손실 {f0(-QI['disc'])}억이 더해져 순손실이 커졌다.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 성장 사업은 분명하다")
rp.para(f"반도체장비 부품은 9개월 만에 2025년 연간의 {SG['semi']/SG25['semi']:.1f}배를 팔았고, ESS 수출이 새로 생겼다. Bloom Energy 계약은 연료전지라는 새 고객군이다. "
        f"기본 시나리오는 2027년 매출 {f0(FB['rev27'])}억, EBITDA {f0(FB['ebitda27'])}억(3Q26 EBITDA {f0(BY['ebitda_q3'])}억 × 4 + Bloom 계약)이다.")
rp.h2("Thesis 2. 빚이 주주 몫을 줄인다")
rp.img(HERE / f"full_band_{TAG}.png", W)
rp.para(f"차입금 {f0(R['debt_3q'])}억 중 단기·유동성 장기가 {f0(R['debt']['short'] + R['debt']['current_lt'])}억이다. 이자만 분기 {f0(QI['interest'])}억이고, 달러 차입·자산이 섞여 환율이 움직일 때마다 손익이 흔들린다. "
        f"전환사채는 전환가(30,391~36,950원)가 지금 주가 근처라, 주가가 오르면 주식 수가 늘어 주당 가치가 희석된다.")
rp.h2("Thesis 3. 피어와의 비교")
rp.table([["피어 (TTM 2Q26)", "PBR", "EV/EBITDA", "EV/매출", "영업이익률"]] +
         [[p["name"], f"{p['PBR']:.1f}배", f"{p['EV/EBITDA']:.1f}배", f"{p['EV/Sales']:.1f}배", pc(p["OPM"], 0)] for p in R["peer"]],
         [28, 18, 18, 18, 18], note=f"tools/peers.py(stock_db 재무, 2Q26까지 4개 분기 합). 중앙값 EV/EBITDA {R['peer_eve_med']:.1f}배. 목표 8배는 ESS·반도체 부품 성장을 반영해 피어보다 높게 잡았다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.table([["가정", "보수", "기본", "낙관"],
          ["4Q26 매출 / 영업이익률", *[f"{f0(SA[k]['q4'])}억 / {pc(SA[k]['q4m'],1)}" for k in ("보수", "기본", "낙관")]],
          ["2027 매출", *[f"{f0(SA[k]['rev27'])}억" for k in ("보수", "기본", "낙관")]],
          ["2027 EBITDA", *[f"{f0(SA[k]['ebitda27'])}억" for k in ("보수", "기본", "낙관")]],
          ["2027 순이익", *[f"{f0(S[k]['f']['ni27'])}억" for k in ("보수", "기본", "낙관")]],
          ["목표 EV/EBITDA", *[f"{SA[k]['mult']:.0f}배" for k in ("보수", "기본", "낙관")]],
          ["목표 PBR (밴드)", f"{L['pbr']:.2f}배 (하위 25%)", f"{B['pbr']:.2f}배 (중앙)", f"{H['pbr']:.2f}배 (상위 25%)"]],
         [30, 23, 23, 24], note=f"2027E 자본 = 9월 말 지배자본 {f0(R['eq_3q'])}억 + 11월 영구형 전환사채 600억 + 2027 순이익. 완전희석 BPS는 부채로 잡힌 전환사채 1,600억이 전환된다고 보고 계산.")

rp.h1("5. 밸류에이션 (Valuation)", new_page=False)
rp.para("차입이 커서 주식가치보다 기업가치(EV) 기준이 맞고, 감가상각이 커서 EBITDA를 쓴다(A, 60%). 순손실 구간이라 자산가치(PBR)로 아래쪽을 확인한다(B, 40%).")
rp.h2("5-1. A. EV/EBITDA")
rp.para(f"2027E EBITDA {f0(FB['ebitda27'])}억 × 8배 = 기업가치 {f0(FB['ebitda27']*8)}억 − 순차입 {f0(R['net_debt'])}억 = {f0(FB['ebitda27']*8-R['net_debt'])}억 ÷ 완전희석 {R['sh_fd']:,}주 → **{B['va']:,.0f}원**.")
sn = R["sens_n"]
rp.table([["배수 \\ 순차입"] + [f"{f0(n)}억" for n in sn["nd"]]] + [[f"{m:.0f}배"] + [f0(x) for x in row] for m, row in zip(sn["mult"], sn["v"])],
         [20, 20, 20, 20, 20], note="A 값(원), EBITDA 3,300억. 순차입이 1,000억 줄 때마다 A가 약 1,370원 오른다.")
rp.h2("5-2. B. PBR")
rp.para(f"2027E 완전희석 BPS {FB['bps27_fd']:,.0f}원 × 자기 PBR 밴드 중앙값 {B['pbr']:.2f}배 = **{B['vb']:,.0f}원**. 밴드는 과거 주식수가 지금보다 적어 실제보다 높게 나오는 근사치다.")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. EV/EBITDA", "60%", f"{L['va']:,.0f} ({L['mult']:.0f}배)", f"{B['va']:,.0f} ({B['mult']:.0f}배)", f"{H['va']:,.0f} ({H['mult']:.0f}배)"],
          ["B. PBR", "40%", f"{L['vb']:,.0f}", f"{B['vb']:,.0f}", f"{H['vb']:,.0f}"],
          ["목표주가", "", f0(L["tp"]), f"{B['tp']:,.0f} → {TP:,}", f0(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [24, 10, 22, 22, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / f"full_football_{TAG}.png", W)
rp.h2("5-4. 민감도 — EV/EBITDA × 2027 EBITDA (목표주가)")
sp = R["sens_p"]
rp.table([["EBITDA \\ 배수"] + [f"{m:.0f}배" for m in sp["mult"]]] + [[f"{f0(e)}억"] + [f0(x) for x in row] for e, row in zip(sp["e"], sp["v"])],
         [20, 16, 16, 16, 16, 16], note="A 60 · B 40.")

rp.h1("6. BUY가 되기 위한 조건", new_page=False)
rp.para(f"목표주가는 위 방법 그대로 두고, 지금 주가({PRICE:,.0f}원)에서 BUY(+15%, 목표주가 {BY['buy_price']:,.0f}원)가 되려면 무엇이 맞아야 하는지 거꾸로 계산했다. 목표가에는 넣지 않는다.")
rp.table([["조건", "필요한 값", "비교"],
          ["2027 EBITDA가 기본(3,300억)일 때 EV/EBITDA", f"{BY['need_mult']:.1f}배", f"피어 중앙 {BY['peer_eve_med']:.1f}배, 최고 비에이치아이 7.7배"],
          ["배수 8배일 때 2027 EBITDA", f"{f0(BY['need_ebitda27'])}억", f"3Q26 EBITDA {f0(BY['ebitda_q3'])}억 × 4 = {f0(BY['ebitda_q3']*4)}억의 {BY['need_ebitda27']/(BY['ebitda_q3']*4):.1f}배"],
          ["EBITDA·배수 기본일 때 순차입", "0원이 돼도 부족" if BY["need_net_debt"] is None else f"{f0(BY['need_net_debt'])}억", f"지금 {f0(R['net_debt'])}억"]],
         [38, 26, 36])
rp.h2("확인할 지표와 조건부 매수 가격")
rp.table([["이 조건이 확인되면", "적정가", "매수 추천 가격 (15% 여유)"]] +
         [[c["cond"], f0(c["px"] * 1.15), f"{c['px']:,.0f}원 이하"] for c in BY["cond"]], [56, 18, 26],
         note="매수 가격 = 그 조건에서의 목표주가 ÷ 1.15. 순차입은 분기보고서 차입금 − 현금으로 확인한다.")
rp.para("이 회사는 사업 성장보다 재무 구조가 주가를 정한다. 안정적인 관점에서는 영업 흑자가 이어지면서 빚이 실제로 줄어드는 것을 확인한 뒤가 매수 시점이다.", 8.5)

rp.h1("7. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "ESS·연료전지 수주 확대", "Bloom Energy 추가 발주, 미국 ESS 수출 확대 시 EBITDA 상향", f"낙관 {H['tp']:,.0f}원"],
          ["상방", "전환사채 전환으로 차입 감소", "부채로 잡힌 전환사채 1,600억이 전환되면 순차입이 줄어든다(희석은 이미 반영)", "A 상향"],
          ["하방", "환율", "원/달러 변동으로 외화환산손실 반복(3Q26 760억)", "순이익·자본 감소"],
          ["하방", "단기 차입 차환", f"단기·유동성 장기 차입 {f0(R['debt']['short'] + R['debt']['current_lt'])}억의 만기 연장·금리", f"보수 {L['tp']:,.0f}원"],
          ["하방", "최대주주 주식담보", "주식담보 계약 정정 공시가 잦음 — 주가 급락 시 반대매매 위험", "주가 변동"]],
         [8, 22, 46, 24])
rp.h1("8. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {TP:,}원 (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {TP:,}원 · 보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"],
          ["BUY 조건", f"EV/EBITDA {BY['need_mult']:.1f}배, 또는 2027 EBITDA {f0(BY['need_ebitda27'])}억"],
          ["재검토 조건", "① 4Q26 영업이익·EBITDA ② 순차입 감소 여부 ③ 전환사채 전환·추가 발행"],
          ["결론", "사업은 좋아지고 있지만 빚과 희석이 주주 몫을 줄인다. 재무 구조 개선이 확인되기 전까지는 보수적으로 본다."]], [20, 80])
rp.since("9", "2026-08-24",
         [["항목", "원래 리포트 (2026-08-24)", "재조사 (2026-11-18)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {O['tp']:,}원", f"{RATING} / {TP:,}원 (기준주가 {PRICE:,.0f}원)"],
          ["주가", f"{R['px_orig']:,.0f}원 (08-24 종가)", f"{PRICE:,.0f}원 ({R['chg_since']*100:+.1f}%, 10-06 고점 {R['hi_since']:,.0f}원)"],
          ["실적", "1H26까지 (영업적자)", f"3Q26 영업이익 {f0(q3['op'])}억, 순이익 {f0(q3['ni'])}억"],
          ["주식 수", f"{R['sh_begin']:,}주 (기초)", f"{R['sh']:,}주, 완전희석 {R['sh_fd']:,}주"],
          ["평가 방법", O["method"], "A. EV/EBITDA 8배 60 + B. PBR 밴드 40, 'BUY가 되기 위한 조건' 추가"],
          ["대안 시나리오", "-", f"보수 {L['tp']:,.0f} · 낙관 {H['tp']:,.0f}원"]],
         [f"3Q26 영업 흑자 전환(387억), 반도체장비·ESS 수출 급증. 그러나 외화환산손실·이자·중단영업 손실로 순손실 {f0(q3['ni'])}억.",
          "전환사채 3,200억 추가 발행(8월 2,000억, 11월 1,200억). 베트남 법인 일부 사업 중단(09-30).",
          f"Bloom Energy SOFC 공급계약 {f0(BL['amt'])}억(10-12).",
          f"주가: 08-24 {R['px_orig']:,.0f}원 → 10-06 {R['hi_since']:,.0f}원(최고) → 11-18 {PRICE:,.0f}원."],
         ["주식 수를 전환사채 전환까지 넣은 완전희석 기준으로 바꿨다.",
          "EBITDA를 3Q26 실적과 Bloom 계약으로 다시 쌓았고, 피어 EV/EBITDA를 새로 모았다.",
          "지금 가격이 정당화되려면 무엇이 필요한지 'BUY가 되기 위한 조건' 장으로 보였다."],
         f"{O['tp']:,}원 → {TP:,}원. 영업은 좋아졌지만 순차입 {f0(R['net_debt'])}억과 전환사채 희석이 주당 가치를 낮췄다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 DART 공시(분기보고서, 전환사채 발행, 사업 중단, 단일판매·공급계약), 한국은행 ECOS, FinanceDataReader(네이버 시세), yfinance(KOSDAQ, 베타), stock_db 재무(피어 배수)를 바탕으로 작성한 개인 분석 자료입니다.")
out = HERE / f"서진시스템_리서치리포트_{TAG}.docx"
rp.doc.save(out); print(out); to_pdf(out)
