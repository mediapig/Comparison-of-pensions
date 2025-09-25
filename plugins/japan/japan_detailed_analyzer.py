#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本详细分析器
提供日本养老金、税收、社保的全面分析
"""

from typing import Dict, Any, Optional
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
# 延迟导入以避免循环导入
from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount

class JapanDetailedAnalyzer:
    """日本详细分析器"""

    def __init__(self, engine=None):
        self.engine = engine
        self.converter = SmartCurrencyConverter()

    def analyze_comprehensive(self, monthly_salary_cny: float, 
                           start_age: int = 30, 
                           retirement_age: Optional[int] = None) -> Dict[str, Any]:
        """
        综合分析日本养老金、税收、社保情况
        
        Args:
            monthly_salary_cny: 月薪（人民币）
            start_age: 开始工作年龄
            retirement_age: 退休年龄（默认65岁）
            
        Returns:
            分析结果字典
        """
        if retirement_age is None:
            retirement_age = 65
            
        # 转换为日元
        currency_amount = CurrencyAmount(monthly_salary_cny * 12, "CNY", "")
        jpy_amount = self.converter.convert_to_local(currency_amount, "JPY")
        monthly_salary_jpy = jpy_amount.amount / 12
        
        # 创建测试数据
        person = self._create_test_person(start_age)
        salary_profile = SalaryProfile(
            monthly_salary=monthly_salary_jpy,
            annual_growth_rate=0.0,
            contribution_start_age=start_age
        )
        economic_factors = EconomicFactors(
            inflation_rate=0.02,
            investment_return_rate=0.05,
            social_security_return_rate=0.03
        )
        
        # 获取日本插件
        from core.plugin_manager import plugin_manager
        japan_plugin = plugin_manager.get_plugin("JP")
        
        # 1. 养老金分析
        pension_analysis = self._analyze_pension(japan_plugin, person, salary_profile, economic_factors)
        
        # 2. 收入分析
        income_analysis = self._analyze_income(japan_plugin, person, salary_profile, economic_factors)
        
        # 3. 全生命周期总结
        lifetime_summary = self._analyze_lifetime_summary(japan_plugin, person, salary_profile, economic_factors)
        
        return {
            "国家": "日本",
            "国家代码": "JP",
            "货币": "JPY",
            "分析时间": "2024年",
            "第一年分析": income_analysis,
            "工作期总计": lifetime_summary,
            "退休期分析": pension_analysis,
            "投资回报分析": self._analyze_roi(pension_analysis, lifetime_summary),
            "人民币对比": self._convert_to_cny(pension_analysis, lifetime_summary)
        }
    
    def _create_test_person(self, start_age: int) -> Person:
        """创建测试人员"""
        current_year = date.today().year
        return Person(
            name="日本用户",
            birth_date=date(current_year - start_age, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(current_year - start_age, 1, 1)
        )
    
    def _analyze_pension(self, plugin, person: Person, salary_profile: SalaryProfile, 
                        economic_factors: EconomicFactors) -> Dict[str, Any]:
        """分析养老金"""
        pension_result = plugin.calculate_pension(person, salary_profile, economic_factors)
        
        return {
            "年龄范围": f"{plugin.get_retirement_age(person)}-90岁",
            "退休年限": 90 - plugin.get_retirement_age(person),
            "退休金收入": {
                "月领取金额": pension_result.monthly_pension,
                "年领取金额": pension_result.monthly_pension * 12,
                "退休期总领取": pension_result.total_benefit
            }
        }
    
    def _analyze_income(self, plugin, person: Person, salary_profile: SalaryProfile,
                       economic_factors: EconomicFactors) -> Dict[str, Any]:
        """分析收入情况"""
        monthly_salary = salary_profile.monthly_salary
        annual_income = monthly_salary * 12
        
        # 计算社保缴费
        ss_result = plugin.calculate_social_security(monthly_salary, person.work_years)
        
        # 计算个税
        tax_result = plugin.calculate_tax(annual_income)
        
        # 计算实际到手
        net_income = annual_income - tax_result.get('total_tax', 0) - ss_result.get('monthly_employee', 0) * 12
        
        return {
            "年龄": person.age,
            "收入情况": {
                "年收入": annual_income,
                "社保缴费基数": monthly_salary,
                "年薪上限限制": False
            },
            "社保缴费": {
                "雇员费率": 9.175,
                "雇主费率": 9.175,
                "总费率": 18.35,
                "年缴费金额": ss_result.get('total_lifetime', 0) / person.work_years if person.work_years > 0 else 0,
                "雇员缴费": ss_result.get('monthly_employee', 0) * 12,
                "雇主缴费": ss_result.get('monthly_employer', 0) * 12
            },
            "税务情况": {
                "应税收入": tax_result.get('taxable_income', 0),
                "所得税": tax_result.get('total_tax', 0),
                "实际到手收入": net_income
            }
        }
    
    def _analyze_lifetime_summary(self, plugin, person: Person, salary_profile: SalaryProfile,
                                economic_factors: EconomicFactors) -> Dict[str, Any]:
        """分析全生命周期"""
        work_years = person.work_years
        monthly_salary = salary_profile.monthly_salary
        annual_income = monthly_salary * 12
        
        # 计算社保缴费
        ss_result = plugin.calculate_social_security(monthly_salary, work_years)
        
        # 计算个税
        tax_result = plugin.calculate_tax(annual_income)
        
        # 计算总收入
        total_income = annual_income * work_years
        total_tax = tax_result.get('total_tax', 0) * work_years
        total_ss_employee = ss_result.get('monthly_employee', 0) * 12 * work_years
        net_income = total_income - total_tax - total_ss_employee
        
        return {
            "工作年限": work_years,
            "年龄范围": f"{person.age}-{plugin.get_retirement_age(person)}岁",
            "收入情况": {
                "总收入": total_income,
                "总税费": total_tax,
                "实际到手收入": net_income
            },
            "社保缴费总计": {
                "雇员缴费": total_ss_employee,
                "雇主缴费": ss_result.get('monthly_employer', 0) * 12 * work_years,
                "总缴费": ss_result.get('total_lifetime', 0)
            }
        }
    
    def _analyze_roi(self, pension_analysis: Dict[str, Any], 
                    lifetime_summary: Dict[str, Any]) -> Dict[str, Any]:
        """分析投资回报"""
        pension_result = pension_analysis["退休金收入"]
        ss_total = lifetime_summary["社保缴费总计"]["总缴费"]
        
        # 计算简单回报率
        total_benefit = pension_result["退休期总领取"]
        simple_roi = ((total_benefit / ss_total) - 1) * 100 if ss_total > 0 else 0
        
        # 计算回本年龄
        monthly_pension = pension_result["月领取金额"]
        break_even_years = ss_total / (monthly_pension * 12) if monthly_pension > 0 else 0
        break_even_age = 65 + break_even_years
        
        return {
            "简单回报率": simple_roi,
            "内部收益率_IRR": 0.06,  # 假设6%
            "回本分析": {
                "回本年龄": break_even_age,
                "回本时间": break_even_years,
                "能否回本": 1 if break_even_age < 90 else 0
            }
        }
    
    def _convert_to_cny(self, pension_analysis: Dict[str, Any], 
                       lifetime_summary: Dict[str, Any]) -> Dict[str, Any]:
        """转换为人民币显示"""
        monthly_pension_jpy = pension_analysis["退休金收入"]["月领取金额"]
        total_contribution_jpy = lifetime_summary["社保缴费总计"]["总缴费"]
        
        # 转换为人民币
        monthly_pension_cny = self.converter.convert_to_local(
            CurrencyAmount(monthly_pension_jpy, "JPY", ""), "CNY"
        ).amount
        
        total_contribution_cny = self.converter.convert_to_local(
            CurrencyAmount(total_contribution_jpy, "JPY", ""), "CNY"
        ).amount
        
        return {
            "退休金收入": {
                "月退休金": monthly_pension_cny
            },
            "缴费情况": {
                "总缴费": total_contribution_cny
            }
        }
    
    def print_detailed_analysis(self, person: Person, salary_profile: SalaryProfile,
                              economic_factors: EconomicFactors, pension_result, 
                              currency_amount: CurrencyAmount):
        """打印详细分析结果"""
        # 转换为人民币进行分析
        cny_amount = self.converter.convert_to_local(currency_amount, "CNY")
        monthly_salary_cny = cny_amount.amount / 12
        
        # 执行综合分析
        analysis_result = self.analyze_comprehensive(monthly_salary_cny, person.age)
        
        # 打印JSON格式结果
        import json
        print(json.dumps(analysis_result, ensure_ascii=False, indent=2))