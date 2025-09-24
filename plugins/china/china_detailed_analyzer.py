#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国详细分析器
提供详细的中国社保分析输出
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount
from .china_social_security_calculator import ChinaSocialSecurityCalculator


class ChinaDetailedAnalyzer:
    """中国详细分析器"""

    def __init__(self):
        self.smart_converter = SmartCurrencyConverter()
        self.social_security_calculator = ChinaSocialSecurityCalculator()

    def print_detailed_analysis(self,
                               plugin,
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors,
                               pension_result: PensionResult,
                               local_amount: CurrencyAmount):
        """打印详细的中国社保分析"""

        # 生成JSON格式的分析结果
        analysis_data = self._generate_analysis_json(plugin, person, salary_profile, economic_factors, pension_result, local_amount)

        # 打印格式化的JSON
        import json

        # 格式化所有数字为2位小数
        formatted_data = self._format_decimals(analysis_data)
        print(json.dumps(formatted_data, ensure_ascii=False, indent=2))

    def _generate_analysis_json(self,
                               plugin,
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors,
                               pension_result: PensionResult,
                               local_amount: CurrencyAmount) -> dict:
        """生成JSON格式的分析结果"""

        # 基础信息
        start_age = person.age if person.age > 0 else 30
        retirement_age = 62  # 中国：62岁退休
        work_years = retirement_age - start_age

        # 计算第一年数据
        monthly_salary = salary_profile.monthly_salary

        # 社保缴费
        ss_contribution = self.social_security_calculator.calculate_social_security_contribution(monthly_salary)

        # 住房公积金
        hf_contribution = self.social_security_calculator.calculate_housing_fund_contribution(monthly_salary)

        # 个人所得税
        annual_income = monthly_salary * 12
        tax_result = self.social_security_calculator.calculate_personal_tax(
            annual_income,
            ss_contribution.employee_total * 12,
            hf_contribution.employee_contribution * 12  # 只扣除个人公积金缴费
        )

        # 计算工作期总计
        total_salary = 0
        total_ss_employee = 0
        total_ss_employer = 0
        total_hf_employee = 0
        total_hf_employer = 0
        total_tax = 0

        current_salary = monthly_salary
        for year_offset in range(work_years):
            year = 2024 + year_offset

            # 年度薪资
            annual_salary = current_salary * 12
            total_salary += annual_salary

            # 社保缴费
            ss_contrib = self.social_security_calculator.calculate_social_security_contribution(current_salary, year)
            total_ss_employee += ss_contrib.employee_total * 12
            total_ss_employer += ss_contrib.employer_total * 12

            # 住房公积金
            hf_contrib = self.social_security_calculator.calculate_housing_fund_contribution(current_salary)
            total_hf_employee += hf_contrib.employee_contribution * 12
            total_hf_employer += hf_contrib.employer_contribution * 12

            # 个人所得税
            tax_contrib = self.social_security_calculator.calculate_personal_tax(
                annual_salary,
                ss_contrib.employee_total * 12,
                hf_contrib.employee_contribution * 12  # 只扣除个人公积金缴费
            )
            total_tax += tax_contrib.tax_amount

            # 薪资增长
            current_salary *= (1 + salary_profile.annual_growth_rate)

        # 计算退休期数据
        retirement_years = 90 - retirement_age
        total_retirement_payout = pension_result.monthly_pension * 12 * retirement_years

        # 计算人民币对比
        monthly_pension_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(pension_result.monthly_pension, plugin.CURRENCY, ""),
            'CNY'
        )
        total_contribution_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(pension_result.total_contribution, plugin.CURRENCY, ""),
            'CNY'
        )

        return {
            "国家": "中国",
            "国家代码": "CN",
            "货币": "CNY",
            "分析时间": "2024年",
            "第一年分析": {
                "年龄": start_age,
                "收入情况": {
                    "年收入": annual_income,
                    "社保缴费基数": ss_contribution.contribution_base,
                    "年薪上限限制": monthly_salary > self.social_security_calculator.params.social_security_base_upper
                },
                "社保缴费": {
                    "雇员费率": (ss_contribution.employee_total / ss_contribution.contribution_base) * 100,
                    "雇主费率": (ss_contribution.employer_total / ss_contribution.contribution_base) * 100,
                    "总费率": (ss_contribution.total_contribution / ss_contribution.contribution_base) * 100,
                    "年缴费金额": ss_contribution.total_contribution * 12,
                    "雇员缴费": ss_contribution.employee_total * 12,
                    "雇主缴费": ss_contribution.employer_total * 12
                },
                "账户分配": {
                    "养老保险": ss_contribution.employee_pension * 12,
                    "医疗保险": ss_contribution.employee_medical * 12,
                    "失业保险": ss_contribution.employee_unemployment * 12
                },
                "住房公积金": {
                    "缴费基数": hf_contribution.contribution_base,
                    "单位缴费": hf_contribution.employer_contribution * 12,
                    "个人缴费": hf_contribution.employee_contribution * 12,
                    "总缴费": hf_contribution.total_contribution * 12
                },
                "税务情况": {
                    "应税收入": tax_result.taxable_income,
                    "所得税": tax_result.tax_amount,
                    "实际到手收入": tax_result.net_income
                }
            },
            "工作期总计": {
                "工作年限": work_years,
                "年龄范围": f"{start_age}-{retirement_age-1}岁",
                "收入情况": {
                    "总收入": total_salary,
                    "总税费": total_tax,
                    "实际到手收入": total_salary - total_ss_employee - total_hf_employee - total_tax
                },
                "社保缴费总计": {
                    "雇员缴费": total_ss_employee,
                    "雇主缴费": total_ss_employer,
                    "总缴费": total_ss_employee + total_ss_employer
                },
                "住房公积金总计": {
                    "雇员缴费": total_hf_employee,
                    "雇主缴费": total_hf_employer,
                    "总缴费": total_hf_employee + total_hf_employer
                }
            },
            "退休期分析": {
                "年龄范围": f"{retirement_age}-90岁",
                "退休年限": retirement_years,
                "退休金收入": {
                    "月领取金额": pension_result.monthly_pension,
                    "年领取金额": pension_result.monthly_pension * 12,
                    "退休期总领取": total_retirement_payout
                }
            },
            "投资回报分析": {
                "简单回报率": pension_result.roi,
                "内部收益率_IRR": pension_result.details.get('irr', pension_result.roi),
                "回本分析": {
                    "回本年龄": pension_result.break_even_age,
                    "回本时间": pension_result.break_even_age - retirement_age if pension_result.break_even_age else None,
                    "能否回本": 1 if pension_result.break_even_age else 0
                }
            },
            "人民币对比": {
                "退休金收入": {
                    "月退休金": monthly_pension_cny.amount
                },
                "缴费情况": {
                    "总缴费": total_contribution_cny.amount
                }
            }
        }

    def _format_decimals(self, data: Any) -> Any:
        """格式化数字为2位小数"""
        if isinstance(data, dict):
            return {key: self._format_decimals(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._format_decimals(item) for item in data]
        elif isinstance(data, float):
            return round(data, 2)
        else:
            return data