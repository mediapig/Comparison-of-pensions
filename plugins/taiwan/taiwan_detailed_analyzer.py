#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾详细分析器
提供台湾劳保、健保、税收的全面分析
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount


class TaiwanDetailedAnalyzer:
    """台湾详细分析器"""

    def __init__(self):
        self.smart_converter = SmartCurrencyConverter()

    def print_detailed_analysis(self,
                               plugin,
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors,
                               pension_result: PensionResult,
                               local_amount: CurrencyAmount):
        """打印详细的台湾分析"""

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

        # 基本参数
        start_age = person.age
        retirement_age = 65
        work_years = retirement_age - start_age
        monthly_salary = salary_profile.monthly_salary
        annual_salary = monthly_salary * 12

        # 获取统一的汇率进行转换（确保报表内汇率一致）
        rate_info = self.smart_converter.daily_cache.get_rate_info("TWD", "CNY")
        twd_to_cny_rate = rate_info['exchange_rate']
        monthly_salary_cny = monthly_salary * twd_to_cny_rate
        annual_salary_cny = monthly_salary_cny * 12

        # 计算劳保
        labor_insurance = self._calculate_labor_insurance(monthly_salary, work_years)

        # 计算健保
        health_insurance = self._calculate_health_insurance(monthly_salary, work_years)

        # 计算劳工退休金
        labor_pension = self._calculate_labor_pension(monthly_salary, work_years)

        # 计算个人所得税（扣除员工自提劳退）
        employee_labor_pension_annual = labor_pension['employee_annual']
        income_tax = self._calculate_income_tax(annual_salary, employee_labor_pension_annual)

        # 计算劳保年金
        labor_annuity = self._calculate_labor_annuity(monthly_salary, work_years)

        # 计算劳工退休金月领取金额（基于账户余额）
        labor_pension_monthly = self._calculate_labor_pension_monthly(labor_pension['total_lifetime'])

        # 计算总缴费和收益
        total_employee_contribution = (labor_insurance['employee_total'] +
                                     health_insurance['employee_total'] +
                                     labor_pension['employee_total'])

        total_employer_contribution = (labor_insurance['employer_total'] +
                                     health_insurance['employer_total'] +
                                     labor_pension['employer_total'])

        # 计算退休期分析
        retirement_years = 90 - retirement_age

        # 使用统一的汇率进行转换（确保与年收入使用相同汇率）
        monthly_pension_cny = pension_result.monthly_pension * twd_to_cny_rate

        # 计算总缴费的人民币金额（使用相同的汇率）
        total_employee_contribution_cny = total_employee_contribution * twd_to_cny_rate

        return {
            "基础信息": {
                "国家": "台湾",
                "货币": "TWD",
                "分析时间": "2025-01-01 00:00:00",
                "姓名": "台湾用户",
                "年龄": start_age,
                "工作年限": f"{start_age}-{retirement_age-1}岁",
                "退休年龄": retirement_age,
                "退休年限": retirement_years
            },
            "收入信息": {
                "月收入": self._format_number(monthly_salary),
                "年收入": self._format_number(annual_salary),
                "年收入_人民币": self._format_number(annual_salary_cny),
                "年薪上限限制": False
            },
            "劳工保险缴费": {
                "费率": "12% (雇主70% + 员工20% + 政府10%)",
                "投保薪资上限": "45,800 TWD/月",
                "实际投保薪资": self._format_number(min(monthly_salary, 45800)),
                "年度缴费": {
                    "员工缴费": self._format_number(labor_insurance['employee_annual']),
                    "雇主缴费": self._format_number(labor_insurance['employer_annual']),
                    "政府缴费": self._format_number(labor_insurance['government_annual']),
                    "总缴费(含政府)": self._format_number(labor_insurance['total_annual_with_gov']),
                    "总缴费(不含政府)": self._format_number(labor_insurance['total_annual'])
                },
                "终身缴费": {
                    "员工缴费": self._format_number(labor_insurance['employee_total']),
                    "雇主缴费": self._format_number(labor_insurance['employer_total']),
                    "政府缴费": self._format_number(labor_insurance['government_total']),
                    "总缴费(含政府)": self._format_number(labor_insurance['total_lifetime_with_gov']),
                    "总缴费(不含政府)": self._format_number(labor_insurance['total_lifetime'])
                }
            },
            "全民健康保险缴费": {
                "费率": "5.17% (雇主60% + 员工30% + 政府10%)",
                "投保薪资上限": "182,000 TWD/月",
                "实际投保薪资": self._format_number(min(monthly_salary, 182000)),
                "年度缴费": {
                    "员工缴费": self._format_number(health_insurance['employee_annual']),
                    "雇主缴费": self._format_number(health_insurance['employer_annual']),
                    "总缴费": self._format_number(health_insurance['total_annual'])
                },
                "终身缴费": {
                    "员工缴费": self._format_number(health_insurance['employee_total']),
                    "雇主缴费": self._format_number(health_insurance['employer_total']),
                    "总缴费": self._format_number(health_insurance['total_lifetime'])
                }
            },
            "劳工退休金缴费": {
                "雇主缴费率": "6%",
                "员工自愿缴费率": "0-6% (假设3%)",
                "年度缴费": {
                    "员工缴费": self._format_number(labor_pension['employee_annual']),
                    "雇主缴费": self._format_number(labor_pension['employer_annual']),
                    "总缴费": self._format_number(labor_pension['total_annual'])
                },
                "终身缴费": {
                    "员工缴费": self._format_number(labor_pension['employee_total']),
                    "雇主缴费": self._format_number(labor_pension['employer_total']),
                    "总缴费": self._format_number(labor_pension['total_lifetime'])
                }
            },
            "税务情况": {
                "应税收入": self._format_number(income_tax['taxable_income']),
                "所得税": self._format_number(income_tax['total_tax']),
                "扣除明细": {
                    "免税额": self._format_number(income_tax['exemption']),
                    "标准扣除额": self._format_number(income_tax['standard_deduction']),
                    "薪资所得特别扣除额": self._format_number(income_tax['salary_deduction']),
                    "员工自提劳退扣除": self._format_number(income_tax['labor_pension_deduction']),
                    "总扣除额": self._format_number(income_tax['total_deductions'])
                },
                "实际到手收入": self._format_number(income_tax['net_income']),
                "税务口径说明": "员工自提劳退已纳入税前扣除；劳保/健保个人缴费未纳入列举扣除"
            },
            "退休金计算": {
                "劳保年金": {
                    "月领取金额": self._format_number(labor_annuity['monthly_pension']),
                    "年领取金额": self._format_number(labor_annuity['annual_pension']),
                    "退休期总领取": self._format_number(labor_annuity['total_benefit']),
                    "计算公式说明": "月平均投保薪资 × 年资 × 1.55% × 0.775(65岁退休调整系数)"
                },
                "劳工退休金": {
                    "月领取金额": self._format_number(labor_pension_monthly),
                    "年领取金额": self._format_number(labor_pension_monthly * 12),
                    "退休期总领取": self._format_number(labor_pension_monthly * 12 * 25)
                },
                "总退休金": {
                    "月领取金额": self._format_number(labor_annuity['monthly_pension'] + labor_pension_monthly),
                    "年领取金额": self._format_number((labor_annuity['monthly_pension'] + labor_pension_monthly) * 12),
                    "退休期总领取": self._format_number(labor_annuity['total_benefit'] + labor_pension_monthly * 12 * 25)
                }
            },
            "工作期总计": {
                "总工作年限": work_years,
                "总收入": self._format_number(annual_salary * work_years),
                "劳工保险": {
                    "员工缴费": self._format_number(labor_insurance['employee_total']),
                    "雇主缴费": self._format_number(labor_insurance['employer_total'])
                },
                "全民健康保险": {
                    "员工缴费": self._format_number(health_insurance['employee_total']),
                    "雇主缴费": self._format_number(health_insurance['employer_total'])
                },
                "劳工退休金缴费": {
                    "员工缴费": self._format_number(labor_pension['employee_total']),
                    "雇主缴费": self._format_number(labor_pension['employer_total'])
                },
                "个人投资缴费": self._format_number(total_employee_contribution),
                "个人投资占比": f"{self._format_number((total_employee_contribution / (annual_salary * work_years)) * 100)}%",
                "个人投资占比说明": "个人(员工)缴费 / 税前收入 × 100%"
            },
            "退休期分析": {
                "年龄范围": f"{retirement_age}-90岁",
                "退休年限": retirement_years,
                "退休金收入": {
                    "月领取金额": self._format_number(labor_annuity['monthly_pension'] + labor_pension_monthly),
                    "年领取金额": self._format_number((labor_annuity['monthly_pension'] + labor_pension_monthly) * 12),
                    "退休期总领取": self._format_number(labor_annuity['total_benefit'] + labor_pension_monthly * 12 * 25)
                }
            },
            "投资回报分析": {
                "说明": "仅计算劳工退休金的投资回报，劳保年金为现收现付制",
                "个人投资投入": self._format_number(labor_pension['employee_total']),
                "个人投资产出": self._format_number(labor_pension_monthly * 12 * 25),
                "净收益": self._format_number(labor_pension_monthly * 12 * 25 - labor_pension['employee_total']),
                "投资回报率": self._format_number(((labor_pension_monthly * 12 * 25 / labor_pension['employee_total']) - 1) * 100),
                "回本年龄": self._format_number(retirement_age + (labor_pension['employee_total'] / (labor_pension_monthly * 12))),
                "回本时间": self._format_number(labor_pension['employee_total'] / (labor_pension_monthly * 12)),
                "替代率": self._format_number(((labor_annuity['monthly_pension'] + labor_pension_monthly) * 12 / annual_salary) * 100),
                "年化投资回报率": "2.0%",
                "工作期投资回报": self._format_number(labor_pension['employee_total'] * ((1.02 ** 35) - 1))
            },
            "三支柱详细分析": {
                "劳工保险": {
                    "制度名称": "劳工保险",
                    "覆盖范围": "在职劳工",
                    "缴费方式": "雇主70% + 员工20% + 政府10%",
                    "给付方式": "现收现付制，提供老年给付",
                    "特点": "强制性社会保险，提供基本保障"
                },
                "全民健康保险": {
                    "制度名称": "全民健康保险",
                    "覆盖范围": "全体国民",
                    "缴费方式": "雇主60% + 员工30% + 政府10%",
                    "给付方式": "现收现付制，提供医疗给付",
                    "特点": "强制性医疗保险，提供基本医疗"
                },
                "劳工退休金": {
                    "制度名称": "劳工退休金",
                    "覆盖范围": "在职劳工",
                    "缴费方式": "雇主6% + 员工自愿0-6%",
                    "给付方式": "个人账户制，退休后领取",
                    "特点": "个人账户制，可携带，有投资回报"
                }
            },
            "人民币对比": {
                "月退休金": self._format_number(monthly_pension_cny),
                "年退休金": self._format_number(monthly_pension_cny * 12),
                "总缴费": self._format_number(total_employee_contribution_cny),
                "说明": "基于统一汇率转换，确保报表内汇率一致"
            }
        }

    def _calculate_labor_insurance(self, monthly_salary: float, work_years: int) -> Dict[str, float]:
        """计算劳工保险"""
        # 投保薪资上限（劳保上限45,800/月）
        max_insured_salary = min(monthly_salary, 45800)

        # 费率
        total_rate = 0.12  # 12%
        employee_rate = 0.20  # 员工20%
        employer_rate = 0.70  # 雇主70%
        government_rate = 0.10  # 政府10%

        # 年度缴费
        employee_annual = max_insured_salary * total_rate * employee_rate * 12
        employer_annual = max_insured_salary * total_rate * employer_rate * 12
        government_annual = max_insured_salary * total_rate * government_rate * 12
        total_annual = employee_annual + employer_annual
        total_annual_with_gov = total_annual + government_annual

        # 终身缴费
        employee_total = employee_annual * work_years
        employer_total = employer_annual * work_years
        government_total = government_annual * work_years
        total_lifetime = employee_total + employer_total
        total_lifetime_with_gov = total_lifetime + government_total

        return {
            'employee_annual': round(employee_annual, 2),
            'employer_annual': round(employer_annual, 2),
            'government_annual': round(government_annual, 2),
            'total_annual': round(total_annual, 2),
            'total_annual_with_gov': round(total_annual_with_gov, 2),
            'employee_total': round(employee_total, 2),
            'employer_total': round(employer_total, 2),
            'government_total': round(government_total, 2),
            'total_lifetime': round(total_lifetime, 2),
            'total_lifetime_with_gov': round(total_lifetime_with_gov, 2)
        }

    def _calculate_health_insurance(self, monthly_salary: float, work_years: int) -> Dict[str, float]:
        """计算全民健康保险"""
        # 投保薪资上限
        max_insured_salary = min(monthly_salary, 182000)

        # 费率
        total_rate = 0.0517  # 5.17%
        employee_rate = 0.30  # 员工30%
        employer_rate = 0.60  # 雇主60%

        # 年度缴费
        employee_annual = max_insured_salary * total_rate * employee_rate * 12
        employer_annual = max_insured_salary * total_rate * employer_rate * 12
        total_annual = employee_annual + employer_annual

        # 终身缴费
        employee_total = employee_annual * work_years
        employer_total = employer_annual * work_years
        total_lifetime = employee_total + employer_total

        return {
            'employee_annual': employee_annual,
            'employer_annual': employer_annual,
            'total_annual': total_annual,
            'employee_total': employee_total,
            'employer_total': employer_total,
            'total_lifetime': total_lifetime
        }

    def _calculate_labor_pension(self, monthly_salary: float, work_years: int) -> Dict[str, float]:
        """计算劳工退休金"""
        # 提缴薪资上限（劳退上限150,000/月）
        max_contribution_salary = min(monthly_salary, 150000)

        # 雇主缴费率
        employer_rate = 0.06  # 6%
        # 员工自愿缴费率（假设3%）
        employee_rate = 0.03  # 3%

        # 年度缴费
        employee_annual = max_contribution_salary * employee_rate * 12
        employer_annual = max_contribution_salary * employer_rate * 12
        total_annual = employee_annual + employer_annual

        # 终身缴费
        employee_total = employee_annual * work_years
        employer_total = employer_annual * work_years
        total_lifetime = employee_total + employer_total

        return {
            'employee_annual': employee_annual,
            'employer_annual': employer_annual,
            'total_annual': total_annual,
            'employee_total': employee_total,
            'employer_total': employer_total,
            'total_lifetime': total_lifetime
        }

    def _calculate_income_tax(self, annual_salary: float, employee_labor_pension: float = 0) -> Dict[str, float]:
        """计算个人所得税"""
        # 扣除额（2024年标准）
        exemption = 92000  # 免税额
        standard_deduction = 120000  # 标准扣除额（单身）
        salary_deduction = 200000  # 薪资所得特别扣除额
        labor_pension_deduction = employee_labor_pension  # 员工自提劳退扣除

        total_deductions = exemption + standard_deduction + salary_deduction + labor_pension_deduction
        taxable_income = max(0, annual_salary - total_deductions)

        # 税率计算（简化版）
        if taxable_income <= 0:
            total_tax = 0
        elif taxable_income <= 540000:
            total_tax = taxable_income * 0.05
        elif taxable_income <= 1210000:
            total_tax = 27000 + (taxable_income - 540000) * 0.12
        elif taxable_income <= 2420000:
            total_tax = 107400 + (taxable_income - 1210000) * 0.20
        elif taxable_income <= 4530000:
            total_tax = 349400 + (taxable_income - 2420000) * 0.30
        else:
            total_tax = 982400 + (taxable_income - 4530000) * 0.40

        net_income = annual_salary - total_tax

        return {
            'taxable_income': taxable_income,
            'total_tax': total_tax,
            'exemption': exemption,
            'standard_deduction': standard_deduction,
            'salary_deduction': salary_deduction,
            'labor_pension_deduction': labor_pension_deduction,
            'total_deductions': total_deductions,
            'net_income': net_income
        }

    def _calculate_labor_annuity(self, monthly_salary: float, work_years: int) -> Dict[str, float]:
        """计算劳保年金（修正版）"""
        # 投保薪资上限（劳保上限45,800/月）
        insured_salary = min(monthly_salary, 45800)

        # 劳保年金计算（基于台湾实际公式）
        # 平均投保薪资 × 年资 × 1.55% × 0.775（65岁退休调整系数）
        monthly_pension = insured_salary * work_years * 0.0155 * 0.775

        # 退休期总领取（假设领取25年）
        retirement_years = 25
        annual_pension = monthly_pension * 12
        total_benefit = annual_pension * retirement_years

        return {
            'monthly_pension': round(monthly_pension, 2),
            'annual_pension': round(annual_pension, 2),
            'total_benefit': round(total_benefit, 2)
        }

    def _calculate_labor_pension_monthly(self, total_contribution: float) -> float:
        """计算劳工退休金月领取金额"""
        # 假设年化投资回报率2%，工作35年（更保守的假设）
        work_years = 35
        annual_return = 0.02

        # 计算账户余额（考虑投资回报）
        account_balance = total_contribution * ((1 + annual_return) ** work_years)

        # 假设退休后领取25年，使用年金现值公式
        retirement_years = 25
        monthly_return = annual_return / 12
        total_months = retirement_years * 12

        if monthly_return > 0:
            monthly_pension = account_balance * (monthly_return * (1 + monthly_return) ** total_months) / ((1 + monthly_return) ** total_months - 1)
        else:
            monthly_pension = account_balance / total_months

        return round(monthly_pension, 2)

    def _format_number(self, number: float) -> str:
        """格式化数字为字符串，保留2位小数"""
        return f"{number:,.2f}"

    def _format_decimals(self, obj):
        """递归格式化数字，保留2位小数"""
        if isinstance(obj, dict):
            return {k: self._format_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._format_decimals(item) for item in obj]
        elif isinstance(obj, float):
            return round(obj, 2)
        else:
            return obj
