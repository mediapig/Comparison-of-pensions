# -*- coding: utf-8 -*-
# cpf_life_engine.py
# Author: you + ChatGPT
# A compact CPF LIFE simulator with BHS cap, RA@55 (FRS/ERS), and annuity plans.
# Python 3.9+ recommended. Pure Python (no external deps).

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import math

# ==============================
# ---------- Defaults ----------
# ==============================

# Annual CPF Salary Ceiling - can be overridden by year table
ANNUAL_CPF_CEILING_DEFAULT = 102000  # 2025 benchmark (can be updated via parameters)

# Account interest rates (nominal annual, more precise rate structure)
OA_RATE = 0.025  # Ordinary Account
SA_RA_RATE = 0.040  # Special Account & Retirement Account
MA_RATE = 0.040  # MediSave Account

# CPF LIFE premium interest approximation (for annuity present value discounting)
PREMIUM_RATE = 0.035

# Escalating annuity annual growth rate
ESCALATING_G = 0.02

# Basic plan: only 10-20% goes to premium at age 65, rest stays in RA until ~90
BASIC_PREMIUM_PCT = 0.15  # adjustable

# Age-related contribution rates (more precise CPF rates)
CPF_RATES_BY_AGE = {
    # (employee_rate, employer_rate) for different age brackets
    (0, 35): (0.20, 0.17),    # Age 35 and below
    (36, 45): (0.20, 0.17),    # Age 36-45
    (46, 50): (0.20, 0.17),    # Age 46-50
    (51, 55): (0.20, 0.17),    # Age 51-55
    (56, 60): (0.20, 0.17),    # Age 56-60
    (61, 65): (0.20, 0.17),    # Age 61-65
    (66, 70): (0.075, 0.075),  # Age 66-70
    (71, 75): (0.05, 0.05),    # Age 71-75
}

# Age-related account allocation ratios (more precise allocation)
ACCOUNT_ALLOCATION_BY_AGE = {
    # (OA_pct, SA_pct, MA_pct) for different age brackets
    (0, 35): (0.23, 0.06, 0.08),    # Age 35 and below
    (36, 45): (0.23, 0.06, 0.08),    # Age 36-45
    (46, 50): (0.23, 0.06, 0.08),    # Age 46-50
    (51, 55): (0.23, 0.06, 0.08),    # Age 51-55
    (56, 60): (0.23, 0.06, 0.08),    # Age 56-60
    (61, 65): (0.23, 0.06, 0.08),    # Age 61-65
    (66, 70): (0.23, 0.06, 0.08),    # Age 66-70
    (71, 75): (0.23, 0.06, 0.08),    # Age 71-75
}

# FRS (Full Retirement Sum) annual table
FRS_BY_YEAR = {
    2025: 205800,
    2026: 212000,
    2027: 218000,
    2028: 224000,
    2029: 230000,
    2030: 236000,
}

# BRS (Basic Retirement Sum) = 0.5 * FRS
# ERS (Enhanced Retirement Sum) = 2.0 * FRS (adjustable)

# BHS (MediSave Basic Healthcare Sum) annual table (can be overridden externally)
# More precise BHS annual table
def default_bhs(year: int) -> float:
    """Return BHS value for specified year"""
    bhs_table = {
        2025: 71500,
        2026: 73500,
        2027: 75500,
        2028: 77500,
        2029: 79500,
        2030: 81500,
    }
    
    if year in bhs_table:
        return bhs_table[year]
    
    # For years beyond the table, use linear extrapolation
    if year > 2030:
        return bhs_table[2030] * (1.03 ** (year - 2030))  # 3% annual growth
    elif year < 2025:
        return bhs_table[2025] * (0.97 ** (2025 - year))  # 3% annual growth
    
    return bhs_table[2025]

# ---- BHS helpers ----
def bhs_prevailing(year: int) -> float:
    """BHS prevailing rate with correct values"""
    # 使用正确的BHS值
    bhs_table = {
        2024: 71500,
        2025: 73500,
        2026: 75500,
        2027: 77500,
        2028: 79500,
        2029: 81500,
        2030: 83500,
    }
    
    if year in bhs_table:
        return bhs_table[year]
    
    # 线性外推
    if year > 2030:
        return bhs_table[2030] * (1.03 ** (year - 2030))
    elif year < 2024:
        return bhs_table[2024] * (0.97 ** (2024 - year))
    
    return bhs_table[2024]

