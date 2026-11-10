"""오리온_분석보고서.docx 생성 (results.json·peers_kr.csv 기반). 실행: python valuation/오리온/make_report.py"""
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
P = pd.read_csv(HERE / "peers_kr_v2.csv")
B, L, H = R["scen"]["기본"], R["scen"]["보수"], R["scen"]["낙관"]
PRICE = R["price"]; W = R["wacc_calc"]; RB = R["rev_build"]
TP = round(B["tp"] / 5_000) * 5_000
UP = TP / PRICE - 1
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
NAVY = "1F3864"

# ───────── 차트: 방법별 가치 범위(보수~낙관) vs 현재가
fig, ax = plt.subplots(figsize=(7.2, 2.3), dpi=200)
rows = [("DCF 출구7.0x (25%)", L["tp_dcf"], B["tp_dcf"], H["tp_dcf"]), ("PER (45%)", L["tp_per"], B["tp_per"], H["tp_per"]),
        ("EV/EBITDA (30%)", L["tp_ev"], B["tp_ev"], H["tp_ev"]), ("가중 목표가", L["tp"], B["tp"], H["tp"])]
for i, (n, lo, mid, hi) in enumerate(rows[::-1]):
    ax.barh(i, (hi - lo) / 1e4, left=lo / 1e4, color="#9DB4D6" if n != "가중 목표가" else "#2F5597", height=0.5)
    ax.plot(mid / 1e4, i, "o", color="white", mec="#1F3864", ms=6)
    ax.text(hi / 1e4 + 0.6, i, f"{mid/1e4:.1f}만", va="center", fontsize=7)
ax.set_yticks(range(4)); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=8)
ax.axvline(PRICE / 1e4, color="#C00000", ls="--", lw=1); ax.text(PRICE / 1e4, 3.55, f"현재가 {PRICE:,}", color="#C00000", fontsize=7, ha="center")
ax.set_xlabel("주당 가치(만원) · 막대=보수~낙관, 점=기본", fontsize=7); ax.tick_params(axis="x", labelsize=7)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_xlim(8, 36); plt.tight_layout(); plt.savefig(HERE / "football.png"); plt.close()

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
pc = lambda x: f"{x*100:.1f}%"

# ───────── 1. 표제·투자의견
para("오리온 (271560) 기업분석 보고서", bold=True, size=15, color=NAVY, after=0)
para("기준일 2026-10-22 · 기준주가 112,600원(KRX 종가) · 시가총액 4.45조원 · 작성: 송호빈 (포트폴리오용, 투자권유 아님)", size=8, color="595959", after=3)
t = table([["투자의견", "목표주가(12M)", "상승여력", "시가총액", "2026E PER / EV·EBITDA", "배당수익률(DPS 3,500)"],
           ["BUY", f"{TP:,}원", f"{UP*100:+.1f}%", "4.45조원", f"{R['now']['per_26']:.1f}x / {R['now']['ev_ebitda_26']:.1f}x", "3.1%"]], size=9)
