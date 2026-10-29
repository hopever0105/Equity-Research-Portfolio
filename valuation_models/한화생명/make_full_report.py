"""한화생명_리서치리포트_2026_개정판.docx/.pdf (전체판, 약 10쪽) + _요약본(2~3쪽). 서식은 케이뱅크 make_full_report.py 를 따른다.
입력: results.json(model.py), price_db.csv. 실행: python valuation/한화생명/make_full_report.py
기준일 2026-10-01. 원래 리포트(2026-05-12, BUY 7,500원)와 바뀐 점은 한화생명_수정메모.md.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
S = R["scen"]; B, L, H = S["기본"], S["보수"], S["낙관"]
PRICE, TP, UP, RATING = R["price"], R["tp"], R["upside"], R["rating"]
TP_RIM = R["rim_tp"]
HI, HS = R["hist"], R["hist"]
FB = B["rows"]
NAVY, LIGHT, PALE, RED, GRAY, GREEN = "1F3864", "D9E2F3", "EEF3FA", "C00000", "595959", "548235"
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
f0 = lambda x: f"{x:,.0f}"
pc = lambda x, d=1: f"{x*100:.{d}f}%"
jo = lambda x: f"{x/1e4:.2f}조"
SH = R["shares"]

# ═════════════════════════ 차트
px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str}).assign(d=lambda x: pd.to_datetime(x.날짜)).set_index("d")
px = px[(px.index >= "2024-10-01") & (px.index <= "2026-10-01")]


def ax_clean(a):
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.tick_params(labelsize=6.5)


# 1) 주가 (표지)
fig, a = plt.subplots(figsize=(3.6, 2.5), dpi=220)
a.plot(px.index, px["종가"], color="#" + NAVY, lw=1.1)
a.axhline(TP, color="#" + RED, ls="--", lw=.9)
a.text(px.index[5], TP + 120, f"목표주가 {TP:,}", fontsize=5.5, color="#" + RED)
a.set_title("최근 2년 종가(원), 기준일 2026-10-01", fontsize=7); ax_clean(a)
import matplotlib.dates as mdates
a.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7))); a.xaxis.set_major_formatter(mdates.DateFormatter("%y.%m"))
plt.tight_layout(); plt.savefig(HERE / "full_price.png"); plt.close()

# 2) PBR 밴드
band = pd.Series(R["band"]["series"]); band.index = pd.to_datetime(band.index)
bm, bs = R["band"]["mean"], R["band"]["sd"]
fig, a = plt.subplots(figsize=(7.2, 2.2), dpi=220)
a.plot(band.index, band.values, color="#" + NAVY, lw=1.1, label="보통주 PBR")
for k, ls, lab in ((0, "-", "평균"), (1, "--", "+1σ"), (-1, ":", "-1σ"), (2, ":", "+2σ")):
    a.axhline(bm + k * bs, color="#7F7F7F" if k != 1 else "#" + RED, ls=ls, lw=.8)
    a.text(band.index[-1], bm + k * bs + .005, f"{lab} {bm + k*bs:.2f}", fontsize=5.8, ha="right", color="#" + GRAY if k != 1 else "#" + RED)
a.axhline(TP / R["bps"], color="#" + GREEN, ls="-.", lw=.9)
a.text(band.index[0], TP / R["bps"] + .006, f"목표주가 PBR {TP/R['bps']:.2f}배", fontsize=5.8, color="#" + GREEN)
a.set_title(f"IFRS17 이후 보통주 PBR (주가 ÷ 공시 시점 보통주 BPS, {R['band']['start']} ~ 2026-10-01)", fontsize=7); ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / "full_band.png"); plt.close()

# 3) CSM 롤포워드(1H26) + 잔액 추이
c = R["csm_1h26"]; c0 = R["csm"]["2025"]
steps = [("2025말", c0), ("신계약", c["new"]), ("추정치 변동", c["adj"]), ("이자부리", c["accr"]), ("상각(이익 인식)", c["rel"]), ("기타", c["other"])]
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.3), dpi=220, gridspec_kw={"width_ratios": [1.6, 1]})
cum = 0
for i, (n, v) in enumerate(steps):
    if i == 0:
        a.bar(i, v / 1e4, color="#9DB4D6"); cum = v
    else:
        a.bar(i, v / 1e4, bottom=cum / 1e4 if v > 0 else (cum + v) / 1e4, color="#2F5597" if v > 0 else "#F4B183")
        cum += v if v > 0 else 0
        if v < 0:
            cum += v
    a.text(i, (cum if i else v) / 1e4 + .15, f"{v/1e4:+.2f}" if i else f"{v/1e4:.2f}", ha="center", fontsize=6)
a.bar(len(steps), R["csm"]["1H26"] / 1e4, color="#" + NAVY); a.text(len(steps), R["csm"]["1H26"] / 1e4 + .15, f"{R['csm']['1H26']/1e4:.2f}", ha="center", fontsize=6)
a.set_xticks(range(len(steps) + 1)); a.set_xticklabels([s[0] for s in steps] + ["2Q26"], fontsize=6)
a.set_ylim(11, 15.8); a.set_title("1H26 연결 CSM 변동 (조원)", fontsize=7); ax_clean(a)
lab = ["2024말", "1H25", "2025말", "1H26"]
b.plot(lab, [R["csm"][k] / 1e4 for k in ("2024", "1H25", "2025", "1H26")], "o-", color="#" + NAVY, lw=1.2, ms=3, label="연결")
b.plot(lab, [R["csm_sep"][k] / 1e4 for k in ("2024", "1H25", "2025", "1H26")], "s-", color="#9DB4D6", lw=1.2, ms=3, label="별도(생보)")
for x_, k in enumerate(("2024", "1H25", "2025", "1H26")):
    b.text(x_, R["csm"][k] / 1e4 + .2, f"{R['csm'][k]/1e4:.1f}", ha="center", fontsize=5.8)
    b.text(x_, R["csm_sep"][k] / 1e4 - .55, f"{R['csm_sep'][k]/1e4:.1f}", ha="center", fontsize=5.8)
b.set_ylim(7.5, 14.5); b.legend(fontsize=5.8, frameon=False); b.set_title("CSM 잔액 (조원)", fontsize=7); ax_clean(b)
plt.tight_layout(); plt.savefig(HERE / "full_csm.png"); plt.close()

# 4) 금리와 자본 (ALM)
o = R["oci_1h26"]
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.2), dpi=220)
nm = ["FVOCI 채권\n평가손익", "보험계약\n순금융손익", "기타", "기타포괄손익\n합계"]
other = o["total"] - o["bond"] - o["liab"]
vals = [o["bond"], o["liab"], other, o["total"]]
a.bar(nm, [v / 1e4 for v in vals], color=["#F4B183", "#2F5597", "#BFBFBF", "#" + NAVY])
for i, v in enumerate(vals):
    a.text(i, v / 1e4 + (.25 if v > 0 else -.6), f"{v/1e4:+.2f}", ha="center", fontsize=6.3)
a.axhline(0, color="black", lw=.5); a.set_ylim(-6, 9.5); a.tick_params(axis="x", labelsize=6)
a.set_title(f"1H26 기타포괄손익(조원) — 국고채 10년 {R['rf_2025']*100:.2f}% → {R['rf_1h26']*100:.2f}%", fontsize=7); ax_clean(a)
kk = ["2024", "2025", "1H26"]
b.bar(kk, [R["kics"][k] for k in kk], color=["#9DB4D6", "#9DB4D6", "#" + NAVY], width=.55)
for i, k in enumerate(kk):
    b.text(i, R["kics"][k] + 2, f"{R['kics'][k]:.1f}%", ha="center", fontsize=6.5)
b.axhline(150, color="#" + RED, ls="--", lw=.8); b.text(2.3, 151.5, "권고 150%", fontsize=5.8, color="#" + RED, ha="right")
b.set_ylim(100, 185); b.set_title("K-ICS 비율 (연결, 경과조치 적용)", fontsize=7); ax_clean(b)
plt.tight_layout(); plt.savefig(HERE / "full_alm.png"); plt.close()

# 5) 실적 추정
yrs = ["2024A", "2025A"] + [f"{r['year']}E" for r in FB]
ins = [HI["2024"]["ins"], HI["2025"]["ins"]] + [r["ins"] for r in FB]
inv = [HI["2024"]["inv"], HI["2025"]["inv"]] + [r["inv"] for r in FB]
cni = [HI["2024"]["ni"] - HI["2024"]["cpn"], HI["2025"]["ni"] - HI["2025"]["cpn"]] + [r["cni"] for r in FB]
roe = [R["roe_hist"]["2024"], R["roe_hist"]["2025"]] + [r["roe"] for r in FB]
fig, a = plt.subplots(figsize=(7.2, 2.4), dpi=220)
x = range(len(yrs)); w = .27
for i, (v, col, n) in enumerate(((ins, "#9DB4D6", "보험손익"), (inv, "#F4B183", "투자손익"), (cni, "#" + NAVY, "보통주 순이익"))):
    a.bar([j + (i - 1) * w for j in x], v, w, color=col, label=n)
a.set_xticks(list(x)); a.set_xticklabels(yrs); a.set_ylabel("억원", fontsize=6.5); ax_clean(a)
a2 = a.twinx(); a2.plot(list(x), [r_ * 100 for r_ in roe], "o-", color="#" + RED, lw=1.2, ms=3, label="보통주 ROE(우)")
a2.set_ylim(0, 12); a2.tick_params(labelsize=6.5); a2.spines["top"].set_visible(False)
for j, r_ in enumerate(roe):
    a2.text(j, r_ * 100 + .5, f"{r_*100:.1f}%", fontsize=6, color="#" + RED, ha="center")
h1_, l1_ = a.get_legend_handles_labels(); h2_, l2_ = a2.get_legend_handles_labels()
a.legend(h1_ + h2_, l1_ + l2_, fontsize=6, ncol=4, loc="upper left", frameon=False)
a.axvspan(1.5, len(yrs) - .5, color="#F2F2F2", zorder=-1)
plt.tight_layout(); plt.savefig(HERE / "full_earn.png"); plt.close()

# 6) 풋볼필드
rows_ff = [("A. 고든 적정 PBR (50%)", L["va"], B["va"], H["va"]), ("B. 자기 PBR 밴드 (50%)", L["vb"], B["vb"], H["vb"]),
           ("목표주가 = A·B 평균", L["tp"], B["tp"], H["tp"]), ("RIM 시나리오 (이익 추정)", L["rim"], B["rim"], H["rim"])]
fig, a = plt.subplots(figsize=(7.2, 2.0), dpi=220)
for i, (n, lo, mid, hi) in enumerate(rows_ff[::-1]):
    a.barh(i, hi - lo, left=lo, color="#2F5597" if n.startswith("목표") else ("#F4B183" if n.startswith("RIM") else "#9DB4D6"), height=.5)
    a.plot(mid, i, "o", color="white", mec="#" + NAVY, ms=5); a.text(hi + 150, i, f"{mid:,.0f}", va="center", fontsize=6.5)
a.set_yticks(range(4)); a.set_yticklabels([r_[0] for r_ in rows_ff[::-1]], fontsize=7)
a.axvline(PRICE, color="#" + RED, ls="--", lw=1); a.text(PRICE, 3.45, f"현재가 {PRICE:,.0f}", color="#" + RED, fontsize=6.5, ha="center")
a.set_xlim(2_500, 15_500); a.set_xlabel("주당 가치(원) · 막대=보수~낙관, 점=기본", fontsize=6.5); ax_clean(a)
plt.tight_layout(); plt.savefig(HERE / "full_football.png"); plt.close()


# ═════════════════════════ 문서 유틸
def new_doc():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.6); sec.top_margin = Cm(1.5); sec.bottom_margin = Cm(1.4)
    sec.header_distance = Cm(0.6); sec.footer_distance = Cm(0.6)
    st = doc.styles["Normal"]; st.font.name = "Malgun Gothic"; st.font.size = Pt(8.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Malgun Gothic")
    st.paragraph_format.space_after = Pt(2); st.paragraph_format.line_spacing = 1.25
    return doc, sec


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


class Rep:
    def __init__(self, title_sub):
        self.doc, self.sec = new_doc()
        hp = self.sec.header.paragraphs[0]
        run(hp, f"EQUITY RESEARCH  │  생명보험 (Life Insurance){title_sub}", 7.5, True, NAVY)
        run(hp, " " * (62 if not title_sub else 44) + "기준일: 2026년 10월 1일  │  작성자: 송호빈", 7, False, GRAY)
        pborder(hp, NAVY, "6")
        fp = self.sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(fp, "본 리포트는 공개 자료 기반 개인 분석 자료입니다. 투자 판단의 참고 자료로만 활용하시기 바랍니다.  |  Page ", 6.5, False, "808080")
        r = fp.add_run(); r.font.size = Pt(6.5)
        for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
            if tag:
                e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag); r._r.append(e)
            else:
                e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)

    def para(self, text="", size=8.5, bold=False, color=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=2, before=0, cont=None):
        p = (cont or self.doc).add_paragraph()
        run(p, text, size, bold, color); p.alignment = align
        p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(before)
        return p

    def h1(self, text, new_page=True):
        p = self.para(text, 12, True, NAVY, WD_ALIGN_PARAGRAPH.LEFT, 4, 8); pborder(p, NAVY, "12")
        p.paragraph_format.page_break_before = new_page
        p.paragraph_format.keep_with_next = True

    def h2(self, text):
        p = self.para("▌ " + text, 9.5, True, NAVY, WD_ALIGN_PARAGRAPH.LEFT, 2, 6)
        p.paragraph_format.keep_with_next = True

    @staticmethod
    def cellp(c, text, size=7.5, bold=False, color=None, align=WD_ALIGN_PARAGRAPH.CENTER):
        p = c.paragraphs[0]; run(p, text, size, bold, color); p.alignment = align
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.1
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        return p

    def table(self, rows, widths, size=7.3, first_left=True, hl_rows=(), hl_cols=(), note=None, cont=None):
        t = (cont or self.doc).add_table(rows=len(rows), cols=len(rows[0])); t.alignment = WD_TABLE_ALIGNMENT.CENTER
        borders(t)
        tot = sum(widths)
        for i, r in enumerate(rows):
            trPr = t.rows[i]._tr.get_or_add_trPr(); trPr.append(OxmlElement("w:cantSplit"))
            for j, v in enumerate(r):
                c = t.cell(i, j); c.width = Cm((W if cont is None else W / 2 - 0.4) * widths[j] / tot)
                head = i == 0
                self.cellp(c, v, size, head or i in hl_rows, "FFFFFF" if head else None,
                           WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and first_left and not head) else WD_ALIGN_PARAGRAPH.CENTER)
                if head:
                    shade(c, NAVY)
                elif i in hl_rows:
                    shade(c, LIGHT)
                elif j in hl_cols:
                    shade(c, PALE)
        if note:
            self.para(note, 6.8, color=GRAY, after=4, cont=cont)
        else:
            (cont or self.doc).add_paragraph().paragraph_format.space_after = Pt(1)
        return t

    def img(self, path, width=W, cont=None, caption=None):
        p = (cont or self.doc).add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Cm(width)); p.paragraph_format.space_after = Pt(1)
        if caption:
            self.para(caption, 6.8, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, after=4, cont=cont)

    def thesis_box(self, no, title, lines):
        t = self.doc.add_table(rows=1 + len(lines), cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t, "FFFFFF", "8")
        a = t.cell(0, 0).merge(t.cell(len(lines), 0)); shade(a, NAVY); a.width = Cm(1.3)
        self.cellp(a, no, 14, True, "FFFFFF")
        c = t.cell(0, 1); c.width = Cm(W - 1.3); shade(c, LIGHT); self.cellp(c, title, 9, True, NAVY, WD_ALIGN_PARAGRAPH.LEFT)
        for i, ln in enumerate(lines, 1):
            c = t.cell(i, 1); c.width = Cm(W - 1.3); shade(c, PALE); self.cellp(c, ln, 7.6, False, None, WD_ALIGN_PARAGRAPH.LEFT)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def kpi_tiles(self, items):
        t = self.doc.add_table(rows=1, cols=len(items)); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t, "FFFFFF", "12")
        for j, (lab, val, sub) in enumerate(items):
            c = t.cell(0, j); c.width = Cm(W / len(items)); shade(c, LIGHT if j % 2 == 0 else "E2EFDA")
            self.cellp(c, lab, 6.8, False, GRAY)
            p = c.add_paragraph(); run(p, val, 11.5, True, NAVY); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(0)
            p = c.add_paragraph(); run(p, sub, 6.5, False, GRAY); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(1)

    def page_break(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def to_pdf(out):
    import win32com.client
    w = win32com.client.DispatchEx("Word.Application"); w.Visible = False; w.DisplayAlerts = 0
    try:
        d = w.Documents.Open(str(out.resolve()), ReadOnly=True)
        print("pages", d.ComputeStatistics(2))
        d.ExportAsFixedFormat(str(out.with_suffix(".pdf").resolve()), 17); d.Close(False)
    finally:
        w.Quit()
    print(out.with_suffix(".pdf"))


# ═════════════════════════ 공통 블록
SUBTITLE = "CSM은 다시 늘고, 금리 상승이 자본을 키웠다 — 시장이 가정한 ROE 3.8%와 실제 7%대의 간극"
ce25 = HI["2025"]["ce"]


def cover(rp):
    t = rp.doc.add_table(rows=1, cols=1); borders(t, NAVY, "4"); c = t.cell(0, 0); shade(c, NAVY); c.width = Cm(W)
    rp.cellp(c, "한화생명 (088350 KS)", 17, True, "FFFFFF", WD_ALIGN_PARAGRAPH.LEFT)
    p = c.add_paragraph(); run(p, SUBTITLE, 9, False, "D9E2F3"); p.paragraph_format.space_after = Pt(4)
    rp.doc.add_paragraph().paragraph_format.space_after = Pt(2)
    t = rp.doc.add_table(rows=1, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t, "FFFFFF", "4")
    lc, rc = t.cell(0, 0), t.cell(0, 1); lc.width = Cm(W * .52); rc.width = Cm(W * .48)
    rt = lc.add_table(rows=1, cols=2); borders(rt, "FFFFFF", "8")
    a = rt.cell(0, 0); shade(a, GREEN if RATING == "BUY" else (RED if RATING == "SELL" else "7F7F7F")); a.width = Cm(3.2)
    rp.cellp(a, RATING, 20, True, "FFFFFF"); p = a.add_paragraph(); run(p, {"BUY": "(매수)", "SELL": "(매도)"}.get(RATING, "(보유)"), 7.5, False, "FFFFFF"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    b2 = rt.cell(0, 1); shade(b2, LIGHT); b2.width = Cm(5.8)
    rp.cellp(b2, "목표주가 (12개월)", 7, False, GRAY, WD_ALIGN_PARAGRAPH.LEFT)
    p = b2.add_paragraph(); run(p, f"{TP:,}원", 17, True, NAVY)
    p = b2.add_paragraph(); run(p, f"현재주가 {PRICE:,.0f}원 · 상승여력 {UP*100:+.1f}%", 7.5, True, GREEN)
    p = b2.add_paragraph(); run(p, f"RIM 시나리오 {TP_RIM:,}원 ({TP_RIM/PRICE-1:+.1%})", 7, False, GRAY)
    rp.img(HERE / "full_price.png", W * .5, cont=lc)
    lc.paragraphs[0]._p.getparent().remove(lc.paragraphs[0]._p)
    mk = [["항목", "수치"], ["현재주가 (2026.10.01 종가)", f"{PRICE:,.0f}원"], ["시가총액 (유통주식 기준)", f"{R['mcap']/1e4:.2f}조원"],
          ["발행주식 / 자기주식", "868,530,000 / 117,139,750주"], ["52주 최고 / 최저", "7,560 / 2,930원"],
          ["최대주주", "(주)한화 외 45.04%"], ["보통주 BPS / PBR", f"{R['bps']:,.0f}원 / {R['pbr_now']:.2f}배"],
          ["보통주 ROE (최근 4분기)", pc(R["roe_ttm"])], ["PER (보통주 순이익)", f"{R['per_now']:.1f}배"],
          ["K-ICS 비율 (2Q26)", f"{R['kics']['1H26']:.1f}%"], ["CSM (연결, 2Q26)", f"{R['csm']['1H26']/1e4:.2f}조원"],
          ["배당 (2024·2025 사업연도)", "무배당"]]
    rp.table(mk, [55, 45], 7.2, cont=rc)
    rc.paragraphs[0]._p.getparent().remove(rc.paragraphs[0]._p)


def fin_summary(rp, cols=5):
    sel = FB[:cols - 2]
    yy = ["2024A", "2025A"] + [f"{r['year']}E" for r in sel]
    rows = [["항목 (억원)"] + yy,
            ["보험손익", f0(HI["2024"]["ins"]), f0(HI["2025"]["ins"])] + [f0(r["ins"]) for r in sel],
            ["투자손익", f0(HI["2024"]["inv"]), f0(HI["2025"]["inv"])] + [f0(r["inv"]) for r in sel],
            ["영업이익", f0(HI["2024"]["op"]), f0(HI["2025"]["op"])] + [f0(r["op"]) for r in sel],
            ["지배주주 순이익", f0(HI["2024"]["ni"]), f0(HI["2025"]["ni"])] + [f0(r["ni_ctrl"]) for r in sel],
            ["보통주 순이익 (신종자본증권 이자 차감)", f0(HI["2024"]["ni"] - HI["2024"]["cpn"]), f0(HI["2025"]["ni"] - HI["2025"]["cpn"])] + [f0(r["cni"]) for r in sel],
            ["CSM 기말 (연결)", f0(R["csm"]["2024"]), f0(R["csm"]["2025"])] + [f0(r["csm_end"]) for r in sel],
            ["보통주 ROE", pc(R["roe_hist"]["2024"]), pc(R["roe_hist"]["2025"])] + [pc(r["roe"]) for r in sel],
            ["보통주 BPS (원)", f0(HI["2024"]["ce"] * 1e8 / SH), f0(ce25 * 1e8 / SH)] + [f0(r["ce_end"] * 1e8 / SH) for r in sel],
            ["PBR (현재가 기준)", "-", "-"] + [f"{PRICE / (r['ce_end'] * 1e8 / SH):.2f}배" for r in sel]]
    w_ = [30] + [14] * (len(yy))
    rp.table(rows, w_, hl_cols=tuple(range(3, 3 + len(sel))),
             note="자료: DART 연결재무제표(2024는 2025 사업보고서의 소급 재작성 비교표시 값), 2026E 이후 본 리포트 추정(기본 시나리오). BPS는 유통주식 751,390,250주 기준(과거 연도도 같은 주식수).")


# ═════════════════════════ 전체판
rp = Rep("")
cover(rp)
rp.h2("재무 요약 (Financial Summary, 연결 기준)")
fin_summary(rp, 5)
rp.page_break()
rp.h2("핵심 투자 포인트")
rp.thesis_box("①", "CSM이 다시 늘기 시작했다 — 다만 신계약의 절반을 가정 변경이 갉아먹는다",
              [f"연결 CSM {jo(R['csm']['2025'])}(2025말) → {jo(R['csm']['1H26'])}(2Q26), 6개월 +{(R['csm']['1H26']/R['csm']['2025']-1)*100:.1f}%. 신계약 CSM {jo(R['csm_1h26']['new'])}(별도 {R['new_csm_sep_1h26']/1e4:.2f}조)이 상각 {jo(-R['csm_1h26']['rel'])}의 3배",
               f"같은 기간 추정치 변동(계리가정·경험조정)이 {jo(R['csm_1h26']['adj'])}로 신계약의 {-R['csm_1h26']['adj']/R['csm_1h26']['new']*100:.0f}%. 기본 추정은 이 비율을 40%로, 보수는 60%로 두었다"])
rp.thesis_box("②", "금리가 오르면 자본이 늘어나는 회사 — 부채 듀레이션이 자산보다 길다",
              [f"1H26 국고채 10년 {R['rf_2025']*100:.2f}% → {R['rf_1h26']*100:.2f}%(+{R['drate_bp']:.0f}bp). 채권 평가손 {jo(R['oci_1h26']['bond'])}보다 보험부채 할인 효과 {jo(R['oci_1h26']['liab'])}가 커서 기타포괄손익 {jo(R['oci_1h26']['total'])}",
               f"금리 1bp당 자본 약 {R['oci_per_bp']:,.0f}억원(1H26 실측 근사). K-ICS {R['kics']['2025']:.1f}% → {R['kics']['1H26']:.1f}%. 거꾸로 금리 하락이 가장 큰 자본 위험이다"])
rp.thesis_box("③", f"주가는 ROE {R['implied_roe']*100:.1f}%를 가정한다 — 할인의 이유는 이익이 아니라 '나눌 수 없는 이익'",
              [f"보통주 ROE {pc(R['roe_hist']['2024'])}(2024) · {pc(R['roe_hist']['2025'])}(2025) · {pc(R['roe_ttm'])}(최근 4분기), 기본 추정 2027~2030E 평균 {pc(B['roe_s'])}",
               f"해약환급금준비금 적립으로 2025년 별도 조정이익 {R['adj_ni_2025']/1e4:.2f}조 → 2년 연속 무배당. 준비금 제도 개선(배당 재개)이 PBR 밴드 상단으로 가는 열쇠"])
rp.para(f"▶ 결론: 목표주가 {TP:,}원(A. 고든 적정 PBR {B['pb']:.2f}배 {B['va']:,.0f}원 · B. 자기 PBR 밴드 평균+1σ {B['pb_b']:.2f}배 {B['vb']:,.0f}원 50:50), "
        f"현재가 대비 {UP*100:+.1f}%로 **{RATING}**. 목표 PBR {TP/R['bps']:.2f}배는 IFRS17 이후 최고치({R['band']['max']:.2f}배)보다 낮다. "
        f"CSM 상각과 투자손익을 직접 추정한 **RIM 시나리오**는 {TP_RIM:,}원이며, 보수 시나리오({R['scen_tp']['보수']:,}원)도 현재가보다 높다. "
        "원래 리포트(2026-05-12, BUY 7,500원) 대비 목표가를 올린 이유는 2Q26 금리 상승에 따른 자본 증가(BPS +22%)와 CSM 순증 확인이다.", 8.5, before=4)

# 1. 기업 개요
rp.h1("1. 기업 개요 (Company Overview)")
rp.h2("1-1. 사업 소개")
rp.para("한화생명(088350)은 1946년 설립된 국내 대형 생명보험사로, 한화그룹 금융 부문의 중간 지주 역할을 겸한다. 별도 기준 자산 124.6조원(2Q26)이며, "
        "보장성 중심 상품 전략으로 2023~2025년 3년 연속 연 2조원 이상의 신계약 CSM을 확보했다(반기보고서). 2026년 상반기 별도 순이익 5,102억원, 별도 신계약 CSM 1조 3,001억원. "
        "판매는 한화생명금융서비스(GA, 100%) 등 자회사형 판매채널로 분리되어 있다.")
rp.h2("1-2. 연결 구조 — 생보 + 손보 + 자산운용·증권 + 해외")
rp.table([["회사", "지분율", "장부가 (억원)", "비고"],
          ["한화손해보험", "63.3% (의결권 51.86%)", "5,627", f"K-ICS {R['hgi_kics']:.1f}% (경과조치 전 {R['hgi_kics_pre']:.1f}%), 1H26 별도 순이익 2,153억"],
          ["한화자산운용", "100%", "10,929", "수탁고 점유율 4.7% 업계 5위 (2026-06)"],
          ["한화생명금융서비스", "100%", "7,847", "보험대리·중개 (판매 자회사)"],
          ["해외 생보 (베트남·인도네시아)", "100% / 99.6%", "2,439 / 1,977", "PT Bank Nationalnobu 40%(관계기업)"],
          ["한화저축은행 / 한화리츠", "100% / 30.2%", "1,785 / 2,390", "리츠는 연결 대상"]],
         [24, 20, 14, 42], note="자료: 2026 반기보고서 별도재무제표 주석(종속기업투자). 장부가는 별도 기준 취득원가.")
rp.h2("1-3. 운용자산 — 연결 자산 186.5조원의 구성")
rp.table([["구분 (2Q26, 연결)", "금액", "비중", "회계 처리"],
          ["당기손익-공정가치(FVPL) 금융자산", "56.9조", "30.5%", "수익증권·대체투자 등, 평가손익이 바로 이익에"],
          ["기타포괄손익-공정가치(FVOCI) 금융자산", "59.7조", "32.0%", "주로 장기채, 평가손익은 자본(OCI)"],
          ["상각후원가(AC) 금융자산", "56.8조", "30.5%", "대출채권 33.5조 · 유가증권 12.3조 · 기타 11.0조"],
          ["투자부동산 · 유형자산", "4.9조", "2.6%", "63빌딩 등"],
          ["보험계약부채 (참고)", "105.7조", "-", "최선추정 · 위험조정 · CSM 합계"]],
         [34, 13, 10, 43], note="자료: 2026 반기보고서 연결재무상태표. 비중은 자산총계 186.5조 대비.")
rp.h2("1-4. 주주 구성")
rp.table([["주주", "지분율", "비고"], ["(주)한화 외 특수관계인", "45.04%", "(주)한화 43.24%, 한화갤러리아타임월드 1.75%"],
          ["자기주식", "13.49%", "117,139,750주 — 시가총액·BPS 계산에서 제외"], ["예금보험공사", "10.00%", "공적자금 회수 지분"],
          ["국민연금공단", "5.57%", ""]], [30, 15, 55], note="자료: 2026 반기보고서(주주에 관한 사항, 2026-06-30).")

# 2. 실적 분석
rp.h1("2. 실적 분석 (Performance Review)")
rp.h2("2-1. 1H26 실적 리뷰 — 투자손익이 끌고 보험손익이 받쳤다")
rp.kpi_tiles([("1H26 지배주주 순이익", f"{HI['1H26']['ni']:,.0f}억", f"{(HI['1H26']['ni']/HI['1H25']['ni']-1)*100:+.0f}% YoY"),
              ("1H26 보험손익", f"{HI['1H26']['ins']:,.0f}억", f"{(HI['1H26']['ins']/HI['1H25']['ins']-1)*100:+.0f}% YoY"),
              ("1H26 투자손익", f"{HI['1H26']['inv']:,.0f}억", f"{(HI['1H26']['inv']/HI['1H25']['inv']-1)*100:+.0f}% YoY"),
              ("연결 CSM (2Q26)", jo(R["csm"]["1H26"]), f"2025말 대비 {(R['csm']['1H26']/R['csm']['2025']-1)*100:+.1f}%")])
rp.para("투자손익이 1H25 2,141억에서 6,210억으로 세 배가 되며 순이익 증가를 이끌었다(이자수익 2.41조, FVPL 평가 · 처분이익 증가). "
        "보험손익도 CSM 상각 6,092억이 이어지며 +22% 늘었지만, 경험조정은 1,714억 손실로 보험금이 예상보다 많이 나갔다. 1H25 비교 수치는 유배당 계약 회계(일탈회계 → IFRS17) 변경으로 소급 재작성된 값이다.")
rp.h2("2-2. 보험손익은 어디서 오나 — 1H26 보험서비스 결과 구성 (연결)")
rp.table([["항목", "금액 (억원)", "의미"],
          ["CSM 상각 (제공한 서비스)", "6,092", "이미 판 계약의 이익을 서비스 기간에 나눠 인식 — 이익의 뿌리"],
          ["위험조정(RA) 해제", "945", "불확실성 대가로 쌓아 둔 몫이 풀림"],
          ["경험조정 (예상 대비 실제)", "△1,714", "보험금 · 사업비가 예상보다 많이 나간 몫(예실차 손실)"],
          ["손실부담계약 손실 환입 / 신규 손실계약", "571 / △184", "기존 손실계약은 환입, 새로 판 손실계약은 즉시 비용"],
          ["과거 서비스 관련 변동", "989", "발생사고부채 재추정 이익"],
          ["보험서비스 결과 (PAA 외)", "6,699", "재보험 · 기타사업비 차감 전"],
          ["보험손익 (손익계산서)", "4,866", "재보험 · 기타사업비 · PAA 계약 포함 — CSM 상각의 0.80배"]],
         [28, 14, 58], hl_rows=(7,), note="자료: 2026 반기보고서 연결 주석 19(보험계약부채 구성요소별 변동, 부채 감소 = 이익으로 부호를 바꿔 표시). 모델은 '보험손익 = 0.80 × CSM 상각'으로 단순화.")
rp.h2("2-3. 수익성 · 자본 지표")
rp.table([["지표", "2024", "2025", "1H25", "1H26"],
          ["지배주주 순이익 (억원)", f0(HI["2024"]["ni"]), f0(HI["2025"]["ni"]), f0(HI["1H25"]["ni"]), f0(HI["1H26"]["ni"])],
          ["신종자본증권 이자 (억원)", f0(HI["2024"]["cpn"]), f0(HI["2025"]["cpn"]), f0(HI["1H25"]["cpn"]), f0(HI["1H26"]["cpn"])],
          ["신종자본증권 잔액 (억원)", f0(HI["2024"]["hyb"]), f0(HI["2025"]["hyb"]), "-", f0(HI["1H26"]["hyb"])],
          ["보통주 자본 (억원)", f0(HI["2024"]["ce"]), f0(ce25), "-", f0(HI["1H26"]["ce"])],
          ["보통주 ROE", pc(R["roe_hist"]["2024"]), pc(R["roe_hist"]["2025"]), "-", f"{pc(R['roe_ttm'])} (최근 4분기)"],
          ["K-ICS 비율 (연결)", f"{R['kics']['2024']:.1f}%", f"{R['kics']['2025']:.1f}%", "-", f"{R['kics']['1H26']:.1f}%"]],
         [30, 17, 17, 17, 19], note="보통주 자본 = 지배주주지분 − 신종자본증권. 신종자본증권은 2024년 1.10조 → 2025년 3.07조로 늘었고, 그 이자(연 1,770억 안팎)는 보통주 이익에서 뺀다.")
rp.para("신종자본증권이 자본의 19%(지배지분 16.25조 중 3.07조)를 차지한다. K-ICS를 지키기 위해 2025년에만 1.97조를 발행했고, 그 비용이 보통주 ROE를 1%p 안팎 낮춘다. "
        "보통주 기준으로 다시 계산하면 2025년 ROE는 4.9%로, 회사 전체 이익만 보면 놓치는 부분이다.")

# 3. 투자 포인트
rp.h1("3. 투자 포인트 (Investment Thesis)")
rp.h2("Thesis 1. CSM 순증 — 미래 이익의 창고가 다시 차고 있다")
rp.img(HERE / "full_csm.png", W, caption="좌: 1H26 연결 CSM 변동(신계약 · 추정치 변동 · 이자부리 · 상각). 우: 연결 · 별도 CSM 잔액. 자료: 반기 · 사업보고서 주석 19")
rp.para(f"CSM은 상각률 연 {R['rel_rate']*100:.1f}%(1H26 상각 × 2 ÷ 기초 잔액)로 이익이 되고, 이자부리(연 {R['accr_rate']*100:.1f}%)로 늘어난다. "
        f"따라서 '신계약 + 추정치 변동'이 기초 잔액의 약 {(R['rel_rate']-R['accr_rate'])*100:.1f}%를 넘으면 잔액이 늘어난다. 1H26은 신계약 1.94조에서 추정치 변동 1.01조를 빼도 0.93조가 남아 잔액이 늘었다. "
        "2025년에는 해지율 · 손해율 가정 변경으로 연결 CSM이 0.12조 줄었다. 핵심 변수는 신계약 규모가 아니라 가정 변경의 크기다(5-5절 민감도).")
rp.h2("Thesis 2. ALM — 금리가 오를 때 자본이 늘고, 내릴 때 줄어든다")
rp.img(HERE / "full_alm.png", W, caption="좌: 1H26 기타포괄손익 구성. 우: K-ICS 비율. 자료: 반기보고서 연결포괄손익계산서 · 재무건전성 지표, 한국은행 ECOS")
rp.para(f"IFRS17에서는 보험부채도 현재 금리로 할인한다. 1H26 금리가 {R['drate_bp']:.0f}bp 오르자 FVOCI 채권 평가손 {jo(R['oci_1h26']['bond'])}보다 보험부채 감소 효과 {jo(R['oci_1h26']['liab'])}가 더 컸다. "
        f"부채 듀레이션이 자산보다 길다는 뜻이고, 금리 1bp당 자본이 약 {R['oci_per_bp']:,.0f}억원(세후, 비지배 포함) 움직인다. "
        "보통주 자본이 2025말 10.81조에서 2Q26 13.19조로 22% 늘어난 대부분이 이 효과다. 이 리포트는 2H26 이후 기타포괄손익을 0으로 두어 금리 효과를 추정에 더하지 않았다. "
        "금리가 다시 2025말 수준으로 내려오면 자본이 1.8조 줄어들 수 있고, 장기채 매입으로 듀레이션 차이를 줄이는 속도가 자본 변동성을 결정한다.")
rp.table([["K-ICS (연결, 억원)", "2024", "2025", "2Q26"],
          ["지급여력 (A)", "213,317", "229,011", f0(R["kics_avail"])], ["지급여력기준 (B)", "130,276", "145,388", f0(R["kics_req"])],
          ["K-ICS 비율 (A/B)", f"{R['kics']['2024']:.1f}%", f"{R['kics']['2025']:.1f}%", f"{R['kics']['1H26']:.1f}%"]],
         [34, 22, 22, 22], note="자료: 2026 반기보고서(정정, 2026-08-31) 재무건전성 지표. 기본자본 K-ICS 비율은 공시에서 확인하지 못함(확인 필요).")
rp.h2("Thesis 3. 할인의 이유 — 해약환급금준비금과 무배당")
rp.table([["별도 기준 (억원)", "2024", "2025"],
          ["당기순이익 (별도)", "7,206", "3,133"], ["해약환급금준비금 적립 예정액", "11,265", "28,766"],
          ["준비금 전입 후 조정이익", "△4,403", f"△{-R['adj_ni_2025']:,.0f}"], ["해약환급금준비금 누적 (적립 후)", "36,312", f"{R['surr_res']['before']+R['surr_res']['add_2025']:,.0f}"],
          ["보통주 배당", "무배당", "무배당"]],
         [40, 30, 30], note="자료: 2025 사업보고서 별도 주석 34-1(감독목적상 적립금). 준비금은 이익잉여금 안에 쌓이며 배당가능이익에서 빠진다.")
rp.para(f"현재 주가는 보통주 PBR {R['pbr_now']:.2f}배로, COE {pc(R['coe'])} · 성장률 1%에서 지속 ROE {R['implied_roe']*100:.1f}%를 가정한 값이다. 실제 보통주 ROE는 5~7%대다. "
        "이 차이는 이익이 없어서가 아니라 이익을 주주에게 나눌 수 없어서 생긴다. 해약환급금준비금 적립 기준이 완화되거나 기본자본이 확충되어 배당이 재개되면, "
        "PBR 밴드 상단(평균 +1~2σ)으로 갈 근거가 생긴다. 기본 시나리오는 2028년부터 배당성향 20%, 낙관은 30%, 보수는 무배당 지속을 가정했다.")

# 4. 실적 추정
rp.h1("4. 실적 추정 (Earnings Forecast)")
rp.para("CSM을 먼저 굴린다(기초 + 신계약 + 추정치 변동 + 이자부리 − 상각). 보험손익은 CSM 상각의 0.80배(1H26 실적 비율), 투자손익은 2025년과 최근 4분기 평균에서 연 2% 성장, "
        f"세율 {R['tax']*100:.0f}%(2025 유효세율), 비지배 귀속 {R['nci']*100:.0f}%, 신종자본증권 이자 연 {R['cpn']:,.0f}억을 차례로 뺀다. 2026E 투자손익은 1H26 실적 + 2H25 실적이다.")
ab = R["assump"]["기본"]
rows = [["항목 (기본, 억원)", "2025A"] + [f"{r['year']}E" for r in FB],
        ["기초 CSM", "130,658"] + [f0(r["csm_beg"]) for r in FB],
        ["+ 신계약 CSM", "-"] + [f0(r["new"]) for r in FB],
        ["+ 추정치 변동", "-"] + [f0(r["adj"]) for r in FB],
        ["+ 이자부리 − 상각", "-"] + [f"{r['accr']:,.0f} / △{r['rel']:,.0f}" for r in FB],
        ["기말 CSM", f0(R["csm"]["2025"])] + [f0(r["csm_end"]) for r in FB],
        ["보험손익", f0(HI["2025"]["ins"])] + [f0(r["ins"]) for r in FB],
        ["투자손익", f0(HI["2025"]["inv"])] + [f0(r["inv"]) for r in FB],
        ["지배주주 순이익", f0(HI["2025"]["ni"])] + [f0(r["ni_ctrl"]) for r in FB],
        ["보통주 순이익", f0(HI["2025"]["ni"] - HI["2025"]["cpn"])] + [f0(r["cni"]) for r in FB],
        ["배당", "0"] + [f0(r["div"]) for r in FB],
        ["보통주 ROE", pc(R["roe_hist"]["2025"])] + [pc(r["roe"]) for r in FB]]
rp.table(rows, [24, 12, 13, 13, 13, 13, 13], hl_rows=(9, 11), hl_cols=(2, 3, 4, 5, 6),
         note="2026E 추정치 변동은 1H26 실적(△10,074억) + 2H26 가정. 2026E 기말 자본은 2Q26 실제 보통주 자본에 2H26E 순이익을 더함(금리 효과 포함), 2027E 이후 기타포괄손익 0.")
rp.img(HERE / "full_earn.png", W, caption="보험손익 · 투자손익 · 보통주 순이익(억원)과 보통주 ROE. 음영은 추정 구간")
rp.h2("시나리오별 핵심 가정")
rp.table([["가정", "보수", "기본", "낙관"],
          ["연간 신계약 CSM (연결, 2027E~)", *[f"{R['assump'][k]['new']/1e4:.1f}조" for k in ("보수", "기본", "낙관")]],
          ["추정치 변동 / 신계약", *[pc(R["assump"][k]["adj"], 0) for k in ("보수", "기본", "낙관")]],
          ["2027E 투자손익", *[f"{R['assump'][k]['inv']:,}억" for k in ("보수", "기본", "낙관")]],
          ["COE / 영구성장률 g", *[f"{R['assump'][k]['coe']*100:.1f}% / {R['assump'][k]['g']*100:.1f}%" for k in ("보수", "기본", "낙관")]],
          ["2028년~ 배당성향", *[pc(R["assump"][k]["payout"], 0) for k in ("보수", "기본", "낙관")]],
          ["2027~2030E 평균 보통주 ROE", *[pc(S[k]["roe_s"]) for k in ("보수", "기본", "낙관")]]],
         [34, 22, 22, 22], note="1H26 실적: 신계약 연 환산 3.9조, 추정치 변동 비율 △52%, 최근 4분기 투자손익 9,303억.")

# 5. 밸류에이션
rp.h1("5. 밸류에이션 (Valuation)")
rp.para("생명보험사는 이익이 계리가정에 따라 크게 흔들려 PER보다 자본 대비 수익성(PBR–ROE)으로 본다. ① 추정한 지속 ROE와 자본비용으로 계산한 적정 PBR(고든)과 "
        "② 시장이 IFRS17 이후 이 회사에 실제로 준 PBR 밴드를 50:50으로 가중했다. ①은 '이익이 결국 주주 몫이 된다면'의 값, ②는 배당 제약이 이어지는 현실의 값이다. 증권사 목표주가는 계산에 넣지 않았다.")
rp.h2("5-1. 자기자본비용 (COE)")
rp.table([["항목", "값", "근거"],
          ["무위험이자율", pc(R["rf"], 2), "국고채 10년, 2026-10-01 (한국은행 ECOS 817Y002)"],
          ["베타", f"{R['beta']:.2f}", f"주간 수익률 3년 KOSPI 대비 원베타 {R['beta_raw']:.2f} → Blume 조정(0.67 × β + 0.33)"],
          ["시장위험프리미엄", pc(R["mrp"], 1), "가정 (5-5절 민감도에서 6~8%)"],
          ["COE", pc(R["coe"], 2), "CAPM = 무위험이자율 + 베타 × 위험프리미엄"]],
         [22, 14, 64])
rp.h2("5-2. A. 고든 적정 PBR")
rp.para(f"적정 PBR = (지속 ROE − g) ÷ (COE − g) = ({B['roe_s']*100:.2f}% − {ab['g']*100:.1f}%) ÷ ({R['coe']*100:.2f}% − {ab['g']*100:.1f}%) = **{B['pb']:.2f}배**. "
        f"2Q26 보통주 BPS {R['bps']:,.0f}원을 곱하면 주당 **{B['va']:,.0f}원**. 지속 ROE는 4장 기본 추정의 2027~2030E 평균이다.")
rp.h2("5-3. B. 자기 PBR 밴드 (IFRS17 이후)")
rp.img(HERE / "full_band.png", W)
rp.para(f"{R['band']['start']} 이후 보통주 PBR은 평균 {bm:.2f}배, 표준편차 {bs:.2f}배, 범위 {R['band']['min']:.2f}~{R['band']['max']:.2f}배다. 이 기간의 대부분은 2025년 CSM 감소 · 무배당 구간이었다. "
        f"CSM 순증과 ROE 회복을 반영해 기본은 평균 +1σ({B['pb_b']:.2f}배, {B['vb']:,.0f}원), 보수는 평균({L['pb_b']:.2f}배), 낙관은 +2σ({H['pb_b']:.2f}배)를 쓴다.")
rp.h2("5-4. 종합 목표주가")
rp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. 고든 적정 PBR", "50%", f"{L['va']:,.0f} ({L['pb']:.2f}배)", f"{B['va']:,.0f} ({B['pb']:.2f}배)", f"{H['va']:,.0f} ({H['pb']:.2f}배)"],
          ["B. 자기 PBR 밴드", "50%", f"{L['vb']:,.0f} ({L['pb_b']:.2f}배)", f"{B['vb']:,.0f} ({B['pb_b']:.2f}배)", f"{H['vb']:,.0f} ({H['pb_b']:.2f}배)"],
          ["목표주가", "", f0(L["tp"]), f"{B['tp']:,.0f} → {TP:,}", f0(H["tp"])],
          ["목표 PBR", "", f"{L['pbr_tp']:.2f}배", f"{TP/R['bps']:.2f}배", f"{H['pbr_tp']:.2f}배"],
          ["현재가 대비", "", pc(L["upside"]), pc(UP), pc(H["upside"])],
          ["RIM 시나리오", "", f0(L["rim"]), f"{B['rim']:,.0f} → {TP_RIM:,}", f0(H["rim"])]],
         [26, 10, 21, 22, 21], hl_rows=(3,), note="투자의견 기준: +15% 이상 BUY, -5% ~ +15% HOLD, -5% 미만 SELL.")
rp.img(HERE / "full_football.png", W)
rp.h2("5-5. 민감도")
s1 = R["sens_roe_coe"]
rp.table([["지속 ROE × COE"] + [pc(c_) for c_ in s1["coe"]]] + [[pc(r_, 0)] + [f0(x_) for x_ in row] for r_, row in zip(s1["roe"], s1["v"])],
         [20, 13, 13, 13, 13, 14, 14], note=f"목표주가(원, B는 기본 {B['vb']:,.0f}원 고정, g {ab['g']*100:.1f}%).")
s2 = R["sens_new_adj"]
rp.table([["연간 신계약 CSM × 추정치 변동 비율"] + [pc(j, 0) for j in s2["adj"]]] + [[f"{n/1e4:.1f}조"] + [f0(x_) for x_ in row] for n, row in zip(s2["new"], s2["tp"])],
         [28, 14, 14, 14, 14, 16], note="목표주가(원). 추정치 변동 비율이 −60%로 커지면 신계약이 늘어도 목표가가 크게 낮아진다 — 신계약 규모보다 가정 변경이 더 중요하다.")
s3 = R["sens_mrp_g"]
rp.table([["시장위험프리미엄 × g"] + [pc(g_) for g_ in s3["g"]]] + [[pc(m_)] + [f0(x_) for x_ in row] for m_, row in zip(s3["mrp"], s3["tp"])],
         [24, 15, 15, 15, 15, 16], note="목표주가(원), 지속 ROE 기본 고정.")
rp.h2(f"5-6. RIM 시나리오 — {TP_RIM:,}원")
rp.table([["항목", f"기본 — 목표가 {TP:,}원", f"RIM 시나리오 — {TP_RIM:,}원"],
          ["방법", "고든 적정 PBR + 자기 PBR 밴드 (50:50)", "잔여이익모형: 2Q26 보통주 자본 + 2H26~2030E 잔여이익 현가 + 2030E 이후 영구성장"],
          ["배당 제약 반영", "B(밴드)가 무배당 구간의 시장 배수를 담음", "반영하지 않음 — 이익이 쌓인 자본도 COE 이상을 벌면 가치로 인정"],
          ["이 시나리오가 맞으려면", "준비금 제약이 일부 풀리고 PBR이 밴드 상단으로", "가정 변경 손실이 신계약의 40% 안에 머물고 배당 재개로 할인이 해소"]],
         [18, 38, 44], note="RIM은 할인 요인을 직접 넣지 않아 목표가보다 높다. 목표가는 기본 시나리오로 두고, RIM은 배당 재개가 확인될 때 가까워질 값으로 함께 제시한다.")
rp.h2("5-7. 교차확인 — 국내 상장 보험사 (2026-10-01)")
pr = [["회사", "구분", "시가총액 (억원)", "보통주자본 (억원)", "PBR", "PER", "ROE"]]
for p_ in R["peers"]:
    pr.append([p_["name"], p_["grp"], f0(p_["mcap"]), f0(p_["common_eq"]), f"{p_['PBR']:.2f}", f"{p_['PER']:.1f}", pc(p_["ROE"])])
rp.table(pr, [18, 8, 16, 18, 10, 10, 10], hl_rows=(1,),
         note="자료: DART 연결재무제표(2Q26 보통주자본 = 지배지분 − 신종자본증권, TTM 지배순이익), stock_db 종가 × 유통주식수. peers_ins.py로 재현. "
              "삼성생명은 삼성전자 지분 평가이익이 자본에 크게 반영돼 ROE가 낮게 나온다. 업종 PBR이 ROE와 뚜렷한 관계를 보이지 않아(손보 0.29~0.91배) 회귀는 쓰지 않았다.")

# 6. 리스크 · 7. 결론
rp.h1("6. 리스크 분석 (Risk Analysis)", new_page=False)
rp.table([["방향", "리스크", "내용", "목표가 영향"],
          ["하방", "금리 하락", f"부채 듀레이션 > 자산. 1bp당 자본 약 {R['oci_per_bp']:,.0f}억, K-ICS 하락", "BPS 하락 → A·B 모두 하락"],
          ["하방", "계리가정 변경 (연말)", "해지율 · 손해율 가정 강화 시 CSM 추정치 변동 확대", "변동 비율 −60% → 보수 시나리오"],
          ["하방", "투자손익 변동", "FVPL 대체투자 · 수익증권 평가손, 1H26 투자손익의 상당 부분이 평가이익", "2027E 투자손익 6,500억 → 보수"],
          ["하방", "자본 확충 부담", "신종자본증권 3.07조, 이자 연 1,770억이 보통주 ROE를 낮춤", "추가 발행 시 ROE 희석"],
          ["상방", "배당 재개", "해약환급금준비금 기준 완화, 배당가능이익 회복", "밴드 +2σ → 낙관 시나리오"],
          ["상방", "자사주 13.49% 소각", "상법 개정 · 밸류업 정책 시 유통주식 감소", "BPS · EPS 상승"]],
         [8, 20, 48, 24])
rp.h1("7. 투자 전략 및 결론 (Conclusion)", new_page=False)
rp.table([["항목", "내용"],
          ["투자의견 / 목표주가", f"{RATING} / {TP:,}원 (보통주 BPS 대비 {TP/R['bps']:.2f}배, 현재가 대비 {UP*100:+.1f}%)"],
          ["시나리오별 주당가치", f"기본(목표가) {TP:,}원 · RIM {TP_RIM:,}원 · 보수 {R['scen_tp']['보수']:,}원 · 낙관 {R['scen_tp']['낙관']:,}원"],
          ["재검토 조건", "① 3Q26 CSM 순증 지속 여부, ② 연말 계리가정 변경 규모(추정치 변동 / 신계약 60% 초과 시 하향), ③ 국고채 10년 3.5% 이하로 하락 시 자본 재점검"],
          ["확인할 일정", "2026년 11월 3분기 실적 · K-ICS, 2027년 3월 사업보고서(해약환급금준비금 · 배당), 해약환급금준비금 제도 개선 발표"],
          ["결론", "한화생명은 CSM이 다시 늘고 금리 상승으로 자본이 커졌지만, 해약환급금준비금 때문에 이익을 나눌 수 없어 PBR 0.3배에 머문다. "
                   "보수적으로 자기 PBR 밴드를 절반 반영해도 현재가보다 높고, 배당 재개가 확인되면 RIM 시나리오 쪽으로 다가간다."]],
         [20, 80])

# 8. 개정 내역
REV_SUMMARY = [["항목", "이전판 (2026-05-12)", "개정판 (2026-10-01 기준)"],
               ["투자의견 / 목표주가", "BUY / 7,500원 (기준주가 4,845원)", f"{RATING} / {TP:,}원 (기준주가 {PRICE:,.0f}원)"],
               ["평가 방법", "PBR(고든) 20 · PBR(업종할인) 40 · PER 30 · EV/보험이익 10, 뒤에 −9.3% 정성 할인",
                "A. 고든 적정 PBR 50 + B. 자기 PBR 밴드(IFRS17 이후 평균+1σ) 50, 정성 할인 없음"],
               ["이익 추정", "증권사 컨센서스(2026E 영업이익 8,160억 등)를 그대로 사용", "CSM 롤포워드(신계약 · 추정치 변동 · 이자부리 · 상각) → 보험손익 → 순이익 직접 추정"],
               ["대안 시나리오", "Bull 12,000 / Bear 4,000원", f"RIM {TP_RIM:,} · 보수 {R['scen_tp']['보수']:,} · 낙관 {R['scen_tp']['낙관']:,}원"],
               ["증권사 목표가", "컨센서스 표, 결론에 '컨센서스 대비 +25%'", "쓰지 않음"]]
REV_FIX = [["#", "이전판의 잘못", "개정판에서 고친 방법"],
           ["1", "BPS · PBR 기준 혼재: 표지 0.26배(별도 BPS 18,650원), 피어표 0.18배, 수정 PBR 0.13~0.26배가 한 문서 안에서 서로 다름",
            "연결 보통주 BPS(지배지분 − 신종자본증권 ÷ 유통주식) 하나로 통일 → PBR 0.30배"],
           ["2", "신종자본증권 3.07조(지배지분의 22%)를 보통주 자본에 포함, 그 이자(2025년 1,145억)도 이익에서 빼지 않아 BPS · ROE 과대",
            "자본과 이익 양쪽에서 모두 차감"],
           ["3", "자기주식 13.5%를 주식수에 포함(시가총액 = 4,845원 × 발행주식 전체)", "유통주식 751,390,250주 기준"],
           ["4", "이익 추정을 증권사 컨센서스에 의존", "DART 주석의 CSM 변동표로 직접 추정, 증권사 목표가는 계산에서 제외"],
           ["5", "십억원 · 억원 단위 혼용(예: '2025A 보험손익 344.4', 'OPM 바닥 431억')", "억원으로 통일"],
           ["6", "가중평균 8,272원 뒤 근거 없는 −9.3% 할인으로 7,500원", "할인 삭제, 배당 제약은 B(자기 PBR 밴드)로 시장 배수에 반영"],
           ["7", "경험조정 +1,714억을 이익처럼 읽음(부채 변동표 부호 오해)", "부채 감소 = 이익으로 부호를 바꿔 '경험조정 손실 1,714억'으로 표기"],
           ["8", "리스크표 '기본자본 K-ICS 60% 수준' — 공시 근거 없음", "삭제하고 '확인 필요'로 표기, K-ICS는 2Q26 168.0%(정정 공시)로 갱신"],
           ["9", "유배당 계약 회계 변경(일탈회계 → IFRS17) 전 수치 사용", "소급 재작성된 수치로 교체(1H25 지배순이익 3,512억 등)"]]
REV_NEW = [["새로 넣은 분석", "내용"],
           ["CSM 롤포워드", "연결 CSM 12.94 → 13.54조, 신계약 1.94조 vs 추정치 변동 −1.01조, 신계약 × 가정변경 민감도"],
           ["ALM (금리–자본)", f"1H26 금리 +{R['drate_bp']:.0f}bp에 채권 −4.67조 vs 보험부채 +7.83조 → 자본 +1.84조, 1bp당 약 {R['oci_per_bp']:,.0f}억"],
           ["배당 제약", "해약환급금준비금 적립으로 2년 연속 무배당 → 할인의 원인을 이익이 아니라 '나눌 수 없는 이익'으로 설명"],
           ["피어 7사 직접 계산", "DART 원본으로 보통주 자본 · TTM 이익을 다시 계산(peers_ins.py)"]]
rp.h1("8. 개정 내역 (이전판 대비)")
rp.para("이 리포트는 2026-05-12에 작성한 이전판(BUY, 목표주가 7,500원)을 다시 쓴 것이다. 이전판은 그대로 보존하고, 달라진 점과 이전판에서 틀렸던 점을 아래에 모두 적는다.", 8.5)
rp.h2("8-1. 결론과 방법의 변화")
rp.table(REV_SUMMARY, [20, 38, 42])
rp.h2("8-2. 이전판에서 잘못했던 점과 고친 방법")
rp.table(REV_FIX, [4, 52, 44], size=7.0)
rp.h2("8-3. 새로 넣은 분석")
rp.table(REV_NEW, [22, 78])
rp.para("목표주가를 7,500원 → 7,900원으로 올린 이유: 2Q26 금리 상승에 따른 보통주 자본 증가(BPS +22%)와 CSM 순증 확인. 방법을 바로잡은 효과(신종자본증권 · 자사주 차감은 하향, 정성 할인 삭제는 상향)는 서로 일부 상쇄됐다.", 8.0, before=2)
rp.para("Disclaimer · 본 리포트는 DART 공시(사업 · 반기보고서, 정정 포함), 한국은행 ECOS, 시세 DB(stock_db), yfinance(KOSPI 지수, 베타 계산)를 바탕으로 작성한 개인 분석 자료입니다. "
        "목표주가와 투자의견은 작성자의 개인 견해이며 투자 권유가 아닙니다. 계산은 model.py · peers_ins.py로 재현할 수 있습니다(github.com/hopever0105/Equity-Research-Portfolio).", 6.8, color=GRAY, before=6)
out = HERE / "한화생명_리서치리포트_2026_개정판.docx"
rp.doc.save(out); print(out); to_pdf(out)

# ═════════════════════════ 요약본 (2~3쪽)
sp = Rep("  │  요약본")
cover(sp)
sp.h2("재무 요약 (연결, 억원)")
fin_summary(sp, 5)
sp.h2("핵심 투자 포인트")
sp.thesis_box("①", f"CSM 순증: {jo(R['csm']['2025'])} → {jo(R['csm']['1H26'])}",
              [f"신계약 {jo(R['csm_1h26']['new'])} − 추정치 변동 {jo(-R['csm_1h26']['adj'])}(신계약의 {-R['csm_1h26']['adj']/R['csm_1h26']['new']*100:.0f}%) − 상각 {jo(-R['csm_1h26']['rel'])}. 핵심 변수는 가정 변경의 크기"])
sp.thesis_box("②", "ALM: 금리 상승이 자본을 키웠다",
              [f"1H26 금리 +{R['drate_bp']:.0f}bp → 기타포괄손익 {jo(R['oci_1h26']['total'])}(채권 {jo(R['oci_1h26']['bond'])}, 보험부채 {jo(R['oci_1h26']['liab'])}). 1bp당 약 {R['oci_per_bp']:,.0f}억, K-ICS {R['kics']['1H26']:.1f}%"])
sp.thesis_box("③", f"주가가 가정한 ROE {R['implied_roe']*100:.1f}% vs 실제 보통주 ROE {pc(R['roe_ttm'])}",
              [f"할인 원인은 해약환급금준비금(누적 {(R['surr_res']['before']+R['surr_res']['add_2025'])/1e4:.1f}조)으로 인한 무배당. 신종자본증권 이자를 뺀 보통주 기준으로 계산"])
sp.h2("밸류에이션 요약")
sp.table([["방법", "가중치", "보수", "기본", "낙관"],
          ["A. 고든 적정 PBR (ROE–COE)", "50%", f"{L['va']:,.0f}", f"{B['va']:,.0f} ({B['pb']:.2f}배)", f"{H['va']:,.0f}"],
          ["B. 자기 PBR 밴드 (평균 + kσ)", "50%", f"{L['vb']:,.0f}", f"{B['vb']:,.0f} ({B['pb_b']:.2f}배)", f"{H['vb']:,.0f}"],
          ["목표주가", "", f"{R['scen_tp']['보수']:,}", f"{TP:,} ({UP*100:+.1f}%)", f"{R['scen_tp']['낙관']:,}"],
          ["RIM 시나리오 (이익 추정)", "", f"{R['scen_rim']['보수']:,}", f"{TP_RIM:,}", f"{R['scen_rim']['낙관']:,}"]],
         [30, 10, 18, 24, 18], hl_rows=(3,),
         note=f"COE {pc(R['coe'],2)} = 국고채 10년 {pc(R['rf'],2)} + 베타 {R['beta']:.2f} × 7%. 지속 ROE = CSM 롤포워드로 추정한 2027~2030E 평균 보통주 ROE {pc(B['roe_s'])}. 전체판 5장 참조.")
sp.img(HERE / "full_football.png", W)
sp.table([["리스크", "내용"],
          ["금리 하락", f"부채 듀레이션 > 자산 → 1bp당 자본 약 {R['oci_per_bp']:,.0f}억 감소"],
          ["계리가정 변경", "추정치 변동 / 신계약 60% 시 보수 시나리오"],
          ["배당 재개 지연", "해약환급금준비금 제도 개선이 늦어지면 PBR 밴드 평균에 머묾"]], [22, 78])
sp.h2("이전판(2026-05-12, BUY 7,500원) 대비 고친 점")
sp.table([["이전판의 잘못", "개정판"],
          ["BPS · PBR 기준 혼재(0.26 · 0.18 · 0.13배)", "연결 보통주 BPS 하나로 통일 → 0.30배"],
          ["신종자본증권 3.07조 · 이자, 자사주 13.5% 미차감", "보통주 자본 · 이익 · 유통주식 기준으로 차감"],
          ["컨센서스 이익 · 근거 없는 −9.3% 할인", "CSM 롤포워드 직접 추정, 정성 할인 삭제"],
          ["단위 혼용, 경험조정 부호 오해, 근거 없는 K-ICS 문구", "억원 통일, 손실 1,714억으로 정정, 확인 필요 표기"]],
         [50, 50], size=7.0, note="전체 목록은 전체판 8장.")
sp.para("전체판: 한화생명_리서치리포트_2026_개정판(10쪽 안팎) · 계산 코드 model.py · peers_ins.py (github.com/hopever0105/Equity-Research-Portfolio)", 6.8, color=GRAY, before=4)
out2 = HERE / "한화생명_리서치리포트_2026_개정판_요약본.docx"
sp.doc.save(out2); print(out2); to_pdf(out2)