def cohort_bhs_at_65(start_year: int, start_age: int) -> float:
    """Calculate BHS at age 65 for a given cohort"""
    # 你模型的"30岁对应年份"为 start_year（比如 2024）；据此算出 65 岁所在年份
    year_turn_65 = start_year + (65 - start_age)
    return bhs_prevailing(year_turn_65)

# OA/SA/MA allocation by age (total = 37% of employer+employee contribution base)
def default_allocation(age: int) -> Tuple[float, float, float]:
    """Return account allocation ratios for specified age (OA_pct, SA_pct, MA_pct)"""
    for (min_age, max_age), allocation in ACCOUNT_ALLOCATION_BY_AGE.items():
        if min_age <= age <= max_age:
            return allocation
    
    # Default to age 35 and below ratio
    return ACCOUNT_ALLOCATION_BY_AGE[(0, 35)]

def get_cpf_rates(age: int) -> Tuple[float, float]:
    """Return CPF rates for specified age (employee_rate, employer_rate)"""
    for (min_age, max_age), rates in CPF_RATES_BY_AGE.items():
        if min_age <= age <= max_age:
            return rates
    
    # Default to age 35 and below rates
    return CPF_RATES_BY_AGE[(0, 35)]

# ==============================
# --------- Data Model ---------
# ==============================

@dataclass
class Inputs:
    start_age: int = 30
    retire_age: int = 65
    end_age: int = 90              # End age for reporting/IRR calculation (can set 95/100 for longevity sensitivity)
    annual_salary: float = 180000
    salary_growth: float = 0.0     # Annual salary growth (nominal), can be enabled
    employee_rate: Optional[float] = None  # If None, use age-related rates
    employer_rate: Optional[float] = None  # If None, use age-related rates
    annual_cpf_ceiling: float = ANNUAL_CPF_CEILING_DEFAULT
    ra_target: str = "FRS"         # "FRS" / "ERS" / "BRS" / "number"
    frs_at_55: Optional[float] = None     # If None, use year table lookup
    ers_multiplier: float = 2.0    # ERS = 2 * FRS (approximate)
    brs_multiplier: float = 0.5    # BRS = 0.5 * FRS
    withdraw_surplus_OA: bool = False  # Whether to treat excess OA at 55 as withdrawal (cash inflow)
    cpf_life_plan: str = "standard"    # "standard" / "basic" / "escalating"
    premium_rate: float = PREMIUM_RATE
    escalating_g: float = ESCALATING_G
    basic_premium_pct: float = BASIC_PREMIUM_PCT
    use_personal_irr: bool = True      # Personal IRR: only employee contributions negative; False = system IRR: both employer+employee negative
    bhs_func: Optional[callable] = None  # If not provided, use default_bhs
    allocation_func: Optional[callable] = None  # If not provided, use default_allocation
    frs_func: Optional[callable] = None  # If not provided, use year table lookup
    
    # New: More precise CPF LIFE parameters
    cpf_life_start_age: int = 65   # CPF LIFE start age
    mortality_table: str = "singapore_2020"  # Mortality table
    
    # New: Investment options
    oa_investment_rate: float = 0.0  # OA investment return rate (optional)
    sa_investment_rate: float = 0.0  # SA investment return rate (optional)

@dataclass
class YearState:
    year: int
    age: int
    salary: float
    base_for_cpf: float
    emp_contrib: float
    empr_contrib: float
    OA: float
    SA: float
    MA: float
    RA: float

@dataclass
class Outputs:
    first_year: Dict
    work_summary: Dict
    retirement_summary: Dict
    end_balances: Dict
    irr_personal: Optional[float]
    irr_system: Optional[float]
    cashflows_monthly: List[float]

# ==============================
# --------- IRR Helpers --------
# ==============================

def irr_newton(cashflows: List[float], guess: float = 0.01, tol: float = 1e-7, max_iter: int = 200) -> Optional[float]:
    # Monthly IRR; returns r (monthly). May fail and return None
    def npv(r: float) -> float:
        try:
            return sum(cf / ((1 + r) ** t) for t, cf in enumerate(cashflows))
        except (ZeroDivisionError, OverflowError):
            return float('inf') if r == -1 else float('-inf')
    
    def dnpv(r: float) -> float:
        try:
            return sum(-t * cf / ((1 + r) ** (t + 1)) for t, cf in enumerate(cashflows))
        except (ZeroDivisionError, OverflowError):
            return float('inf') if r == -1 else float('-inf')
    
    r = guess
    for _ in range(max_iter):
        f, df = npv(r), dnpv(r)
        if abs(df) < 1e-14:
            break
        r_next = r - f / df
        if abs(r_next - r) < tol:
            return r_next
        r = r_next
    return None

