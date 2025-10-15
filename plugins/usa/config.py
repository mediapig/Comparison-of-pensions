#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国插件配置文件
"""

class USAConfig:
    """美国插件配置"""

    def __init__(self):
        # 退休年龄配置
        self.retirement_ages = {
            "male": 67,
            "female": 67
        }

        # 税年
        self.tax_year = 2024

        # 社保缴费率
        self.contribution_rates = {
            "employee": 0.062,      # 6.2% 社会保障税
            "employer": 0.062,      # 6.2% 雇主缴费
            "total": 0.124          # 总缴费比例 12.4%
        }

        # 社保缴费基数上限（逐年）
        self.social_security_cap_by_year = {
            2023: 160200,
            2024: 168600,
            2025: 174900
        }

        # 当前年份的社保缴费基数上限
        self.social_security_cap = self.social_security_cap_by_year.get(self.tax_year, 168600)

        # 标准扣除额（2024年）
        self.standard_deduction = 14600  # 单身

        # Medicare税率
        self.medicare_rate = 0.0145  # 1.45%

        # Additional Medicare Tax (对超过$200,000的收入)
        self.additional_medicare_threshold = 200000  # 触发额外Medicare税的阈值
        self.additional_medicare_rate = 0.009  # 0.9% (仅员工缴纳)

        # 401(k)限额（逐年）
        self.employee_deferral_limit_by_year = {
            2023: {"under_50": 22500, "over_50": 30000},
            2024: {"under_50": 23000, "over_50": 30500},
            2025: {"under_50": 23500, "over_50": 31000}
        }

        self.annual_additions_limit_by_year = {
            2023: 66000,
            2024: 69000,
            2025: 71000
        }

        # 标准扣除额（逐年，单身申报）
        self.standard_deduction_by_year = {
            2023: 13850,
            2024: 14600,
            2025: 15000
        }

        # 当前年份的401(k)限额
        self.employee_deferral_limit = self.employee_deferral_limit_by_year.get(self.tax_year, {"under_50": 23000, "over_50": 30500})
        self.annual_additions_limit = self.annual_additions_limit_by_year.get(self.tax_year, 69000)