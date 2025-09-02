#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡个人所得税计算器
基于2024年最新个税政策
"""

from typing import Dict, List

class SingaporeTaxCalculator:
    """新加坡个人所得税计算器"""

    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'

        # 新加坡个税税率表 (2024年)
        self.tax_brackets = [
            {'min': 0, 'max': 20000, 'rate': 0.0, 'quick_deduction': 0},
            {'min': 20000, 'max': 30000, 'rate': 0.02, 'quick_deduction': 0},
            {'min': 30000, 'max': 40000, 'rate': 0.035, 'quick_deduction': 200},
            {'min': 40000, 'max': 80000, 'rate': 0.07, 'quick_deduction': 550},
            {'min': 80000, 'max': 120000, 'rate': 0.115, 'quick_deduction': 3350},
            {'min': 120000, 'max': 160000, 'rate': 0.15, 'quick_deduction': 7950},
            {'min': 160000, 'max': 200000, 'rate': 0.18, 'quick_deduction': 13950},
            {'min': 200000, 'max': 240000, 'rate': 0.19, 'quick_deduction': 18150},
            {'min': 240000, 'max': 280000, 'rate': 0.195, 'quick_deduction': 23250},
            {'min': 280000, 'max': 320000, 'rate': 0.20, 'quick_deduction': 29250},
            {'min': 320000, 'max': 500000, 'rate': 0.22, 'quick_deduction': 37250},
            {'min': 500000, 'max': 1000000, 'rate': 0.23, 'quick_deduction': 47250},
            {'min': 1000000, 'max': float('inf'), 'rate': 0.24, 'quick_deduction': 147250}
        ]

        # 新加坡CPF缴费率 (2024年)
        self.cpf_rates = {
            'employee': 0.20,         # 员工缴费率 20%
            'employer': 0.17,         # 雇主缴费率 17%
            'total': 0.37             # 总缴费率 37%
        }

    def get_tax_brackets(self) -> List[Dict]:
        """获取新加坡个税税率表"""
        return self.tax_brackets

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """
        计算新加坡个人所得税

        Args:
            annual_income: 年收入
            deductions: 扣除项字典，包含CPF等

        Returns:
            税收计算结果字典
        """
        if deductions is None:
            deductions = {}

        # 新加坡CPF可以税前扣除
        cpf_deduction = deductions.get('cpf_contribution', 0)

        # 计算应纳税所得额
        taxable_income = annual_income - cpf_deduction

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': cpf_deduction,
                'breakdown': {
                    'cpf_deduction': cpf_deduction,
                    'tax_brackets': []
                }
            }

        # 计算个税
        total_tax = 0
        bracket_details = []

        for bracket in self.tax_brackets:
            if taxable_income > bracket['min']:
                # 计算该档位的应纳税所得额
                bracket_taxable = min(taxable_income - bracket['min'],
                                    bracket['max'] - bracket['min'])

                if bracket_taxable > 0:
                    # 计算该档位的税额
                    bracket_tax = bracket_taxable * bracket['rate']
                    total_tax += bracket_tax

                    bracket_details.append({
                        'bracket': f"S${bracket['min']:,.0f}-S${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': cpf_deduction,
            'breakdown': {
                'cpf_deduction': cpf_deduction,
                'tax_brackets': bracket_details
            }
        }

    def calculate_cpf_contribution(self, monthly_salary: float) -> Dict:
        """计算CPF缴费金额"""
        # 新加坡CPF缴费上限 (2024年)
        cpf_ceiling = 7400  # 月薪上限

        # 计算缴费基数
        contribution_base = min(monthly_salary, cpf_ceiling)

        # 员工缴费
        employee_total = contribution_base * self.cpf_rates['employee']

        # 雇主缴费
        employer_total = contribution_base * self.cpf_rates['employer']

        # 总缴费
        total_cpf = employee_total + employer_total

        return {
            'employee': {
                'total': employee_total
            },
            'employer': {
                'total': employer_total
            },
            'total': total_cpf,
            'contribution_base': contribution_base
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
