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
        retirement_years = 85 - retirement_age  # 假设活到85岁

        # 获取401k详细分析
        k401_analysis = plugin.get_401k_analysis(person, salary_profile, economic_factors)

        # 计算年度数据
        base_salary = salary_profile.base_salary if salary_profile.base_salary is not None else salary_profile.monthly_salary
        annual_salary = base_salary * 12
        annual_salary_usd = annual_salary * 0.14  # 人民币转美元

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
                "401k缴费": {
                    "缴费基数": annual_salary_usd,
                    "员工缴费": min(annual_salary_usd * 0.10, 23500),
                    "雇主匹配": min(annual_salary_usd * 0.10, 23500) * 0.4,  # 40%匹配率
                    "总缴费": min(annual_salary_usd * 0.10, 23500) * 1.4
                },
                "税务情况": {
                    "应税收入": annual_salary_usd - min(annual_salary_usd * 0.10, 23500) - 14600,  # 401k缴费+标准扣除
                    "所得税": max(0, (annual_salary_usd - min(annual_salary_usd * 0.10, 23500) - 14600) * 0.22),  # 简化税率
                    "实际到手收入": annual_salary_usd - min(annual_salary_usd, 160200) * 0.062 - min(annual_salary_usd * 0.10, 23500) - max(0, (annual_salary_usd - min(annual_salary_usd * 0.10, 23500) - 14600) * 0.22)
                }
            },
            "工作期总计": {
                "工作年限": work_years,
                "年龄范围": f"{start_age}-{retirement_age-1}岁",
                "收入情况": {
                    "总收入": annual_salary_usd * work_years,  # 简化计算
                    "总税费": total_contribution,
                    "实际到手收入": annual_salary_usd * work_years - total_contribution
                },
                "社保缴费总计": {
                    "雇员缴费": total_ss_contribution / 2 if total_ss_contribution > 0 else 0,
                    "雇主缴费": total_ss_contribution / 2 if total_ss_contribution > 0 else 0,
                    "总缴费": total_ss_contribution
                },
                "401k缴费总计": {
                    "雇员缴费": total_k401_contribution * 0.6,  # 估算员工缴费占比
                    "雇主缴费": total_k401_contribution * 0.4,  # 估算雇主匹配占比
                    "总缴费": total_k401_contribution
                }
            },
            "退休期分析": {
                "年龄范围": f"{retirement_age}-85岁",
                "退休年限": retirement_years,
                "退休金收入": {
                    "月领取金额": pension_result.monthly_pension,
                    "年领取金额": pension_result.monthly_pension * 12,
                    "退休期总领取": total_benefit
                }
            },
            "投资回报分析": {
                "简单回报率": pension_result.roi / 100,
                "内部收益率_IRR": pension_result.roi / 100,
                "回本分析": {
                    "回本年龄": pension_result.break_even_age,
                    "回本时间": pension_result.break_even_age - retirement_age if pension_result.break_even_age else None,
                    "能否回本": 1 if pension_result.break_even_age else 0
                }
            },
            "人民币对比": {
                "退休金收入": {
                    "月退休金": pension_result.monthly_pension * 7.2  # 美元转人民币
                },
                "缴费情况": {
                    "总缴费": total_contribution * 7.2  # 美元转人民币
                }
            }
        }


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