def irr_bisect(cashflows: List[float], lo: float = -0.99, hi: float = 1.0, tol: float = 1e-7, max_iter: int = 200) -> Optional[float]:
    # Fallback method: bisection; suitable for general cash flows
    def npv(r: float) -> float:
        try:
            return sum(cf / ((1 + r) ** t) for t, cf in enumerate(cashflows))
        except (ZeroDivisionError, OverflowError):
            return float('inf') if r == -1 else float('-inf')
    
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < tol or (hi - lo) < tol:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return mid

def irr_annual_from_monthly_r(r_month: Optional[float]) -> Optional[float]:
    if r_month is None:
        return None
    return (1 + r_month) ** 12 - 1

# ==============================
# ------ Core CPF Builders -----
# ==============================

def _resolve_allocation(inputs: Inputs, age: int) -> Tuple[float, float, float]:
    f = inputs.allocation_func or default_allocation
    return f(age)

def _bhs(inputs: Inputs, year: int) -> float:
    f = inputs.bhs_func or default_bhs
    return f(year)

def build_ra_target(inputs: Inputs, year: int = 2025) -> float:
    """Build RA target amount"""
    # Get FRS value
    if inputs.frs_at_55 is not None:
        frs_value = inputs.frs_at_55
    elif inputs.frs_func is not None:
        frs_value = inputs.frs_func(year)
    else:
        frs_value = FRS_BY_YEAR.get(year, FRS_BY_YEAR[2025])
    
    if inputs.ra_target == "FRS":
        return frs_value
    elif inputs.ra_target == "ERS":
        return frs_value * inputs.ers_multiplier
    elif inputs.ra_target == "BRS":
        return frs_value * inputs.brs_multiplier
    else:
        try:
            return float(inputs.ra_target)
        except:
            return frs_value

def allocate_year(age: int, year: int, salary: float, inputs: Inputs,
                  OA: float, SA: float, MA: float, RA: float) -> Tuple[float, float, float, float, float, float, float]:
    """Calculate annual CPF allocation including contributions, account allocation, interest calculation"""
    # Calculate annual base and contributions
    base = min(salary, inputs.annual_cpf_ceiling)
    
    # Get age-related rates
    if inputs.employee_rate is not None and inputs.employer_rate is not None:
        emp_rate, empr_rate = inputs.employee_rate, inputs.employer_rate
    else:
        emp_rate, empr_rate = get_cpf_rates(age)
    
    emp = base * emp_rate
    empr = base * empr_rate
    total = emp + empr

    # Get account allocation ratios
    oa_pct, sa_pct, ma_pct = _resolve_allocation(inputs, age)
    add_OA = base * oa_pct
    add_SA = base * sa_pct
    add_MA = base * ma_pct

    # BHS limit + overflow handling
    bhs_limit = _bhs(inputs, year)
    can_MA = max(0.0, bhs_limit - MA)
    to_MA = min(add_MA, can_MA)
    overflow = add_MA - to_MA

    # Overflow allocation: <55 to SA, ≥55 to RA
    add_RA_overflow = 0.0
    if age < 55:
        add_SA += overflow
    else:
        add_RA_overflow = overflow

    # Update account balances
    OA += add_OA
    SA += add_SA
    MA += to_MA
    RA += add_RA_overflow

    # Account interest (year-end) - consider investment options
    oa_rate = OA_RATE + inputs.oa_investment_rate
    sa_rate = SA_RA_RATE + inputs.sa_investment_rate
    
    OA *= (1 + oa_rate)
    SA *= (1 + sa_rate)
    MA *= (1 + MA_RATE)
    RA *= (1 + sa_rate)  # RA uses SA/RA rate

    return base, emp, empr, OA, SA, MA, RA

