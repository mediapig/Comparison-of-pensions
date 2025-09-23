"""
CPF ROI Model - Improved Version
Singapore Central Provident Fund Return on Investment Calculator

This module provides a comprehensive simulation of CPF contributions and payouts,
calculating IRR and NPV for retirement planning analysis.
"""

import math
from typing import Dict, List, Tuple, Optional


def cpf_roi_model(params: Dict) -> Dict:
    """
    Calculate CPF ROI based on contribution and payout simulation.
    
    Args:
        params: Dictionary containing simulation parameters including:
            - start_age: Starting age for contributions
            - start_annual_salary: Initial annual salary
            - annual_salary_ceiling: CPF salary ceiling
            - cpf_annual_limit: Annual CPF contribution limit
            - BHS: Basic Healthcare Sum limit
            - FRS: Full Retirement Sum
            - RA_target_multiplier: Multiplier for RA target
            - retire_age: Retirement age
            - stop_age: Age when payouts stop
            - rate_by_age: Function returning (employee_rate, employer_rate) by age
            - ratio_by_age: Function returning (OA_ratio, SA_ratio, MA_ratio) by age
            - rate_OA: OA interest rate
            - rate_SA_RA: SA/RA interest rate
            - rate_MA: MA interest rate
            - annual_salary_growth: Annual salary growth rate
            - use_official_payout: Whether to use official payout amount
            - official_monthly_payout: Official monthly payout if applicable
            - annual_ra_credit_rate: Annual RA credit rate for annuity calculation
            - annuity_indexation: "level" or "growing" annuity type
            - annual_inflation: Annual inflation rate for growing annuity
    
    Returns:
        Dictionary containing IRR, NPV, and cashflows
    """
    # Validate required parameters
    _validate_params(params)
    
    # Initialize accounts
    OA, SA, MA, RA = 0.0, 0.0, 0.0, 0.0
    cashflows = []  # Negative = contributions (outflow), Positive = payouts (inflow)
    
    age = params["start_age"]
    salary = params["start_annual_salary"]
    
    # Phase A: Working years simulation
    while age < 55:
        # Calculate CPF contribution base (considering salary ceiling)
        base = min(salary, params["annual_salary_ceiling"])
        
        # Get contribution rates for current age
        emp_rate, er_rate = params["rate_by_age"](age)
        total_rate = emp_rate + er_rate
        
        # Calculate total CPF contribution (subject to annual limit)
        cpf_year = min(base * total_rate, params["cpf_annual_limit"])
        
        # Get allocation ratios for current age
        share_OA, share_SA, share_MA = params["ratio_by_age"](age)
        
        to_OA = cpf_year * share_OA
        to_SA = cpf_year * share_SA
        to_MA = cpf_year * share_MA
        
        # Handle MA overflow to SA then OA (BHS limit)
        room_MA = max(0.0, params["BHS"] - MA)
        put_MA = min(to_MA, room_MA)
        overflow_from_MA = to_MA - put_MA
        
        put_SA = to_SA + overflow_from_MA
        put_OA = to_OA
        
        # Update account balances
        OA += put_OA
        SA += put_SA
        MA += put_MA
        
        # Apply interest (compound annually)
        OA *= (1 + params["rate_OA"])
        SA *= (1 + params["rate_SA_RA"])
        MA *= (1 + params["rate_MA"])
        
        # Record employee contribution as negative cashflow (monthly)
        employee_contribution = min(base * emp_rate, params["cpf_annual_limit"])
        monthly_contribution = employee_contribution / 12.0
        for month in range(12):
            cashflows.append(-monthly_contribution)
        
        # Move to next year
        age += 1
        salary *= (1 + params["annual_salary_growth"])
    
    # Age 55: Establish RA
    target_RA = params["FRS"] * params["RA_target_multiplier"]
    transferable = OA + SA
    moved_to_RA = min(target_RA, transferable)
    
    # Transfer from SA first, then OA
    move_from_SA = min(SA, moved_to_RA)
    SA -= move_from_SA
    rest = moved_to_RA - move_from_SA
    move_from_OA = min(OA, rest)
    OA -= move_from_OA
    RA += moved_to_RA
    
    # Phase B: Pre-retirement years (55 to retirement age)
    while age < params["retire_age"]:
        OA *= (1 + params["rate_OA"])
        SA *= (1 + params["rate_SA_RA"])
        MA *= (1 + params["rate_MA"])
        RA *= (1 + params["rate_SA_RA"])
        age += 1
    
    # Phase C: Retirement payouts
    months = (params["stop_age"] - params["retire_age"]) * 12
    
    if params["use_official_payout"]:
        monthly_payout = params["official_monthly_payout"]
    else:
        monthly_payout = _calculate_annuity_payment(RA, months, params)
    
    # Generate retirement cashflows
    for i in range(months):
        if params["annuity_indexation"] == "level" or params["use_official_payout"]:
            cashflows.append(monthly_payout)
        else:
            # Growing annuity
            g = params["annual_inflation"] / 12.0
            cashflows.append(monthly_payout * (1 + g) ** i)
    
    # Calculate returns
    irr = compute_irr(cashflows)
    npv = compute_npv(cashflows, discount=0.03)
    
    return {
        "IRR": irr,
        "NPV@3%": npv,
        "cashflows": cashflows,
        "final_balances": {"OA": OA, "SA": SA, "MA": MA, "RA": RA}
    }


