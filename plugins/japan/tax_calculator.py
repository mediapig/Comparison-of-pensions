#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本个人所得税计算器
"""

from typing import Dict, List

class JapanTaxCalculator:
    """日本个人所得税计算器"""

    def __init__(self):
        self.country_code = 'JP'
        self.country_name = '日本'
        self.currency = 'JPY'

    def get_tax_brackets(self) -> List[Dict]:
        """获取日本个税税率表 (2024年)"""
        return [
            {'min': 0, 'max': 1950000, 'rate': 0.05},
            {'min': 1950000, 'max': 3300000, 'rate': 0.10},
            {'min': 3300000, 'max': 6950000, 'rate': 0.20},
            {'min': 6950000, 'max': 9000000, 'rate': 0.23},
            {'min': 9000000, 'max': 18000000, 'rate': 0.33},
            {'min': 18000000, 'max': 40000000, 'rate': 0.40},
            {'min': 40000000, 'max': float('inf'), 'rate': 0.45}
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None, social_security_contribution: float = 0) -> Dict:
        """计算日本个人所得税"""
        if deductions is None:
            deductions = {}

        # 1. 工资所得控除（給与所得控除）
        salary_deduction = self._calculate_salary_deduction(annual_income)

        # 2. 基础控除（基礎控除）
        basic_deduction = self._calculate_basic_deduction(annual_income)

        # 3. 社会保险料控除（年金+健保+雇保合计）
        social_security_deduction = social_security_contribution

        # 总扣除额
        total_deductions = salary_deduction + basic_deduction + social_security_deduction + sum(deductions.values())

        # 应纳税所得额
        taxable_income = max(0, annual_income - total_deductions)

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'basic_deduction': basic_deduction,
                    'social_security_deduction': social_security_deduction,
                    'other_deductions': sum(deductions.values()),
                    'tax_brackets': []
                }
            }

        # 计算个税
        tax_brackets = self.get_tax_brackets()
        total_tax = 0
        bracket_details = []

        for bracket in tax_brackets:
            if taxable_income > bracket['min']:
                taxable_in_bracket = min(taxable_income - bracket['min'],
                                       bracket['max'] - bracket['min'])
                if taxable_in_bracket > 0:
                    bracket_tax = taxable_in_bracket * bracket['rate']
                    total_tax += bracket_tax

                    bracket_details.append({
                        'bracket': f"¥{bracket['min']:,.0f}-{bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': taxable_in_bracket,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': total_deductions,
            'breakdown': {
                'salary_deduction': salary_deduction,
                'basic_deduction': basic_deduction,
                'social_security_deduction': social_security_deduction,
                'other_deductions': sum(deductions.values()),
                'tax_brackets': bracket_details
            }
        }

    def calculate_effective_tax_rate(self, annual_income: float, deductions: Dict = None) -> float:
        """计算有效税率"""
        tax_result = self.calculate_income_tax(annual_income, deductions)
        total_tax = tax_result.get('total_tax', 0)
        return (total_tax / annual_income * 100) if annual_income > 0 else 0

    def calculate_net_income(self, annual_income: float, deductions: Dict = None) -> float:
        """计算税后净收入"""
        tax_result = self.calculate_income_tax(annual_income, deductions)
        total_tax = tax_result.get('total_tax', 0)
        return annual_income - total_tax

    def _calculate_salary_deduction(self, annual_income: float) -> float:
        """
        计算工资所得控除（給与所得控除）
        按照日本税法规定的梯度计算
        """
        if annual_income <= 1800000:
            # ≤1.8M：40%−100k
            return annual_income * 0.4 - 100000
        elif annual_income <= 3600000:
            # ≤3.6M：30%+80k
            return annual_income * 0.3 + 80000
        elif annual_income <= 6600000:
            # ≤6.6M：20%+440k（5M 案例 → 1,440,000）
            return annual_income * 0.2 + 440000
        elif annual_income <= 8500000:
            # ≤8.5M：10%+1,100k
            return annual_income * 0.1 + 1100000
        else:
            # ＞8.5M：1,950,000（封顶）（20M 案例 → 1,950,000）
            return 1950000

    def _calculate_basic_deduction(self, annual_income: float) -> float:
        """
        计算基础控除（基礎控除）
        高收入者有调减
        """
        if annual_income <= 24000000:
            # 一般情况：480,000
            return 480000
        elif annual_income <= 24500000:
            # 24M-24.5M：320,000
            return 320000
        elif annual_income <= 25000000:
            # 24.5M-25M：160,000
            return 160000
        else:
            # 25M以上：0
            return 0