# ---- 在"当年分配+计息"里套用 BHS 上限 + 溢出 ----
def allocate_year_with_bhs(age: int, year: int, salary: float,
                           OA: float, SA: float, MA: float, RA: float,
                           start_year: int, start_age: int,
                           oa_pct: float, sa_pct: float, ma_pct: float,
                           emp_rate: float, empr_rate: float,
                           annual_cpf_ceiling: float,
                           OA_RATE=0.025, SA_RA_RATE=0.04, MA_RATE=0.04):
    """Calculate annual CPF allocation with BHS limits and overflow handling"""
    base = min(salary, annual_cpf_ceiling)
    emp  = base * emp_rate
    empr = base * empr_rate

    add_OA = base * oa_pct
    add_SA = base * sa_pct
    add_MA = base * ma_pct

    # 1) 计算当年 MA 上限：<65 用当年 BHS；>=65 用 cohort BHS 锁定值
    cap_65 = cohort_bhs_at_65(start_year, start_age)
    cap_now = bhs_prevailing(year) if age < 65 else cap_65

    # 2) 先把当年的 MA 入账限额算出来
    room = max(0.0, cap_now - MA)
    to_MA = min(add_MA, room)
    overflow = add_MA - to_MA

    # 3) 溢出处理：<55 → SA；≥55 → RA
    if age < 55:
        add_SA += overflow
    else:
        RA += overflow

    # 4) 计入当年三账户
    OA += add_OA
    SA += add_SA
    MA += to_MA

    # 5) 年终计息
    OA *= (1 + OA_RATE)
    SA *= (1 + SA_RA_RATE)
    MA *= (1 + MA_RATE)
    RA *= (1 + SA_RA_RATE)

    # 6) 利息可能把 MA 顶破上限 → 再次溢出（官方会把超额转出）
    if MA > cap_now + 1e-9:
        extra = MA - cap_now
        MA = cap_now
        if age < 55:
            SA += extra
        else:
            RA += extra

    return base, emp, empr, OA, SA, MA, RA

def build_ra_at_55(OA: float, SA: float, inputs: Inputs, year: int = 2025) -> Tuple[float, float, float, float]:
    """Establish RA account at age 55, transfer SA and OA funds"""
    target = build_ra_target(inputs, year)
    RA = 0.0

    # Age 55 RA establishment: first transfer SA (SA must be fully transferred to RA)
    move_sa = min(SA, target)
    RA += move_sa
    SA -= move_sa

    # Then transfer OA until target
    need = target - RA
    if need > 0:
        move_oa = min(OA, need)
        RA += move_oa
        OA -= move_oa

    # Whether to withdraw remaining OA (excess)
    cash_out = 0.0
    if inputs.withdraw_surplus_OA and OA > 1e-6:
        cash_out = OA
        OA = 0.0

    return RA, OA, SA, cash_out

# ==============================
# --------- CPF LIFE ----------
# ==============================

def annuity_pmt(PV: float, annual_rate: float, years: float, m: int = 12) -> float:
    r = annual_rate / m
    n = int(max(1, round(years * m)))
    if abs(r) < 1e-12:
        return PV / n
    return PV * (r / (1 - (1 + r) ** (-n)))

def growing_annuity_pmt(PV: float, rate: float, years: float, growth: float, m: int = 12) -> float:
    r, g = rate / m, growth / m
    n = int(max(1, round(years * m)))
    if abs(r - g) < 1e-12:
        return PV / n
    return PV * ((r - g) / (1 - ((1 + g) / (1 + r)) ** n))

