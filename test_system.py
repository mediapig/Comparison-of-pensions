#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试文件
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    try:
        from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
        from core.base_calculator import BasePensionCalculator
        from core.pension_engine import PensionEngine
        from plugins.china.china_calculator import ChinaPensionCalculator
        from plugins.usa.usa_calculator import USAPensionCalculator
        from utils.inflation import InflationCalculator
        from utils.salary_growth import SalaryGrowthModel
        from utils.investment import InvestmentCalculator
        print("✓ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_basic_models():
    """测试基本数据模型"""
    try:
        from datetime import date
        from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType

        # 测试Person模型
        person = Person(
            name="测试用户",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(2015, 7, 1)
        )

        print(f"✓ Person模型创建成功: {person.name}, 年龄: {person.age}")

        # 测试SalaryProfile模型
        salary = SalaryProfile(
            base_salary=8000,
            annual_growth_rate=0.05
        )

        future_salary = salary.get_salary_at_age(35, 30)
        print(f"✓ SalaryProfile模型创建成功: 5年后工资: {future_salary:.0f}")

        # 测试EconomicFactors模型
        economic = EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.07,
            social_security_return_rate=0.05
        )

        print(f"✓ EconomicFactors模型创建成功: 通胀率 {economic.inflation_rate:.1%}")

        return True

    except Exception as e:
        print(f"✗ 基本模型测试失败: {e}")
        return False

def test_calculators():
    """测试计算器"""
    try:
        from core.pension_engine import PensionEngine
        from plugins.china.china_calculator import ChinaPensionCalculator
        from plugins.usa.usa_calculator import USAPensionCalculator

        # 创建引擎
        engine = PensionEngine()

        # 注册计算器
        engine.register_calculator(ChinaPensionCalculator())
        engine.register_calculator(USAPensionCalculator())

        countries = engine.get_available_countries()
        print(f"✓ 计算器注册成功: {countries}")

        return True

    except Exception as e:
        print(f"✗ 计算器测试失败: {e}")
        return False

def test_utilities():
    """测试工具模块"""
    try:
        from utils.inflation import InflationCalculator
        from utils.salary_growth import SalaryGrowthModel
        from utils.investment import InvestmentCalculator

        # 测试通胀计算
        inflation_calc = InflationCalculator()
        adjusted_amount = inflation_calc.calculate_inflation_adjusted_amount(10000, 10, 0.03)
        print(f"✓ 通胀计算测试: 10年后10000元的现值: {adjusted_amount:.0f}")

        # 测试工资增长
        salary_model = SalaryGrowthModel()
        salaries = salary_model.compound_growth(8000, 0.05, 5)
        print(f"✓ 工资增长测试: 5年后工资: {salaries[-1]:.0f}")

        # 测试投资计算
        investment_calc = InvestmentCalculator()
        future_value = investment_calc.calculate_future_value(10000, 10, 0.07)
        print(f"✓ 投资计算测试: 10年后10000元的未来价值: {future_value:.0f}")

        return True

    except Exception as e:
        print(f"✗ 工具模块测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始系统测试...\n")

    tests = [
        ("模块导入测试", test_imports),
        ("基本模型测试", test_basic_models),
        ("计算器测试", test_calculators),
        ("工具模块测试", test_utilities)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"运行 {test_name}...")
        if test_func():
            passed += 1
        print()

    print(f"测试完成: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
