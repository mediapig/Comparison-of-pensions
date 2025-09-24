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

        # 社保缴费基数上限（2024年）
        self.social_security_cap = 160200  # 年收入上限

        # 标准扣除额（2024年）
        self.standard_deduction = 14600  # 单身

        # Medicare税率
        
        self.medicare_rate = 0.0145  # 1.45%