def cpf_life_schedule(RA65: float, plan: str, start_age: int, end_age: int,
                      premium_rate: float, escalating_g: float, basic_pct: float,
                      mortality_adjustment: bool = True) -> Tuple[List[float], List[float]]:
    """
    Return (monthly_payouts, bequest_curve); unit: months
    - Standard/Escalating: full amount goes to premium bucket
    - Basic: deduct basic_pct to premium, rest stays in RA until ~90
    Bequest = premium balance + RA balance (excluding OA/MA; can be added at outer level if needed)
    
    New: mortality_adjustment considers mortality adjustment
    """
    months = max(1, (end_age - start_age) * 12)
    premium = 0.0
    ra = 0.0

    if plan in ("standard", "escalating"):
        premium = RA65
    elif plan == "basic":
        premium = RA65 * basic_pct
        ra = RA65 - premium
    else:
        raise ValueError(f"Unknown plan: {plan}. Must be 'standard', 'escalating', or 'basic'")

    payouts: List[float] = []
    bequest: List[float] = []

    # Basic plan has two phases: first use RA until 90, then use premium
    phase1_months = max(0, min(months, (90 - start_age) * 12)) if plan == "basic" else 0
    phase2_months = months - phase1_months

    if plan == "standard":
        # Monthly payment considering mortality adjustment
        if mortality_adjustment:
            m0 = annuity_pmt_with_mortality(premium, premium_rate, start_age, end_age)
        else:
            m0 = annuity_pmt(premium, premium_rate, (end_age - start_age))
            
        for i in range(months):
            # Monthly interest calculation
            premium *= (1 + premium_rate / 12)
            payout = m0
            premium -= payout
            payouts.append(max(0.0, payout))
            bequest.append(max(0.0, premium))
        return payouts, bequest

    if plan == "escalating":
        # Escalating monthly payment considering mortality adjustment
        if mortality_adjustment:
            m0 = growing_annuity_pmt_with_mortality(premium, premium_rate, start_age, end_age, escalating_g)
        else:
            m0 = growing_annuity_pmt(premium, premium_rate, (end_age - start_age), escalating_g)
            
        for i in range(months):
            premium *= (1 + premium_rate / 12)
            yr_idx = i // 12
            payout = m0 * ((1 + escalating_g) ** yr_idx)
            premium -= payout
            payouts.append(max(0.0, payout))
            bequest.append(max(0.0, premium))
        return payouts, bequest

    # plan == "basic"
    # Phase 1: Payment from RA
    m1 = annuity_pmt(ra, SA_RA_RATE, phase1_months / 12) if phase1_months > 0 else 0.0
    for i in range(phase1_months):
        premium *= (1 + premium_rate / 12)
        ra *= (1 + SA_RA_RATE / 12)
        payout = m1
        take = min(ra, payout)
        ra -= take
        if take < payout:
            premium -= (payout - take)  # Extreme error tolerance
        payouts.append(max(0.0, payout))
        bequest.append(max(0.0, premium) + max(0.0, ra))

    # Phase 2: Premium payment only
    if phase2_months > 0:
        m2 = annuity_pmt(premium, premium_rate, phase2_months / 12)
        for _ in range(phase2_months):
            premium *= (1 + premium_rate / 12)
            payout = m2
            premium -= payout
            payouts.append(max(0.0, payout))
            bequest.append(max(0.0, premium))

    return payouts, bequest

def annuity_pmt_with_mortality(PV: float, annual_rate: float, start_age: int, end_age: int) -> float:
    """Annuity payment calculation considering mortality"""
    # Simplified mortality adjustment - should use complete mortality table in practice
    # Here using approximate values from Singapore 2020 mortality table
    monthly_rate = annual_rate / 12
    total_payments = 0.0
    discount_factor = 0.0
    
    for year in range(start_age, end_age):
        for month in range(12):
            # Simplified survival probability (should look up table in practice)
            survival_prob = get_survival_probability(year, month)
            period = year * 12 + month - start_age * 12
            
            total_payments += survival_prob
            discount_factor += survival_prob / ((1 + monthly_rate) ** period)
    
    if discount_factor > 0:
        return PV / discount_factor
    else:
        return PV / ((end_age - start_age) * 12)

def growing_annuity_pmt_with_mortality(PV: float, rate: float, start_age: int, end_age: int, growth: float) -> float:
    """Escalating annuity payment calculation considering mortality"""
    monthly_rate = rate / 12
    monthly_growth = growth / 12
    total_payments = 0.0
    discount_factor = 0.0
    
    for year in range(start_age, end_age):
        for month in range(12):
            survival_prob = get_survival_probability(year, month)
            period = year * 12 + month - start_age * 12
            growth_factor = (1 + monthly_growth) ** period
            
            total_payments += survival_prob * growth_factor
            discount_factor += survival_prob * growth_factor / ((1 + monthly_rate) ** period)
    
    if discount_factor > 0:
        return PV / discount_factor
    else:
        return PV / ((end_age - start_age) * 12)

def get_survival_probability(age: int, month: int) -> float:
    """Get survival probability for specified age and month (simplified version)"""
    # Simplified survival probability calculation - should use complete mortality table in practice
    if age < 65:
        return 1.0
    elif age < 75:
        return 0.99 - (age - 65) * 0.001
    elif age < 85:
        return 0.98 - (age - 75) * 0.01
    else:
        return max(0.5, 0.88 - (age - 85) * 0.02)

# ==============================
# --------- Orchestration ------
# ==============================