para(f"▶ 가중평균(DCF 25·PER 45·EV/EBITDA 30) 기본 시나리오 {B['tp']:,.0f}원을 5,000원 단위로 반올림. 보수 {L['tp']:,.0f}원({L['upside']*100:+.0f}%) · 기본 {B['tp']:,.0f}원({B['upside']*100:+.0f}%) · 낙관 {H['tp']:,.0f}원({H['upside']*100:+.0f}%).", size=8.5, after=1)
para(f"▶ 주의: 목표가의 DCF는 출구배수 7.0x(2031E EBITDA 기준)로 계산한 {B['tp_dcf']:,.0f}원이며 배수법(PER {B['tp_per']:,.0f}원 · EV/EBITDA {B['tp_ev']:,.0f}원)보다 높다. 7.0x는 시장 정합적인 5.0x(피어 중앙값 4.9x)와 영구성장 DCF({B['tp_dcf_pg']:,.0f}원)가 내포하는 {B['tv_mult']:.1f}x의 중간으로 둔 판단치다(3장). DCF 40%면 {R['tp_by_weight']['DCF 40%']['tp']['기본']:,.0f}원, 0%면 {R['tp_by_weight']['DCF 0%']['tp']['기본']:,.0f}원. 보수 시나리오는 {L['tp']:,.0f}원({L['upside']*100:+.0f}%, {R['rating']['보수']}).", size=8.5, color="C00000", after=1)
doc.add_picture(str(HERE / "football.png"), width=Cm(16.5)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

# ───────── 2. 투자포인트
h("1. 투자포인트")
bullet(f"26E 성장 상향: 월별 법인별 잠정실적(한국·중국·베트남·러시아) 9월까지 누계 순매출 {RB['nine_s26']:,.0f}억(+{(RB['nine_s26']/RB['nine_s25']-1)*100:.1f}% YoY), 영업이익 {RB['nine_o26']:,.0f}억(+{(RB['nine_o26']/RB['nine_o25']-1)*100:.1f}%). 3Q 매출 +{(RB['q3_s26']/RB['q3_s25']-1)*100:.1f}%. 26E 연결 매출 {B['rev'][0]:,.0f}억(+{(B['rev'][0]/33324.4-1)*100:.1f}%), 영업이익 {B['op'][0]:,.0f}억(OPM {B['opm'][0]*100:.1f}%).")
bullet(f"순현금·주주환원: 6월말 현금 6,633억 + 단기금융예치금 6,979억(차입금 없음). 리스부채 1,495억 차감 후에도 시총의 약 27%. FY25 DPS 3,500원(배당성향 36.2%, 전년비 +40%)에 더해 2026년 첫 분기배당 1,750원(지급 8/6) 도입, 자사주 7,344주 소각. 고배당기업 요건 충족 공시.")
bullet("성장 투자: 진천 통합센터 4,600억(공정 36%, ~2027.12), 하노이3공장 1,300억(57%), 트베르 제2공장 2,400억(11%) 등 총 8,300억. 단기 FCF는 눌리나 2028년 이후 capex 정상화 시 FCFF 개선(모델 반영).")

# ───────── 3. 실적·재무
h("2. 실적·재무 (연결, 억원)")
table([["", "FY21", "FY22", "FY23", "FY24", "FY25", "1H26", "26E", "27E"],
       ["매출", "23,555", "28,732", "29,124", "31,043", "33,324", "18,239", f0(B["rev"][0]), f0(B["rev"][1])],
       ["영업이익", "3,729", "4,666", "4,924", "5,436", "5,583", "2,980", f0(B["op"][0]), f0(B["op"][1])],
       ["OPM", "15.8%", "16.2%", "16.9%", "17.5%", "16.8%", "16.3%", pc(B["opm"][0]), pc(B["opm"][1])],
       ["지배순이익", "2,577", "3,924", "3,766", "5,246", "3,827", "2,106", f0(B["ni"][0]), f0(B["ni"][1])],
       ["EPS(원)", "6,519", "9,926", "9,527", "13,271", "9,682", "5,329", f0(B["eps"][0]), f0(B["eps"][1])],
       ["감가상각(D&A)", "-", "1,615", "1,571", "1,605", "1,647", "-", f0(B["da"][0]), f0(B["da"][1])]], size=7.5)
para("출처: DART 연결재무제표(지배순이익은 포괄손익이 아닌 '지배기업 소유주 귀속 당기순이익'으로 정정: 2023 3,766, 2024 5,246). FY24 순이익은 영업외 요인으로 높아 정상화 필요. D&A=유형자산 감가상각(사용권 포함)+무형자산 상각. FY21 EPS 등은 주식수 39.53백만주 고정 환산.", size=7, color="595959")
para("지역별 매출(FY25, 사업보고서): 한국 10,967억(33%) · 중국 13,164억(40%) · 기타(베트남·러시아·인도) 9,194억(28%). 사업부문은 제과 단일(비스킷·파이·껌·초콜릿·스낵).", size=8)
table([["26E 매출 근거 (4개 법인 순매출 합, 억원)", "2025", "2026", "YoY"],
       ["1~9월 누계", f0(RB["nine_s25"]), f0(RB["nine_s26"]), f"+{(RB['nine_s26']/RB['nine_s25']-1)*100:.1f}%"],
       ["3분기(7~9월)", f0(RB["q3_s25"]), f0(RB["q3_s26"]), f"+{(RB['q3_s26']/RB['q3_s25']-1)*100:.1f}%"],
       ["4Q (25년 12월은 연간치 역산)", f0(RB["q4_25_sales_4c"]), f"기본 +7%: {f0(RB['q4_25_sales_4c']*1.07)}", "보수 +3% / 낙관 +10%"],
       ["연결/4법인 합 환산계수(1H26 실측)", "0.996", f"{RB['ratio_s']:.3f}", "연결 26E=" + f0(B["rev"][0])]], size=7.5, widths=[7, 3.2, 4.2, 3.6])

# ───────── 4. 밸류에이션
h("3. 밸류에이션")
para("EV 브리지(2026-12-31E, 기본)", bold=True, size=8.5)
table([["항목", "억원", "비고"],
       ["+ 현금및현금성자산 + 단기금융예치금 + FVPL", f0(6632.9 + 6979.2 + 50), "2026-06-30, 차입금 0(FY25 단기차입금 상환 완료)"],
       ["− 분기배당(8/6 지급, 주당 1,750원)", f"-{R['interim_div']:,.0f}", "주가는 배당락 후이므로 현금에서 차감"],
       ["+ 2H26E FCFF", f0(B["fcff_h2"]), "모델 산출"],
       ["− 리스부채 (유동 272 + 비유동 1,223)", "-1,495", "FY25말 355억 → 오리온홀딩스 부동산 신규 임차(관계사)로 급증"],
       ["+ 지분법적용 투자지분(장부가)", "6,845", "26E 지분법손익 -690억(1H 역산) 반영 → 장부가 100% 인정은 낙관적"],
       ["− 비지배지분", "-1,151", "중국·러시아 법인 소수지분"],
       ["= EV→주주가치 가산액(순현금성 자산)", f0(B["bridge"]), f"주당 {B['bridge']*1e8/R['shares']:,.0f}원"]], size=7.5, bold_last=True, widths=[7, 2.2, 8.8])
para("방법별 가치 (기본 시나리오)", bold=True, size=8.5)
table([["방법", "가중치", "핵심 가정", "주당 가치(원)", "보수 / 낙관"],
       ["DCF (FCFF 2027~31E + 출구배수)", "25%", f"WACC 8.0%(국가위험 가산 포함), 출구 EV/EBITDA 7.0x(보수 5.0x·낙관 9.4x) × 2031E EBITDA {B['ebitda31']:,.0f}억, 잔존가치 비중 {B['tv_share']*100:.0f}%", f0(B["tp_dcf"]), f"{L['tp_dcf']:,.0f} / {H['tp_dcf']:,.0f}"],
       ["PER (27E EPS × 12.5x)", "45%", f"EPS {B['eps'][1]:,.0f}원, 피어 중앙값 12.8x(삼양 제외), 오리온 5년(2021~25) 연말 PER 평균 11.9x", f0(B["tp_per"]), f"{L['tp_per']:,.0f} / {H['tp_per']:,.0f}"],
       ["EV/EBITDA (26E × 5.0x)", "30%", f"EBITDA {B['ebitda26']:,.0f}억, 피어 중앙값 4.9x(삼양 제외) 부근 적용", f0(B["tp_ev"]), f"{L['tp_ev']:,.0f} / {H['tp_ev']:,.0f}"],
       ["가중 목표가", "100%", "", f0(B["tp"]), f"{L['tp']:,.0f} / {H['tp']:,.0f}"]], size=7.5, bold_last=True, widths=[4.4, 1.3, 6.9, 2.3, 3.1])
para("DCF와 배수법의 격차 원인, 가중치 결정", bold=True, size=8.5)
para(f"① 격차: 출구 7.0x DCF {B['tp_dcf']:,.0f}원은 배수법(약 {B['tp_per']:,.0f}원)의 약 1.5배다. 영구성장 DCF({B['tp_dcf_pg']:,.0f}원)가 내포하는 영구가치 EV/EBITDA는 {B['tv_mult']:.1f}x로 국내 피어 중앙값 4.9x의 약 2배이고, 현재 시총이 내포하는 EV는 영구성장 DCF EV의 {R['implied_fcff_factor']*100:.0f}%(출구 7.0x DCF EV의 {R['implied_fcff_factor_x']*100:.0f}%)뿐이다. "
     f"② 원인: 2029E 이후 설비투자 정상화로 FCFF가 2028E {B['fcff'][2]:,.0f}억 → 2029E {B['fcff'][3]:,.0f}억으로 뛰는 구간과 순현금성 자산(주당 {B['bridge']*1e8/R['shares']:,.0f}원)이 가치의 대부분이며(출구 7.0x DCF의 잔존가치 비중 {B['tv_share']*100:.0f}%), 시장은 이 개선과 해외(중국·러시아) 현금의 자유로운 환류를 크게 할인한다. "
     f"③ 7.0x 선택 이유: 5.0x는 피어 중앙값과 정합적이나 오리온의 마진(16.9% 대 피어 3.7~6.1%)·성장 프리미엄을 반영하지 못하고, 9.4x는 영구성장 가정이 내포하는 값으로 피어의 약 2배라 과하다. 그 중간인 7.0x를 판단치로 두었다(검증 불가한 가정, 확인 필요). "
     f"④ 비중: DCF를 0%로 두지 않는 이유는 피어 배수가 오리온의 마진·순현금·증설 사이클을 담지 못하기 때문이고, 40%로 두지 않는 이유는 잔존가치 가정(출구배수)에 가치의 대부분이 좌우되며 시장 내재 수준과의 괴리가 커 불확실성이 가장 크기 때문이다. 따라서 DCF 25%, 시장 기반 두 배수법 75%로 정했다(증권사 목표가는 고려하지 않음). 비중별 결과는 부록.", size=7.5)
para("DCF 민감도 ④ 출구배수 방식 = 목표가 산출 방식 (주당가치, 원): 잔존가치 = 2031E EBITDA × 출구 EV/EBITDA", bold=True, size=8.5)
sx = R["sens_exit"]
table([["WACC \\ 출구배수"] + [f"{m:.1f}x" + (" (영구성장 2% 내포)" if i == 2 else " (피어 중앙값)" if i == 0 else " (기본, 목표가)") for i, m in enumerate(sx["mult"])]] +
      [[f"{w*100:.1f}%"] + [f0(v) for v in r] for w, r in zip(sx["wacc"], sx["tp"])], size=7.5)
i8 = sx["wacc"].index(0.08); e5, e7, e94 = sx["tp"][i8]
alt5 = 0.25 * e5 + 0.45 * B["tp_per"] + 0.30 * B["tp_ev"]; alt7 = 0.25 * e7 + 0.45 * B["tp_per"] + 0.30 * B["tp_ev"]; alt94 = 0.25 * e94 + 0.45 * B["tp_per"] + 0.30 * B["tp_ev"]
para(f"해석: WACC 8.0%에서 출구 5.0x는 {e5:,.0f}원, 7.0x는 {e7:,.0f}원, 9.4x는 {e94:,.0f}원이며 영구성장 DCF({B['tp_dcf_pg']:,.0f}원)는 출구 9.4x와 같은 값이다. "
     f"출구배수를 5.0x→9.4x로 바꾸면 가치가 {(e94/e5-1)*100:.0f}% 움직이지만 WACC를 7%→9%로 바꾸어도 5.0x 기준 {(sx['tp'][0][0]/sx['tp'][-1][0]-1)*100:.0f}%뿐이라, DCF 가치는 할인율보다 잔존가치 가정이 좌우한다. "
     f"가중 목표가로 환산하면 출구 5.0x는 {alt5:,.0f}원({alt5/PRICE-1:+.0%}), 7.0x는 {alt7:,.0f}원({alt7/PRICE-1:+.0%}, 목표가 {TP:,}원), 9.4x는 {alt94:,.0f}원({alt94/PRICE-1:+.0%})이다. "
     f"이 결과는 25% 비중을 이렇게 뒷받침한다. ⓐ가장 보수적인 5.0x 출구에서도 DCF가 {e5:,.0f}원으로 배수법보다 높고 가중 목표가의 상승여력이 Buy 기준(+15%)을 넘으므로, DCF를 0%로 둘 이유는 없고 결론(Buy)도 출구배수 선택에 민감하지 않다. "
     f"ⓑ다만 목표가 자체는 출구배수가 5.0x→9.4x로 움직일 때 {alt5/1000:,.0f}천원~{alt94/1000:,.0f}천원으로 크게 달라지는 7.0x 판단치에 의존하므로, 비중을 40%로 올릴 근거는 되지 않는다. 25%는 '잔존가치 불확실성이 커서 제한하되 배제하지는 않는' 판단이다(7.0x와 25%는 모두 판단치).", size=7.5)
para("WACC 산출 (국가위험 가산 유무)", bold=True, size=8.5)
Wn = R["wacc_calc_noadj"]; dc = R["dcf_cases"]
table([["구분", "Rf", "β", "ERP", "Ke", "Kd(세전→세후)", "D/V", "WACC", "DCF 출구7.0x / 영구성장(원)", "잔존가치 비중(출구/영구)"],
       ["가산 없음(한국 ERP)", pc(Wn["rf"]), "0.70", pc(Wn["erp"]), pc(Wn["ke"]), f"{Wn['kd_pre']*100:.2f}% → {Wn['kd_post']*100:.2f}%", "5%", pc(Wn["wacc"]), f"{dc['가산없음']['tp_dcf']:,.0f} / {dc['가산없음']['tp_dcf_pg']:,.0f}", f"{dc['가산없음']['tv_share']*100:.0f}% / {dc['가산없음']['tv_share_pg']*100:.0f}%"],
       ["가산 있음(매출비중 가중 ERP, 기본)", pc(W["rf"]), "0.70", pc(W["erp"]), pc(W["ke"]), f"{W['kd_pre']*100:.2f}% → {W['kd_post']*100:.2f}%", "5%", pc(W["wacc"]), f"{dc['가산있음']['tp_dcf']:,.0f} / {dc['가산있음']['tp_dcf_pg']:,.0f}", f"{dc['가산있음']['tv_share']*100:.0f}% / {dc['가산있음']['tv_share_pg']*100:.0f}%"]], size=7)
mx = R["mix"]
para(f"Rf·Kd: 한국은행 ECOS 817Y002 시장금리(일별) 2026-10-22 — 국고채(10년) 4.152%, 회사채(3년, AA-, 민평) 4.516%(무차입이라 대용치). 이전 버전의 4.385%는 한국 국고채가 맞지만 2026-09-07 값이었음(10/22 기준 4.152%로 교체). "
     f"ERP: Damodaran ctryprem(2026-01판) Korea 4.87%, China 5.14%, Vietnam·Russia 8.13%(성숙시장 4.23%); 가산 있음 = 2026.1~9월 4개 법인 순매출 비중(한국 {mx['한국']*100:.0f}%·중국 {mx['중국']*100:.0f}%·베트남 {mx['베트남']*100:.0f}%·러시아 {mx['러시아']*100:.0f}%) 가중 ERP {W['erp']*100:.2f}%. "
     "β: 2~5년 주간 회귀 β는 오리온 0.10(조정 0.39), 피어 0.1~0.3으로 KOSPI가 반도체 중심이라 구조적으로 낮아 판단치 0.70 사용(확인 필요). 세율 25%. 시나리오 WACC는 기본(가산 있음, 8.0%) ±0.5%p.", size=7, color="595959")
para("피어 배수 (TTM=2025.3Q~2026.2Q, 시총 2026-10-22, 순차입금=차입금+사채+리스−현금−단기금융·유동금융자산, DART 2026 반기 BS, 억원)", bold=True, size=8.5)
prow = [["", "시총", "순차입금(−순현금)", "비지배", "EBITDA(TTM)", "EV/EBITDA", "PER", "OPM"]]
for _, r in P.iterrows():
    prow.append([r["name"], f0(r["mcap"]), f0(r["netdebt"]), f0(r["nci"]), f0(r["ebitda"]), f"{r['EV_EBITDA']:.1f}x", f"{r['PER']:.1f}x", pc(r["OPM"])])
pe = P[P.name.isin(["농심", "롯데웰푸드", "오뚜기", "해태제과식품"])]; pa = P[P.name.isin(["농심", "롯데웰푸드", "오뚜기", "해태제과식품", "삼양식품"])]
prow.append(["중앙값 (삼양 제외)", "", "", "", "", f"{pe.EV_EBITDA.median():.1f}x", f"{pe.PER.median():.1f}x", ""])
prow.append(["중앙값 (삼양 포함)", "", "", "", "", f"{pa.EV_EBITDA.median():.1f}x", f"{pa.PER.median():.1f}x", ""])
prow.append(["참고: Mondelez / Hershey", "", "", "", "", "17.0x / 14.9x", "24.0x / 24.0x", "22.0% / 23.1%"])
table(prow, size=7)
para("정정: 직전 버전의 피어 EV/EBITDA 중앙값 2.6x는 오류였다. stock_db의 '유동/비유동금융부채'에 차입금·사채가 빠져 순차입금이 과소(예: 롯데웰푸드 순현금 3,012억 → 실제 순차입 11,346억)였고, DART 원자료로 재구성해 4.9x로 바로잡았다. "
     "5.0x 근거: ⓐ피어 중앙값 4.9x(삼양 제외; 포함 시 5.2x, 범위 4.5~6.2x), ⓑ오리온 현재 4.3x, ⓒ프리미엄 요인(OPM 16.9% vs 3.7~6.1%, 성장 +14%)과 할인 요인(해외 67%, 중국·러시아, 8,300억 설비투자)이 상쇄돼 중앙값 부근 적용. 보수 4.0x(최저 피어 이하), 낙관 6.2x(롯데웰푸드 최고). "
     "삼양식품은 12.8x로 튀어 제외 기준 우선(포함 시 PER 중앙값 13.2x). 글로벌(몬델리즈·허쉬 15~17x)은 yfinance 조회값으로 시장·규모 차이가 커 교차확인만.", size=7, color="595959")

# ───────── 5. 민감도
h("4. 민감도")
sd = R["sens_dcf"]
rows = [["WACC \\ g"] + [f"{g*100:.1f}%" for g in sd["g"]]] + [[f"{w*100:.1f}%"] + [f0(v) for v in r] for w, r in zip(sd["wacc"], sd["tp"])]
para("① 영구성장 방식 DCF 주당가치(원, 교차확인용): WACC × 영구성장률 (기본 시나리오)", bold=True, size=8.5); table(rows, size=7.5)
sp = R["sens_per"]
rows = [["PER \\ 27E EPS"] + [f"{m*100-100:+.0f}% ({sp['eps_base']*m:,.0f})" for m in sp["eps_mult"]]] + [[f"{p:.1f}x"] + [f0(v) for v in r] for p, r in zip(sp["per"], sp["tp"])]
para("② PER법 주당가치(원): 목표 PER × 27E EPS", bold=True, size=8.5); table(rows, size=7.5)
stt = R["sens_total"]
rows = [["WACC \\ PER"] + [f"{p:.1f}x" for p in stt["per"]]] + [[f"{w*100:.1f}%"] + [f0(v) for v in r] for w, r in zip(stt["wacc"], stt["tp"])]
para("③ 가중 목표가(원): WACC × 목표 PER (DCF 25% 기준)", bold=True, size=8.5); table(rows, size=7.5)

# ───────── 6. 리스크
h("5. 리스크")
bullet("국가·환율: 매출의 약 67%가 해외(중국 40%). 위안·동·루블 환율과 러시아 제재·송금 리스크. 역외 현금의 배당 송금 시 원천세 부담.")
bullet("원가·가격: 코코아·설탕·팜유 등 원재료 상승(26년 3Q 분기 OPM이 전년비 소폭 하락: 4법인 합 기준 16.5% vs 17.1%).")
bullet("투자 부담: 8,300억 설비투자로 2027~28E FCFF 둔화, 증설 지연·가동률 리스크. 지분법손실(1H26 약 -345억 역산)이 지속될 가능성.")
bullet("주주환원 변동: 배당 3,500원+분기 1,750원 가정 시 배당성향 40%대. 투자 확대 시 환원 여력 축소. 관계사(오리온홀딩스) 리스 거래 등 지배구조 이슈.")
bullet(f"모델 리스크: DCF 가치의 {B['tv_share']*100:.0f}%가 잔존가치(출구 7.0x 판단치)이며 출구 5.0x~9.4x에 따라 가중 목표가가 {alt5/1000:,.0f}천~{alt94/1000:,.0f}천원으로 움직인다. 영구성장 DCF가 내포하는 {B['tv_mult']:.1f}x는 피어 4.9x의 약 2배 → DCF 비중 25%로 제한. 증권사 목표가(KB 16만 2026.7, 한화 18만 2026.4)는 교차확인용으로만 사용했고 가중치 결정에는 쓰지 않음.")

# ───────── 7. 부록
h("부록. 핵심 가정")
table([["항목", "보수", "기본", "낙관"],
       ["4Q26 매출 YoY / 4Q OPM", "+3% / 16.5%", "+7% / 17.5%", "+10% / 18.5%"],
       ["27E~31E 매출성장률", "4·3·3·3·3%", "7·6·5·5·4%", "9·8·7·6·5%"],
       ["27E~ 영업이익률", "15.5%", "16.5%", "17.5%"],
       ["WACC / 영구성장률", "8.5% / 1.5%", "8.0% / 2.0%", "7.5% / 2.5%"],
       ["목표 PER / EV·EBITDA", "10.0x / 4.0x", "12.5x / 5.0x", "14.5x / 6.2x"],
       ["DCF 출구 EV/EBITDA (2031E)", "5.0x", "7.0x", "9.4x"],
       ["지분법손익(27E~)", "-690억", "-400억", "-150억"],
       ["26E 매출 / 영업이익(억)", f"{L['rev'][0]:,.0f} / {L['op'][0]:,.0f}", f"{B['rev'][0]:,.0f} / {B['op'][0]:,.0f}", f"{H['rev'][0]:,.0f} / {H['op'][0]:,.0f}"],
       ["공통: 세율 27%, D&A 4.8%, 유지보수 capex 4.0%+증설 잔여 5,639억(2H26 1,300·27E 2,600·28E 1,739), 운전자본 3%×Δ매출, 금융수익률 3.5%, 배당성향 40%, 주식수 39,528,788주", "", "", ""]], size=7.5)
para("확인 필요: 한국 ERP는 Damodaran 2026-01판(그 이후 판 존재 여부 미확인), β 0.70은 판단치, 12월 월별 잠정실적(역산치), 1H26 지분법손실(역산), 증설 일정, 피어 순차입금의 '기타 금융자산' 분류. 자료: DART, 한국은행 ECOS, Damodaran, KRX(pykrx), stock_db, 오리온 공정공시. 면책: 개인 포트폴리오용 분석이며 투자 권유가 아님.", size=7, color="595959")
para("비중별 목표가 (원, 기본 시나리오 · 나머지 비중은 PER:EV/EBITDA = 3:2로 배분)", bold=True, size=8.5)
tw = R["tp_by_weight"]
table([["DCF 비중", "PER / EV·EBITDA 비중", "보수", "기본", "낙관", "기본 상승여력"]] +
      [[k, f"{v['per_w']*100:.0f}% / {v['ev_w']*100:.0f}%", f0(v["tp"]["보수"]), f0(v["tp"]["기본"]), f0(v["tp"]["낙관"]), f"{(v['tp']['기본']/PRICE-1)*100:+.0f}%"] for k, v in tw.items()], size=7.5)
para(f"참고(교차확인): 영구성장 방식 DCF = 보수 {L['tp_dcf_pg']:,.0f} · 기본 {B['tp_dcf_pg']:,.0f} · 낙관 {H['tp_dcf_pg']:,.0f}원. 목표가 DCF의 출구배수는 보수 5.0x · 기본 7.0x · 낙관 9.4x.", size=7, color="595959")

out = HERE / "오리온_분석보고서.docx"
doc.save(out); print(out)



