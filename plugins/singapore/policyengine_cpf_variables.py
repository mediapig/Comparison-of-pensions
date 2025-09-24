#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PolicyEngine-compatible CPF calculation variables for Singapore
Based on PolicyEngine Singapore structure and standards
"""

from typing import Dict, Tuple
import sys
import os

# Add PolicyEngine imports if available
try:
    from policyengine_sg.model_api import *
    POLICYENGINE_AVAILABLE = True
except ImportError:
    POLICYENGINE_AVAILABLE = False
    # Fallback imports for standalone usage
    from dataclasses import dataclass
    from typing import Optional


class CPFContributionRates:
    """CPF contribution rates based on PolicyEngine Singapore parameters"""

    @staticmethod
    def get_employee_rate(age: int) -> float:
        """Get employee CPF contribution rate by age"""
        if age <= 55:
            return 0.20  # 20%
        elif age <= 60:
            return 0.13  # 13%
        elif age <= 65:
            return 0.075  # 7.5%
        else:
            return 0.05  # 5%

    @staticmethod
    def get_employer_rate(age: int) -> float:
        """Get employer CPF contribution rate by age"""
        if age <= 55:
            return 0.17  # 17%
        elif age <= 60:
            return 0.13  # 13%
        elif age <= 65:
            return 0.09  # 9%
        else:
            return 0.075  # 7.5%

    @staticmethod
    def get_account_allocation(age: int) -> Dict[str, float]:
        """Get CPF account allocation percentages by age"""
        if age <= 35:
            return {'oa': 0.62, 'sa': 0.16, 'ma': 0.22}
        elif age <= 45:
            return {'oa': 0.62, 'sa': 0.16, 'ma': 0.22}
        elif age <= 50:
            return {'oa': 0.62, 'sa': 0.16, 'ma': 0.22}
        elif age <= 55:
            return {'oa': 0.62, 'sa': 0.16, 'ma': 0.22}
        elif age <= 60:
            return {'oa': 0.21, 'sa': 0.07, 'ma': 0.72}
        elif age <= 65:
            return {'oa': 0.12, 'sa': 0.04, 'ma': 0.84}
        else:
            return {'oa': 0.01, 'sa': 0.01, 'ma': 0.98}


class CPFLimits:
    """CPF limits and thresholds"""

    # 2024 official limits
    ORDINARY_WAGE_CEILING = 8000  # Monthly
    ADDITIONAL_WAGE_CEILING = 102000  # Annual
    BHS_2024 = 71500  # Basic Healthcare Sum
    FRS_2024 = 205800  # Full Retirement Sum

    @staticmethod
    def get_contribution_base(monthly_wage: float, annual_bonus: float = 0) -> Tuple[float, float]:
        """Calculate CPF contribution base for OW and AW"""
        # Ordinary Wage (monthly salary)
        ow_base = min(monthly_wage, CPFLimits.ORDINARY_WAGE_CEILING)

        # Additional Wage (bonuses, etc.)
        aw_base = min(annual_bonus, CPFLimits.ADDITIONAL_WAGE_CEILING)

        return ow_base, aw_base

    @staticmethod
    def get_bhs_limit(year: int) -> float:
        """Get BHS limit for given year"""
        years_from_2024 = year - 2024
        return CPFLimits.BHS_2024 * (1.03 ** years_from_2024)  # 3% annual increase

    @staticmethod
    def get_frs_limit(year: int) -> float:
        """Get FRS limit for given year"""
        years_from_2024 = year - 2024
        return CPFLimits.FRS_2024 * (1.03 ** years_from_2024)  # 3% annual increase


class CPFInterestRates:
    """CPF interest rates"""

    OA_RATE = 0.025  # 2.5% per annum
    SA_RATE = 0.04   # 4% per annum
    MA_RATE = 0.04   # 4% per annum
    RA_RATE = 0.04   # 4% per annum
    EXTRA_INTEREST_RATE = 0.01  # 1% extra on first $60k
    EXTRA_INTEREST_THRESHOLD = 60000
    OA_EXTRA_INTEREST_LIMIT = 20000  # OA only gets extra interest on first $20k


class PolicyEngineCPFCalculator:
    """PolicyEngine-compatible CPF calculator"""

    def __init__(self):
        self.rates = CPFContributionRates()
        self.limits = CPFLimits()
        self.interest_rates = CPFInterestRates()

    def calculate_monthly_contribution(self, monthly_wage: float, age: int) -> Dict[str, float]:
        """Calculate monthly CPF contribution"""
        # Get contribution rates
        ee_rate = self.rates.get_employee_rate(age)
        er_rate = self.rates.get_employer_rate(age)

        # Calculate contribution base
        ow_base, _ = self.limits.get_contribution_base(monthly_wage)

        # Calculate contributions
        ee_contrib = ow_base * ee_rate
        er_contrib = ow_base * er_rate
        total_contrib = ee_contrib + er_contrib

        # Get account allocation
        allocation = self.rates.get_account_allocation(age)

        # Allocate to accounts
        oa_contrib = total_contrib * allocation['oa']
        sa_contrib = total_contrib * allocation['sa']
        ma_contrib = total_contrib * allocation['ma']

        return {
            'employee_contribution': ee_contrib,
            'employer_contribution': er_contrib,
            'total_contribution': total_contrib,
            'oa_contribution': oa_contrib,
            'sa_contribution': sa_contrib,
            'ma_contribution': ma_contrib
        }

    def calculate_interest(self, balances: Dict[str, float]) -> Dict[str, float]:
        """Calculate CPF interest with extra interest logic"""
        # Basic interest
        oa_interest = balances.get('oa', 0) * self.interest_rates.OA_RATE
        sa_interest = balances.get('sa', 0) * self.interest_rates.SA_RATE
        ma_interest = balances.get('ma', 0) * self.interest_rates.MA_RATE
        ra_interest = balances.get('ra', 0) * self.interest_rates.RA_RATE

        # Calculate extra interest
        total_balance = sum(balances.values())
        if total_balance > 0:
            extra_pool = min(total_balance, self.interest_rates.EXTRA_INTEREST_THRESHOLD) * self.interest_rates.EXTRA_INTEREST_RATE

            # Eligible balances for extra interest
            oa_eligible = min(balances.get('oa', 0), self.interest_rates.OA_EXTRA_INTEREST_LIMIT)
            sa_eligible = balances.get('sa', 0)
            ma_eligible = balances.get('ma', 0)
            ra_eligible = balances.get('ra', 0)

            total_eligible = oa_eligible + sa_eligible + ma_eligible + ra_eligible

            if total_eligible > 0:
                oa_extra = extra_pool * (oa_eligible / total_eligible)
                sa_extra = extra_pool * (sa_eligible / total_eligible)
                ma_extra = extra_pool * (ma_eligible / total_eligible)
                ra_extra = extra_pool * (ra_eligible / total_eligible)

                oa_interest += oa_extra
                sa_interest += sa_extra
                ma_interest += ma_extra
                ra_interest += ra_extra

        return {
            'oa_interest': oa_interest,
            'sa_interest': sa_interest,
            'ma_interest': ma_interest,
            'ra_interest': ra_interest
        }

    def handle_bhs_overflow(self, ma_balance: float, ma_contribution: float, year: int) -> Tuple[float, float]:
        """Handle MA BHS overflow - excess goes to SA"""
        bhs_limit = self.limits.get_bhs_limit(year)

        # Calculate how much can go to MA
        ma_room = max(0, bhs_limit - ma_balance)
        to_ma = min(ma_contribution, ma_room)
        overflow = ma_contribution - to_ma

        return to_ma, overflow

    def establish_ra_at_55(self, oa_balance: float, sa_balance: float, year: int) -> Tuple[float, float, float]:
        """Establish RA at age 55 using SA first, then OA"""
        frs_target = self.limits.get_frs_limit(year)

        ra_balance = 0.0
        need = max(0, frs_target - ra_balance)

        # Use SA first
        take_sa = min(sa_balance, need)
        sa_balance -= take_sa
        ra_balance += take_sa
        need -= take_sa

        # Use OA if needed
        take_oa = min(oa_balance, need)
        oa_balance -= take_oa
        ra_balance += take_oa

        return ra_balance, oa_balance, sa_balance


# PolicyEngine Variable Classes (if PolicyEngine is available)
if POLICYENGINE_AVAILABLE:

    class cpf_employee_contribution(Variable):
        """Employee CPF contribution"""
        value_type = float
        entity = Person
        label = "Employee CPF contribution"
        unit = SGD
        definition_period = MONTH
        reference = "https://www.cpf.gov.sg/employer/employer-obligations/cpf-contributions/cpf-contribution-rates"

        def formula(person, period, parameters):
            age = person("age", period)
            employment_income = person("employment_income", period)
            monthly_income = employment_income / 12

            # Get employee rate
            if age <= 55:
                rate = 0.20
            elif age <= 60:
                rate = 0.13
            elif age <= 65:
                rate = 0.075
            else:
                rate = 0.05

            # Apply OW ceiling
            cpf_base = min(monthly_income, 8000)
            return cpf_base * rate

    class cpf_employer_contribution(Variable):
        """Employer CPF contribution"""
        value_type = float
        entity = Person
        label = "Employer CPF contribution"
        unit = SGD
        definition_period = MONTH
        reference = "https://www.cpf.gov.sg/employer/employer-obligations/cpf-contributions/cpf-contribution-rates"

        def formula(person, period, parameters):
            age = person("age", period)
            employment_income = person("employment_income", period)
            monthly_income = employment_income / 12

            # Get employer rate
            if age <= 55:
                rate = 0.17
            elif age <= 60:
                rate = 0.13
            elif age <= 65:
                rate = 0.09
            else:
                rate = 0.075

            # Apply OW ceiling
            cpf_base = min(monthly_income, 8000)
            return cpf_base * rate

    class cpf_total_contribution(Variable):
        """Total CPF contribution (employee + employer)"""
        value_type = float
        entity = Person
        label = "Total CPF contribution"
        unit = SGD
        definition_period = MONTH
        adds = ["cpf_employee_contribution", "cpf_employer_contribution"]

    class cpf_oa_contribution(Variable):
        """CPF Ordinary Account contribution"""
        value_type = float
        entity = Person
        label = "CPF OA contribution"
        unit = SGD
        definition_period = MONTH

        def formula(person, period, parameters):
            age = person("age", period)
            total_contrib = person("cpf_total_contribution", period)

            # Get allocation percentage
            if age <= 55:
                oa_allocation = 0.62
            elif age <= 60:
                oa_allocation = 0.21
            elif age <= 65:
                oa_allocation = 0.12
            else:
                oa_allocation = 0.01

            return total_contrib * oa_allocation

    class cpf_sa_contribution(Variable):
        """CPF Special Account contribution"""
        value_type = float
        entity = Person
        label = "CPF SA contribution"
        unit = SGD
        definition_period = MONTH

        def formula(person, period, parameters):
            age = person("age", period)
            total_contrib = person("cpf_total_contribution", period)

            # Get allocation percentage
            if age <= 55:
                sa_allocation = 0.16
            elif age <= 60:
                sa_allocation = 0.07
            elif age <= 65:
                sa_allocation = 0.04
            else:
                sa_allocation = 0.01

            return total_contrib * sa_allocation

    class cpf_ma_contribution(Variable):
        """CPF Medisave Account contribution"""
        value_type = float
        entity = Person
        label = "CPF MA contribution"
        unit = SGD
        definition_period = MONTH

        def formula(person, period, parameters):
            age = person("age", period)
            total_contrib = person("cpf_total_contribution", period)

            # Get allocation percentage
            if age <= 55:
                ma_allocation = 0.22
            elif age <= 60:
                ma_allocation = 0.72
            elif age <= 65:
                ma_allocation = 0.84
            else:
                ma_allocation = 0.98

            return total_contrib * ma_allocation