def run_cpf(inputs: Inputs) -> Outputs:
    states: List[YearState] = []
    age = inputs.start_age
    salary = inputs.annual_salary
    OA = SA = MA = RA = 0.0
    monthly_employee_cf: List[float] = []  # 雇员月度负现金流
    monthly_system_cf: List[float] = []    # 雇主+雇员月度负现金流

    # Working period (until end of age 54)
    for y in range(inputs.start_age, 55):
        base, emp, empr, OA, SA, MA, RA = allocate_year(age=y, year=year_of_age(y),
                                                         salary=salary, inputs=inputs,
                                                         OA=OA, SA=SA, MA=MA, RA=RA)
        states.append(YearState(year=year_of_age(y), age=y, salary=salary, base_for_cpf=base,
                                emp_contrib=emp, empr_contrib=empr, OA=OA, SA=SA, MA=MA, RA=RA))
        # Cash flow (negative): monthly allocation
        monthly_employee_cf += [-(emp / 12.0)] * 12
        monthly_system_cf += [-((emp + empr) / 12.0)] * 12
        salary *= (1 + inputs.salary_growth)

    # Age 55: first calculate annual contributions/interest, then establish RA (strict: establish RA then annual interest also fine, minimal difference)
    base, emp, empr, OA, SA, MA, RA = allocate_year(age=55, year=year_of_age(55),
                                                     salary=salary, inputs=inputs,
                                                     OA=OA, SA=SA, MA=MA, RA=RA)
    states.append(YearState(year=year_of_age(55), age=55, salary=salary, base_for_cpf=base,
                            emp_contrib=emp, empr_contrib=empr, OA=OA, SA=SA, MA=MA, RA=RA))
    monthly_employee_cf += [-(emp / 12.0)] * 12
    monthly_system_cf += [-((emp + empr) / 12.0)] * 12

    RA, OA, SA, cashout = build_ra_at_55(OA, SA, inputs)
    # Whether to treat excess OA at age 55 as withdrawal (cash inflow)
    if inputs.withdraw_surplus_OA and cashout > 0:
        monthly_employee_cf[-1] += cashout  # Record at year-end (simple handling)

    # Ages 56→64
    for y in range(56, inputs.retire_age):
        base, emp, empr, OA, SA, MA, RA = allocate_year(age=y, year=year_of_age(y),
                                                         salary=salary, inputs=inputs,
                                                         OA=OA, SA=SA, MA=MA, RA=RA)
        states.append(YearState(year=year_of_age(y), age=y, salary=salary, base_for_cpf=base,
                                emp_contrib=emp, empr_contrib=empr, OA=OA, SA=SA, MA=MA, RA=RA))
        monthly_employee_cf += [-(emp / 12.0)] * 12
        monthly_system_cf += [-((emp + empr) / 12.0)] * 12
        salary *= (1 + inputs.salary_growth)

    # Age 65: convert RA balance to CPF LIFE annuity (generate monthly pension sequence)
    RA65 = RA
    payouts, bequest_curve = cpf_life_schedule(RA65=RA65,
                                               plan=inputs.cpf_life_plan,
                                               start_age=inputs.cpf_life_start_age,
                                               end_age=inputs.end_age,
                                               premium_rate=inputs.premium_rate,
                                               escalating_g=inputs.escalating_g,
                                               basic_pct=inputs.basic_premium_pct,
                                               mortality_adjustment=True)
    # Monthly positive cash flow: pension
    monthly_payouts = payouts[:]

    # Terminal bequest (only includes premium/RA bucket; if OA/MA also treated as bequest, add their terminal values)
    # During retirement, OA/MA continue to accrue annual interest (simplified: annual more precise, here monthly allocation to terminal)
    # For simplicity, only compound OA/MA to end_age terminal balance for "bequest terminal value", not add to monthly cash flow
    grow_years = inputs.end_age - inputs.retire_age
    OA_end = OA * ((1 + OA_RATE) ** grow_years)
    MA_end = MA * ((1 + MA_RATE) ** grow_years)
    # Bequest terminal value = bequest_curve[-1] (from premium/RA bucket) + OA_end + MA_end
    terminal_bequest = (bequest_curve[-1] if bequest_curve else 0.0) + OA_end + MA_end

    # Aggregate cash flows (two approaches)
    cf_personal = monthly_employee_cf + monthly_payouts + [terminal_bequest]
    cf_system = monthly_system_cf + monthly_payouts + [terminal_bequest]

    r_month_personal = irr_bisect(cf_personal) or irr_newton(cf_personal)  # First bisection, then Newton
    r_month_system = irr_bisect(cf_system) or irr_newton(cf_system)

    irr_personal = irr_annual_from_monthly_r(r_month_personal)
    irr_system = irr_annual_from_monthly_r(r_month_system)

    # Reporting section
    first = states[0]
    first_year = {
        "Age": first.age,
        "Annual Income": round(first.salary, 2),
        "CPF Contribution Base": first.base_for_cpf,
        "Employee Rate": inputs.employee_rate * 100 if inputs.employee_rate else get_cpf_rates(first.age)[0] * 100,
        "Employer Rate": inputs.employer_rate * 100 if inputs.employer_rate else get_cpf_rates(first.age)[1] * 100,
        "Total Rate": (inputs.employee_rate + inputs.employer_rate) * 100 if inputs.employee_rate and inputs.employer_rate else sum(get_cpf_rates(first.age)) * 100,
        "Annual Contribution": round(first.emp_contrib + first.empr_contrib, 2),
        "Employee Contribution": round(first.emp_contrib, 2),
        "Employer Contribution": round(first.empr_contrib, 2),
        "Account Allocation (Based on Base)": {
            "OA": round(first.base_for_cpf * _resolve_allocation(inputs, first.age)[0], 2),
            "SA": round(first.base_for_cpf * _resolve_allocation(inputs, first.age)[1], 2),
            "MA": round(first.base_for_cpf * _resolve_allocation(inputs, first.age)[2], 2),
        }
    }

    work_summary = {
        "Working Years": inputs.retire_age - inputs.start_age,
        "Age Range": f"{inputs.start_age}-{inputs.retire_age-1} years old",
        "Total Income": round(sum(s.salary for s in states), 2),
        "Total Taxes": "(Taxes removed to your upper module)",
        "Net Take-home Income": "(Taxes removed to your upper module)",
        "Total CPF Contributions": {
            "Employee Contributions": round(sum(s.emp_contrib for s in states), 2),
            "Employer Contributions": round(sum(s.empr_contrib for s in states), 2),
            "Total Contributions": round(sum(s.emp_contrib + s.empr_contrib for s in states), 2),
        },
        "Account Allocation Cumulative (Nominal Input, Excluding Interest Split)": {
            "OA": round(sum(min(s.base_for_cpf, inputs.annual_cpf_ceiling) * _resolve_allocation(inputs, s.age)[0] for s in states), 2),
            "SA": round(sum(min(s.base_for_cpf, inputs.annual_cpf_ceiling) * _resolve_allocation(inputs, s.age)[1] for s in states), 2),
            "MA": round(sum(min(s.base_for_cpf, inputs.annual_cpf_ceiling) * _resolve_allocation(inputs, s.age)[2] for s in states), 2),
        }
    }

    retirement_summary = {
        "Age Range": f"{inputs.retire_age}-{inputs.end_age} years old",
        "Monthly Payout (First Month)": round(monthly_payouts[0], 2),
        "Total Retirement Payout": round(sum(monthly_payouts), 2),
        "Bequest (Terminal)": round(terminal_bequest, 2),
        "Plan": inputs.cpf_life_plan
    }

    end_balances = {
        "OA Balance": round(OA_end, 2),
        "SA Balance": 0.0,  # Usually merged into RA after 55; can accumulate separately if retained
        "MA Balance": round(MA_end, 2),
        "RA/Annuity Pool Balance (Part of Terminal Bequest)": round((bequest_curve[-1] if bequest_curve else 0.0), 2),
        "Total Balance (For Bequest)": round(terminal_bequest, 2)
    }

    return Outputs(
        first_year=first_year,
        work_summary=work_summary,
        retirement_summary=retirement_summary,
        end_balances=end_balances,
        irr_personal=irr_personal,
        irr_system=irr_system,
        cashflows_monthly=cf_personal if inputs.use_personal_irr else cf_system
    )

