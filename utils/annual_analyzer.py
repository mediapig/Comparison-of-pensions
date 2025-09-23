#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
年度详细分析器
提供每年的收入、扣税、社保缴费明细，以及累计统计和回报率分析
"""

from typing import Dict, List, Any, Optional
from datetime import date
from dataclasses import dataclass
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.plugin_manager import plugin_manager
from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount


@dataclass
class AnnualData:
    """年度数据"""
    year: int
    age: int
    annual_income: float
    annual_tax: float
    annual_social_security_employee: float
    annual_social_security_employer: float
    annual_medical_employee: float
    annual_medical_employer: float
    annual_net_income: float
    monthly_salary: float
    monthly_tax: float
    monthly_social_security_employee: float
    monthly_social_security_employer: float
    monthly_medical_employee: float
    monthly_medical_employer: float
    monthly_net_income: float
    currency: str


@dataclass
class CumulativeStats:
    """累计统计"""
    total_income: float
    total_tax: float
    total_social_security_employee: float
    total_social_security_employer: float
    total_social_security_total: float
    total_medical_employee: float
    total_medical_employer: float
    total_medical_total: float
    total_net_income: float
    currency: str


@dataclass
class RetirementAnalysis:
    """退休分析"""
    monthly_pension: float
    total_contribution: float
    total_benefit: float
    roi_percentage: float
    break_even_age: Optional[int]
    currency: str


@dataclass
class AnnualAnalysisResult:
    """年度分析结果"""
    country_code: str
    country_name: str
    currency: str
    annual_data: List[AnnualData]
    cumulative_stats: CumulativeStats
    retirement_analysis: RetirementAnalysis
    work_years: int
    retirement_age: int
    start_age: int


class AnnualAnalyzer:
    """年度详细分析器"""

    def __init__(self):
        self.plugin_manager = plugin_manager
        self.smart_converter = SmartCurrencyConverter()

    def analyze_country(self, 
                       country_code: str, 
                       currency_amount: CurrencyAmount,
                       start_age: int = 30,
                       retirement_age: Optional[int] = None) -> AnnualAnalysisResult:
        """
        分析指定国家的年度详细数据
        
        Args:
            country_code: 国家代码
            currency_amount: 初始薪资（支持多货币）
            start_age: 开始工作年龄
            retirement_age: 退休年龄（None则使用默认）
            
        Returns:
            年度分析结果
        """
        plugin = self.plugin_manager.get_plugin(country_code)
        if not plugin:
            raise ValueError(f"未找到国家 {country_code} 的插件")

        # 转换为本地货币
        local_amount = self.smart_converter.convert_to_local(currency_amount, plugin.CURRENCY)
        
        # 判断输入是年薪还是月薪（如果金额很大，可能是年薪）
        if local_amount.amount > 50000:  # 如果超过5万，假设是年薪
            initial_monthly_salary = local_amount.amount / 12
        else:
            initial_monthly_salary = local_amount.amount
        
        # 创建测试数据
        person = Person(
            name="分析用户",
            birth_date=date(2024 - start_age, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(2024 - start_age, 1, 1)
        )

        # 获取退休年龄
        if retirement_age is None:
            retirement_age = plugin.get_retirement_age(person)

        work_years = retirement_age - start_age
        if work_years <= 0:
            work_years = 1

        # 计算年度数据
        annual_data = self._calculate_annual_data(
            plugin, person, initial_monthly_salary, start_age, retirement_age
        )

        # 计算累计统计
        cumulative_stats = self._calculate_cumulative_stats(annual_data, plugin.CURRENCY)

        # 计算退休分析
        retirement_analysis = self._calculate_retirement_analysis(
            plugin, person, initial_monthly_salary, work_years, plugin.CURRENCY
        )

        return AnnualAnalysisResult(
            country_code=country_code,
            country_name=plugin.COUNTRY_NAME,
            currency=plugin.CURRENCY,
            annual_data=annual_data,
            cumulative_stats=cumulative_stats,
            retirement_analysis=retirement_analysis,
            work_years=work_years,
            retirement_age=retirement_age,
            start_age=start_age
        )

    def _calculate_annual_data(self, 
                               plugin, 
                               person: Person, 
                               initial_monthly_salary: float,
                               start_age: int,
                               retirement_age: int) -> List[AnnualData]:
        """计算年度详细数据"""
        annual_data = []
        work_years = retirement_age - start_age
        
        # 工资增长率（假设3%）
        salary_growth_rate = 0.03
        
        current_monthly_salary = initial_monthly_salary
        
        for year_offset in range(retirement_age - start_age):
            current_year = 2024 + year_offset
            current_age = start_age + year_offset
            
            # 计算年收入
            annual_income = current_monthly_salary * 12
            
            # 计算社保（传递年龄信息）
            ss_result = plugin.calculate_social_security(current_monthly_salary, 1, age=current_age)
            monthly_ss_employee = ss_result.get('monthly_employee', 0)
            monthly_ss_employer = ss_result.get('monthly_employer', 0)
            annual_ss_employee = monthly_ss_employee * 12
            annual_ss_employer = monthly_ss_employer * 12
            
            # 计算医保（从CPF breakdown中提取MA账户）
            annual_medical_employee = 0
            annual_medical_employer = 0
            if 'cpf_breakdown' in ss_result:
                cpf_breakdown = ss_result['cpf_breakdown']
                # MA账户的年度缴费
                if 'ma_total' in cpf_breakdown:
                    # 这里应该计算当年的MA缴费，而不是总缴费除以年限
                    # 使用CPF计算器计算当年的MA缴费
                    if hasattr(plugin, 'cpf_calculator'):
                        contribution = plugin.cpf_calculator.calculate_cpf_split(
                            current_monthly_salary, current_age
                        )
                        annual_medical_employee = contribution.ma_contribution * 12
                        annual_medical_employer = contribution.ma_contribution * 12
            
            # 计算个税（考虑社保扣除）
            # 对于新加坡，传递CPF缴费信息
            deductions = {}
            if hasattr(plugin, 'cpf_calculator'):
                # 新加坡CPF缴费可以作为税务减免
                deductions['cpf_contribution'] = annual_ss_employee
            
            tax_result = plugin.calculate_tax(annual_income, deductions)
            annual_tax = tax_result.get('total_tax', 0)
            
            # 计算净收入
            annual_net_income = annual_income - annual_ss_employee - annual_tax
            monthly_net_income = annual_net_income / 12
            
            annual_data.append(AnnualData(
                year=current_year,
                age=current_age,
                annual_income=annual_income,
                annual_tax=annual_tax,
                annual_social_security_employee=annual_ss_employee,
                annual_social_security_employer=annual_ss_employer,
                annual_medical_employee=annual_medical_employee,
                annual_medical_employer=annual_medical_employer,
                annual_net_income=annual_net_income,
                monthly_salary=current_monthly_salary,
                monthly_tax=annual_tax / 12,
                monthly_social_security_employee=monthly_ss_employee,
                monthly_social_security_employer=monthly_ss_employer,
                monthly_medical_employee=annual_medical_employee / 12,
                monthly_medical_employer=annual_medical_employer / 12,
                monthly_net_income=monthly_net_income,
                currency=plugin.CURRENCY
            ))
            
            # 下一年工资增长
            current_monthly_salary *= (1 + salary_growth_rate)
        
        return annual_data

    def _calculate_cumulative_stats(self, 
                                   annual_data: List[AnnualData], 
                                   currency: str) -> CumulativeStats:
        """计算累计统计"""
        total_income = sum(data.annual_income for data in annual_data)
        total_tax = sum(data.annual_tax for data in annual_data)
        total_ss_employee = sum(data.annual_social_security_employee for data in annual_data)
        total_ss_employer = sum(data.annual_social_security_employer for data in annual_data)
        total_medical_employee = sum(data.annual_medical_employee for data in annual_data)
        total_medical_employer = sum(data.annual_medical_employer for data in annual_data)
        total_net_income = sum(data.annual_net_income for data in annual_data)
        
        return CumulativeStats(
            total_income=total_income,
            total_tax=total_tax,
            total_social_security_employee=total_ss_employee,
            total_social_security_employer=total_ss_employer,
            total_social_security_total=total_ss_employee + total_ss_employer,
            total_medical_employee=total_medical_employee,
            total_medical_employer=total_medical_employer,
            total_medical_total=total_medical_employee + total_medical_employer,
            total_net_income=total_net_income,
            currency=currency
        )

    def _calculate_retirement_analysis(self, 
                                     plugin, 
                                     person: Person, 
                                     monthly_salary: float,
                                     work_years: int,
                                     currency: str) -> RetirementAnalysis:
        """计算退休分析"""
        # 创建薪资档案
        salary_profile = SalaryProfile(
            monthly_salary=monthly_salary,
            annual_growth_rate=0.03,
            contribution_start_age=person.age
        )

        # 创建经济因素
        economic_factors = EconomicFactors(
            inflation_rate=0.02,
            investment_return_rate=0.05,
            social_security_return_rate=0.03
        )

        # 计算退休金
        pension_result = plugin.calculate_pension(person, salary_profile, economic_factors)
        
        return RetirementAnalysis(
            monthly_pension=pension_result.monthly_pension,
            total_contribution=pension_result.total_contribution,
            total_benefit=pension_result.total_benefit,
            roi_percentage=pension_result.roi,
            break_even_age=pension_result.break_even_age,
            currency=currency
        )

    def format_currency(self, amount: float, currency: str) -> str:
        """格式化货币显示"""
        return self.smart_converter.format_amount(CurrencyAmount(amount, currency, ""))

    def print_annual_analysis(self, result: AnnualAnalysisResult, show_yearly_detail: bool = True):
        """打印年度分析结果"""
        print(f"\n=== 📊 {result.country_name} ({result.country_code}) 年度详细分析 ===")
        print(f"工作年限: {result.start_age}岁 - {result.retirement_age}岁 ({result.work_years}年)")
        print(f"货币: {result.currency}")
        
        if show_yearly_detail:
            print(f"\n📅 年度明细:")
            print(f"{'年份':<6} {'年龄':<4} {'年收入':<12} {'年个税':<12} {'年社保(员工)':<12} {'年社保(雇主)':<12} {'年医保(员工)':<12} {'年医保(雇主)':<12} {'年净收入':<12}")
            print("-" * 100)
            
            for data in result.annual_data:
                print(f"{data.year:<6} {data.age:<4} "
                      f"{self.format_currency(data.annual_income, data.currency):<12} "
                      f"{self.format_currency(data.annual_tax, data.currency):<12} "
                      f"{self.format_currency(data.annual_social_security_employee, data.currency):<12} "
                      f"{self.format_currency(data.annual_social_security_employer, data.currency):<12} "
                      f"{self.format_currency(data.annual_medical_employee, data.currency):<12} "
                      f"{self.format_currency(data.annual_medical_employer, data.currency):<12} "
                      f"{self.format_currency(data.annual_net_income, data.currency):<12}")
        
        # 累计统计
        print(f"\n💰 累计统计 ({result.work_years}年):")
        print(f"  总收入: {self.format_currency(result.cumulative_stats.total_income, result.currency)}")
        print(f"  总个税: {self.format_currency(result.cumulative_stats.total_tax, result.currency)}")
        print(f"  总社保(员工): {self.format_currency(result.cumulative_stats.total_social_security_employee, result.currency)}")
        print(f"  总社保(雇主): {self.format_currency(result.cumulative_stats.total_social_security_employer, result.currency)}")
        print(f"  总社保(合计): {self.format_currency(result.cumulative_stats.total_social_security_total, result.currency)}")
        print(f"  总医保(员工): {self.format_currency(result.cumulative_stats.total_medical_employee, result.currency)}")
        print(f"  总医保(雇主): {self.format_currency(result.cumulative_stats.total_medical_employer, result.currency)}")
        print(f"  总医保(合计): {self.format_currency(result.cumulative_stats.total_medical_total, result.currency)}")
        print(f"  总净收入: {self.format_currency(result.cumulative_stats.total_net_income, result.currency)}")
        
        # 退休分析
        print(f"\n🏦 退休分析:")
        print(f"  月退休金: {self.format_currency(result.retirement_analysis.monthly_pension, result.currency)}")
        print(f"  总缴费: {self.format_currency(result.retirement_analysis.total_contribution, result.currency)}")
        print(f"  总收益: {self.format_currency(result.retirement_analysis.total_benefit, result.currency)}")
        print(f"  回报率: {result.retirement_analysis.roi_percentage:.2f}%")
        if result.retirement_analysis.break_even_age:
            print(f"  回本年龄: {result.retirement_analysis.break_even_age}岁")
        
        # 社保投资回报分析
        print(f"\n📈 社保投资回报分析:")
        total_ss_investment = result.cumulative_stats.total_social_security_employee
        monthly_pension_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(result.retirement_analysis.monthly_pension, result.currency, ""), 
            'CNY'
        )
        annual_pension_cny = monthly_pension_cny.amount * 12
        
        # 假设退休后活到85岁
        retirement_years = 85 - result.retirement_age
        total_pension_benefit = annual_pension_cny * retirement_years
        
        ss_roi = ((total_pension_benefit - total_ss_investment) / total_ss_investment * 100) if total_ss_investment > 0 else 0
        
        print(f"  社保投入(员工): {self.format_currency(total_ss_investment, result.currency)}")
        print(f"  退休后总收益: {self.format_currency(total_pension_benefit, result.currency)}")
        print(f"  社保ROI: {ss_roi:.2f}%")
        
        # 计算回本年限
        if annual_pension_cny > 0:
            payback_years = total_ss_investment / annual_pension_cny
            payback_age = result.retirement_age + payback_years
            print(f"  回本年限: {payback_years:.1f}年 (到{payback_age:.0f}岁)")
        
        # 人民币对比
        print(f"\n💱 人民币对比:")
        total_income_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(result.cumulative_stats.total_income, result.currency, ""), 
            'CNY'
        )
        total_tax_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(result.cumulative_stats.total_tax, result.currency, ""), 
            'CNY'
        )
        total_ss_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(result.cumulative_stats.total_social_security_total, result.currency, ""), 
            'CNY'
        )
        
        print(f"  总收入: {self.smart_converter.format_amount(total_income_cny)}")
        print(f"  总个税: {self.smart_converter.format_amount(total_tax_cny)}")
        print(f"  总社保: {self.smart_converter.format_amount(total_ss_cny)}")
        print(f"  月退休金: {self.smart_converter.format_amount(monthly_pension_cny)}")