def _validate_params(params: Dict) -> None:
    """Validate required parameters."""
    required_params = [
        "start_age", "start_annual_salary", "annual_salary_ceiling",
        "cpf_annual_limit", "BHS", "FRS", "RA_target_multiplier",
        "retire_age", "stop_age", "rate_by_age", "ratio_by_age",
        "rate_OA", "rate_SA_RA", "rate_MA", "annual_salary_growth",
        "use_official_payout", "annual_ra_credit_rate", "annuity_indexation"
    ]
    
    for param in required_params:
        if param not in params:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Additional validation
    if params["start_age"] >= 55:
        raise ValueError("Start age must be less than 55")
    if params["retire_age"] < 55:
        raise ValueError("Retirement age must be at least 55")
    if params["stop_age"] <= params["retire_age"]:
        raise ValueError("Stop age must be greater than retirement age")


def _calculate_annuity_payment(present_value: float, months: int, params: Dict) -> float:
    """Calculate monthly annuity payment."""
    r = params["annual_ra_credit_rate"] / 12.0  # Monthly rate
    
    if params["annuity_indexation"] == "level":
        # Level annuity: PMT = PV * r / (1 - (1+r)^-n)
        if r == 0:
            return present_value / months
        return present_value * (r / (1 - (1 + r) ** (-months)))
    else:
        # Growing annuity: PMT0 = PV * (r - g) / (1 - ((1+g)/(1+r))^n)
        g = params["annual_inflation"] / 12.0
        if abs(r - g) < 1e-12:
            return present_value / months
        else:
            return present_value * ((r - g) / (1 - ((1 + g) / (1 + r)) ** months))


def compute_npv(cashflows: List[float], discount: float) -> float:
    """
    Calculate Net Present Value of cashflows.
    
    Args:
        cashflows: List of monthly cashflows (negative = outflow, positive = inflow)
        discount: Annual discount rate
    
    Returns:
        NPV in present value terms
    """
    monthly_discount = discount / 12.0
    npv = 0.0
    
    for t, cf in enumerate(cashflows):
        npv += cf / ((1 + monthly_discount) ** t)
    
    return npv


