"""케이뱅크_리서치리포트_2026.docx/.pdf (전체판, 약 11쪽) — 기존 리포트(한화생명·마키나락스) 서식을 따른다.
입력: results.json(약식 모델), results_full.json(추정·RIM 모델), price_db.csv. 실행: python valuation/케이뱅크/make_full_report.py
약식 노트(케이뱅크_분석보고서, 3쪽)는 make_report.py 가 따로 만든다.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
N = json.loads((HERE / "results.json").read_text(encoding="utf-8"))          # 약식 노트
F = json.loads((HERE / "results_full.json").read_text(encoding="utf-8"))     # 전체판
S = F["scen"]; B, L, H = S["기본"], S["보수"], S["낙관"]
PRICE, IPO = F["price"], F["ipo_px"]
# 목표주가·투자의견은 지원서(프라핏자산운용, 2026-10-27 제출)에 쓴 약식 모델(model.py) 값과 같게 둔다.
# 이익 추정(model_full.py)은 교차확인(5-5절)과 실적 추정(4장)에만 쓴다.
NB, NL, NH = N["scen"]["기본"], N["scen"]["보수"], N["scen"]["낙관"]
TP = round(NB["tp"] / 100) * 100
TP_ALT = round(B["tp"] / 100) * 100       # 이익 추정 시나리오(RIM + 2027E ROE 회귀) — 목표가와 나란히 제시하는 대안 시나리오
UP = TP / PRICE - 1
RATING = "BUY" if UP >= 0.15 else ("HOLD" if UP >= -0.05 else "SELL")
K, RG = N["kakao"], N["reg"]
NAVY, LIGHT, PALE, RED, GRAY = "1F3864", "D9E2F3", "EEF3FA", "C00000", "595959"
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"

# ═════════════════════════ 차트
px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str}).assign(d=lambda x: pd.to_datetime(x.날짜)).set_index("d")


def ax_clean(a):
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.tick_params(labelsize=6.5)


# 1) 주가 (표지)
fig, a = plt.subplots(figsize=(3.6, 2.5), dpi=220)
a.plot(px.index, px["종가"], color="#" + NAVY, lw=1.1)
a.axhspan(8_300, 9_500, color="#D9D9D9", alpha=.5, lw=0); a.axhline(IPO, color="#7F7F7F", ls=":", lw=.9)
a.axhline(TP, color="#" + RED, ls="--", lw=.9)
a.text(px.index[2], 9_580, "희망밴드 8,300~9,500", fontsize=5.5, color="#" + GRAY)
a.text(px.index[-1], TP - 330, f"목표주가 {TP:,}", fontsize=5.5, color="#" + RED, ha="right")
a.set_title("상장(2026-03-05) 이후 종가(원)", fontsize=7); ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / "full_price.png"); plt.close()

# 2) 실적 추이·추정
yrs = ["2024A", "2025A", "2026E", "2027E", "2028E"]
hist = F["hist"]; fb = B["f"]
nii = [hist["2024"]["nii"], hist["2025"]["nii"]] + [r["nii"] for r in fb]
ppop = [3_864, 3_310] + [r["ppop"] for r in fb]
prov = [2_536, 2_174] + [r["prov"] for r in fb]
ni = [hist["2024"]["ni"], hist["2025"]["ni"]] + [r["ni"] for r in fb]
roe = [0.0651, 0.0526] + [r["roe"] for r in fb]
fig, a = plt.subplots(figsize=(7.2, 2.4), dpi=220)
x = range(5); w = .2
for i, (v, c, n) in enumerate(((nii, "#9DB4D6", "순이자이익"), (ppop, "#2F5597", "충당금적립전이익"), (prov, "#F4B183", "순충당금"), (ni, "#" + NAVY, "순이익"))):
    a.bar([j + (i - 1.5) * w for j in x], v, w, color=c, label=n)
a.set_xticks(list(x)); a.set_xticklabels(yrs); a.set_ylabel("억원", fontsize=6.5); ax_clean(a)
a2 = a.twinx(); a2.plot(list(x), [r * 100 for r in roe], "o-", color="#" + RED, lw=1.2, ms=3, label="ROE(우)")
a2.set_ylim(0, 10); a2.tick_params(labelsize=6.5); a2.spines["top"].set_visible(False)
for j, r in enumerate(roe):
    a2.text(j, r * 100 + .4, f"{r*100:.1f}%", fontsize=6, color="#" + RED, ha="center")
h1, l1 = a.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
a.legend(h1 + h2, l1 + l2, fontsize=6, ncol=5, loc="upper left", frameon=False)
a.axvspan(1.5, 4.5, color="#F2F2F2", zorder=-1)
plt.tight_layout(); plt.savefig(HERE / "full_earn.png"); plt.close()

# 3) 업비트 의존도 + 보호예수 해제
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.3), dpi=220)
lab = ["2021말", "3Q25", "2025말"]; val = [52.9, 24.6, 20.5]; amt = [5.99, 7.49, 5.83]
a.bar(lab, val, color=["#BFBFBF", "#9DB4D6", "#2F5597"])
for i, (v, m) in enumerate(zip(val, amt)):
    a.text(i, v + 1.2, f"{v}%\n({m}조)", ha="center", fontsize=6.5)
a.set_ylim(0, 65); a.set_title("두나무(업비트) 가상자산 예금 / 전체 수신", fontsize=7); ax_clean(a)
lk = ["상장~2개월", "3개월(6/5)", "6개월(9/5)", "1년(27/3/5)"]; lv = [36.35, 45.16, 65.81, 100]
b.bar(lk, lv, color=["#9DB4D6", "#9DB4D6", "#2F5597", "#" + RED])
for i, v in enumerate(lv):
    b.text(i, v + 2, f"{v:.1f}%", ha="center", fontsize=6.5)
b.set_ylim(0, 115); b.set_title("상장 후 유통가능 물량(발행주식 대비)", fontsize=7); ax_clean(b)
b.tick_params(axis="x", labelsize=6)
plt.tight_layout(); plt.savefig(HERE / "full_vasp_lock.png"); plt.close()

# 4) 방법별 가치 (풋볼필드)
rows = [("A. 초과자본 분리 적정 PBR (50%)", NL["va"], NB["va"], NH["va"]), ("B. PBR–ROE 회귀 + 플랫폼 (50%)", NL["vb"], NB["vb"], NH["vb"]),
        ("목표주가 = A·B 평균", NL["tp"], NB["tp"], NH["tp"]), ("이익 추정 시나리오(RIM·회귀)", L["tp"], B["tp"], H["tp"])]
fig, a = plt.subplots(figsize=(7.2, 2.0), dpi=220)
for i, (n, lo, mid, hi) in enumerate(rows[::-1]):
    a.barh(i, hi - lo, left=lo, color="#2F5597" if n.startswith("목표") else ("#F4B183" if n.startswith("이익") else "#9DB4D6"), height=.5)
    a.plot(mid, i, "o", color="white", mec="#" + NAVY, ms=5); a.text(hi + 120, i, f"{mid:,.0f}", va="center", fontsize=6.5)
a.set_yticks(range(4)); a.set_yticklabels([r[0] for r in rows[::-1]], fontsize=7)
a.axvline(PRICE, color="#" + RED, ls="--", lw=1); a.text(PRICE, 3.45, f"현재가 {PRICE:,.0f}", color="#" + RED, fontsize=6.5, ha="center")
a.axvline(IPO, color="#7F7F7F", ls=":", lw=1); a.text(IPO, 3.45, f"공모가 {IPO:,}", color="#" + GRAY, fontsize=6.5, ha="center")
a.set_xlim(500, 9_500); a.set_xlabel("주당 가치(원) · 막대=보수~낙관, 점=기본", fontsize=6.5); ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / "full_football.png"); plt.close()

# ═════════════════════════ 문서 유틸
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(1.6); sec.top_margin = Cm(1.5); sec.bottom_margin = Cm(1.4)
sec.header_distance = Cm(0.6); sec.footer_distance = Cm(0.6)
st = doc.styles["Normal"]; st.font.name = "Malgun Gothic"; st.font.size = Pt(8.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Malgun Gothic")
st.paragraph_format.space_after = Pt(2); st.paragraph_format.line_spacing = 1.25
W = 17.8


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    for s in tcPr.findall(qn("w:shd")):
        tcPr.remove(s)
    s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcPr.append(s)


def borders(t, color="BFC9D9", sz="4", inside=True):
    tblPr = t._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right") + (("insideH", "insideV") if inside else ()):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), sz); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color); b.append(e)
    tblPr.append(b)


def pborder(p, color=NAVY, sz="8", side="bottom"):
    pPr = p._p.get_or_add_pPr(); b = OxmlElement("w:pBdr"); e = OxmlElement(f"w:{side}")
    for k, v in (("val", "single"), ("sz", sz), ("space", "1"), ("color", color)):
        e.set(qn(f"w:{k}"), v)
    b.append(e); pPr.append(b)


def run(p, text, size=8.5, bold=False, color=None):
    parts = str(text).split("**")
    for i, t in enumerate(parts):
        if not t:
            continue
        r = p.add_run(t); r.font.size = Pt(size); r.bold = bold or (i % 2 == 1)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
    return p


def para(text="", size=8.5, bold=False, color=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=2, before=0, cont=None):
    p = (cont or doc).add_paragraph()
    run(p, text, size, bold, color); p.alignment = align
    p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(before)
    return p


def h1(text, new_page=True):
    p = para(text, 12, True, NAVY, WD_ALIGN_PARAGRAPH.LEFT, 4, 8); pborder(p, NAVY, "12")
    p.paragraph_format.page_break_before = new_page     # 기존 리포트처럼 큰 장마다 새 쪽
    p.paragraph_format.keep_with_next = True


def h2(text):
    p = para("▌ " + text, 9.5, True, NAVY, WD_ALIGN_PARAGRAPH.LEFT, 2, 6)
    p.paragraph_format.keep_with_next = True


def cellp(c, text, size=7.5, bold=False, color=None, align=WD_ALIGN_PARAGRAPH.CENTER):
    p = c.paragraphs[0]; run(p, text, size, bold, color); p.alignment = align
    p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.1
    c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    return p


def table(rows, widths, size=7.3, first_left=True, hl_rows=(), hl_cols=(), note=None, cont=None):
    t = (cont or doc).add_table(rows=len(rows), cols=len(rows[0])); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(t)
    tot = sum(widths)
    for i, r in enumerate(rows):
        trPr = t.rows[i]._tr.get_or_add_trPr(); trPr.append(OxmlElement("w:cantSplit"))
        for j, v in enumerate(r):
            c = t.cell(i, j); c.width = Cm((W if cont is None else W / 2 - 0.4) * widths[j] / tot)
            head = i == 0
            cellp(c, v, size, head or i in hl_rows, "FFFFFF" if head else None,
                  WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and first_left and not head) else WD_ALIGN_PARAGRAPH.CENTER)
            if head:
                shade(c, NAVY)
            elif i in hl_rows:
                shade(c, LIGHT)
            elif j in hl_cols:
                shade(c, PALE)
    if note:
        para(note, 6.8, color=GRAY, after=4, cont=cont)
    else:
        (cont or doc).add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def img(path, width=W, cont=None, caption=None):
    p = (cont or doc).add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Cm(width)); p.paragraph_format.space_after = Pt(1)
    if caption:
        para(caption, 6.8, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, after=4, cont=cont)


def thesis_box(no, title, lines):
    t = doc.add_table(rows=1 + len(lines), cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t, "FFFFFF", "8")
    a = t.cell(0, 0).merge(t.cell(len(lines), 0)); shade(a, NAVY); a.width = Cm(1.3)
    cellp(a, no, 14, True, "FFFFFF")
    c = t.cell(0, 1); c.width = Cm(W - 1.3); shade(c, LIGHT); cellp(c, title, 9, True, NAVY, WD_ALIGN_PARAGRAPH.LEFT)
    for i, ln in enumerate(lines, 1):
        c = t.cell(i, 1); c.width = Cm(W - 1.3); shade(c, PALE); cellp(c, ln, 7.6, False, None, WD_ALIGN_PARAGRAPH.LEFT)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def kpi_tiles(items):
    t = doc.add_table(rows=1, cols=len(items)); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t, "FFFFFF", "12")
    for j, (lab, val, sub) in enumerate(items):
        c = t.cell(0, j); c.width = Cm(W / len(items)); shade(c, LIGHT if j % 2 == 0 else "E2EFDA")
        cellp(c, lab, 6.8, False, GRAY)
        p = c.add_paragraph(); run(p, val, 11.5, True, NAVY); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(0)
        p = c.add_paragraph(); run(p, sub, 6.5, False, GRAY); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# 머리·꼬리
hp = sec.header.paragraphs[0]
run(hp, "EQUITY RESEARCH  │  은행 (Internet Bank)", 7.5, True, NAVY)
run(hp, "                                                                           작성일: 2026년 10월 27일  │  작성자: 송호빈", 7, False, GRAY)
pborder(hp, NAVY, "6")
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(fp, "본 리포트는 공개 자료 기반 개인 분석 자료입니다. 투자 판단의 참고 자료로만 활용하시기 바랍니다.  |  Page ", 6.5, False, "808080")
r = fp.add_run(); r.font.size = Pt(6.5)
for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if tag:
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag); r._r.append(e)
    else:
        e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)

# ═════════════════════════ 1쪽: 표지
t = doc.add_table(rows=1, cols=1); borders(t, NAVY, "4"); c = t.cell(0, 0); shade(c, NAVY); c.width = Cm(W)
cellp(c, "케이뱅크 (279570 KS)", 17, True, "FFFFFF", WD_ALIGN_PARAGRAPH.LEFT)
p = c.add_paragraph(); run(p, "공모가 8,300원이 가정한 ROE 15% — 이익 추정으로 다시 본 인터넷은행의 적정 PBR", 9, False, "D9E2F3"); p.paragraph_format.space_after = Pt(4)
doc.add_paragraph().paragraph_format.space_after = Pt(2)

t = doc.add_table(rows=1, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t, "FFFFFF", "4")
lc, rc = t.cell(0, 0), t.cell(0, 1); lc.width = Cm(W * .52); rc.width = Cm(W * .48)
rt = lc.add_table(rows=1, cols=2); borders(rt, "FFFFFF", "8")
a = rt.cell(0, 0); shade(a, RED if RATING == "SELL" else "548235"); a.width = Cm(3.2)
cellp(a, RATING, 20, True, "FFFFFF"); p = a.add_paragraph(); run(p, "(매도)" if RATING == "SELL" else "", 7.5, False, "FFFFFF"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
b2 = rt.cell(0, 1); shade(b2, LIGHT); b2.width = Cm(5.8)
cellp(b2, "목표주가 (12개월)", 7, False, GRAY, WD_ALIGN_PARAGRAPH.LEFT)
p = b2.add_paragraph(); run(p, f"{TP:,}원", 17, True, NAVY)
p = b2.add_paragraph(); run(p, f"현재주가 {PRICE:,.0f}원 · 하락여력 {UP*100:+.1f}%", 7.5, True, RED)
p = b2.add_paragraph(); run(p, f"이익 추정 시나리오 {TP_ALT:,}원 ({TP_ALT/PRICE-1:+.1%})", 7, False, GRAY)
img(HERE / "full_price.png", W * .5, cont=lc)
lc.paragraphs[0]._p.getparent().remove(lc.paragraphs[0]._p)
mk = [["항목", "수치"], ["현재주가 (2026.10.26)", f"{PRICE:,.0f}원"], ["시가총액", f"{N['mcap']/1e4:.2f}조원"],
      ["발행주식수", "405,695,151주"], ["공모가 / 상장일", "8,300원 / 2026.03.05"], ["상장 후 최고 / 최저", "9,880 / 5,080원"],
      ["최대주주", "BC카드 31.23%"], ["PBR (보통주 BPS)", f"{N['pbr_now']:.2f}배 ({N['bps']:,.0f}원)"], ["ROE (최근 4분기)", pc(N["roe_ttm"])],
      ["CET1 비율 (2Q26)", pc(N["cet1_ratio"])], ["2027E PER / PBR", f"{PRICE/B['f'][1]['eps']:.1f}배 / {PRICE/B['f'][1]['bps']:.2f}배"],
      ["유통가능 / 다음 해제", "65.81% / 2027.03.05"]]
table(mk, [55, 45], 7.2, cont=rc)
rc.paragraphs[0]._p.getparent().remove(rc.paragraphs[0]._p)

h2("재무 요약 (Financial Summary, 별도 기준, 단위: 억원)")
fs = [["항목", "2024A", "2025A", "2026E", "2027E", "2028E"],
      ["순이자이익"] + [f0(v) for v in nii], ["충당금적립전이익"] + [f0(v) for v in ppop], ["순충당금"] + [f0(v) for v in prov],
      ["당기순이익"] + [f0(v) for v in ni], ["ROE (보통주)"] + [pc(v) for v in roe],
      ["총여신 (기말)", "162,670", "183,787"] + [f0(r["loan_end"]) for r in fb],
      ["BPS (원)", "-", f0(N["eq"]["4Q25"] * 1e8 / 375_695_151 - 998.94e8 / 375_695_151)] + [f0(r["bps"]) for r in fb],
      ["PBR (현재가 기준)", "-", "-"] + [f"{PRICE/r['bps']:.2f}배" for r in fb]]
table(fs, [22, 15, 15, 16, 16, 16], hl_cols=(3, 4, 5), note="자료: DART 사업·반기보고서(부문별 영업실적), 2026E~2028E는 본 리포트 추정(기본 시나리오). 2025A BPS는 상장 전 주식수(375,695,151주) 기준.")

page_break()
# ═════════════════════════ 2쪽: 핵심 투자 포인트
h2("핵심 투자 포인트")
thesis_box("①", "공모가는 ROE 15%를 가정했다 — 실제 ROE는 4~6%",
           [f"주관사 산식(자본총계 × 비교 PBR 1.80 + 신주 공모금액)은 카카오뱅크(ROE {K['roe']*100:.1f}%)·라쿠텐뱅크와 같은 PBR을 적용, 이를 정당화하는 핵심자본 ROE는 {N['implied']['roe_at_ipo']*100:.1f}%",
            f"최근 4분기 ROE {N['roe_ttm']*100:.1f}%, 회사 공시 ROE 2024년 6.51% · 2025년 5.26% · 1H26 4.98%. 기본 추정 2027E {B['f'][1]['roe']*100:.1f}% · 2028E {B['f'][2]['roe']*100:.1f}%"])
thesis_box("②", "이익 성장보다 자본 성장이 빠르다 — 공모 자본 2,450억이 ROE를 희석",
           [f"CET1 비율 12.4%(2025말) → 18.1%(2Q26). 정상 13%를 넘는 초과자본 약 {N['excess']:,.0f}억이 아직 대출로 전환되지 않음",
            "총여신은 2025말 18.4조 → 2Q26 19.8조(+7.7%)로 늘었지만, 충당금 · 판관비 증가와 세율 정상화로 순이익은 1H26 601억(-28.7% YoY)"])
thesis_box("③", "업비트 의존은 줄었지만 수급 부담은 남았다",
           ["두나무 가상자산 예금 비중 52.9%(2021말) → 20.5%(2025말). 10/2 제휴 1년 연장(2027-10-05까지)으로 단기 이탈 위험은 낮아짐",
            "2027-03-05 상장 1년 보호예수 해제 시 최대주주 BC카드 31.23% 포함 잔여 34.19%가 유통 가능 — 재무적투자자(FI) 지분 출회 가능성"])
para(f"▶ 결론: 목표주가 {TP:,}원(A. 초과자본 분리 적정 PBR {NB['va']:,.0f}원 · B. PBR–ROE 회귀 {NB['vb']:,.0f}원 50:50), 현재가 대비 {UP*100:+.1f}%로 **{RATING}**. "
     f"현재가 {PRICE:,.0f}원은 보통주 PBR {N['pbr_now']:.2f}배로 국내 상장 은행 평균(0.65배)보다 높고, 이를 정당화하려면 핵심자본 ROE {N['implied']['roe_at_price']*100:.1f}%가 필요하다. "
     f"한편 2026E~2028E 이익을 직접 추정한 **이익 추정 시나리오**에서는 ROE가 5%대에 머물러 주당 {TP_ALT:,}원(RIM {B['rim']:,.0f}원 · 2027E ROE 회귀 {B['reg']:,.0f}원)이다. "
     "3분기 실적(10/30) 이후 이익 개선이 확인되지 않으면 이 시나리오 쪽으로 무게가 옮겨간다(5-5절).", 8.5, color=None, before=4)

# ═════════════════════════ 1. 기업 개요
h1("1. 기업 개요 (Company Overview)")
h2("1-1. 사업 소개")
para("케이뱅크(279570)는 2016년 12월 은행업 본인가를 받은 국내 최초의 인터넷전문은행으로, 최대주주는 BC카드(KT 계열, 31.23%)다. "
     "점포 없이 모바일 채널로 예금 · 대출 · 결제 서비스를 제공하며, 2020년 6월 두나무(업비트)와 실명확인 입출금계정 제휴로 고객 기반을 빠르게 넓혔다. "
     "2025년말 고객 수 1,553만 명, 여수신 합산 46.8조원, 직원 646명(2Q26). 2026년 3월 5일 유가증권시장에 상장했다(공모 6,000만주 = 신주 3,000만 + 구주 3,000만, 공모가 8,300원, 총 4,980억원).")
h2("1-2. 여신 · 수신 구조")
table([["구분", "2024말", "2025말", "2Q26", "비고"],
       ["총여신 (억원)", "162,670", "183,787", "197,857", "2Q26 YTD +7.7%"],
       [" ㄴ 가계", "151,156", "160,680", "164,842", "주담대 47.9% · 가계 일반(신용) 41.3% (3Q25)"],
       [" ㄴ 기업(개인사업자)", "11,514", "23,107", "33,015", "2024.8 인터넷은행 최초 개인사업자 부동산담보대출"],
       ["예수부채 (억원)", "285,687", "284,319", "266,371", "업비트 예금 2025말 58,327억(20.5%)"],
       ["평균 대출이율 / 조달이율", "5.04% / 2.72%", "4.53% / 2.52%", "4.52% / 2.40%", "원화예대금리차 2.29 → 1.91 → 2.14%p"],
       ["중·저신용자 신용대출 비중", "-", "33.1%(3Q25 평잔)", "-", "정책 목표 평잔 30% 이상"]],
      [22, 14, 15, 14, 35], note="자료: 2026 반기보고서(자산건전성 · 자금조달 및 운용 현황), 투자설명서(2026-02-04). 총여신은 무수익여신 산정대상 기준.")
h2("1-3. 주주 구성 및 보호예수")
table([["주주", "지분율", "매각 제한", "비고"],
       ["BC카드 (최대주주)", "31.23%", "상장 후 1년 (2027-03-05)", "KT 69.54% 보유"],
       ["우리은행", "9.22%", "6개월 (해제)", "공모 시 구주 일부 매출"],
       ["국민연금공단", "5.69%", "-", "상장 후 취득"],
       ["KHAN SS L.P. / BCC KINGPIN, LLC", "5.36% / 5.13%", "3 · 6개월 (해제)", "재무적투자자(FI), 공모 시 구주 매출"],
       ["NH투자증권", "5.11%", "6개월 (해제)", ""],
       ["우리사주조합", "0.87%", "1년", ""],
       ["소액주주", "20.53%", "-", "429,218명"]],
      [32, 14, 26, 28], note="자료: 2026 반기보고서(주주에 관한 사항), 투자설명서(공모 후 유통가능주식 현황).")
img(HERE / "full_vasp_lock.png", W, caption="좌: 업비트 예금 비중(자료: 투자설명서). 우: 유통가능 물량 — 9/5 이후 65.81%, 2027-03-05 이후 100%")

# ═════════════════════════ 2. 실적 분석
h1("2. 실적 분석 (Performance Review)")
h2("2-1. 1H26 실적 리뷰 — 이자이익은 늘고 순이익은 줄었다")
kpi_tiles([("1H26 순이자이익", "2,530억", "+19.5% YoY"), ("1H26 충당금적립전이익", "1,642억", "-9.9% YoY"),
           ("1H26 순이익", "601억", "-28.7% YoY"), ("명목 NIM", "1.59%", "1H25 1.38%")])
para("조달금리가 2.51%(1H25)에서 2.39%로 내려가며 순이자이익은 19.5% 늘었지만, 1H25에 있었던 유가증권 관련 이익(기타영업잡수익 669억 → 272억)이 줄고 "
     "판관비(+10.4%)와 대손상각비(+6.6%)가 늘면서 충당금적립전이익과 순이익이 감소했다. 분기로는 1Q26 332억 → 2Q26 269억으로 2Q25(682억) 대비 -60.6%다.")
h2("2-2. 수익성 · 건전성 지표")
table([["지표", "2024", "2025", "1H25", "1H26"],
       ["ROE (회사 공시)", "6.51%", "5.26%", "8.09%", "4.98%"], ["ROA", "0.51%", "0.36%", "0.56%", "0.38%"],
       ["명목 NIM", "1.91%", "1.40%", "1.38%", "1.59%"], ["원화예대금리차", "2.29%p", "1.91%p", "1.89%p", "2.14%p"],
       ["판관비 (억원)", "1,826", "2,279", "1,046", "1,155"], ["대손상각비 (억원)", "2,498", "2,133", "961", "1,024"],
       ["고정이하여신비율", "0.82%", "0.57%", "-", "0.59%"], ["연체율 (1개월 이상)", "0.90%", "0.60%", "-", "0.60%"],
       ["대손충당금적립률", "251.7%", "272.1%", "-", "261.4%"], ["BIS 총자본비율 / CET1", "14.67% / 13.52%", "14.52% / 12.43%", "-", "20.02% / 18.08%"]],
      [28, 18, 18, 18, 18], note="자료: 2026 반기보고서(수익성지표 · 부문별 수지 · 자산건전성 · 자본적정성).")
para("건전성은 연체율 0.60%, 고정이하여신비율 0.59%로 안정적이고 적립률도 260%대를 유지한다. 문제는 건전성이 아니라 수익성이다. "
     "대손비용률(순충당금 ÷ 평균대출)이 1.25%(2025)에서 1.11%(1H26 연환산)로 내려왔는데도 ROE가 5%를 넘지 못하는 것은, "
     "가계 신용대출 금리가 내려가는 동안 판관비가 매년 10% 넘게 늘고 공모로 자본이 커졌기 때문이다.")

# ═════════════════════════ 3. 투자 포인트
h1("3. 투자 포인트 (Investment Thesis)")
h2("Thesis 1. 공모가 산정식의 빈칸은 ROE였다")
table([["단계", "주당 가치", "바꾼 것"]] + [[s["step"], f0(s["value"]) + "원", s["note"]] for s in N["ipo_steps"]],
      [44, 13, 43], hl_rows=(5,), note="①은 투자설명서의 10,287원을 그대로 재현: 3Q25 자본총계 2.19조 × 비교 PBR 1.80(카카오뱅크 1.54 · 라쿠텐뱅크 조정 2.05) + 신주 공모금액 2,490억 ÷ 잠재주식수(표기 1.80은 반올림, 역산 1.799). 희망밴드 8,300~9,500원, 확정 공모가 8,300원.")
para("신종자본증권(999억)을 빼고 비교 PBR을 지금 카카오뱅크 값으로 바꿔도 8,000원대가 유지되지만, 두 회사의 ROE 차이를 반영하면 주당 가치가 4,034원으로 절반이 된다. "
     "할인율(7.65~19.32%)도 최근 5년 유가증권시장 공모(카카오뱅크 18.85~31.33% 등)보다 낮아, 공모가는 ROE 차이를 할인으로도 흡수하지 못했다.")
h2("Thesis 2. 초과자본 2,450억이 대출로 바뀌는 속도가 ROE를 결정한다")
para(f"CET1 18.1%에서 정상 수준 13%를 넘는 약 {N['excess']:,.0f}억은 위험가중자산 기준 약 {N['excess']/0.13/1e4:.1f}조의 추가 대출 여력이다. "
     "2Q26 기준 총여신은 연 15% 안팎으로 늘고 있고 개인사업자 대출(2025말 2.3조 → 2Q26 3.3조)이 성장을 이끈다. 다만 중·저신용자 대출 비중 규제(평잔 30% 이상)와 "
     "가계부채 총량 관리로 주담대 · 신용대출을 빠르게 늘리기 어렵다. 기본 시나리오는 총여신 연 10~12% 성장, 대손비용률 1.0~1.1%를 가정했고 이때 ROE는 5%대에 머문다.")
h2("Thesis 3. 업비트 — 리스크는 줄었고, 레버리지도 줄었다")
para("업비트 예금 비중은 2021말 52.9%에서 2025말 20.5%로 낮아졌고, 2026-10-02 제휴가 2027-10-05까지 연장되며 단기 이탈 위험은 줄었다. "
     "반대로 가상자산 시장이 다시 커질 때 케이뱅크가 얻는 몫(예금 · 펌뱅킹 수수료 FY2025 188억)도 이익의 일부에 그친다. "
     "예치금 이용료율 · 운용 스프레드는 공시되지 않아 아래 민감도로만 제시한다.")
v = F["vasp"]
table([["가정", "세전이익 영향 (연, 억원)", "주당가치 영향 (원, 세율 20%)"]] +
      [[f"제휴 종료: 예치금 운용 스프레드 {r['spread']*100:.1f}%p + 펌뱅킹 수수료 상실", f"-{r['lost_pbt']:,.0f}", f"-{r['lost_ps']:,.0f}원/년"] for r in v["exit"]] +
      [[f"예치금 이용료율 +{r['bp']}bp", f"{r['d_pbt']:,.0f}", "-"] for r in v["rate"]],
      [52, 24, 24], note="기준: 2025말 업비트 예금 58,327억, 펌뱅킹 수수료 188억(투자설명서). 스프레드 · 이용료율은 본 리포트 가정.")

# ═════════════════════════ 4. 실적 추정
h1("4. 실적 추정 (Earnings Forecast)")
para("평균대출 × 대출이율 + 대출 외 수익성자금 × 운용이율 − 원가성자금 × 조달이율로 순이자이익을 만들고, 비이자 · 기타이익, 판관비, 대손비용, 법인세를 차례로 뺐다. "
     "2026E는 연간 추정에서 상반기 실적(순이익 601억)을 포함한다. 공모 신주 대금(순 2,451억)은 1Q26 자본에 더했다.")
ab = B["assump"]
rows = [["항목 (기본)", "2025A", "2026E", "2027E", "2028E"],
        ["총여신 증가율 (기말)", "+13.0%"] + [f"+{g*100:.0f}%" for g in ab["g"]],
        ["평균대출 (억원)", "174,319"] + [f0(r["L"]) for r in fb],
        ["대출이율 / 조달이율", "4.53% / 2.52%"] + [f"{y*100:.2f}% / {c*100:.2f}%" for y, c in zip(ab["yL"], ab["cF"])],
        ["순이자이익", "4,442"] + [f0(r["nii"]) for r in fb],
        ["NIM (수익성자금 기준)", "1.52%"] + [pc(r["nim"], 2) for r in fb],
        ["비이자 · 기타 순이익", "1,147"] + [f0(r["x"]) for r in fb],
        ["판관비 (CIR)", "2,279 (40.8%)"] + [f"{r['sga']:,.0f} ({r['cir']*100:.1f}%)" for r in fb],
        ["순충당금 (대손비용률)", "2,174 (1.25%)"] + [f"{r['prov']:,.0f} ({r['cc']*100:.2f}%)" for r in fb],
        ["법인세율 (가정)", "0.9%"] + [pc(t_, 0) for t_ in ab["tax"]],
        ["당기순이익", "1,126"] + [f0(r["ni"]) for r in fb],
        ["ROE (보통주 평균)", "5.3%"] + [pc(r["roe"]) for r in fb]]
table(rows, [30, 17, 17, 18, 18], hl_rows=(10, 11), hl_cols=(2, 3, 4),
      note="2025A NIM은 순이자이익 ÷ 평균 수익성자금(회사 공시 명목 NIM 1.40%와 정의가 다름). 법인세율: 2025년 실효세율 0.9%(DART), 2027E 이후 정상화 가정 — 이월결손금 잔액 확인 필요.")
img(HERE / "full_earn.png", W, caption="순이자이익 · 충당금적립전이익 · 순충당금 · 순이익(억원)과 ROE. 음영은 추정 구간")
h2("이익 추정 시나리오별 핵심 가정 (교차확인용)")
table([["가정", "보수", "기본", "낙관"],
       ["총여신 증가율 26E/27E/28E", *["/".join(f"{g*100:.0f}" for g in S[k]["assump"]["g"]) + "%" for k in ("보수", "기본", "낙관")]],
       ["대출이율 2028E", *[pc(S[k]["assump"]["yL"][2], 2) for k in ("보수", "기본", "낙관")]],
       ["조달이율 2028E", *[pc(S[k]["assump"]["cF"][2], 2) for k in ("보수", "기본", "낙관")]],
       ["대손비용률 2027E", *[pc(S[k]["assump"]["cc"][1], 2) for k in ("보수", "기본", "낙관")]],
       ["2027E / 2028E ROE", *[f"{S[k]['f'][1]['roe']*100:.1f}% / {S[k]['f'][2]['roe']*100:.1f}%" for k in ("보수", "기본", "낙관")]],
       ["2029년 이후 장기 ROE", *[pc(S[k]["assump"]["roe_lt"], 0) for k in ("보수", "기본", "낙관")]],
       ["카카오뱅크 플랫폼 프리미엄 반영", *[f"{S[k]['assump']['w_plat']:.0%}" for k in ("보수", "기본", "낙관")]]],
      [34, 22, 22, 22])

# ═════════════════════════ 5. 밸류에이션
h1("5. 밸류에이션 (Valuation)")
para("은행은 자본으로 얼마를 버느냐(ROE)가 가치를 정한다. 공모로 늘어난 초과자본을 따로 떼어 ① 핵심자본은 적정 PBR, 초과자본은 장부가로 평가하고, "
     "② 국내 상장 은행의 PBR–ROE 회귀에 카카오뱅크의 플랫폼 프리미엄 일부를 더해 50:50으로 가중했다. 증권사 목표주가는 계산에 넣지 않았다.")
h2("5-1. A. 초과자본 분리 적정 PBR")
table([["구성", "금액 (억원)", "적용 배수", "주당 (원)"],
       ["핵심자본 (CET1 13% 수준)", f0(N["core"]) + "억", f"{NB['pb_core']:.2f}배 = (ROE {NB['roe']*100:.0f}% − g {NB['g']*100:.1f}%) ÷ (COE {NB['coe']*100:.0f}% − g)", f0(N["core"] * NB["pb_core"] * 1e8 / N["dil"])],
       ["초과자본 (CET1 13% 초과분)", f0(N["excess"]) + "억", f"{NB['xm']:.1f}배 (장부가)", f0(N["excess"] * NB["xm"] * 1e8 / N["dil"])],
       ["A 주당가치", "", "", f0(NB["va"])]],
      [28, 14, 42, 16], hl_rows=(3,),
      note=f"초과자본 = 보통주자본 {N['cet1']:,}억 − 위험가중자산 {N['rwa']:,}억 × 13%(2026 반기보고서). COE = 국고채 10년 {N['rf']*100:.2f}%(10/26, 한국은행 ECOS) + 베타 약 1.0 × 위험프리미엄 약 6%. 주식수 407,535,286주(미행사 주식매수선택권 포함).")
para("공모 후 CET1이 12.4%에서 18.1%로 오른 만큼의 자본은 아직 대출로 바뀌지 않아 ROE를 낮춘다. 이를 장부가로 분리하지 않으면 은행 본업의 수익성이 실제보다 낮게 평가된다.")
h2("5-2. B. PBR–ROE 회귀 (국내 상장 은행 7곳)")
img(HERE / "price_pbr.png", W * .95, caption=f"우: PBR = {RG['icpt']:.2f} + {RG['slope']:.2f} × ROE (R² {RG['r2']:.2f}). 카카오뱅크는 회귀선보다 {K['premium']:.2f}배 높음(플랫폼 프리미엄)")
para(f"보통주 전체 기준 ROE {NB['fwd_roe']*100:.1f}%(핵심자본 ROE {NB['roe']*100:.0f}%와 초과자본 운용수익 세후 2.5%의 가중)를 회귀선에 넣고, 카카오뱅크 플랫폼 프리미엄 {K['premium']:.2f}배의 50%를 더하면 "
     f"PBR {NB['pb_b']:.2f}배, 주당 {NB['vb']:,.0f}원이다.")
h2("5-3. 종합 목표주가")
table([["방법", "가중치", "보수", "기본", "낙관"],
       ["A. 초과자본 분리 적정 PBR", "50%", f0(NL["va"]), f0(NB["va"]), f0(NH["va"])], ["B. PBR–ROE 회귀", "50%", f0(NL["vb"]), f0(NB["vb"]), f0(NH["vb"])],
       ["목표주가", "", f0(NL["tp"]), f"{NB['tp']:,.0f} → {TP:,}", f0(NH["tp"])],
       ["현재가 대비", "", pc(NL["upside"]), pc(UP), pc(NH["upside"])], ["투자의견", "", N["rating"]["보수"], RATING, N["rating"]["낙관"]],
       ["핵심 가정 (핵심자본 ROE / COE / 프리미엄 반영)", "", f"{NL['roe']*100:.0f}% / {NL['coe']*100:.0f}% / {NL['w_plat']:.0%}", f"{NB['roe']*100:.0f}% / {NB['coe']*100:.0f}% / {NB['w_plat']:.0%}", f"{NH['roe']*100:.0f}% / {NH['coe']*100:.1f}% / {NH['w_plat']:.0%}"]],
      [32, 10, 19, 20, 19], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, -5% ~ +15% HOLD, -5% 미만 SELL. 기본 시나리오는 경계선 바로 아래.")
img(HERE / "full_football.png", W)
h2("5-4. 민감도")
s1 = N["sens_roe_coe"]
table([["핵심자본 ROE × COE"] + [pc(c) for c in s1["coe"]]] + [[pc(r_, 0)] + [f0(x_) for x_ in row] for r_, row in zip(s1["roe"], s1["va"])],
      [20, 16, 16, 16, 16, 16], note="A 주당가치(원, g 2.5%, 초과자본 1.0배).")
s2 = N["sens_roe_plat"]
table([["핵심자본 ROE × 프리미엄 반영"] + [f"{w:.0%}" for w in s2["w"]]] + [[pc(r_, 0)] + [f0(x_) for x_ in row] for r_, row in zip(s2["roe"], s2["tp"])],
      [24, 15, 15, 15, 15, 16], note=f"목표주가(원). 현재가를 넘으려면 핵심자본 ROE {N['implied']['roe_at_price']*100:.1f}% 이상, 공모가를 회복하려면 {N['implied']['roe_at_ipo']*100:.1f}%가 필요하다.")
h2(f"5-5. 이익 추정 시나리오 — {TP_ALT:,}원")
table([["항목", f"기본 시나리오 — 목표가 {TP:,}원 (5-1 ~ 5-3)", f"이익 추정 시나리오 — {TP_ALT:,}원 (4장 추정 기반)"],
       ["ROE", f"핵심자본 지속 ROE {NB['roe']*100:.0f}% (보통주 전체 {NB['fwd_roe']*100:.1f}%)", f"2027E {B['roe27']*100:.1f}% · 2028E {B['f'][2]['roe']*100:.1f}%, 2029년 이후 8%로 수렴"],
       ["방법", "초과자본 분리 적정 PBR + 회귀", f"잔여이익모델(RIM) {B['rim']:,.0f}원 · 2027E ROE 회귀 {B['reg']:,.0f}원"],
       ["주당가치", f"{NB['tp']:,.0f}원 → {TP:,}원 ({UP:+.1%})", f"{B['tp']:,.0f}원 → {TP_ALT:,}원 ({TP_ALT/PRICE-1:+.1%}), 범위 {L['tp']:,.0f} ~ {H['tp']:,.0f}원"],
       ["이 시나리오가 맞으려면", f"초과자본이 대출로 바뀌며 핵심자본 ROE {NB['roe']*100:.0f}%가 유지", "금리 하락 · 판관비 증가 · 세율 정상화로 2027년까지 ROE 5%대"]],
      [16, 38, 46], note="두 시나리오 모두 현재가보다 낮다(SELL). 목표주가는 장기 수익성(핵심자본 ROE 8%)을 기준으로 한 기본 시나리오로 두고, 이익 추정 시나리오는 향후 1~2년 실적이 지금 추세대로 갈 때의 값으로 함께 제시한다.")

# ═════════════════════════ 6. 리스크 · 7. 전략
h1("6. 리스크 분석 (Risk Analysis)", new_page=False)
table([["방향", "리스크", "내용", "목표가 영향"],
       ["상방", "초과자본의 빠른 대출 전환", "개인사업자 · 주담대 성장으로 CET1 13%까지 자본을 쓰면 ROE 1~2%p 개선", "낙관 시나리오(7,100원 안팎)"],
       ["상방", "주주환원 정책 도입", "상장 첫 배당 · 자사주 정책이 나오면 초과자본이 장부가 이상으로 평가될 수 있음", "PBR 0.1배 ≈ 주당 570원"],
       ["상방", "가상자산 시장 확대", "업비트 예금 · 펌뱅킹 수수료 증가, 저원가 예금 유입", "민감도 표 참조"],
       ["하방", "보호예수 해제 (2027-03-05)", "BC카드 31.23% 등 34.19%가 유통 가능. FI 지분은 이미 6개월 해제", "수급 부담"],
       ["하방", "금리 인하 · 경쟁 심화", "대출금리가 조달금리보다 먼저 하락, 제4 인터넷은행 · 시중은행 비대면 경쟁", "보수 시나리오(2,400원 안팎)"],
       ["하방", "규제", "중·저신용자 대출 비중 30% 유지, 가계부채 총량 관리로 성장 제약", "대손비용률 상승"]],
      [9, 22, 47, 22])
h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
table([["항목", "내용"],
       ["투자의견 / 목표주가", f"{RATING} / {TP:,}원 (보통주 BPS 대비 {NB['pbr_tp']:.2f}배, 현재가 대비 {UP*100:+.1f}%)"],
       ["시나리오별 주당가치", f"기본(목표가) {TP:,}원 · 이익 추정 {TP_ALT:,}원 · 보수 {NL['tp']:,.0f}원 · 낙관 {NH['tp']:,.0f}원"],
       ["재검토 조건", "① 3Q26 실적에서 NIM 1.6% 이상 유지 + 대손비용률 1.0% 이하, ② 배당 · 자사주 등 자본정책 발표, ③ 주가가 보통주 PBR 0.65배(약 3,750원) 이하"],
       ["확인할 일정", "2026-10-30 3분기 실적 · IR, 2027-03-05 상장 1년 보호예수 해제, 2027-10-05 업비트 제휴 만기"],
       ["결론", "케이뱅크는 건전성이 안정적이고 고객 기반이 크지만, 공모 후 커진 자본에 비해 이익이 따라오지 못해 ROE 5%대에 머문다. "
                "공모가는 카카오뱅크 수준의 수익성을 가정했고, 현재가도 여전히 국내 은행 평균보다 높은 PBR을 받고 있다."]],
      [20, 80], first_left=True)
para("Disclaimer · 본 리포트는 DART 공시(사업 · 반기 · 분기보고서, 증권신고서 · 투자설명서, 공정공시), 한국은행 ECOS, 시세 DB(stock_db)를 바탕으로 작성한 개인 분석 자료입니다. "
     "목표주가와 투자의견은 작성자의 개인 견해이며 투자 권유가 아닙니다. 계산은 model.py · model_full.py로 재현할 수 있습니다(github.com/hopever0105/Equity-Research-Portfolio).", 6.8, color=GRAY, before=6)

out = HERE / "케이뱅크_리서치리포트_2026.docx"
doc.save(out); print(out)
import win32com.client
w = win32com.client.DispatchEx("Word.Application"); w.Visible = False; w.DisplayAlerts = 0
try:
    d = w.Documents.Open(str(out.resolve()), ReadOnly=True)
    print("pages", d.ComputeStatistics(2))
    d.ExportAsFixedFormat(str(out.with_suffix(".pdf").resolve()), 17); d.Close(False)
finally:
    w.Quit()
print(out.with_suffix(".pdf"))
