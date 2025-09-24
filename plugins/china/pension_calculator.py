#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国养老金计算器
"""

from typing import Dict, Any, List
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class ChinaPensionCalculator:
    """中国养老金计算器"""

    def __init__(self):
        self.country_code = "CN"
        self.country_name = "中国"

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算中国退休金 - 使用精确算法"""
        # 使用精确的中国养老金算法
        init_salary_month = salary_profile.monthly_salary
        init_avg_month = 10500  # 初始社平月工资（南京2024参考）
        start_age = 30  # 固定30岁开始工作
        retire_age = 60  # 默认60岁退休
        salary_growth = salary_profile.annual_growth_rate
        avg_growth = 0.02
        emp_rate = 0.08
        base_lower = 0.60
        base_upper = 3.00

        # 调用精确算法
        result = self._calc_china_pension_pure(
            init_salary_month, init_avg_month, start_age, retire_age,
            salary_growth, avg_growth, emp_rate, base_lower, base_upper
        )

        # 计算缴费历史（用于税收计算）
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算税收和税后净收入
        tax_result = self._calculate_tax_and_net_income(
            contribution_history, economic_factors
        )

        # 总收益基于个人账户口径计算
        total_benefit = result['final_balance']  # 个人账户最终余额作为总收益展示

        # 按照标准公式计算ROI和替代率
        final_balance = result['final_balance']  # = 员工8%累计（pa_rate=0）
        total_employee_contrib = result['personal_account_employee_sum']  # 同上一行的构成
        total_return = result['total_return']  # = 0 (pa_rate=0)
        roi_pct = final_balance / total_employee_contrib - 1.0 if total_employee_contrib > 0 else 0

        # 替代率计算
        last_year_salary = result['last_salary'] * 12  # 年工资
        replacement = (result['total_pension'] * 12.0) / last_year_salary if last_year_salary > 0 else 0

        # 计算回本年龄
        break_even_age = self._calculate_break_even_age(
            total_employee_contrib, result['total_pension'], retire_age
        )

        return PensionResult(
            monthly_pension=result['total_pension'],
            total_contribution=total_employee_contrib,
            total_benefit=total_benefit,
            retirement_account_balance=result['personal_account_balance'],
            break_even_age=break_even_age,
            roi=roi_pct,
            original_currency="CNY",
            details={
                'basic_pension': result['basic_pension'],
                'account_pension': result['account_pension'],
                'personal_account_balance': result['personal_account_balance'],
                'total_employee_contrib': result['total_employee_contrib'],
                'indexed_salary': result['indexed_salary'],
                'last_avg_salary': result['last_avg_salary'],
                'last_salary': result['last_salary'],
                'work_years': result['years'],
                'avg_index': result['avg_index'],
                'jifa_months': result['jifa_months'],
                'replacement_rate': replacement,
                'final_balance': final_balance,
                'total_contrib': total_employee_contrib,
                'total_return': total_return,
                # 新增税收相关字段，与新加坡保持一致
                'total_emp': tax_result['total_emp'],
                'total_er': tax_result['total_er'],
                'total_tax': tax_result['total_tax'],
                'net_income': tax_result['net_income'],
                'effective_tax_rate': tax_result['effective_tax_rate'],
                'monthly_net_income': tax_result['monthly_net_income'],
                'social_security_deduction': tax_result['social_security_deduction'],
                'housing_fund_deduction': tax_result['housing_fund_deduction']
            }
        )

    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict[str, Any]]:
        """计算缴费历史"""
        retirement_age = 60  # 默认60岁退休
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        history = []
        current_age = person.age

        for year in range(work_years):
            age = current_age + year
            salary = salary_profile.monthly_salary * (1 + salary_profile.annual_growth_rate) ** year

            # 社保缴费基数（通常有上下限）
            # 2024年北京社保缴费基数下限：5869元，上限：31884元
            social_base = min(max(salary, 5869), 31884)

            # 个人缴费 8%
            personal_contribution = social_base * 0.08 * 12

            # 单位缴费 16%
            employer_contribution = social_base * 0.16 * 12

            # 个人账户计入（个人缴费8% + 单位缴费的8%）
            personal_account_contribution = personal_contribution + (employer_contribution * 0.5)

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'social_base': social_base,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'personal_account_contribution': personal_account_contribution
            })

        return history

    def _calculate_break_even_age(self,
                                total_contribution: float,
                                monthly_pension: float,
                                retirement_age: int) -> int:
        """计算回本年龄"""
        if monthly_pension <= 0:
            return None

        months_to_break_even = total_contribution / monthly_pension
        years_to_break_even = months_to_break_even / 12

        return retirement_age + int(years_to_break_even)

    def _calc_china_pension_pure(self,
                                init_salary_month: float,   # 初始月工资
                                init_avg_month: float = 10500,  # 初始社平月工资（南京2024参考）
                                start_age: int = 30,
                                retire_age: int = 60,
                                salary_growth: float = 0.02,
                                avg_growth: float = 0.02,
                                emp_rate: float = 0.08,
                                base_lower: float = 0.60,   # 缴费基数下限 = 社平*60%
                                base_upper: float = 3.00,   # 缴费基数上限 = 社平*300%
                                pa_rate: float = 0.0        # 个人账户收益率，默认0%
                                ):
        """精确的中国养老金计算算法"""
        # 1) 年限与退休年龄
        years = retire_age - start_age  # = 30 (60-30)

        # 2) 计发月数：60岁
        JIFA_MONTHS = 139  # 60岁=139，55岁=170，50岁=195

        # 初始化
        salary = init_salary_month
        avg = init_avg_month
        personal_account = 0.0
        ratios = []
        total_employee_contrib = 0.0

        # 3) 每年工资 & 社平增长 2%，计算缴费基数
        for year in range(years):
            # 计算缴费基数（社平*0.6~3.0）
            lower = base_lower * avg
            upper = base_upper * avg
            base = max(lower, min(salary, upper))  # clamp(salary_t, 0.60*avg_t, 3.00*avg_t)

            # 4) 个人账户只累"个人 8%"
            employee_contrib_t = base * emp_rate * 12
            personal_account = personal_account * (1 + pa_rate) + employee_contrib_t
            total_employee_contrib += employee_contrib_t

            # 缴费指数
            ratios.append(base / avg)

            # 增长
            salary *= (1 + salary_growth)
            avg *= (1 + avg_growth)

        # 退休当年社平月工资
        last_avg_month = init_avg_month * ((1 + avg_growth) ** years)

        # 5) 基础养老金（月）（指数化平均口径）
        avg_index = sum(ratios) / len(ratios) if ratios else 0
        indexed_month = avg_index * last_avg_month
        basic_monthly = ((indexed_month + last_avg_month) / 2) * (years * 0.01)

        # 6) 个人账户养老金（月）
        account_monthly = personal_account / JIFA_MONTHS  # 60岁 = 139个月

        total_monthly = basic_monthly + account_monthly

        # 个人账户口径（养老部分）
        final_balance = personal_account                        # = 员工8%累计（pa_rate=0）
        personal_account_employee_sum = total_employee_contrib  # 同上一行的构成
        total_return = final_balance - personal_account_employee_sum  # = 0 (pa_rate=0)

        return {
            "basic_pension": basic_monthly,
            "account_pension": account_monthly,
            "total_pension": total_monthly,
            "personal_account_balance": personal_account,
            "total_employee_contrib": total_employee_contrib,
            "personal_account_employee_sum": personal_account_employee_sum,
            "final_balance": final_balance,
            "total_return": total_return,
            "indexed_salary": indexed_month,
            "last_avg_salary": last_avg_month,
            "last_salary": salary,
            "years": years,
            "avg_index": avg_index,
            "jifa_months": JIFA_MONTHS
        }

    def _calculate_tax_and_net_income(self,
                                    contribution_history: List[Dict[str, Any]],
                                    economic_factors: EconomicFactors) -> Dict[str, Any]:
        """计算税收和税后净收入"""
        if not contribution_history:
            return {
                'total_emp': 0, 'total_er': 0, 'total_tax': 0, 'net_income': 0,
                'effective_tax_rate': 0, 'monthly_net_income': 0,
                'social_security_deduction': 0, 'housing_fund_deduction': 0
            }

        # 计算总缴费
        total_emp = sum(record['personal_contribution'] for record in contribution_history)
        total_er = sum(record['employer_contribution'] for record in contribution_history)

        # 计算最后一年工资（用于税收计算）
        last_record = contribution_history[-1]
        last_year_salary = last_record['salary'] * 12

        # 计算社保扣除（个人缴费部分）
        social_security_deduction = total_emp

        # 假设住房公积金缴费比例（通常为12%）
        housing_fund_rate = 0.12
        housing_fund_deduction = last_year_salary * housing_fund_rate

        # 设置专项附加扣除
        deductions = {
            'social_security': social_security_deduction,
            'housing_fund': housing_fund_deduction,
            'education': 12000,      # 子女教育
            'housing': 12000,        # 住房租金/房贷利息
            'elderly': 24000,        # 赡养老人
            'medical': 0,            # 大病医疗
            'continuing_education': 0, # 继续教育
            'other': 0               # 其他扣除
        }

        # 简化的税收计算
        basic_deduction = 60000  # 基本减除费用
        total_deductions = basic_deduction + sum(deductions.values())
        taxable_income = max(0, last_year_salary - total_deductions)

        # 简化的个税计算（使用累进税率）
        if taxable_income <= 36000:
            total_tax = taxable_income * 0.03
        elif taxable_income <= 144000:
            total_tax = 36000 * 0.03 + (taxable_income - 36000) * 0.10
        elif taxable_income <= 300000:
            total_tax = 36000 * 0.03 + 108000 * 0.10 + (taxable_income - 144000) * 0.20
        else:
            total_tax = 36000 * 0.03 + 108000 * 0.10 + 156000 * 0.20 + (taxable_income - 300000) * 0.25

        # 计算税后净收入
        net_income = last_year_salary - total_tax
        monthly_net_income = net_income / 12
        effective_tax_rate = (total_tax / last_year_salary * 100) if last_year_salary > 0 else 0

        return {
            'total_emp': total_emp,
            'total_er': total_er,
            'total_tax': total_tax,
            'net_income': net_income,
            'effective_tax_rate': effective_tax_rate,
            'monthly_net_income': monthly_net_income,
            'social_security_deduction': social_security_deduction,
            'housing_fund_deduction': housing_fund_deduction
        }
