"""OpenDART 수집 도구 (재사용용). 사용: python -m valuation_models.tools.dart 오리온 271560"""
import json, sys, time, zipfile, io, xml.etree.ElementTree as ET
from pathlib import Path
import requests, pandas as pd

BASE = Path(__file__).resolve().parents[1]
API = "https://opendart.fss.or.kr/api"

def key():
    for l in (BASE / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith("DART_API_KEY="):
            return l.split("=", 1)[1].strip()

def corp_code(stock_code, cache=BASE / "tools" / "corpCode.xml"):
    if not cache.exists():
        r = requests.get(f"{API}/corpCode.xml", params={"crtfc_key": key()}, timeout=60)
        z = zipfile.ZipFile(io.BytesIO(r.content)); cache.write_bytes(z.read(z.namelist()[0]))
    for e in ET.parse(cache).getroot().iter("list"):
        if e.findtext("stock_code", "").strip() == stock_code:
            return e.findtext("corp_code"), e.findtext("corp_name")

def fs(corp, year, reprt="11011", fs_div="CFS"):
    """reprt: 11013 1Q, 11012 반기, 11014 3Q, 11011 사업보고서"""
    r = requests.get(f"{API}/fnlttSinglAcntAll.json", params=dict(
        crtfc_key=key(), corp_code=corp, bsns_year=year, reprt_code=reprt, fs_div=fs_div), timeout=60).json()
    if r.get("status") != "000":
        return pd.DataFrame()
    d = pd.DataFrame(r["list"]); d["year"] = year; d["reprt"] = reprt; d["fs_div"] = fs_div
    return d

def disclosures(corp, bgn, end, pblntf_ty="B"):
    r = requests.get(f"{API}/list.json", params=dict(crtfc_key=key(), corp_code=corp, bgn_de=bgn,
                     end_de=end, pblntf_ty=pblntf_ty, page_count=100), timeout=60).json()
    return pd.DataFrame(r.get("list", []))

def collect(name, stock_code, years, out):
    corp, nm = corp_code(stock_code)
    out.mkdir(parents=True, exist_ok=True)
    frames = []
    for y in years:
        for rp in ["11013", "11012", "11014", "11011"]:
            d = fs(corp, y, rp)
            if d.empty:
                d = fs(corp, y, rp, "OFS")
            if not d.empty:
                frames.append(d)
            time.sleep(0.2)
    pd.concat(frames).to_csv(out / "dart_fs_raw.csv", index=False, encoding="utf-8-sig")
    disclosures(corp, "20240101", "20261231").to_csv(out / "dart_major_disclosures.csv", index=False, encoding="utf-8-sig")
    disclosures(corp, "20240101", "20261231", "I").to_csv(out / "dart_disclosures_issuer.csv", index=False, encoding="utf-8-sig")
    (out / "corp.json").write_text(json.dumps({"corp_code": corp, "name": nm, "stock_code": stock_code}, ensure_ascii=False))
    return corp

if __name__ == "__main__":
    name, code = sys.argv[1], sys.argv[2]
    print(collect(name, code, range(2021, 2027), BASE / name))


def document_text(rcept_no, out_dir=None):
    """공시 원문(document.xml zip) -> 태그 제거 텍스트. 사업보고서·잠정실적 공시 본문 확인용."""
    import re
    r = requests.get(f"{API}/document.xml", params={"crtfc_key": key(), "rcept_no": rcept_no}, timeout=120)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    txt = []
    for n in z.namelist():
        raw = z.read(n)
        for enc in ("utf-8", "euc-kr", "cp949"):
            try:
                s = raw.decode(enc); break
            except UnicodeDecodeError:
                continue
        s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
        s = re.sub(r"</(tr|p|div|table)>", "\n", s)
        s = re.sub(r"</t[dh]>", " | ", s)
        s = re.sub(r"<[^>]+>", " ", s)
        txt.append(re.sub(r"[ \t ]+", " ", s))
    t = "\n".join(txt)
    if out_dir:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / f"{rcept_no}.txt").write_text(t, encoding="utf-8")
    return t
