"""피어 EV/EBITDA 재계산 (순차입금을 DART 2026 반기 재무상태표 원자료로 직접 구성).
이전 버전 오류: stock_db kor_fs 의 '유동/비유동금융부채'에는 차입금·사채가 빠져 있어 순차입금이 과소(순현금 과대)였음.
단위 억원. 부채 = 단기+유동성장기+장기 차입금 + 사채(교환사채 포함) + 리스부채. 유동성 자산 = 현금 + 단기금융상품/예치금 + 유동 금융자산(당기손익·상각후원가).
시총·TTM EBITDA·TTM 지배순이익 = peers_kr.csv (stock_db: kor_ticker 2026-10-22, kor_fs 분기 합)."""
import pandas as pd
from pathlib import Path
H = Path(__file__).resolve().parent
p = pd.read_csv(H / "peers_kr.csv", dtype={"code": str}).set_index("name")
D = {  # 출처: DART 반기보고서(2026.06) 연결 BS (peers_bs_dart.csv)
 "오리온":   dict(borrow=0.0, bond=0.0, lease=272.2 + 1223.3, cash=6632.9, st_fin=6979.2, oth_liq=50.0, note="차입금 없음; 단기금융예치금; 당기손익금융자산 50"),
 "농심":     dict(borrow=275.1, bond=1138.5, lease=130.2 + 286.9, cash=2194.2, st_fin=8425.5, oth_liq=0.0, note="교환사채 1,138.5; 기타 유동 금융자산 2,186은 성격 불명이라 제외(보수적)"),
 "롯데웰푸드": dict(borrow=1356.9 + 2807.1, bond=3769.2 + 6688.7, lease=315.1 + 814.0, cash=3545.5, st_fin=0.0, oth_liq=859.8, note="사채 10,458 · 차입금 4,164; 기타 유동 금융자산 860"),
 "오뚜기":   dict(borrow=5300.6 + 1232.1 + 2259.3, bond=0.0, lease=289.0 + 486.7, cash=4425.4, st_fin=1579.2, oth_liq=814.8, note="단기차입금 5,301 + 유동성장기 1,232 + 장기 2,259; 상각후원가(유동) 1,579 + 당기손익 815"),
 "해태제과식품": dict(borrow=577.2, bond=399.7 + 1096.5, lease=29.2 + 27.7, cash=123.6, st_fin=0.0, oth_liq=4.8, note="사채(유동성 포함) 1,496"),
 "삼양식품": dict(borrow=368.8 + 3549.1, bond=0.0, lease=262.4 + 449.3, cash=6306.0, st_fin=1187.1, oth_liq=61.3, note="기타유동금융부채 1,632(성격 불명)는 부채에서 제외"),
}
rows = []
for n, d in D.items():
    r = p.loc[n]
    debt = d["borrow"] + d["bond"] + d["lease"]; liq = d["cash"] + d["st_fin"] + d["oth_liq"]
    nd = debt - liq; ev = r.mcap + nd + r.nci
    rows.append(dict(name=n, mcap=r.mcap, debt=debt, liquid=liq, netdebt=nd, nci=r.nci, ev=ev, op=r.op, da=r.dep + r.amo,
                     ebitda=r.ebitda, ni=r.ni, rev=r.rev, OPM=r.op / r.rev, PER=r.mcap / r.ni, EV_EBITDA=ev / r.ebitda,
                     old_netdebt=r.netdebt, old_EV_EBITDA=r["EV/EBITDA"], note=d["note"]))
v = pd.DataFrame(rows); v.to_csv(H / "peers_kr_v2.csv", index=False, encoding="utf-8-sig")
x = v.set_index("name")
ex = x.loc[["농심", "롯데웰푸드", "오뚜기", "해태제과식품"]]; al = x.loc[["농심", "롯데웰푸드", "오뚜기", "해태제과식품", "삼양식품"]]
print(v[["name", "mcap", "netdebt", "nci", "ebitda", "EV_EBITDA", "old_EV_EBITDA", "PER", "OPM"]].round(2).to_string(index=False))
print("median EV/EBITDA ex-삼양 %.2f / incl %.2f ; PER ex %.2f / incl %.2f" % (ex.EV_EBITDA.median(), al.EV_EBITDA.median(), ex.PER.median(), al.PER.median()))
