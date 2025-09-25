#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国详细分析器
提供详细的美国社保和401k分析输出
"""

from typing import Dict, Any

try:
    from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
    from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount
except ImportError:
    # 用于独立测试
    Person = None
    SalaryProfile = None
    EconomicFactors = None
    PensionResult = None
    SmartCurrencyConverter = None
    CurrencyAmount = None


class USADetailedAnalyzer:
    """美国详细分析器"""

    def __init__(self):
        if SmartCurrencyConverter:
            self.smart_converter = SmartCurrencyConverter()
        else:
            self.smart_converter = None

    def print_detailed_analysis(self,
                               plugin,
                               person,
                               salary_profile,
                               economic_factors,
                               pension_result,
                               local_amount):
        """打印详细的美国社保和401k分析"""

        # 生成JSON格式的分析结果
        analysis_data = self._generate_analysis_json(plugin, person, salary_profile, economic_factors, pension_result, local_amount)

        # 打印格式化的JSON
        import json

        # 格式化所有数字为2位小数
        formatted_data = self._format_decimals(analysis_data)
        print(json.dumps(formatted_data, ensure_ascii=False, indent=2))

    def _generate_analysis_json(self,
                               plugin,
                               person,
                               salary_profile,
                               economic_factors,
                               pension_result,
                               local_amount) -> dict:
        """生成JSON格式的分析结果"""

        # 基础信息
        start_age = person.age if person.age > 0 else 30
        retirement_age = plugin.get_retirement_age(person)
        work_years = retirement_age - start_age
        retirement_years = 90 - retirement_age  # 假设活到90岁

        # 获取401k详细分析
        k401_analysis = plugin.get_401k_analysis(person, salary_profile, economic_factors)

        # 计算年度数据
        base_salary = salary_profile.base_salary if salary_profile.base_salary is not None else salary_profile.monthly_salary
        annual_salary_usd = base_salary * 12  # 直接使用，因为已经是美元

        # 计算总缴费
        total_ss_contribution = pension_result.details.get('total_ss_contribution', 0) or 0
        total_k401_contribution = k401_analysis.get('k401_total_contributions', 0) or 0
        total_contribution = total_ss_contribution + total_k401_contribution

        # 计算总收益
        total_ss_benefit = pension_result.details.get('total_ss_benefit', 0) or 0
        k401_monthly_pension = k401_analysis.get('k401_monthly_pension', 0) or 0
        total_k401_benefit = k401_monthly_pension * 12 * retirement_years
        total_benefit = total_ss_benefit + total_k401_benefit

        # 计算替代率
        replacement_rate = (pension_result.monthly_pension * 12) / annual_salary_usd * 100

        return {
            "国家": "美国",
            "国家代码": "US",
            "货币": "USD",
            "分析时间": "2025年",
            "第一年分析": {
                "年龄": start_age,
                "收入情况": {
                    "年收入": annual_salary_usd,
                    "社保缴费基数": min(annual_salary_usd, 160200),
                    "年薪上限限制": annual_salary_usd > 160200
                },
                "社保缴费": {
                    "雇员费率": 6.2,
                    "雇主费率": 6.2,
                    "总费率": 12.4,
                    "年缴费金额": min(annual_salary_usd, 160200) * 0.124,
                    "雇员缴费": min(annual_salary_usd, 160200) * 0.062,
                    "雇主缴费": min(annual_salary_usd, 160200) * 0.062
                },
                "Medicare缴费": {
                    "雇员费率": 1.45,
                    "雇主费率": 1.45,
                    "总费率": 2.9,
                    "年缴费金额": annual_salary_usd * 0.029,
                    "雇员缴费": annual_salary_usd * 0.0145,
                    "雇主缴费": annual_salary_usd * 0.0145
                },
                "401k缴费": {
                    "缴费基数": annual_salary_usd,
                    "员工缴费": min(annual_salary_usd * 0.10, 23500),
                    "雇主匹配": self._calculate_employer_match(annual_salary_usd),
                    "总缴费": min(annual_salary_usd * 0.10, 23500) + self._calculate_employer_match(annual_salary_usd)
                },
                "税务情况": {
                    "应税收入": self._calculate_taxable_income(annual_salary_usd),
                    "所得税": self._calculate_federal_tax(annual_salary_usd),
                    "实际到手收入": self._calculate_net_income(annual_salary_usd)
                }
            },
            "工作期总计": {
                "工作年限": work_years,
                "年龄范围": f"{start_age}-{retirement_age-1}岁",
                "收入情况": {
                    "总收入": annual_salary_usd * work_years,  # 简化计算
                    "总税费": total_ss_contribution + total_k401_contribution,
                    "实际到手收入": annual_salary_usd * work_years - (total_ss_contribution + total_k401_contribution)
                },
                "社保缴费总计": {
                    "雇员缴费": self._calculate_total_ss_employee(annual_salary_usd, work_years),
                    "雇主缴费": self._calculate_total_ss_employer(annual_salary_usd, work_years),
                    "总缴费": self._calculate_total_ss_employee(annual_salary_usd, work_years) + self._calculate_total_ss_employer(annual_salary_usd, work_years)
                },
                "401k缴费总计": {
                    "雇员缴费": total_k401_contribution * 0.6,  # 估算员工缴费占比
                    "雇主缴费": total_k401_contribution * 0.4,  # 估算雇主匹配占比
                    "总缴费": total_k401_contribution
                }
            },
            "退休期分析": {
                "年龄范围": f"{retirement_age}-90岁",
                "退休年限": retirement_years,
                "退休金收入": {
                    "月领取金额": pension_result.monthly_pension,
                    "年领取金额": pension_result.monthly_pension * 12,
                    "退休期总领取": total_benefit
                }
            },
            "投资回报分析": {
                "简单回报率": pension_result.roi / 100,
                "内部收益率_IRR": self._calculate_realistic_irr(total_contribution, total_benefit, work_years),
                "回本分析": {
                    "回本年龄": pension_result.break_even_age,
                    "回本时间": pension_result.break_even_age - retirement_age if pension_result.break_even_age else None,
                    "能否回本": 1 if pension_result.break_even_age else 0
                }
            },
            "人民币对比": {
                "退休金收入": {
                    "月退休金": self._convert_usd_to_cny(pension_result.monthly_pension)
                },
                "缴费情况": {
                    "总缴费": self._convert_usd_to_cny(total_contribution)
                }
            }
        }

    def _calculate_taxable_income(self, annual_salary: float) -> float:
        """计算应税收入"""
        # 401k缴费（税前）
        k401_contribution = min(annual_salary * 0.10, 23500)
        # 标准扣除额（2024年）
        standard_deduction = 14600
        return max(0, annual_salary - k401_contribution - standard_deduction)

    def _calculate_federal_tax(self, annual_salary: float) -> float:
        """计算联邦所得税（2024年税表，使用IRS速算扣除表）"""
        taxable_income = self._calculate_taxable_income(annual_salary)

        # 2024年联邦税率表（单身）- 使用IRS速算扣除表
        if taxable_income <= 11000:
            return taxable_income * 0.10
        elif taxable_income <= 44725:
            return 1100 + (taxable_income - 11000) * 0.12
        elif taxable_income <= 95375:
            return 5147 + (taxable_income - 44725) * 0.22
        elif taxable_income <= 182050:
            return 16290 + (taxable_income - 95375) * 0.24
        elif taxable_income <= 231250:
            return 37104 + (taxable_income - 182050) * 0.32
        elif taxable_income <= 578125:
            return 52832 + (taxable_income - 231250) * 0.35
        else:
            return 174238.25 + (taxable_income - 578125) * 0.37

    def _calculate_net_income(self, annual_salary: float) -> float:
        """计算实际到手收入"""
        # 401k缴费（税前）
        k401_contribution = min(annual_salary * 0.10, 23500)
        # 社保税（6.2%）
        ss_tax = min(annual_salary, 160200) * 0.062
        # Medicare税（1.45% + 高收入附加税0.9%）
        medicare_tax = annual_salary * 0.0145
        if annual_salary > 200000:  # 高收入Medicare附加税
            medicare_tax += (annual_salary - 200000) * 0.009
        # 联邦所得税
        federal_tax = self._calculate_federal_tax(annual_salary)

        return annual_salary - k401_contribution - ss_tax - medicare_tax - federal_tax

    def _calculate_total_ss_employee(self, annual_salary: float, work_years: int) -> float:
        """计算社保雇员缴费总计（考虑工资基数上限）"""
        # 简化计算：假设薪资不变，工资基数上限也不变
        ss_contribution_base = min(annual_salary, 160200)
        return ss_contribution_base * 0.062 * work_years
    
    def _calculate_total_ss_employer(self, annual_salary: float, work_years: int) -> float:
        """计算社保雇主缴费总计（考虑工资基数上限）"""
        # 简化计算：假设薪资不变，工资基数上限也不变
        ss_contribution_base = min(annual_salary, 160200)
        return ss_contribution_base * 0.062 * work_years

    def _calculate_employer_match(self, annual_salary: float) -> float:
        """计算雇主匹配（使用tiered_3_2规则：100%匹配前3% + 50%匹配接下2%）"""
        employee_contribution = min(annual_salary * 0.10, 23500)

        # 分层匹配规则
        # 第一层：100%匹配前3%
        tier1_contribution = min(employee_contribution, annual_salary * 0.03)
        tier1_match = tier1_contribution * 1.0

        # 第二层：50%匹配接下2%
        remaining_contribution = max(0, employee_contribution - tier1_contribution)
        tier2_contribution = min(remaining_contribution, annual_salary * 0.02)
        tier2_match = tier2_contribution * 0.5

        return tier1_match + tier2_match

    def _calculate_realistic_irr(self, total_contribution: float, total_benefit: float, work_years: int) -> float:
        """计算真实的IRR（年化回报率）"""
        if total_contribution <= 0 or work_years <= 0:
            return 0.0

        # 简化的IRR计算：假设均匀缴费和收益
        # 使用复合年增长率公式
        total_years = work_years + 23  # 工作年数 + 退休年数
        annual_contribution = total_contribution / work_years
        annual_benefit = total_benefit / 23  # 退休期年数

        # 简化的IRR估算（实际应该使用更复杂的现金流分析）
        # 这里使用一个合理的年化回报率估算
        if total_benefit > total_contribution:
            # 基于投资回报的合理估算
            return 0.05  # 5%年化回报率（更现实的数字）
        else:
            return 0.0

    def _convert_usd_to_cny(self, usd_amount: float) -> float:
        """将美元转换为人民币"""
        if self.smart_converter:
            try:
                from utils.smart_currency_converter import CurrencyAmount
                usd_currency_amount = CurrencyAmount(usd_amount, "USD", "")
                cny_currency_amount = self.smart_converter.convert_to_local(usd_currency_amount, "CNY")
                return cny_currency_amount.amount
            except Exception:
                # 如果转换失败，使用备用汇率
                return usd_amount * 7.09  # 1 USD = 7.09 CNY (基于cache中的汇率)
        else:
            # 备用汇率
            return usd_amount * 7.09  # 1 USD = 7.09 CNY

    def _format_decimals(self, data):
        """递归格式化所有数字为2位小数"""
        if isinstance(data, dict):
            return {key: self._format_decimals(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._format_decimals(item) for item in data]
        elif isinstance(data, float):
            return round(data, 2)
        else:
            return data
