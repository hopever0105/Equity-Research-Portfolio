"""한화생명(088350) 밸류에이션 모델. 단위: 억원(주당·배수·비율 제외). 실행: python valuation/한화생명/model.py
기준일 2026-10-01 · 기준주가 2026-10-01 종가 5,300원(stock_db kor_price). 그날까지 공개된 공시(2026 반기보고서 정정 2026-08-31)만 쓴다.
출력: results.json (보고서·민감도용). 모든 가정은 ASSUMP 에 모아 둠. 출처는 주석.
방법: 목표가 = 보통주 ROE–COE 적정 PBR(고든) × 2Q26 보통주 BPS.
      적정 ROE는 CSM 롤포워드 → 보험손익 → 순이익 드라이버로 추정한 2027~2030E 평균 보통주 ROE.
      이익 추정 RIM(잔여이익모형)은 'RIM 시나리오'로 목표가와 나란히 둔다. 증권사 목표가는 쓰지 않음.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

# ───────────────────────── 기준 데이터 (확인값)
px = pd.read_csv(HERE / "price_db.csv", dtype={"종목코드": str})
px = px[px["날짜"] <= "2026-10-01"]
PRICE = float(px.iloc[-1]["종가"])                  # 5,300 (2026-10-01)
PRICE_DATE = str(px.iloc[-1]["날짜"])[:10]
SHARES_ISSUED = 868_530_000                          # 발행주식총수 (2026 반기보고서 주식총수현황)
TREASURY = 117_139_750                               # 자기주식 13.49%
SHARES = SHARES_ISSUED - TREASURY                    # 751,390,250 유통주식수
MCAP = PRICE * SHARES / 1e8

# DART 연결재무제표 (억원). 2024는 2025 사업보고서의 소급 재작성 비교표시 값(유배당 일탈회계 → IFRS17)
HIST = {  # 보험손익, 투자손익, 영업이익, 지배순이익, 지배지분, 신종자본증권, 신종자본증권배당(지배)
    "2023": dict(ins=8488.5, inv=2081.9, op=10570.4, ni=7584.8, eq=130381.7, hyb=4983.4, cpn=None),   # 2023 이자는 ROE 계산에 안 씀
    "2024": dict(ins=8347.2, inv=2622.4, op=10969.7, ni=7372.5, eq=118175.7, hyb=10968.3, cpn=283.4),
    "2025": dict(ins=6238.8, inv=5233.7, op=11472.5, ni=6413.1, eq=138752.3, hyb=30684.5, cpn=1144.6),
    "1H25": dict(ins=3979.3, inv=2141.3, op=6120.6, ni=3511.6, cpn=292.1),
    "1H26": dict(ins=4866.0, inv=6209.7, op=11075.6, ni=7719.5, eq=162537.0, hyb=30684.7, cpn=886.0),
}
for k, v in HIST.items():
    if "eq" in v:
        v["ce"] = v["eq"] - v["hyb"]                 # 보통주 자본 = 지배지분 - 신종자본증권
CE_NOW = HIST["1H26"]["ce"]                          # 131,852
BPS = CE_NOW * 1e8 / SHARES                          # 17,548
NI_TTM = HIST["2025"]["ni"] - HIST["1H25"]["ni"] + HIST["1H26"]["ni"]
CPN_TTM = HIST["2025"]["cpn"] - HIST["1H25"]["cpn"] + HIST["1H26"]["cpn"]
CNI_TTM = NI_TTM - CPN_TTM                           # 보통주 귀속 순이익
ROE_TTM = CNI_TTM / ((HIST["2025"]["ce"] + CE_NOW) / 2)
ROE_HIST = {y: (HIST[y]["ni"] - HIST[y]["cpn"]) / ((HIST[p]["ce"] + HIST[y]["ce"]) / 2)
            for p, y in [("2023", "2024"), ("2024", "2025")]}

# IFRS17 CSM (연결 주석 19 보험계약부채 구성요소별 변동, 발행 보험계약 PAA 외, 억원)
CSM = {"2024": 130657.9, "1H25": 130947.8, "2025": 129445.9, "1H26": 135447.1}
CSM_1H26 = dict(new=19368.1, adj=-10073.7, accr=2676.8, rel=-6092.3, other=122.5)   # 신계약, 추정치변동, 이자부리, 상각, 기타
CSM_SEP = {"2024": 91091.4, "1H25": 88331.0, "2025": 87136.5, "1H26": 89284.6}       # 별도
NEW_CSM_SEP_1H26 = 13001                              # 별도 신계약 CSM (반기보고서 사업의 내용)
REL_RATE = -CSM_1H26["rel"] * 2 / CSM["2025"]         # 연 상각률 9.41% (기초 대비)
ACCR_RATE = CSM_1H26["accr"] * 2 / CSM["2025"]        # 연 이자부리율 4.14%
K_INS = HIST["1H26"]["ins"] / -CSM_1H26["rel"]        # 보험손익 / CSM 상각 = 0.80 (RA 해제·예실차·손실부담·PAA 합산 효과)

# 자본적정성 (반기보고서 정정 2026-08-31, 한화생명 연결 K-ICS, 경과조치 적용)
KICS = {"2024": 163.7, "2025": 157.5, "1H26": 168.0}
KICS_AVAIL, KICS_REQ = 252154.2, 150111.7            # 지급여력 / 지급여력기준 (억원)
HGI_KICS, HGI_KICS_PRE = 227.9, 184.7                 # 한화손해보험 1H26 (경과조치 적용 / 적용 전, 원문 주5)

# 배당가능이익 제약 (별도, 2025 사업보고서 주석 34-1)
SURR_RES = dict(before=36312.1, add_2025=28765.8)     # 해약환급금준비금 기적립 + 2025 적립예정
ADJ_NI_2025 = -26955.6                                # 준비금 전입 후 조정이익 (음수 → 배당 불가)

# ALM: 금리와 자본 (연결 포괄손익, 1H26 누적)
OCI_1H26 = dict(bond=-46733.1, liab=78287.2, total=18403.4)   # FVOCI 채무증권 평가손익, 보험계약 순금융손익, 기타포괄손익 합계
rf = pd.read_csv(HERE / "rf_ktb10y.csv", dtype={"date": str})
RF = float(rf[rf.date <= "20261001"].iloc[-1]["value"]) / 100          # 4.436% (2026-10-01)
RF_2025 = float(rf[rf.date <= "20251230"].iloc[-1]["value"]) / 100     # 3.385%
RF_1H26 = float(rf[rf.date <= "20260630"].iloc[-1]["value"]) / 100     # 4.091%
DRATE_BP = (RF_1H26 - RF_2025) * 1e4
OCI_PER_BP = OCI_1H26["total"] / DRATE_BP             # 금리 1bp 상승당 기타포괄손익(세후, 억원) 근사

# 베타: 주간 수익률 3년, KOSPI(yfinance ^KS11) 대비 → Blume 조정
yf = pd.read_csv(HERE / "yf_kospi_hl.csv", index_col=0, parse_dates=True)
w = yf[yf.index >= "2023-10-01"].resample("W-FRI").last().pct_change().dropna()
BETA_RAW = float(np.cov(w["088350.KS"], w["^KS11"])[0, 1] / w["^KS11"].var())
BETA = 0.67 * BETA_RAW + 0.33
MRP = 0.07                                            # 시장위험프리미엄 가정 (민감도 표에서 6~8%)
COE_CAPM = RF + BETA * MRP

# 피어 (peers_ins.py, 2026-10-01 종가, 2Q26 보통주자본, TTM 지배순이익)
peers = pd.read_csv(HERE / "peers_ins.csv", dtype={"code": str})


def pbr_band():
    """IFRS17 이후 보통주 PBR 밴드. 분기 보통주 자본(DART 연결, 당시 공시값)을 공시 시점(1Q 5/15, 반기 8/14, 3Q 11/14,
    사업보고서 다음해 3/15)부터 적용. 자기주식 수는 현재값 고정(확인 필요: 과거 변동 여부)."""
    raw, cache = HERE / "dart_fs_raw.csv", HERE / "ce_hist.csv"   # 원본 DART csv가 없으면(저장소) 저장해 둔 분기 보통주자본을 읽는다
    if raw.exists():
        d = pd.read_csv(raw, dtype=str)
        pub = {"11013": ("05-15", 0), "11012": ("08-14", 0), "11014": ("11-14", 0), "11011": ("03-15", 1)}
        rows = []
        for (y, r), x in d[d.sj_div == "BS"].groupby(["year", "reprt"]):
            def v(n):
                z = x[x.account_nm.str.strip() == n]
                return float(z.iloc[0].thstrm_amount) / 1e8 if len(z) else 0.0
            md, add = pub[r]
            rows.append(dict(period=f"{y}-{r}", pub=pd.Timestamp(f"{int(y) + add}-{md}"), ce=v("지배주주지분") - v("신종자본증권")))
        pd.DataFrame(rows).sort_values("pub").to_csv(cache, index=False, encoding="utf-8-sig")
    b = pd.read_csv(cache, parse_dates=["pub"]).set_index("pub")["ce"]
    p = px.assign(날짜=pd.to_datetime(px["날짜"])).set_index("날짜")["종가"]
    p = p[p.index >= b.index[0]]
    bps = b.reindex(p.index.union(b.index)).ffill().reindex(p.index) * 1e8 / SHARES
    s = (p / bps).dropna()
    return s


BAND = pbr_band()
BAND_MEAN, BAND_SD = float(BAND.mean()), float(BAND.std())
WEIGHTS = {"A": 0.5, "B": 0.5}   # A 고든 적정 PBR(내재가치) · B 자기 PBR 밴드(시장이 실제로 준 배수)
BAND_K = {"보수": 0.0, "기본": 1.0, "낙관": 2.0}   # B의 목표 PBR = 평균 + kσ

# ───────────────────────── 시나리오 가정
ASSUMP = {
    "보수": dict(new=30000, adj=-0.60, inv=6500, coe=COE_CAPM + 0.007, g=0.005, payout=0.0),
    "기본": dict(new=35000, adj=-0.40, inv=7300, coe=COE_CAPM, g=0.010, payout=0.20),
    "낙관": dict(new=38000, adj=-0.25, inv=8000, coe=COE_CAPM - 0.007, g=0.015, payout=0.30),
}
# new = 연간 신계약 CSM(연결, 억원; 1H26 19,368 → 연 환산 3.9조, 2023~25 별도만 연 2조 이상)
# adj = 신계약 대비 CSM 추정치 변동(가정변경·경험조정) 비율. 1H26 실적 -52%
# inv = 2027E 투자손익(억원). 2025 5,234 · TTM 9,303 의 평균 7,269 근처. 이후 연 2% 증가
# payout = 2028년부터 보통주 배당성향(해약환급금준비금 제도개선 전제). 2026~27E는 0
TAX = 0.26                                            # 2025 유효세율 (법인세차감전 1조 1,325억 → 순이익 8,363억)
NCI = 0.19                                            # 비지배 귀속 비율 (2025 23%, 1H26 15%의 중간)
CPN = HIST["1H26"]["cpn"] * 2                         # 신종자본증권 연 이자 1,772억
NONOP = 0.0                                           # 영업외손익 (1H26 +44억, 무시)
YEARS = [2026, 2027, 2028, 2029, 2030]


def forecast(a):
    """CSM 롤포워드 → 보험손익 → 지배·보통주 순이익 → 보통주 자본. 2026E는 1H26 실적 + 2H26 추정."""
    rows, csm, ce = [], CSM["2025"], HIST["2025"]["ce"]
    for y in YEARS:
        if y == 2026:
            new = CSM_1H26["new"] + a["new"] / 2
            adj = CSM_1H26["adj"] + a["adj"] * a["new"] / 2
            inv = HIST["1H26"]["inv"] + (HIST["2025"]["inv"] - HIST["1H25"]["inv"])   # 1H26 + 2H25
        else:
            new, adj = a["new"], a["adj"] * a["new"]
            inv = a["inv"] * 1.02 ** (y - 2027)
        rel = REL_RATE * csm
        accr = ACCR_RATE * csm
        csm_end = csm + new + adj + accr - rel
        ins = K_INS * rel
        op = ins + inv
        ni = (op + NONOP) * (1 - TAX)
        ni_ctrl = ni * (1 - NCI)
        cni = ni_ctrl - CPN
        div = cni * a["payout"] if y >= 2028 else 0.0
        # 2026E 기말 자본 = 2Q26 실제 보통주 자본(금리 상승 OCI 포함) + 2H26E 보통주 순이익. 이후 OCI는 0 가정
        ce_end = CE_NOW + cni - (HIST["1H26"]["ni"] - HIST["1H26"]["cpn"]) if y == 2026 else ce + cni - div
        roe = cni / ((ce + ce_end) / 2)
        rows.append(dict(year=y, csm_beg=csm, new=new, adj=adj, accr=accr, rel=rel, csm_end=csm_end, ins=ins, inv=inv,
                         op=op, ni=ni, ni_ctrl=ni_ctrl, cni=cni, div=div, ce_beg=ce, ce_end=ce_end, roe=roe))
        csm, ce = csm_end, ce_end
    return rows


def gordon(roe, coe, g):
    pb = (roe - g) / (coe - g)
    return pb * BPS, pb


def rim(a, rows):
    """보통주 자본 2Q26에서 출발. 2H26 잔여이익(반기) + 2027~30E + 2030E 이후 영구성장."""
    coe, g = a["coe"], a["g"]
    v, ce = CE_NOW, CE_NOW
    r26 = rows[0]
    h2 = r26["cni"] - (HIST["1H26"]["ni"] - HIST["1H26"]["cpn"])          # 2H26E 보통주 순이익
    v += (h2 - coe / 2 * ce) / (1 + coe) ** 0.5
    ce += h2
    for i, r in enumerate(rows[1:], start=1):
        ri = r["cni"] - coe * ce
        v += ri / (1 + coe) ** (i + 0.5)
        ce = ce + r["cni"] - r["div"]
    last = rows[-1]
    ri_next = last["roe"] * ce * (1 + g) - coe * ce
    v += ri_next / (coe - g) / (1 + coe) ** (len(rows) - 0.5)
    return v * 1e8 / SHARES


def run(name, a, **kw):
    a = {**a, **kw}
    rows = forecast(a)
    roe_s = float(np.mean([r["roe"] for r in rows if r["year"] >= 2027]))
    va, pb = gordon(roe_s, a["coe"], a["g"])
    pb_b = BAND_MEAN + BAND_K.get(name, 1.0) * BAND_SD
    vb = pb_b * BPS
    tp = WEIGHTS["A"] * va + WEIGHTS["B"] * vb
    rv = rim(a, rows)
    return dict(name=name, **a, rows=rows, roe_s=roe_s, pb=pb, va=va, pb_b=pb_b, vb=vb, tp=tp, pbr_tp=tp / BPS,
                upside=tp / PRICE - 1, rim=rv, rim_up=rv / PRICE - 1)


def rating(up):
    return "BUY" if up >= 0.15 else ("HOLD" if up >= -0.05 else "SELL")


def round_tp(x):
    return int(round(x / 100.0) * 100)


if __name__ == "__main__":
    out = {"base_date": "2026-10-01", "price_date": PRICE_DATE, "price": PRICE, "shares_issued": SHARES_ISSUED,
           "treasury": TREASURY, "shares": SHARES, "mcap": MCAP, "hist": HIST, "ce_now": CE_NOW, "bps": BPS,
           "pbr_now": PRICE / BPS, "ni_ttm": NI_TTM, "cpn_ttm": CPN_TTM, "cni_ttm": CNI_TTM, "roe_ttm": ROE_TTM,
           "roe_hist": ROE_HIST, "per_now": MCAP / CNI_TTM, "csm": CSM, "csm_1h26": CSM_1H26, "csm_sep": CSM_SEP,
           "new_csm_sep_1h26": NEW_CSM_SEP_1H26, "rel_rate": REL_RATE, "accr_rate": ACCR_RATE, "k_ins": K_INS,
           "kics": KICS, "hgi_kics_pre": HGI_KICS_PRE, "kics_avail": KICS_AVAIL, "kics_req": KICS_REQ, "hgi_kics": HGI_KICS,
           "surr_res": SURR_RES, "adj_ni_2025": ADJ_NI_2025, "oci_1h26": OCI_1H26, "rf": RF, "rf_2025": RF_2025,
           "rf_1h26": RF_1H26, "drate_bp": DRATE_BP, "oci_per_bp": OCI_PER_BP, "beta_raw": BETA_RAW, "beta": BETA,
           "mrp": MRP, "coe": COE_CAPM, "tax": TAX, "nci": NCI, "cpn": CPN, "assump": ASSUMP,
           "peers": peers.to_dict("records"), "scen": {}}
    for k, a in ASSUMP.items():
        out["scen"][k] = run(k, a)
    base = out["scen"]["기본"]; b = ASSUMP["기본"]
    out["tp"] = round_tp(base["tp"])
    out["upside"] = out["tp"] / PRICE - 1
    out["rating"] = rating(out["upside"])
    out["rim_tp"] = round_tp(base["rim"])
    out["scen_tp"] = {k: round_tp(v["tp"]) for k, v in out["scen"].items()}
    out["scen_rim"] = {k: round_tp(v["rim"]) for k, v in out["scen"].items()}
    # 민감도 1: 적정 ROE × COE → 적정주가 (g 기본)
    roes = [0.05, 0.06, 0.07, 0.08, 0.09]; coes = [0.090, 0.095, 0.100, 0.105, 0.110, 0.115]
    vb0 = base["vb"]
    tp_of = lambda va: WEIGHTS["A"] * va + WEIGHTS["B"] * vb0
    out["sens_roe_coe"] = {"roe": roes, "coe": coes, "v": [[tp_of(gordon(r, c, b["g"])[0]) for c in coes] for r in roes]}
    # 민감도 2: 연간 신계약 CSM × 추정치 변동 비율 → 목표가
    news = [28000, 31000, 35000, 38000, 41000]; adjs = [-0.6, -0.5, -0.4, -0.3, -0.2]
    out["sens_new_adj"] = {"new": news, "adj": adjs, "tp": [[run("x", b, new=n, adj=j)["tp"] for j in adjs] for n in news]}
    # 민감도 3: MRP × g
    mrps = [0.06, 0.065, 0.07, 0.075, 0.08]; gs = [0.0, 0.005, 0.01, 0.015, 0.02]
    out["sens_mrp_g"] = {"mrp": mrps, "g": gs, "tp": [[tp_of(gordon(base["roe_s"], RF + BETA * m, gg)[0]) for gg in gs] for m in mrps]}
    out["band"] = dict(mean=BAND_MEAN, sd=BAND_SD, min=float(BAND.min()), max=float(BAND.max()), start=str(BAND.index[0].date()),
                       series={str(k.date()): float(v) for k, v in BAND.resample("W-FRI").last().dropna().items()})
    out["weights"] = WEIGHTS
    # 역산: 현재가가 내포한 지속 ROE (COE·g 기본)
    out["implied_roe"] = b["g"] + (PRICE / BPS) * (b["coe"] - b["g"])
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

    print(f"price {PRICE:,.0f} ({PRICE_DATE}) shares {SHARES:,} mcap {MCAP:,.0f}억 CE {CE_NOW:,.0f} BPS {BPS:,.0f} PBR {PRICE/BPS:.3f}")
    print(f"NI_TTM {NI_TTM:,.0f} cpn {CPN_TTM:,.0f} CNI {CNI_TTM:,.0f} ROE_TTM {ROE_TTM*100:.2f}% hist {[round(v*100,2) for v in ROE_HIST.values()]} PER {MCAP/CNI_TTM:.2f}")
    print(f"CSM rel {REL_RATE*100:.2f}% accr {ACCR_RATE*100:.2f}% k {K_INS:.3f}  rf {RF*100:.3f}% beta raw {BETA_RAW:.3f} adj {BETA:.3f} COE {COE_CAPM*100:.2f}%")
    print(f"band {BAND.index[0].date()}~ mean {BAND_MEAN:.3f} sd {BAND_SD:.3f} min {BAND.min():.3f} max {BAND.max():.3f}")
    print(f"ALM: Δrate {DRATE_BP:.1f}bp OCI {OCI_1H26['total']:,.0f}억 → {OCI_PER_BP:,.1f}억/bp")
    for k, v in out["scen"].items():
        print(f"{k}: ROE_s {v['roe_s']*100:.2f}% A PB {v['pb']:.3f} {v['va']:,.0f} | B PB {v['pb_b']:.3f} {v['vb']:,.0f} -> TP {v['tp']:,.0f} ({v['upside']*100:+.1f}%) PBR {v['pbr_tp']:.3f} RIM {v['rim']:,.0f} ({v['rim_up']*100:+.1f}%)")
        for r in v["rows"]:
            print(f"   {r['year']} CSM {r['csm_beg']:,.0f}->{r['csm_end']:,.0f} ins {r['ins']:,.0f} inv {r['inv']:,.0f} NI {r['ni']:,.0f} CNI {r['cni']:,.0f} ROE {r['roe']*100:.2f}% CE {r['ce_end']:,.0f}")
    print("TP", out["tp"], f"{out['upside']*100:+.1f}%", out["rating"], "RIM", out["rim_tp"], "implied ROE", round(out["implied_roe"] * 100, 2))
