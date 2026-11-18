"""에스피지_리서치리포트_20261118.docx/.pdf — 2026-08-22 리포트를 2026-11-18 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_fdr.csv. 실행: python valuation/에스피지/make_full_report_20261118.py
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
FB = B["f"]; BD = R["band"]
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
YRS = ["2022", "2023", "2024", "2025"]
TAG = "20261118"
q3, q3p = Q["20263Q"], Q["20253Q"]
RD = R["reducer"]

px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / f"full_price_{TAG}.png", "최근 2년 종가(원), 기준일 2026-11-18", alt=[(H["tp"], "낙관")])
bs = pd.Series(BD["series"]); bs.index = pd.to_datetime(bs.index)
line_band_chart(list(bs.index), list(bs.values), BD["mean"], BD["sd"], HERE / f"full_band_{TAG}.png",
                f"에스피지 PER 밴드(월말 종가 ÷ 최근 4분기 지배 EPS, 2022-03~2026-11, 200배 이상 제외) — 중앙값 {BD['median']:.0f}배", "PER(배)")
yrs = [f"{y}A" for y in YRS] + ["2026E", "2027E"]
bar_chart(yrs, [("매출(억원)", [HI[y]["rev"] for y in YRS] + [FB["rev26"], FB["rev27"]], "#1F3864"),
                ("영업이익(억원)", [HI[y]["op"] for y in YRS] + [FB["op26"], FB["op27"]], "#8FAADC")],
          HERE / f"full_earn_{TAG}.png", "매출·영업이익(억원)과 영업이익률 — 음영은 추정(기본)", est_from=4,
          line=("영업이익률", [HI[y]["op"] / HI[y]["rev"] for y in YRS] + [FB["op26"] / FB["rev26"], FB["op27"] / FB["rev27"]]))
ql = ["20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q"]
bar_chart(["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"],
          [("영업이익", [Q[k]["op"] for k in ql], "#1F3864"), ("지배순이익", [Q[k]["ni"] for k in ql], "#8FAADC")],
          HERE / f"full_q_{TAG}.png", "분기 영업이익·순이익(억원)", ylab="억원")
football_chart([("A. 선행 PER (2027E EPS × 자기 밴드)", L["va"], B["va"], H["va"]), ("B. SOTP (본업 + 감속기 − 순차입)", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A·B 50:50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / f"full_football_{TAG}.png")

SUB = f"본업 이익은 줄고 주가는 감속기 기대 — 지금 가격은 감속기 매출의 {R['red_evs_now']:.0f}배, BUY에는 {BY['need_evs']:.0f}배가 필요"
MKT = [["현재주가 (2026.11.18 종가)", f"{PRICE:,.0f}원"], ["시가총액", f"{R['mcap']/1e4:.2f}조원"],
       ["발행주식 (자기주식 없음)", f"{R['sh']:,}주"], ["52주 최고 / 최저 (장중)", f"{R['hi52']:,.0f} / {R['lo52']:,.0f}원"],
       ["PER (최근 4분기)", f"{R['per_ttm']:.0f}배"], ["PER (2027E 기본)", f"{R['per_27_now']:.0f}배"],
       ["PBR (9월 말 지배자본)", f"{R['pbr']:.1f}배"], ["9M26 매출 / 영업이익", f"{f0(R['m9']['매출'])}억 / {f0(R['m9']['영업이익'])}억"],
       ["순차입 (9월 말)", f"{f0(R['net_debt'])}억"], ["원래 리포트 (2026.08.22)", f"{O['rating']} · {O['tp']:,}원"]]
ALT = [f"보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"]

rp = Rep("모터·정밀감속기", "2026년 11월 18일")
rp.cover("에스피지 (058610 KS)", SUB, RATING, TP, PRICE, UP, "원", HERE / f"full_price_{TAG}.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, 연결 기준)")
rows = [["항목 (억원)", "2022A", "2023A", "2024A", "2025A", "2026E", "2027E"],
        ["매출액"] + [f0(HI[y]["rev"]) for y in YRS] + [f0(FB["rev26"]), f0(FB["rev27"])],
        ["영업이익"] + [f0(HI[y]["op"]) for y in YRS] + [f0(FB["op26"]), f0(FB["op27"])],
        ["영업이익률"] + [pc(HI[y]["op"] / HI[y]["rev"]) for y in YRS] + [pc(FB["op26"] / FB["rev26"]), pc(FB["op27"] / FB["rev27"])],
        ["지배주주 순이익"] + [f0(HI[y]["ni"]) for y in YRS] + [f0(FB["ni26"]), f0(FB["ni27"])],
        ["EPS (원)"] + [f0(HI[y]["ni"] * 1e8 / R["sh"]) for y in YRS] + [f0(FB["ni26"] * 1e8 / R["sh"]), f0(FB["eps27"])]]
rp.table(rows, [24, 12, 12, 12, 12, 14, 14], hl_cols=(5, 6),
         note=f"자료: DART 연결재무제표. 2026E = 9M 실적 + 4Q 추정. 2027E 순이익 = 영업이익 × {R['ni_conv']:.2f}(2022년 비율 수준).")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", "본업은 약해졌다 — 3Q26 영업이익 34억(−31% YoY), 순손실",
              [f"9M26 매출 {f0(R['m9']['매출'])}억({R['m9']['매출']/R['m9p']['매출']-1:+.1%}), 영업이익률 {R['m9']['영업이익']/R['m9']['매출']*100:.1f}%. 3Q 판관비 +28%, 기타비용 52억",
               f"모터 본업 순이익은 최고 {BY['peak']['ni_y']}년 {f0(BY['peak']['ni'])}억에서 2025년 {f0(HI['2025']['ni'])}억으로 줄었다"])
rp.thesis_box("②", f"주가는 정밀감속기(로봇) 기대 — 감속기 매출의 약 {R['red_evs_now']:.0f}배",
              [f"정밀감속기 매출 2023년 {RD['2023']}억 → 2024년 {RD['2024']}억 → 2025년 {RD['2025']}억(연 +35%)",
               f"본업에 PER {R['motor_per']:.0f}배를 주고 남는 값을 감속기에 돌리면 2027E 감속기 매출의 {R['red_evs_now']:.0f}배다. 로봇 완성품 회사(레인보우로보틱스·두산로보틱스·로보티즈)는 적자에 EV/매출 50~145배"])
rp.thesis_box("③", f"목표주가 {TP:,}원, {RATING}",
              [f"A. 2027E EPS {FB['eps27']:,.0f}원 × 자기 PER 밴드 중앙값 {B['per']:.0f}배 = {B['va']:,.0f}원, B. SOTP {B['vb']:,.0f}원",
               f"BUY(+15%)가 되려면 감속기에 매출의 {BY['need_evs']:.0f}배, 또는 20배일 때 2027 감속기 매출 {f0(BY['need_red27'])}억(2025년의 {BY['need_red27']/RD['2025']:.0f}배)이 필요하다(6장)"])
rp.para(f"▶ 결론: 목표주가 {TP:,}원(A·B 50:50), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. 원래 리포트(08-22, {O['rating']} {O['tp']:,}원) 이후 본업 이익은 줄었고, 주가는 10-06 {R['hi_since']:,.0f}원까지 오른 뒤 {PRICE:,.0f}원이다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.h2("1-1. 사업 소개")
rp.para("에스피지(058610)는 소형 모터와 기어드 모터, 감속기를 만드는 기업이다. 매출 대부분은 가전·산업용 모터에서 나오고, 로봇 관절에 쓰는 정밀감속기는 아직 작지만 빠르게 크는 사업이다. "
        f"정밀감속기 매출은 2025년 {RD['2025']}억으로 전체 매출({f0(HI['2025']['rev'])}억)의 {RD['2025']/HI['2025']['rev']*100:.0f}%다.")
rp.h2("1-2. 원래 리포트 이후 주요 공시")
rp.table([["날짜", "공시", "내용"],
          ["2026-09-07", "중간배당 결정", "분기(중간) 현금배당"],
          ["2026-10-08", "기업설명회", "IR 개최"],
          ["2026-11-12", "3Q26 잠정실적", f"매출 {f0(q3['rev'])}억, 영업이익 {f0(q3['op'])}억"],
          ["2026-11-13", "3Q26 분기보고서", f"지배순이익 {f0(q3['ni'])}억(기타비용 52억)"]],
         [14, 20, 66], note="자료: DART.")
rp.para(f"9월 말 차입금 약 {f0(R['debt'])}억, 현금·단기금융상품 {f0(R['cash_st'])}억으로 순차입 {f0(R['net_debt'])}억이다. 지배자본 {f0(R['eq_3q'])}억.")

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("3Q26 매출", f"{f0(q3['rev'])}억", f"{q3['rev']/q3p['rev']-1:+.1%} YoY"),
              ("3Q26 영업이익", f"{f0(q3['op'])}억", f"영업이익률 {q3['op']/q3['rev']*100:.1f}%"),
              ("9M26 매출", f"{f0(R['m9']['매출'])}억", f"{R['m9']['매출']/R['m9p']['매출']-1:+.1%} YoY"),
              ("9M26 순이익", f"{f0(R['m9']['지배순이익'])}억", f"전년 {f0(R['m9p']['지배순이익'])}억")])
rp.img(HERE / f"full_q_{TAG}.png", W)
rp.para(f"영업이익은 1Q26 {f0(Q['20261Q']['op'])}억 → 2Q26 {f0(Q['20262Q']['op'])}억 → 3Q26 {f0(q3['op'])}억으로 줄었다. 판관비가 늘었고, 3Q에는 기타비용 52억으로 순손실이 났다.")
rp.h2("2-1. 연간 실적")
rp.img(HERE / f"full_earn_{TAG}.png", W)

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 본업 — 정체된 모터 사업")
rp.para(f"모터 매출은 2022년 {f0(HI['2022']['rev'])}억 이후 줄어 2025년 {f0(HI['2025']['rev'])}억이다. 기본 시나리오는 2027년 매출 {pc(SA['기본']['g27'],0)}, 영업이익률 {pc(SA['기본']['m27'],1)}"
        f"(2021~2025 평균 수준)로 2027E 순이익 {f0(FB['ni27'])}억, EPS {FB['eps27']:,.0f}원이다.")
rp.h2("Thesis 2. 감속기 — 빠르지만 아직 작다")
rp.para(f"정밀감속기는 2023~2025년 연 35%씩 늘었다. 같은 속도면 2027년 약 {f0(SA['기본']['red27'])}억이다. 감속기 가치를 따로 보려고 본업과 나눠 SOTP(B)로 계산했다. "
        f"목표 EV/매출 20배는 로봇 완성품 회사(50~145배, 적자)보다 크게 낮게, 부품사인 점을 반영했다.")
rp.table([["피어 (TTM 2Q26)", "PBR", "EV/매출", "영업이익률"]] +
         [[p["name"], f"{p['PBR']:.1f}배", f"{p['EV/Sales']:.1f}배", pc(p["OPM"], 0)] for p in R["peer"]], [34, 22, 22, 22],
         note="tools/peers.py(stock_db 재무, 2Q26까지 4개 분기 합). 모터 동종(계양전기·비에이치)은 EV/매출 0.1~0.3배.")
rp.h2("Thesis 3. 시장이 이 회사에 준 배수")
rp.img(HERE / f"full_band_{TAG}.png", W)
rp.para(f"2022-03 이후 PER(최근 4분기 EPS)은 중앙값 {BD['median']:.0f}배, 사분위 {BD['q25']:.0f}~{BD['q75']:.0f}배다. 로봇 기대가 이미 배수에 들어 있어, A(선행 PER)는 이 중앙값을 그대로 썼다.")

rp.h1("4. 실적 추정과 가정 (Forecast)")
rp.table([["가정", "보수", "기본", "낙관"],
          ["4Q26 매출 / 영업이익률", *[f"{f0(SA[k]['q4'])}억 / {pc(SA[k]['q4m'],1)}" for k in ("보수", "기본", "낙관")]],
          ["2027 매출 성장률", *[pc(SA[k]["g27"], 0) for k in ("보수", "기본", "낙관")]],
          ["2027 영업이익률", *[pc(SA[k]["m27"], 1) for k in ("보수", "기본", "낙관")]],
          ["2027 EPS", *[f"{S[k]['f']['eps27']:,.0f}원" for k in ("보수", "기본", "낙관")]],
          ["2027 감속기 매출", *[f"{f0(SA[k]['red27'])}억" for k in ("보수", "기본", "낙관")]],
          ["감속기 EV/매출", *[f"{SA[k]['evs']:.0f}배" for k in ("보수", "기본", "낙관")]],
          ["PER (자기 밴드)", f"{L['per']:.0f}배 (하위 25%)", f"{B['per']:.0f}배 (중앙)", f"{H['per']:.0f}배 (상위 25%)"]],
         [30, 23, 23, 24], note=f"SOTP 본업 순이익 = 전체 순이익 − 감속기 순이익(매출 × {R['red_ni_m']*100:.0f}%), 본업 PER {R['motor_per']:.0f}배.")

rp.h1("5. 밸류에이션 (Valuation)", new_page=False)
rp.para("A는 시장이 이 회사에 실제로 준 배수(자기 PER 밴드)로 2027E 이익을 평가하고, B는 본업과 감속기를 나눠 감속기 가치를 드러낸다. 50:50.")
rp.h2("5-1. A. 선행 PER")
rp.para(f"2027E EPS {FB['eps27']:,.0f}원 × PER 밴드 중앙값 {B['per']:.1f}배 = **{B['va']:,.0f}원**.")
sa = R["sens_a"]
rp.table([["2027 마진 \\ PER"] + [f"{p:.0f}배" for p in sa["per"]]] + [[pc(m, 1)] + [f0(x) for x in row] for m, row in zip(sa["m"], sa["v"])],
         [20, 20, 20, 20, 20], note="A 값(원).")
rp.h2("5-2. B. SOTP")
rp.table([["구성", "2027E", "배수", "가치(억원)"],
          ["모터 등 본업 순이익", f"{f0(FB['motor_ni27'])}억", f"PER {R['motor_per']:.0f}배", f0(FB["motor_ni27"] * R["motor_per"])],
          ["정밀감속기 매출", f"{f0(FB['red27'])}억", f"EV/매출 {B['evs']:.0f}배", f0(FB["red27"] * B["evs"])],
          ["순차입", "", "", f"−{f0(R['net_debt'])}"],
          ["주주가치 / 주당", "", "", f"{f0(FB['motor_ni27']*R['motor_per'] + FB['red27']*B['evs'] - R['net_debt'])}억 / {B['vb']:,.0f}원"]], [34, 20, 20, 26])
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. 선행 PER", "50%", f"{L['va']:,.0f} ({L['per']:.0f}배)", f"{B['va']:,.0f} ({B['per']:.0f}배)", f"{H['va']:,.0f} ({H['per']:.0f}배)"],
          ["B. SOTP", "50%", f"{L['vb']:,.0f}", f"{B['vb']:,.0f}", f"{H['vb']:,.0f}"],
          ["목표주가", "", f0(L["tp"]), f"{B['tp']:,.0f} → {TP:,}", f0(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [24, 10, 22, 22, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / f"full_football_{TAG}.png", W)
rp.h2("5-4. 민감도 — 감속기 EV/매출 × 2027 감속기 매출 (목표주가)")
sp = R["sens_p"]
rp.table([["감속기 매출 \\ EV/매출"] + [f"{e:.0f}배" for e in sp["evs"]]] + [[f"{f0(r)}억"] + [f0(x) for x in row] for r, row in zip(sp["red"], sp["v"])],
         [20, 16, 16, 16, 16, 16], note="A·B 50:50.")

rp.h1("6. BUY가 되기 위한 조건", new_page=False)
rp.para(f"목표주가는 위 방법 그대로 두고, 지금 주가({PRICE:,.0f}원)에서 BUY(+15%, 목표주가 {BY['buy_price']:,.0f}원)가 되려면 무엇이 맞아야 하는지 거꾸로 계산했다. 목표가에는 넣지 않는다.")
rp.table([["조건", "필요한 값", "비교"],
          ["감속기 매출 250억(2027E)일 때 EV/매출", f"{BY['need_evs']:.0f}배", "로봇 완성품 회사 50~145배(적자), 제안 20배"],
          ["EV/매출 20배일 때 2027 감속기 매출", f"{f0(BY['need_red27'])}억", f"2025년 {RD['2025']}억의 {BY['need_red27']/RD['2025']:.0f}배, 회사 전체 매출의 {BY['need_red27']/HI['2025']['rev']*100:.0f}%"],
          ["2027E 이익이 기본일 때 PER (A)", f"{BY['need_per']:.0f}배", f"자기 밴드 상위 25% {BD['q75']:.0f}배"]],
         [38, 24, 38])
rp.h2("확인할 지표와 조건부 매수 가격")
rp.table([["이 조건이 확인되면", "적정가", "매수 추천 가격 (15% 여유)"]] +
         [[c["cond"], f0(c["px"] * 1.15), f"{c['px']:,.0f}원 이하"] for c in BY["cond"]], [56, 18, 26],
         note="매수 가격 = 그 조건에서의 목표주가 ÷ 1.15. 감속기 매출은 사업보고서 제품별 매출에서 확인한다.")
rp.para("지금 가격은 감속기가 몇 년 안에 회사의 주력 사업이 된다는 가정이다. 감속기 매출이 실제로 그 속도로 느는지 사업보고서로 확인하면서 판단하는 편이 안정적이다.", 8.5)

rp.h1("7. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "로봇 고객 확보", "휴머노이드·협동로봇 업체의 감속기 대량 채택 시 매출 급증", f"낙관 {H['tp']:,.0f}원"],
          ["상방", "로봇 테마 배수", "로봇 기대가 이어지면 자기 밴드 상단 배수 유지", "A 상향"],
          ["하방", "본업 부진", "가전·산업용 모터 수요 둔화와 판관비 증가로 마진 하락(3Q26 4.2%)", f"보수 {L['tp']:,.0f}원"],
          ["하방", "테마 배수 축소", "로봇 기대가 식으면 PER이 밴드 하단으로", "주가 변동"]],
         [8, 18, 50, 24])
rp.h1("8. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {TP:,}원 (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {TP:,}원 · 보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"],
          ["BUY 조건", f"감속기 EV/매출 {BY['need_evs']:.0f}배, 또는 20배 기준 2027 감속기 매출 {f0(BY['need_red27'])}억"],
          ["재검토 조건", "① 2026 사업보고서 감속기 매출 ② 로봇 고객 공급계약 공시 ③ 본업 마진 회복"],
          ["결론", "감속기 성장은 사실이지만 회사 전체에서 아직 작고, 본업 이익은 줄었다. 주가는 감속기가 훨씬 커진 미래를 반영한다."]], [20, 80])
rp.since("9", "2026-08-22",
         [["항목", "원래 리포트 (2026-08-22)", "재조사 (2026-11-18)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {O['tp']:,}원", f"{RATING} / {TP:,}원 (기준주가 {PRICE:,.0f}원)"],
          ["주가", f"{R['px_orig']:,.0f}원 (08-21 종가)", f"{PRICE:,.0f}원 ({R['chg_since']*100:+.1f}%, 10-06 고점 {R['hi_since']:,.0f}원)"],
          ["실적", "1H26까지", f"3Q26 영업이익 {f0(q3['op'])}억(−31% YoY), 순이익 {f0(q3['ni'])}억"],
          ["평가 방법", O["method"], "A. 2027E EPS × 자기 PER 밴드 50 + B. SOTP(본업 12배 + 감속기 EV/매출 20배) 50, 'BUY가 되기 위한 조건' 추가"],
          ["대안 시나리오", "-", f"보수 {L['tp']:,.0f} · 낙관 {H['tp']:,.0f}원"]],
         [f"3Q26: 매출 {f0(q3['rev'])}억, 영업이익 {f0(q3['op'])}억(−31% YoY), 판관비 +28%, 기타비용 52억으로 분기 순손실.",
          "중간배당 결정(09-07), 기업설명회(10-08).",
          f"주가: 08-21 {R['px_orig']:,.0f}원 → 10-06 {R['hi_since']:,.0f}원(최고) → 11-18 {PRICE:,.0f}원."],
         ["본업과 감속기를 나눈 SOTP로 감속기에 주는 가치를 드러냈다.",
          "로봇 피어 배수를 새로 모으고, 부품사라 크게 할인한 20배를 썼다.",
          "지금 가격이 정당화되려면 무엇이 필요한지 'BUY가 되기 위한 조건' 장으로 보였다."],
         f"{O['tp']:,}원 → {TP:,}원. 본업 이익이 줄었고, 감속기에 피어보다 낮지만 높은 배수(20배)를 줘도 주당 가치가 지금 주가에 못 미친다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 DART 공시(분기보고서, 잠정실적, 배당), 한국은행 ECOS, FinanceDataReader(네이버 시세), yfinance(KOSDAQ, 베타), stock_db 재무(피어 배수)를 바탕으로 작성한 개인 분석 자료입니다. 정밀감속기 매출은 원래 리포트(2026-08-22)의 값을 썼습니다.")
out = HERE / f"에스피지_리서치리포트_{TAG}.docx"
rp.doc.save(out); print(out); to_pdf(out)
