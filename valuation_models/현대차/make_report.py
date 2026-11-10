"""현대차_분석보고서.docx/.pdf 생성 (results.json·price_db.csv·fx_usdkrw.csv 기반). 실행: python valuation/현대차/make_report.py"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
B, L, H = R["scen"]["기본"], R["scen"]["보수"], R["scen"]["낙관"]
PRICE = R["price"]; NOW = R["now"]; HS = R["hist_stats"]; IM = R["implied"]; ST = R["stakes"]; QQ = R["q"]; FXQ = R["fx_q"]
TP = round(B["tp"] / 5_000) * 5_000
UP = TP / PRICE - 1
RATING = "BUY" if UP >= 0.15 else ("HOLD" if UP >= -0.05 else "SELL")
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
NAVY = "1F3864"

# ───────── 차트 1: 방법별 가치 범위(보수~낙관) vs 기준주가
fig, ax = plt.subplots(figsize=(7.2, 2.0), dpi=200)
rows = [("본업 PER 2027E (50%)", L["tp_per"], B["tp_per"], H["tp_per"]), ("본업 PBR 2026E (50%)", L["tp_pbr"], B["tp_pbr"], H["tp_pbr"]),
        ("본업 가치", L["tp_core"], B["tp_core"], H["tp_core"]), ("목표가 = 본업 + 로봇(BD)", L["tp"], B["tp"], H["tp"])]
for i, (n, lo, mid, hi) in enumerate(rows[::-1]):
    ax.barh(i, (hi - lo) / 1e4, left=lo / 1e4, color="#9DB4D6" if not n.startswith("목표가") else "#2F5597", height=0.5)
    ax.plot(mid / 1e4, i, "o", color="white", mec="#1F3864", ms=6)
    ax.text(hi / 1e4 + 0.8, i, f"{mid/1e4:.1f}만", va="center", fontsize=7)
ax.set_yticks(range(4)); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=8)
ax.axvline(PRICE / 1e4, color="#C00000", ls="--", lw=1); ax.text(PRICE / 1e4, 3.5, f"기준주가 {PRICE:,.0f}", color="#C00000", fontsize=7, ha="center")
ax.set_xlabel("주당 가치(만원) · 막대=보수~낙관, 점=기본", fontsize=7); ax.tick_params(axis="x", labelsize=7)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_xlim(15, 50); plt.tight_layout(); plt.savefig(HERE / "football.png"); plt.close()

# ───────── 차트 2: 주가 vs 원/달러 (2025-10 ~ 기준일), 분기 영업이익
px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str})
px = px[(px.종목코드 == "005380")].assign(d=lambda x: pd.to_datetime(x.날짜)).query("d <= '2026-10-02'").set_index("d")["종가"]
fx = pd.read_csv(HERE / "fx_usdkrw.csv").assign(d=lambda x: pd.to_datetime(x.date.astype(str))).set_index("d")["value"]["2025-10-20":"2026-10-02"]
fig, (a1, a3) = plt.subplots(1, 2, figsize=(7.2, 2.3), dpi=200, gridspec_kw={"width_ratios": [1.7, 1]})
a1.plot(px.index, px / 1e4, color="#1F3864", lw=1.2); a1.set_ylabel("주가(만원)", fontsize=7, color="#1F3864")
a2 = a1.twinx(); a2.plot(fx.index, fx, color="#C55A11", lw=1); a2.set_ylabel("원/달러", fontsize=7, color="#C55A11"); a2.invert_yaxis()
a1.set_title("주가 vs 원/달러(축 반전: 위로 갈수록 원화 약세)", fontsize=7.5)
for a in (a1, a2): a.tick_params(labelsize=6)
a1.spines["top"].set_visible(False); a2.spines["top"].set_visible(False)
qs = ["3Q25", "4Q25", "1Q26", "2Q26"]
a3.bar(qs, [QQ[q]["op"] for q in qs], color="#9DB4D6"); a3.set_title("분기 영업이익(조원)과 평균 환율", fontsize=7.5)
for i, q in enumerate(qs):
    a3.text(i, QQ[q]["op"] + 0.05, f"{QQ[q]['op']:.2f}\n{FXQ[q]:,.0f}원", ha="center", fontsize=6)
a3.set_ylim(0, 3.6); a3.tick_params(labelsize=6)
for s in ("top", "right"): a3.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(HERE / "price_fx.png"); plt.close()

# ───────── 문서 유틸
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(1.5); sec.top_margin = Cm(1.2); sec.bottom_margin = Cm(1.2)
st = doc.styles["Normal"]; st.font.name = "Malgun Gothic"; st.font.size = Pt(8.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Malgun Gothic")
st.paragraph_format.space_after = Pt(2); st.paragraph_format.space_before = Pt(0)


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcPr.append(s)


def para(text="", bold=False, size=None, color=None, align=None, after=None):
    p = doc.add_paragraph(); r = p.add_run(text); r.bold = bold
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    if align: p.alignment = align
    if after is not None: p.paragraph_format.space_after = Pt(after)
    return p


def h(text):
    p = para(text, bold=True, size=10.5, color=NAVY, after=2); p.paragraph_format.space_before = Pt(5)
    pPr = p._p.get_or_add_pPr(); b = OxmlElement("w:pBdr"); bt = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", "6"), ("space", "1"), ("color", NAVY)): bt.set(qn(f"w:{k}"), v)
    b.append(bt); pPr.append(b)


def bullet(text):
    p = doc.add_paragraph(style="List Bullet"); p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Cm(0.5)
    r = p.add_run(text); r.font.size = Pt(8.5)


def table(rows, header=True, widths=None, size=7.5, bold_last=False, first_left=True):
    t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = ""; p = c.paragraphs[0]; r = p.add_run(str(v)); r.font.size = Pt(size)
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and first_left) else WD_ALIGN_PARAGRAPH.CENTER
            if header and i == 0:
                r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); shade(c, NAVY)
            if bold_last and i == len(rows) - 1: r.bold = True; shade(c, "DEEAF6")
    if widths:
        for row in t.rows:
            for j, w in enumerate(widths): row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


f0 = lambda x: f"{x:,.0f}"
f1 = lambda x: f"{x:,.1f}"
f2 = lambda x: f"{x:,.2f}"
pc = lambda x: f"{x*100:.1f}%"
fxd = (FXQ["4Q25"], R["fx_spot"])

# ───────── 1. 표제·투자의견
RB = R["robot"]
para("현대자동차 (005380) 기업분석 보고서 — 본업·환율·로봇(BD) 가치로 다시 본 적정가치", bold=True, size=14, color=NAVY, after=0)
para(f"작성일 2026-10-06 · 기준주가 {PRICE:,.0f}원 (2026-10-02 종가, 10/5 대체공휴일 휴장) · 시가총액 {R['mcap']:.1f}조원(보통+우선) · 작성: 송호빈 (포트폴리오용, 투자권유 아님)", size=8, color="595959", after=3)
table([["투자의견", "목표주가(12M)", "상승여력", "PER 26E / 27E", "PBR 26E (7년 범위)", "배당수익률(분기 2,500원×4)"],
       [RATING, f"{TP:,}원", f"{UP*100:+.1f}%", f"{NOW['per_26']:.1f}x / {NOW['per_27']:.1f}x",
        f"{NOW['pbr_26']:.2f}x ({HS['pbr_min']:.2f}~{HS['pbr_max']:.2f}x)", pc(NOW["dy"])]], size=9)
para(f"▶ 목표주가 = 본업 가치 [PER(2027E EPS {B['eps27']:,.0f}원 × {B['per']:.1f}배) 50% + PBR(2026E말 BPS {B['bps26']:,.0f}원 × {B['pbr']:.2f}배) 50% = {B['tp_core']:,.0f}원] "
     f"+ 로봇(보스턴다이내믹스) 가치 [BD {B['bd']:.1f}조 × 현대차 실질 지분 {RB['look']*100:.1f}% − 이미 반영된 장부가 → 주당 {B['tp_robot']:+,.0f}원] = {B['tp']:,.0f}원 → 5,000원 단위 반올림. "
     f"보수 {L['tp']:,.0f}원({L['upside']*100:+.0f}%) · 기본 {B['tp']:,.0f}원({B['upside']*100:+.0f}%) · 낙관 {H['tp']:,.0f}원({H['upside']*100:+.0f}%). 투자의견 기준: +15% 이상 BUY, -5%~+15% HOLD, -5% 미만 SELL.", size=8.5, after=1)
para(f"▶ 핵심: 기준주가는 2027E 영업이익률 {IM['opm_need']*100:.1f}%(환율 중립)를 가정해야 정당화된다. 회사 2026 가이던스 상단(7.3%){'보다 높고' if IM['opm_need'] > 0.0735 else ' 수준이고'}, 최근 4개 분기 실적(3.6~5.8%)과 거리가 멀다. "
     f"여기에 원/달러가 2Q26 평균 {FXQ['2Q26']:,.0f}원에서 10/2 {R['fx_spot']:,.1f}원으로 내려와(원화 강세) 2027E 영업이익을 약 {abs(B['fx_eff']):.2f}조원 깎는다. 로봇 쪽에서 보면 기준주가는 BD 가치 약 {RB['implied_bd_at_price']:.0f}조원(증권가 기대 30~60조의 하단)을 이미 반영하고 있고, 6/1 고점 750,000원은 약 {RB['implied_bd_at_peak']:.0f}조원을 반영했다. 증권사 목표가는 계산에 넣지 않았다.", size=8.5, color="C00000", after=1)
doc.add_picture(str(HERE / "football.png"), width=Cm(16.0)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

# ───────── 2. 투자포인트
h("1. 투자포인트")
bullet(f"이익이 아니라 멀티플이 움직였다: 2025-10-30 265,000원 → 2026-06-01 750,000원(종가 최고, 장중 783,000원) → 10/2 {PRICE:,.0f}원. 같은 기간 분기 영업이익은 "
       f"{QQ['3Q25']['op']:.2f} · {QQ['4Q25']['op']:.2f} · {QQ['1Q26']['op']:.2f} · {QQ['2Q26']['op']:.2f}조원에 머물렀다. 고점 대비 -54%(종가 기준) 내려왔지만 "
       f"2026E PBR {NOW['pbr_26']:.2f}x는 2019~2025년 연말 PBR 범위({HS['pbr_min']:.2f}~{HS['pbr_max']:.2f}x)의 상단이고, 2027E PER {NOW['per_27']:.1f}x는 같은 기간 중앙값 {HS['per_med']:.1f}x(2020 제외)보다 높다. 로봇 프리미엄은 아직 다 빠지지 않았다.")
bullet(f"로봇은 가치에 넣되 지분 구조대로 넣는다: 현대차는 BD를 직접 갖고 있지 않다. 관계기업 HMG Global LLC(지분 49.5%, 장부가 {RB['book']:.2f}조원)를 통해 보유하고, 그룹 계열사 합계 BD 지분은 68%다(2026 반기보고서). "
       f"따라서 현대차 몫은 최대 {RB['look']*100:.1f}%이고, BD 가치 1조원은 현대차 주당 약 {RB['look']*1e12/R['shares']:,.0f}원이다. 시장 기대 하단인 30조원을 넣어도 주당 {RB['ps']['낙관']:,.0f}원(장부가 차감 후)이다. "
       f"반대로 기준주가를 본업 가치({B['tp_core']:,.0f}원)로 설명하고 남는 부분은 BD 가치 약 {RB['implied_bd_at_price']:.0f}조원에 해당한다. 로봇 생산 계획(아틀라스 현장 투입 준비, 2028년 연 3만 대 생산 체계, 2025 사업보고서)은 장기 가치의 근거지만, "
       f"상장·수익화 전까지는 거래 증거(풋옵션 5.2조원)와 시장 기대(30조원)의 중간인 {B['bd']:.1f}조원을 기본값으로 둔다.")
bullet(f"환율이 이익의 방향을 바꾼다: 2Q26 영업이익 증감 중 환율 효과는 +2,380억원(평균 1,502원, +7.0% YoY, 회사 IR). 이를 연 기준으로 바꾸면 원화 1% 움직임에 영업이익 약 {R['fx_sens']*1e4:,.0f}억원이다. "
       f"원/달러 월평균은 6월 1,527원 → 9월 1,359원으로 11% 내려왔고, 4Q26을 10/2 수준({R['fx_spot']:,.0f}원)으로 두면 전년 4Q({FXQ['4Q25']:,.0f}원) 대비 -6%다. "
       f"2027E 환율 {B['fx27']:,}원(2026 평균 {R['fx26']:,.0f}원 대비 {B['fx_chg']:.1f}%)은 영업이익 {B['fx_eff']:+.2f}조원 요인이다. 관세(분기 1.8조 → 0.9조원) 완화 효과를 환율이 되돌리는 구간이다.")
bullet(f"본업 체력과 주주환원은 하단을 받친다: 미국 하이브리드 판매 신기록(9월 미국 7.7만대, +9%), 2030년 영업이익률 목표 9+α%(2026-08-26 CEO Investor Day 공시), 분기배당 2,500원, "
       f"자기주식 소각(8/31, 보통 1,291,274주·우선 1,214,332주). 상장 관계사 지분(기아 35.17% 등) 시가만 {ST['total']:.1f}조원으로 시가총액의 {ST['share_of_mcap']*100:.0f}%다. 다만 이는 이미 지분법이익으로 EPS·BPS에 들어 있어 따로 더하지 않았다.")

# ───────── 3. 실적·재무
h("2. 실적·재무 (연결, 조원)")
fy = R["fy"]
table([["", "FY23", "FY24", "FY25", "3Q25", "4Q25", "1Q26", "2Q26", "3Q26E", "4Q26E", "2026E", "2027E"],
       ["매출", f1(fy["2023"]["rev"]), f1(fy["2024"]["rev"]), f1(fy["2025"]["rev"]), f1(QQ["3Q25"]["rev"]), f1(QQ["4Q25"]["rev"]), f1(QQ["1Q26"]["rev"]), f1(QQ["2Q26"]["rev"]),
        f1(45.5), f1(48.5), f1(B["rev26"]), f1(B["rev27"])],
       ["영업이익", f2(fy["2023"]["op"]), f2(fy["2024"]["op"]), f2(fy["2025"]["op"]), f2(QQ["3Q25"]["op"]), f2(QQ["4Q25"]["op"]), f2(QQ["1Q26"]["op"]), f2(QQ["2Q26"]["op"]),
        "2.40", "2.90", f2(B["op26"]), f2(B["op27"])],
       ["영업이익률", pc(fy["2023"]["opm"]), pc(fy["2024"]["opm"]), pc(fy["2025"]["opm"]), pc(QQ["3Q25"]["opm"]), pc(QQ["4Q25"]["opm"]), pc(QQ["1Q26"]["opm"]), pc(QQ["2Q26"]["opm"]),
        pc(2.4 / 45.5), pc(2.9 / 48.5), pc(B["opm26"]), pc(B["opm27_rep"])],
       ["지배순이익", f2(fy["2023"]["ni_p"]), f2(fy["2024"]["ni_p"]), f2(fy["2025"]["ni_p"]), f2(QQ["3Q25"]["ni_p"]), f2(QQ["4Q25"]["ni_p"]), f2(QQ["1Q26"]["ni_p"]), f2(QQ["2Q26"]["ni_p"]),
        "", "", f2(B["ni26"]), f2(B["ni27"])],
       ["평균 원/달러", "", "", "", f0(FXQ["3Q25"]), f0(FXQ["4Q25"]), f0(FXQ["1Q26"]), f0(FXQ["2Q26"]), f0(FXQ["3Q26"]), f0(R["fx_spot"]) + "(가정)", f0(R["fx26"]), f0(B["fx27"])]], size=6.8)
para("출처: DART 연결재무제표(사업·분기·반기보고서, 4Q25 = 연간 − 3Q 누적), 한국은행 ECOS 원/달러 매매기준율(분기 평균). 2Q26 매출 49.2조(+1.9%), 영업이익 2.85조(-20.8%, 전년 3.60조) 공시값 일치. "
     "1H26 부문 영업이익: 차량 3.76조 · 금융 약 1.34조(연결 − 차량 − 기타 역산) · 기타 0.27조(반기보고서). 3Q26E는 자체 추정(전년 2.54조 + 관세 완화 약 +0.9조 + 환율 +0.1조 − 파업 손실 약 -0.6조 − 믹스·원가 약 -0.5조), "
     "교차확인: NH 2.40조(10/6), 다올 2.47조(9/7). 3Q 실적 발표는 10월 말 예정.", size=7, color="595959")
doc.add_picture(str(HERE / "price_fx.png"), width=Cm(16.5)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
para("2Q26 영업이익 증감(YoY, 회사 IR 2026-07-23): 판매 믹스 -5,700억 · 판매 물량 -5,420억(부품사 화재) · 환율 +2,380억 · 금융 +1,060억. 9월 판매(공시 2026-10-01): 국내 49,022대(-25.7%) · 해외 258,976대(-13.9%) · 합계 307,998대(-16.0%). "
     "파업: 7/13~15 부분파업, 8/21 전일 파업(생산중단 공시), 9/2 단체교섭 타결·생산재개. 생산차질 약 5.5만대(언론 추정, 파이낸셜뉴스 2026-08-22).", size=7.5)

# ───────── 4. 밸류에이션
h("3. 밸류에이션")
table([["방법", "가중치", "핵심 가정 (기본)", "주당 가치(원)", "보수 / 낙관"],
       ["PER", "50%", f"2027E EPS {B['eps27']:,.0f}원 × {B['per']:.1f}배. 2019~25 연말 PER 중앙값 {HS['per_med']:.1f}x·평균 {HS['per_mean']:.1f}x(2020 제외) 위에 주주환원 확대(분기배당·소각)를 반영해 소폭 할증",
        f0(B["tp_per"]), f"{L['tp_per']:,.0f} / {H['tp_per']:,.0f}"],
       ["PBR", "50%", f"2026E말 BPS {B['bps26']:,.0f}원 × {B['pbr']:.2f}배. 7년 연말 PBR 평균 {HS['pbr_mean']:.2f}x·최고 {HS['pbr_max']:.2f}x, 2027E ROE {B['roe27']*100:.1f}%(FY25 8.2%에서 PBR 0.68x)",
        f0(B["tp_pbr"]), f"{L['tp_pbr']:,.0f} / {H['tp_pbr']:,.0f}"],
       ["본업 가치", "PER·PBR 50:50", "자동차·금융·관계사(지분법) 포함", f0(B["tp_core"]), f"{L['tp_core']:,.0f} / {H['tp_core']:,.0f}"],
       ["+ 로봇(BD) SOTP", "가산", f"BD 100% {B['bd']:.1f}조 × 실질 지분 {RB['look']*100:.1f}% − HMG Global 장부가 {RB['book']:.2f}조 (보수 5.2조 · 낙관 30조)", f0(B["tp_robot"]), f"{L['tp_robot']:,.0f} / {H['tp_robot']:,.0f}"],
       ["목표가", "", f"→ {TP:,}원 (5,000원 단위)", f0(B["tp"]), f"{L['tp']:,.0f} / {H['tp']:,.0f}"]], size=7.5, bold_last=True, widths=[2.6, 1.8, 8.8, 2.3, 3.0])
para("로봇(보스턴다이내믹스) 가치 산정", bold=True, size=8.5)
table([["단계", "값", "근거"],
       ["① 현대차 → HMG Global LLC", "49.5% (장부가 2.85조)", "2026 반기보고서 관계기업 목록(신사업 투자·관리, 미국)"],
       ["② 그룹 계열사 → BD", "68% (현대차 직접 보유 없음)", "2026 반기보고서 계열회사 지분 표"],
       ["③ 현대차 실질 지분", f"{RB['look']*100:.1f}% (= ① × ②)", "그룹 68%가 모두 HMG Global 경유라는 가정 → 상한, 확인 필요"],
       ["④ BD 100% 가치", f"보수 5.2조 · 기본 {B['bd']:.1f}조 · 낙관 30조", "풋옵션 매입가 환산 / 두 값의 기하평균 / 증권가 상장 기대 하단"],
       ["⑤ 주당 가산액", f"{L['tp_robot']:+,.0f} · {B['tp_robot']:+,.0f} · {H['tp_robot']:+,.0f}원", "③×④ − HMG Global 장부가(이미 BPS에 포함, 이중계산 제거)"],
       ["⑥ 시장이 내포한 BD 가치", f"기준주가 {RB['implied_bd_at_price']:.0f}조 · 6/1 고점 {RB['implied_bd_at_peak']:.0f}조", "(주가 − 본업 가치) × 주식수 + 장부가, ÷ 실질 지분 (본업 가치는 기본 시나리오로 고정)"]], size=7.2, widths=[4.2, 5.4, 8.4])
para(f"해석: 2026년 상반기 랠리(265,000 → 750,000원)는 BD 가치로 환산하면 약 {RB['implied_bd_at_peak']:.0f}조원을 반영한 셈이다. KB증권의 최상단 시나리오(134조원)보다도 높다. 기준주가 {PRICE:,.0f}원도 BD를 약 {RB['implied_bd_at_price']:.0f}조원으로 본 가격이라, 시장 기대 하단(30조원)은 이미 주가에 들어 있다. "
     f"로봇 가치를 넣어도 결론이 바뀌지 않는 이유는 현대차 몫이 {RB['look']*100:.0f}% 수준이고, 주식수가 2.6억 주라 BD 1조원이 주당 {RB['look']*1e12/R['shares']:,.0f}원에 그치기 때문이다.", size=7.5)
para("방법 선택 이유", bold=True, size=8.5)
para(f"① 금융 부문(현대캐피탈 등) 차입이 연결 부채에 섞여 있어(6월말 사채 116조·유동성장기부채 40조원) EV/EBITDA·DCF는 순차입금 정의에 따라 결과가 크게 바뀐다. 그래서 이익(PER)과 순자산(PBR)을 같은 비중으로 썼다. "
     f"② ROE 기반 적정 PBR 공식((ROE−g)/(COE−g), COE = 국고채 10년 4.37%(10/2) + β1.0×ERP 4.87% = 9.2%, g 2%)에 2023~24년 ROE 11~13%를 넣으면 1.3x 안팎이 나오지만, 현대차는 그때 실제로 PBR 0.5~0.6x에 거래됐다. 시장 정합성이 낮아 과거 밴드를 기준으로 삼았다. "
     f"③ 원본 리포트(10/6)의 목표가 447,000원은 증권사 목표가 평균·최저치(가중 60%)와 현재가(15%)를 섞은 값이어서 독자 평가로 볼 수 없어 폐기했다. 최근 증권사 목표가(Citi 45.5만 · 삼성 50만 · NH 54만 · 노무라 52만원, 2026.9~10)는 교차확인용이며, 본 목표가는 이들보다 낮다.", size=7.5)
para("교차확인", bold=True, size=8.5)
sv = ST["value"]
table([["항목", "값", "해석"],
       ["기준주가가 내포하는 배수", f"PER 27E {IM['per_on_27']:.1f}x · PBR 26E {IM['pbr_on_26']:.2f}x", "PER은 7년 중앙값의 1.4배, PBR은 7년 최고치 수준"],
       ["기준주가를 정당화하는 2027E 영업이익률", f"{IM['opm_need']*100:.1f}% (환율 중립)", f"PER 8.0x·PBR 0.70x 고정, 환율 {B['fx27']:,}원 유지 시. 가이던스 6.3~7.3%, 2030 목표 9+α%"],
       ["상장 관계사 지분 시가 (10/2)", f"기아 {sv['기아']:.1f} · 현대건설 {sv['현대건설']:.1f} · 현대위아 {sv['현대위아']:.2f}조", f"합 {ST['total']:.1f}조(주당 {ST['per_share']:,.0f}원, 시총의 {ST['share_of_mcap']*100:.0f}%). 기아 장부가 {ST['book_kia']:.1f}조보다 낮음"],
       ["보스턴다이내믹스(BD) 기대치", "증권가 30~60조, KB 134조(2026-05-28)", "본 목표가는 기본 12.5조 반영. 60조면 주당 +" + f"{RB['sens']['ps'][3][1]:,.0f}원, 134조면 +{RB['sens']['ps'][4][1]:,.0f}원 (민감도 ④)"]], size=7.2, widths=[4.6, 5.2, 8.2])

# ───────── 5. 민감도
h("4. 민감도")
sf = R["sens_fx_per"]
para("① 2027E 원/달러 × 목표 PER → 목표주가(원, PBR 0.70x 고정, 로봇 기본값 포함). 괄호는 해당 환율의 2027E EPS", bold=True, size=8.5)
table([["원/달러 × PER"] + [f"{p:.1f}x" for p in sf["per"]]] +
      [[f"{f:,}원 ({e:,.0f})"] + [f0(v) for v in r] for f, e, r in zip(sf["fx"], sf["eps"], sf["tp"])], size=7.5)
sp = R["sens_per_pbr"]
para("② 목표 PER × 목표 PBR → 목표주가(원, 기본 이익 추정, 로봇 기본값 포함)", bold=True, size=8.5)
table([["PER × PBR"] + [f"{q:.2f}x" for q in sp["pbr"]]] + [[f"{p:.1f}x"] + [f0(v) for v in r] for p, r in zip(sp["per"], sp["tp"])], size=7.5)
so = R["sens_opm_fx"]
para("③ 2027E 영업이익률(환율 중립) × 원/달러 → 2027E EPS(원)", bold=True, size=8.5)
table([["영업이익률 × 원/달러"] + [f"{f:,}" for f in so["fx"]]] + [[pc(o)] + [f0(v) for v in r] for o, r in zip(so["opm"], so["eps"])], size=7.5)
i_fx = sf["fx"].index(1_500); i_per = sf["per"].index(8.0)
rs = RB["sens"]
para("④ BD 100% 가치 × 현대차 실질 지분 → 로봇 주당 가산액(원, HMG Global 장부가 차감 후)", bold=True, size=8.5)
table([["BD 가치 × 실질 지분"] + [f"{l*100:.1f}%" for l in rs["look"]]] + [[f"{v:,.1f}조"] + [f"{x:+,.0f}" for x in r] for v, r in zip(rs["bd"], rs["ps"])], size=7.5)
para(f"해석: 환율이 1,360원 → 1,500원(원화 약세)으로 돌아가면 목표가는 {sf['tp'][2][i_per]:,.0f}원 → {sf['tp'][i_fx][i_per]:,.0f}원으로 오르지만, 그래도 기준주가에 못 미친다. "
     f"기준주가를 넘으려면 환율 약세와 함께 PER 9배 이상(로봇·주주환원 재평가) 또는 영업이익률 7%대 회복이 필요하다. 원화가 1,300원까지 강해지면 같은 PER에서 {sf['tp'][1][i_per]:,.0f}원이다.", size=7.5)

# ───────── 6. 리스크
h("5. 리스크 (목표가 대비 상·하방)")
bullet("상방 — BD 상장·로봇: 나스닥 상장 일정 확정이나 아틀라스 공장 투입 성과가 확인되면 BD 가치와 본업 멀티플이 함께 오른다(낙관: BD 30조 + PER 9.5x·PBR 0.85x = " + f"{H['tp']:,.0f}원). 상장 시 BD 가치가 시장에서 정해지면 ③ 실질 지분 가정도 확인할 수 있다.")
bullet("하방 — 로봇 기대 소멸: 풋옵션 매입가 기준 BD 가치 약 5.2조원(글로벌이코노믹 2026-06-19, 로이터 인용)이 기준이 되면 HMG Global 장부가 일부 손상 요인(주당 " + f"{L['tp_robot']:,.0f}원). 핵심 인력 이탈·누적 적자·중복상장 우려 보도도 부담.")
bullet("상방 — 환율 반전·관세: 원/달러가 1,450원 이상으로 돌아가거나 미국 관세가 추가 인하되면 2027E 영업이익이 0.5~1조원 늘어난다(민감도 ①·③).")
bullet("하방 — 원화 강세 장기화: 경상흑자 확대로 1,300원 아래로 내려가면 보수 시나리오(" + f"{L['tp']:,.0f}원)에 가까워진다. 삼성증권은 원화 강세 영향이 2027년까지 이어질 수 있다고 봤다(남도일보 2026-09-28).")
bullet("하방 — 노사·가이던스: 노조의 로봇 투입 반대(2026-01 소식지)와 10년 만의 전면파업. 1~2분기 영업이익률 5.5~5.8%로 가이던스(6.3~7.3%) 하단 미달이 이어질 가능성.")
bullet("모델 리스크: 지배순이익/영업이익 전환비율 " + f"{R['conv']:.2f}(FY23~1H26 평균)" + ", 환율 민감도는 2Q26 한 분기 수치에서 뽑은 근사치(헤지·현지생산 비중 변화 미반영). 3Q26 실적 발표(10월 말) 후 갱신 필요.")

# ───────── 7. 부록
h("부록. 핵심 가정과 원본(10/6) 대비 정정")
ra = table([["항목", "보수", "기본", "낙관"],
       ["3Q26E 매출 / 영업이익(조원)", "44.5 / 2.2", "45.5 / 2.4", "46.5 / 2.5"],
       ["4Q26E 매출 / 영업이익(조원)", "47.0 / 2.6", "48.5 / 2.9", "49.5 / 3.1"],
       ["2027E 매출 성장 / 영업이익률(환율 중립)", "+1% / 5.6%", "+3% / 6.3%", "+4% / 7.0%"],
       ["2027E 원/달러 (환율 효과)", f"1,300원 ({L['fx_eff']:+.2f}조)", f"1,360원 ({B['fx_eff']:+.2f}조)", f"1,420원 ({H['fx_eff']:+.2f}조)"],
       ["목표 PER (2027E EPS) / 목표 PBR (2026E BPS)", f"6.5x ({L['eps27']:,.0f}) / 0.55x", f"8.0x ({B['eps27']:,.0f}) / 0.70x", f"9.5x ({H['eps27']:,.0f}) / 0.85x"],
       ["로봇: BD 100% 가치 (주당 가산액)", f"5.2조 ({L['tp_robot']:+,.0f})", f"{B['bd']:.1f}조 ({B['tp_robot']:+,.0f})", f"30조 ({H['tp_robot']:+,.0f})"],
       ["목표주가 (상승여력)", f"{L['tp']:,.0f} ({L['upside']*100:+.0f}%)", f"{B['tp']:,.0f} ({B['upside']*100:+.0f}%)", f"{H['tp']:,.0f} ({H['upside']*100:+.0f}%)"],
       [f"공통: 주식수 {R['shares']:,}주(보통 {R['common']:,} + 우선 3종 {sum(R['pref'].values()):,}, 2026 반기 주식총수 + 7/31 자기주식 처분 2,747주), 지배순이익 = 영업이익 × {R['conv']:.3f}, "
        f"2026E말 지배지분 = 6월말 {122.33:.2f}조 + 2H 순이익 − 분기배당 2회(2,500원), 2026 평균 환율 {R['fx26']:,.1f}원(4Q는 10/2 현물 유지), 환율 민감도 연 {R['fx_sens']:.3f}조/1%", "", "", ""]], size=7.2)
ra.rows[-1].cells[0].merge(ra.rows[-1].cells[3])
table([["원본 표기", "정정", "근거"],
       ["현재주가 2026.10.05 종가 347,000원", "2026.10.02 종가 347,000원", "10/5 대체공휴일 휴장 (stock_db)"],
       ["52주 최고 787,000원(5/27 무렵) / 최저 211,000원", "최고 783,000원(6/1 장중, 종가 최고 750,000원) / 최저 214,000원(2025-10-13 장중)", "stock_db 일봉"],
       ["고점 대비 -55.9%", "-55.7% (장중 고점) / -53.7% (종가 고점)", "347,000 기준"],
       ["2026.01.29 525,000원 / 2월말→3월초 674,000→440,000원", "528,000원 / 2/27 674,000 → 3/4 501,000원 (44만원대는 3/31 445,500원)", "stock_db"],
       ["4Q25·1Q26 매출 공란", f"{QQ['4Q25']['rev']:.1f}조 / {QQ['1Q26']['rev']:.1f}조", "DART"],
       ["시가총액 약 70.7조원", f"보통주만 {R['common']*PRICE/1e12:.1f}조, 우선주 포함 {R['mcap']:.1f}조", "유통주식수 × 10/2 종가"],
       ["목표주가 447,000원 (증권사 목표가 60% + 현재가 15% 가중)", f"{TP:,}원 (본업 PER·PBR + 로봇 SOTP 독자 산출)", "증권사 목표가는 교차확인만"]], size=7, widths=[6.0, 7.2, 4.8])
para("자료: DART(사업·분기·반기보고서, 주식총수현황, 공정공시·주요사항보고서), 한국은행 ECOS(731Y001 원/달러, 817Y002 국고채 10년), stock_db(kor_price), Naver(FinanceDataReader, 우선주 시세), 현대차그룹 IR(2026-07-23), "
     "언론(파이낸셜뉴스·글로벌이코노믹·남도일보·아주경제·이투데이). 확인 필요: 3Q 배당 2,500원 유지 여부, 환율 민감도의 비선형성, HMG Global LLC의 BD 지분(그룹 68% 전부 경유 가정). 면책: 개인 포트폴리오용 분석이며 투자 권유가 아님.", size=7, color="595959")

out = HERE / "현대차_분석보고서.docx"
doc.save(out); print(out)

# PDF (Word로 변환)
import win32com.client
w = win32com.client.DispatchEx("Word.Application"); w.Visible = False; w.DisplayAlerts = 0
try:
    d = w.Documents.Open(str(out.resolve()), ReadOnly=True)
    print("pages", d.ComputeStatistics(2))
    d.ExportAsFixedFormat(str(out.with_suffix(".pdf").resolve()), 17); d.Close(False)
finally:
    w.Quit()
print(out.with_suffix(".pdf"))


