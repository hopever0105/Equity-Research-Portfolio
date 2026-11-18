"""주성엔지니어링_리서치리포트_20261118.docx/.pdf — 2026-08-12 리포트를 2026-11-18 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_fdr.csv. 실행: python valuation/주성엔지니어링/make_full_report_20261118.py
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
FB = B["rows"]
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
YRS = ["2022", "2023", "2024", "2025"]
TAG = "20261118"

# ═════════════════════════ 차트
px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / f"full_price_{TAG}.png", "최근 2년 종가(원), 기준일 2026-11-18", alt=[(H["tp"], "낙관")])
pb = pd.Series(R["pband"]["series"]); pb.index = pd.to_datetime(pb.index)
line_band_chart(list(pb.index), list(pb.values), R["pband"]["mean"], R["pband"]["sd"], HERE / f"full_band_{TAG}.png",
                f"주성엔지니어링 PBR 밴드(월말 종가 ÷ 공시된 지배 BPS, 2022-03~2026-11) — 중앙값 {R['pband']['median']:.1f}배", "PBR(배)")
yrs = [f"{y}A" for y in YRS] + ["2026E", "2027E", "2028E"]
bar_chart(yrs, [("매출(억원)", [HI[y]["rev"] for y in YRS] + [r["rev"] for r in FB[:3]], "#1F3864"),
                ("영업이익(억원)", [HI[y]["op"] for y in YRS] + [r["op"] for r in FB[:3]], "#8FAADC")],
          HERE / f"full_earn_{TAG}.png", "매출·영업이익(억원)과 영업이익률 — 음영은 추정(기본, 2026E = 9M 실적 + 4Q 추정)", est_from=4,
          line=("영업이익률", [HI[y]["op"] / HI[y]["rev"] for y in YRS] + [r["opm"] for r in FB[:3]]))
ql = ["20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q"]
bar_chart(["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"],
          [("매출", [Q[k]["rev"] for k in ql], "#1F3864"), ("영업이익", [Q[k]["op"] for k in ql], "#8FAADC")],
          HERE / f"full_q_{TAG}.png", "분기 매출·영업이익(억원)", ylab="억원")
football_chart([("A. 선행 PER (2027E EPS × 목표 PER)", L["va"], B["va"], H["va"]), ("B. DCF (FCFF, WACC %.1f%%)" % (R["wacc"] * 100), L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A·B 50:50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / f"full_football_{TAG}.png")

PK = BY["peak"]
SUB = f"3분기 영업이익률 23%로 회복, 그러나 주가는 2027E EPS의 {R['per_27_now']:.0f}배 — BUY가 되려면 PER {BY['need_per']:.0f}배가 필요하다"
MKT = [["현재주가 (2026.11.18 종가)", f"{PRICE:,.0f}원"], ["시가총액", f"{R['mcap']/1e4:.1f}조원"],
       ["유통주식수", f"{R['sh']:,}주"], ["52주 최고 / 최저 (장중)", f"{R['hi52']:,.0f} / {R['lo52']:,.0f}원"],
       ["PER (최근 4분기)", f"{R['per_ttm']:.0f}배"], ["PER (2027E 기본)", f"{R['per_27_now']:.0f}배"],
       ["PBR (9월 말 지배자본)", f"{R['pbr']:.1f}배"], ["9M26 매출 / 영업이익", f"{f0(R['m9']['매출'])}억 / {f0(R['m9']['영업이익'])}억"],
       ["순현금 (9월 말)", f"{f0(R['net_cash'])}억"], ["원래 리포트 (2026.08.12)", f"{O['rating']} · {O['tp']:,}원"]]
ALT = [f"보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"]

rp = Rep("반도체 장비 (증착)", "2026년 11월 18일")
rp.cover("주성엔지니어링 (036930 KS)", SUB, RATING, TP, PRICE, UP, "원", HERE / f"full_price_{TAG}.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, 연결 기준)")
rows = [["항목 (억원)", "2022A", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출액"] + [f0(HI[y]["rev"]) for y in YRS] + [f0(r["rev"]) for r in FB[:3]],
        ["영업이익"] + [f0(HI[y]["op"]) for y in YRS] + [f0(r["op"]) for r in FB[:3]],
        ["영업이익률"] + [pc(HI[y]["op"] / HI[y]["rev"]) for y in YRS] + [pc(r["opm"]) for r in FB[:3]],
        ["지배주주 순이익"] + [f0(HI[y]["ni"]) for y in YRS] + [f0(r["ni"]) for r in FB[:3]],
        ["EPS (원)"] + [f0(HI[y]["ni"] * 1e8 / R["sh"]) for y in YRS] + [f0(r["eps"]) for r in FB[:3]]]
rp.table(rows, [22, 11, 11, 11, 11, 11, 11, 12], hl_cols=(5, 6, 7),
         note=f"자료: DART 연결재무제표. 2026E = 9M 실적 + 4Q 추정. 2027E 이후 순이익 = 영업이익 × (1 − {R['tax']*100:.0f}%) + 이자수익 20억. EPS는 현재 유통주식수 기준.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", "실적은 돌아섰다 — 3Q26 매출 781억, 영업이익률 23%",
              [f"3Q26 매출은 전년보다 33% 늘었고 영업이익 177억은 2024년 3분기 이후 가장 많다. 1Q26 적자(−70억)에서 두 분기 만에 회복",
               f"9월 말 수주잔고 {f0(R['backlog']['total'])}억(반도체 {f0(R['backlog']['semi'])}억 · 디스플레이 {f0(R['backlog']['disp'])}억)은 2026E 매출의 약 {R['backlog']['total']/FB[0]['rev']*100:.0f}%"])
rp.thesis_box("②", f"그러나 가격은 과거 최고 이익의 몇 배를 전제 — PBR {R['pbr']:.0f}배, 2027E PER {R['per_27_now']:.0f}배",
              [f"2027년 매출이 {pc(SA['기본']['g27'],0)} 늘어 영업이익률 {pc(SA['기본']['m27'],0)}가 돼도 EPS는 {FB[1]['eps']:,.0f}원이다. 최고였던 {PK['ni_y']}년 순이익 {f0(PK['ni'])}억을 다시 내도 지금 주가는 그 이익의 {R['mcap']/PK['ni']:.0f}배",
               f"자기 PBR 밴드 중앙값은 {R['pband']['median']:.1f}배인데 지금은 {R['pbr']:.1f}배다"])
rp.thesis_box("③", f"현금흐름 가치는 {B['vb']:,.0f}원 — 목표주가 {TP:,}원, {RATING}",
              [f"할인율 {pc(R['wacc'])}(베타 {R['beta']['blume']:.2f})로 2036년까지 현금흐름을 할인하면 주당 {B['vb']:,.0f}원",
               f"BUY(+15%)가 되려면 2027E 이익이 그대로일 때 PER {BY['need_per']:.0f}배, 영업이익률 30%를 가정해도 2027년 매출 {f0(BY['need_rev27_hi'])}억(2022년 최고의 {BY['need_rev27_hi']/PK['rev']:.1f}배)이 필요하다(6장)"])
rp.para(f"▶ 결론: 목표주가 {TP:,}원(A. 2027E EPS {FB[1]['eps']:,.0f}원 × PER {B['per']:.0f}배 = {B['va']:,.0f}원 · B. DCF {B['vb']:,.0f}원, 50:50), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(08-12, {O['rating']} {O['tp']:,}원) 이후 주가는 10-06 {R['hi_since']:,.0f}원까지 올랐다가 {PRICE:,.0f}원으로 내려왔다. 실적 회복은 맞지만 가격이 그보다 훨씬 앞서 있다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.h2("1-1. 사업 소개")
rp.para("주성엔지니어링(036930)은 반도체·디스플레이·태양전지 증착 장비 기업이다. 웨이퍼 위에 아주 얇은 막을 입히는 CVD(화학기상증착)와 "
        "원자층 단위로 막을 쌓는 ALD(원자층증착) 장비가 주력이다. 메모리 미세화와 3차원 구조가 늘수록 얇고 고른 막이 더 많이 필요해 ALD 수요가 커진다. "
        "장비는 고객이 설비투자를 할 때 한꺼번에 발주하므로 매출과 이익이 고객 투자 주기를 따라 크게 흔들린다(2022년 매출 4,379억 → 2023년 2,847억).")
rp.h2("1-2. 매출 구조의 변화")
ex = R["export"]
rp.table([["구분 (억원)", "2025년 연간", "2026년 9개월"],
          ["내수", f0(ex["fy25_dom"]), f0(ex["m9_dom"])], ["수출", f0(ex["fy25_exp"]), f0(ex["m9_exp"])],
          ["수출 비중", pc(ex["fy25_exp"] / (ex["fy25_dom"] + ex["fy25_exp"]), 0), pc(ex["m9_exp"] / (ex["m9_dom"] + ex["m9_exp"]), 0)]],
         [40, 30, 30], note="자료: 3Q26 분기보고서. 2025년에는 중국 고객 비중이 컸고, 2026년에는 국내 메모리 고객 비중이 커졌다.")
rp.h2("1-3. 재무 상태")
rp.para(f"9월 말 현금성자산 {f0(R['cash'])}억, 차입금 {f0(R['debt'])}억으로 순현금 {f0(R['net_cash'])}억이다. 지배자본 {f0(R['eq_3q'])}억. 유통주식 {R['sh']:,}주.")

rp.h1("2. 실적 분석 (Performance Review)")
q3, q3p = Q["20263Q"], Q["20253Q"]
rp.kpi_tiles([("3Q26 매출", f"{f0(q3['rev'])}억", f"{q3['rev']/q3p['rev']-1:+.0%} YoY"),
              ("3Q26 영업이익", f"{f0(q3['op'])}억", f"영업이익률 {q3['op']/q3['rev']*100:.0f}%"),
              ("9M26 매출", f"{f0(R['m9']['매출'])}억", f"{R['m9']['매출']/R['m9p']['매출']-1:+.1%} YoY"),
              ("9M26 영업이익", f"{f0(R['m9']['영업이익'])}억", f"{R['m9']['영업이익']/R['m9p']['영업이익']-1:+.1%} YoY")])
rp.img(HERE / f"full_q_{TAG}.png", W)
rp.para(f"1Q26은 매출 {f0(Q['20261Q']['rev'])}억에 영업손실 {f0(-Q['20261Q']['op'])}억이었지만 2Q26 흑자로 돌아섰고, 3Q26에는 매출 {f0(q3['rev'])}억, 영업이익 {f0(q3['op'])}억으로 회복 속도가 빨라졌다. "
        f"다만 9개월 누계는 매출 {R['m9']['매출']/R['m9p']['매출']-1:+.0%}, 영업이익 {R['m9']['영업이익']/R['m9p']['영업이익']-1:+.0%}로 아직 전년보다 적다. 3Q 순이익 {f0(q3['ni'])}억에는 법인세 환급 효과가 들어 있다.")
rp.h2("2-1. 연간 실적")
rp.img(HERE / f"full_earn_{TAG}.png", W)

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 회복의 크기 — 수주잔고와 분기 실적")
rp.para(f"9월 말 수주잔고 {f0(R['backlog']['total'])}억은 4Q26 이후 매출의 바탕이다. 기본 시나리오는 4Q26 매출 {f0(SA['기본']['q4'])}억(3Q 수준), 2027년 매출 {pc(SA['기본']['g27'],0)} 성장"
        f"({f0(FB[1]['rev'])}억)과 영업이익률 {pc(SA['기본']['m27'],0)}를 둔다. 2022년 정점(매출 4,379억, 영업이익률 28%)까지는 가지 않는다고 본 것이다. "
        "회복은 국내 메모리 고객의 투자에 기대고 있고, 수출(중국) 매출은 2025년보다 크게 줄었다.")
rp.h2("Thesis 2. 가격이 이미 정점 이익을 넘어섰다")
rp.img(HERE / f"full_band_{TAG}.png", W)
rp.para(f"2022-03 이후 월말 PBR은 중앙값 {R['pband']['median']:.1f}배, 상위 25% {R['pband']['q75']:.1f}배였다. 지금 {R['pbr']:.1f}배는 이 범위를 크게 벗어났다. "
        f"최근 4분기 PER은 {R['per_ttm']:.0f}배, 2027E 기본 EPS로도 {R['per_27_now']:.0f}배다. 반도체 장비 피어(유진테크·피에스케이·테스·이오테크닉스·케이씨텍) PER 중앙값은 {R['peer_per_med']:.0f}배다.")
rp.h2("Thesis 3. 현금흐름이 말하는 값")
rp.para(f"DCF(5-3절)는 2027~2028년 회복 뒤 2029~2036년 성장률을 6% → 2%로, 영업이익률을 {pc(SA['기본']['m27'],0)} → {pc(SA['기본']['m_lt'],0)}로 둔다. "
        f"할인율 {pc(R['wacc'])}에서 주당 {B['vb']:,.0f}원이다. 장비 업체의 이익은 고객 증설 주기를 따르므로, 정점 마진이 길게 이어진다고 보지 않았다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rows = [["항목 (기본, 억원)", "2025A", "9M26A", "2026E", "2027E", "2028E", "2030E", "2036E"]]
pick = [FB[0], FB[1], FB[2], FB[4], FB[-1]]
rows += [["매출액", f0(HI["2025"]["rev"]), f0(R["m9"]["매출"])] + [f0(r["rev"]) for r in pick],
         ["영업이익", f0(HI["2025"]["op"]), f0(R["m9"]["영업이익"])] + [f0(r["op"]) for r in pick],
         ["영업이익률", pc(HI["2025"]["op"] / HI["2025"]["rev"]), pc(R["m9"]["영업이익"] / R["m9"]["매출"])] + [pc(r["opm"]) for r in pick],
         ["순이익", f0(HI["2025"]["ni"]), f0(R["m9"]["지배순이익"])] + [f0(r["ni"]) for r in pick],
         ["FCFF", "-", "-"] + [f0(r["fcff"]) for r in pick]]
rp.table(rows, [18, 11, 11, 12, 12, 12, 12, 12], hl_cols=(3, 4, 5, 6, 7),
         note="FCFF = 영업이익 × (1 − 15%) + 감가상각(매출 5.4%) − 설비투자(매출 5%) − 운전자본 증가(매출 증가분의 15%).")
rp.table([["가정", "보수", "기본", "낙관"],
          ["4Q26 매출 / 영업이익률", *[f"{f0(SA[k]['q4'])}억 / {pc(SA[k]['q4m'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2027 매출 성장률", *[pc(SA[k]["g27"], 0) for k in ("보수", "기본", "낙관")]],
          ["2027~2028 영업이익률", *[pc(SA[k]["m27"], 0) for k in ("보수", "기본", "낙관")]],
          ["2028 매출 성장률", *[pc(SA[k]["g28"], 0) for k in ("보수", "기본", "낙관")]],
          ["2036 영업이익률 (DCF)", *[pc(SA[k]["m_lt"], 0) for k in ("보수", "기본", "낙관")]],
          ["목표 PER", f"{L['per']:.0f}배 (피어 중앙)", f"{B['per']:.0f}배", f"{H['per']:.0f}배 (자기 밴드 상위)"]],
         [30, 23, 23, 24], note="목표 PER 30배는 반도체 장비 피어 중앙(약 18배)과 자기 PER 밴드 상위 25%(약 49배)의 중간이다(2026-11-18 결정).")

rp.h1("5. 밸류에이션 (Valuation)", new_page=False)
rp.para("장비주는 시장이 선행 PER로 가격을 매기므로 A(2027E EPS × 목표 PER)를 쓰고, 배수가 업황에 따라 부풀 수 있어 B(DCF)로 현금흐름 기준 값을 함께 본다. 50:50.")
rp.h2("5-1. 할인율")
bt = R["beta"]
rp.table([["항목", "값", "근거"], ["무위험이자율", pc(R["rf"], 2), "국고채 10년, 2026-11-17 (ECOS)"],
          ["베타", f"{bt['blume']:.2f}", f"KOSDAQ 대비 2년 주간 원베타 {bt['raw']:.2f}, Blume 조정"],
          ["시장위험프리미엄", "7.0%", "다른 리포트와 같음"], ["WACC (= 자기자본비용)", pc(R["wacc"], 2), "순현금"], ["영구성장률", "2.0%", ""]], [22, 14, 64])
rp.h2("5-2. A. 선행 PER")
rp.para(f"2027E EPS {FB[1]['eps']:,.0f}원 × PER {B['per']:.0f}배 = **{B['va']:,.0f}원**.")
rp.h2("5-3. B. DCF")
rp.para(f"4Q26~2036 FCFF 현재가치 {B['pv']:,.0f}억 + 영구가치 {B['tv']:,.0f}억(현재가치) + 순현금 {f0(R['net_cash'])}억 → 주당 **{B['vb']:,.0f}원**.")
sd = R["sens_d"]
rp.table([["2036 영업이익률 \\ WACC"] + [pc(w, 1) for w in sd["wacc"]]] + [[pc(m, 0)] + [f0(x) for x in row] for m, row in zip(sd["m"], sd["v"])],
         [25, 18, 19, 19, 19], note="B 값(원).")
rp.h2("5-4. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. 선행 PER", "50%", f"{L['va']:,.0f} ({L['per']:.0f}배)", f"{B['va']:,.0f} ({B['per']:.0f}배)", f"{H['va']:,.0f} ({H['per']:.0f}배)"],
          ["B. DCF", "50%", f0(L["vb"]), f0(B["vb"]), f0(H["vb"])],
          ["목표주가", "", f0(L["tp"]), f"{B['tp']:,.0f} → {TP:,}", f0(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [24, 10, 22, 22, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / f"full_football_{TAG}.png", W)
rp.h2("5-5. 민감도 — 목표 PER × 2027 영업이익률 (목표주가)")
sp = R["sens_p"]
rp.table([["2027 마진 \\ PER"] + [f"{p:.0f}배" for p in sp["per"]]] + [[pc(m, 0)] + [f0(x) for x in row] for m, row in zip(sp["m"], sp["v"])],
         [20, 16, 16, 16, 16, 16], note="A·B 50:50. 2027 매출은 기본(+45%).")
rp.table([["교차확인 (반도체 장비 피어, TTM 2Q26)", "PER", "PBR", "영업이익률"]] +
         [[p["name"], f"{p['PER']:.1f}배", f"{p['PBR']:.1f}배", pc(p["OPM"], 0)] for p in R["peer"]], [40, 20, 20, 20],
         note="tools/peers.py(stock_db 재무, 2Q26까지 4개 분기 합). 목표가 계산에는 쓰지 않았다.")

rp.h1("6. BUY가 되기 위한 조건", new_page=False)
rp.para(f"목표주가는 위 방법 그대로 두고, 지금 주가({PRICE:,.0f}원)에서 BUY(+15%, 목표주가 {BY['buy_price']:,.0f}원)가 되려면 무엇이 맞아야 하는지 거꾸로 계산했다. 목표가에는 넣지 않는다.")
rp.table([["조건", "필요한 값", "비교"],
          ["2027E 이익이 기본(EPS {:,.0f}원)일 때 목표 PER".format(BY["base_eps27"]), f"{BY['need_per']:.0f}배", f"제안 30배, 피어 중앙 {R['peer_per_med']:.0f}배, 자기 밴드 상위 25% 약 49배"],
          ["PER 30배 · 2027 영업이익률 30%일 때 2027 매출", f"{f0(BY['need_rev27_hi'])}억 (성장 {BY['need_g27_hi']*100:+.0f}%)", f"최고 {PK['rev_y']}년 {f0(PK['rev'])}억의 {BY['need_rev27_hi']/PK['rev']:.1f}배"],
          ["그때 2027 순이익", f"{f0(BY['need_ni27_hi'])}억", f"최고 {PK['ni_y']}년 {f0(PK['ni'])}억의 {BY['need_ni27_hi']/PK['ni']:.1f}배"],
          ["수주잔고 (9월 말)", f"{f0(R['backlog']['total'])}억", "필요 매출의 약 {:.0f}%".format(R['backlog']['total'] / BY['need_rev27_hi'] * 100)]],
         [38, 24, 38], note="영업이익률 기본(20%) 그대로면 2027 매출을 몇 배로 늘려도 BUY 가격에 닿지 않는다(DCF 부분이 따라 오르지 않음).")
rp.h2("확인할 지표와 조건부 매수 가격")
rp.table([["이 조건이 확인되면", "적정가", "매수 추천 가격 (15% 여유)"]] +
         [[c["cond"], f0(c["px"] * 1.15), f"{c['px']:,.0f}원 이하"] for c in BY["cond"]], [56, 18, 26],
         note="매수 가격 = 그 조건에서의 목표주가 ÷ 1.15. 분기 실적과 수주잔고는 분기보고서로 확인한다.")
rp.para("정리하면, 지금 가격에서 사는 것은 2022년 정점의 몇 배에 이르는 이익을 미리 사는 것이다. 실적 회복을 확인하면서 사려면 위 가격대까지 기다리는 쪽이 안정적이다.", 8.5)

rp.h1("7. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "ALD 수요 확대", "메모리 미세화·3차원 구조로 ALD 장비 채택이 빨라지면 2027 성장률·마진 상향", f"낙관 {H['tp']:,.0f}원"],
          ["상방", "해외 고객 회복", "중국 등 수출 매출이 2025년 수준(2,009억)으로 돌아오면 매출 규모 확대", "매출 상향"],
          ["하방", "고객 투자 지연", "국내 메모리 고객의 설비투자가 늦어지면 분기 실적이 다시 적자 가능(1Q26 −70억)", f"보수 {L['tp']:,.0f}원"],
          ["하방", "배수 정상화", "PBR이 자기 밴드(중앙 {:.1f}배)로 돌아가면 주가 하락 폭이 큼".format(R["pband"]["median"]), "주가 변동"]],
         [8, 18, 50, 24])
rp.h1("8. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {TP:,}원 (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {TP:,}원 · 보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"],
          ["BUY 조건", f"2027E 이익 그대로면 PER {BY['need_per']:.0f}배, 또는 2027 매출 {f0(BY['need_rev27_hi'])}억 · 영업이익률 30%"],
          ["재검토 조건", "① 4Q26 실적과 수주잔고 ② 2027 국내 메모리 투자 계획 ③ 수출 매출 회복 여부"],
          ["결론", "실적 회복은 사실이지만 주가는 그 회복보다 몇 배 앞서 있다. 안정적인 관점에서는 회복이 숫자로 쌓이는 것을 보며 6장의 가격대에서 다시 판단한다."]], [20, 80])
rp.since("9", "2026-08-12",
         [["항목", "원래 리포트 (2026-08-12)", "재조사 (2026-11-18)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {O['tp']:,}원", f"{RATING} / {TP:,}원 (기준주가 {PRICE:,.0f}원)"],
          ["주가", f"{R['px_orig']:,.0f}원 (08-12 종가)", f"{PRICE:,.0f}원 ({R['chg_since']*100:+.1f}%, 10-06 고점 {R['hi_since']:,.0f}원)"],
          ["실적", "1H26까지 (1Q 적자, 2Q 흑자 전환)", f"3Q26 매출 {f0(q3['rev'])}억 · 영업이익 {f0(q3['op'])}억(영업이익률 23%)"],
          ["평가 방법", O["method"], "A. 2027E EPS × PER 30배 50 + B. DCF 50, 'BUY가 되기 위한 조건' 추가"],
          ["2027 가정", "-", f"매출 {pc(SA['기본']['g27'],0)} · 영업이익률 {pc(SA['기본']['m27'],0)}"],
          ["대안 시나리오", "-", f"보수 {L['tp']:,.0f} · 낙관 {H['tp']:,.0f}원"]],
         [f"3Q26: 매출 {f0(q3['rev'])}억(+33% YoY), 영업이익 {f0(q3['op'])}억. 9월 말 수주잔고 {f0(R['backlog']['total'])}억.",
          "매출 지역: 2026년 9개월 내수 1,382억 · 수출 547억으로 국내 메모리 고객 비중이 커지고 중국 매출이 줄었다.",
          f"주가: 08-12 {R['px_orig']:,.0f}원 → 10-06 {R['hi_since']:,.0f}원(최고) → 11-18 {PRICE:,.0f}원. PBR은 {R['pbr']:.0f}배로 자기 밴드 범위를 크게 벗어났다."],
         ["목표 PER을 피어 중앙과 자기 밴드 상위의 중간(30배)으로 두고, DCF를 절반 반영했다.",
          "회복이 정점(2022년)까지 간다고 보지 않고 2027 영업이익률 20%를 기본으로 했다.",
          "지금 가격이 정당화되려면 무엇이 필요한지 'BUY가 되기 위한 조건' 장으로 따로 보였다."],
         f"{O['tp']:,}원 → {TP:,}원. 실적은 회복했지만 DCF 할인율 {pc(R['wacc'])}에서 현금흐름 가치가 주당 {B['vb']:,.0f}원에 그치고, "
         f"2027E 이익에 30배를 줘도 {B['va']:,.0f}원이다. 상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 DART 공시(사업·분기·반기보고서, 연결 잠정실적), 한국은행 ECOS, FinanceDataReader(네이버 시세), yfinance(KOSDAQ, 베타), stock_db 재무(피어 배수)를 바탕으로 작성한 개인 분석 자료입니다.")
out = HERE / f"주성엔지니어링_리서치리포트_{TAG}.docx"
rp.doc.save(out); print(out); to_pdf(out)
