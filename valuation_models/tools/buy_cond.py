"""'BUY가 되기 위한 조건' 계산 도구 (재조사 원칙 8, 2026-11-18 본인 지시).
목표가·의견은 각 model.py의 기존 방식 그대로 두고, 지금 주가에서 +15%(BUY 기준)가 되려면
무엇이 필요한지를 거꾸로 푼다. 목표가 계산에는 넣지 않는다.
사용: from valuation.tools.buy_cond import BUY_UP, buy_price, solve_min
"""
BUY_UP = 0.15   # report_kit.rating_of: +15% 이상 BUY


def buy_price(price):
    """BUY가 되려면 필요한 목표주가 = 현재가 × 1.15"""
    return price * (1 + BUY_UP)


def solve_min(f, lo, hi, target, steps=400):
    """f(x)가 target 이상이 되는 가장 작은 x (lo~hi 구간을 steps로 나눠 찾고 이분법으로 다듬음). 없으면 None.
    f는 x가 커질수록 값이 커지는 함수여야 한다."""
    prev = lo
    for i in range(steps + 1):
        x = lo + (hi - lo) * i / steps
        if f(x) >= target:
            if i == 0:
                return x
            a, b = prev, x
            for _ in range(40):
                m = (a + b) / 2
                if f(m) >= target:
                    b = m
                else:
                    a = m
            return b
        prev = x
    return None


def cond_price(tp_if_confirmed):
    """그 조건이 확인됐을 때의 적정가에서 15% 상승여력이 남는 매수 가격 = 적정가 ÷ 1.15"""
    return tp_if_confirmed / (1 + BUY_UP)
