"""일라이릴리_리서치리포트_20261109.docx/.pdf — 2026-10-15 리포트를 2026-11-09 기준으로 다시 조사한 후속 리포트.
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_yf.csv. 실행: python valuation/일라이릴리/make_full_report.py
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
A_, Qk, Y9, P3 = K["annual"], K["quarterly"], K["ytd_9m26"], K["q3_26_press"]
GN, GP = K["guidance_2026"]["20261029"], K["guidance_2026"]["prior"]
PR = P3["products_3q"]
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
          "분기 매출($B)과 순이익률(GAAP, 인수 IPR&D 포함)", line=("순이익률", [Qk["net_income"][q] / Qk["revenue"][q] for q in ql]), ylab="$B")
yrs = ["2023A", "2024A", "2025A", "2026E", "2027E", "2028E", "2029E"]
revs = [A_["revenue"][y] for y in ("2023", "2024", "2025")] + [r["rev"] for r in FB[:4]]
bar_chart(yrs, [("매출($B)", [v / 1e3 for v in revs], "#1F3864")], HERE / "full_earn.png", "연간 매출($B)과 성장률 — 음영은 추정(기본, 2026E = 가이던스 중간값)", est_from=3,
          line=("매출 성장률", [0.0] + [revs[i] / revs[i - 1] - 1 for i in range(1, len(revs))]))
football_chart([("A. DCF (WACC %.1f%%)" % (R["wacc"] * 100), L["va"], B["va"], H["va"]), ("B. 2027E EPS × 제약 피어 선행 PER", L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A 50 : B 50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$")

SUB = f"매출 +39%·가이던스 $5.5B 상향 — 현재가는 2029년에도 매출이 {R['implied_g']*100:.0f}% 늘어야 맞는 가격"
MKT = [["현재주가 (2026.11.09 종가)", u2(PRICE)], ["시가총액 (희석 894백만주)", f"${R['mcap']/1e6:,.2f}T"], ["순차입 (9월말)", b(R["net_debt"])],
       ["52주 최고 / 최저 (장중)", f"{u2(R['hi52'])} / {u2(R['lo52'])}"], ["PER (2026E 기초 EPS, IPR&D 제외)", f"{R['per26_now']:.1f}배"],
       ["PER (2027E 기본)", f"{R['per27_now']:.1f}배"], ["제약 피어 선행 PER 중앙값", f"{R['fpe_med']:.1f}배"],
       ["2026 매출 가이던스", f"${GN['revenue'][0]/1e3:.0f}~{GN['revenue'][1]/1e3:.0f}B"], ["3Q26 가격 효과", "−15% (물량 +53%)"], ["원래 리포트 (2026.10.15)", f"{O['rating']} · {usd(O['tp'])}"]]
ALT = [f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]

rp = Rep("글로벌 헬스케어 (GLP-1)", "2026년 11월 9일")
rp.cover("일라이릴리 (Eli Lilly, NYSE: LLY)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, $M)")
rows = [["항목", "2023A", "2024A", "2025A", "2026E", "2027E", "2028E"],
        ["매출"] + [f0(A_["revenue"][y]) for y in ("2023", "2024", "2025")] + [f0(r["rev"]) for r in FB[:3]],
        ["매출 성장률"] + ["-", pc(A_["revenue"]["2024"] / A_["revenue"]["2023"] - 1), pc(A_["revenue"]["2025"] / A_["revenue"]["2024"] - 1)] + [pc(r["g"]) for r in FB[:3]],
        ["성과마진 (원가·연구개발·판관비 차감)"] + ["-", "-", "-"] + [pc(r["pm"]) for r in FB[:3]],
        ["순이익"] + [f0(A_["net_income"][y]) for y in ("2023", "2024", "2025")] + [f0(r["ni"]) for r in FB[:3]],
        ["희석 EPS ($)"] + [f"{A_['eps_diluted'][y]:.2f}" for y in ("2023", "2024", "2025")] + [f"{r['eps']:.2f}" for r in FB[:3]]]
rp.table(rows, [28, 11, 11, 11, 13, 13, 13], hl_cols=(4, 5, 6),
         note=f"자료: SEC 10-K·10-Q·8-K. 2026E = 회사 가이던스 중간값(매출 $91.5B, 성과마진 52.25%, 비GAAP EPS $35.50 — 9월까지의 인수 IPR&D 주당 ${R['iprd26_ps']:.2f} 포함). "
              f"2027E부터는 인수 IPR&D를 정상 연 $3B로 둔다.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", f"성장은 여전히 압도적 — 3Q 매출 +39%, Mounjaro {b(PR['Mounjaro'][0])}(+65%)·Zepbound {b(PR['Zepbound'][0])}(+49%)",
              [f"2026 매출 가이던스 $85~87B → $91~92B, 성과마진 49.0~50.5% → 52.0~52.5%",
               "신제품(Jaypirca·Ebglyss·Kisunla·Omvoh·Foundayo·Inluriyo) 매출 두 배, 레타트루타이드 3상 긍정적"])
rp.thesis_box("②", "그러나 가격은 내려가고, 3Q에는 일회성 도움이 $0.9B",
              [f"3Q 물량 +53%, 가격 −15%(미국 −7%, 해외 −29%). 중국 국가 보험약 목록(NRDL) 등재로 해외 가격 하락",
               f"Jardiance 마일스톤 $410M(더 이상 없음)·리베이트 추정 조정 등 약 $900M이 3Q 매출에 포함 — 2027년 성장률 기저 부담"])
rp.thesis_box("③", f"현재가는 2027E EPS의 {R['per27_now']:.1f}배 — 제약 피어 중앙값 {R['fpe_med']:.1f}배",
              [f"노보노디스크·애브비·머크·아스트라제네카·J&J·암젠·버텍스·리제네론 선행 PER {min(R['fpe'].values()):.1f}~{max(R['fpe'].values()):.1f}배(11-09)",
               f"DCF(WACC {pc(R['wacc'])})로 현재가를 맞추려면 2027년 +20%, 2028년 +14% 뒤 2029년에도 매출이 {pc(R['implied_g'],0)} 늘어야 한다"])
rp.para(f"▶ 결론: 목표주가 {usd(TP)}(A. DCF {usd(B['va'])} × 50% + B. 2027E EPS ${FB[1]['eps']:.2f} × {B['mult']:.1f}배 {usd(B['vb'])} × 50%), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"원래 리포트(10-15, {O['rating']} {usd(O['tp'])}) 뒤 3분기 실적과 가이던스 상향으로 주가는 {R['chg_since']*100:+.1f}% 올라 {u2(PRICE)}가 됐다. 사업은 원래 예상보다 좋아졌지만, "
        f"자체 이익 추정(2027E EPS ${FB[1]['eps']:.2f}, 원래 리포트 가정 $48.29와 거의 같음)을 기준으로 하면 오른 주가가 그 이상을 반영했다. 낙관 시나리오도 {usd(H['tp'])}다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.para("일라이릴리는 미국 최대 제약회사로, GLP-1 계열 당뇨·비만 치료제 터제파타이드(당뇨 Mounjaro, 비만 Zepbound)가 매출의 약 3분의 2를 차지한다. "
        "경구 비만약 Foundayo, 3중 작용제 레타트루타이드(2027년 허가 신청 예정, 원래 리포트), 면역·항암·신경과학 신제품이 다음 성장 축이다.")
rp.table([["제품 (3Q26)", "매출", "증가율", "내용"]] +
         [[k, f0(v[0]), pc(v[1], 0) if v[1] is not None else "신규", d] for (k, v), d in zip(PR.items(),
          ["미국 $5.0B(+41%), 해외 $5.7B(+93%)", "미국 비만, 가격 하락을 물량이 상쇄", "BTK 억제제, CLL 1차 치료 확대", "아토피 피부염", "알츠하이머", "궤양성 대장염", "경구 GLP-1 비만약", "유방암(Verzenio 병용)"])],
         [18, 14, 12, 56], note="자료: 8-K 3Q26 보도자료(10-29). 매출 단위 $M.")
rp.h2("1-1. 원래 리포트 이후 주요 사건")
rp.table([["날짜", "사건", "내용"],
          ["2026-10-14", "원래 리포트 기준", f"종가 {u2(R['px_orig'])}"],
          ["2026-10-29", "3Q26 실적·가이던스 상향", f"매출 $24.4B(+39%), 매출 가이던스 +$5.5B. 주가 {(R['px_earn']/R['px_pre']-1)*100:+.1f}%"],
          ["3Q~10월", "사업개발", "AtaiBeckley·Curevo 인수(3Q IPR&D $4.2B), 분기 후 Merida Biosciences 인수 완료"],
          ["3Q~10월", "허가", "Mounjaro 심혈관 위험 감소, Onswik(주 1회 기저 인슐린), Inluriyo, Jaypirca 확대 — FDA 승인"],
          ["2026-11-04", "주가 고점", f"종가 {u2(R['hi_since'])}"],
          ["2026-11-09", "기준일", f"종가 {u2(PRICE)}"]],
         [15, 22, 63], note="자료: SEC 8-K, yfinance 종가.")
rp.h2("1-2. 재무 상태 (2026-09-30)")
bb = K["balance_20260930"]
rp.table([["항목", "금액", "의미"], ["현금", b(bb["cash"]), "6월말 $9.0B → 인수에 사용"], ["차입", b(R["debt"]), "2024년 이후 설비·인수로 증가"],
          ["순차입", b(R["net_debt"]), f"시가총액의 {R['net_debt']/R['mcap']:.1%}"], ["희석주식", f"{R['sh_dil']}백만주", "회사 가이던스 가정"]], [22, 18, 60])

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("3Q26 매출", b(Qk["revenue"]["3Q26"]), "+39%"), ("3Q26 비GAAP EPS", f"${Qk['eps_nongaap']['3Q26']:.2f}", f"IPR&D ${Qk['ipr_d_per_share']['3Q26']:.2f} 포함"),
              ("비GAAP 매출총이익률", pc(P3["gross_margin_nongaap"]), "+1.0%p"), ("9M 인수 IPR&D", b(Y9["ipr_d"]), f"전년 {b(Y9['ipr_d_9m25'])}")])
rp.img(HERE / "full_q.png", W)
rp.table([["2026 가이던스", "직전(8월)", "10-29 (상향)"],
          ["매출", f"${GP['revenue'][0]/1e3:.0f}~{GP['revenue'][1]/1e3:.0f}B", f"${GN['revenue'][0]/1e3:.0f}~{GN['revenue'][1]/1e3:.0f}B"],
          ["성과마진", f"{pc(GP['perf_margin'][0])}~{pc(GP['perf_margin'][1])}", f"{pc(GN['perf_margin'][0])}~{pc(GN['perf_margin'][1])}"],
          ["세율", f"{pc(GP['tax'][0],0)}~{pc(GP['tax'][1],0)}", f"{pc(GN['tax'][0],0)}~{pc(GN['tax'][1],0)}"],
          ["비GAAP EPS", f"${GP['eps'][0]}~{GP['eps'][1]}", f"${GN['eps'][0]}~{GN['eps'][1]} (기초 +$4.07, 3Q IPR&D −$4.57)"]], [26, 30, 44],
         note="자료: 8-K 3Q26 보도자료. EPS 가이던스는 10-01 이후 인수 IPR&D를 포함하지 않는다.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 물량 대 가격 — 성장률은 내려간다")
rp.para("3분기 매출 증가 39%는 물량 +53%와 가격 −15%의 합이다. 비만약 보험 적용이 넓어지고 중국 NRDL 등재·경구약 출시로 처방이 늘수록 단가는 내려간다. "
        f"여기에 3분기에만 있던 일회성 도움($0.9B)이 빠지면 2027년 성장률은 2026년(+{pc(FB[0]['g'],0)})보다 크게 낮아진다. 이 리포트는 2027년 +20%, 2028년 +14%를 기본으로 잡았다.")
rp.h2("Thesis 2. 마진은 이미 정점권")
rp.para(f"성과마진 가이던스 52.0~52.5%는 원가 개선과 매출 규모 효과의 결과다. 연구개발비도 +23%로 늘고 있어, 이 리포트는 2032년까지 52%를 유지한 뒤 "
        f"터제파타이드 특허 만료가 가까워지는 구간(이 리포트 가정: 2033~2036년)에서 {pc(SA['기본']['pm_lt'],0)}로 내려간다고 가정했다. 매년 반복되는 인수 IPR&D는 정상 연 $3B로 뺐다.")
rp.h2("Thesis 3. 피어와 비교한 가격")
pe = R["peers"]
rp.table([["회사", "선행 PER", "매출 성장"]] +
         [[pe[t]["shortName"].strip()[:30], f"{pe[t]['forwardPE']:.1f}", pc(pe[t]["revenueGrowth"])] for t in pe] +
         [["중앙값", f"{R['fpe_med']:.1f}", ""], ["일라이릴리 (현재가, 2027E 기본)", f"{R['per27_now']:.1f}", "+39% (3Q)"]],
         [46, 27, 27], hl_rows=(len(pe) + 2,), note="자료: yfinance(2026-11-10 조회 = 11-09 종가 기준). 노보노디스크의 EV/EBITDA 등 일부 지표는 자료 오류로 보여 PER만 비교. 일라이릴리 줄은 이 리포트 추정.")
rp.para(f"성장률이 훨씬 높은 만큼 피어보다 높은 배수는 정당하다. 다만 현재 2027E {R['per27_now']:.0f}배는 피어 상위 25%({R['mult']['1']:.1f}배)보다 약 {R['per27_now']/R['mult']['1']-1:.0%} 높다. "
        "경쟁사 노보노디스크는 12배다 — 같은 GLP-1 시장에서도 성장이 꺾이면 배수가 얼마나 빨리 줄어드는지 보여준다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.img(HERE / "full_earn.png", W)
pick = [FB[0], FB[1], FB[2], FB[4], FB[7], FB[-1]]
rp.table([["항목 (기본, $M)", "2026E", "2027E", "2028E", "2030E", "2033E", "2036E"],
          ["매출"] + [f0(r["rev"]) for r in pick], ["매출 성장률"] + [pc(r["g"]) for r in pick],
          ["성과마진"] + [pc(r["pm"]) for r in pick], ["순이익"] + [f0(r["ni"]) for r in pick],
          ["FCFF", "-"] + [f0(r["fcff"]) for r in pick[1:]], ["희석 EPS ($)"] + [f"{r['eps']:.2f}" for r in pick]],
         [22, 13, 13, 13, 13, 13, 13], hl_rows=(1,))
rp.para(f"순이익 = (매출 × 성과마진 − 인수 IPR&D $3B − 순이자 $1.3B) × (1 − 19%). FCFF = 순이익 × 현금전환율(2027 70% → 2030 이후 85%, 텍사스·버지니아 등 공장 증설로 설비투자가 큼) + 세후 이자. "
        f"2027E EPS ${FB[1]['eps']:.2f}는 원래 리포트 가정($48.29)과 거의 같다.")
rp.table([["가정", "보수", "기본", "낙관"],
          ["2027 / 2028 매출 성장", *[f"{pc(SA[k]['g27'],0)} / {pc(SA[k]['g28'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2029년 성장 (2036년 0%로 수렴)", *[pc(SA[k]["g_late0"], 0) for k in ("보수", "기본", "낙관")]],
          ["성과마진 (2032까지 / 2036)", *[f"{pc(SA[k]['pm'],0)} / {pc(SA[k]['pm_lt'],0)}" for k in ("보수", "기본", "낙관")]],
          ["2027E EPS", *[f"${S[k]['rows'][1]['eps']:.2f}" for k in ("보수", "기본", "낙관")]],
          ["제약 피어 선행 PER", *[f"{S[k]['mult']:.1f}배" for k in ("보수", "기본", "낙관")]]], [30, 23, 23, 24],
         note="피어 배수: 보수 하위 25%, 기본 중앙값, 낙관 상위 25%.")

rp.h1("5. 밸류에이션 (Valuation)")
rp.table([["항목", "값", "근거"], ["미국채 10년", pc(R["ust"], 2), "2026-11-09 (yfinance ^TNX)"],
          ["베타", f"{R['beta']['blume']:.2f}", f"S&P500(SPY) 대비 2년 주간 원베타 {R['beta']['raw']:.2f}, Blume 조정"],
          ["주식위험프리미엄", "5.0%", "미국 종목 공통"], ["자기자본비용", pc(R["coe"], 2), ""],
          ["세후 타인자본비용 / 부채 비중", f"{pc(R['kd'],2)} / {pc(R['wd'])}", ""], ["WACC", pc(R["wacc"], 2), ""], ["영구성장률", "3.0%", "미국 공통"]], [26, 18, 56])
rp.h2("5-1. A. DCF")
rp.para(f"4Q26~2036 FCFF 현재가치 {b(B['pv'])} + 영구가치 {b(B['tv'])} − 순차입 {b(R['net_debt'])} ÷ 희석주식 {R['sh_dil']}백만주 = **{usd(B['va'])}**.")
rp.h2("5-2. B. 2027E EPS × 제약 피어 선행 PER")
sb = R["sens_b"]
rp.para(f"2027E EPS ${FB[1]['eps']:.2f} × 피어 중앙값 {B['mult']:.1f}배 = **{usd(B['vb'])}**.")
rp.table([["2027 매출 성장 \\ PER"] + [f"{p:.1f}배" for p in sb["per"]]] + [[pc(g, 0)] + [usd(x) for x in row] for g, row in zip(sb["g"], sb["v"])],
         [28, 18, 18, 18, 18], note="B 값($). 28배는 현재 yfinance 선행 PER 수준 참고용.")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. DCF", "50%", usd(L["va"]), usd(B["va"]), usd(H["va"])],
          ["B. PER", "50%", f"{usd(L['vb'])} ({L['mult']:.1f}배)", f"{usd(B['vb'])} ({B['mult']:.1f}배)", f"{usd(H['vb'])} ({H['mult']:.1f}배)"],
          ["목표주가", "", usd(L["tp"]), f"{usd(B['tp'])} → {usd(TP)}", usd(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [22, 10, 22, 24, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-4. 민감도 — 2036년 성과마진 × WACC (목표주가)")
sn = R["sens"]
rp.table([["2036 마진 \\ WACC"] + [pc(w) for w in sn["wacc"]]] + [[pc(p, 0)] + [usd(x) for x in row] for p, row in zip(sn["pm"], sn["v"])],
         [25, 18, 19, 19, 19], note="B는 기본값 고정. WACC를 1%p 낮추고 장기 마진을 45%로 올려도 현재가에 못 미친다.")
rp.h2("5-5. 교차확인 — 애널리스트 목표가")
rp.table([["구분", "내용"], ["원래 리포트 직전 1개월(9/15~10/15) 7건", "평균 $1,440, 범위 $1,341(BofA) ~ $1,600(Citi)"],
          ["JP모건", "$1,500(발간일 미확인)"], ["전체 컨센서스", "약 $1,321(10월 중순, MarketBeat)"]],
         [40, 60], note="자료: 원래 리포트(2026-10-15)에서 정리한 Benzinga·Investing.com·MarketBeat·StockAnalysis 집계. 3Q 실적 뒤 변경은 따로 확인하지 않았다. 목표가 계산에 넣지 않았다.")

rp.h1("6. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "레타트루타이드", "2027년 허가 신청·출시가 빠르고 가격이 유지되면 2028년 이후 성장 상향", f"낙관 {usd(H['tp'])}"],
          ["상방", "경구 비만약", "Foundayo가 시장을 넓히면 물량 증가 지속", "성장률"],
          ["하방", "가격 하락 가속", "미국 약가 정책·보험사 협상·해외 NRDL로 가격 −15%보다 빠르게", f"보수 {usd(L['tp'])}"],
          ["하방", "경쟁", "노보노디스크·후발 GLP-1(경구·주사) 진입", "점유율"],
          ["하방", "배수 축소", "성장이 한 번 꺾이면 PER이 빠르게 내려간다(노보노디스크 사례)", "B 값"]], [8, 20, 48, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {usd(TP)} (현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {usd(TP)} · 보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"],
          ["확인할 일정", "① 12월 R&D Day(원래 리포트) ② 4Q26 실적·2027 가이던스(2월) ③ 레타트루타이드 허가 신청"],
          ["결론", f"최고의 성장 기업이지만, 현재가는 2027E EPS의 {R['per27_now']:.0f}배로 2029년 이후까지 높은 성장이 이어진다고 전제한다. 가격 하락과 일회성 도움을 감안하면 {RATING}."]], [20, 80])
rp.since("8", "2026-10-15",
         [["항목", "원래 리포트 (2026-10-15)", "재조사 (2026-11-09)"],
          ["투자의견 / 목표주가", f"{O['rating']} / {usd(O['tp'])}", f"{RATING} / {usd(TP)} (기준주가 {u2(PRICE)})"],
          ["주가", f"{u2(R['px_orig'])} (10-14 종가)", f"{u2(PRICE)} ({R['chg_since']*100:+.1f}%, 11-04 고점 {u2(R['hi_since'])})"],
          ["실적", "2Q26까지 (매출 $23.0B)", "3Q26 매출 $24.4B(+39%), 비GAAP EPS $7.48(IPR&D $4.57 포함)"],
          ["2026 가이던스", "매출 $85~87B, EPS $35.50~36.50", "매출 $91~92B, EPS $35.00~36.00(IPR&D 반영)"],
          ["평가 방법", O["method"], "A. DCF(FCFF) 50 + B. 2027E EPS × 제약 피어 선행 PER 50"],
          ["대안 시나리오", "-", f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]],
         ["3Q26(10-29): 매출이 예상을 넘었고 매출 가이던스를 $5.5B 올렸다. 다만 3Q 매출에 일회성 도움 약 $0.9B가 있었고, 가격은 −15%였다.",
          "인수(AtaiBeckley·Curevo·Merida)로 3Q 인수 IPR&D $4.2B가 생겼다.",
          f"주가는 실적 뒤 +{(R['px_earn']/R['px_pre']-1)*100:.1f}%, 원래 리포트 이후 {R['chg_since']*100:+.1f}% 올랐다. 미국채 10년 4.86%(11-09)."],
         ["목표가를 자체 추정(DCF)과 제약 피어 배수로만 계산했다. 증권사 목표가는 교차확인 표로만 둔다.",
          "매출 × 성과마진에서 정상 인수 IPR&D와 이자를 빼 이익을 만들고, 특허 만료 구간의 마진 하락을 DCF에 넣었다."],
         f"{usd(O['tp'])} → {usd(TP)}. 이익 추정은 원래와 거의 같지만 주가가 17% 올랐고, 자체 DCF와 피어 배수로 다시 계산하면 현재가가 높다. "
         f"상승여력 {UP*100:+.1f}%로 의견을 {O['rating']}에서 {RATING}로 바꾼다.")
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K 실적 보도자료), yfinance(시세·미국채·피어 배수), 원래 리포트에서 정리한 증권사 목표가 집계를 바탕으로 작성한 개인 분석 자료입니다. "
              "증권사 목표가는 교차확인에만 썼습니다.")
out = HERE / "일라이릴리_리서치리포트_20261109.docx"
rp.doc.save(out); print(out); to_pdf(out)
