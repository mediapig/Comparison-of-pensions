#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挪威配置信息
基于2024年挪威政策
"""

class NorwayConfig:
    """挪威配置类"""

    def __init__(self):
        # 退休年龄配置
        self.retirement_ages = {
            'male': 62,      # 男性退休年龄
            'female': 62,     # 女性退休年龄
            'default': 62     # 默认退休年龄
        }

        # 税年
        self.tax_year = 2024

        # 货币
        self.currency = "NOK"

        # 挪威克朗汇率 (相对于人民币)
        self.exchange_rate_to_cny = 0.65  # 1 NOK = 0.65 CNY (大致汇率)

        # 基本免税额 (年收入)
        self.basic_deduction = 70000  # 70,000 NOK

        # 社保缴费基数上下限
        self.social_security_base_min = 50000   # 最低缴费基数
        self.social_security_base_max = 1000000 # 最高缴费基数

        # 养老金系统信息 (基于2024年挪威政策)
        self.pension_system = {
            'name': 'Folketrygden',
            'employee_rate': 0.082,     # 员工缴费率 8.2%
            'employer_rate': 0.141,     # 雇主缴费率 14.1%
            'total_rate': 0.223,       # 总缴费率 22.3%
            'accrual_rate': 0.181,     # 养老金积累率 18.1%
            'g_basic_amount': 118620,   # G基础额 (2024年)
            'income_cap_multiplier': 7.1,  # 收入上限倍数 (G的7.1倍)
            'minimum_pension': 200000,  # 最低养老金 (年)
            'maximum_pension': 1200000  # 最高养老金 (年)
        }

        # 职业养老金 (OTP)
        self.occupational_pension = {
            'name': 'Occupational Pension',
            'minimum_employer_rate': 0.02,  # 雇主最低缴费率 2%
            'common_rates': [0.02, 0.03, 0.04, 0.05, 0.06, 0.07],  # 常见缴费率
            'default_employer_rate': 0.05,  # 默认雇主缴费率 5%
            'employee_contribution': True,  # 是否允许员工缴费
            'default_employee_rate': 0.03   # 默认员工缴费率 3%
        }

        # 个人养老金 (IPS)
        self.individual_pension = {
            'name': 'Individual Pension Savings',
            'annual_limit': 15000,      # 年缴费上限 NOK 15,000
            'tax_deductible': True,     # 可抵税
            'default_contribution': 0   # 默认不缴费
        }

        # 税收信息
        self.tax_info = {
            'progressive_rates': True,
            'municipal_tax_rate': 0.22,  # 市政税 22%
            'county_tax_rate': 0.00,     # 郡税 (已取消)
            'national_tax_rate': 0.22,   # 国家税 22%
            'total_tax_rate': 0.44       # 总税率 44%
        }