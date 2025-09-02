#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收入分析器
计算各个国家的社保缴纳、个人所得税和实际到手金额
"""

from typing import Dict, List, Tuple
from utils.tax_manager import TaxManager
from utils.currency_converter import converter

class IncomeAnalyzer:
    """收入分析器"""

    def __init__(self):
        self.tax_manager = TaxManager()
        self.scenarios = {
            'high_income': {
                'monthly_salary_cny': 50000,  # 月薪5万人民币
                'annual_growth_rate': 0.02,   # 每年2%增长
                'work_years': 35
            },
            'low_income': {
                'monthly_salary_cny': 5000,   # 月薪5千人民币
                'annual_growth_rate': 0.02,   # 每年2%增长
                'work_years': 35
            }
        }

    def calculate_social_security(self, country_code: str, monthly_salary: float, year: int = 1) -> Dict:
        """计算社保缴纳金额"""
        # 考虑年增长率
        adjusted_salary = monthly_salary * ((1 + self.scenarios['high_income']['annual_growth_rate']) ** (year - 1))

        if country_code == 'CN':
            # 中国社保：养老8%+医疗2%+失业0.5%+公积金12%
            pension_rate = 0.08
            medical_rate = 0.02
            unemployment_rate = 0.005
            housing_fund_rate = 0.12

            pension = adjusted_salary * pension_rate
            medical = adjusted_salary * medical_rate
            unemployment = adjusted_salary * unemployment_rate
            housing_fund = adjusted_salary * housing_fund_rate

            total_ss = pension + medical + unemployment + housing_fund

            return {
                'pension': pension,
                'medical': medical,
                'unemployment': unemployment,
                'housing_fund': housing_fund,
                'total': total_ss,
                'monthly_salary': adjusted_salary
            }

        elif country_code == 'US':
            # 美国：Social Security 6.2% + Medicare 1.45%
            social_security_rate = 0.062
            medicare_rate = 0.0145

            # 2024年Social Security上限为$168,600
            social_security_cap = 168600 / 12  # 月上限
            taxable_salary = min(adjusted_salary, social_security_cap)

            social_security = taxable_salary * social_security_rate
            medicare = adjusted_salary * medicare_rate

            total_ss = social_security + medicare

            return {
                'social_security': social_security,
                'medicare': medicare,
                'total': total_ss,
                'monthly_salary': adjusted_salary
            }

        elif country_code == 'SG':
            # 新加坡：CPF (Central Provident Fund)
            # 员工缴费率：20%
            # 雇主缴费率：17%
            # 总缴费率：37%
            employee_rate = 0.20
            employer_rate = 0.17

            # CPF缴费上限为SGD 6,000/月
            cpf_cap = 6000
            taxable_salary = min(adjusted_salary, cpf_cap)

            employee_contribution = taxable_salary * employee_rate
            employer_contribution = taxable_salary * employer_rate
            total_ss = employee_contribution + employer_contribution

            return {
                'employee_cpf': employee_contribution,
                'employer_cpf': employer_contribution,
                'total': total_ss,
                'monthly_salary': adjusted_salary
            }

        else:
            # 其他国家的社保计算可以在这里添加
            return {
                'total': 0,
                'monthly_salary': adjusted_salary,
                'note': '社保计算待实现'
            }

    def calculate_net_income(self, country_code: str, monthly_salary: float, year: int = 1) -> Dict:
        """计算实际到手金额"""
        # 计算社保
        ss_result = self.calculate_social_security(country_code, monthly_salary, year)
        monthly_ss = ss_result['total']

        # 计算年收入
        annual_income = ss_result['monthly_salary'] * 12

        # 计算个税（考虑社保扣除）
        if country_code == 'CN':
            # 中国：社保可以税前扣除
            tax_result = self.tax_manager.calculate_with_social_security(
                country_code, annual_income, monthly_ss * 12
            )
        elif country_code == 'US':
            # 美国：社保不能税前扣除，但401K可以
            # 这里简化处理，假设没有401K扣除
            tax_result = self.tax_manager.calculate_country_tax(country_code, annual_income)
        elif country_code == 'SG':
            # 新加坡：CPF可以税前扣除
            tax_result = self.tax_manager.calculate_country_tax(
                country_code, annual_income, {'cpf_contribution': monthly_ss * 12}
            )
        else:
            tax_result = self.tax_manager.calculate_country_tax(country_code, annual_income)

        # 计算实际到手金额
        monthly_tax = tax_result.get('total_tax', 0) / 12
        monthly_net_income = ss_result['monthly_salary'] - monthly_ss - monthly_tax

        return {
            'monthly_salary': ss_result['monthly_salary'],
            'monthly_social_security': monthly_ss,
            'monthly_tax': monthly_tax,
            'monthly_net_income': monthly_net_income,
            'annual_income': annual_income,
            'annual_tax': tax_result.get('total_tax', 0),
            'effective_tax_rate': tax_result.get('effective_tax_rate', 0),
            'social_security_details': ss_result,
            'tax_details': tax_result
        }

    def analyze_scenario(self, scenario_name: str, country_codes: List[str] = None) -> Dict:
        """分析指定场景"""
        if country_codes is None:
            country_codes = self.tax_manager.get_available_countries()

        scenario = self.scenarios[scenario_name]
        monthly_salary_cny = scenario['monthly_salary_cny']
        work_years = scenario['work_years']

        print(f"\n{'='*80}")
        print(f"💰 收入分析 - {scenario_name}")
        print(f"月薪: {converter.format_amount(monthly_salary_cny, 'CNY')}")
        print(f"年增长率: {scenario['annual_growth_rate']:.1%}")
        print(f"工作年限: {work_years}年")
        print(f"{'='*80}")

        results = {}

        for country_code in country_codes:
            print(f"\n🏛️  分析 {country_code} 的收入情况...")

            # 计算第一年的情况
            year1_result = self.calculate_net_income(country_code, monthly_salary_cny, 1)

            # 计算最后一年的情况
            year_last_result = self.calculate_net_income(country_code, monthly_salary_cny, work_years)

            # 计算平均值
            total_ss = 0
            total_tax = 0
            total_net = 0

            for year in range(1, work_years + 1):
                year_result = self.calculate_net_income(country_code, monthly_salary_cny, year)
                total_ss += year_result['monthly_social_security']
                total_tax += year_result['monthly_tax']
                total_net += year_result['monthly_net_income']

            avg_monthly_ss = total_ss / work_years
            avg_monthly_tax = total_tax / work_years
            avg_monthly_net = total_net / work_years

            country_result = {
                'year1': year1_result,
                'year_last': year_last_result,
                'average': {
                    'monthly_social_security': avg_monthly_ss,
                    'monthly_tax': avg_monthly_tax,
                    'monthly_net_income': avg_monthly_net
                }
            }

            results[country_code] = country_result

            # 显示结果
            print(f"📊 {country_code} 收入分析结果:")
            print(f"   第一年:")
            print(f"     月薪: {converter.format_amount(year1_result['monthly_salary'], year1_result['tax_details']['currency'])}")
            print(f"     月社保: {converter.format_amount(year1_result['monthly_social_security'], year1_result['tax_details']['currency'])}")
            print(f"     月个税: {converter.format_amount(year1_result['monthly_tax'], year1_result['tax_details']['currency'])}")
            print(f"     月到手: {converter.format_amount(year1_result['monthly_net_income'], year1_result['tax_details']['currency'])}")
            print(f"   最后一年:")
            print(f"     月薪: {converter.format_amount(year_last_result['monthly_salary'], year_last_result['tax_details']['currency'])}")
            print(f"     月社保: {converter.format_amount(year_last_result['monthly_social_security'], year_last_result['tax_details']['currency'])}")
            print(f"     月个税: {converter.format_amount(year_last_result['monthly_tax'], year_last_result['tax_details']['currency'])}")
            print(f"     月到手: {converter.format_amount(year_last_result['monthly_net_income'], year_last_result['tax_details']['currency'])}")
            print(f"   35年平均:")
            print(f"     月社保: {converter.format_amount(avg_monthly_ss, year1_result['tax_details']['currency'])}")
            print(f"     月个税: {converter.format_amount(avg_monthly_tax, year1_result['tax_details']['currency'])}")
            print(f"     月到手: {converter.format_amount(avg_monthly_net, year1_result['tax_details']['currency'])}")

        return results

    def compare_scenarios(self, country_codes: List[str] = None) -> Dict:
        """对比高低收入场景"""
        if country_codes is None:
            country_codes = self.tax_manager.get_available_countries()

        print(f"\n{'='*80}")
        print(f"📊 高低收入场景对比分析")
        print(f"{'='*80}")

        high_income_results = self.analyze_scenario('high_income', country_codes)
        low_income_results = self.analyze_scenario('low_income', country_codes)

        # 生成对比表格
        print(f"\n📋 对比汇总表:")
        print(f"{'='*120}")
        print(f"{'国家':<8} {'收入':<8} {'月薪':<12} {'月社保':<12} {'月个税':<12} {'月到手':<12} {'有效税率':<10}")
        print(f"{'='*120}")

        for country_code in country_codes:
            # 高收入
            high = high_income_results[country_code]['year1']
            high_currency = high['tax_details']['currency']
            print(f"{country_code:<8} {'高收入':<8} {converter.format_amount(high['monthly_salary'], high_currency):<12} "
                  f"{converter.format_amount(high['monthly_social_security'], high_currency):<12} "
                  f"{converter.format_amount(high['monthly_tax'], high_currency):<12} "
                  f"{converter.format_amount(high['monthly_net_income'], high_currency):<12} "
                  f"{high['effective_tax_rate']:<10.1f}%")

            # 低收入
            low = low_income_results[country_code]['year1']
            low_currency = low['tax_details']['currency']
            print(f"{country_code:<8} {'低收入':<8} {converter.format_amount(low['monthly_salary'], low_currency):<12} "
                  f"{converter.format_amount(low['monthly_social_security'], low_currency):<12} "
                  f"{converter.format_amount(low['monthly_tax'], low_currency):<12} "
                  f"{converter.format_amount(low['monthly_net_income'], low_currency):<12} "
                  f"{low['effective_tax_rate']:<10.1f}%")
            print(f"{'-'*120}")

        return {
            'high_income': high_income_results,
            'low_income': low_income_results
        }
