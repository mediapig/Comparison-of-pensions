#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PolicyEngine-compatible tax calculator for Singapore
Based on PolicyEngine Singapore tax rate parameters
"""

from typing import Dict, List, Tuple, Optional
import sys
import os

# Add PolicyEngine imports if available
try:
    from policyengine_sg.model_api import *
    POLICYENGINE_AVAILABLE = True
except ImportError:
    POLICYENGINE_AVAILABLE = False
    from dataclasses import dataclass


class SingaporeTaxBrackets:
    """Singapore personal income tax brackets based on PolicyEngine parameters"""

    # 2024 tax brackets from PolicyEngine Singapore
    BRACKETS_2024 = [
        (0, 0.00),           # 0 - 20,000: 0%
        (20000, 0.02),       # 20,001 - 30,000: 2%
        (30000, 0.035),      # 30,001 - 40,000: 3.5%
        (40000, 0.07),       # 40,001 - 80,000: 7%
        (80000, 0.115),      # 80,001 - 120,000: 11.5%
        (120000, 0.15),      # 120,001 - 160,000: 15%
        (160000, 0.18),      # 160,001 - 200,000: 18%
        (200000, 0.19),      # 200,001 - 240,000: 19%
        (240000, 0.195),     # 240,001 - 280,000: 19.5%
        (280000, 0.20),      # 280,001 - 320,000: 20%
        (320000, 0.22),      # 320,001 - 500,000: 22%
        (500000, 0.24),      # 500,001 - 1,000,000: 24%
        (1000000, 0.245),    # 1,000,001+: 24.5%
    ]

    @staticmethod
    def calculate_progressive_tax(chargeable_income: float) -> float:
        """Calculate progressive tax using Singapore brackets"""
        if chargeable_income <= 0:
            return 0.0

        tax = 0.0
        remaining_income = chargeable_income

        for i, (threshold, rate) in enumerate(SingaporeTaxBrackets.BRACKETS_2024):
            if remaining_income <= 0:
                break

            # Determine the taxable amount for this bracket
            if i == 0:
                # First bracket: 0 to threshold
                bracket_income = min(remaining_income, threshold)
            else:
                # Subsequent brackets: previous threshold to current threshold
                prev_threshold = SingaporeTaxBrackets.BRACKETS_2024[i-1][0]
                bracket_income = min(remaining_income, threshold - prev_threshold)

            # Calculate tax for this bracket
            tax += bracket_income * rate
            remaining_income -= bracket_income

        return round(tax, 2)


class SingaporeTaxReliefs:
    """Singapore tax reliefs and deductions"""

    # 2024 relief amounts
    EARNED_INCOME_RELIEF = 1000
    SPOUSE_RELIEF = 2000
    CHILD_RELIEF = 4000
    PARENT_RELIEF = 1500
    CPF_RELIEF_CAP = 8000
    DONATION_MULTIPLIER = 2.5
    OVERALL_RELIEF_CAP = 80000

    @staticmethod
    def calculate_earned_income_relief(employment_income: float) -> float:
        """Calculate earned income relief"""
        return min(employment_income, SingaporeTaxReliefs.EARNED_INCOME_RELIEF)

    @staticmethod
    def calculate_cpf_relief(cpf_contribution: float) -> float:
        """Calculate CPF relief (capped)"""
        return min(cpf_contribution, SingaporeTaxReliefs.CPF_RELIEF_CAP)

    @staticmethod
    def calculate_donation_relief(donations: float) -> float:
        """Calculate donation relief with multiplier"""
        return donations * SingaporeTaxReliefs.DONATION_MULTIPLIER

    @staticmethod
    def apply_overall_relief_cap(total_reliefs: float) -> float:
        """Apply overall relief cap"""
        return min(total_reliefs, SingaporeTaxReliefs.OVERALL_RELIEF_CAP)


class PolicyEngineTaxCalculator:
    """PolicyEngine-compatible Singapore tax calculator"""

    def __init__(self):
        self.brackets = SingaporeTaxBrackets()
        self.reliefs = SingaporeTaxReliefs()

    def calculate_tax(self,
                     employment_income: float,
                     cpf_contribution: float = 0,
                     other_reliefs: float = 0,
                     donations: float = 0,
                     spouse_income: float = 0,
                     children_count: int = 0,
                     parents_count: int = 0) -> Dict[str, float]:
        """
        Calculate Singapore personal income tax

        Args:
            employment_income: Annual employment income
            cpf_contribution: Annual CPF contribution
            other_reliefs: Other tax reliefs
            donations: Approved donations
            spouse_income: Spouse's income (for relief calculation)
            children_count: Number of children
            parents_count: Number of parents/dependents

        Returns:
            Dictionary with tax calculation results
        """

        # Calculate reliefs
        earned_income_relief = self.reliefs.calculate_earned_income_relief(employment_income)
        cpf_relief = self.reliefs.calculate_cpf_relief(cpf_contribution)
        donation_relief = self.reliefs.calculate_donation_relief(donations)

        # Family reliefs
        spouse_relief = SingaporeTaxReliefs.SPOUSE_RELIEF if spouse_income == 0 else 0
        child_relief = children_count * SingaporeTaxReliefs.CHILD_RELIEF
        parent_relief = parents_count * SingaporeTaxReliefs.PARENT_RELIEF

        # Total reliefs
        total_reliefs = (earned_income_relief + cpf_relief + donation_relief +
                        spouse_relief + child_relief + parent_relief + other_reliefs)

        # Apply overall relief cap
        total_reliefs = self.reliefs.apply_overall_relief_cap(total_reliefs)

        # Calculate chargeable income
        chargeable_income = max(0, employment_income - total_reliefs)

        # Calculate tax
        tax_payable = self.brackets.calculate_progressive_tax(chargeable_income)

        # Calculate effective tax rate
        effective_rate = (tax_payable / employment_income) if employment_income > 0 else 0

        # Calculate net income
        net_income = employment_income - tax_payable

        return {
            'employment_income': employment_income,
            'total_reliefs': total_reliefs,
            'chargeable_income': chargeable_income,
            'tax_payable': tax_payable,
            'effective_rate': effective_rate,
            'net_income': net_income,
            'relief_breakdown': {
                'earned_income_relief': earned_income_relief,
                'cpf_relief': cpf_relief,
                'donation_relief': donation_relief,
                'spouse_relief': spouse_relief,
                'child_relief': child_relief,
                'parent_relief': parent_relief,
                'other_reliefs': other_reliefs
            }
        }

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """Get tax brackets information"""
        brackets_info = []
        for i, (threshold, rate) in enumerate(SingaporeTaxBrackets.BRACKETS_2024):
            if i == 0:
                lower_bound = 0
            else:
                lower_bound = SingaporeTaxBrackets.BRACKETS_2024[i-1][0] + 1

            brackets_info.append({
                'lower_bound': lower_bound,
                'upper_bound': threshold if threshold < float('inf') else None,
                'rate': rate,
                'rate_percentage': rate * 100
            })

        return brackets_info

    def calculate_marginal_tax_rate(self, income: float) -> float:
        """Calculate marginal tax rate for given income"""
        for threshold, rate in reversed(SingaporeTaxBrackets.BRACKETS_2024):
            if income > threshold:
                return rate
        return 0.0

    def calculate_effective_tax_rate(self, income: float, reliefs: float = 0) -> float:
        """Calculate effective tax rate for given income and reliefs"""
        chargeable_income = max(0, income - reliefs)
        tax = self.brackets.calculate_progressive_tax(chargeable_income)
        return (tax / income) if income > 0 else 0


# PolicyEngine Variable Classes (if PolicyEngine is available)
if POLICYENGINE_AVAILABLE:

    class earned_income_relief(Variable):
        """Earned income relief"""
        value_type = float
        entity = Person
        label = "Earned income relief"
        unit = SGD
        definition_period = YEAR
        reference = "https://www.iras.gov.sg/taxes/individual-income-tax/reliefs-rebates-and-deductions/reliefs"

        def formula(person, period, parameters):
            employment_income = person("employment_income", period)
            return min(employment_income, 1000)  # $1,000 relief

    class cpf_relief(Variable):
        """CPF relief"""
        value_type = float
        entity = Person
        label = "CPF relief"
        unit = SGD
        definition_period = YEAR
        reference = "https://www.iras.gov.sg/taxes/individual-income-tax/reliefs-rebates-and-deductions/reliefs"

        def formula(person, period, parameters):
            cpf_contribution = person("cpf_total_contribution", period) * 12  # Convert monthly to annual
            return min(cpf_contribution, 8000)  # $8,000 cap

    class total_reliefs(Variable):
        """Total tax reliefs"""
        value_type = float
        entity = Person
        label = "Total tax reliefs"
        unit = SGD
        definition_period = YEAR
        adds = ["earned_income_relief", "cpf_relief"]

    class chargeable_income(Variable):
        """Chargeable income for tax calculation"""
        value_type = float
        entity = Person
        label = "Chargeable income"
        unit = SGD
        definition_period = YEAR
        reference = "https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/chargeable-income"

        def formula(person, period, parameters):
            employment_income = person("employment_income", period)
            total_reliefs = person("total_reliefs", period)
            return max_(0, employment_income - total_reliefs)

    class income_tax(Variable):
        """Personal income tax"""
        value_type = float
        entity = Person
        label = "Personal income tax"
        unit = SGD
        definition_period = YEAR
        reference = "https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/tax-rates"

        def formula(person, period, parameters):
            chargeable_income = person("chargeable_income", period)

            # Progressive tax calculation
            tax = 0.0
            remaining_income = chargeable_income

            brackets = [
                (0, 0.00),
                (20000, 0.02),
                (30000, 0.035),
                (40000, 0.07),
                (80000, 0.115),
                (120000, 0.15),
                (160000, 0.18),
                (200000, 0.19),
                (240000, 0.195),
                (280000, 0.20),
                (320000, 0.22),
                (500000, 0.24),
                (1000000, 0.245),
            ]

            for i, (threshold, rate) in enumerate(brackets):
                if remaining_income <= 0:
                    break

                if i == 0:
                    bracket_income = min_(remaining_income, threshold)
                else:
                    prev_threshold = brackets[i-1][0]
                    bracket_income = min_(remaining_income, threshold - prev_threshold)

                tax += bracket_income * rate
                remaining_income -= bracket_income

            return tax

    class net_income(Variable):
        """Net income after tax"""
        value_type = float
        entity = Person
        label = "Net income"
        unit = SGD
        definition_period = YEAR

        def formula(person, period, parameters):
            employment_income = person("employment_income", period)
            income_tax = person("income_tax", period)
            return employment_income - income_tax

    class effective_tax_rate(Variable):
        """Effective tax rate"""
        value_type = float
        entity = Person
        label = "Effective tax rate"
        unit = "/1"
        definition_period = YEAR

        def formula(person, period, parameters):
            employment_income = person("employment_income", period)
            income_tax = person("income_tax", period)
            return where(employment_income > 0, income_tax / employment_income, 0)
