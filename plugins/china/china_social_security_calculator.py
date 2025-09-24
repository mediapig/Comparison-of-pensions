#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国社保计算器 - 2024年度最新参数
包含社保缴费、住房公积金、个人所得税等完整计算
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import date
from dataclasses import dataclass
import math


@dataclass
class ChinaSocialSecurityParams:
    """中国社保参数配置 - 2024年度"""
    
    # 社保缴费基数（2024年度）
    social_security_base_upper: float = 36921  # 上限 36921元/月
    social_security_base_lower: float = 7384   # 下限 7384元/月
    
    # 2025年度示例（用于未来滚动）
    social_security_base_upper_2025: float = 37302  # 上限 37302元/月
    social_security_base_lower_2025: float = 7460   # 下限 7460元/月
    
    # 社平工资
    avg_salary_2023: float = 12307  # 2023年社平 12307元/月
    avg_salary_2024: float = 12434  # 2024年社平 12434元/月
    avg_salary_growth_rate: float = 0.01  # 社平年增速默认1%
    
    # 单位缴费比例（2024年口径）
    employer_pension_rate: float = 0.16      # 养老 16%
    employer_medical_rate: float = 0.09      # 医疗（含生育）9%
    employer_unemployment_rate: float = 0.005 # 失业 0.5%
    employer_injury_rate: float = 0.0016    # 工伤 0.16%（默认档）
    
    # 个人缴费比例
    employee_pension_rate: float = 0.08      # 养老 8%
    employee_medical_rate: float = 0.02      # 医疗 2%
    employee_unemployment_rate: float = 0.005 # 失业 0.5%
    
    # 住房公积金（2024年度）
    housing_fund_base_upper: float = 36921   # 基数上限 36921元/月
    housing_fund_base_lower: float = 2690    # 基数下限 2690元/月
    housing_fund_rate_employer: float = 0.07 # 单位比例 7%
    housing_fund_rate_employee: float = 0.07 # 个人比例 7%
    housing_fund_supplement_rate: float = 0.0 # 补充公积金 0%（可配置）
    
    # 个人所得税
    personal_tax_basic_deduction: float = 60000  # 年度基本减除费用 60000元
    
    # 退休年龄
    retirement_age_male: int = 60    # 男 60岁
    retirement_age_female: int = 55   # 女 55岁
    
    # 渐进式延迟退休（可选）
    enable_delayed_retirement: bool = False
    retirement_age_male_delayed: int = 63  # 男逐步至 63岁
    retirement_age_female_delayed: int = 58 # 女至 58岁
    retirement_age_flexible_range: int = 3  # 弹性提前/延后±3年


@dataclass
class SocialSecurityContribution:
    """社保缴费明细"""
    # 缴费基数
    contribution_base: float
    
    # 单位缴费
    employer_pension: float
    employer_medical: float
    employer_unemployment: float
    employer_injury: float
    employer_total: float
    
    # 个人缴费
    employee_pension: float
    employee_medical: float
    employee_unemployment: float
    employee_total: float
    
    # 总缴费
    total_contribution: float


@dataclass
class HousingFundContribution:
    """住房公积金缴费明细"""
    contribution_base: float
    employer_contribution: float
    employee_contribution: float
    supplement_contribution: float
    total_contribution: float


@dataclass
class PersonalTaxResult:
    """个人所得税计算结果"""
    annual_income: float
    social_security_deduction: float
    housing_fund_deduction: float
    basic_deduction: float
    taxable_income: float
    tax_amount: float
    net_income: float
    effective_rate: float


@dataclass
class ChinaPensionResult:
    """中国养老金计算结果"""
    # 基础信息
    work_years: int
    retirement_age: int
    
    # 缴费情况
    total_employee_contributions: float
    total_employer_contributions: float
    total_contributions: float
    
    # 养老金计算
    basic_pension: float
    personal_account_pension: float
    monthly_pension: float
    annual_pension: float
    
    # 其他收益
    housing_fund_balance: float
    medical_account_balance: float
    
    # 财务分析
    total_benefits: float
    roi: float
    break_even_age: Optional[int]


