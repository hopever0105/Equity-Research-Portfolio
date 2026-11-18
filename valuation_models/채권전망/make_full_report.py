"""채권전망_리서치리포트_20261118.docx/.pdf — 국고채·회사채 12개월 전망과 만기 전략 (ETF & Macro 신규, 둘째 편).
서식: valuation/tools/report_kit.py(표지만 이 파일 안에서 채권용으로 바꿈 — 공통 도구는 고치지 않음).
입력: results.json(model.py), rates_daily.csv, regression_monthly.csv. 실행: python valuation/채권전망/make_full_report.py
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from valuation.tools import report_kit as rk
from valuation.tools.report_kit import Rep, to_pdf, football_chart, W

R = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
SC, TR, VW, NM, MD = R["scen"], R["tr"], R["view"], R["names"], R["model"]
KS = list(SC.keys()); KH, KB, KC = KS[0], KS[1], KS[2]
short = {KH: "인상", KB: "동결(기본)", KC: "인하"}
y = lambda x: f"{x:.2f}%"
bp = lambda x: f"{x*100:+.0f}bp"
pp = lambda x, d=1: f"{x*100:.{d}f}%"
pv = lambda p: "<0.001" if p < 0.001 else f"{p:.3f}"
TAG = "20261118"

# ═════════════════════════ 차트
RD = pd.read_csv(HERE / "rates_daily.csv", index_col=0, parse_dates=True); RD = RD[RD.index <= R["now_d"]]
fig, a = plt.subplots(figsize=(3.6, 2.5), dpi=220)
for k, c, lab in (("ktb3", "#1F3864", "국고 3년"), ("ktb10", "#C00000", "국고 10년"), ("aa3", "#7F7F7F", "회사채 AA- 3년")):
    a.plot(RD.index, RD[k], color=c, lw=1.0, label=lab)
a.set_title("국내 금리(%), 2024-01~2026-11-17", fontsize=7); a.legend(fontsize=5.5, frameon=False); rk.ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / f"full_rates_{TAG}.png"); plt.close()

idx = pd.PeriodIndex(list(R["base_series"].keys()), freq="M").to_timestamp()
fig, a = plt.subplots(figsize=(7.2, 2.3), dpi=220)
a.step(idx, list(R["base_series"].values()), color="#7F7F7F", lw=1.0, where="post", label="기준금리")
a.plot(pd.PeriodIndex(list(R["ktb3_series"].keys()), freq="M").to_timestamp(), list(R["ktb3_series"].values()), color="#1F3864", lw=1.1, label="국고 3년")
a.plot(pd.PeriodIndex(list(R["ktb10_series"].keys()), freq="M").to_timestamp(), list(R["ktb10_series"].values()), color="#C00000", lw=1.0, label="국고 10년")
a.set_title("기준금리와 국고채 금리(월평균, %), 2015-01~2026-10", fontsize=7.5); a.legend(fontsize=6, frameon=False, ncol=3); rk.ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / f"full_long_{TAG}.png"); plt.close()

tp = pd.Series(R["tp3_series"]); tp.index = pd.PeriodIndex(tp.index, freq="M").to_timestamp()
rk.line_band_chart(list(tp.index), list(tp.values), R["tp3_mean"], R["tp3_sd"], HERE / f"full_tp_{TAG}.png",
                   f"국고 3년 − 기준금리(%p) — 평균 {R['tp3_mean']:.2f}, 지금 {R['tp3_now']:.2f}", "%p")

G = pd.read_csv(HERE / "regression_monthly.csv", index_col=0); G.index = pd.PeriodIndex(G.index, freq="M").to_timestamp()
fig, a = plt.subplots(figsize=(7.2, 2.3), dpi=220)
a.plot(G.index, G["ktb10"], color="#1F3864", lw=1.2, label="실제 국고 10년(월평균)")
a.plot(G.index, G["fitted"], color="#C00000", lw=1.0, ls="--", label="회귀 적정금리")
a.set_title(f"국고 10년 실제 vs 회귀 적정금리 (R² {R['r2']:.2f})", fontsize=7.5); a.legend(fontsize=6, frameon=False); rk.ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / f"full_fit_{TAG}.png"); plt.close()

names = list(TR.keys())
fig, a = plt.subplots(figsize=(7.2, 2.4), dpi=220)
wbar = .2
for i, (k, col) in enumerate(((KH, "#C00000"), (KB, "#1F3864"), (KC, "#8FAADC"))):
    a.bar([j + (i - 1) * wbar for j in range(len(names))], [TR[n]["sc"][k]["ret"] * 100 for n in names], wbar, color=col, label=short[k])
a.plot(range(len(names)), [TR[n]["exp"] * 100 for n in names], "D", color="#000000", ms=4, label="확률가중")
a.axhline(R["cd91"], color="#7F7F7F", ls="--", lw=.8); a.text(len(names) - .5, R["cd91"], f" 현금(CD) {R['cd91']:.2f}%", fontsize=6, va="bottom", ha="right")
a.set_xticks(range(len(names))); a.set_xticklabels(names, fontsize=6.8); a.set_ylabel("%", fontsize=6.5)
a.set_title("12개월 총수익(%) — 시나리오별", fontsize=7.5); a.legend(fontsize=6, frameon=False, ncol=4); rk.ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / f"full_tr_{TAG}.png"); plt.close()

cr = (RD["aa3"] - RD["ktb3"]) * 100
fig, a = plt.subplots(figsize=(7.2, 2.0), dpi=220)
a.plot(cr.index, cr.values, color="#1F3864", lw=1.0); a.axhline(cr.mean(), color="#7F7F7F", ls="--", lw=.8)
a.text(cr.index[-1], cr.mean(), f" 평균 {cr.mean():.0f}bp", fontsize=6, va="bottom", ha="right")
a.set_title("회사채 AA- 3년 − 국고 3년(bp), 2024-01~2026-11-17", fontsize=7.5); rk.ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / f"full_cred_{TAG}.png"); plt.close()

fig, a = plt.subplots(figsize=(7.2, 2.1), dpi=220)
a.plot(RD.index, RD["ktb10"], color="#C00000", lw=1.0, label="국고 10년")
a.plot(RD.index, RD["us10y"], color="#1F3864", lw=1.0, label="미국채 10년")
b = a.twinx(); b.fill_between(RD.index, (RD["ktb10"] - RD["us10y"]) * 100, 0, color="#D9E2F3", alpha=.6, label="한·미 차이(bp, 오른쪽)")
b.tick_params(labelsize=6); b.set_ylabel("bp", fontsize=6.5); b.spines["top"].set_visible(False)
a.set_zorder(b.get_zorder() + 1); a.patch.set_visible(False)
a.set_title("국고 10년과 미국채 10년(%), 2024-01~2026-11-17", fontsize=7.5); a.legend(fontsize=6, frameon=False, loc="upper left"); rk.ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / f"full_us_{TAG}.png"); plt.close()

# 금리 사이클별 국고3년 − 기준금리: 직전 12개월 기준금리 변화로 구분
bser = pd.Series(R["base_series"]); bser.index = pd.PeriodIndex(bser.index, freq="M")
tps = pd.Series(R["tp3_series"]); tps.index = pd.PeriodIndex(tps.index, freq="M")
chg12 = (bser - bser.shift(12)).reindex(tps.index)
REG = {"인상기 (12개월 기준금리 ↑)": tps[chg12 > 0], "동결기 (변화 없음)": tps[chg12 == 0], "인하기 (12개월 기준금리 ↓)": tps[chg12 < 0]}

football_chart([("국고 3년 (A. 기대가설)", SC[KC]["ktb3"], SC[KB]["ktb3"], SC[KH]["ktb3"]), ("국고 10년 (B. 회귀)", SC[KC]["ktb10"], SC[KB]["ktb10"], SC[KH]["ktb10"]),
                ("회사채 AA- 3년", SC[KC]["aa3"], SC[KB]["aa3"], SC[KH]["aa3"])], R["ktb3"], HERE / f"full_football_{TAG}.png", unit="%",
               xlabel="12개월 뒤 금리(%) · 막대=인하~인상, 점=동결(기본), 선=지금 국고 3년")

# ═════════════════════════ 표지
rp = Rep("ETF & Macro (채권)", "2026년 11월 18일")


def bond_cover(name, subtitle, view, png, rows, alt):
    t = rp.doc.add_table(rows=1, cols=1); rk.borders(t, rk.NAVY, "4"); c = t.cell(0, 0); rk.shade(c, rk.NAVY); c.width = Cm(W)
    rp.cellp(c, name, 17, True, "FFFFFF", WD_ALIGN_PARAGRAPH.LEFT)
    p = c.add_paragraph(); rk.run(p, subtitle, 9, False, "D9E2F3")
    rp.doc.add_paragraph()
    t = rp.doc.add_table(rows=1, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; rk.borders(t, "FFFFFF", "4")
    lc, rc = t.cell(0, 0), t.cell(0, 1); lc.width = Cm(W * .52); rc.width = Cm(W * .48)
    rt = lc.add_table(rows=1, cols=2); rk.borders(rt, "FFFFFF", "8")
    a_ = rt.cell(0, 0); rk.shade(a_, rk.GREEN); a_.width = Cm(3.2)
    rp.cellp(a_, view, 11, True, "FFFFFF"); p = a_.add_paragraph(); rk.run(p, "(만기 전략)", 6.5, False, "FFFFFF"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    b2 = rt.cell(0, 1); rk.shade(b2, rk.LIGHT); b2.width = Cm(5.8)
    rp.cellp(b2, "12개월 뒤 국고 3년 (확률가중)", 7, False, rk.GRAY, WD_ALIGN_PARAGRAPH.LEFT)
    p = b2.add_paragraph(); rk.run(p, y(R["exp3"]), 17, True, rk.NAVY)
    p = b2.add_paragraph(); rk.run(p, f"지금 {y(R['ktb3'])} → {bp((R['exp3'] - R['ktb3']) / 100)}", 7.5, True, rk.NAVY)
    for ln in alt:
        p = b2.add_paragraph(); rk.run(p, ln, 7, False, rk.GRAY)
    rp.img(png, W * .5, cont=lc); lc.paragraphs[0]._p.getparent().remove(lc.paragraphs[0]._p)
    rp.table([["항목", "수치"]] + rows, [55, 45], 7.2, cont=rc); rc.paragraphs[0]._p.getparent().remove(rc.paragraphs[0]._p)


ow = [n for n, v in VW.items() if v == "비중 확대"]; nt = [n for n, v in VW.items() if v == "중립"]
bond_cover("채권전망 — 국고채·회사채 12개월", "기준금리는 두 번 올린 뒤 멈출 가능성이 크고, 3년물은 그보다 더 올라 있다 — 중기물과 우량 회사채의 이자를 받는다",
           "중기물\n비중 확대", HERE / f"full_rates_{TAG}.png",
           [["기준금리 (2026-08 인상)", f"{R['base']:.2f}%"], ["국고 3년 / 10년 / 30년", f"{R['ktb3']:.3f} / {R['ktb10']:.3f} / {R['ktb30']:.3f}%"],
            ["회사채 AA- 3년", f"{R['aa3']:.3f}%"], ["CD 91일", f"{R['cd91']:.2f}%"],
            ["국고 3년 − 기준금리", f"{R['tp3_now']*100:.0f}bp (평균 {R['tp3_mean']*100:.0f}bp)"], ["국고 10년 − 3년", f"{R['slope_now']*100:.0f}bp (평균 {R['slope_mean']*100:.0f}bp)"],
            ["AA- − 국고 3년", f"{R['cred_now']*100:.0f}bp (2024~ 평균 {R['cred_mean']*100:.0f}bp)"], ["소비자물가 (전년비)", f"{R['inf']:.1f}% ({R['inf_m']})"],
            ["미국채 10년", f"{R['ust10']:.2f}%"], ["기준일", f"2026-11-17 금리 (11-18 작성)"]],
           [f"10년 확률가중 {y(R['exp10'])}", "비중 확대: " + ", ".join(ow), ("중립: " + ", ".join(nt)) if nt else ""])

rp.h2("한눈에 보기")
rp.table([["", "국고 3년", "국고 10년", "국고 30년", "회사채 AA- 3년"],
          ["지금 금리"] + [y(TR[n]["y0"]) for n in names],
          ["12개월 기대 총수익"] + [pp(TR[n]["exp"], 2) for n in names],
          ["인상 시나리오 총수익"] + [pp(TR[n]["sc"][KH]["ret"], 2) for n in names],
          ["현금(CD) 대비"] + [f"{TR[n]['vs_cash']*100:+.2f}%p" for n in names],
          ["의견"] + [VW[n] for n in names]], [24, 19, 19, 19, 19], hl_rows=(5,),
         note=f"의견 기준(안정적 자산배분): 확률가중 수익이 현금보다 1%p 이상 높고, 인상 시나리오에서도 현금({R['cd91']:.2f}%) 이상이면 비중 확대. 현금 이상·인상 시 현금 −2%p 이내면 중립.")
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", f"3년물은 기준금리보다 {R['tp3_now']*100:.0f}bp 높다 — 평균({R['tp3_mean']*100:.0f}bp)보다 추가 인상을 더 반영",
              [f"한은은 2026-07에 2.50% → 2.75%, 08월에 3.00%로 두 번 올렸다. 물가는 6월 3.2% → 10월 {R['inf']:.1f}%로 낮아지는 중",
               f"동결이면 12개월 뒤 국고 3년은 {y(SC[KB]['ktb3'])}(기준금리 + 평균 기간프리미엄)로 내려간다고 본다"])
rp.thesis_box("②", "장기물은 미국 금리와 물가에 묶여 있다 — 기대수익은 크지만 흔들림도 크다",
              [f"회귀 결과 국고 10년은 미국채 10년 1%p에 {MD['ust10']['coef']:.2f}%p, 물가 1%p에 {MD['inf']['coef']:.2f}%p 움직였다",
               f"국고 30년은 동결 시 {pp(TR['국고 30년']['sc'][KB]['ret'],1)}지만 인상 시 {pp(TR['국고 30년']['sc'][KH]['ret'],1)}로 현금보다 낮다"])
rp.thesis_box("③", "우량 회사채의 이자가 두껍다",
              [f"AA- 3년은 국고보다 {R['cred_now']*100:.0f}bp 높아 2024년 이후 최대({R['cred_max']*100:.0f}bp) 근처다",
               f"인상 시나리오에서도 12개월 총수익 {pp(TR['회사채 AA- 3년']['sc'][KH]['ret'],1)}로 현금보다 높다"])

rp.h1("1. 지금 상황 (Where We Are)")
rp.img(HERE / f"full_long_{TAG}.png", W)
rp.para(f"기준금리는 {', '.join(f'{d} {v:.2f}%' for d, v in R['base_chg'])}로 움직였다. 국고 3년은 52주 {y(R['lo52']['ktb3'])}~{y(R['hi52']['ktb3'])}, 10년은 {y(R['lo52']['ktb10'])}~{y(R['hi52']['ktb10'])}에서 움직였다. "
        f"미국채 10년이 {R['ust10']:.2f}%로 높아 한·미 10년 금리차는 {R['krus']*100:.0f}bp다.")
rp.h2("1-1. 스프레드 세 가지")
rp.img(HERE / f"full_tp_{TAG}.png", W)
rp.table([["스프레드", "지금", "평균", "해석"],
          ["국고 3년 − 기준금리", f"{R['tp3_now']*100:.0f}bp", f"{R['tp3_mean']*100:.0f}bp (2015~)", "시장이 추가 인상을 일부 반영"],
          ["국고 10년 − 3년", f"{R['slope_now']*100:.0f}bp", f"{R['slope_mean']*100:.0f}bp (2015~)", "장단기 곡선이 평평"],
          ["회사채 AA- − 국고 3년", f"{R['cred_now']*100:.0f}bp", f"{R['cred_mean']*100:.0f}bp (2024~)", "신용 스프레드가 넓은 편"]], [28, 14, 22, 36])

rp.img(HERE / f"full_cred_{TAG}.png", W)
rp.h2("1-2. 미국 금리와의 연결")
rp.img(HERE / f"full_us_{TAG}.png", W)
rp.para(f"국고 10년은 미국채 10년보다 {abs(R['krus'])*100:.0f}bp 낮다. 미국 금리가 높게 머무는 동안 국내 장기금리가 크게 내려가기 어렵다는 점이 장기물 판단의 핵심이다(3장 회귀에서 미국채 10년 계수 {MD['ust10']['coef']:.2f}).")

rp.h1("2. 방법 A — 기대가설과 기간프리미엄 (국고 3년)", new_page=False)
rp.h2("2-1. 금리 사이클별 기간프리미엄 (2015-01~2026-10)")
rp.table([["구간", "개월 수", "국고 3년 − 기준금리 평균", "최소 ~ 최대"]] +
         [[k, f"{len(v)}", f"{v.mean()*100:.0f}bp", f"{v.min()*100:.0f} ~ {v.max()*100:.0f}bp"] for k, v in REG.items() if len(v)],
         [34, 14, 26, 26], note="직전 12개월 사이 기준금리가 올랐으면 인상기, 내렸으면 인하기. 인상기에는 시장이 추가 인상을 미리 반영해 프리미엄이 커진다 — 인상 시나리오에 지금 수준을 쓴 근거.")
rp.h2("2-2. 시나리오")
rp.para(f"3년 금리는 앞으로 3년 동안의 기준금리 평균에 기간프리미엄을 더한 값으로 볼 수 있다. 12개월 뒤 기준금리를 시나리오별로 정하고, 기간프리미엄은 2015-01~2026-10 평균 {R['tp3_mean']*100:.0f}bp를 쓴다. "
        f"다만 인상 시나리오에서는 지금 수준({R['tp3_now']*100:.0f}bp)이 유지된다고 봤다.")
rp.table([["시나리오", "확률", "기준금리 (12개월 뒤)", "기간프리미엄", "국고 3년", "근거"]] +
         [[short[k], pp(s["p"], 0), f"{s['base']:.2f}%", f"{s['tp']*100:.0f}bp", y(s["ktb3"]), s["why"]] for k, s in SC.items()] +
         [["확률가중", "", "", "", y(R["exp3"]), ""]], [11, 8, 13, 12, 10, 46], hl_rows=(4,))

rp.h1("3. 방법 B — 국고 10년 회귀", new_page=False)
rp.para(f"2015-01~2026-10 월별 국고 10년을 후보 6개({', '.join(NM.values())})로 설명했다. VIF 10을 넘는 변수가 없어 모두 남겼고, HAC(뉴이-웨스트, 6개월) p값이 0.10을 넘는 변수를 하나씩 뺐다"
        f"({', '.join(NM[s[0]] + f' p={s[2]:.2f}' for s in R['steps'])}).")
rp.table([["후보 변수 (전체 모형)", "계수", "p값 (HAC)", "VIF"]] +
         [[NM[c], f"{R['full'][c]['coef']:+.3f}", pv(R["full"][c]["p"]), f"{R['vif_all'][c]:.1f}"] for c in NM], [40, 20, 20, 20],
         note="6개 모두 넣은 모형. VIF는 모두 10 미만(기준금리·미국 3개월물이 9.5 안팎으로 가장 높음).")
rp.table([["변수", "계수", "p값 (HAC)", "VIF", "뜻"]] +
         [[NM[c], f"{MD[c]['coef']:+.3f}", pv(MD[c]["p"]), f"{R['vif_final'][c]:.1f}",
           {"base": "기준금리 1%p ↑ → 10년 금리", "inf": "물가 1%p ↑ → 10년 금리", "ust10": "미국채 10년 1%p ↑ → 10년 금리", "ust3m": "미국 단기금리 ↑ (다른 변수 고정 시)"}.get(c, "")]
          for c in R["final"]], [26, 12, 14, 10, 38],
         note=f"표본 {R['n']}개월, R² {R['r2']:.3f}, 잔차 표준편차 {R['sd']*100:.0f}bp. 지금 적정금리 {y(R['fair10'])}, 실제와 차이 {R['resid_now']*100:+.0f}bp(시나리오에는 절반만 유지).")
rp.img(HERE / f"full_fit_{TAG}.png", W)
rp.h2("3-1. 표본 밖 점검 — 이 회귀를 그대로 믿지 않는 이유")
rp.para(f"2015~2022년으로 추정한 식으로 2023-01~2026-10을 예측하면(실제 설명변수 사용) 오차(RMSE)는 {R['oos_rmse']*100:.0f}bp, 평균 {R['oos_bias']*100:+.0f}bp 치우쳤다. "
        f"'지난달 값 그대로' 방법의 한 달 오차 {R['rw_rmse']*100:.0f}bp보다 크다. 회귀는 금리의 '수준'이 어디쯤이 자연스러운지 보는 데 쓰고, 한 달 단위 예측에는 쓰지 않는다. "
        "그래서 10년 전망은 시나리오 입력값(미국 금리·물가)에 따른 범위로 제시한다.")
sn = R["sens"]
rp.table([["기준금리 \\ 미국채 10년"] + [f"{u:.2f}%" for u in sn["ust"]]] + [[f"{b:.2f}%"] + [y(x) for x in row] for b, row in zip(sn["base"], sn["v"])],
         [24, 15, 15, 15, 15, 16], note="12개월 뒤 국고 10년(물가 2.4%, 잔차 절반 유지).")

rp.h1("4. 방법 C — 시나리오별 12개월 총수익", new_page=False)
rp.para("총수익 = 이자(지금 금리) + 롤다운(1년 지나 만기가 짧아지며 금리가 내려가는 효과) − 듀레이션 × 금리 변화 + ½ × 볼록성 × 금리 변화². "
        "듀레이션·볼록성은 액면(쿠폰 = 금리) 반기 이표채로 계산했고, 30년물 금리는 10년물에 지금 30−10년 차이를 더했다.")
rp.table([["", "지금 금리", "롤다운", "1년 뒤 듀레이션"] + [short[k] for k in KS] + ["확률가중"]] +
         [[n, y(TR[n]["y0"]), f"{TR[n]['roll_bp']:.0f}bp", f"{TR[n]['dur']:.1f}"] + [pp(TR[n]["sc"][k]["ret"], 2) for k in KS] + [pp(TR[n]["exp"], 2)] for n in names],
         [18, 11, 10, 13, 12, 12, 12, 12])
rp.img(HERE / f"full_tr_{TAG}.png", W)
rp.h2("4-1. 시나리오별 12개월 뒤 금리")
rp.table([["", "기준금리", "국고 3년", "국고 10년", "국고 30년", "회사채 AA- 3년", "근거"]] +
         [[short[k], f"{s_['base']:.2f}%", y(s_["ktb3"]), y(s_["ktb10"]), y(s_["ktb30"]), y(s_["aa3"]), f"물가 {s_['inf']:.1f}%, 미국채 10년 {s_['ust10']:.2f}%, AA- 스프레드 {s_['cred']*100:.0f}bp"] for k, s_ in SC.items()] +
         [["지금", f"{R['base']:.2f}%", y(R["ktb3"]), y(R["ktb10"]), y(R["ktb30"]), y(R["aa3"]), ""]], [11, 10, 10, 10, 10, 13, 36], hl_rows=(4,))
rp.h2("4-2. 12개월 이자를 다 까먹는 금리 상승폭")
rp.table([["", "이자 + 롤다운", "1년 뒤 듀레이션", "손익분기 금리 상승", "현금(CD)과 같아지는 상승"]] +
         [[n, f"{TR[n]['y0'] + TR[n]['roll_bp']/100:.2f}%", f"{TR[n]['dur']:.1f}", f"{(TR[n]['y0'] + TR[n]['roll_bp']/100) / TR[n]['dur'] * 100:.0f}bp",
           f"{(TR[n]['y0'] + TR[n]['roll_bp']/100 - R['cd91']) / TR[n]['dur'] * 100:.0f}bp"] for n in names], [22, 18, 18, 21, 21],
         note="손익분기 = (이자 + 롤다운) ÷ 듀레이션. 1년 뒤 같은 채권 금리가 이만큼 오르면 12개월 총수익이 0(또는 현금 수준)이 된다.")
rp.img(HERE / f"full_football_{TAG}.png", W)

rp.h1("5. 과거 점검 — 연도별 만기 성과 (2015~2025)", new_page=False)
EM = pd.read_csv(HERE.parents[0] / "환율전략" / "ecos_monthly.csv", index_col=0); EM.index = pd.PeriodIndex(EM.index, freq="M")
D3, D10 = TR["국고 3년"]["dur"], TR["국고 10년"]["dur"]
hist_rows, wins = [], {"3": 0, "10": 0}
for yr in range(2015, 2026):
    a0, a1 = pd.Period(f"{yr-1}-12", "M"), pd.Period(f"{yr}-12", "M")
    r3 = EM.loc[a0, "ktb3"] - D3 * (EM.loc[a1, "ktb3"] - EM.loc[a0, "ktb3"])
    r10 = EM.loc[a0, "ktb10"] - D10 * (EM.loc[a1, "ktb10"] - EM.loc[a0, "ktb10"])
    cash = EM.loc[f"{yr}-01":f"{yr}-12", "cd91"].mean()
    bchg = EM.loc[a1, "base"] - EM.loc[a0, "base"]
    wins["3"] += r3 > cash; wins["10"] += r10 > cash
    hist_rows.append([str(yr), f"{bchg:+.2f}%p", f"{r3:.1f}%", f"{r10:.1f}%", f"{cash:.1f}%", "3년" if r3 > max(r10, cash) else ("10년" if r10 > cash else "현금")])
rp.para("지금의 판단이 과거에도 통했는지 보려고, 매년 말 국고 3년·10년을 사서 1년 들고 있었다면 얼마를 벌었을지 근사 계산했다(이자 + 듀레이션 × 금리 변화, 롤다운 제외). 현금은 그해 CD 91일 평균.")
rp.table([["연도", "기준금리 변화", "국고 3년", "국고 10년", "현금(CD)", "가장 나은 것"]] + hist_rows, [12, 18, 16, 16, 16, 22],
         note=f"국고 3년이 현금보다 나았던 해 {wins['3']}/11, 국고 10년 {wins['10']}/11. 듀레이션은 4장 값(3년물 {D3:.1f}, 10년물 {D10:.1f}) 고정. 자료: ECOS 월평균.")
rp.para("기준금리를 크게 올린 2021~2022년에는 10년물이 현금보다 크게 뒤졌고(2022년 −8.0%), 3년물은 손실 폭이 작았다(−1.7%). 인하한 2015·2019·2024년에는 10년물 수익이 가장 컸지만, "
        "2020·2025년처럼 인하해도 장기금리가 올라 10년물이 뒤진 해도 있었다. "
        "인상 가능성이 남아 있는 지금은 손실 폭이 작은 중기물을 중심에 두는 근거다.", 8.5)

rp.h1("6. 전략과 결론 (Strategy)")
rp.table([["구분", "의견", "이유"]] +
         [[n, VW[n], f"기대 {pp(TR[n]['exp'],1)}, 인상 시 {pp(TR[n]['sc'][KH]['ret'],1)}, 현금 대비 {TR[n]['vs_cash']*100:+.1f}%p"] for n in names], [22, 14, 64])
rp.para(f"안정적인 자산배분 관점에서 결론은 **국고 3년 안팎 중기물과 AA- 우량 회사채 3년의 비중 확대**다. 두 자산은 기준금리가 한 번 더 올라도 12개월 수익이 현금(CD {R['cd91']:.2f}%)보다 높다. "
        f"국고 10년도 기대수익은 크지만(확률가중 {pp(TR['국고 10년']['exp'],1)}) 회귀의 예측력이 약해 비중은 중기물보다 작게 둔다. "
        f"국고 30년은 동결·인하에서 수익이 크지만 인상 시 현금보다 낮아 {VW['국고 30년']}이다.", 8.5)
rp.h2("6-1. 배분 예시 (채권 몫 100 기준)")
MIX = {"국고 3년": 0.40, "회사채 AA- 3년": 0.30, "국고 10년": 0.20, "국고 30년": 0.0}
cash_w = 1 - sum(MIX.values())
mix_sc = {k: sum(w_ * TR[n]["sc"][k]["ret"] for n, w_ in MIX.items()) + cash_w * R["cd91"] / 100 for k in KS}
mix_exp = sum(SC[k]["p"] * v for k, v in mix_sc.items())
rp.table([["구성", "비중"]] + [[n, pp(w_, 0)] for n, w_ in MIX.items() if w_] + [["현금(CD)", pp(cash_w, 0)]] +
         [["시나리오별 12개월 수익", " · ".join(f"{short[k]} {pp(v,1)}" for k, v in mix_sc.items())], ["확률가중", pp(mix_exp, 2)]], [40, 60],
         note="중기물·우량 회사채 중심으로 인상 시나리오에서도 현금보다 높은 수익을 노리는 구성. 국고 30년은 인상 시 현금보다 낮아 넣지 않았다.")
rp.h2("이 판단을 바꿀 조건")
rp.table([["지표", "확인 시점", "바뀌는 판단"],
          ["소비자물가 전년비 3% 재돌파", "매월 초 통계청 발표", "인상 확률 상향 → 장기물 축소"],
          ["한은 금리 결정·의사록", "금통위 회의", "인상 시사 시 3년물 기간프리미엄 유지 가정"],
          ["미국채 10년 5.25% 이상", "매일", "국고 10년 상승 압력 → 10년 비중 축소"],
          ["AA- 스프레드 76bp(최근 최대) 초과", "매일", "신용 위험 확대 → 회사채 비중 재검토"]], [34, 26, 40])
rp.h2("리스크")
rp.table([["방향", "리스크", "내용"],
          ["금리 상승", "물가 재상승", "유가·환율로 물가가 다시 3%를 넘으면 추가 인상과 장기금리 상승"],
          ["금리 상승", "미국 금리", "미국채 10년이 5%대에 머물면 국고 장기물 금리 하락이 제한됨"],
          ["금리 하락", "경기 둔화", "성장 둔화가 빨라지면 인하와 함께 장기물 수익이 크게 늘어남(30년 인하 시나리오)"],
          ["신용", "회사채 스프레드", "기업 실적 악화 시 AA- 스프레드 확대"]], [14, 18, 68])
rp.disclaimer("본 리포트는 한국은행 ECOS(기준금리, 국고채·회사채·CD 금리, 소비자물가), yfinance(미국채 금리, VIX, WTI), FRED(연방기금금리)를 바탕으로 작성한 개인 분석 자료입니다. "
              "시나리오 확률과 입력값은 작성자의 가정이며, 특정 상품의 매매를 권유하지 않습니다.")
out = HERE / f"채권전망_리서치리포트_{TAG}.docx"
rp.doc.save(out); print(out); to_pdf(out)
