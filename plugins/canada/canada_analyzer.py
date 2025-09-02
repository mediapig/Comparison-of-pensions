#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加拿大养老金分析器
分析CPP和OAS的详细情况
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter

class CanadaPensionAnalyzer:
    """加拿大养老金分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['CA']

    def analyze_scenario(self, scenario_name: str, monthly_salary: float):
        """分析单个场景"""
        print(f"\n{'='*80}")
        print(f"🇨🇦 加拿大养老金分析 - {scenario_name}")
        print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
        print(f"工作年限: 35年")
        print(f"退休年龄: 65岁")
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
            display_currency="CAD"
        )

        print(f"\n🏦 正在计算加拿大养老金...")

        # 计算加拿大养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示给付信息（公共年金制）
        cpp_annual = result.details.get('cpp_monthly', 0) * 12
        oas_annual = result.details.get('oas_monthly', 0) * 12
        annual_pension = result.monthly_pension * 12

        print(f"\n📊 养老金给付（公共年金制：CPP + OAS）")
        print("-" * 50)
        print(f"  CPP: {converter.format_amount(cpp_annual, 'CAD')}/年 | OAS: {converter.format_amount(oas_annual, 'CAD')}/年")
        print(f"  合计: {converter.format_amount(annual_pension, 'CAD')}/年 ≈ {converter.format_amount(result.monthly_pension, 'CAD')}/月")

        # 显示缴费统计信息
        print(f"\n💰 CPP 累计缴费（仅统计口径）")
        print("-" * 50)
        print("  合计费率: 11.9% = 员工 5.95% + 雇主 5.95%")
        print(f"  累计缴费（合计）: {converter.format_amount(result.total_contribution * 2, 'CAD')}")

        print(f"\nℹ️ 说明：CPP 与 OAS 为公共年金（DB/准DB），不计算总收益、投资回报率与回本年龄。")
        print("    OAS = 734.95(2025Q3, 65–74) × 12 × (居住年限/40) = 734.95×12×(35/40) ≈ 7,716.98/年")
        print("    CPP 满额口径采用：17,196/年（2025），并按年资与平均可计缴工资比例折算")

        # 计算替代率
        annual_salary_cad = monthly_salary * 0.19 * 12  # 转换为加币年工资
        replacement_rate = (result.monthly_pension * 12) / annual_salary_cad * 100

        print(f"\n📋 总结:")
        print("-" * 50)
        print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
        print(f"年工资: {converter.format_amount(annual_salary_cad, 'CAD')} (C$)")
        print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'CAD')}")
        print(f"替代率: {replacement_rate:.1f}%")

    def analyze_all_scenarios(self):
        """分析所有场景"""
        print("🇨🇦 === 加拿大养老金详细分析系统 ===")
        print("分析CPP和OAS的详细情况\n")

        # 定义两个场景
        scenarios = [
            ("高收入场景", 50000),  # 月薪5万人民币
            ("低收入场景", 5000)    # 月薪5千人民币
        ]

        for scenario_name, monthly_salary in scenarios:
            self.analyze_scenario(scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 加拿大养老金分析完成！")
