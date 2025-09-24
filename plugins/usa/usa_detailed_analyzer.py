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
            "货币": "USD",
            "分析时间": "2025年",
            "基础信息": {
                "姓名": person.name,
                "年龄": start_age,
                "工作年限": work_years,
                "退休年龄": retirement_age,
                "退休期": f"{retirement_age}-{85}岁",
                "预期寿命": 85
            },
            "收入信息": {
                "月薪": {
                    "人民币": base_salary,
                    "美元": annual_salary_usd / 12
                },
                "年薪": {
                    "人民币": annual_salary,
                    "美元": annual_salary_usd
                },
                "年增长率": f"{salary_profile.annual_growth_rate:.1%}"
            },
            "社保缴费": {
                "缴费基数": {
                    "月薪": annual_salary_usd / 12,
                    "年薪": annual_salary_usd,
                    "上限": 160200
                },
                "缴费比例": {
                    "个人": "6.2%",
                    "雇主": "6.2%",
                    "总计": "12.4%"
                },
                "年度缴费": {
                    "个人": annual_salary_usd * 0.062,
                    "雇主": annual_salary_usd * 0.062,
                    "总计": annual_salary_usd * 0.124
                },
                "终身缴费": {
                    "个人": total_ss_contribution / 2 if total_ss_contribution > 0 else 0,
                    "雇主": total_ss_contribution / 2 if total_ss_contribution > 0 else 0,
                    "总计": total_ss_contribution
                }
            },
            "401k缴费": {
                "缴费限制": {
                    "基础限制": 23500,
                    "50岁追加": 7500,
                    "60-63岁超级追加": 11250,
                    "总限制": 70000
                },
                "当前年龄限制": {
                    "基础": k401_analysis['age_limits']['current_limit'],
                    "追加": 0 if start_age < 50 else 7500 if start_age < 60 else 11250 if start_age <= 63 else 7500,
                    "总计": k401_analysis['age_limits']['current_limit']
                },
                "年度缴费": {
                    "员工缴费": k401_analysis.get('employer_match_sample', {}).get('employee_contribution', 0) or 0,
                    "雇主匹配": k401_analysis.get('employer_match_sample', {}).get('employer_match', 0) or 0,
                    "总计": k401_analysis.get('employer_match_sample', {}).get('total_401k', 0) or 0
                },
                "终身缴费": {
                    "员工缴费": k401_analysis.get('k401_employee_total', 0) or 0,
                    "雇主匹配": k401_analysis.get('k401_employer_total', 0) or 0,
                    "总计": k401_analysis.get('k401_total_contributions', 0) or 0
                },
                "雇主匹配规则": "100%匹配前3% + 50%匹配接下2%"
            },
            "投资收益": {
                "投资回报率": f"{economic_factors.investment_return_rate:.1%}",
                "通胀率": f"{economic_factors.inflation_rate:.1%}",
                "401k最终余额": k401_analysis.get('k401_balance', 0) or 0,
                "投资增值": (k401_analysis.get('k401_balance', 0) or 0) - (k401_analysis.get('k401_total_contributions', 0) or 0)
            },
            "退休金计算": {
                "社保退休金": {
                    "月退休金": pension_result.details.get('social_security_pension', 0) or 0,
                    "年退休金": (pension_result.details.get('social_security_pension', 0) or 0) * 12,
                    "终身收益": total_ss_benefit
                },
                "401k退休金": {
                    "月退休金": k401_monthly_pension,
                    "年退休金": k401_monthly_pension * 12,
                    "终身收益": total_k401_benefit
                },
                "总退休金": {
                    "月退休金": pension_result.monthly_pension,
                    "年退休金": pension_result.monthly_pension * 12,
                    "终身收益": total_benefit
                }
            },
            "工作期总计": {
                "总缴费": {
                    "社保": total_ss_contribution,
                    "401k": total_k401_contribution,
                    "总计": total_contribution
                },
                "缴费占比": {
                    "社保": f"{total_ss_contribution / total_contribution * 100:.1f}%",
                    "401k": f"{total_k401_contribution / total_contribution * 100:.1f}%"
                }
            },
            "退休期总计": {
                "总收益": {
                    "社保": total_ss_benefit,
                    "401k": total_k401_benefit,
                    "总计": total_benefit
                },
                "收益占比": {
                    "社保": f"{total_ss_benefit / total_benefit * 100:.1f}%",
                    "401k": f"{total_k401_benefit / total_benefit * 100:.1f}%"
                }
            },
            "投资回报分析": {
                "总投入": total_contribution,
                "总产出": total_benefit,
                "净收益": total_benefit - total_contribution,
                "投资回报率": f"{pension_result.roi:.1f}%",
                "回本年龄": pension_result.break_even_age,
                "替代率": f"{replacement_rate:.1f}%"
            },
            "401k详细分析": {
                "缴费历史": self._format_contribution_history(k401_analysis['contribution_history']),
                "年龄限制变化": {
                    "30岁": 23500,
                    "50岁": 31000,
                    "60岁": 34750,
                    "65岁": 31000
                },
                "雇主匹配示例": {
                    "年收入": k401_analysis['employer_match_sample']['salary'],
                    "员工缴费3%": k401_analysis['employer_match_sample']['salary'] * 0.03,
                    "雇主匹配": k401_analysis['employer_match_sample']['employer_match'],
                    "匹配率": f"{k401_analysis['employer_match_sample']['employer_match'] / (k401_analysis['employer_match_sample']['salary'] * 0.03) * 100:.1f}%"
                }
            },
            "税务影响": {
                "401k缴费": "税前缴费，降低当期应税收入",
                "401k提取": "按普通收入税率缴税",
                "社保": "缴费时已缴税，提取时免税",
                "建议": "401k提供税收递延优势，适合高收入人群"
            },
            "风险提示": {
                "投资风险": "401k投资有市场风险，历史回报不代表未来",
                "政策风险": "社保和401k政策可能调整",
                "长寿风险": "预期寿命可能超过85岁",
                "通胀风险": "长期通胀可能影响购买力"
            }
        }

    def _format_contribution_history(self, contribution_history) -> list:
        """格式化缴费历史"""
        if not contribution_history:
            return []

        formatted_history = []
        for i, record in enumerate(contribution_history[:5]):  # 只显示前5年
            formatted_history.append({
                "年份": record.year,
                "年龄": record.age,
                "年薪": record.annual_salary,
                "员工缴费": record.total_employee_contribution,
                "雇主匹配": record.employer_match,
                "总缴费": record.total_contribution
            })

        if len(contribution_history) > 5:
            formatted_history.append({
                "说明": f"... 省略中间{len(contribution_history) - 10}年 ..."
            })

            # 显示最后5年
            for record in contribution_history[-5:]:
                formatted_history.append({
                    "年份": record.year,
                    "年龄": record.age,
                    "年薪": record.annual_salary,
                    "员工缴费": record.total_employee_contribution,
                    "雇主匹配": record.employer_match,
                    "总缴费": record.total_contribution
                })

        return formatted_history

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
