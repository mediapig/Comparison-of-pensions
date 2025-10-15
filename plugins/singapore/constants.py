#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF相关常量
包含新加坡特有的CPF费率、限额等常量
"""


class SingaporeCPFConstants:
    """新加坡CPF相关常量"""

    # 年龄段缴费费率配置
    AGE_RATE_CONFIG = {
        # 年龄范围: (雇员费率, 雇主费率, 总费率)
        (0, 35): (0.20, 0.17, 0.37),    # ≤35岁
        (36, 45): (0.20, 0.17, 0.37),   # 36-45岁
        (46, 50): (0.20, 0.17, 0.37),   # 46-50岁
        (51, 55): (0.20, 0.17, 0.37),   # 51-55岁
        (56, 60): (0.125, 0.125, 0.25), # 56-60岁
        (61, 65): (0.075, 0.075, 0.15), # 61-65岁
        (66, 70): (0.05, 0.05, 0.10),   # 66-70岁
        (71, float('inf')): (0.05, 0.05, 0.10)  # 71岁以上
    }

    # 年龄段账户分配配置
    AGE_ALLOCATION_CONFIG = {
        # 年龄范围: (OA比例, SA比例, MA比例)
        (0, 35): (0.23, 0.06, 0.08),    # ≤35岁: 23%/6%/8%
        (36, 45): (0.23, 0.06, 0.08),   # 36-45岁: 23%/6%/8%
        (46, 50): (0.23, 0.06, 0.08),   # 46-50岁: 23%/6%/8%
        (51, 55): (0.23, 0.06, 0.08),   # 51-55岁: 23%/6%/8%
        (56, 60): (0.21, 0.07, 0.72),   # 56-60岁: 21%/7%/72%
        (61, 65): (0.12, 0.04, 0.84),   # 61-65岁: 12%/4%/84%
        (66, 70): (0.01, 0.01, 0.98),   # 66-70岁: 1%/1%/98%
        (71, float('inf')): (0.01, 0.01, 0.98)  # 71岁以上: 1%/1%/98%
    }

    # 兼容性：保持原有常量
    EMPLOYEE_RATE = 0.20  # 雇员费率20%
    EMPLOYER_RATE = 0.17  # 雇主费率17%
    TOTAL_RATE = 0.37     # 总费率37%

    # 缴费基数上限（2024年）
    OW_ANNUAL_CEILING = 81600  # OW年封顶81,600 (6,800×12)
    OW_MONTHLY_CEILING = 6800  # OW月封顶6,800

    # CPF年度总额上限
    CPF_ANNUAL_LIMIT = 37740  # CPF年度总额上限37,740

    # 账户分配比例（≤35岁）
    OA_ALLOCATION_RATE = 0.23  # OA 23%
    SA_ALLOCATION_RATE = 0.06  # SA 6%
    MA_ALLOCATION_RATE = 0.08  # MA 8%

    # 利息率
    OA_INTEREST_RATE = 0.025   # OA年息2.5%
    SA_INTEREST_RATE = 0.04    # SA年息4%
    MA_INTEREST_RATE = 0.04    # MA年息4%
    RA_INTEREST_RATE = 0.04    # RA年息4%

    # 额外利息
    EXTRA_INTEREST_RATE = 0.01  # 额外1%利息
    EXTRA_INTEREST_THRESHOLD = 60000  # 首$60k
    OA_EXTRA_INTEREST_LIMIT = 20000   # OA额外利息限制$20k

    # 限额（2024年）
    BHS_2024 = 71500      # 2024年BHS
    FRS_2024 = 205800     # 2024年FRS
    ANNUAL_GROWTH_RATE = 0.03  # 年增长率3%

    # 税务相关
    EARNED_INCOME_RELIEF = 1000  # 收入减免

    @classmethod
    def get_age_rates(cls, age: int) -> tuple:
        """根据年龄获取缴费费率"""
        for age_range, rates in cls.AGE_RATE_CONFIG.items():
            if age_range[0] <= age <= age_range[1]:
                return rates
        # 默认返回≤35岁的费率
        return cls.AGE_RATE_CONFIG[(0, 35)]

    @classmethod
    def get_age_allocation(cls, age: int) -> tuple:
        """根据年龄获取账户分配比例"""
        for age_range, allocation in cls.AGE_ALLOCATION_CONFIG.items():
            if age_range[0] <= age <= age_range[1]:
                return allocation
        # 默认返回≤35岁的分配
        return cls.AGE_ALLOCATION_CONFIG[(0, 35)]


class SingaporeTaxConstants:
    """新加坡税务相关常量"""

    # 税率表（2024年）
    TAX_BRACKETS = [
        (0, 20000, 0.0),      # 0-20,000: 0%
        (20000, 30000, 0.02), # 20,001-30,000: 2%
        (30000, 40000, 0.035), # 30,001-40,000: 3.5%
        (40000, 80000, 0.07), # 40,001-80,000: 7%
        (80000, 120000, 0.115), # 80,001-120,000: 11.5%
        (120000, 160000, 0.15), # 120,001-160,000: 15%
        (160000, 200000, 0.18), # 160,001-200,000: 18%
        (200000, 240000, 0.19), # 200,001-240,000: 19%
        (240000, 280000, 0.195), # 240,001-280,000: 19.5%
        (280000, 320000, 0.20), # 280,001-320,000: 20%
        (320000, float('inf'), 0.22) # 320,001+: 22%
    ]

    # 个人减免
    EARNED_INCOME_RELIEF = 1000  # 收入减免
    CHILD_RELIEF = 4000          # 子女减免
    PARENT_RELIEF = 1500         # 父母减免


# 导出常量
__all__ = [
    'SingaporeCPFConstants',
    'SingaporeTaxConstants'
]
