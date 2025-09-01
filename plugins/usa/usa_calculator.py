from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class USAPensionCalculator(BasePensionCalculator):
    """美国退休金计算器（社会保障金）"""

    def __init__(self):
        super().__init__("US", "美国")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取美国退休年龄"""
        return {
            "male": 65,  # 按照用户要求设置为65岁
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取美国缴费比例"""
        return {
            "employee": 0.062,      # 6.2% 社会保障税
            "civil_servant": 0.062,
            "self_employed": 0.124,  # 自雇人士缴纳12.4%
            "farmer": 0.062
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算美国退休金（Social Security + 401K）"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算Social Security部分
        aime = self._calculate_aime(contribution_history, economic_factors)
        pia = self._calculate_pia(aime, retirement_age)
        social_security_pension = pia

        # 计算401K部分
        k401_balance = self._calculate_401k_balance(contribution_history, economic_factors)
        k401_monthly_pension = self._calculate_401k_monthly_pension(k401_balance, retirement_age)

        # 总月退休金 = Social Security + 401K
        monthly_pension = social_security_pension + k401_monthly_pension

        # 计算总缴费
        total_contribution = sum(record['total_contribution'] for record in contribution_history)

        # 计算总收益（假设活到85岁）
        life_expectancy = 85
        retirement_years = life_expectancy - retirement_age
        total_benefit = monthly_pension * 12 * retirement_years

        # 计算ROI
        roi = (total_benefit - total_contribution) / total_contribution if total_contribution > 0 else 0

        # 计算回本年龄
        break_even_age = self._calculate_break_even_age(
            total_contribution, monthly_pension, retirement_age
        )

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi,
            original_currency="USD",
            details={
                'aime': aime,
                'pia': pia,
                'social_security_pension': social_security_pension,
                'k401_balance': k401_balance,
                'k401_monthly_pension': k401_monthly_pension,
                'work_years': work_years,
                'retirement_age': retirement_age
            }
        )

    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict[str, Any]]:
        """计算缴费历史（Social Security + 401K）"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        history = []
        current_age = person.age

        for year in range(work_years):
            age = current_age + year
            salary = salary_profile.get_salary_at_age(age, person.age)

            # 将人民币月薪转换为美元（假设汇率1 CNY = 0.14 USD，2025年参考汇率）
            cny_to_usd_rate = 0.14
            salary_usd = salary * cny_to_usd_rate
            annual_salary = salary_usd * 12

            # Social Security部分
            social_security_cap = 168600  # 2024年上限
            taxable_salary = min(annual_salary, social_security_cap)

            # Social Security缴费（6.2%）
            social_security_contribution = taxable_salary * 0.062

            # Medicare缴费（1.45%）
            medicare_contribution = taxable_salary * 0.0145

            # 401K部分
            k401_contribution_data = self._calculate_401k_contribution(salary_usd, age, year)
            k401_employee_contribution = k401_contribution_data['employee_contribution']
            k401_employer_match = k401_contribution_data['employer_match']

            # 总401K缴费
            k401_total = k401_contribution_data['total_contribution']

            # 个人总缴费（Social Security + Medicare + 401K）
            personal_contribution = social_security_contribution + medicare_contribution + k401_employee_contribution

            # 雇主总缴费（Social Security + Medicare + 401K Match）
            employer_contribution = social_security_contribution + medicare_contribution + k401_employer_match

            # 总缴费
            total_contribution = personal_contribution + employer_contribution

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'annual_salary': annual_salary,
                'taxable_salary': taxable_salary,
                'social_security_contribution': social_security_contribution,
                'medicare_contribution': medicare_contribution,
                'k401_employee_contribution': k401_employee_contribution,
                'k401_employer_match': k401_employer_match,
                'k401_total': k401_total,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': total_contribution
            })

        return history

    def _calculate_aime(self,
                       contribution_history: List[Dict[str, Any]],
                       economic_factors: EconomicFactors) -> float:
        """计算平均指数化月收入 (AIME)"""
        if not contribution_history:
            return 0

        # 获取最高的35年收入
        yearly_earnings = []
        for record in contribution_history:
            yearly_earnings.append({
                'year': record['year'],
                'taxable_salary': record['taxable_salary']
            })

        # 按年份排序
        yearly_earnings.sort(key=lambda x: x['year'])

        # 计算指数化收入
        indexed_earnings = []
        for i, earning in enumerate(yearly_earnings):
            # 简化的指数化计算（实际应该使用官方指数）
            years_to_retirement = len(yearly_earnings) - i - 1
            indexed_wage = earning['taxable_salary'] * (1 + economic_factors.inflation_rate) ** years_to_retirement
            indexed_earnings.append(indexed_wage)

        # 取最高的35年（如果不足35年，用0填充）
        while len(indexed_earnings) < 35:
            indexed_earnings.append(0)

        # 排序并取最高的35年
        indexed_earnings.sort(reverse=True)
        top_35_earnings = indexed_earnings[:35]

        # 计算AIME
        total_indexed_earnings = sum(top_35_earnings)
        aime = total_indexed_earnings / (35 * 12)  # 转换为月收入

        return aime

    def _calculate_pia(self, aime: float, retirement_age: int) -> float:
        """计算主要保险金额 (PIA)"""
        # 2024年的PIA计算（简化版）
        # 实际计算更复杂，这里使用近似值

        if aime <= 1174:
            pia = aime * 0.90
        elif aime <= 7078:
            pia = 1174 * 0.90 + (aime - 1174) * 0.32
        else:
            pia = 1174 * 0.90 + (7078 - 1174) * 0.32 + (aime - 7078) * 0.15

        # 如果提前退休，会有减少
        if retirement_age < 67:
            reduction_months = (67 - retirement_age) * 12
            reduction_rate = 0.00556  # 每月减少0.556%
            pia = pia * (1 - reduction_rate * reduction_months)

        return pia

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

    def _calculate_401k_contribution(self, salary: float, age: int, year: int) -> Dict[str, float]:
        """计算401K缴费（按照2025年准确的上限规则）"""
        # salary已经是美元月薪，直接计算年薪
        annual_salary = salary * 12

        # 1) 员工递延（402(g) + catch-ups）
        deferral_cap = 23_500  # 2025年基础上限

        # 年龄相关的追补缴费
        if 60 <= age <= 63:
            catchup = 11_250  # super catch-up (plan dependent)
        elif age >= 50:
            catchup = 7_500   # 标准catch-up
        else:
            catchup = 0

        # 计算员工实际缴费（考虑工资增长后的10%比例）
        emp_rate = 0.10  # 假设员工选择10%递延比例
        target_deferral = annual_salary * emp_rate

        # 应用员工缴费上限
        employee_deferral = min(target_deferral, deferral_cap) + min(catchup, max(0, 70_000 - deferral_cap))

        # 2) 雇主配比（按 401(a)(17) 薪酬上限）
        comp_for_match = min(annual_salary, 350_000)  # 2025年薪酬上限

        # 雇主配比公式：100% match 前3% + 50% match 接下2%
        match_rate = 0.0
        if employee_deferral > 0:
            # 前3%：100% match
            first_3_percent = min(0.03, employee_deferral / comp_for_match) * 1.0
            match_rate += first_3_percent

            # 接下2%：50% match
            remaining_deferral = max(0, employee_deferral - comp_for_match * 0.03)
            if remaining_deferral > 0:
                next_2_percent = min(0.02, remaining_deferral / comp_for_match) * 0.5
                match_rate += next_2_percent

        employer_match = comp_for_match * match_rate

        # 3) 415(c) 年度总上限
        # 注意：catch-up部分不计入70k上限
        base_employee_contribution = min(employee_deferral, deferral_cap)
        total = min(base_employee_contribution + employer_match, 70_000)

        # 4) 若 total 被 70k 截断，优先截雇主部分（常见做法）
        employer_match = max(0.0, total - base_employee_contribution)

        # 最终计算
        catchup_contributions = max(0, employee_deferral - deferral_cap)
        total_contribution = base_employee_contribution + employer_match + catchup_contributions


        return {
            'employee_contribution': employee_deferral,
            'employer_match': employer_match,
            'total_contribution': total_contribution,
            'base_deferral': base_employee_contribution,
            'catchup_contribution': catchup_contributions,
            'catchup_limit': catchup,
            'compensation_cap': 350_000,
            'overall_limit': 70_000
        }

    def _calculate_401k_balance(self, contribution_history: List[Dict[str, Any]], economic_factors: EconomicFactors) -> float:
        """计算401K账户余额"""
        if not contribution_history:
            return 0

        total_balance = 0

        for i, record in enumerate(contribution_history):
            # 计算每笔缴费的未来价值
            years_to_retirement = len(contribution_history) - i - 1
            k401_contribution = record['k401_total']

            # 使用投资回报率计算未来价值
            future_value = self.calculate_future_value(
                k401_contribution, years_to_retirement, economic_factors.investment_return_rate
            )
            total_balance += future_value

        return total_balance

    def _calculate_401k_monthly_pension(self, k401_balance: float, retirement_age: int) -> float:
        """计算401K月退休金"""
        # 使用定额年金公式计算月退休金
        # PMT = FV * (i / (1 - (1+i)^(-M)))

        # 参数设置
        monthly_rate = 0.03 / 12  # 月收益率3%/12
        months = 240  # 20年（240个月）

        if monthly_rate == 0 or months == 0:
            # 如果参数无效，使用简单除法
            return k401_balance / months if months > 0 else 0

        # 计算年金系数
        annuity_factor = monthly_rate / (1 - (1 + monthly_rate) ** (-months))

        # 计算月退休金
        monthly_pension = k401_balance * annuity_factor

        return monthly_pension

    def get_401k_analysis(self, person: Person, salary_profile: SalaryProfile, economic_factors: EconomicFactors) -> Dict[str, Any]:
        """获取401K详细分析"""
        """获取401K详细分析"""
        contribution_history = self.calculate_contribution_history(person, salary_profile, economic_factors)

        # 计算401K相关数据
        k401_employee_total = sum(record['k401_employee_contribution'] for record in contribution_history)
        k401_employer_total = sum(record['k401_employer_match'] for record in contribution_history)
        k401_total_contributions = sum(record['k401_total'] for record in contribution_history)

        # 计算401K余额
        k401_balance = self._calculate_401k_balance(contribution_history, economic_factors)

        # 计算月退休金
        retirement_age = self.get_retirement_age(person)
        k401_monthly_pension = self._calculate_401k_monthly_pension(k401_balance, retirement_age)

        # 分析缴费上限情况
        age_50_plus = person.age + 15  # 假设15年后达到50岁
        age_60_plus = person.age + 25  # 假设25年后达到60岁

        # 分析雇主配比
        # 将人民币月薪转换为美元
        cny_to_usd_rate = 0.14
        sample_salary_usd = salary_profile.base_salary * cny_to_usd_rate
        sample_salary = sample_salary_usd * 12
        sample_401k_data = self._calculate_401k_contribution(sample_salary_usd, person.age, 0)
        sample_employee_contribution = sample_401k_data['employee_contribution']
        sample_employer_match = sample_401k_data['employer_match']

        return {
            'contribution_history': contribution_history,
            'k401_employee_total': k401_employee_total,
            'k401_employer_total': k401_employer_total,
            'k401_total_contributions': k401_total_contributions,
            'k401_balance': k401_balance,
            'k401_monthly_pension': k401_monthly_pension,
            'age_limits': {
                'current_age': person.age,
                'age_50_plus': age_50_plus,
                'age_60_plus': age_60_plus,
                'current_limit': 23500,
                'age_50_limit': 30000,
                'age_60_limit': 34250
            },
            'employer_match_sample': {
                'salary': sample_salary,
                'employee_contribution': sample_employee_contribution,
                'employer_match': sample_employer_match,
                'total_401k': sample_employee_contribution + sample_employer_match
            },
            'limits_info': {
                'base_deferral_limit': 23500,
                'age_50_catchup': 7500,
                'age_60_63_catchup': 11250,
                'compensation_cap': 350000,
                'overall_limit': 70000
            }
        }

    def get_contribution_scenarios(self, annual_salary: float, years: int = 35, investment_rate: float = 0.07) -> List[Dict[str, Any]]:
        """获取不同缴费比例的401K场景分析"""
        scenarios = []
        deferral_rates = [0.05, 0.08, 0.10, 0.15, 0.20]

        for rate in deferral_rates:
            # 计算年缴费
            annual_contribution = min(annual_salary * rate, 23500)  # 基础上限

            # 计算N年后的余额
            if investment_rate > 0:
                future_value = annual_contribution * ((1 + investment_rate) ** years - 1) / investment_rate
            else:
                future_value = annual_contribution * years

            # 计算月退休金 (25年)
            months = 300
            monthly_pension = future_value / months

            scenarios.append({
                'deferral_rate': rate,
                'annual_contribution': annual_contribution,
                'future_value': future_value,
                'monthly_pension': monthly_pension
            })

        return scenarios

    def get_employer_match_analysis(self, annual_salary: float) -> List[Dict[str, Any]]:
        """获取雇主配比影响分析"""
        analysis = []
        employee_contribution_rates = [0.03, 0.05, 0.08, 0.10]

        for rate in employee_contribution_rates:
            employee_amount = annual_salary * rate

            # 计算雇主配比
            match_1 = min(annual_salary * 0.03, employee_amount)  # 100% match 前3%
            match_2 = min(annual_salary * 0.02, max(0, employee_amount - annual_salary * 0.03))  # 50% match 接下2%
            employer_match = match_1 + (match_2 * 0.5)

            total_contribution = employee_amount + employer_match
            match_rate = (employer_match / employee_amount * 100) if employee_amount > 0 else 0

            analysis.append({
                'employee_rate': rate,
                'employee_amount': employee_amount,
                'employer_match': employer_match,
                'total_contribution': total_contribution,
                'match_rate': match_rate
            })

        return analysis
