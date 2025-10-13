#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF相关常量
包含新加坡特有的CPF费率、限额等常量
"""


class SingaporeCPFConstants:
    """新加坡CPF相关常量"""

    # 缴费费率
    EMPLOYEE_RATE = 0.20  # 雇员费率20%
    EMPLOYER_RATE = 0.17  # 雇主费率17%
    TOTAL_RATE = 0.37     # 总费率37%

    # 缴费基数上限
    OW_ANNUAL_CEILING = 96000  # OW年封顶96,000
    OW_MONTHLY_CEILING = 8000  # OW月封顶8,000

    # 账户分配比例（≤55岁）
    OA_ALLOCATION_RATE = 0.62  # OA 62%
    SA_ALLOCATION_RATE = 0.16  # SA 16%
    MA_ALLOCATION_RATE = 0.22  # MA 22%

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
