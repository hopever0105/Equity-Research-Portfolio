"""/valuation 전체 리포트 공통 서식 (재사용용). 한화생명·케이뱅크 make_full_report.py의 문서 유틸을 회사와 무관하게 뽑아 둔 것.
사용: from valuation.tools.report_kit import Rep, to_pdf, price_chart, football_chart, bar_chart, W, NAVY ...
  rp = Rep(sector="소프트웨어 (Enterprise AI)", asof_txt="2026년 8월 11일")
  rp.cover(dict(name=..., subtitle=..., rating=..., tp=..., price=..., unit="$", ...), market_rows, price_png)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NAVY, LIGHT, PALE, RED, GRAY, GREEN = "1F3864", "D9E2F3", "EEF3FA", "C00000", "595959", "548235"
W = 17.8
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False


def rating_of(upside):
    """투자의견 기준(한화생명·케이뱅크와 같음): +15% 이상 BUY, -5%~+15% HOLD, -5% 미만 SELL."""
    return "BUY" if upside >= 0.15 else ("HOLD" if upside >= -0.05 else "SELL")


# ═════════════════════════ 차트
def _t(s):
    """맑은 고딕에 없는 유니코드 빼기(−)를 차트 글자에서만 하이픈으로."""
    return s.replace("−", "-").replace("\\$", "$").replace("$", r"\$") if isinstance(s, str) else s   # $는 수식 기호라 이스케이프


def ax_clean(a):
    a.title.set_text(_t(a.title.get_text()))
    leg = a.get_legend()
    if leg:
        for t in leg.get_texts():
            t.set_text(_t(t.get_text()))
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.tick_params(labelsize=6.5)


def price_chart(dates, close, tp, out, title, unit="원", alt=None):
    fig, a = plt.subplots(figsize=(3.6, 2.5), dpi=220)
    a.plot(dates, close, color="#" + NAVY, lw=1.1)
    a.axhline(tp, color="#" + RED, ls="--", lw=.9)
    a.text(dates[int(len(dates) * .03)], tp, f" 목표주가 {fmt_px(tp, unit)}", fontsize=5.5, color="#" + RED, va="bottom")
    if alt:
        for v, lab in alt:
            a.axhline(v, color="#7F7F7F", ls=":", lw=.8)
            a.text(dates[int(len(dates) * .03)], v, f" {lab} {fmt_px(v, unit)}", fontsize=5.2, color="#595959", va="bottom")
    a.set_title(title, fontsize=7); ax_clean(a)
    from matplotlib.ticker import FuncFormatter
    a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))   # 1e6 같은 지수 표기 방지 (2026-11-06)
    a.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10))); a.xaxis.set_major_formatter(mdates.DateFormatter("%y.%m"))
    plt.tight_layout(); plt.savefig(out); plt.close()


def football_chart(rows, price, out, unit="원", xlabel="주당 가치 · 막대=보수~낙관, 점=기본"):
    """rows: [(라벨, 보수, 기본, 낙관), ...] 위에서 아래로."""
    fig, a = plt.subplots(figsize=(7.2, 0.45 * len(rows) + 0.9), dpi=220)
    for i, (lab, lo, mid, hi) in enumerate(rows[::-1]):
        a.barh(i, hi - lo, left=lo, color="#" + LIGHT, edgecolor="#" + NAVY, height=.5)
        a.plot(mid, i, "o", color="#" + NAVY, ms=4)
        a.text(hi, i, f"  {fmt_px(lo, unit)} ~ {fmt_px(hi, unit)}", va="center", fontsize=6)
    a.set_yticks(range(len(rows))); a.set_yticklabels([_t(r[0]) for r in rows[::-1]], fontsize=6.8)
    a.axvline(price, color="#" + RED, ls="--", lw=1)
    a.text(price, len(rows) - .45, f"현재가 {fmt_px(price, unit)}", color="#" + RED, fontsize=6.5, ha="center")
    lo_all = min(r[1] for r in rows + [("", price, price, price)]); hi_all = max(r[3] for r in rows + [("", price, price, price)])
    a.set_xlim(lo_all * .75, hi_all * 1.3)
    a.set_xlabel(_t(xlabel), fontsize=6.5); ax_clean(a)
    plt.tight_layout(); plt.savefig(out); plt.close()


def bar_chart(labels, series, out, title="", est_from=None, line=None, ylab="", figsize=(7.2, 2.3)):
    """series: [(이름, 값 리스트, 색)], line: (이름, 값 리스트) 보조축 꺾은선. est_from: 추정 시작 인덱스(음영)."""
    fig, a = plt.subplots(figsize=figsize, dpi=220)
    n = len(series); w = .8 / n
    for k, (nm, vals, col) in enumerate(series):
        xs = [i + (k - (n - 1) / 2) * w for i in range(len(labels))]
        a.bar(xs, vals, w, color=col, label=_t(nm))
    if est_from is not None:
        a.axvspan(est_from - .5, len(labels) - .5, color="#F2F2F2", zorder=0)
    a.set_xticks(range(len(labels))); a.set_xticklabels(labels, fontsize=6.5); a.set_ylabel(ylab, fontsize=6.5)
    a.axhline(0, color="#7F7F7F", lw=.6)
    if line:
        b = a.twinx(); b.plot(range(len(labels)), [v * 100 for v in line[1]], color="#" + RED, marker="o", ms=3, lw=1, label=_t(line[0]))
        b.set_ylabel("%", fontsize=6.5); b.tick_params(labelsize=6.5); b.spines["top"].set_visible(False)
        b.legend(fontsize=6, loc="upper right", frameon=False)
    a.legend(fontsize=6, loc="upper left", frameon=False, ncol=n); a.set_title(_t(title), fontsize=7.5); ax_clean(a)
    plt.tight_layout(); plt.savefig(out); plt.close()


def line_band_chart(dates, vals, mean, sd, out, title, ylab):
    fig, a = plt.subplots(figsize=(7.2, 2.2), dpi=220)
    a.plot(dates, vals, color="#" + NAVY, lw=1.1)
    for k, ls, lab in ((0, "-", "평균"), (1, "--", "+1σ"), (-1, ":", "-1σ")):
        a.axhline(mean + k * sd, color="#7F7F7F" if k != 1 else "#" + RED, ls=ls, lw=.8)
        a.text(dates[-1], mean + k * sd, f" {lab} {mean + k * sd:.2f}", fontsize=5.5, va="center")
    a.set_title(title, fontsize=7.5); a.set_ylabel(ylab, fontsize=6.5); ax_clean(a)
    plt.tight_layout(); plt.savefig(out); plt.close()


def fmt_px(v, unit):
    return f"${v:,.0f}" if unit == "$" else f"{v:,.0f}원"


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
    def __init__(self, sector, asof_txt, title_sub="", date_label="기준일"):
        self.doc, self.sec = new_doc()
        hp = self.sec.header.paragraphs[0]
        run(hp, f"EQUITY RESEARCH  │  {sector}{title_sub}", 7.5, True, NAVY)
        run(hp, "     " + f"{date_label}: {asof_txt}  │  작성자: 송호빈", 7, False, GRAY)
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
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

    def cover(self, name, subtitle, rating, tp, price, upside, unit, price_png, market_rows, alt_lines=()):
        """남색 제목 박스 → 투자의견 박스(목표가·현재가) + 주가 차트 + 시장 데이터 표."""
        t = self.doc.add_table(rows=1, cols=1); borders(t, NAVY, "4"); c = t.cell(0, 0); shade(c, NAVY); c.width = Cm(W)
        self.cellp(c, name, 17, True, "FFFFFF", WD_ALIGN_PARAGRAPH.LEFT)
        p = c.add_paragraph(); run(p, subtitle, 9, False, "D9E2F3"); p.paragraph_format.space_after = Pt(4)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)
        t = self.doc.add_table(rows=1, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t, "FFFFFF", "4")
        lc, rc = t.cell(0, 0), t.cell(0, 1); lc.width = Cm(W * .52); rc.width = Cm(W * .48)
        rt = lc.add_table(rows=1, cols=2); borders(rt, "FFFFFF", "8")
        a = rt.cell(0, 0); shade(a, GREEN if rating == "BUY" else (RED if rating == "SELL" else "7F7F7F")); a.width = Cm(3.2)
        self.cellp(a, rating, 20, True, "FFFFFF"); p = a.add_paragraph(); run(p, {"BUY": "(매수)", "SELL": "(매도)"}.get(rating, "(보유)"), 7.5, False, "FFFFFF"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        b2 = rt.cell(0, 1); shade(b2, LIGHT); b2.width = Cm(5.8)
        self.cellp(b2, "목표주가 (12개월)", 7, False, GRAY, WD_ALIGN_PARAGRAPH.LEFT)
        p = b2.add_paragraph(); run(p, fmt_px(tp, unit), 17, True, NAVY)
        p = b2.add_paragraph(); run(p, f"현재주가 {fmt_px(price, unit)} · {'상승' if upside >= 0 else '하락'}여력 {upside*100:+.1f}%", 7.5, True, GREEN if upside >= 0 else RED)
        for ln in alt_lines:
            p = b2.add_paragraph(); run(p, ln, 7, False, GRAY)
        self.img(price_png, W * .5, cont=lc)
        lc.paragraphs[0]._p.getparent().remove(lc.paragraphs[0]._p)
        self.table([["항목", "수치"]] + market_rows, [55, 45], 7.2, cont=rc)
        rc.paragraphs[0]._p.getparent().remove(rc.paragraphs[0]._p)

    def revision(self, prev_txt, summary, fixes, new, why, chap="8"):
        """마지막 장(Disclaimer 앞): 개정 내역 (이전판 대비) ①~④."""
        self.h1(f"{chap}. 개정 내역 (이전판 대비)")
        self.para(f"이 리포트는 {prev_txt}을 다시 쓴 것이다. 이전판은 그대로 보존하고, 달라진 점과 이전판에서 틀렸던 점을 아래에 모두 적는다. "
                  "기준일은 이전판 작성일과 같고, 그날까지 공개된 공시와 실제 종가만 썼다.", 8.5)
        self.h2(f"{chap}-1. 결론과 방법의 변화")
        self.table(summary, [20, 38, 42])
        self.h2(f"{chap}-2. 이전판에서 잘못했던 점과 고친 방법")
        self.table([["#", "이전판의 잘못", "개정판에서 고친 방법"]] + [[str(i + 1), a, b] for i, (a, b) in enumerate(fixes)], [4, 52, 44], size=7.0)
        self.h2(f"{chap}-3. 새로 넣은 분석")
        self.table([["새로 넣은 분석", "내용"]] + new, [22, 78])
        self.para("목표주가가 바뀐 이유: " + why, 8.0, before=2)

    def since(self, chap, orig_date, compare, market, method, why):
        """마지막 장(Disclaimer 앞): 원래 리포트 이후 달라진 점 (2026-11-05 본인 지시).
        원래 리포트의 잘못·오류는 쓰지 않는다. 그 사이 달라진 실적·데이터·시장상황 → 바꾼 방법·가정 → 목표가가 바뀐 이유.
        compare: 표 행 [[항목, 원래, 지금], ...] (머리행 포함), market/method: 글머리 문장 리스트, why: 한 문단."""
        self.h1(f"{chap}. 원래 리포트({orig_date}) 이후 달라진 점")
        self.para(f"이 리포트는 {orig_date}에 쓴 리포트를 그 뒤 나온 실적과 시장 상황으로 다시 조사한 후속 리포트다. "
                  "원래 리포트는 그대로 두고, 그 사이 달라진 점과 그래서 바꾼 판단을 아래에 정리한다.", 8.5)
        self.table(compare, [22, 37, 41])
        self.h2("그 사이 달라진 실적과 시장")
        for s in market:
            self.para("· " + s, 8.2, after=1)
        self.h2("그래서 바꾼 평가 방법과 가정")
        for s in method:
            self.para("· " + s, 8.2, after=1)
        self.h2("목표주가가 바뀐 이유")
        self.para(why, 8.2)

    def disclaimer(self, text):
        self.para("Disclaimer · " + text + " 목표주가와 투자의견은 작성자의 개인 견해이며 투자 권유가 아닙니다. "
                  "계산은 같은 폴더의 model.py로 재현할 수 있습니다(github.com/hopever0105/Equity-Research-Portfolio).", 6.8, color=GRAY, before=6)


def to_pdf(out):
    import win32com.client
    w = win32com.client.DispatchEx("Word.Application"); w.Visible = False; w.DisplayAlerts = 0
    try:
        d = w.Documents.Open(str(Path(out).resolve()), ReadOnly=True)
        n = d.ComputeStatistics(2)
        d.ExportAsFixedFormat(str(Path(out).with_suffix(".pdf").resolve()), 17); d.Close(False)
    finally:
        w.Quit()
    print("pages", n, Path(out).with_suffix(".pdf"))
    return n
