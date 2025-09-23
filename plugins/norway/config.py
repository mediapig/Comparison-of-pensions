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
            'male': 67,      # 男性退休年龄
            'female': 67,     # 女性退休年龄
            'default': 67     # 默认退休年龄
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
        
        # 养老金系统信息
        self.pension_system = {
            'name': 'Folketrygden',
            'employee_rate': 0.08,      # 员工缴费率 8%
            'employer_rate': 0.14,      # 雇主缴费率 14%
            'total_rate': 0.22,        # 总缴费率 22%
            'minimum_pension': 200000,  # 最低养老金 (年)
            'maximum_pension': 1200000  # 最高养老金 (年)
        }
        
        # 税收信息
        self.tax_info = {
            'progressive_rates': True,
            'municipal_tax_rate': 0.22,  # 市政税 22%
            'county_tax_rate': 0.00,     # 郡税 (已取消)
            'national_tax_rate': 0.22,   # 国家税 22%
            'total_tax_rate': 0.44       # 总税率 44%
        }