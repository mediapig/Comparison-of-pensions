#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国个人所得税计算器
基于2024年最新个税政策
"""

from abc import ABC, abstractmethod
from typing import Dict, List

class ChinaTaxCalculator:
    """中国个人所得税计算器"""

    def __init__(self):
        self.country_code = 'CN'
        self.country_name = '中国'
        self.currency = 'CNY'
        self.basic_deduction = 60000  # 基本减除费用 (5000/月 * 12)
        self.special_deductions = {
            'social_security': 0,      # 社保扣除
            'housing_fund': 0,         # 住房公积金
            'education': 0,            # 子女教育
            'housing': 0,              # 住房租金/房贷利息
            'elderly': 0,              # 赡养老人
            'medical': 0,              # 大病医疗
            'continuing_education': 0, # 继续教育
            'other': 0                 # 其他扣除
        }

    def get_tax_brackets(self) -> List[Dict]:
        """获取中国个税税率表 (2024年)"""
        return [
            {'min': 0, 'max': 36000, 'rate': 0.03, 'quick_deduction': 0},
            {'min': 36000, 'max': 144000, 'rate': 0.10, 'quick_deduction': 2520},
            {'min': 144000, 'max': 300000, 'rate': 0.20, 'quick_deduction': 16920},
            {'min': 300000, 'max': 420000, 'rate': 0.25, 'quick_deduction': 31920},
            {'min': 420000, 'max': 660000, 'rate': 0.30, 'quick_deduction': 52920},
            {'min': 660000, 'max': 960000, 'rate': 0.35, 'quick_deduction': 85920},
            {'min': 960000, 'max': float('inf'), 'rate': 0.45, 'quick_deduction': 181920}
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """
        计算中国个人所得税

        Args:
            annual_income: 年收入
            deductions: 扣除项字典，包含社保、专项附加扣除等

        Returns:
            税收计算结果字典
        """
        if deductions is None:
            deductions = {}

        # 更新专项附加扣除
        for key, value in deductions.items():
            if key in self.special_deductions:
                self.special_deductions[key] = value

        # 计算总扣除额
        total_deductions = self.basic_deduction + sum(self.special_deductions.values())

        # 计算应纳税所得额
        taxable_income = annual_income - total_deductions

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'basic_deduction': self.basic_deduction,
                    'special_deductions': self.special_deductions.copy(),
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
                        'bracket': f"{bracket['min']:,.0f}-{bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': total_deductions,
            'breakdown': {
                'basic_deduction': self.basic_deduction,
                'special_deductions': self.special_deductions.copy(),
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

    def set_social_security_deduction(self, amount: float):
        """设置社保扣除金额"""
        self.special_deductions['social_security'] = amount

    def set_housing_fund_deduction(self, amount: float):
        """设置住房公积金扣除金额"""
        self.special_deductions['housing_fund'] = amount

    def set_education_deduction(self, amount: float):
        """设置子女教育扣除金额 (每年12000元)"""
        self.special_deductions['education'] = min(amount, 12000)

    def set_housing_deduction(self, amount: float):
        """设置住房租金/房贷利息扣除金额"""
        self.special_deductions['housing'] = amount

    def set_elderly_deduction(self, amount: float):
        """设置赡养老人扣除金额 (每年24000元)"""
        self.special_deductions['elderly'] = min(amount, 24000)

    def set_medical_deduction(self, amount: float):
        """设置大病医疗扣除金额"""
        self.special_deductions['medical'] = amount

    def set_continuing_education_deduction(self, amount: float):
        """设置继续教育扣除金额"""
        self.special_deductions['continuing_education'] = amount

    def set_other_deduction(self, amount: float):
        """设置其他扣除金额"""
        self.special_deductions['other'] = amount

    def calculate_social_security_contribution(self, monthly_salary: float) -> Dict:
        """计算社保缴费金额"""
        # 中国社保缴费基数上下限（以北京2024年为例）
        social_base_min = 5869   # 下限
        social_base_max = 31884  # 上限
        
        # 计算缴费基数
        contribution_base = max(social_base_min, min(monthly_salary, social_base_max))
        
        # 社保缴费比例（个人部分）
        pension_rate = 0.08      # 养老保险 8%
        medical_rate = 0.02      # 医疗保险 2%
        unemployment_rate = 0.002 # 失业保险 0.2%
        
        # 计算各项社保缴费
        pension_contribution = contribution_base * pension_rate
        medical_contribution = contribution_base * medical_rate
        unemployment_contribution = contribution_base * unemployment_rate
        
        # 总社保缴费
        total_social_security = pension_contribution + medical_contribution + unemployment_contribution
        
        return {
            'contribution_base': contribution_base,
            'pension': pension_contribution,
            'medical': medical_contribution,
            'unemployment': unemployment_contribution,
            'total': total_social_security
        }

    def calculate_housing_fund_contribution(self, monthly_salary: float) -> Dict:
        """计算住房公积金缴费金额"""
        # 住房公积金缴费比例（通常为12%）
        housing_fund_rate = 0.12
        
        # 计算缴费基数（通常与社保基数一致）
        contribution_base = monthly_salary
        
        # 计算住房公积金缴费
        housing_fund_contribution = contribution_base * housing_fund_rate
        
        return {
            'contribution_base': contribution_base,
            'rate': housing_fund_rate,
            'contribution': housing_fund_contribution
        }
