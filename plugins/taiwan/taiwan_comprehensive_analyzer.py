#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from typing import Dict, Any
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer

class TaiwanTaxCalculator:
    """台湾个人所得税计算器"""
    
    def __init__(self):
        self.country_code = 'TW'
        self.country_name = '台湾'
        self.currency = 'TWD'
        
        # 台湾个税税率表 (2024年)
        self.tax_brackets = [
            {'min': 0, 'max': 560000, 'rate': 0.05, 'quick_deduction': 0},
            {'min': 560000, 'max': 1260000, 'rate': 0.12, 'quick_deduction': 39200},
            {'min': 1260000, 'max': 2520000, 'rate': 0.20, 'quick_deduction': 140000},
            {'min': 2520000, 'max': 4720000, 'rate': 0.30, 'quick_deduction': 392000},
            {'min': 4720000, 'max': float('inf'), 'rate': 0.40, 'quick_deduction': 864000}
        ]
        
        # 台湾劳保缴费率 (2024年)
        self.labor_insurance_rates = {
            'employee': 0.20,         # 员工劳保缴费率 20%
            'employer': 0.70,         # 雇主劳保缴费率 70%
            'total': 0.90             # 总劳保缴费率 90%
        }
        
        # 台湾健保缴费率 (2024年)
        self.health_insurance_rates = {
            'employee': 0.30,         # 员工健保缴费率 30%
            'employer': 0.60,         # 雇主健保缴费率 60%
            'total': 0.90             # 总健保缴费率 90%
        }

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算台湾个人所得税"""
        if deductions is None:
            deductions = {}
            
        # 基本免税额 (2024年)
        basic_allowance = 92000
        
        # 劳保和健保扣除
        labor_insurance_deduction = deductions.get('labor_insurance_contribution', 0)
        health_insurance_deduction = deductions.get('health_insurance_contribution', 0)
        
        # 计算应纳税所得额
        taxable_income = annual_income - basic_allowance - labor_insurance_deduction - health_insurance_deduction
        
        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': basic_allowance + labor_insurance_deduction + health_insurance_deduction,
                'breakdown': {
                    'basic_allowance': basic_allowance,
                    'labor_insurance_deduction': labor_insurance_deduction,
                    'health_insurance_deduction': health_insurance_deduction,
                    'tax_brackets': []
                }
            }
        
        # 计算个税
        total_tax = 0
        bracket_details = []
        
        for bracket in self.tax_brackets:
            if taxable_income > bracket['min']:
                bracket_taxable = min(taxable_income - bracket['min'],
                                    bracket['max'] - bracket['min'])
                
                if bracket_taxable > 0:
                    bracket_tax = bracket_taxable * bracket['rate']
                    total_tax += bracket_tax
                    
                    bracket_details.append({
                        'bracket': f"NT${bracket['min']:,.0f}-NT${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })
        
        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': basic_allowance + labor_insurance_deduction + health_insurance_deduction,
            'breakdown': {
                'basic_allowance': basic_allowance,
                'labor_insurance_deduction': labor_insurance_deduction,
                'health_insurance_deduction': health_insurance_deduction,
                'tax_brackets': bracket_details
            }
        }

    def calculate_labor_insurance_contribution(self, monthly_salary: float) -> Dict:
        """计算劳保缴费金额"""
        # 劳保缴费基数上下限 (2024年)
        min_base = 26400   # 最低基数
        max_base = 45800   # 最高基数
        
        # 计算缴费基数
        contribution_base = max(min_base, min(monthly_salary, max_base))
        
        # 员工和雇主缴费
        employee_contribution = contribution_base * self.labor_insurance_rates['employee']
        employer_contribution = contribution_base * self.labor_insurance_rates['employer']
        
        return {
            'contribution_base': contribution_base,
            'employee': employee_contribution,
            'employer': employer_contribution,
            'total': employee_contribution + employer_contribution
        }

    def calculate_health_insurance_contribution(self, monthly_salary: float) -> Dict:
        """计算健保缴费金额"""
        # 健保缴费基数上下限 (2024年)
        min_base = 26400   # 最低基数
        max_base = 182000  # 最高基数
        
        # 计算缴费基数
        contribution_base = max(min_base, min(monthly_salary, max_base))
        
        # 员工和雇主缴费
        employee_contribution = contribution_base * self.health_insurance_rates['employee']
        employer_contribution = contribution_base * self.health_insurance_rates['employer']
        
        return {
            'contribution_base': contribution_base,
            'employee': employee_contribution,
            'employer': employer_contribution,
            'total': employee_contribution + employer_contribution
        }

class TaiwanComprehensiveAnalyzer:
    """台湾综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['TW']
        self.tax_calculator = TaiwanTaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 台湾退休年龄
        self.retirement_age = 65

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析台湾的情况"""
        print(f"\n{'='*80}")
        print(f"🇹🇼 台湾综合分析")
        print(f"月薪: {converter.format_amount(monthly_salary_cny, 'CNY')}")
        print(f"年增长率: 2.0%")
        print(f"工作年限: 35年 (30岁-65岁)")
        print(f"{'='*80}")

        # 1. 养老金分析
        self._analyze_pension(monthly_salary_cny)

        # 2. 收入分析（社保+个税+实际到手）
        self._analyze_income(monthly_salary_cny)

        # 3. 全生命周期总结
        self._analyze_lifetime_summary(monthly_salary_cny)

    def _analyze_pension(self, monthly_salary_cny: float):
        """分析养老金情况"""
        print(f"\n🏦 养老金分析")
        print("-" * 50)

        # 创建个人信息
        person = Person(
            name="测试用户",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(1995, 7, 1)
        )

        # 创建工资档案 - 工资每年增长2%
        salary_profile = SalaryProfile(
            base_salary=monthly_salary_cny,
            annual_growth_rate=0.02
        )

        # 创建经济因素
        economic_factors = EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.07,
            social_security_return_rate=0.05,
            base_currency="CNY",
            display_currency="TWD"
        )

        # 计算台湾养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'TWD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'TWD')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'TWD')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示缴费率信息
        contribution_rates = self.calculator.contribution_rates
        print(f"\n缴费率信息:")
        print(f"总缴费率: {contribution_rates['total']:.1%}")
        print(f"员工缴费率: {contribution_rates['employee']:.1%}")
        print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

    def _analyze_income(self, monthly_salary_cny: float):
        """分析收入情况（社保+个税+实际到手）"""
        print(f"\n💰 收入分析")
        print("-" * 50)

        # 转换月薪到新台币（假设1 CNY = 4.4 TWD）
        monthly_salary_twd = monthly_salary_cny * 4.4
        print(f"月薪 (TWD): {converter.format_amount(monthly_salary_twd, 'TWD')}")

        # 计算劳保和健保缴费详情
        labor_insurance = self.tax_calculator.calculate_labor_insurance_contribution(monthly_salary_twd)
        health_insurance = self.tax_calculator.calculate_health_insurance_contribution(monthly_salary_twd)

        print(f"\n劳保缴费详情:")
        print(f"员工缴费: {converter.format_amount(labor_insurance['employee'], 'TWD')}")
        print(f"雇主缴费: {converter.format_amount(labor_insurance['employer'], 'TWD')}")
        print(f"总劳保缴费: {converter.format_amount(labor_insurance['total'], 'TWD')}")

        print(f"\n健保缴费详情:")
        print(f"员工缴费: {converter.format_amount(health_insurance['employee'], 'TWD')}")
        print(f"雇主缴费: {converter.format_amount(health_insurance['employer'], 'TWD')}")
        print(f"总健保缴费: {converter.format_amount(health_insurance['total'], 'TWD')}")

        # 计算个人所得税
        annual_income = monthly_salary_twd * 12
        
        # 设置扣除项
        deductions = {
            'labor_insurance_contribution': labor_insurance['employee'] * 12,
            'health_insurance_contribution': health_insurance['employee'] * 12,
        }
        
        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)
        
        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income, 'TWD')}")
        print(f"劳保扣除: {converter.format_amount(deductions['labor_insurance_contribution'], 'TWD')}")
        print(f"健保扣除: {converter.format_amount(deductions['health_insurance_contribution'], 'TWD')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'TWD')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'TWD')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'TWD')}")

        # 计算实际到手金额
        monthly_labor = labor_insurance['employee']
        monthly_health = health_insurance['employee']
        monthly_tax = tax_result['total_tax'] / 12
        
        monthly_net_income = monthly_salary_twd - monthly_labor - monthly_health - monthly_tax
        effective_tax_rate = (tax_result['total_tax'] / annual_income * 100) if annual_income > 0 else 0
        
        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_twd, 'TWD')}")
        print(f"劳保: -{converter.format_amount(monthly_labor, 'TWD')}")
        print(f"健保: -{converter.format_amount(monthly_health, 'TWD')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'TWD')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'TWD')}")
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-65岁，35年)")
        print("-" * 50)

        # 计算35年的总收入
        total_income = 0
        total_labor = 0
        total_health = 0
        total_tax = 0
        total_net_income = 0
        
        for year in range(35):
            current_salary = monthly_salary_cny * (1.02 ** year) * 4.4 * 12  # 转换为新台币
            
            # 劳保和健保缴费
            monthly_labor = self.tax_calculator.calculate_labor_insurance_contribution(
                monthly_salary_cny * (1.02 ** year) * 4.4
            )['employee']
            monthly_health = self.tax_calculator.calculate_health_insurance_contribution(
                monthly_salary_cny * (1.02 ** year) * 4.4
            )['employee']
            
            annual_labor = monthly_labor * 12
            annual_health = monthly_health * 12
            
            # 个税
            deductions = {
                'labor_insurance_contribution': annual_labor,
                'health_insurance_contribution': annual_health,
            }
            annual_tax = self.tax_calculator.calculate_income_tax(current_salary, deductions)['total_tax']
            
            # 累计
            total_income += current_salary
            total_labor += annual_labor
            total_health += annual_health
            total_tax += annual_tax
            total_net_income += current_salary - annual_labor - annual_health - annual_tax

        print(f"35年总收入: {converter.format_amount(total_income, 'TWD')}")
        print(f"35年劳保缴费: {converter.format_amount(total_labor, 'TWD')}")
        print(f"35年健保缴费: {converter.format_amount(total_health, 'TWD')}")
        print(f"35年总个税: {converter.format_amount(total_tax, 'TWD')}")
        print(f"35年总净收入: {converter.format_amount(total_net_income, 'TWD')}")

        print(f"\n比例分析:")
        social_ratio = (total_labor + total_health) / total_income * 100 if total_income > 0 else 0
        tax_ratio = total_tax / total_income * 100 if total_income > 0 else 0
        net_ratio = total_net_income / total_income * 100 if total_income > 0 else 0
        
        print(f"社保占收入比例: {social_ratio:.1f}%")
        print(f"个税占收入比例: {tax_ratio:.1f}%")
        print(f"净收入占收入比例: {net_ratio:.1f}%")

        print(f"\n月平均值:")
        avg_monthly_income = total_income / (35 * 12)
        avg_monthly_social = (total_labor + total_health) / (35 * 12)
        avg_monthly_tax = total_tax / (35 * 12)
        avg_monthly_net = total_net_income / (35 * 12)
        
        print(f"平均月收入: {converter.format_amount(avg_monthly_income, 'TWD')}")
        print(f"平均月社保: {converter.format_amount(avg_monthly_social, 'TWD')}")
        print(f"平均月个税: {converter.format_amount(avg_monthly_tax, 'TWD')}")
        print(f"平均月净收入: {converter.format_amount(avg_monthly_net, 'TWD')}")

        print(f"\n{'='*80}")
