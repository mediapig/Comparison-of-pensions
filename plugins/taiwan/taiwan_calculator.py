from typing import Dict, Any, List
import math
from datetime import date
from dataclasses import dataclass
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

@dataclass
class TWParams:
    start_age: int = 30
    retire_age: int = 65
    wage_growth: float = 0.0    # 年薪增长 0%

    # 劳保年金 (DB)
    ins_rate: float = 0.105     # 劳保费率 10.5%
    employer_share: float = 0.70  # 雇主承担 70%
    worker_share: float = 0.20    # 劳工承担 20%
    gov_share: float = 0.10       # 政府承担 10%
    cap_month: float = 45800.0    # 月投保薪资上限 NT$45,800

    # 劳退新制 (DC)
    labor_pension_rate: float = 0.06  # 劳退新制雇主提缴率 6%
    voluntary_rate: float = 0.06      # 劳工自提上限 6%
    investment_return: float = 0.05   # 年投资回报率 5%
    labor_pension_cap: float = 150000.0  # 劳退月提缴工资上限 NT$150,000

class TaiwanPensionCalculator(BasePensionCalculator):
    """台湾退休金计算器（劳保年金）"""

    def __init__(self):
        super().__init__("TW", "台湾")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取台湾退休年龄"""
        return {
            "male": 65,      # 劳保年金请领年龄
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取台湾缴费比例"""
        params = TWParams()
        return {
            "employee": params.ins_rate * params.worker_share,    # 10.5% × 20% = 2.1% 劳工缴费
            "employer": params.ins_rate * params.employer_share,  # 10.5% × 70% = 7.35% 雇主缴费
            "government": params.ins_rate * params.gov_share,     # 10.5% × 10% = 1.05% 政府补助
            "total": params.ins_rate,                             # 10.5% 总费率
            "civil_servant": params.ins_rate,   # 公务员缴费比例
            "self_employed": params.ins_rate,   # 自雇人士缴费比例
            "farmer": params.ins_rate           # 农民缴费比例
        }

    def calc_tw_pension(self, annual_salary: float, params: TWParams = TWParams()) -> Dict[str, float]:
        """台湾劳保年金计算核心逻辑"""
        years = params.retire_age - params.start_age
        salary = annual_salary
        contrib_total = 0.0

        # 缴费总额累积（按照劳工实际缴费比例计算，考虑投保薪资上限）
        worker_contrib_total = 0.0
        employer_contrib_total = 0.0
        gov_contrib_total = 0.0

        for y in range(years):
            # 年循环内：
            monthly_salary = salary / 12.0
            insured_base = min(monthly_salary, params.cap_month)
            annual_base = insured_base * 12.0

            total_insurance = annual_base * params.ins_rate
            worker_contrib = total_insurance * params.worker_share
            employer_contrib = total_insurance * params.employer_share
            gov_contrib = total_insurance * params.gov_share

            contrib_total += total_insurance
            worker_contrib_total += worker_contrib
            employer_contrib_total += employer_contrib
            gov_contrib_total += gov_contrib

            salary *= (1 + params.wage_growth)

        # 平均投保薪资（用首尾平均近似，考虑投保薪资上限）
        initial_monthly = annual_salary / 12.0
        final_monthly = salary / 12.0
        initial_insured = min(initial_monthly, params.cap_month)
        final_insured = min(final_monthly, params.cap_month)
        avg_salary = (initial_insured + final_insured) / 2 * 12

        # 年金公式
        base_ratio = 0.775
        extra_ratio = max(years - 15, 0) * 0.015
        benefit_ratio = min(base_ratio + extra_ratio, 1.0)   # 上限 100%

        avg_base_month = avg_salary / 12
        monthly_pension = avg_base_month * benefit_ratio

        # 纯DB口径的所得替代率
        replacement_ratio = monthly_pension / avg_base_month

        return {
            "Initial_Annual_Salary": annual_salary,
            "Final_Annual_Salary": salary,
            "Average_Salary": avg_salary,
            "Average_Base_Monthly": avg_base_month,
            "Total_Contributions": contrib_total,
            "Worker_Contributions": worker_contrib_total,
            "Employer_Contributions": employer_contrib_total,
            "Government_Contributions": gov_contrib_total,
            "Years_Contributed": years,
            "Benefit_Ratio": benefit_ratio,
            "Replacement_Ratio": replacement_ratio,
            "Monthly_Pension": monthly_pension
        }

    def calc_labor_pension_dc(self, annual_salary: float, params: TWParams = TWParams()) -> Dict[str, float]:
        """台湾劳退新制（DC）计算"""
        years = params.retire_age - params.start_age
        salary = annual_salary

        total_contrib = 0.0
        employer_contrib_total = 0.0
        worker_contrib_total = 0.0  # 假设劳工自提6%
        balance = 0.0

        for y in range(years):
            monthly_salary = salary / 12.0
            # 劳退新制有更高的薪资上限
            capped_monthly = min(monthly_salary, params.labor_pension_cap)
            capped_annual = capped_monthly * 12.0

            # 雇主提缴 6%
            employer_contrib = capped_annual * params.labor_pension_rate
            # 劳工自提 6% (可选，这里假设全额自提)
            worker_contrib = capped_annual * params.voluntary_rate

            annual_contrib = employer_contrib + worker_contrib

            # 投资增值
            balance = balance * (1 + params.investment_return) + annual_contrib

            total_contrib += annual_contrib
            employer_contrib_total += employer_contrib
            worker_contrib_total += worker_contrib

            salary *= (1 + params.wage_growth)

        # 退休时账户余额
        account_balance = balance

        # 月退休金（年金化，假设20年领取）
        annuity_years = 20
        monthly_periods = annuity_years * 12
        discount_rate = 0.03 / 12  # 月折现率3%

        if discount_rate > 0:
            monthly_pension = account_balance * discount_rate / (1 - (1 + discount_rate) ** -monthly_periods)
        else:
            monthly_pension = account_balance / monthly_periods

        # 总投资收益
        total_return = account_balance - total_contrib

        return {
            "Initial_Annual_Salary": annual_salary,
            "Final_Annual_Salary": salary,
            "Total_Contributions": total_contrib,
            "Employer_Contributions": employer_contrib_total,
            "Worker_Contributions": worker_contrib_total,
            "Account_Balance": account_balance,
            "Total_Return": total_return,
            "Monthly_Pension": monthly_pension,
            "Years_Contributed": years
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算台湾劳保年金"""
        # 使用新的计算逻辑
        params = TWParams()

        # 转换月薪为年薪（TWD）
        monthly_salary_cny = salary_profile.base_salary
        cny_to_twd_rate = 4.4  # 1 CNY = 4.4 TWD
        annual_salary_twd = monthly_salary_cny * 12 * cny_to_twd_rate

        # 调用核心计算函数
        db_result = self.calc_tw_pension(annual_salary_twd, params)
        dc_result = self.calc_labor_pension_dc(annual_salary_twd, params)

        print("🇹🇼 === 台湾养老金详细分析系统 ===")
        print("分析劳保年金（DB） + 劳退新制（DC）")

        # DB系统数据
        db_avg_base_month = db_result['Average_Base_Monthly']
        db_years = db_result['Years_Contributed']
        db_ratio = db_result['Benefit_Ratio']
        db_monthly_pension = db_result['Monthly_Pension']
        db_last_year_salary = db_result['Final_Annual_Salary']

        # DC系统数据
        dc_monthly_pension = dc_result['Monthly_Pension']
        dc_account_balance = dc_result['Account_Balance']
        dc_total_contrib = dc_result['Total_Contributions']
        dc_total_return = dc_result['Total_Return']
        dc_last_year_salary = dc_result['Final_Annual_Salary']

        # 计算替代率
        db_last_year_monthly = db_last_year_salary / 12.0
        dc_last_year_monthly = dc_last_year_salary / 12.0
        db_replacement_ratio = db_monthly_pension / db_last_year_monthly
        dc_replacement_ratio = dc_monthly_pension / dc_last_year_monthly

        # 合计
        total_monthly_pension = db_monthly_pension + dc_monthly_pension
        total_replacement_ratio = db_replacement_ratio + dc_replacement_ratio

        print(f"\n--------------------------------------------------")
        print(f"📊 劳保年金（DB）")
        print(f"  - 平均月投保薪资: NT${db_avg_base_month:,.0f}{'（封顶）' if db_avg_base_month >= params.cap_month else ''}")
        print(f"  - 缴费年资: {db_years} 年")
        print(f"  - 月退休金: NT${db_monthly_pension:,.0f}")
        print(f"  - 替代率: {db_replacement_ratio*100:.1f}%（对比最后一年薪资）")

        print(f"\n📊 劳退新制（DC）")
        print(f"  - 总缴费: NT${dc_total_contrib:,.0f}")
        print(f"  - 投资收益: NT${dc_total_return:,.0f}")
        print(f"  - 退休账户余额: NT${dc_account_balance:,.0f}")
        print(f"  - 月退休金: NT${dc_monthly_pension:,.0f}")
        print(f"  - 替代率: {dc_replacement_ratio*100:.1f}%（对比最后一年薪资）")

        print(f"\n📋 合计（DB+DC）")
        print(f"  - 总月退休金: NT${total_monthly_pension:,.0f} ({db_monthly_pension:,.0f} + {dc_monthly_pension:,.0f})")
        print(f"  - 总替代率: {total_replacement_ratio*100:.1f}% ({db_replacement_ratio*100:.1f}% + {dc_replacement_ratio*100:.1f}%)")

        # 使用合计的月退休金作为返回值
        monthly_pension = total_monthly_pension
        worker_contribution = db_result['Worker_Contributions'] + dc_result['Worker_Contributions']

        # 计算总收益（假设活到85岁）
        life_expectancy = 85
        retirement_years = life_expectancy - params.retire_age
        total_benefit = monthly_pension * 12 * retirement_years

        # 计算ROI（基于合计缴费）
        roi = (total_benefit - worker_contribution) / worker_contribution if worker_contribution > 0 else 0

        # 计算回本年龄（基于合计缴费）
        break_even_age = self._calculate_break_even_age(
            worker_contribution, monthly_pension, params.retire_age
        )

        return PensionResult(
            monthly_pension=monthly_pension,  # DB + DC 合计
            total_contribution=worker_contribution,  # DB + DC 劳工缴费合计
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi,
            original_currency="TWD",
            details={
                'db_monthly_pension': db_monthly_pension,
                'dc_monthly_pension': dc_monthly_pension,
                'db_replacement_ratio': db_replacement_ratio,
                'dc_replacement_ratio': dc_replacement_ratio,
                'total_replacement_ratio': total_replacement_ratio,
                'dc_account_balance': dc_account_balance,
                'dc_total_contributions': dc_total_contrib,
                'dc_total_return': dc_total_return,
                'initial_annual_salary': db_result['Initial_Annual_Salary'],
                'final_annual_salary': db_result['Final_Annual_Salary'],
                'years_contributed': db_years,
                'work_years': db_years,
                'retirement_age': params.retire_age,
                'system_type': 'DB+DC',  # 双重制度
                'hide_summary': True  # 标记隐藏标准汇总指标
            }
        )

    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict[str, Any]]:
        """计算缴费历史"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        history = []
        current_age = person.age

        for year in range(work_years):
            age = current_age + year
            salary = salary_profile.get_salary_at_age(age, person.age)

            # 将人民币月薪转换为新台币
            cny_to_twd_rate = 4.35  # 1 CNY = 4.35 TWD (2025年参考汇率)
            salary_twd = salary * cny_to_twd_rate

            # 台湾劳保有投保薪资上下限（2024年约为25,250-45,800新台币）
            min_insured_salary = 25250
            max_insured_salary = 45800
            insured_salary = min(max(salary_twd, min_insured_salary), max_insured_salary)

            # 总缴费（20%）
            total_contribution = insured_salary * 0.20 * 12

            # 个人缴费（约7%）
            personal_contribution = insured_salary * 0.07 * 12

            # 雇主缴费（约13%）
            employer_contribution = insured_salary * 0.13 * 12

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'insured_salary': insured_salary,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': total_contribution
            })

        return history

    def _calculate_average_insured_salary(self,
                                        contribution_history: List[Dict[str, Any]]) -> float:
        """计算平均月投保薪资"""
        if not contribution_history:
            return 0

        total_insured_salary = sum(record['insured_salary'] for record in contribution_history)
        return total_insured_salary / len(contribution_history)

    def _calculate_labor_pension(self,
                               avg_insured_salary: float,
                               work_years: int,
                               economic_factors: EconomicFactors) -> float:
        """计算劳保年金"""
        # 台湾劳保年金计算公式
        # 月年金 = 平均月投保薪资 × 年资 × 1.55% × 0.65

        # 基础年金
        base_pension = avg_insured_salary * work_years * 0.0155

        # 考虑投资回报的调整系数
        investment_factor = 0.65

        monthly_pension = base_pension * investment_factor

        return monthly_pension

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
