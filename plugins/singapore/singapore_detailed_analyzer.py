#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡详细分析器
提供详细的CPF分析输出
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount


class SingaporeDetailedAnalyzer:
    """新加坡详细分析器"""

    def __init__(self):
        self.smart_converter = SmartCurrencyConverter()

    def print_detailed_analysis(self, 
                               plugin,
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors,
                               pension_result: PensionResult,
                               local_amount: CurrencyAmount):
        """打印详细的新加坡CPF分析"""
        
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
        
        # 计算第一年数据
        base = min(local_amount.amount, 102000)
        employee_contrib = base * 0.20
        employer_contrib = base * 0.17
        total_contrib = base * 0.37
        
        # 计算税收
        annual_income = local_amount.amount
        taxable_income = annual_income - employee_contrib
        tax_result = plugin.calculate_tax(taxable_income)
        net_income = taxable_income - tax_result.get('total_tax', 0)
        
        # 计算35年工作期数据
        cpf_base = min(annual_income, 102000)
        annual_cpf_total = cpf_base * 0.37
        annual_cpf_employee = cpf_base * 0.20
        annual_cpf_employer = cpf_base * 0.17
        
        total_cpf_employee = annual_cpf_employee * 35
        total_cpf_employer = annual_cpf_employer * 35
        total_cpf_total = annual_cpf_total * 35
        
        total_cpf_OA = cpf_base * 0.23 * 35
        total_cpf_SA = cpf_base * 0.06 * 35
        total_cpf_MA = cpf_base * 0.08 * 35
        
        # 计算总收入（考虑工资增长）
        total_salary = 0
        total_tax = 0
        for year in range(35):
            salary = annual_income * (1.03 ** year)
            total_salary += salary
            total_tax += plugin.calculate_tax(salary).get('total_tax', 0)
        
        # 计算退休期数据
        total_retirement_payout = pension_result.total_benefit if hasattr(pension_result, 'total_benefit') else pension_result.monthly_pension * 12 * 25
        monthly_pension = pension_result.monthly_pension
        annual_pension = monthly_pension * 12
        
        # 计算最终账户余额（退休开始时65岁的账户余额）
        final_accounts = {}
        if hasattr(pension_result, 'details') and pension_result.details and 'cpf_accounts' in pension_result.details:
            accounts = pension_result.details['cpf_accounts']
            final_accounts = {
                "普通账户_OA": accounts.get('oa_balance', 0),
                "特别账户_SA": accounts.get('sa_balance', 0),
                "医疗账户_MA": accounts.get('ma_balance', 0),
                "退休账户_RA": accounts.get('ra_balance', 0),
                "总余额": sum([accounts.get('oa_balance', 0), accounts.get('sa_balance', 0), 
                              accounts.get('ma_balance', 0), accounts.get('ra_balance', 0)])
            }
        else:
            # 如果details中没有数据，使用默认值或从其他地方获取
            # 这里我们可以从lifetime_result中获取数据
            try:
                # 尝试从插件获取CPF计算器的结果
                lifetime_result = plugin.cpf_calculator.calculate_lifetime_cpf(
                    salary_profile.monthly_salary, 
                    person.age if person.age > 0 else 30, 
                    plugin.get_retirement_age(person)
                )
                final_balances = lifetime_result['final_balances']
                final_accounts = {
                    "普通账户_OA": final_balances.get('oa_balance', 0),
                    "特别账户_SA": final_balances.get('sa_balance', 0),
                    "医疗账户_MA": final_balances.get('ma_balance', 0),
                    "退休账户_RA": final_balances.get('ra_balance', 0),
                    "总余额": sum([final_balances.get('oa_balance', 0), final_balances.get('sa_balance', 0), 
                                  final_balances.get('ma_balance', 0), final_balances.get('ra_balance', 0)])
                }
            except Exception as e:
                # 如果获取失败，使用空值
                final_accounts = {
                    "普通账户_OA": 0,
                    "特别账户_SA": 0,
                    "医疗账户_MA": 0,
                    "退休账户_RA": 0,
                    "总余额": 0
                }
        
        # 计算人民币对比
        monthly_pension_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(pension_result.monthly_pension, plugin.CURRENCY, ""), 
            'CNY'
        )
        total_contribution_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(pension_result.total_contribution, plugin.CURRENCY, ""), 
            'CNY'
        )
        
        # 构建JSON数据结构
        analysis_data = {
            "国家": "新加坡",
            "国家代码": "SG",
            "货币": "SGD",
            "分析时间": "2024年",
            "第一年分析": {
                "年龄": 30,
                "收入情况": {
                    "年收入": local_amount.amount,
                    "CPF缴费基数": base,
                    "年薪上限限制": True
                },
                "社保缴费": {
                    "雇员费率": 20.0,
                    "雇主费率": 17.0,
                    "总费率": 37.0,
                    "年缴费金额": total_contrib,
                    "雇员缴费": employee_contrib,
                    "雇主缴费": employer_contrib
                },
                "账户分配": {
                    "普通账户_OA": base * 0.23,
                    "特别账户_SA": base * 0.06,
                    "医疗账户_MA": base * 0.08
                },
                "税务情况": {
                    "应税收入": taxable_income,
                    "所得税": tax_result.get('total_tax', 0),
                    "实际到手收入": net_income
                }
            },
            "工作期总计": {
                "工作年限": 35,
                "年龄范围": "30-64岁",
                "收入情况": {
                    "总收入": total_salary,
                    "总税费": total_tax,
                    "实际到手收入": total_salary - total_cpf_employee - total_tax
                },
                "社保缴费总计": {
                    "雇员缴费": total_cpf_employee,
                    "雇主缴费": total_cpf_employer,
                    "总缴费": total_cpf_total
                },
                "账户分配总计": {
                    "普通账户_OA": total_cpf_OA,
                    "特别账户_SA": total_cpf_SA,
                    "医疗账户_MA": total_cpf_MA
                }
            },
            "退休期分析": {
                "年龄范围": "65-90岁",
                "退休年限": 25,
                "退休金收入": {
                    "月领取金额": monthly_pension,
                    "年领取金额": annual_pension,
                    "退休期总领取": total_retirement_payout
                }
            },
            "最终账户余额": final_accounts,
            "投资回报分析": {
                "简单回报率": pension_result.roi,
                "内部收益率_IRR": pension_result.roi,
                "回本分析": {
                    "回本年龄": pension_result.break_even_age if pension_result.break_even_age else None,
                    "回本时间": (pension_result.break_even_age - 65) if pension_result.break_even_age else None,
                    "能否回本": pension_result.break_even_age is not None
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
        
        return analysis_data
    
    def _format_decimals(self, data):
        """递归格式化所有数字为2位小数"""
        if isinstance(data, dict):
            return {key: self._format_decimals(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._format_decimals(item) for item in data]
        elif isinstance(data, (int, float)):
            return round(data, 2)
        else:
            return data