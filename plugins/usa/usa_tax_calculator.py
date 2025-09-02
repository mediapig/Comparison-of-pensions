#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国个人所得税计算器
基于2024年最新个税政策
"""

from typing import Dict, List

class USATaxCalculator:
    """美国个人所得税计算器"""

    def __init__(self):
        self.country_code = 'US'
        self.country_name = '美国'
        self.currency = 'USD'
        self.standard_deduction = {
            'single': 14600,           # 单身标准扣除
            'married_filing_jointly': 29200,  # 夫妻联合申报
            'married_filing_separately': 14600,  # 夫妻分别申报
            'head_of_household': 21900  # 户主
        }
        self.filing_status = 'single'  # 默认单身

    def get_tax_brackets(self) -> List[Dict]:
        """获取美国个税税率表 (2024年，单身)"""
        return [
            {'min': 0, 'max': 11600, 'rate': 0.10, 'quick_deduction': 0},
            {'min': 11600, 'max': 47150, 'rate': 0.12, 'quick_deduction': 1160},
            {'min': 47150, 'max': 100525, 'rate': 0.22, 'quick_deduction': 5423},
            {'min': 100525, 'max': 191950, 'rate': 0.24, 'quick_deduction': 16290},
            {'min': 191950, 'max': 243725, 'rate': 0.32, 'quick_deduction': 37104},
            {'min': 243725, 'max': 609350, 'rate': 0.35, 'quick_deduction': 52832},
            {'min': 609350, 'max': float('inf'), 'rate': 0.37, 'quick_deduction': 174238}
        ]

    def set_filing_status(self, status: str):
        """设置申报状态"""
        if status in self.standard_deduction:
            self.filing_status = status

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """
        计算美国个人所得税

        Args:
            annual_income: 年收入
            deductions: 扣除项字典，包含401K、IRA等

        Returns:
            税收计算结果字典
        """
        if deductions is None:
            deductions = {}

        # 获取标准扣除
        standard_deduction = self.standard_deduction[self.filing_status]

        # 计算总扣除额 (标准扣除 + 其他扣除)
        total_deductions = standard_deduction + deductions.get('other_deductions', 0)

        # 计算应纳税所得额
        taxable_income = annual_income - total_deductions

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'standard_deduction': standard_deduction,
                    'other_deductions': deductions.get('other_deductions', 0),
                    'tax_brackets': []
                }
            }

        # 计算个税
        tax_brackets = self.get_tax_brackets()
        total_tax = 0
        bracket_details = []

        for bracket in tax_brackets:
            if taxable_income > bracket['min']:
                # 计算该档位的应纳税所得额
                bracket_taxable = min(taxable_income - bracket['min'],
                                    bracket['max'] - bracket['min'])

                if bracket_taxable > 0:
                    # 计算该档位的税额
                    bracket_tax = bracket_taxable * bracket['rate']
                    total_tax += bracket_tax

                    bracket_details.append({
                        'bracket': f"${bracket['min']:,.0f}-${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': total_deductions,
            'breakdown': {
                'standard_deduction': standard_deduction,
                'other_deductions': deductions.get('other_deductions', 0),
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

    def get_tax_summary(self, annual_income: float, deductions: Dict = None) -> Dict:
        """获取税收汇总信息"""
        tax_result = self.calculate_income_tax(annual_income, deductions)

        return {
            'country_code': self.country_code,
            'country_name': self.country_name,
            'currency': self.currency,
            'annual_income': annual_income,
            'total_tax': tax_result.get('total_tax', 0),
            'net_income': self.calculate_net_income(annual_income, deductions),
            'effective_tax_rate': self.calculate_effective_tax_rate(annual_income, deductions),
            'monthly_net_income': self.calculate_net_income(annual_income, deductions) / 12,
            'details': tax_result
        }

    def calculate_with_401k(self, annual_income: float, k401_contribution: float,
                           other_deductions: float = 0) -> Dict:
        """计算包含401K扣除的个税"""
        deductions = {
            'other_deductions': other_deductions + k401_contribution
        }
        return self.calculate_income_tax(annual_income, deductions)

    def calculate_with_ira(self, annual_income: float, ira_contribution: float,
                          other_deductions: float = 0) -> Dict:
        """计算包含IRA扣除的个税"""
        # IRA扣除上限 (2024年)
        ira_limit = 7000 if annual_income < 146000 else 0
        actual_ira_deduction = min(ira_contribution, ira_limit)

        deductions = {
            'other_deductions': other_deductions + actual_ira_deduction
        }
        return self.calculate_income_tax(annual_income, deductions)
