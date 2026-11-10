"""월마트_리서치리포트_20261106.docx/.pdf — 신규 리포트(기준일 2026-11-06).
서식: valuation/tools/report_kit.py. 입력: results.json(model.py), price_yf.csv. 실행: python valuation/월마트/make_full_report.py
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
PRICE, TP, UP, RATING, K = R["price"], R["tp"], R["upside"], R["rating"], R["key"]
SA = R["scen_assump"]; A_, Qk, P2, GD = K["annual"], K["quarterly"], K["q2_fy27_press"], R["guide"]
b = lambda x: f"${x/1e3:,.1f}B"
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
usd = lambda x, d=0: f"${x:,.{d}f}"
FYS = ["FY23", "FY24", "FY25", "FY26"]

px = pd.read_csv(HERE / "price_yf.csv", index_col=0, parse_dates=True)
p2 = px[(px.index >= "2024-11-01") & (px.index <= R["asof"])]
price_chart(list(p2.index), list(p2["Close"]), TP, HERE / "full_price.png", "최근 2년 종가($), 기준일 2026-11-06", unit="$", alt=[(H["tp"], "낙관")])
revs = [A_["revenue"][y] for y in FYS]
bar_chart(FYS + ["FY27E"], [("매출($B)", [v / 1e3 for v in revs] + [R["totrev27"] / 1e3], "#1F3864"),
                            ("영업이익($B, FY27E는 조정)", [A_["op_income"][y] / 1e3 for y in FYS] + [R["adjop27"] / 1e3], "#8FAADC")],
          HERE / "full_earn.png", "매출·영업이익($B)과 영업이익률 — 음영은 추정(FY27E = 회사 가이던스 중간값)", est_from=4,
          line=("영업이익률", [A_["op_income"][y] / A_["revenue"][y] for y in FYS] + [R["adjop27"] / R["totrev27"]]))
ql = ["1Q FY26", "2Q FY26", "3Q FY26", "4Q FY26", "1Q FY27", "2Q FY27"]
bar_chart([q.replace(" ", "\n") for q in ql], [("매출($B)", [Qk["revenue"][q] / 1e3 for q in ql], "#1F3864")], HERE / "full_q.png",
          "분기 매출($B)과 영업이익률(GAAP) — 2Q FY27은 관세 환급 효과 포함", line=("영업이익률", [Qk["op_income"][q] / Qk["revenue"][q] for q in ql]), ylab="$B")
# 선행 PER 비교
import matplotlib.pyplot as plt
fpe = dict(R["fpe"]); fpe["WMT (현재가/FY27E)"] = R["per27_now"]; fpe["WMT 목표 (기본)"] = R["per_base"]
items = sorted(fpe.items(), key=lambda x: x[1])
fig, a = plt.subplots(figsize=(7.2, 2.1), dpi=220)
a.barh(range(len(items)), [v for _, v in items], color=["#C00000" if "WMT (현" in k else ("#1F3864" if "목표" in k else "#8FAADC") for k, _ in items], height=.55)
for i, (k_, v) in enumerate(items):
    a.text(v, i, f" {v:.1f}배", va="center", fontsize=6.3)
a.set_yticks(range(len(items))); a.set_yticklabels([k for k, _ in items], fontsize=6.5); a.set_xlim(0, max(fpe.values()) * 1.18)
a.set_title("선행 PER 비교 (11-06, yfinance) — 코스트코만 월마트보다 비싸다", fontsize=7.5)
for s_ in ("top", "right"):
    a.spines[s_].set_visible(False)
a.tick_params(labelsize=6.5); plt.tight_layout(); plt.savefig(HERE / "full_pe.png"); plt.close()
football_chart([("A. FY28E EPS × 목표 PER", L["va"], B["va"], H["va"]), ("B. DCF (WACC %.1f%%)" % (R["wacc"] * 100), L["vb"], B["vb"], H["vb"]),
                ("목표주가 (A·B 50:50)", L["tp"], B["tp"], H["tp"])], PRICE, HERE / "full_football.png", unit="$")

SUB = f"이커머스·광고·멤버십으로 체질은 바뀌었다 — 그러나 FY27E 이익의 {R['per27_now']:.0f}배는 코스트코급 가격, DCF로는 영구성장 {R['implied_g']*100:.1f}%가 필요하다"
MKT = [["현재주가 (2026.11.06 종가)", usd(PRICE, 2)], ["시가총액", b(R["mcap"])], ["순차입 + 운용리스 + 비지배", b(R["claims"])],
       ["52주 최고 / 최저 (장중)", f"{usd(R['hi52'],2)} / {usd(R['lo52'],2)}"], ["연초 대비", pc(R["ytd"])],
       ["PER (FY27E 조정 EPS $2.835)", f"{R['per27_now']:.1f}배"], ["PER (FY28E 기본 ${:.2f})".format(B["eps28"]), f"{R['per28_now']:.1f}배"],
       ["EV / FY27E 조정 영업이익", f"{R['ev_ebit27']:.1f}배"], ["FY27 가이던스 (08-20 상향)", "조정 EPS $2.80~2.87"], ["애널리스트 평균 목표가 (43명)", usd(R["cons"]["tp_mean"], 2)]]
ALT = [f"보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"]

rp = Rep("유통 (Discount Retail · Omnichannel)", "2026년 11월 6일")
rp.cover("월마트 (Walmart, NASDAQ: WMT)", SUB, RATING, TP, PRICE, UP, "$", HERE / "full_price.png", MKT, ALT)
rp.h2("재무 요약 (Financial Summary, $M, 회계연도 2~1월)")
rows = [["항목", "FY23", "FY24", "FY25", "FY26", "FY27E", "FY28E"],
        ["매출"] + [f0(A_["revenue"][y]) for y in FYS] + [f0(R["totrev27"]), f0(B["rows"][0]["rev"])],
        ["영업이익 (FY27E~ 조정)"] + [f0(A_["op_income"][y]) for y in FYS] + [f0(R["adjop27"]), f0(B["rows"][0]["ebit"])],
        ["영업이익률"] + [pc(A_["op_income"][y] / A_["revenue"][y]) for y in FYS] + [pc(R["adjop27"] / R["totrev27"]), pc(B["rows"][0]["m"])],
        ["순이익 (GAAP)"] + [f0(A_["net_income"][y]) for y in FYS] + ["-", "-"],
        ["조정 EPS ($)", "-", "-", "-", f"{R['eps26']:.2f}", f"{R['eps27']:.3f}", f"{B['eps28']:.2f}"],
        ["영업현금흐름 − 설비투자"] + [f0(A_["cfo"][y] - A_["capex"][y]) for y in FYS] + ["-", "-"]]
rp.table(rows, [24, 12, 12, 12, 12, 14, 14], hl_cols=(5, 6),
         note="자료: SEC 10-K·10-Q·8-K. FY27E = 2026-08-20 가이던스 중간값(순매출 +4.5%, 조정 영업이익 +7.75%, 조정 EPS $2.835). FY24부터 3:1 액면분할 후 주식수.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", "체질 변화는 진짜 — 이커머스 +23%, 광고 +38%, 멤버십 +17% (2Q FY27)",
              ["매장 픽업·당일 배송과 마켓플레이스가 이커머스를 키우고, 광고·멤버십 같은 고마진 수익이 영업이익률을 끌어올린다",
               "FY27 가이던스를 2월과 8월 두 번 올렸다(조정 EPS $2.75~2.85 → $2.80~2.87)"])
rp.thesis_box("②", f"그러나 가격은 코스트코급 — FY27E PER {R['per27_now']:.0f}배, 자기 5년 평균 {R['own_avg']:.0f}배",
              [f"유통 피어 선행 PER: 코스트코 {R['fpe']['COST']:.0f}배, 아마존 {R['fpe']['AMZN']:.0f}배, BJ's {R['fpe']['BJ']:.0f}배, 타깃·달러제너럴 16~17배, 크로거 12배",
               f"매출 성장(+4~5%)은 코스트코(+11%)의 절반인데 배수는 비슷하다"])
rp.thesis_box("③", f"현금흐름이 말하는 값 {usd(B['vb'])} — 영구성장 {R['implied_g']*100:.1f}%여야 현재가",
              [f"설비투자가 매출의 4%(FY27 가이던스)로 커지며 FCF는 1H FY27 {b(P2['fcf_ytd'])}로 줄었다(−$1.4B). 시가총액 대비 FCF 수익률 약 1.5%",
               "목표가는 시장 배수(A)와 현금흐름(B)을 절반씩 — 프리미엄을 절반만 인정한 값"])
rp.para(f"▶ 결론: 목표주가 {usd(TP)}(A. FY28E 조정 EPS ${B['eps28']:.2f} × {B['per']:.1f}배 = {usd(B['va'])} · B. DCF {usd(B['vb'])}, 50:50), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
        f"좋은 회사지만 지금 가격은 장기 고성장을 전제한다. 낙관 시나리오(코스트코 배수 {R['cost_fpe']:.0f}배)도 {usd(H['tp'])}로 현재가 아래다.", 8.5, before=4)

rp.h1("1. 기업 개요 (Company Overview)")
rp.para("월마트는 세계 최대 유통 기업으로, 미국 월마트, 해외(월마트 인터내셔널 — 멕시코 Walmex, 인도 플립카트 등), 회원제 창고형 할인점 샘스클럽 세 부문으로 나뉜다. "
        "FY26(2026년 1월 결산) 매출 $713B, 영업이익 $29.8B다. 최근 몇 년은 매장을 물류 거점으로 쓰는 옴니채널(매장 픽업·당일 배송)과 마켓플레이스, "
        "광고(월마트 커넥트), 유료 멤버십(월마트+)으로 매출 구성이 바뀌고 있다.")
rp.h2("1-1. 부문별 실적 (2Q FY27, 2026-05~07)")
rp.table([["부문 ($B)", "순매출", "증가율", "영업이익", "증가율", "특징"],
          ["월마트 US", "125.2", "+3.5%", "8.1", "+20.6%", "동일점 +2.6%(약국 가격 규제 −125bp), 이커머스 +24%, 월마트 커넥트 광고 +43%"],
          ["월마트 인터내셔널", "35.2", "+12.8% (cc +7.9%)", "1.4", "+16.6% (cc +5.7%)", "이커머스 +19%, 플립카트 광고 주도 광고 +20%"],
          ["샘스클럽 US", "25.7", "+8.8%", "0.7", "+44.3% (조정 +23.3%)", "동일점(유류 제외) +4.4%, 이커머스 +26%, 회원비 +6%"],
          ["연결", "187.9", "+5.9%", "9.4", "+28.8%", "관세 환급 효과 포함, 조정(cc) +17.4%"]],
         [16, 10, 14, 10, 16, 34], hl_rows=(4,), note="자료: 8-K 2Q FY27 보도자료(2026-08-20). 연결 매출은 회원비 등을 포함한 총매출.")
rp.h2("1-2. 기준일까지의 주요 공시")
rp.table([["날짜", "공시", "내용"],
          ["2026-02-19", "8-K 4Q FY26 실적", "FY27 가이던스 첫 제시: 순매출 +3.5~4.5%, 조정 EPS $2.75~2.85, 자사주 $30B 신규 승인"],
          ["2026-03-13", "10-K FY26", "연간 매출 $713.2B, 영업이익 $29.8B, 순이익 $21.9B"],
          ["2026-05-21", "8-K 1Q FY27 실적", "가이던스 유지"],
          ["2026-08-20", "8-K 2Q FY27 실적", "매출 +5.9%, 영업이익 +28.8%(관세 환급 포함), 조정 EPS $0.81, 가이던스 상향"],
          ["2026-08-28", "10-Q 2Q FY27", "현금 $11.5B, 총차입 $57.2B"]], [14, 22, 64], note="자료: SEC EDGAR. 3Q FY27 실적은 11월 중순 발표 예정으로 기준일 뒤.")
rp.h2("1-3. 재무 상태 (2026-07-31)")
bl = K["balance_20260731"]
rp.table([["항목", "금액", "비고"], ["현금", b(bl["cash"]), ""], ["단기차입 + 장기차입(유동 포함)", b(bl["short_borrow"] + bl["ltd"] + bl["ltd_current"]), "보도자료 총차입 $57.2B(금융리스 포함)"],
          ["운용리스 부채 (비유동)", b(bl["op_lease_nc"]), "EV 계산에 포함"], ["비지배지분", b(bl["nci"]), "플립카트·Walmex 소수주주"],
          ["자기자본", b(bl["equity"]), ""], ["자사주 매입 (1H FY27)", b(P2["buyback_ytd"]), f"잔여 한도 {b(P2['buyback_remaining'])}"]], [32, 18, 50])

rp.h2("1-4. 주주환원")
rp.table([["항목 ($M)", "FY23", "FY24", "FY25", "FY26", "1H FY27"],
          ["배당"] + [f0(A_["dividends"][y]) for y in FYS] + ["3,945"],
          ["자사주 매입"] + [f0(A_["buyback"][y]) for y in FYS] + [f0(P2["buyback_ytd"])],
          ["영업현금흐름 − 설비투자"] + [f0(A_["cfo"][y] - A_["capex"][y]) for y in FYS] + [f0(P2["fcf_ytd"])],
          ["환원 / FCF"] + [pc((A_["dividends"][y] + A_["buyback"][y]) / (A_["cfo"][y] - A_["capex"][y]), 0) for y in FYS] + [pc((3945 + P2["buyback_ytd"]) / P2["fcf_ytd"], 0)]],
         [26, 14, 14, 14, 14, 18], note="자료: 10-K·10-Q 현금흐름표. 1H FY27은 FCF보다 많이 환원해 차입(단기차입 $6.6B → $10.5B)으로 메웠다.")

rp.h1("2. 실적 분석 (Performance Review)")
rp.kpi_tiles([("2Q FY27 매출", b(Qk["revenue"]["2Q FY27"]), f"+{P2['rev_growth']*100:.1f}% (cc +{P2['rev_growth_cc']*100:.1f}%)"),
              ("2Q FY27 영업이익", b(Qk["op_income"]["2Q FY27"]), f"+{P2['op_growth']*100:.1f}% (조정 cc +{P2['adj_op_growth_cc']*100:.1f}%)"),
              ("조정 EPS", f"${P2['adj_eps']:.2f}", f"GAAP ${P2['gaap_eps']:.2f}"), ("미국 동일점 매출", f"+{P2['us_comp']*100:.1f}%", "거래 수 증가 주도")])
rp.img(HERE / "full_q.png", W)
rp.para("2Q FY27 영업이익 +28.8%에는 관세 환급 효과가 들어 있고, 회사는 남은 환급분을 하반기 가격 인하에 다시 쓰겠다고 했다. 그래서 3Q 조정 영업이익 가이던스는 +2~4%로 낮다. "
        "CFO는 2Q와 3Q를 합쳐서 봐야 기초 성장률이 보인다고 했다. 이커머스(+23%)·광고(+38%)·멤버십(+17%)은 고르게 높다.")

rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. 고마진 수익원이 마진을 올린다")
rp.para(f"영업이익률은 FY23 {pc(A_['op_income']['FY23']/A_['revenue']['FY23'])}에서 FY26 {pc(A_['op_income']['FY26']/A_['revenue']['FY26'])}로 올랐고, FY27E 조정 기준 {pc(R['adjop27']/R['totrev27'])}다. "
        "광고와 멤버십은 매출 비중은 작지만 거의 그대로 이익이 되는 수익이라, 이 비중이 늘수록 영업이익 증가율이 매출 증가율의 두 배 가까이 된다(FY27 가이던스: 매출 +4~5%, 조정 영업이익 +7~8.5%). "
        f"기본 시나리오는 이 흐름이 이어져 FY37 영업이익률 {pc(SA['기본']['m_lt'])}에 이른다고 가정했다.")
rp.h2("Thesis 2. 배수 — 코스트코와 비슷한 값을 받고 있다")
rp.img(HERE / "full_pe.png", W)
rp.para(f"월마트의 연도별 선행 PER은 FY22 21배 → FY26 42배로 두 배가 됐다(stockanalysis.com, 기준 시점 미표기 참고치). 5년 평균은 {R['own_avg']:.1f}배다. "
        f"이 리포트의 목표 PER {R['per_base']:.1f}배는 이 평균과 코스트코({R['cost_fpe']:.1f}배)의 중간으로, 체질 변화를 절반 인정한 값이다.")
rp.h2("Thesis 3. 투자 확대기 — FCF가 줄고 있다")
rp.para(f"FY27 설비투자 가이던스는 매출의 약 4%(약 $30B)로 FY26(3.7%)보다 늘었다. 자동화 물류센터와 매장 리모델링 투자다. 그 결과 1H FY27 FCF는 {b(P2['fcf_ytd'])}로 전년보다 $1.4B 줄었다. "
        f"DCF는 설비투자가 FY37 매출의 {pc(SA['기본']['capex_lt'])}로 내려간다고 가정해도 주당 {usd(B['vb'])}다.")

rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.img(HERE / "full_earn.png", W)
rp.para(f"FY27E는 회사 가이던스 중간값을 그대로 썼다(총매출 {b(R['totrev27'])}, 조정 영업이익 {b(R['adjop27'])}). FY28E는 고마진 수익 확대로 조정 영업이익이 {pc(SA['기본']['op28'],0)} 늘고 "
        f"자사주로 주식수가 1% 줄어 조정 EPS ${B['eps28']:.2f}(+{B['eps28']/R['eps27']-1:.0%})로 본다. 컨센서스 ${R['cons']['fy28_eps']}보다 약간 낮다 — 3Q 가이던스(+2~4%)처럼 관세 환급을 가격에 재투자하는 기간이 FY28 상반기까지 이어질 수 있어서다.")
rp.table([["가정", "보수", "기본", "낙관"],
          ["FY28 조정 영업이익 증가", *[pc(SA[k]["op28"], 0) for k in ("보수", "기본", "낙관")]],
          ["주식수 변화 (자사주)", *[pc(SA[k]["sh"]) for k in ("보수", "기본", "낙관")]],
          ["FY28E 조정 EPS", *[f"${S[k]['eps28']:.2f}" for k in ("보수", "기본", "낙관")]],
          ["목표 PER", f"{L['per']:.1f}배 (자기 5년 평균)", f"{B['per']:.1f}배 (평균·코스트코 중간)", f"{H['per']:.1f}배 (코스트코)"],
          ["매출 성장 FY28~FY37", *[pc(SA[k]["g"]) for k in ("보수", "기본", "낙관")]],
          ["FY37 영업이익률 / 설비투자율", *[f"{pc(SA[k]['m_lt'])} / {pc(SA[k]['capex_lt'])}" for k in ("보수", "기본", "낙관")]]],
         [30, 23, 23, 24], note=f"FY28E 조정 EPS 컨센서스 ${R['cons']['fy28_eps']}(247wallst 인용, 10-05), 이 리포트 기본은 ${B['eps28']:.2f}. 이자·세율은 FY27 가이던스와 같다고 가정.")

rp.h1("5. 밸류에이션 (Valuation)")
rp.table([["항목", "값", "근거"], ["미국채 10년", pc(R["ust"], 2), "2026-11-06"], ["베타", f"{R['beta']['blume']:.2f}", f"SPY 대비 2년 주간 원베타 {R['beta']['raw']:.2f}, Blume 조정"],
          ["주식위험프리미엄", "5.0%", ""], ["할인율", pc(R["wacc"], 2), "자기자본비용(부채 비중 작음, 보수적으로 WACC로 사용)"], ["영구성장률", "3.0%", ""],
          ["EV 조정", b(R["claims"]), "순차입 + 운용리스 + 비지배지분"]], [22, 14, 64])
rp.h2("5-1. A. FY28E 조정 EPS × 목표 PER")
rp.para(f"FY28E 조정 EPS ${B['eps28']:.2f} × {B['per']:.1f}배 = **{usd(B['va'])}**.")
sa_ = R["sens_a"]
rp.table([["FY28 이익 증가 \\ PER"] + [f"{p:.1f}배" for p in sa_["per"]]] + [[pc(g, 0)] + [usd(x) for x in row] for g, row in zip(sa_["g"], sa_["v"])],
         [20, 16, 16, 16, 16, 16], note="A 값($).")
rp.h2("5-2. B. DCF")
rp.para(f"FY28~FY37 FCFF(조정 영업이익 × (1 − 24%) + 감가상각 매출 1.9% − 설비투자) 현재가치 {b(B['pv'])} + 영구가치 {b(B['tv'])} − 순차입·리스·비지배 {b(R['claims'])} "
        f"÷ 희석주식 {R['sh_dil']:,.0f}백만주 = **{usd(B['vb'])}**.")
rws = B["rows"]
rp.table([["FY (기본, $B)"] + [str(r["fy"])[2:] for r in rws[::1]][:10]] +
         [["매출"] + [f"{r['rev']/1e3:,.0f}" for r in rws], ["영업이익률"] + [pc(r["m"]) for r in rws],
          ["설비투자"] + [f"{r['capex']/1e3:,.1f}" for r in rws], ["FCFF"] + [f"{r['fcff']/1e3:,.1f}" for r in rws]],
         [13] + [8.7] * 10, size=6.6, note="FY28~FY37. 감가상각은 매출의 1.9%, 세율 24%. 영구가치는 FY37 FCFF × 1.03 ÷ (할인율 − 3%).")
sb_ = R["sens_b"]
rp.table([["FY37 마진 \\ 할인율"] + [pc(w, 2) for w in sb_["wacc"]]] + [[pc(m)] + [usd(x) for x in row] for m, row in zip(sb_["m"], sb_["v"])],
         [24, 19, 19, 19, 19], note="B 값($).")
rp.h2("5-3. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. EPS × PER", "50%", usd(L["va"]), usd(B["va"]), usd(H["va"])], ["B. DCF", "50%", usd(L["vb"]), usd(B["vb"]), usd(H["vb"])],
          ["목표주가", "", usd(L["tp"]), f"{usd(B['tp'],1)} → {usd(TP)}", usd(H["tp"])], ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])]],
         [22, 10, 22, 24, 22], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, −5% ~ +15% HOLD, −5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-4. 교차확인 — 애널리스트 목표가 (2Q FY27 실적 이후)")
rp.table([["기관", "날짜", "의견", "목표가"]] + [[a, d, c, usd(t)] for a, d, c, t in R["analysts"]] +
         [["컨센서스 (S&P Global, 43명)", "11-03", "Buy", f"평균 {usd(R['cons']['tp_mean'],2)} · 중앙 {usd(R['cons']['tp_median'])}"]],
         [34, 14, 14, 38], note="자료: stockanalysis.com(11-03 업데이트). 산출 방법 미공개. 목표가 계산에 넣지 않았다.")

rp.h1("6. 리스크 (Risk)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["상방", "광고·멤버십 가속", "고마진 수익 비중이 예상보다 빨리 늘어 영업이익률 6% 이상", f"낙관 {usd(H['tp'])}"],
          ["상방", "배수 유지", "방어주 선호가 이어지면 40배 이상 유지", "A 상향"],
          ["하방", "관세·가격 투자", "관세 환급분을 가격에 재투자 — 하반기 이익 증가율 둔화(3Q 가이던스 +2~4%)", "EPS"],
          ["하방", "설비투자 확대", "자동화 투자로 FCF 감소 지속", "B 하향"],
          ["하방", "배수 정상화", "자기 5년 평균 29배로 돌아가면 FY28E 기준 약 $90", f"보수 {usd(L['tp'])}"]], [8, 20, 48, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {usd(TP)} (FY28E PER {TP/B['eps28']:.0f}배, 현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {usd(TP)} · 보수 {usd(L['tp'])} · 낙관 {usd(H['tp'])}"],
          ["확인할 일정", "① 3Q FY27 실적(11월 중순) ② FY28 가이던스(2027-02) ③ 설비투자율·FCF 회복"],
          ["결론", f"월마트는 유통에서 플랫폼으로 바뀌는 중이고 실적도 좋다. 그러나 FY27E PER {R['per27_now']:.0f}배는 그 변화를 다 반영했고, 현금흐름으로는 영구성장 {R['implied_g']*100:.1f}%를 요구한다. "
                   f"사업이 아니라 가격 때문에 {RATING}."]], [20, 80])
rp.disclaimer("본 리포트는 SEC 공시(10-K, 10-Q, 8-K 실적 보도자료), yfinance(시세·미국채·피어 배수), stockanalysis.com·247wallst(애널리스트 목표가·컨센서스, 연도별 선행 PER)를 바탕으로 작성한 개인 분석 자료입니다. "
              "애널리스트 목표가는 교차확인에만 썼습니다.")
out = HERE / "월마트_리서치리포트_20261106.docx"
rp.doc.save(out); print(out); to_pdf(out)
