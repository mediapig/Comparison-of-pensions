#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本养老金分析器
分析国民年金(NPI) + 厚生年金(EPI) 的详细情况
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter

class JapanPensionAnalyzer:
    """日本养老金分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['JP']

    def analyze_scenario(self, scenario_name: str, monthly_salary: float):
        """分析单个场景"""
        # 获取实际参数
        retirement_age = 65  # Japan retirement age
        start_age = 30
        work_years = retirement_age - start_age  # 65-30 = 35

        print(f"\n{'='*80}")
        print(f"🇯🇵 日本养老金分析 - {scenario_name}")
        print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
        print(f"工作年限: {work_years}年")
        print(f"退休年龄: {retirement_age}岁")
        print(f"领取年限: 20年")
        print(f"{'='*80}")

        # 创建个人信息
        person = Person(
            name="测试用户",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(1995, 7, 1)
        )

        # 创建工资档案 - 工资不增长
        salary_profile = SalaryProfile(
            base_salary=monthly_salary,
            annual_growth_rate=0.00
        )

        # 创建经济因素
        economic_factors = EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.07,
            social_security_return_rate=0.05,
            base_currency="CNY",
            display_currency="JPY"
        )

        print(f"\n🏦 正在计算日本养老金...")

        # 计算日本养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示基本信息
        print(f"\n📊 养老金计算结果:")
        print("-" * 50)
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'JPY')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'JPY')}")
        print("总收益: N/A（DB制）")
        print("投资回报率: N/A（DB制）")
        print("回本年龄: N/A（DB制）")

        # 显示缴费率信息
        print(f"\n💰 缴费率信息（厚生年金，统计口径）:")
        print("-" * 50)
        print("合计费率: 18.3% ＝ 员工 9.15% + 雇主 9.15%")

        # 显示累计缴费金额
        EPI_RATE_TOTAL = 0.183
        EPI_RATE_EMP   = 0.0915
        EPI_RATE_ER    = 0.0915
        epi_contrib_total = result.total_contribution
        epi_contrib_emp   = epi_contrib_total * (EPI_RATE_EMP / EPI_RATE_TOTAL)
        epi_contrib_er    = epi_contrib_total * (EPI_RATE_ER  / EPI_RATE_TOTAL)
        print(f"累计缴费（合计）: {converter.format_amount(epi_contrib_total, 'JPY')} ＝ 员工 {converter.format_amount(epi_contrib_emp, 'JPY')} + 雇主 {converter.format_amount(epi_contrib_er, 'JPY')}")

        # 计算替代率
        annual_salary_jpy = monthly_salary * 20 * 12  # 转换为日元年工资
        replacement_rate = (result.monthly_pension * 12) / annual_salary_jpy * 100

        print(f"\n📋 总结:")
        print("-" * 50)
        print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
        print(f"年工资: {converter.format_amount(annual_salary_jpy, 'JPY')} (¥)")
        print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'JPY')}")
        print(f"替代率: {replacement_rate:.1f}%")

    def analyze_all_scenarios(self, monthly_salary: float = 10000):
        """分析指定工资的养老金情况"""
        print("🇯🇵 === 日本养老金详细分析系统 ===")
        print("分析国民年金(NPI) + 厚生年金(EPI) 的详细情况\n")

        self.analyze_scenario("分析场景", monthly_salary)
        print(f"\n{'='*80}")
        print(f"✅ 分析完成")
        print(f"{'='*80}")

        print(f"\n🎯 日本养老金分析完成！")
