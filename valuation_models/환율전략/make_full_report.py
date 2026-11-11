"""환율전략_리서치리포트_20261109.docx/.pdf — 원/달러 거시 모형(VIF·HAC·공적분) + 모형 비교 + 표본 밖 백테스트 + 한·미 기관 전망·전략 비교 (ETF & Macro 신규).
서식: valuation/tools/report_kit.py(표지만 이 파일 안에서 환율용으로 바꿈 — 공통 도구는 고치지 않음).
입력: results.json(model.py), backtest.json(backtest.py), market_daily.csv. 실행: python valuation/환율전략/make_full_report.py
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools import report_kit as rk
from valuation.tools.report_kit import Rep, to_pdf, price_chart, football_chart, W

R = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
BT = json.loads((HERE / "backtest.json").read_text(encoding="utf-8"))
FX, SC, NM, MD, OL = R["fx"], R["scen"], R["names"], R["model"], R["outlook"]
KS = list(SC.keys()); KW, KB, KST = KS[0], KS[1], KS[2]
WK, BS, ST = SC[KW], SC[KB], SC[KST]
short = {KW: "원화 약세", KB: "기본", KST: "원화 강세"}
w = lambda x: f"{x:,.0f}원"
pc = lambda x, d=1: f"{x*100:+.{d}f}%"
pp = lambda x, d=0: f"{x*100:.{d}f}%"
pv = lambda p: "<0.001" if p < 0.001 else f"{p:.3f}"

D = pd.read_csv(HERE / "market_daily.csv", index_col=0, parse_dates=True); D = D[D.index <= R["asof"]]
fxd = D["KRW=X"].dropna()
MOM12 = FX / float(fxd[:"2025-11-09"].iloc[-1]) - 1; MOM6 = FX / float(fxd[:"2026-05-09"].iloc[-1]) - 1
lm = np.log(fxd.resample("ME").last()); SD12 = float((lm.shift(-12) - lm).dropna()["2015":].std())
RW_BAND = (FX * np.exp(-SD12), FX * np.exp(SD12))
mret = D[["KRW=X", "^KS11"]].resample("ME").last().pct_change(fill_method=None).dropna()
CORR_KS_ALL, CORR_KS_3Y = float(mret.corr().iloc[0, 1]), float(mret.iloc[-36:].corr().iloc[0, 1])
FIN = BT["backtest"]["최종 6변수"]; ROB = BT["robust"]

d2 = fxd.loc["2024-11-01":]
price_chart(list(d2.index), list(d2), FX, HERE / "full_price.png", "원/달러 최근 2년(원), 기준일 2026-11-09", unit="원", alt=[(RW_BAND[1], "+1σ"), (RW_BAND[0], "−1σ")])
G = pd.read_csv(HERE / "regression_monthly.csv", index_col=0); G.index = pd.PeriodIndex(G.index, freq="M").to_timestamp()
PPP = pd.read_csv(HERE / "ppp_monthly.csv", index_col=0); PPP.index = pd.PeriodIndex(PPP.index, freq="M").to_timestamp()
fig, a = plt.subplots(figsize=(7.2, 2.4), dpi=220)
a.plot(G.index, G["fx"], color="#1F3864", lw=1.2, label="실제(월평균)")
a.plot(G.index, G["fitted"], color="#C00000", lw=1.0, ls="--", label="거시 회귀 적정환율(전체 표본)")
a.plot(PPP.index, PPP.iloc[:, 0], color="#7F7F7F", lw=0.9, ls=":", label="상대 PPP")
a.set_title("원/달러 실제 vs 거시 적정환율(2015~2026-09)", fontsize=7.5); a.legend(fontsize=6, frameon=False); rk.ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / "full_fit.png"); plt.close()
fig, a = plt.subplots(figsize=(7.2, 2.0), dpi=220)
rk_ = list(ROB.keys()); a.barh(rk_, [ROB[k]["fair"] for k in rk_], color=["#C00000" if k == "최종 6변수" else "#8EA9DB" for k in rk_])
a.axvline(FX, color="#1F3864", lw=1); a.text(FX, -0.7, f" 현재 {FX:,.0f}", fontsize=6, color="#1F3864")
a.set_xlim(1200, 1700); a.set_title("모형 사양별 지금의 적정환율(원) — 사양에 따라 1,289~1,645원", fontsize=7); a.tick_params(labelsize=6); rk.ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / "full_robust.png"); plt.close()
football_chart([("과거 12개월 변동 ±1σ (현재 기준)", RW_BAND[0], FX, RW_BAND[1]), ("거시 시나리오 (강세~약세, 점=기본)", ST["fx"], BS["fx"], WK["fx"]),
                ("기관 전망 숫자 (2027년 1,280~1,370원)", 1280, 1300, 1370), ("상대 PPP (장기 기준)", R["fair_b"], R["fair_b"], R["fair_b"])],
               FX, HERE / "full_football.png", unit="원", xlabel="원/달러 · 막대=범위, 점=중심값, 선=현재")

rp = Rep("ETF & Macro (외환)", "2026년 11월 9일")


def fx_cover(name, subtitle, view, center, png, rows, alt):
    t = rp.doc.add_table(rows=1, cols=1); rk.borders(t, rk.NAVY, "4"); c = t.cell(0, 0); rk.shade(c, rk.NAVY); c.width = Cm(W)
    rp.cellp(c, name, 17, True, "FFFFFF", WD_ALIGN_PARAGRAPH.LEFT)
    p = c.add_paragraph(); rk.run(p, subtitle, 9, False, "D9E2F3")
    rp.doc.add_paragraph()
    t = rp.doc.add_table(rows=1, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; rk.borders(t, "FFFFFF", "4")
    lc, rc = t.cell(0, 0), t.cell(0, 1); lc.width = Cm(W * .52); rc.width = Cm(W * .48)
    rt = lc.add_table(rows=1, cols=2); rk.borders(rt, "FFFFFF", "8")
    a_ = rt.cell(0, 0); rk.shade(a_, "7F7F7F"); a_.width = Cm(3.2)
    rp.cellp(a_, view, 13, True, "FFFFFF"); p = a_.add_paragraph(); rk.run(p, "(방향 예측 대신 위험관리)", 6.5, False, "FFFFFF"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    b2 = rt.cell(0, 1); rk.shade(b2, rk.LIGHT); b2.width = Cm(5.8)
    rp.cellp(b2, "원/달러 12개월 중심값 = 현재 수준", 7, False, rk.GRAY, WD_ALIGN_PARAGRAPH.LEFT)
    p = b2.add_paragraph(); rk.run(p, w(center), 17, True, rk.NAVY)
    p = b2.add_paragraph(); rk.run(p, f"±1σ {w(RW_BAND[0])}~{w(RW_BAND[1])} (과거 12개월 변동 {SD12*100:.1f}%)", 7.5, True, rk.NAVY)
    for ln in alt:
        p = b2.add_paragraph(); rk.run(p, ln, 7, False, rk.GRAY)
    rp.img(png, W * .5, cont=lc); lc.paragraphs[0]._p.getparent().remove(lc.paragraphs[0]._p)
    rp.table([["항목", "수치"]] + rows, [55, 45], 7.2, cont=rc); rc.paragraphs[0]._p.getparent().remove(rc.paragraphs[0]._p)


MKT = [["원/달러 (2026.11.09)", w(FX)], ["2026년 평균 / 52주 최고·최저(종가)", f"{w(R['ytd_avg'])} / {w(R['hi52'])}·{w(R['lo52'])}"],
       ["6개월 / 12개월 변화", f"{pc(MOM6)} / {pc(MOM12)}"], ["달러인덱스 / VIX / WTI", f"{R['dxy']:.2f} / {R['vix']:.1f} / ${R['wti']:.1f}"],
       ["장기금리차 (국고10Y − 미국채10Y)", f"{R['ktb']-R['ust']:+.2f}%p"], ["단기금리차 (기준금리 − 연방기금)", f"{R['base_kr']-R['ff']:+.2f}%p"],
       ["거시 적정환율 (최종 6변수)", f"{w(R['fair_a'])} (사양별 1,289~1,645)"], ["표본 밖 12개월 오차 (모형 ÷ 랜덤워크)", f"{FIN['12']['ec_ratio']:.2f}배"],
       ["1년 선물환 (헤지 비용)", f"{w(R['fwd'])} (연 {abs(R['hedge'])*100:.2f}%)"], ["기관 전망 (MUFG 2027 3Q)", "1,280원"]]
fx_cover("환율전략: 원/달러 12개월 전망과 헤지", "모형은 환율을 맞히지 못했다 — 그래서 방향에 걸지 않고, 원화 약세가 오는 '위기 때'를 대비하는 헤지 전략",
         "중립", FX, HERE / "full_price.png", MKT, [f"거시 시나리오 {w(ST['fx'])}~{w(WK['fx'])} · 기관 전망은 원화 강세(1,200원대~1,300원대)"])
rp.h2("핵심 결론 요약")
rp.table([["질문", "답", "근거"],
          ["1년 뒤 원/달러를 맞힐 수 있나?", "아니다", f"표본 밖(2022-12~) 12개월 예측 오차가 '그대로' 예측의 {FIN['12']['ec_ratio']:.2f}배, 이긴 달 {pp(FIN['12']['ec_win'])}"],
          ["그럼 중심값은?", f"현재 수준 {w(FX)}", f"±1σ {w(RW_BAND[0])}~{w(RW_BAND[1])}(2015년 이후 12개월 변동 {SD12*100:.1f}%)"],
          ["어느 쪽 위험이 큰가?", "판단이 엇갈린다", f"거시 모형·연준 고금리는 약세 쪽, 기관 전망 다수·PPP·최근 6개월 추세({pc(MOM6)})는 강세 쪽"],
          ["미국 자산 헤지는?", "비헤지 60%·헤지 40%", f"방향과 무관하게, 원화는 코스피가 떨어질 때 약해져(월간 상관 {CORR_KS_ALL:+.2f}) 달러 노출이 국내 자산 손실을 일부 메운다"],
          ["보유 달러·환전은?", "구간 분할", f"±1σ 상단({w(RW_BAND[1])}) 위에서 분할 환전, 하단({w(RW_BAND[0])}) 아래에서 분할 매수"]],
         [26, 22, 52], note="자료: model.py·backtest.py, 기관 전망은 5장. 첫 판(원화 강세, 1,295원)과 둘째 판(중립·약세 위험, 1,358원)은 모형 하나에 기댄 결론이라 이 판에서 고쳤다.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", "모형 검증: 거시 회귀는 '설명'은 하지만 '예측'은 못 한다",
              [f"최종 6변수 모형(R² {R['r2']:.2f}, VIF ≤ {max(R['vif_final'].values()):.1f}, 공적분 p {R['adf_p']:.3f})도 표본 밖 3·6·12개월 모두 랜덤워크보다 오차가 컸다",
               f"미래 거시 변수의 실제값을 알려줘도(정답 입력) 12개월 오차가 랜덤워크의 {FIN['12']['orc_ratio']:.1f}배 — 2023년 이후 환율과 거시 변수의 관계 자체가 바뀌었다"])
rp.thesis_box("②", "적정환율은 모형을 어떻게 짜느냐에 따라 1,289~1,645원",
              ["처음 판(달러·위안·장기금리차) 1,289원 → 최종 6변수 1,366원 → 경상수지 포함 1,612원 → 전체 10변수 1,645원",
               "같은 데이터로도 결론이 '원화 강세'부터 '크게 약세'까지 바뀐다 — 한 모형의 점 예측에 걸면 안 되는 이유"])
rp.thesis_box("③", "한·미 기관 전망은 원화 강세 쪽, 이 리포트 모형은 약세 쪽",
              ["MUFG(11월): 2027년 3분기 1,280원·달러인덱스 97. 국내 증권사 10곳 중 7곳이 2027년 1,200원대 진입 가능(언론 보도)",
               "연준은 2027년에도 4.1%(SEP) — 달러 약세 전망과 미국 고금리가 맞서는 구간. 국민연금 전략적 환헤지·한은 스와프는 2026년 말까지(연장 여부 확인 필요)"])
rp.para(f"▶ 결론: 12개월 중심값은 현재 수준 {w(FX)}(±1σ {w(RW_BAND[0])}~{w(RW_BAND[1])}), 판단은 **중립**. 모형과 기관 전망이 반대 방향이고, 모형은 표본 밖에서 단순 예측을 못 이겼다. "
        "그래서 방향에 거는 전략(달러 매수·매도 베팅)은 하지 않는다. 대신 ① 미국 자산은 비헤지 60%·헤지 40%로 위기 때 원화 약세를 보험으로 쓰고, "
        f"② 보유 달러는 {w(RW_BAND[1])} 위에서, 신규 달러는 {w(RW_BAND[0])} 아래에서 나눠 거래하는 구간 전략을 제안한다.", 8.5, before=4)

rp.h1("1. 현재 상황 (Overview)")
rp.para(f"원/달러는 2024년 평균 {w(R['yr']['2024'])}, 2025년 {w(R['yr']['2025'])}로 올랐고 2026년에도 평균 {w(R['ytd_avg'])}로 높았다. {R['hi52_d'][5:7]}월 {R['hi52_d'][8:]}일 종가 {w(R['hi52'])}에서 고점을 찍은 뒤 "
        f"6개월 {pc(MOM6)}, 12개월 {pc(MOM12)} 내려 지금 {w(FX)}다. 국고채 10년은 2026년 9월 월평균 {R['ktb_hist']['2026-09']:.2f}%에서 11-09 {R['ktb']:.2f}%로 내렸고, "
        f"코스피는 9월 월평균 6,848에서 {R['kospi']:,.0f}로 크게 내렸다. VIX는 {R['vix']:.1f}, WTI는 ${R['wti']:.1f}다.")
rp.table([["연도", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026(~11/9)"],
          ["원/달러 평균"] + [f"{R['yr'][str(y)]:,.0f}" for y in range(2019, 2027)]], [16] + [10.5] * 8, note="자료: yfinance(KRW=X) 일별 종가 평균.")
rp.h2("1-1. 경제전망 (미국·한국)")
rp.table([["항목", "미국 (연준 SEP, 2026-09-16)", "한국 (한국은행, 2026-08)"],
          ["실질 GDP 성장률", f"2026 2.3% → 2027 {OL['us_gdp_2027']}% → 2028 2.2%", f"2026 {OL['kr_gdp_2026']}% → 2027 {OL['kr_gdp_2027']}%"],
          ["물가", f"PCE 2026 {OL['us_pce_2026']}% → 2027 {OL['us_pce_2027']}%", f"CPI 전년비 현재 {R['inf_kr']:.1f}% (미국 CPI {R['inf_us']:.1f}%)"],
          ["정책금리", f"2026·2027년 말 {OL['fed_2027']}%(위원 범위 {OL['fed_range']}%), 9월 0.25%p 인상", f"기준금리 {R['base_kr']:.2f}%(10월)"]], [18, 46, 36],
         note="자료: 연준 SEP 원문(federalreserve.gov), 한국은행 8월 전망은 언론 보도(SBS Biz) — 11월 수정 전망은 기준일까지 확인되지 않음.")

rp.h1("2. 거시 적정환율 모형 (Fair Value)")
rp.h2("2-1. 변수 선택 — 다중공선성(VIF)과 유의성(HAC)")
fa = R["full"]
rp.table([["후보 변수", "VIF", "전체 모형 계수", "HAC p값", "결과"]] +
         [[NM[k], f"{R['vif_all'][k]:.1f}", f"{fa[k]['coef']:+.3f}", pv(fa[k]["p"]),
           "최종 채택" if k in R["final"] else next((f"제외({why})" for c, why, _ in R["steps"] if c == k), "")] for k in NM],
         [32, 10, 18, 14, 26], note=f"VIF 최대 {max(R['vif_all'].values()):.1f}(10 미만) → VIF로 뺀 변수 없음. 이론과 부호가 반대인 경상수지 제외 후, HAC(6개월) p > 0.10 변수를 하나씩 뺐다.")
for _s in ("· VIF(분산팽창계수)는 한 변수가 다른 변수들로 얼마나 설명되는지를 보여주며, 10 이상이면 계수가 불안정하다고 본다.",
           "· HAC(Newey-West) 표준오차: 월별 환율 회귀는 잔차끼리 이어져 있어(자기상관) 보통 t값이 부풀려진다. 6개월 시차까지 보정했다.",
           f"· 경상수지는 '흑자가 클수록 원화 약세'(계수 {fa['ca12']['coef']:+.3f})로 이론과 반대였다. 2025~26년 사상 최대 흑자가 해외투자로 빠져나간 기간과 겹친 것으로 본다."):
    rp.para(_s, 8.0, after=1)
rp.h2("2-2. 최종 모형과 검정")
df_ = R["diff"]
rp.table([["변수", "계수", "HAC p값", "VIF", "해석 (원/달러)"]] +
         [[NM[k], f"{MD[k]['coef']:+.4f}", pv(MD[k]["p"]), f"{R['vif_final'][k]:.1f}",
           {"ln_dxy": f"달러인덱스 1% ↑ → {MD[k]['coef']:.2f}% ↑", "lsp": f"장기금리차 1%p ↑ → {MD[k]['coef']*100:.1f}%",
            "ssp": f"단기금리차 1%p ↑ → {MD[k]['coef']*100:.1f}%", "ln_vix": f"VIX 10% ↑ → {MD[k]['coef']*10:.2f}% ↑",
            "ln_wti": f"유가 10% ↑ → {MD[k]['coef']*10:.2f}% ↑", "ur": f"미국 실업률 1%p ↑ → {MD[k]['coef']*100:.1f}% ↑"}.get(k, "")] for k in R["final"]] +
         [["검정", f"R² {R['r2']:.2f}", f"ADF {R['adf_p']:.3f}", f"ρ {R['rho']:.2f}", f"잔차 정상(공적분), 괴리 지속성 높음. 월 변화 회귀(R² {R['diff_r2']:.2f})에서도 달러·VIX 유의"]],
         [30, 13, 12, 9, 36], note=f"2015~2026-09 월별 {R['n']}개월. 적정환율(지금 입력값) {w(R['fair_a'])}, ±1σ {w(R['band'][0])}~{w(R['band'][1])}.")
rp.img(HERE / "full_fit.png", W)

rp.h1("3. 모형 검증 — 강건성과 백테스트 (Validation)")
rp.h2("3-1. 모형 사양을 바꾸면 (전체 표본, 지금 입력값)")
rp.table([["사양", "변수 수", "유의(p<0.10)", "R²", "최대 VIF", "지금 적정환율", "현재 대비 괴리"]] +
         [[k, str(v["n"]), f"{v['sig']}/{v['n']}", f"{v['r2']:.2f}", f"{v['vif']:.1f}", w(v["fair"]), pc(v["gap"])] for k, v in ROB.items()],
         [30, 9, 12, 9, 11, 15, 14], hl_rows=(3,))
rp.img(HERE / "full_robust.png", W)
rp.para("R²는 변수를 늘릴수록 오르지만(0.59 → 0.87), 적정환율은 1,289원에서 1,645원까지 움직인다. 경상수지를 넣느냐가 가장 크게 바꾸는데, 그 계수는 이론과 반대 부호다. "
        "즉 '어떤 모형을 고르느냐'가 결론을 정한다. 처음 판(원화 강세)과 둘째 판(중립)의 결론이 바뀐 이유가 바로 이것이다.", 8.2)
rp.h2("3-2. 표본 밖 백테스트 — 2015~2022년으로 만들고 2023~2026년을 맞혀 보기")
rows = []
for h in ("3", "6", "12"):
    v = FIN[h]
    rows.append([f"{h}개월 뒤", str(v["n"]), f"{v['rw']:.2f}%", f"{v['ec']:.2f}% ({v['ec_ratio']:.2f}배)", pp(v["ec_win"]), f"{v['orc']:.2f}% ({v['orc_ratio']:.2f}배)"])
rp.table([["예측 거리", "예측 횟수", "랜덤워크 오차", "모형 오차 (÷랜덤워크)", "모형이 이긴 비율", "정답 입력 모형 오차"]] + rows, [14, 12, 16, 22, 16, 20],
         note=f"최종 6변수, 2022-12부터 매월 그 시점까지 데이터로 다시 추정(확장 창). 오차 = 로그 오차 RMSE(%). 랜덤워크 = '환율은 그대로'. 정답 입력 = 미래 거시 변수의 실제값을 넣은 경우.")
o1, o2 = BT["backtest"]["처음 판(달러·위안·장기금리차)"]["12"], BT["backtest"]["2변수(달러·장기금리차)"]["12"]
rp.table([["사양 (12개월 뒤)", "모형 오차 ÷ 랜덤워크", "이긴 비율"], ["처음 판(달러·위안·장기금리차)", f"{o1['ec_ratio']:.2f}배", pp(o1["ec_win"])],
          ["2변수(달러·장기금리차)", f"{o2['ec_ratio']:.2f}배", pp(o2["ec_win"])], ["최종 6변수", f"{FIN['12']['ec_ratio']:.2f}배", pp(FIN["12"]["ec_win"])]], [44, 28, 28])
rp.para("결과는 분명하다. 어느 사양도 랜덤워크를 이기지 못했고, 12개월 뒤 예측은 랜덤워크보다 오차가 1.7~2.0배 컸다. 미래 거시 변수를 정확히 알려줘도 결과가 더 나빴다는 것은, "
        "2022년까지의 관계(달러·금리차·위험회피가 원화를 정하는 방식)가 2023년 이후 바뀌었다는 뜻이다. 원화가 거시 변수보다 계속 약했고(해외투자 자금 유출로 추정), "
        "'괴리가 적정 수준으로 돌아온다'는 가정이 틀렸다. 이는 환율 예측 연구의 오래된 결론(1년 이내에는 랜덤워크를 이기기 어렵다)과도 같다. "
        "그래서 이 리포트는 모형을 방향 예측에 쓰지 않고, 2장 회귀는 '무엇이 환율을 움직이는지' 설명하는 데만 쓴다.", 8.2)

rp.h1("4. 12개월 범위와 시나리오 (Outlook)")
rp.img(HERE / "full_football.png", W)
rp.table([["구분", "2027-11 원/달러", "현재 대비", "성격"],
          ["중심값 (랜덤워크)", w(FX), "0.0%", "백테스트에서 가장 정확했던 예측"],
          ["±1σ 범위", f"{w(RW_BAND[0])}~{w(RW_BAND[1])}", f"±{SD12*100:.1f}%", "2015년 이후 12개월 변화의 표준편차"]] +
         [[f"거시 시나리오: {short[k]} ({pp(SC[k]['p'])})", w(SC[k]["fx"]), pc(SC[k]["chg"]), SC[k]["why"]] for k in KS],
         [24, 16, 12, 48], note="거시 시나리오는 '경제가 이렇게 되면 환율은 대략 이 정도'라는 조건부 계산이다(예측력 검증 결과는 3-2). 확률은 경제전망을 반영한 이 리포트의 판단.")
rp.h2("4-1. 민감도 — 달러인덱스 × VIX (조건부, 나머지는 기본값)")
sn = R["sens"]
rp.table([["VIX \\ 달러인덱스"] + [f"{d}" for d in sn["dxy"]]] + [[f"{v_}"] + [f"{x:,.0f}" for x in row] for v_, row in zip(sn["vix"], sn["v"])],
         [24, 15, 15, 15, 15, 16], note="위험회피(VIX 30 이상)와 달러 강세(103 이상)가 겹치면 1,450원을 넘는다 — 헤지 전략이 대비하는 상황.")

rp.h1("5. 다른 기관 전망과 환율 전략 (Cross-check)")
rp.h2("5-1. 한·미 기관 전망 (교차확인, 계산에 넣지 않음)")
rp.table([["기관", "발표", "원/달러 전망", "근거"],
          ["MUFG (일본, 글로벌)", "2026-11 월간", "4Q26 1,320 → 1Q27 1,300 → 2Q27 1,300 → 3Q27 1,280", "12월 이후 연준 추가 인상 없음 가정 → 2027년 달러 약세(달러인덱스 3Q27 97)"],
          ["iM증권", "2027 전망", "1,200~1,450원, 연평균 1,280원", "연준과 주요국 금리차 축소, 달러 약세"],
          ["한화투자증권", "2027 전망", "연평균 1,300원", "반도체 수출 증가에 따른 달러 공급"],
          ["신한투자증권", "2027 전망", "1분기 1,300 → 4분기 1,370원", "하반기 원화 약세 전환"],
          ["대신증권", "2026-10 2027 전략", "2027년 2분기 1,300원", "-"],
          ["KB국민은행", "10월 FX 전망", "2027년 상반기 말~하반기 초 1,200원대 진입 가능", "대규모 경상흑자로 외환 수급 변화"],
          ["국내 증권사 10곳", "언론 집계", "7곳이 2027년 1,200원대 진입 가능", "-"],
          ["Cambridge Currencies", "2026-11", "달러인덱스 2027년 97~104 (원화 없음)", "달러 강세 쪽으로 기운 범위"]],
         [20, 15, 33, 32], note="자료: MUFG Research 원문(mufgresearch.com, 11월 월간 외환전망 표) 확인. 국내 기관은 언론 보도(이데일리·비즈니스포스트·KB Think) 인용 — 원문 미확인. 목표 수치를 이 리포트 계산에 넣지 않았다.")
rp.para("기관 전망은 대체로 원화 강세(1,200원대~1,300원대)다. 근거는 ① 2027년 달러 약세, ② 반도체 호황에 따른 사상 최대 경상흑자다. 이 리포트의 거시 모형은 반대(약세 쪽)인데, "
        "모형은 연준 고금리·위험회피를, 기관은 경상흑자·달러 약세를 더 무겁게 본 차이다. 3장에서 보았듯 어느 쪽도 1년 방향을 맞힌다고 볼 근거는 약하다.", 8.2)
rp.h2("5-2. 환율 전략의 종류와 지금 신호")
rp.table([["전략 (외환 운용에서 쓰는 방식)", "규칙", "지금 원/달러 신호", "방향"],
          ["캐리(carry)", "금리가 높은 통화를 보유", f"미국 3개월 {R['tb3']:.2f}% > CD 91일 {R['cd91']:.2f}% → 달러 보유가 연 {abs(R['hedge'])*100:.2f}% 유리", "달러 보유"],
          ["가치(value, PPP)", "장기 적정가보다 싼 통화를 보유", f"상대 PPP {w(R['fair_b'])} 대비 원화 {pc(np.log(FX / R['fair_b']))} 저평가", "원화 보유"],
          ["모멘텀(momentum)", "최근 오른 통화를 보유", f"6개월 원/달러 {pc(MOM6)}, 12개월 {pc(MOM12)} — 원화 강세 추세", "원화 보유"],
          ["위험관리 헤지", "자산 손실과 반대로 움직이는 통화를 보유", f"원/달러와 코스피 월간 상관 {CORR_KS_ALL:+.2f}(최근 3년 {CORR_KS_3Y:+.2f})", "달러 일부 보유"],
          ["정책 수급", "국민연금 전략적 환헤지(해외자산 10%)·한은 650억 달러 스와프", "2026년 말까지 연장(2025-12 기금위). 환율이 높을 때 달러 공급", "1,400원대 상단 제한, 2027년 연장 여부가 변수"]],
         [22, 26, 36, 16], note="캐리·가치·모멘텀은 외환 운용에서 널리 쓰는 세 가지 체계적 전략이다. 정책 수급 자료: 언론 보도(파이낸셜뉴스·SBS Biz 등, 2025-12).")
rp.para("세 가지 체계적 신호가 엇갈린다(캐리는 달러, 가치·모멘텀은 원화). 신호가 엇갈릴 때는 한쪽에 크게 걸지 않는 것이 원칙이다. 그래서 이 리포트의 결론도 방향 대신 "
        "'위기 때 원화가 약해지는 성질'을 이용한 헤지 비중 조절에 맞췄다. 다만 최근 3년은 원화와 코스피의 상관이 약해져(" + f"{CORR_KS_3Y:+.2f}" + ") 이 보험 효과가 예전보다 작다는 점은 감안해야 한다.", 8.2)

rp.h1("6. 투자 전략 (Strategy)")
rp.h2("6-1. 미국 자산 환헤지 비중")
rp.table([["2027-11 원/달러", "비헤지 환손익", "헤지 대비 차이", "언제 오나"],
          [w(RW_BAND[1]) + " (+1σ)", pc(RW_BAND[1] / FX - 1), pc(RW_BAND[1] / FX - 1 - R["hedge"]), "위험회피·달러 강세 — 국내 자산도 약할 때"],
          [w(FX) + " (그대로)", "0.0%", pc(-R["hedge"]), "헤지는 비용만큼 손해"],
          [w(RW_BAND[0]) + " (−1σ)", pc(RW_BAND[0] / FX - 1), pc(RW_BAND[0] / FX - 1 - R["hedge"]), "달러 약세·위험선호 — 국내 자산은 강할 때"]],
         [22, 18, 18, 42], note=f"헤지 비용 연 {abs(R['hedge'])*100:.2f}%(CD 91일 {R['cd91']:.2f}% − 미국 3개월물 {R['tb3']:.2f}%), 1년 선물환 {w(R['fwd'])}.")
rp.para("방향을 모르면 기대 환손익은 0에 가깝고, 헤지는 연 0.78%의 비용이 든다. 반면 비헤지의 손실(원화 강세)은 국내 자산이 좋을 때, 이익(원화 약세)은 국내 자산이 나쁠 때 생긴다. "
        "그래서 한국 투자자 전체 포트폴리오 기준으로는 비헤지가 위험을 줄인다. 다만 원화 강세 쪽 기관 전망과 최근 상관 약화를 감안해 헤지 40%를 남긴다.", 8.2)
rp.h2("6-2. 상품으로 구현하는 방법")
rp.table([["목적", "방법", "비고"],
          ["미국 주식·채권 (기본)", "환노출형 60% + 환헤지형(H) 40%", "같은 지수 상품으로 비율만 나눔"],
          ["보유 달러 원화 환전", f"{w(RW_BAND[1])} 위에서 분할", "+1σ — 국민연금 환헤지가 작동하는 구간과 겹침"],
          ["신규 달러 매수", f"{w(RW_BAND[0])} 아래에서 분할(미국달러선물 ETF·달러 예금)", "−1σ — 기관 전망(1,280원)과 겹치는 구간"],
          ["방향 베팅(레버리지·인버스)", "하지 않음", "모형·기관 전망이 엇갈리고 예측력 검증 실패"]], [26, 42, 32])
rp.h2("6-3. 업종 영향")
rp.table([["원/달러 방향", "유리", "불리", "이 포트폴리오의 관련 리포트"],
          ["상승(원화 약세)", "자동차·조선 등 수출, 해외자산 많은 보험(비헤지분)", "항공·원재료 수입", "현대자동차 개정판(환율 민감도), 한화생명·대한항공 재조사"],
          ["하락(원화 강세)", "항공·여행, 원재료 수입", "수출 업종", "대한항공 재조사"]], [18, 30, 20, 32])

rp.h1("7. 리스크와 결론 (Risk & Conclusion)", new_page=False)
rp.table([["리스크", "내용", "원/달러"],
          ["연준 추가 인상", "PCE 3.7%가 내려오지 않아 SEP 상단(4.4%)까지", "상승(단기금리차 −0.5%p → +1.3%)"],
          ["위험회피", "코스피 추가 하락·VIX 30", f"상승(약세 시나리오 {w(WK['fx'])})"],
          ["국민연금 환헤지 종료", "2026년 말 이후 연장되지 않으면 달러 공급 감소", "상승"],
          ["달러 약세·경상흑자", "기관 전망대로 2027년 달러 약세", "하락(1,200원대)"],
          ["모형 위험", "환율과 거시 변수의 관계가 다시 바뀜(3장)", "예측 불가 — 그래서 방향 베팅 안 함"]], [20, 50, 30])
rp.table([["항목", "내용"],
          ["판단", f"중립 — 12개월 중심값 {w(FX)}, ±1σ {w(RW_BAND[0])}~{w(RW_BAND[1])}"],
          ["모형", f"거시 6변수(VIF ≤ {max(R['vif_final'].values()):.1f}, HAC 유의, 공적분)는 설명용. 표본 밖 예측은 랜덤워크보다 못함(12개월 {FIN['12']['ec_ratio']:.2f}배)"],
          ["전략", f"미국 자산 비헤지 60%·헤지 40%, {w(RW_BAND[1])} 위 분할 환전, {w(RW_BAND[0])} 아래 분할 매수, 방향 베팅 없음"],
          ["확인할 지표", "① 12월 FOMC·SEP ② 한국은행 11월 수정 전망 ③ 국민연금 환헤지 2027년 연장 ④ VIX·코스피 ⑤ 월별 경상수지·해외증권투자"]], [18, 82])
rp.disclaimer("본 리포트는 한국은행 ECOS(국고채·CD 금리, 기준금리, 소비자물가, 경상수지), FRED(미국 CPI·연방기금금리·실업률), 연준 SEP(2026-09-16), MUFG 월간 외환전망(2026-11), "
              "한국은행·국내 증권사·국민연금 관련 언론 보도, yfinance(시세)를 바탕으로 작성한 개인 분석 자료입니다. 기관 전망은 교차확인에만 썼습니다. 특정 금융상품의 매매를 권유하지 않습니다.")
out = HERE / "환율전략_리서치리포트_20261109.docx"
rp.doc.save(out); print(out); to_pdf(out)