class ChinaSocialSecurityCalculator:
    """中国社保计算器"""
    
    def __init__(self, params: Optional[ChinaSocialSecurityParams] = None):
        self.params = params or ChinaSocialSecurityParams()
        
        # 个人所得税税率表（2019版沿用至今）
        self.tax_brackets = [
            (0, 36000, 0.03, 0),           # 3%
            (36000, 144000, 0.10, 2520),   # 10%
            (144000, 300000, 0.20, 16920), # 20%
            (300000, 420000, 0.25, 31920), # 25%
            (420000, 660000, 0.30, 52920), # 30%
            (660000, 960000, 0.35, 85920), # 35%
            (960000, float('inf'), 0.45, 181920) # 45%
        ]
    
    def calculate_social_security_contribution(self, monthly_salary: float, year: int = 2024) -> SocialSecurityContribution:
        """计算社保缴费"""
        # 计算缴费基数（基于当年社平工资）
        avg_salary = self._get_avg_salary(year)
        base_upper = avg_salary * 3.0  # 300%
        base_lower = avg_salary * 0.6  # 60%
        
        # 确定实际缴费基数
        contribution_base = max(base_lower, min(monthly_salary, base_upper))
        
        # 单位缴费
        employer_pension = contribution_base * self.params.employer_pension_rate
        employer_medical = contribution_base * self.params.employer_medical_rate
        employer_unemployment = contribution_base * self.params.employer_unemployment_rate
        employer_injury = contribution_base * self.params.employer_injury_rate
        employer_total = employer_pension + employer_medical + employer_unemployment + employer_injury
        
        # 个人缴费
        employee_pension = contribution_base * self.params.employee_pension_rate
        employee_medical = contribution_base * self.params.employee_medical_rate
        employee_unemployment = contribution_base * self.params.employee_unemployment_rate
        employee_total = employee_pension + employee_medical + employee_unemployment
        
        return SocialSecurityContribution(
            contribution_base=contribution_base,
            employer_pension=employer_pension,
            employer_medical=employer_medical,
            employer_unemployment=employer_unemployment,
            employer_injury=employer_injury,
            employer_total=employer_total,
            employee_pension=employee_pension,
            employee_medical=employee_medical,
            employee_unemployment=employee_unemployment,
            employee_total=employee_total,
            total_contribution=employer_total + employee_total
        )
    
    def calculate_housing_fund_contribution(self, monthly_salary: float) -> HousingFundContribution:
        """计算住房公积金缴费"""
        # 确定缴费基数
        contribution_base = max(
            self.params.housing_fund_base_lower,
            min(monthly_salary, self.params.housing_fund_base_upper)
        )
        
        # 单位缴费
        employer_contribution = contribution_base * self.params.housing_fund_rate_employer
        
        # 个人缴费
        employee_contribution = contribution_base * self.params.housing_fund_rate_employee
        
        # 补充公积金
        supplement_contribution = contribution_base * self.params.housing_fund_supplement_rate
        
        return HousingFundContribution(
            contribution_base=contribution_base,
            employer_contribution=employer_contribution,
            employee_contribution=employee_contribution,
            supplement_contribution=supplement_contribution,
            total_contribution=employer_contribution + employee_contribution + supplement_contribution
        )
    
    def calculate_personal_tax(self, annual_income: float, 
                             social_security_deduction: float,
                             housing_fund_deduction: float) -> PersonalTaxResult:
        """计算个人所得税"""
        # 计算应税收入
        taxable_income = annual_income - social_security_deduction - housing_fund_deduction - self.params.personal_tax_basic_deduction
        
        # 计算税额
        tax_amount = 0
        if taxable_income > 0:
            for min_income, max_income, rate, deduction in self.tax_brackets:
                if min_income < taxable_income <= max_income:
                    tax_amount = taxable_income * rate - deduction
                    break
        
        # 计算净收入
        net_income = annual_income - social_security_deduction - housing_fund_deduction - tax_amount
        
        # 计算有效税率
        effective_rate = tax_amount / annual_income if annual_income > 0 else 0
        
        return PersonalTaxResult(
            annual_income=annual_income,
            social_security_deduction=social_security_deduction,
            housing_fund_deduction=housing_fund_deduction,
            basic_deduction=self.params.personal_tax_basic_deduction,
            taxable_income=taxable_income,
            tax_amount=tax_amount,
            net_income=net_income,
            effective_rate=effective_rate
        )
    
    def calculate_lifetime_pension(self, monthly_salary: float, start_age: int = 30, 
                                 retirement_age: int = 60, salary_growth_rate: float = 0.02) -> ChinaPensionResult:
        """计算终身养老金"""
        work_years = retirement_age - start_age
        
        # 累计缴费
        total_employee_contributions = 0
        total_employer_contributions = 0
        personal_account_balance = 0
        
        current_salary = monthly_salary
        
        for year_offset in range(work_years):
            year = 2024 + year_offset
            age = start_age + year_offset
            
            # 计算当年社保缴费
            ss_contribution = self.calculate_social_security_contribution(current_salary, year)
            
            # 累计缴费
            total_employee_contributions += ss_contribution.employee_total * 12
            total_employer_contributions += ss_contribution.employer_total * 12
            
            # 个人账户累计（养老8% + 医疗2%）
            personal_account_balance += (ss_contribution.employee_pension + ss_contribution.employee_medical) * 12
            
            # 薪资增长
            current_salary *= (1 + salary_growth_rate)
        
        # 计算养老金
        # 基础养老金 = (退休时社平工资 + 本人指数化月平均工资) / 2 × 缴费年限 × 1%
        avg_salary_at_retirement = self._get_avg_salary(2024 + work_years)
        indexed_avg_salary = avg_salary_at_retirement  # 简化计算
        basic_pension = (avg_salary_at_retirement + indexed_avg_salary) / 2 * work_years * 0.01
        
        # 个人账户养老金 = 个人账户储存额 / 计发月数
        # 60岁退休计发月数为139个月
        personal_account_pension = personal_account_balance / 139
        
        # 月养老金
        monthly_pension = basic_pension + personal_account_pension
        annual_pension = monthly_pension * 12
        
        # 其他收益
        housing_fund_balance = self._calculate_housing_fund_balance(monthly_salary, work_years, salary_growth_rate)
        medical_account_balance = self._calculate_medical_account_balance(monthly_salary, work_years, salary_growth_rate)
        
        # 总收益
        total_benefits = annual_pension * (90 - retirement_age) + housing_fund_balance + medical_account_balance
        
        # ROI计算
        roi = (total_benefits - total_employee_contributions) / total_employee_contributions if total_employee_contributions > 0 else 0
        
        # 回本年龄
        break_even_age = None
        if monthly_pension > 0:
            break_even_months = total_employee_contributions / (monthly_pension * 12)
            break_even_age = retirement_age + break_even_months
            if break_even_age > 90:
                break_even_age = None
        
        return ChinaPensionResult(
            work_years=work_years,
            retirement_age=retirement_age,
            total_employee_contributions=total_employee_contributions,
            total_employer_contributions=total_employer_contributions,
            total_contributions=total_employee_contributions + total_employer_contributions,
            basic_pension=basic_pension,
            personal_account_pension=personal_account_pension,
            monthly_pension=monthly_pension,
            annual_pension=annual_pension,
            housing_fund_balance=housing_fund_balance,
            medical_account_balance=medical_account_balance,
            total_benefits=total_benefits,
            roi=roi,
            break_even_age=break_even_age
        )
    
    def _get_avg_salary(self, year: int) -> float:
        """获取指定年份的社平工资"""
        if year <= 2023:
            return self.params.avg_salary_2023
        elif year == 2024:
            return self.params.avg_salary_2024
        else:
            # 基于2024年社平工资，按增长率推算
            years_from_2024 = year - 2024
            return self.params.avg_salary_2024 * ((1 + self.params.avg_salary_growth_rate) ** years_from_2024)
    
    def _calculate_housing_fund_balance(self, monthly_salary: float, work_years: int, 
                                       salary_growth_rate: float) -> float:
        """计算住房公积金余额"""
        total_balance = 0
        current_salary = monthly_salary
        
        for year_offset in range(work_years):
            hf_contribution = self.calculate_housing_fund_contribution(current_salary)
            # 住房公积金年利率约2.75%
            annual_rate = 0.0275
            total_balance += hf_contribution.total_contribution * 12 * ((1 + annual_rate) ** (work_years - year_offset))
            current_salary *= (1 + salary_growth_rate)
        
        return total_balance
    
    def _calculate_medical_account_balance(self, monthly_salary: float, work_years: int,
                                         salary_growth_rate: float) -> float:
        """计算医保账户余额"""
        total_balance = 0
        current_salary = monthly_salary
        
        for year_offset in range(work_years):
            ss_contribution = self.calculate_social_security_contribution(current_salary)
            # 医保个人账户（个人缴费2% + 单位缴费部分）
            medical_contribution = ss_contribution.employee_medical + ss_contribution.employer_medical * 0.3
            # 医保账户年利率约2%
            annual_rate = 0.02
            total_balance += medical_contribution * 12 * ((1 + annual_rate) ** (work_years - year_offset))
            current_salary *= (1 + salary_growth_rate)
        
        return total_balance
    
    def get_retirement_age(self, gender: str, birth_year: int) -> int:
        """获取退休年龄"""
        if self.params.enable_delayed_retirement:
            if gender.lower() == 'male':
                return self.params.retirement_age_male_delayed
            else:
                return self.params.retirement_age_female_delayed
        else:
            if gender.lower() == 'male':
                return self.params.retirement_age_male
            else:
                return self.params.retirement_age_female