# Utility function: map age to year (replace baseline with your system's "current year")
def year_of_age(age: int, base_year: int = 2024, base_age: int = 30) -> int:
    return base_year + (age - base_age)

# ==============================
# ----------- Demo -------------
# ==============================

def run_demo():
    """运行演示，展示不同CPF LIFE计划的效果"""
    print("=== CPF LIFE 引擎演示 ===\n")
    
    # 基础参数
    base_params = {
        'start_age': 30,
        'retire_age': 65,
        'end_age': 90,
        'annual_salary': 180000,
        'salary_growth': 0.02,  # 2%年增长
        'annual_cpf_ceiling': 102000,
        'withdraw_surplus_OA': False,
        'premium_rate': 0.035,
        'escalating_g': 0.02,
        'basic_premium_pct': 0.15,
        'use_personal_irr': True,
        'bhs_func': default_bhs,
        'allocation_func': default_allocation,
        'cpf_life_start_age': 65,
    }
    
    # Test different RA targets
    ra_targets = ["FRS", "ERS", "BRS"]
    
    for ra_target in ra_targets:
        print(f"\n--- {ra_target} Plan ---")
        inp = Inputs(**base_params, ra_target=ra_target)
        out = run_cpf(inp)
        
        print(f"Monthly Payout (First Month): ${out.retirement_summary['Monthly Payout (First Month)']:,.2f}")
        print(f"Total Retirement Payout: ${out.retirement_summary['Total Retirement Payout']:,.2f}")
        print(f"Bequest (Terminal): ${out.retirement_summary['Bequest (Terminal)']:,.2f}")
        print(f"IRR (Personal): {out.irr_personal:.2%}" if out.irr_personal else "IRR (Personal): N/A")
        print(f"IRR (System): {out.irr_system:.2%}" if out.irr_system else "IRR (System): N/A")
    
    # Test different CPF LIFE plans
    print("\n\n=== Different CPF LIFE Plans Comparison ===")
    plans = ["standard", "escalating", "basic"]
    
    for plan in plans:
        print(f"\n--- {plan.upper()} Plan ---")
        inp = Inputs(**base_params, ra_target="FRS", cpf_life_plan=plan)
        out = run_cpf(inp)
        
        print(f"Monthly Payout (First Month): ${out.retirement_summary['Monthly Payout (First Month)']:,.2f}")
        print(f"Total Retirement Payout: ${out.retirement_summary['Total Retirement Payout']:,.2f}")
        print(f"Bequest (Terminal): ${out.retirement_summary['Bequest (Terminal)']:,.2f}")
        print(f"IRR (Personal): {out.irr_personal:.2%}" if out.irr_personal else "IRR (Personal): N/A")
    
    # Detailed output for first case
    print("\n\n=== Detailed Output (FRS + Standard) ===")
    inp = Inputs(**base_params, ra_target="FRS", cpf_life_plan="standard")
    out = run_cpf(inp)
    
    print("\n=== First Year ===")
    for key, value in out.first_year.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")
    
    print("\n=== Working Period Summary ===")
    for key, value in out.work_summary.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")
    
    print("\n=== Retirement Period Summary ===")
    for key, value in out.retirement_summary.items():
        print(f"{key}: {value}")
    
    print("\n=== Terminal Balance/Bequest ===")
    for key, value in out.end_balances.items():
        print(f"{key}: {value}")


