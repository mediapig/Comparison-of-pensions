#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挪威插件 - 增强版，清晰的职责分离
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.enhanced_base_plugin import BaseCountryPlugin, PluginConfig, SocialSecurityType, SocialSecurityResult
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import NorwayConfig
from .tax_calculator import NorwayTaxCalculator
from .pension_calculator import NorwayPensionCalculator

class NorwayEnhancedPlugin(BaseCountryPlugin):
    """挪威插件 - 增强版"""

    COUNTRY_CODE = "NO"
    COUNTRY_NAME = "挪威"
    CURRENCY = "NOK"

    def __init__(self):
        super().__init__()
        self.tax_calculator = NorwayTaxCalculator()
        self.pension_calculator = NorwayPensionCalculator()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = NorwayConfig()
        return PluginConfig(
            country_code=self.COUNTRY_CODE,
            country_name=self.COUNTRY_NAME,
            currency=self.CURRENCY,
            retirement_ages=config.retirement_ages,
            tax_year=config.tax_year,
            supported_social_security_types=[
                SocialSecurityType.PENSION,      # 养老金
                SocialSecurityType.MEDICAL,       # 医疗保险
                SocialSecurityType.DISABILITY,    # 残疾保险
                SocialSecurityType.MATERNITY      # 生育保险
            ]
        )

    # ==================== 养老金计算 ====================
    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算退休金"""
        return self.pension_calculator.calculate_pension(person, salary_profile, economic_factors)

    def calculate_pension_contribution(self,
                                     monthly_salary: float,
                                     years: int,
                                     **kwargs) -> SocialSecurityResult:
        """计算养老金缴费"""
        # 挪威养老金缴费：员工8% + 雇主14%
        employee_rate = 0.08
        employer_rate = 0.14
        
        monthly_employee = monthly_salary * employee_rate
        monthly_employer = monthly_salary * employer_rate
        
        return SocialSecurityResult(
            employee_contribution=monthly_employee,
            employer_contribution=monthly_employer,
            total_contribution=monthly_employee + monthly_employer,
            coverage_type=SocialSecurityType.PENSION,
            details={
                'employee_rate': employee_rate,
                'employer_rate': employer_rate,
                'monthly_employee': monthly_employee,
                'monthly_employer': monthly_employer,
                'annual_employee': monthly_employee * 12,
                'annual_employer': monthly_employer * 12,
                'lifetime_employee': monthly_employee * 12 * years,
                'lifetime_employer': monthly_employer * 12 * years
            }
        )

    # ==================== 医疗保险计算 ====================
    def calculate_medical_contribution(self,
                                     monthly_salary: float,
                                     years: int,
                                     **kwargs) -> SocialSecurityResult:
        """计算医疗保险缴费"""
        # 挪威医疗保险：员工0% + 雇主8%
        employee_rate = 0.0
        employer_rate = 0.08
        
        monthly_employee = monthly_salary * employee_rate
        monthly_employer = monthly_salary * employer_rate
        
        return SocialSecurityResult(
            employee_contribution=monthly_employee,
            employer_contribution=monthly_employer,
            total_contribution=monthly_employee + monthly_employer,
            coverage_type=SocialSecurityType.MEDICAL,
            details={
                'employee_rate': employee_rate,
                'employer_rate': employer_rate,
                'monthly_employee': monthly_employee,
                'monthly_employer': monthly_employer,
                'note': '挪威医疗保险主要由雇主承担'
            }
        )

    # ==================== 税务计算 ====================
    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算个人所得税"""
        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)
        return {
            'total_tax': tax_result.get('total_tax', 0),
            'taxable_income': tax_result.get('taxable_income', 0),
            'effective_rate': self.tax_calculator.calculate_effective_tax_rate(annual_income, deductions),
            'net_income': self.tax_calculator.calculate_net_income(annual_income, deductions)
        }

    # ==================== 社保计算（兼容旧接口）====================
    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算社保缴费（兼容旧接口）"""
        # 计算养老金
        pension_result = self.calculate_pension_contribution(monthly_salary, years)
        
        # 计算医疗保险
        medical_result = self.calculate_medical_contribution(monthly_salary, years)
        
        # 合并结果
        total_employee = pension_result.employee_contribution + (medical_result.employee_contribution if medical_result else 0)
        total_employer = pension_result.employer_contribution + (medical_result.employer_contribution if medical_result else 0)
        
        return {
            'monthly_employee': total_employee,
            'monthly_employer': total_employer,
            'total_employee': total_employee * 12 * years,
            'total_employer': total_employer * 12 * years,
            'total_lifetime': (total_employee + total_employer) * 12 * years,
            'breakdown': {
                'pension': pension_result.details,
                'medical': medical_result.details if medical_result else None
            }
        }

    # ==================== 其他方法 ====================
    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        gender = person.gender.value if hasattr(person.gender, 'value') else person.gender
        return self.config.retirement_ages.get(gender.lower(), 67)

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """获取税率表"""
        return self.tax_calculator.get_tax_brackets()

    def get_contribution_rates(self) -> Dict[str, float]:
        """获取社保缴费率"""
        return {
            "pension_employee": 0.08,        # 养老金个人缴费 8%
            "pension_employer": 0.14,        # 养老金雇主缴费 14%
            "medical_employee": 0.0,         # 医疗保险个人缴费 0%
            "medical_employer": 0.08,        # 医疗保险雇主缴费 8%
            "total_employee": 0.08,          # 个人总缴费 8%
            "total_employer": 0.22           # 雇主总缴费 22%
        }

    def get_social_security_summary(self, monthly_salary: float, years: int) -> Dict[str, Any]:
        """获取社保汇总信息"""
        pension = self.calculate_pension_contribution(monthly_salary, years)
        medical = self.calculate_medical_contribution(monthly_salary, years)
        
        return {
            'pension': {
                'type': '养老金',
                'employee_rate': '8%',
                'employer_rate': '14%',
                'monthly_employee': pension.employee_contribution,
                'monthly_employer': pension.employer_contribution,
                'lifetime_total': pension.employee_contribution * 12 * years + pension.employer_contribution * 12 * years
            },
            'medical': {
                'type': '医疗保险',
                'employee_rate': '0%',
                'employer_rate': '8%',
                'monthly_employee': medical.employee_contribution if medical else 0,
                'monthly_employer': medical.employer_contribution if medical else 0,
                'lifetime_total': (medical.employee_contribution + medical.employer_contribution) * 12 * years if medical else 0,
                'note': '挪威医疗保险主要由雇主承担'
            },
            'total': {
                'monthly_employee': pension.employee_contribution + (medical.employee_contribution if medical else 0),
                'monthly_employer': pension.employer_contribution + (medical.employer_contribution if medical else 0),
                'lifetime_total': (pension.employee_contribution + pension.employer_contribution) * 12 * years + 
                                ((medical.employee_contribution + medical.employer_contribution) * 12 * years if medical else 0)
            }
        }