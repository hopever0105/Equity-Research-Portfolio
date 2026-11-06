"""재조사·신규 리포트 공통 계산 도구 (재사용용, 2026-11-06 영원무역·한화솔루션·삼성전기에서 처음 씀).
- hist(): fs_summary_<asof>.csv → 연간·분기 실적 dict (억원)
- band(): 월말 종가 ÷ 그때 공시된 지배 BPS(또는 최근 4분기 지배 EPS) 밴드 (공시 지연 45일, 사업보고서 90일)
- gordon_pbr / gordon_per: 적정 배수
사용: from valuation.tools.simple_val import hist, band, gordon_pbr, gordon_per
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
QEND = {"1Q": "-03-31", "2Q": "-06-30", "3Q": "-09-30", "FY": "-12-31"}
LAG = {"1Q": 45, "2Q": 45, "3Q": 45, "FY": 90}


def hist(name, asof):
    d = pd.read_csv(BASE / name / f"fs_summary_{asof}.csv")
    fy, q = {}, {}
    for _, r in d.iterrows():
        k = r["기간"]
        rec = {c: (None if pd.isna(r[c]) else float(r[c])) for c in d.columns if c not in ("기간", "fs_div")}
        (fy if k.endswith("FY") else q)[k[:4] if k.endswith("FY") else k] = rec
    # 4분기(3개월) = 연간 − 1~3Q (흐름 항목)
    for y in list(fy):
        if all(f"{y}{p}" in q for p in ("1Q", "2Q", "3Q")):
            q[f"{y}4Q"] = {c: (fy[y][c] - sum(q[f"{y}{p}"][c] or 0 for p in ("1Q", "2Q", "3Q"))
                               if c in ("매출", "영업이익", "세전이익", "당기순이익", "지배순이익") and fy[y][c] is not None
                               else fy[y][c]) for c in fy[y]}
    return fy, q


def _known(q, shares):
    """공시일(분기말 + 45일, 4분기는 + 90일) 기준으로 알려진 지배 BPS와 최근 4분기 지배 EPS 시계열."""
    keys = sorted(q, key=lambda k: (k[:4], k[4:]))
    rows = []
    for i, k in enumerate(keys):
        y, p = k[:4], k[4:]
        d = pd.Timestamp(y + QEND["FY" if p == "4Q" else p]) + pd.Timedelta(days=LAG["FY" if p == "4Q" else p])
        bps = q[k]["지배자본"] * 1e8 / shares if q[k].get("지배자본") else np.nan
        last4 = keys[max(0, i - 3): i + 1]
        eps = (sum(q[j]["지배순이익"] for j in last4) * 1e8 / shares
               if len(last4) == 4 and all(q[j].get("지배순이익") is not None for j in last4) else np.nan)
        rows.append((d, bps, eps))
    return pd.DataFrame(rows, columns=["d", "bps", "eps"]).set_index("d").sort_index()


def band(px, q, shares, asof, start=None, kind="pbr"):
    """px: 종가 Series(일별). 월말 종가 ÷ 그 시점 알려진 BPS(kind='pbr') 또는 EPS(kind='per', 적자 달 제외)."""
    k = _known(q, shares)
    m = px[px.index <= asof].resample("ME").last()
    if start:
        m = m[m.index >= start]
    base = k["bps" if kind == "pbr" else "eps"].reindex(m.index.union(k.index)).ffill().reindex(m.index)
    s = (m / base).replace([np.inf, -np.inf], np.nan).dropna()
    if kind == "per":
        s = s[(s > 0) & (s < 200)]
    return dict(series={str(i.date()): float(v) for i, v in s.items()}, mean=float(s.mean()), sd=float(s.std()),
                min=float(s.min()), max=float(s.max()), now=float(s.iloc[-1]), n=int(len(s)),
                start=str(s.index[0].date()), end=str(s.index[-1].date()))


def gordon_pbr(roe, coe, g=0.02):
    return (roe - g) / (coe - g)


def gordon_per(roe, coe, g):
    return (1 - g / roe) / (coe - g)