def run_comparison_analysis():
    """Run comparison analysis showing impact of different parameters on CPF LIFE"""
    print("\n=== CPF LIFE Parameter Sensitivity Analysis ===\n")
    
    # Base case
    base_case = Inputs(
        start_age=30, retire_age=65, end_age=90,
        annual_salary=180000, salary_growth=0.02,
        ra_target="FRS", cpf_life_plan="standard"
    )
    
    # Test different starting ages
    print("--- Impact of Different Starting Ages ---")
    for start_age in [25, 30, 35, 40]:
        inp = Inputs(start_age=start_age, retire_age=65, end_age=90,
                    annual_salary=180000, salary_growth=0.02,
                    ra_target="FRS", cpf_life_plan="standard")
        out = run_cpf(inp)
        irr_str = f"{out.irr_personal:.1%}" if out.irr_personal is not None else "N/A"
        print(f"Starting Age {start_age}: Monthly Payout ${out.retirement_summary['Monthly Payout (First Month)']:,.0f}, IRR {irr_str}")
    
    # Test different salary levels
    print("\n--- Impact of Different Salary Levels ---")
    for salary in [120000, 180000, 240000, 300000]:
        inp = Inputs(start_age=30, retire_age=65, end_age=90,
                    annual_salary=salary, salary_growth=0.02,
                    ra_target="FRS", cpf_life_plan="standard")
        out = run_cpf(inp)
        irr_str = f"{out.irr_personal:.1%}" if out.irr_personal is not None else "N/A"
        print(f"Annual Salary ${salary:,}: Monthly Payout ${out.retirement_summary['Monthly Payout (First Month)']:,.0f}, IRR {irr_str}")
    
    # Test different salary growth rates
    print("\n--- Impact of Different Salary Growth Rates ---")
    for growth in [0.0, 0.02, 0.03, 0.04]:
        inp = Inputs(start_age=30, retire_age=65, end_age=90,
                    annual_salary=180000, salary_growth=growth,
                    ra_target="FRS", cpf_life_plan="standard")
        out = run_cpf(inp)
        irr_str = f"{out.irr_personal:.1%}" if out.irr_personal is not None else "N/A"
        print(f"Salary Growth {growth:.0%}: Monthly Payout ${out.retirement_summary['Monthly Payout (First Month)']:,.0f}, IRR {irr_str}")

if __name__ == "__main__":
    run_demo()
    run_comparison_analysis()