# 便捷函数
def create_china_calculator(**kwargs) -> ChinaSocialSecurityCalculator:
    """创建中国社保计算器"""
    params = ChinaSocialSecurityParams(**kwargs)
    return ChinaSocialSecurityCalculator(params)


def calculate_china_pension(monthly_salary: float, start_age: int = 30, 
                           retirement_age: int = 60, salary_growth_rate: float = 0.02) -> ChinaPensionResult:
    """计算中国养老金"""
    calculator = create_china_calculator()
    return calculator.calculate_lifetime_pension(monthly_salary, start_age, retirement_age, salary_growth_rate)


if __name__ == "__main__":
    # 演示
    print("=== 中国社保计算器演示 ===\n")
    
    # 创建计算器
    calculator = create_china_calculator()
    
    # 测试案例：月薪15000元
    monthly_salary = 15000
    print(f"月薪: ¥{monthly_salary:,}")
    
    # 计算社保缴费
    ss_contribution = calculator.calculate_social_security_contribution(monthly_salary)
    print(f"\n=== 社保缴费 (2024年度) ===")
    print(f"缴费基数: ¥{ss_contribution.contribution_base:,.2f}")
    print(f"单位缴费: ¥{ss_contribution.employer_total:,.2f}/月")
    print(f"个人缴费: ¥{ss_contribution.employee_total:,.2f}/月")
    print(f"总缴费: ¥{ss_contribution.total_contribution:,.2f}/月")
    
    # 计算住房公积金
    hf_contribution = calculator.calculate_housing_fund_contribution(monthly_salary)
    print(f"\n=== 住房公积金 ===")
    print(f"缴费基数: ¥{hf_contribution.contribution_base:,.2f}")
    print(f"单位缴费: ¥{hf_contribution.employer_contribution:,.2f}/月")
    print(f"个人缴费: ¥{hf_contribution.employee_contribution:,.2f}/月")
    print(f"总缴费: ¥{hf_contribution.total_contribution:,.2f}/月")
    
    # 计算个人所得税
    annual_income = monthly_salary * 12
    tax_result = calculator.calculate_personal_tax(
        annual_income, 
        ss_contribution.employee_total * 12,
        hf_contribution.total_contribution * 12
    )
    print(f"\n=== 个人所得税 ===")
    print(f"年收入: ¥{tax_result.annual_income:,.2f}")
    print(f"社保扣除: ¥{tax_result.social_security_deduction:,.2f}")
    print(f"公积金扣除: ¥{tax_result.housing_fund_deduction:,.2f}")
    print(f"应纳税所得额: ¥{tax_result.taxable_income:,.2f}")
    print(f"税额: ¥{tax_result.tax_amount:,.2f}")
    print(f"净收入: ¥{tax_result.net_income:,.2f}")
    print(f"有效税率: {tax_result.effective_rate:.2%}")
    
    # 计算终身养老金
    pension_result = calculator.calculate_lifetime_pension(monthly_salary)
    print(f"\n=== 养老金计算 ===")
    print(f"工作年限: {pension_result.work_years}年")
    print(f"退休年龄: {pension_result.retirement_age}岁")
    print(f"总缴费: ¥{pension_result.total_contributions:,.2f}")
    print(f"月养老金: ¥{pension_result.monthly_pension:,.2f}")
    print(f"年养老金: ¥{pension_result.annual_pension:,.2f}")
    print(f"住房公积金余额: ¥{pension_result.housing_fund_balance:,.2f}")
    print(f"医保账户余额: ¥{pension_result.medical_account_balance:,.2f}")
    print(f"总收益: ¥{pension_result.total_benefits:,.2f}")
    print(f"ROI: {pension_result.roi:.2%}")
    if pension_result.break_even_age:
        print(f"回本年龄: {pension_result.break_even_age:.1f}岁")