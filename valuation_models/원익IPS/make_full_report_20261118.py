"""원익IPS_리서치리포트_20261118.docx/.pdf — 2026-08-12 리포트를 2026-11-18 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_fdr.csv. 실행: python valuation/원익IPS/make_full_report_20261118.py
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
FB = B["rows"]; WA, WB = R["w"]
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
YRS = ["2022", "2023", "2024", "2025"]
TAG = "20261118"

px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / f"full_price_{TAG}.png", "최근 2년 종가(원), 기준일 2026-11-18", alt=[(H["tp"], "낙관")])
pb = pd.Series(R["pband"]["series"]); pb.index = pd.to_datetime(pb.index)
line_band_chart(list(pb.index), list(pb.values), R["pband"]["mean"], R["pband"]["sd"], HERE / f"full_band_{TAG}.png",
                f"원익IPS PBR 밴드(월말 종가 ÷ 공시된 지배 BPS, 2022-03~2026-11) — 중앙값 {R['pband']['median']:.1f}배", "PBR(배)")
yrs = [f"{y}A" for y in YRS] + ["2026E", "2027E", "2028E"]
bar_chart(yrs, [("매출(억원)", [HI[y]["rev"] for y in YRS] + [r["rev"] for r in FB[:3]], "#1F3864"),
                ("영업이익(억원)", [HI[y]["op"] for y in YRS] + [r["op"] for r in FB[:3]], "#8FAADC")],
          HERE / f"full_earn_{TAG}.png", "매출·영업이익(억원)과 영업이익률 — 음영은 추정(기본, 2026E = 9M 실적 + 4Q 추정)", est_from=4,
          line=("영업이익률", [HI[y]["op"] / HI[y]["rev"] for y in YRS] + [r["opm"] for r in FB[:3]]))
ql = ["20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q"]
bar_chart(["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"],
          [("영업이익", [Q[k]["op"] for k in ql], "#1F3864"), ("지배순이익", [Q[k]["ni"] for k in ql], "#8FAADC")],
          HERE / f"full_q_{TAG}.png", "분기 영업이익과 순이익(억원) — 순이익은 금융자산 평가손익으로 따로 움직인다", ylab="억원")
football_chart([("A. 선행 PER (2027E EPS × 피어 PER)", L["va"], B["va"], H["va"]), ("B. DCF + 금융자산 (WACC %.1f%%)" % (R["wacc"] * 100), L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 60 · B 40)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / f"full_football_{TAG}.png")

PK = BY["peak"]
SUB = f"3분기 영업이익 667억으로 2022년 이후 최대, 그러나 가격은 이미 정상화 이익의 {R['per_27_now']:.0f}배 — BUY에는 영업이익률 {BY['need_m27']*100:.0f}%가 필요"
MKT = [["현재주가 (2026.11.18 종가)", f"{PRICE:,.0f}원"], ["시가총액 (자기주식 제외)", f"{R['mcap']/1e4:.1f}조원"],
       ["발행주식 / 자기주식", f"{R['sh_issued']:,} / {R['treasury']:,}주"], ["52주 최고 / 최저 (장중)", f"{R['hi52']:,.0f} / {R['lo52']:,.0f}원"],
       ["PER (2027E 기본)", f"{R['per_27_now']:.1f}배"], ["PBR (9월 말 지배자본)", f"{R['pbr']:.1f}배"],
       ["9M26 매출 / 영업이익", f"{f0(R['m9']['매출'])}억 / {f0(R['m9']['영업이익'])}억"], ["수주잔고 (9월 말)", f"{f0(R['backlog'])}억"],
       ["현금 + 공정가치 금융자산", f"{f0(R['cash'])}억 + {f0(R['fvpl'])}억"], ["원래 리포트 (2026.08.12)", f"{O['rating']} · {O['tp']:,}원"]]
ALT = [f"보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"]

rp = Rep("반도체 장비 (증착·식각)", "2026년 11월 18일")
rp.cover("원익IPS (240810 KS)", SUB, RATING, TP, PRICE, UP, "원", HERE / f"full_price_{TAG}.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, 연결 기준)")
rows = [["항목 (억원)", "2022A", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출액"] + [f0(HI[y]["rev"]) for y in YRS] + [f0(r["rev"]) for r in FB[:3]],
        ["영업이익"] + [f0(HI[y]["op"]) for y in YRS] + [f0(r["op"]) for r in FB[:3]],
        ["영업이익률"] + [pc(HI[y]["op"] / HI[y]["rev"]) for y in YRS] + [pc(r["opm"]) for r in FB[:3]],
        ["지배주주 순이익"] + [f0(HI[y]["ni"]) for y in YRS] + [f0(r["ni"]) for r in FB[:3]],
        ["EPS (원)"] + [f0(HI[y]["ni"] * 1e8 / R["sh"]) for y in YRS] + [f0(r["eps"]) for r in FB[:3]]]
rp.table(rows, [22, 11, 11, 11, 11, 11, 11, 12], hl_cols=(5, 6, 7),
         note="자료: DART 연결재무제표. 2026E 이후 순이익 = 영업이익 × (1 − 20%) + 이자수익 60억(금융자산 평가손익 제외, 그래서 실제 순이익과 다를 수 있다).")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", "본업은 확실히 좋아졌다 — 3Q26 영업이익 667억, 영업이익률 20%",
              [f"3Q26 매출 {f0(Q['20263Q']['rev'])}억(+26% YoY), 9M26 영업이익 {f0(R['m9']['영업이익'])}억(+{R['m9']['영업이익']/R['m9p']['영업이익']*100-100:.0f}%)",
               f"9월 말 수주잔고 {f0(R['backlog'])}억, 차입금 없음. 현금 {f0(R['cash'])}억과 공정가치 금융자산 {f0(R['fvpl'])}억"])
rp.thesis_box("②", "순이익은 금융자산 평가로 흔들린다 — 목표가는 영업이익 기준",
              [f"2Q26 순이익 {f0(Q['20262Q']['ni'])}억은 평가이익으로 부풀었고, 3Q26 순이익 {f0(Q['20263Q']['ni'])}억은 평가손실로 줄었다",
               "그래서 EPS는 영업이익 기준으로 만들고, 금융자산은 DCF에 따로 더했다"])
rp.thesis_box("③", f"가격은 회복을 이미 반영 — 목표주가 {TP:,}원, {RATING}",
              [f"2027E EPS {FB[1]['eps']:,.0f}원 × 피어 PER {B['per']:.1f}배 = {B['va']:,.0f}원, DCF + 금융자산 {B['vb']:,.0f}원",
               f"BUY(+15%)가 되려면 2027 영업이익률 {BY['need_m27']*100:.0f}%(2021년 최고 {PK['opm']*100:.0f}%) 또는 PER {BY['need_per']:.0f}배가 필요하다(6장)"])
rp.para(f"▶ 결론: 목표주가 {TP:,}원(A 60% · B 40%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. 원래 리포트(08-12, {O['rating']} {O['tp']:,}원) 이후 주가는 10-01 {R['hi_since']:,.0f}원까지 올랐다가 "
        f"3Q 잠정실적 발표(11-09) 뒤에도 내려 {PRICE:,.0f}원이 됐다. 본업 회복은 숫자로 확인됐지만, 지금 가격은 그 회복을 대부분 반영한다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.h2("1-1. 사업 소개")
rp.para("원익IPS(240810)는 반도체·디스플레이 장비 기업이다. 반도체 웨이퍼에 막을 입히는 증착 장비가 주력이고, 디스플레이 공정 장비도 판다. "
        "최대 고객은 국내 메모리·파운드리 기업이고, 장비는 고객의 설비투자 계획에 따라 발주돼 매출이 해마다 크게 바뀐다(2021년 1조 2,323억 → 2023년 6,903억 → 2025년 9,098억).")
rp.h2("1-2. 원래 리포트 이후 주요 공시")
sc = R["stock_comp"]
rp.table([["날짜", "공시", "내용"],
          ["2026-09-04", "임시주주총회 결과", "감사위원 독립이사 최근민(SK온 CPO, SK하이닉스 생산기술센터장 출신) 선임, 자기주식 보유·처분 계획 승인"],
          ["2026-09-15", "자기주식 처분 결정", f"직원 {sc['people']:,}명 주식보상으로 {sc['shares']:,}주 처분({sc['date']})"],
          ["2026-11-09", "3Q26 잠정실적", f"매출 {f0(Q['20263Q']['rev'])}억, 영업이익 {f0(Q['20263Q']['op'])}억"],
          ["2026-11-16", "3Q26 분기보고서", f"수주잔고 {f0(R['backlog'])}억, 공정가치 금융자산 {f0(R['fvpl'])}억(연초 1,082억)"]],
         [14, 20, 66], note="자료: DART.")

rp.h1("2. 실적 분석 (Performance Review)")
q3, q3p = Q["20263Q"], Q["20253Q"]
rp.kpi_tiles([("3Q26 매출", f"{f0(q3['rev'])}억", f"{q3['rev']/q3p['rev']-1:+.0%} YoY"),
              ("3Q26 영업이익", f"{f0(q3['op'])}억", f"영업이익률 {q3['op']/q3['rev']*100:.0f}%"),
              ("9M26 매출", f"{f0(R['m9']['매출'])}억", f"{R['m9']['매출']/R['m9p']['매출']-1:+.1%} YoY"),
              ("9M26 영업이익", f"{f0(R['m9']['영업이익'])}억", f"{R['m9']['영업이익']/R['m9p']['영업이익']-1:+.0%} YoY")])
rp.img(HERE / f"full_q_{TAG}.png", W)
rp.para(f"영업이익은 1Q26 {f0(Q['20261Q']['op'])}억 → 2Q26 {f0(Q['20262Q']['op'])}억 → 3Q26 {f0(q3['op'])}억으로 계속 늘었다. 반면 순이익은 2Q26 {f0(Q['20262Q']['ni'])}억, 3Q26 {f0(q3['ni'])}억으로 "
        "영업이익과 따로 움직였다. 당기손익-공정가치 금융자산이 연초 1,082억에서 9월 말 2,412억으로 커졌고, 그 평가손익이 분기 순이익을 크게 흔든 결과다.")
rp.h2("2-1. 연간 실적")
rp.img(HERE / f"full_earn_{TAG}.png", W)

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 수주잔고가 받치는 2027년")
rp.para(f"9월 말 수주잔고 {f0(R['backlog'])}억은 2026E 매출({f0(FB[0]['rev'])}억)의 {R['backlog']/FB[0]['rev']*100:.0f}%다. 기본 시나리오는 2027년 매출 {pc(SA['기본']['g27'],0)} 성장"
        f"({f0(FB[1]['rev'])}억), 영업이익률 {pc(SA['기본']['m27'],0)}다. 3Q26의 20%는 분기 정점에 가깝고, 2021년 연간 최고가 {PK['opm']*100:.0f}%였다는 점을 반영했다.")
rp.h2("Thesis 2. 가격은 피어와 같은 배수")
rp.img(HERE / f"full_band_{TAG}.png", W)
rp.para(f"지금 PBR {R['pbr']:.1f}배는 자기 밴드 중앙값({R['pband']['median']:.1f}배)과 상위 25%({R['pband']['q75']:.1f}배)보다 높다. 2027E 기본 EPS로 본 PER은 {R['per_27_now']:.1f}배로, "
        f"반도체 장비 피어 PER 중앙값 {R['peer_per_med']:.1f}배(TTM)보다 높다.")
rp.h2("Thesis 3. 현금흐름과 금융자산")
rp.para(f"DCF(5-3절)는 2027~2028년 영업이익률 {pc(SA['기본']['m27'],0)} 뒤 2036년 {pc(SA['기본']['m_lt'],0)}로 낮아지는 경로다. 할인율 {pc(R['wacc'])}에서 현금흐름 가치에 현금 {f0(R['cash'])}억과 "
        f"공정가치 금융자산 {f0(R['fvpl'])}억을 더해 주당 {B['vb']:,.0f}원이다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rows = [["항목 (기본, 억원)", "2025A", "9M26A", "2026E", "2027E", "2028E", "2030E", "2036E"]]
pick = [FB[0], FB[1], FB[2], FB[4], FB[-1]]
rows += [["매출액", f0(HI["2025"]["rev"]), f0(R["m9"]["매출"])] + [f0(r["rev"]) for r in pick],
         ["영업이익", f0(HI["2025"]["op"]), f0(R["m9"]["영업이익"])] + [f0(r["op"]) for r in pick],
         ["영업이익률", pc(HI["2025"]["op"] / HI["2025"]["rev"]), pc(R["m9"]["영업이익"] / R["m9"]["매출"])] + [pc(r["opm"]) for r in pick],
         ["순이익 (영업 기준)", f0(HI["2025"]["ni"]), f0(R["m9"]["지배순이익"])] + [f0(r["ni"]) for r in pick],
         ["FCFF", "-", "-"] + [f0(r["fcff"]) for r in pick]]
rp.table(rows, [18, 11, 11, 12, 12, 12, 12, 12], hl_cols=(3, 4, 5, 6, 7),
         note="FCFF = 영업이익 × (1 − 20%) + 감가상각(매출 3.7%) − 설비투자(매출 3.5%) − 운전자본 증가(매출 증가분의 15%).")
rp.table([["가정", "보수", "기본", "낙관"],
          ["4Q26 매출 / 영업이익률", *[f"{f0(SA[k]['q4'])}억 / {pc(SA[k]['q4m'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2027 매출 성장률", *[pc(SA[k]["g27"], 0) for k in ("보수", "기본", "낙관")]],
          ["2027~2028 영업이익률", *[pc(SA[k]["m27"], 0) for k in ("보수", "기본", "낙관")]],
          ["2036 영업이익률 (DCF)", *[pc(SA[k]["m_lt"], 0) for k in ("보수", "기본", "낙관")]],
          ["목표 PER", f"{L['per']:.0f}배", f"{B['per']:.1f}배 (피어 중앙)", f"{H['per']:.0f}배"]],
         [30, 23, 23, 24])

rp.h1("5. 밸류에이션 (Valuation)", new_page=False)
rp.para("반도체 장비는 선행 PER이 업종 표준이라 A(2027E EPS × 피어 PER 중앙값)에 60%를 두고, 업황 평균 마진으로 본 현금흐름과 금융자산 가치를 B(DCF)로 40% 반영한다.")
rp.h2("5-1. 할인율")
bt = R["beta"]
rp.table([["항목", "값", "근거"], ["무위험이자율", pc(R["rf"], 2), "국고채 10년, 2026-11-17 (ECOS)"],
          ["베타", f"{bt['blume']:.2f}", f"KOSDAQ 대비 2년 주간 원베타 {bt['raw']:.2f}, Blume 조정"],
          ["시장위험프리미엄", "7.0%", "다른 리포트와 같음"], ["WACC (= 자기자본비용)", pc(R["wacc"], 2), "차입 없음"], ["영구성장률", "2.0%", ""]], [22, 14, 64])
rp.h2("5-2. A. 선행 PER")
rp.para(f"2027E EPS {FB[1]['eps']:,.0f}원 × 피어 PER 중앙값 {B['per']:.1f}배 = **{B['va']:,.0f}원**.")
rp.table([["피어 (TTM 2Q26)", "PER", "PBR", "EV/EBITDA", "영업이익률"]] +
         [[p["name"], f"{p['PER']:.1f}배", f"{p['PBR']:.1f}배", f"{p['EV/EBITDA']:.1f}배", pc(p["OPM"], 0)] for p in R["peer"]], [28, 18, 18, 18, 18],
         note="tools/peers.py(stock_db 재무, 2Q26까지 4개 분기 합). 원익IPS 포함 6개 중앙값.")
rp.h2("5-3. B. DCF + 금융자산")
rp.para(f"4Q26~2036 FCFF 현재가치 {B['pv']:,.0f}억 + 영구가치 {B['tv']:,.0f}억 + 현금 {f0(R['cash'])}억 + 공정가치 금융자산 {f0(R['fvpl'])}억 → 주당 **{B['vb']:,.0f}원**.")
sd = R["sens_d"]
rp.table([["2036 영업이익률 \\ WACC"] + [pc(w, 1) for w in sd["wacc"]]] + [[pc(m, 0)] + [f0(x) for x in row] for m, row in zip(sd["m"], sd["v"])],
         [25, 18, 19, 19, 19], note="B 값(원).")
rp.h2("5-4. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. 선행 PER", "60%", f"{L['va']:,.0f} ({L['per']:.0f}배)", f"{B['va']:,.0f} ({B['per']:.1f}배)", f"{H['va']:,.0f} ({H['per']:.0f}배)"],
          ["B. DCF + 금융자산", "40%", f0(L["vb"]), f0(B["vb"]), f0(H["vb"])],
          ["목표주가", "", f0(L["tp"]), f"{B['tp']:,.0f} → {TP:,}", f0(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [24, 10, 22, 22, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / f"full_football_{TAG}.png", W)
rp.h2("5-5. 민감도 — 목표 PER × 2027 영업이익률 (목표주가)")
sp = R["sens_p"]
rp.table([["2027 마진 \\ PER"] + [f"{p:.1f}배" for p in sp["per"]]] + [[pc(m, 0)] + [f0(x) for x in row] for m, row in zip(sp["m"], sp["v"])],
         [20, 16, 16, 16, 16, 16], note="A 60 · B 40. 2027 매출은 기본(+15%).")

rp.h1("6. BUY가 되기 위한 조건", new_page=False)
rp.para(f"목표주가는 위 방법 그대로 두고, 지금 주가({PRICE:,.0f}원)에서 BUY(+15%, 목표주가 {BY['buy_price']:,.0f}원)가 되려면 무엇이 맞아야 하는지 거꾸로 계산했다. 목표가에는 넣지 않는다.")
rp.table([["조건", "필요한 값", "비교"],
          ["2027E 이익이 기본(EPS {:,.0f}원)일 때 목표 PER".format(BY["base_eps27"]), f"{BY['need_per']:.0f}배", f"피어 중앙 {R['peer_per_med']:.1f}배, 피어 최고 이오테크닉스 약 36배"],
          ["2027 매출이 기본일 때 영업이익률", f"{BY['need_m27']*100:.0f}% (영업이익 {f0(BY['need_op27_m'])}억)", f"최고 2021년 {PK['opm']*100:.0f}%, 3Q26 분기 20%"],
          ["영업이익률 18%일 때 2027 매출", f"{f0(BY['need_rev27'])}억 ({BY['need_g27']*100:+.0f}%)", f"최고 {PK['rev_y']}년 {f0(PK['rev'])}억의 {BY['need_rev27']/PK['rev']:.1f}배"],
          ["수주잔고 (9월 말)", f"{f0(R['backlog'])}억", f"필요 매출의 {R['backlog']/BY['need_rev27']*100:.0f}%"]],
         [38, 26, 36])
rp.h2("확인할 지표와 조건부 매수 가격")
rp.table([["이 조건이 확인되면", "적정가", "매수 추천 가격 (15% 여유)"]] +
         [[c["cond"], f0(c["px"] * 1.15), f"{c['px']:,.0f}원 이하"] for c in BY["cond"]], [56, 18, 26],
         note="매수 가격 = 그 조건에서의 목표주가 ÷ 1.15.")
rp.para("필요한 조건이 과거 최고 실적 근처라, 시장 기대가 지나치지 않은 편이다. 낙관 경로(분기 매출 3,500억 · 영업이익률 18%)가 두 분기 이어지면 적정가가 지금 주가 근처까지 올라온다. "
        "그 경로가 확인되면서 주가가 위 가격대에 있을 때가 안정적인 매수 시점이다.", 8.5)

rp.h1("7. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "고객 투자 확대", "국내 메모리 고객의 2027 투자 확대로 수주잔고가 늘면 2027 성장률·마진 상향", f"낙관 {H['tp']:,.0f}원"],
          ["상방", "금융자산 평가이익", f"공정가치 금융자산 {f0(R['fvpl'])}억의 평가이익은 순이익과 자본을 늘림", "B 상향"],
          ["하방", "고객 집중", "소수 고객 발주 시점에 따라 분기 실적 변동(1Q26 영업이익 107억)", f"보수 {L['tp']:,.0f}원"],
          ["하방", "금융자산 평가손실", "3Q26처럼 평가손실이 나면 순이익이 영업이익보다 크게 작아짐", "순이익 변동"]],
         [8, 18, 50, 24])
rp.h1("8. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {TP:,}원 (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {TP:,}원 · 보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"],
          ["BUY 조건", f"2027 영업이익률 {BY['need_m27']*100:.0f}% 또는 PER {BY['need_per']:.0f}배"],
          ["재검토 조건", "① 4Q26 영업이익과 수주잔고 ② 2027 고객 투자 계획 ③ 금융자산 평가손익"],
          ["결론", "본업 회복은 숫자로 확인됐고 재무도 튼튼하다. 다만 지금 가격은 그 회복을 이미 반영해, 낙관 경로가 확인되기 전까지는 매수 근거가 약하다."]], [20, 80])
rp.since("9", "2026-08-12",
         [["항목", "원래 리포트 (2026-08-12)", "재조사 (2026-11-18)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {O['tp']:,}원", f"{RATING} / {TP:,}원 (기준주가 {PRICE:,.0f}원)"],
          ["주가", f"{R['px_orig']:,.0f}원 (08-12 종가)", f"{PRICE:,.0f}원 ({R['chg_since']*100:+.1f}%, 10-01 고점 {R['hi_since']:,.0f}원)"],
          ["실적", "1H26까지", f"3Q26 영업이익 {f0(q3['op'])}억(영업이익률 20%), 수주잔고 {f0(R['backlog'])}억"],
          ["평가 방법", O["method"], "A. 2027E EPS × 피어 PER 60 + B. DCF + 금융자산 40, 'BUY가 되기 위한 조건' 추가"],
          ["대안 시나리오", "-", f"보수 {L['tp']:,.0f} · 낙관 {H['tp']:,.0f}원"]],
         [f"3Q26: 매출 {f0(q3['rev'])}억(+26% YoY), 영업이익 {f0(q3['op'])}억으로 2022년 이후 분기 최대.",
          f"순이익은 공정가치 금융자산(연초 1,082억 → 9월 말 {f0(R['fvpl'])}억) 평가손익으로 2Q 급증, 3Q 급감.",
          "임시주총(09-04) 독립이사 선임, 직원 주식보상 자기주식 처분(09-16).",
          f"주가: 08-12 {R['px_orig']:,.0f}원 → 10-01 {R['hi_since']:,.0f}원(최고) → 11-18 {PRICE:,.0f}원."],
         ["EPS를 영업이익 기준으로 만들고 금융자산 평가손익은 빼서 DCF에 자산으로 따로 더했다.",
          "목표 PER을 반도체 장비 피어 중앙값으로 두었다.",
          "지금 가격이 정당화되려면 무엇이 필요한지 'BUY가 되기 위한 조건' 장으로 보였다."],
         f"{O['tp']:,}원 → {TP:,}원. 실적은 좋아졌지만 2027E EPS에 피어 배수를 곱한 값({B['va']:,.0f}원)과 현금흐름 가치({B['vb']:,.0f}원) 모두 지금 주가보다 낮다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 DART 공시(분기보고서, 잠정실적, 임시주주총회 결과, 자기주식 처분), 한국은행 ECOS, FinanceDataReader(네이버 시세), yfinance(KOSDAQ, 베타), stock_db 재무(피어 배수)를 바탕으로 작성한 개인 분석 자료입니다.")
out = HERE / f"원익IPS_리서치리포트_{TAG}.docx"
rp.doc.save(out); print(out); to_pdf(out)
