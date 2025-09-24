from typing import Dict, Any, List
import math
from datetime import date
from dataclasses import dataclass
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

@dataclass
class JPParams:
    start_age: int = 30
    retire_age: int = 65              # 35 年
    wage_growth: float = 0.0          # 工资年涨 0%
    epi_coef: float = 5.481 / 1000    # 厚生年金系数（年金/年）
    npi_full_annual: float = 780_000  # 国民年金满额/年（40 年）
    npi_full_years: int = 40
    epi_contrib_rate_total: float = 0.183  # 厚生年金合计缴费率（统计用）
    annuity_years: int = 20           # 展示：领取20年（65-85）

class JapanPensionCalculator(BasePensionCalculator):
    """日本退休金计算器（国民年金+厚生年金）"""

    def __init__(self):
        super().__init__("JP", "日本")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取日本退休年龄"""
        return {
            "male": 65,
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取日本缴费比例"""
        return {
            "employee": 0.183,      # 个人缴费比例 18.3%
            "employer": 0.183,      # 雇主缴费比例 18.3%
            "total": 0.366          # 总缴费比例 36.6%
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算日本退休金"""
        # 使用优化后的日本养老金算法
        init_salary_month = salary_profile.base_salary
        work_years = 35  # 固定工作35年
        salary_growth = salary_profile.annual_growth_rate

        # 调用精确算法
        result = self._calc_japan_pension_pure(
            init_salary_month, work_years, salary_growth
        )

        # 计算回本年龄
        break_even_age = self._calculate_break_even_age(
            result['total_contribution'], result['total_pension'], 65
        )

        return PensionResult(
            monthly_pension=result['total_pension'],
            total_contribution=result['total_contribution'],
            total_benefit=result['total_benefit'],
            break_even_age=break_even_age,
            roi=result['roi'],
            original_currency="JPY",
            details={
                'npi_monthly': result['npi_monthly'],
                'epi_monthly': result['epi_monthly'],
                'initial_salary': result['initial_salary'],
                'final_salary': result['final_salary'],
                'avg_salary': result['avg_salary'],
                'work_years': work_years
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

            # 将人民币转换为日元
            cny_to_jpy_rate = 20  # 1 CNY = 20 JPY
            salary_jpy = salary * cny_to_jpy_rate

            # 日本厚生年金缴费 18.3%
            personal_contribution = salary_jpy * 0.183 * 12
            employer_contribution = salary_jpy * 0.183 * 12

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary_jpy,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': personal_contribution + employer_contribution
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

    def calc_japan_pension(self, initial_monthly_salary_jpy: float, p: JPParams = JPParams()) -> Dict[str, float]:
        """日本养老金精确计算 - DB给付制度"""
        years = p.retire_age - p.start_age  # = 35

        # 1) 生成35年工资序列（每年+2%）
        m = initial_monthly_salary_jpy
        monthly_series = []
        for _ in range(years):
            monthly_series.append(m)
            m *= 1.02

        # 2) 国民年金（NPI）：按年限比例折算
        NPI_FULL_ANNUAL = 780_000  # 满40年/年
        npi_annual = NPI_FULL_ANNUAL * (years / 40)
        npi_monthly = npi_annual / 12

        # 3) 厚生年金（EPI）：平均工资 × 年数 × 系数（DB 口径）
        EPI_COEF = 5.481 / 1000  # 年金额系数
        avg_monthly = sum(monthly_series) / len(monthly_series)
        avg_annual = avg_monthly * 12.0
        epi_annual = avg_annual * years * EPI_COEF
        epi_monthly = epi_annual / 12.0

        # 4) （可选统计）厚生年金累计缴费=工资×18.3%（仅统计、不参与给付）
        EPI_RATE_TOTAL = 0.183
        EPI_RATE_EMP   = 0.0915
        EPI_RATE_ER    = 0.0915

        # series 为 35 年每年"实际月薪"的列表
        epi_contrib_total = sum((m * 12.0) * EPI_RATE_TOTAL for m in monthly_series)
        epi_contrib_emp   = epi_contrib_total * (EPI_RATE_EMP / EPI_RATE_TOTAL)
        epi_contrib_er    = epi_contrib_total * (EPI_RATE_ER  / EPI_RATE_TOTAL)

        # 5) 合计月金 & 替代率（跨国统一：对比最后一年"实际月薪"）
        total_monthly = npi_monthly + epi_monthly
        last_month = monthly_series[-1]
        repl_vs_last = total_monthly / last_month

        return {
            # 基本信息
            "Years": years,
            "InitialMonthlySalary": initial_monthly_salary_jpy,
            "LastMonthlySalary": last_month,
            "AvgMonthlySalary": avg_monthly,

            # 给付（DB）
            "NPI_Monthly": npi_monthly,
            "EPI_Monthly": epi_monthly,
            "Total_Monthly": total_monthly,
            "Replacement_vs_LastMonth": repl_vs_last,  # 统一对比口径

            # 仅统计（DC式口径里常见，这里只是信息，不算 ROI）
            "EPI_TotalContrib": epi_contrib_total,
            "EPI_EmployeeContrib": epi_contrib_emp,
            "EPI_EmployerContrib": epi_contrib_er,
            "EPI_Rate_Total": EPI_RATE_TOTAL,
            "EPI_Rate_Employee": EPI_RATE_EMP,
            "EPI_Rate_Employer": EPI_RATE_ER,
        }

    def _calc_japan_pension_pure(self,
                                initial_salary_cny: float,
                                years: int = 35,
                                growth: float = 0.02):
        """精确的日本养老金计算算法（保持向后兼容）"""
        # 汇率转换：1 CNY = 20 JPY
        cny_to_jpy_rate = 20
        initial_salary_jpy = initial_salary_cny * cny_to_jpy_rate

        # 使用新的参数化方法
        params = JPParams(wage_growth=growth)
        result = self.calc_japan_pension(initial_salary_jpy, params)

        # 为了与旧系统兼容，计算总收益和ROI（虽然DB制度不需要）
        total_benefit = result["Total_Monthly"] * 12 * params.annuity_years
        roi = (total_benefit / result["EPI_TotalContrib"] - 1.0) if result["EPI_TotalContrib"] > 0 else 0

        return {
            "initial_salary": result["InitialMonthlySalary"],
            "final_salary": result["LastMonthlySalary"],
            "avg_salary": result["AvgMonthlySalary"],
            "npi_monthly": result["NPI_Monthly"],
            "epi_monthly": result["EPI_Monthly"],
            "total_pension": result["Total_Monthly"],
            "total_contribution": result["EPI_TotalContrib"],
            "total_benefit": total_benefit,
            "roi": roi
        }

# ===== 示例：人民币→日元换算（假设 1 CNY = 20 JPY）=====
if __name__ == "__main__":
    RMB_TO_JPY = 20.0
    high_month_jpy = 50_000 * RMB_TO_JPY   # 5万 RMB / 月
    low_month_jpy  = 5_000  * RMB_TO_JPY   # 5千 RMB / 月

    calculator = JapanPensionCalculator()
    high = calculator.calc_japan_pension(high_month_jpy)
    low  = calculator.calc_japan_pension(low_month_jpy)

    def p(label, d):
        print(f"\n=== {label} ===")
        print(f"年限: {d['Years']} 年")
        print(f"首月薪: ¥{d['InitialMonthlySalary']:,.0f}  | 末年实月薪: ¥{d['LastMonthlySalary']:,.0f}")
        print(f"平均月薪: ¥{d['AvgMonthlySalary']:,.0f}")

        print("\n📊 养老金给付（DB）")
        print(f"  国民年金(NPI): ¥{d['NPI_Monthly']:,.0f}/月")
        print(f"  厚生年金(EPI): ¥{d['EPI_Monthly']:,.0f}/月  （系数 5.481‰，年资 {d['Years']} 年）")
        print(f"  合计:           ¥{d['Total_Monthly']:,.0f}/月")
        print(f"  替代率（对比末年实际月薪）: {d['Replacement_vs_LastMonth']*100:.1f}%")

        print("\n💰 厚生年金累计缴费（仅统计口径）")
        print(f"  合计费率: {d['EPI_Rate_Total']*100:.1f}% ＝ 员工 {d['EPI_Rate_Employee']*100:.2f}% + 雇主 {d['EPI_Rate_Employer']*100:.2f}%")
        print(f"  累计缴费（合计）: ¥{d['EPI_TotalContrib']:,.0f} ＝ 员工 ¥{d['EPI_EmployeeContrib']:,.0f} + 雇主 ¥{d['EPI_EmployerContrib']:,.0f}")

        print("\nℹ️ 说明：日本公共年金为 DB 给付，不计算\"总收益 / ROI / 回本年龄\"。")

    p("日本-高收入（¥50k RMB/月）", high)
    p("日本-低收入（¥5k RMB/月）", low)