def compute_irr(cashflows: List[float], guess: float = 0.03, tolerance: float = 1e-6) -> float:
    """
    Calculate Internal Rate of Return using Newton-Raphson method.
    
    Args:
        cashflows: List of monthly cashflows
        guess: Initial guess for annual IRR
        tolerance: Convergence tolerance
    
    Returns:
        Annual IRR
    """
    if not cashflows:
        return 0.0
    
    # Check if IRR exists (at least one positive and one negative cashflow)
    has_positive = any(cf > 0 for cf in cashflows)
    has_negative = any(cf < 0 for cf in cashflows)
    
    if not (has_positive and has_negative):
        return 0.0
    
    # Newton-Raphson method - convert annual guess to monthly
    monthly_irr = (1 + guess) ** (1/12) - 1
    
    for _ in range(100):  # Maximum iterations
        npv = 0.0
        npv_derivative = 0.0
        
        for t, cf in enumerate(cashflows):
            discount_factor = (1 + monthly_irr) ** t
            npv += cf / discount_factor
            npv_derivative -= t * cf / ((1 + monthly_irr) ** (t + 1))
        
        if abs(npv) < tolerance:
            break
            
        if abs(npv_derivative) < 1e-12:
            # Fallback to bisection method
            return _compute_irr_bisection(cashflows)
        
        monthly_irr = monthly_irr - npv / npv_derivative
        
        # Ensure reasonable bounds
        monthly_irr = max(-0.99, min(0.5, monthly_irr))
    
    # Convert monthly IRR to annual IRR
    annual_irr = (1 + monthly_irr) ** 12 - 1
    return annual_irr


def _compute_irr_bisection(cashflows: List[float]) -> float:
    """Fallback IRR calculation using bisection method."""
    lo, hi = -0.99, 0.5
    
    for _ in range(100):
        mid = (lo + hi) / 2
        npv_mid = compute_npv(cashflows, discount=mid * 12)  # Convert to annual rate
        
        if abs(npv_mid) < 1e-6:
            break
            
        if npv_mid > 0:
            lo = mid
        else:
            hi = mid
    
    monthly_irr = (lo + hi) / 2
    annual_irr = (1 + monthly_irr) ** 12 - 1
    return annual_irr


# Example usage and parameter setup
def create_sample_params() -> Dict:
    """Create sample parameters for CPF simulation."""
    
    def rate_by_age(age):
        """Age-based contribution rates (employee, employer)."""
        if age <= 35:
            return (0.20, 0.17)
        elif age <= 45:
            return (0.20, 0.17)
        elif age <= 50:
            return (0.20, 0.13)
        elif age <= 55:
            return (0.20, 0.13)
        elif age <= 60:
            return (0.125, 0.075)
        else:
            return (0.05, 0.05)
    
    def ratio_by_age(age):
        """Age-based allocation ratios (OA, SA, MA)."""
        if age <= 35:
            return (0.23, 0.06, 0.08)
        elif age <= 45:
            return (0.23, 0.06, 0.08)
        elif age <= 50:
            return (0.23, 0.06, 0.08)
        elif age <= 55:
            return (0.23, 0.06, 0.08)
        else:
            return (0.12, 0.00, 0.08)  # Post-55 allocation
    
    return {
        "start_age": 25,
        "start_annual_salary": 60000,
        "annual_salary_ceiling": 102000,
        "cpf_annual_limit": 37740,
        "BHS": 68000,
        "FRS": 198800,
        "RA_target_multiplier": 1.0,
        "retire_age": 65,
        "stop_age": 90,
        "rate_by_age": rate_by_age,
        "ratio_by_age": ratio_by_age,
        "rate_OA": 0.025,
        "rate_SA_RA": 0.04,
        "rate_MA": 0.04,
        "annual_salary_growth": 0.03,
        "use_official_payout": False,
        "annual_ra_credit_rate": 0.04,
        "annuity_indexation": "level",
        "annual_inflation": 0.02
    }


if __name__ == "__main__":
    # Example usage
    params = create_sample_params()
    result = cpf_roi_model(params)
    
    print("CPF ROI Analysis Results:")
    print(f"IRR: {result['IRR']:.2%}")
    print(f"NPV @ 3%: ${result['NPV@3%']:,.2f}")
    print(f"Final Balances: {result['final_balances']}")