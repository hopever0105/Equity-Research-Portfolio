"""대한광통신_리서치리포트_20261118.docx/.pdf — 2026-08-17 리포트를 2026-11-18 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_fdr.csv. 실행: python valuation/대한광통신/make_full_report_20261118.py
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
PRICE, TP, UP, RATING, O = R["price"], R["tp"], R["upside"], R["rating"], R["orig"]
HI, Q, SA, BY = R["hist"], R["q"], R["scen_assump"], R["buy"]
FB = B["rows"]
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
YRS = ["2022", "2023", "2024", "2025"]
TAG = "20261118"

px = pd.read_csv(HERE / "price_fdr.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / f"full_price_{TAG}.png", "최근 2년 종가(원), 기준일 2026-11-18", alt=[(H["tp"], "낙관")])
yrs = [f"{y}A" for y in YRS] + ["2026E", "2027E", "2028E"]
bar_chart(yrs, [("매출(억원)", [HI[y]["rev"] for y in YRS] + [r["rev"] for r in FB[:3]], "#1F3864"),
                ("영업이익(억원)", [HI[y]["op"] for y in YRS] + [r["op"] for r in FB[:3]], "#8FAADC")],
          HERE / f"full_earn_{TAG}.png", "매출·영업이익(억원)과 영업이익률 — 음영은 추정(기본, 2026E = 9M 실적 + 4Q 추정)", est_from=4,
          line=("영업이익률", [HI[y]["op"] / HI[y]["rev"] for y in YRS] + [r["opm"] for r in FB[:3]]))
ql = ["20251Q", "20252Q", "20253Q", "20254Q", "20261Q", "20262Q", "20263Q"]
bar_chart(["1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26"],
          [("매출", [Q[k]["rev"] for k in ql], "#1F3864"), ("영업이익", [Q[k]["op"] for k in ql], "#8FAADC")],
          HERE / f"full_q_{TAG}.png", "분기 매출·영업이익(억원)", ylab="억원")
football_chart([("A. DCF (FCFF, WACC %.1f%%)" % (R["wacc"] * 100), L["va"], B["va"], H["va"]), ("B. 2027E 매출 × EV/매출", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A·B 50:50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / f"full_football_{TAG}.png")

PK = BY["peak"]
SUB = f"두 분기 연속 영업흑자, 그러나 기업가치는 2027E 매출의 {R['evs_27_now']:.1f}배 — BUY가 되려면 매출의 {BY['need_evs']:.0f}배를 쳐줘야 한다"
MKT = [["현재주가 (2026.11.18 종가)", f"{PRICE:,.0f}원"], ["시가총액", f"{R['mcap']/1e4:.1f}조원"],
       ["발행주식 (9월 말)", f"{R['sh']:,}주"], ["52주 최고 / 최저 (장중)", f"{R['hi52']:,.0f} / {R['lo52']:,.0f}원"],
       ["EV / 2027E 매출", f"{R['evs_27_now']:.1f}배"], ["PBR (9월 말 지배자본)", f"{R['pbr']:.1f}배"],
       ["9M26 매출 / 영업이익", f"{f0(R['m9']['매출'])}억 / {f0(R['m9']['영업이익'])}억"], ["순차입 (9월 말, 리스 포함)", f"{f0(R['net_debt'])}억"],
       ["수주잔고 (9월 말)", f"{f0(R['backlog']['total'])}억"], ["원래 리포트 (2026.08.17)", f"{O['rating']} · {O['tp']:,}원"]]
ALT = [f"보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"]

rp = Rep("광섬유·광케이블", "2026년 11월 18일")
rp.cover("대한광통신 (010170 KS)", SUB, RATING, TP, PRICE, UP, "원", HERE / f"full_price_{TAG}.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, 연결 기준)")
rows = [["항목 (억원)", "2022A", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출액"] + [f0(HI[y]["rev"]) for y in YRS] + [f0(r["rev"]) for r in FB[:3]],
        ["영업이익"] + [f0(HI[y]["op"]) for y in YRS] + [f0(r["op"]) for r in FB[:3]],
        ["영업이익률"] + [pc(HI[y]["op"] / HI[y]["rev"]) for y in YRS] + [pc(r["opm"]) for r in FB[:3]],
        ["지배주주 순이익"] + [f0(HI[y]["ni"]) for y in YRS] + [f0(r["ni"]) for r in FB[:3]]]
rp.table(rows, [22, 11, 11, 11, 11, 11, 11, 12], hl_cols=(5, 6, 7),
         note=f"자료: DART 연결재무제표. 2026E = 9M 실적 + 4Q 추정. 2027E 이후 순이익 = (영업이익 − 이자 {R['debt']*R['kd']:.0f}억) × (1 − 20%).")
rp.page_break()
rp.h2("핵심 투자 포인트")
ex = R["export"]
rp.thesis_box("①", "흑자로 돌아섰다 — 3Q26 매출 603억, 영업이익 29억",
              [f"3Q26 매출 +39% YoY, 2Q26에 이어 두 분기 연속 영업흑자. 매출총이익률 21%(3Q25 1%)",
               f"9M26 수출 {f0(ex['m9_exp'])}억(매출의 {ex['m9_exp']/R['m9']['매출']*100:.0f}%), 그중 통신 수출 {f0(ex['m9_tel_exp'])}억은 2025년 연간({f0(ex['fy25_tel_exp'])}억)을 이미 넘었다"])
rp.thesis_box("②", f"그러나 기업가치는 2027E 매출의 {R['evs_27_now']:.1f}배 — 피어는 0.7~2.1배",
              [f"PBR {R['pbr']:.0f}배. 대형 전선사(대한전선·LS에코에너지)는 EV/매출 1배 안팎이다",
               f"주식 수가 2025년 말 {R['sh_2025']:,}주에서 9월 말 {R['sh']:,}주로 {R['sh']/R['sh_2025']*100-100:.0f}% 늘었다"])
rp.thesis_box("③", f"목표주가 {TP:,}원, {RATING} — BUY에는 2027 매출 {f0(BY['need_rev27_evs3'])}억이 필요",
              [f"DCF {B['va']:,.0f}원, 2027E 매출 {f0(FB[1]['rev'])}억 × EV/매출 3배 {B['vb']:,.0f}원",
               f"EV/매출 3배를 유지하며 BUY가 되려면 2027 매출이 {f0(BY['need_rev27_evs3'])}억(최고 {PK['rev_y']}년의 {BY['need_rev27_evs3']/PK['rev']:.1f}배)이어야 한다(6장)"])
rp.para(f"▶ 결론: 목표주가 {TP:,}원(A. DCF {B['va']:,.0f}원 · B. EV/매출 {B['vb']:,.0f}원, 50:50), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(08-17, {O['rating']} {O['tp']:,}원) 이후 주가는 10-06 {R['hi_since']:,.0f}원까지 올랐다가 {PRICE:,.0f}원이 됐다. 흑자 전환은 확인됐지만 이익 규모가 아직 작다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.h2("1-1. 사업 소개")
rp.para("대한광통신(010170)은 광섬유의 원재료인 프리폼부터 광섬유, 광케이블까지 만드는 수직계열화 기업이다. 통신사·데이터센터용 광케이블이 주력이고 전력선 사업도 있다. "
        "광섬유 가격이 오를 때만 이익이 났고, 2021~2025년 중 영업흑자는 2022년(35억) 한 해였다. 2026년에는 해외 통신 수요가 늘며 2분기부터 흑자로 돌아섰다.")
rp.h2("1-2. 자본과 주식 수")
rp.para(f"2026년 1분기에 자본이 667억에서 1,160억으로 늘었고, 발행주식은 {R['sh_2025']:,}주 → {R['sh']:,}주가 됐다(자기주식 없음). "
        f"9월 말 차입금은 리스 포함 약 {f0(R['debt'])}억, 현금 {f0(R['cash'])}억으로 순차입 {f0(R['net_debt'])}억이다.")
bk = R["backlog"]
rp.table([["9월 말 수주잔고 (억원)", "통신", "전력", "합계"], ["잔고", f0(bk["telecom"]), f0(bk["power"]), f0(bk["total"])]], [40, 20, 20, 20],
         note="자료: 3Q26 분기보고서.")

rp.h1("2. 실적 분석 (Performance Review)")
q3, q3p = Q["20263Q"], Q["20253Q"]
rp.kpi_tiles([("3Q26 매출", f"{f0(q3['rev'])}억", f"{q3['rev']/q3p['rev']-1:+.0%} YoY"),
              ("3Q26 영업이익", f"{f0(q3['op'])}억", f"영업이익률 {q3['op']/q3['rev']*100:.0f}%"),
              ("9M26 매출", f"{f0(R['m9']['매출'])}억", f"{R['m9']['매출']/R['m9p']['매출']-1:+.1%} YoY"),
              ("9M26 영업이익", f"{f0(R['m9']['영업이익'])}억", f"전년 {f0(R['m9p']['영업이익'])}억")])
rp.img(HERE / f"full_q_{TAG}.png", W)
rp.para(f"매출은 1Q26 {f0(Q['20261Q']['rev'])}억 → 2Q26 {f0(Q['20262Q']['rev'])}억 → 3Q26 {f0(q3['rev'])}억으로 늘었고 영업이익도 −40억 → 10억 → 29억으로 좋아졌다. "
        f"다만 3Q26 순이익은 이자비용 등으로 {f0(q3['ni'])}억 적자다.")
rp.h2("2-1. 연간 실적")
rp.img(HERE / f"full_earn_{TAG}.png", W)

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 수출 주문이 바꾼 매출")
rp.para(f"통신 수출이 9개월 {f0(ex['m9_tel_exp'])}억으로 늘어 회사 매출 구조가 바뀌었다. 기본 시나리오는 2027년 매출 {pc(SA['기본']['g27'],0)} 성장({f0(FB[1]['rev'])}억), "
        f"영업이익률 {pc(SA['기본']['m27'],0)}이고, 장기(2036년) 영업이익률은 {pc(SA['기본']['m_lt'],0)}로 둔다. 과거 대부분 적자였던 점을 감안해 광섬유 가격 강세가 길게 이어진다고 보지 않았다.")
rp.h2("Thesis 2. 가격은 이익보다 한참 앞서 있다")
rp.table([["피어 (TTM 2Q26)", "PBR", "EV/EBITDA", "EV/매출", "영업이익률"]] +
         [[p["name"], f"{p['PBR']:.1f}배", (f"{p['EV/EBITDA']:.1f}배" if p["EV/EBITDA"] and p["EV/EBITDA"] > 0 else "적자"), f"{p['EV/Sales']:.1f}배", pc(p["OPM"], 0)] for p in R["peer"]],
         [28, 18, 18, 18, 18], note="tools/peers.py(stock_db 재무, 2Q26까지 4개 분기 합).")
rp.para(f"지금 기업가치는 2027E 매출의 {R['evs_27_now']:.1f}배다. 흑자를 내는 대형 전선사는 1배 안팎, 광통신 부품사(우리로·오이솔루션)도 3.7~4.7배다. 목표 EV/매출 3배는 피어보다 높게, AI 데이터센터 광통신 수요를 반영한 값이다.")
rp.h2("Thesis 3. 현금흐름이 말하는 값")
rp.para(f"DCF(5-3절)는 2036년까지 매출이 연 3~12% 늘고 영업이익률이 {pc(SA['기본']['m_lt'],0)}까지 오른다고 봐도 주당 {B['va']:,.0f}원이다. 이익 규모가 작은 데 비해 차입 이자와 운전자본 부담이 크다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rows = [["항목 (기본, 억원)", "2025A", "9M26A", "2026E", "2027E", "2028E", "2030E", "2036E"]]
pick = [FB[0], FB[1], FB[2], FB[4], FB[-1]]
rows += [["매출액", f0(HI["2025"]["rev"]), f0(R["m9"]["매출"])] + [f0(r["rev"]) for r in pick],
         ["영업이익", f0(HI["2025"]["op"]), f0(R["m9"]["영업이익"])] + [f0(r["op"]) for r in pick],
         ["영업이익률", pc(HI["2025"]["op"] / HI["2025"]["rev"]), pc(R["m9"]["영업이익"] / R["m9"]["매출"])] + [pc(r["opm"]) for r in pick],
         ["FCFF", "-", "-"] + [f0(r["fcff"]) for r in pick]]
rp.table(rows, [18, 11, 11, 12, 12, 12, 12, 12], hl_cols=(3, 4, 5, 6, 7),
         note="FCFF = 영업이익 × (1 − 20%) + 감가상각(매출 4%) − 설비투자(매출 3.5%) − 운전자본 증가(매출 증가분의 20%).")
rp.table([["가정", "보수", "기본", "낙관"],
          ["4Q26 매출 / 영업이익률", *[f"{f0(SA[k]['q4'])}억 / {pc(SA[k]['q4m'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2027 매출 성장률", *[pc(SA[k]["g27"], 0) for k in ("보수", "기본", "낙관")]],
          ["2027 영업이익률", *[pc(SA[k]["m27"], 0) for k in ("보수", "기본", "낙관")]],
          ["2036 영업이익률 (DCF)", *[pc(SA[k]["m_lt"], 0) for k in ("보수", "기본", "낙관")]],
          ["목표 EV/매출", *[f"{SA[k]['evs']:.0f}배" for k in ("보수", "기본", "낙관")]]], [30, 23, 23, 24])

rp.h1("5. 밸류에이션 (Valuation)", new_page=False)
rp.para("막 흑자로 돌아선 단계라 PER은 의미가 없다. A(DCF)로 장기 현금흐름을, B(2027E 매출 × 목표 EV/매출 − 순차입)로 피어와 비교한 값을 보고 50:50으로 섞는다.")
rp.h2("5-1. 할인율")
bt = R["beta"]
rp.table([["항목", "값", "근거"], ["무위험이자율", pc(R["rf"], 2), "국고채 10년, 2026-11-17 (ECOS)"],
          ["베타", f"{bt['blume']:.2f}", f"KOSDAQ 대비 2년 주간 원베타 {bt['raw']:.2f}, Blume 조정"],
          ["자기자본비용", pc(R["coe"], 2), "무위험 + 베타 × 7%"], ["세후 차입비용", pc(R["kd"] * 0.8, 2), f"이자율 {pc(R['kd'],1)} × (1 − 20%)"],
          ["WACC", pc(R["wacc"], 2), "시가총액·차입 비중으로 가중"], ["영구성장률", "2.0%", ""]], [22, 14, 64])
rp.h2("5-2. A. DCF")
rp.para(f"4Q26~2036 FCFF 현재가치 {B['pv']:,.0f}억 + 영구가치 {B['tv']:,.0f}억 − 순차입 {f0(R['net_debt'])}억 → 주당 **{B['va']:,.0f}원**.")
sd = R["sens_d"]
rp.table([["2036 영업이익률 \\ WACC"] + [pc(w, 1) for w in sd["wacc"]]] + [[pc(m, 0)] + [f0(x) for x in row] for m, row in zip(sd["m"], sd["v"])],
         [25, 18, 19, 19, 19], note="A 값(원).")
rp.h2("5-3. B. EV/매출")
rp.para(f"2027E 매출 {f0(FB[1]['rev'])}억 × 3배 − 순차입 {f0(R['net_debt'])}억 → 주당 **{B['vb']:,.0f}원**.")
rp.h2("5-4. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. DCF", "50%", f0(L["va"]), f0(B["va"]), f0(H["va"])],
          ["B. EV/매출", "50%", f"{L['vb']:,.0f} ({L['evs']:.0f}배)", f"{B['vb']:,.0f} ({B['evs']:.0f}배)", f"{H['vb']:,.0f} ({H['evs']:.0f}배)"],
          ["목표주가", "", f0(L["tp"]), f"{B['tp']:,.0f} → {TP:,}", f0(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [24, 10, 22, 22, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / f"full_football_{TAG}.png", W)
rp.h2("5-5. 민감도 — 목표 EV/매출 × 2027 매출 성장률 (목표주가)")
sp = R["sens_p"]
rp.table([["2027 성장 \\ EV/매출"] + [f"{e:.0f}배" for e in sp["evs"]]] + [[pc(g, 0)] + [f0(x) for x in row] for g, row in zip(sp["g"], sp["v"])],
         [20, 16, 16, 16, 16, 16], note="A·B 50:50.")

rp.h1("6. BUY가 되기 위한 조건", new_page=False)
rp.para(f"목표주가는 위 방법 그대로 두고, 지금 주가({PRICE:,.0f}원)에서 BUY(+15%, 목표주가 {BY['buy_price']:,.0f}원)가 되려면 무엇이 맞아야 하는지 거꾸로 계산했다. 목표가에는 넣지 않는다.")
rp.table([["조건", "필요한 값", "비교"],
          ["2027E 매출이 기본({:,.0f}억)일 때 EV/매출".format(BY["base_rev27"]), f"{BY['need_evs']:.0f}배", f"피어 최고 {BY['peer_evs_max']:.1f}배(우리로), 대형 전선사 1배 안팎"],
          ["EV/매출 3배일 때 2027 매출 (B만으로)", f"{f0(BY['need_rev27_evs3'])}억", f"최고 {PK['rev_y']}년 {f0(PK['rev'])}억의 {BY['need_rev27_evs3']/PK['rev']:.1f}배"],
          ["2027 영업이익률 10%일 때 필요한 장기 마진 (DCF)", "100%를 넘어도 부족" if BY["need_mlt"] is None else pc(BY["need_mlt"], 0), "2021~2025년 최고 영업이익률 1.8%(2022년)"],
          ["수주잔고 (9월 말)", f"{f0(R['backlog']['total'])}억", f"필요 매출의 {R['backlog']['total']/BY['need_rev27_evs3']*100:.0f}%"]],
         [38, 26, 36])
rp.h2("확인할 지표와 조건부 매수 가격")
rp.table([["이 조건이 확인되면", "적정가", "매수 추천 가격 (15% 여유)"]] +
         [[c["cond"], f0(c["px"] * 1.15), f"{c['px']:,.0f}원 이하"] for c in BY["cond"]], [56, 18, 26],
         note="매수 가격 = 그 조건에서의 목표주가 ÷ 1.15.")
rp.para("지금 주가는 회사가 지금보다 몇 배 큰 매출을 내며 높은 마진을 오래 유지한다는 가정 위에 있다. 안정적인 관점에서는 이익이 몇 분기 더 쌓이는 것을 확인하는 편이 낫다.", 8.5)

rp.h1("7. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "AI 데이터센터 수요", "데이터센터 광케이블 수요가 예상보다 크면 매출·마진 동시 상향", f"낙관 {H['tp']:,.0f}원"],
          ["상방", "광섬유 가격 상승", "광섬유 가격이 오르는 구간에서 마진이 크게 개선된 적이 있음", "마진 상향"],
          ["하방", "가격 하락·공급 과잉", "광섬유 가격이 내리면 적자로 돌아갈 수 있음(2023~2025 적자)", f"보수 {L['tp']:,.0f}원"],
          ["하방", "추가 증자", "2026년 주식 수 18% 증가 — 운전자본·설비 자금이 더 필요하면 추가 증자 가능", "주당 가치 희석"]],
         [8, 18, 50, 24])
rp.h1("8. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {TP:,}원 (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {TP:,}원 · 보수 {L['tp']:,.0f}원 · 낙관 {H['tp']:,.0f}원"],
          ["BUY 조건", f"2027E 매출에 EV/매출 {BY['need_evs']:.0f}배, 또는 3배 기준 2027 매출 {f0(BY['need_rev27_evs3'])}억"],
          ["재검토 조건", "① 4Q26 흑자 유지 여부 ② 통신 수출 수주잔고 ③ 추가 자금 조달"],
          ["결론", "흑자 전환과 수출 증가는 사실이지만 이익 규모가 아직 작고, 주가는 그보다 훨씬 큰 미래를 반영한다."]], [20, 80])
rp.since("9", "2026-08-17",
         [["항목", "원래 리포트 (2026-08-17)", "재조사 (2026-11-18)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {O['tp']:,}원", f"{RATING} / {TP:,}원 (기준주가 {PRICE:,.0f}원)"],
          ["주가", f"{R['px_orig']:,.0f}원 (08-14 종가)", f"{PRICE:,.0f}원 ({R['chg_since']*100:+.1f}%, 10-06 고점 {R['hi_since']:,.0f}원)"],
          ["실적", "1H26까지 (2Q 흑자 전환)", f"3Q26 매출 {f0(q3['rev'])}억 · 영업이익 {f0(q3['op'])}억"],
          ["평가 방법", O["method"], "A. DCF 50 + B. EV/매출 3배 50, 'BUY가 되기 위한 조건' 추가"],
          ["대안 시나리오", "-", f"보수 {L['tp']:,.0f} · 낙관 {H['tp']:,.0f}원"]],
         [f"3Q26: 매출 {f0(q3['rev'])}억(+39% YoY), 두 분기 연속 영업흑자, 매출총이익률 21%.",
          f"9M26 통신 수출 {f0(ex['m9_tel_exp'])}억으로 2025년 연간({f0(ex['fy25_tel_exp'])}억) 초과.",
          f"주식 수 {R['sh_2025']:,} → {R['sh']:,}주(+{R['sh']/R['sh_2025']*100-100:.0f}%).",
          f"주가: 08-14 {R['px_orig']:,.0f}원 → 10-06 {R['hi_since']:,.0f}원(최고) → 11-18 {PRICE:,.0f}원."],
         ["피어 EV/매출을 새로 모아 목표 배수를 정했다(피어 최고보다 높은 3배).",
          "장기 영업이익률을 과거 실적(대부분 적자~2%)을 감안해 10%로 두었다.",
          "지금 가격이 정당화되려면 무엇이 필요한지 'BUY가 되기 위한 조건' 장으로 보였다."],
         f"{O['tp']:,}원 → {TP:,}원. 흑자 전환은 확인됐지만 DCF 가치가 {B['va']:,.0f}원, 피어보다 높은 배수를 줘도 {B['vb']:,.0f}원이다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 DART 공시(분기보고서), 한국은행 ECOS, FinanceDataReader(네이버 시세), yfinance(KOSDAQ, 베타), stock_db 재무(피어 배수)를 바탕으로 작성한 개인 분석 자료입니다.")
out = HERE / f"대한광통신_리서치리포트_{TAG}.docx"
rp.doc.save(out); print(out); to_pdf(out)
