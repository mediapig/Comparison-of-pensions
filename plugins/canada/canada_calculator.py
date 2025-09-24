from typing import Dict, Any, List
import math
from datetime import date
from dataclasses import dataclass
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

# ===== 常量（2025） =====
START_AGE, RETIRE_AGE = 30, 65
YEARS = RETIRE_AGE - START_AGE       # 35
WAGE_GROWTH = 0.0

CPP_RATE_EMP = 0.0595
CPP_RATE_ER  = 0.0595
CPP_RATE_TOTAL = CPP_RATE_EMP + CPP_RATE_ER

YBE   = 3500.0                       # Year's Basic Exemption
YMPE  = 71300.0                      # Year's Maximum Pensionable Earnings
YAMPE = 81200.0                      # CPP2 upper ceiling (二层，若不实现可忽略给付，只统计缴费)

CPP_MAX_MONTH_2025 = 1433.00         # 65岁最大CPP（2025年1月口径）
CPP_MAX_ANNUAL     = CPP_MAX_MONTH_2025 * 12

OAS_MAX_MONTH_65_74_2025Q3 = 734.95  # 65–74岁 OAS（2025 Q3）
OAS_MAX_ANNUAL = OAS_MAX_MONTH_65_74_2025Q3 * 12

# 汇率
CNY_TO_CAD_RATE = 0.19        # 1 CNY = 0.19 CAD (2025年参考汇率)

@dataclass
class CAParams:
    start_age: int = START_AGE
    retire_age: int = RETIRE_AGE
    years: int = YEARS
    wage_growth: float = WAGE_GROWTH
    cpp_rate_emp: float = CPP_RATE_EMP
    cpp_rate_er: float = CPP_RATE_ER
    cpp_rate_total: float = CPP_RATE_TOTAL
    ybe: float = YBE
    ympe: float = YMPE
    yampe: float = YAMPE
    cpp_max_annual: float = CPP_MAX_ANNUAL
    oas_max_annual: float = OAS_MAX_ANNUAL
    cny_to_cad_rate: float = CNY_TO_CAD_RATE

class CanadaPensionCalculator(BasePensionCalculator):
    """加拿大退休金计算器（CPP+OAS）"""

    def __init__(self):
        super().__init__("CA", "加拿大")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取加拿大退休年龄"""
        return {
            "male": 65,      # CPP和OAS请领年龄
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取加拿大缴费比例"""
        return {
            "employee": CPP_RATE_EMP,        # 5.95% CPP员工缴费（第一层）
            "employer": CPP_RATE_ER,         # 5.95% CPP雇主缴费（第一层）
            "total": CPP_RATE_TOTAL,         # 11.9% CPP总缴费率（第一层）
            "cpp2_employee": 0.04,           # 4% CPP2员工缴费（第二层）
            "cpp2_employer": 0.04,           # 4% CPP2雇主缴费（第二层）
            "civil_servant": CPP_RATE_EMP,   # 公务员缴费比例
            "self_employed": CPP_RATE_TOTAL, # 自雇人士缴纳总额11.9%
            "farmer": CPP_RATE_EMP           # 农民缴费比例
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算加拿大退休金"""
        # 使用优化后的加拿大养老金算法
        init_salary_month = salary_profile.base_salary
        work_years = 35  # 固定工作35年
        salary_growth = salary_profile.annual_growth_rate

        # 调用精确算法
        result = self._calc_canada_pension_pure(
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
            original_currency="CAD",
            details={
                'cpp_monthly': result['cpp_monthly'],
                'oas_monthly': result['oas_monthly'],
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

            # 将人民币月薪转换为加币年薪
            annual_salary_cad = salary * 12 * CNY_TO_CAD_RATE

            # CPP第一层应税工资（扣除基本免税额，有上限）
            base = max(0.0, min(annual_salary_cad, YMPE) - YBE)
            # CPP2第二层应税工资
            tier2 = max(0.0, min(max(annual_salary_cad, YMPE), YAMPE) - max(YMPE, YBE))

            # 个人缴费（第一层 + 第二层）
            personal_contribution = base * CPP_RATE_EMP + tier2 * 0.04

            # 雇主缴费（第一层 + 第二层）
            employer_contribution = base * CPP_RATE_ER + tier2 * 0.04

            # 总缴费
            total_contribution = personal_contribution + employer_contribution

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'annual_salary_cad': annual_salary_cad,
                'cpp_base_earnings': base,
                'cpp2_tier2_earnings': tier2,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': total_contribution
            })

        return history

    def calc_canada_pension(self, initial_annual_salary_cad: float) -> Dict[str, float]:
        """加拿大养老金精确计算 - 2025标准（CPP+CPP2+OAS制度）"""

        # ===== 逐年统计：工资增长 + CPP 缴费 & 计算平均可计缴工资比例 =====
        salary = initial_annual_salary_cad       # 由人民币换算后的年薪（CAD）
        sum_pensionable = 0.0
        total_cpp_contrib_emp = total_cpp_contrib_er = 0.0

        for _ in range(YEARS):
            base = max(0.0, min(salary, YMPE) - YBE)           # 第一层可计缴
            # （可选统计CPP2第二层缴费）
            tier2 = max(0.0, min(max(salary, YMPE), YAMPE) - max(YMPE, YBE))
            # 累计可计缴工资（用于算平均）
            sum_pensionable += base
            # 缴费统计（仅统计口径）
            total_cpp_contrib_emp += base * CPP_RATE_EMP + tier2 * 0.04
            total_cpp_contrib_er  += base * CPP_RATE_ER  + tier2 * 0.04
            # 年末涨薪
            salary *= (1 + WAGE_GROWTH)

        avg_pensionable = sum_pensionable / YEARS
        avg_ratio = min(1.0, avg_pensionable / YMPE)

        # ===== 给付估算 =====
        cpp_annual = CPP_MAX_ANNUAL * min(1.0, YEARS / 39.0) * avg_ratio
        oas_annual = OAS_MAX_ANNUAL * min(1.0, YEARS / 40.0)  # 30–65默认35/40

        annual_pension = cpp_annual + oas_annual
        monthly_pension = annual_pension / 12

        # 替代率（对比末年年薪）
        last_year_salary = salary / (1 + WAGE_GROWTH)
        replacement_vs_last = annual_pension / last_year_salary

        return {
            # 基本信息
            "Years": YEARS,
            "InitialAnnualSalary": initial_annual_salary_cad,
            "LastAnnualSalary": last_year_salary,
            "InitialMonthlySalary": initial_annual_salary_cad / 12.0,
            "LastMonthlySalary": last_year_salary / 12.0,

            # 给付
            "CPP_Annual": cpp_annual,
            "OAS_Annual": oas_annual,
            "Total_Annual": annual_pension,
            "Total_Monthly": monthly_pension,
            "Replacement_vs_LastYear": replacement_vs_last,

            # 缴费统计（仅统计口径）
            "CPP_EmployeeContrib": total_cpp_contrib_emp,
            "CPP_EmployerContrib": total_cpp_contrib_er,
            "CPP_TotalContrib": total_cpp_contrib_emp + total_cpp_contrib_er,
            "CPP_Rate_Employee": CPP_RATE_EMP,
            "CPP_Rate_Employer": CPP_RATE_ER,
            "AvgPensionable": avg_pensionable,
            "AvgRatio": avg_ratio
        }

    def _calc_canada_pension_pure(self,
                                initial_salary_cny: float,
                                years: int = 35,
                                growth: float = 0.02):
        """精确的加拿大养老金计算算法 - DB制度（不计算ROI）"""
        # 汇率转换：1 CNY = 0.19 CAD
        initial_annual_salary_cad = initial_salary_cny * 12 * CNY_TO_CAD_RATE

        # 使用新的2025标准方法
        result = self.calc_canada_pension(initial_annual_salary_cad)

        # DB制度：不计算总收益、ROI、回本年龄
        # 仅返回给付信息和缴费统计
        return {
            "initial_salary": result["InitialMonthlySalary"],
            "final_salary": result["LastMonthlySalary"],
            "avg_salary": (result["InitialMonthlySalary"] + result["LastMonthlySalary"]) / 2,
            "cpp_monthly": result["CPP_Annual"] / 12.0,
            "oas_monthly": result["OAS_Annual"] / 12.0,
            "total_pension": result["Total_Monthly"],
            "total_contribution": result["CPP_EmployeeContrib"],  # 仅员工部分用于统计
            "total_benefit": 0,  # DB制度不适用
            "roi": 0,  # DB制度不适用
            "replacement_rate": result["Replacement_vs_LastYear"]
        }

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

# ===== 示例：人民币→加币换算（2025标准）=====
if __name__ == "__main__":
    high_annual_cad = 50_000 * 12 * CNY_TO_CAD_RATE   # 5万 RMB / 月
    low_annual_cad  = 5_000  * 12 * CNY_TO_CAD_RATE   # 5千 RMB / 月

    calculator = CanadaPensionCalculator()
    high = calculator.calc_canada_pension(high_annual_cad)
    low  = calculator.calc_canada_pension(low_annual_cad)

    def p(label, d):
        print(f"\n=== {label} ===")
        print(f"年限: {d['Years']} 年")
        print(f"首年年薪: ${d['InitialAnnualSalary']:,.0f}  | 末年年薪: ${d['LastAnnualSalary']:,.0f}")
        print(f"首月薪: ${d['InitialMonthlySalary']:,.0f}  | 末年实月薪: ${d['LastMonthlySalary']:,.0f}")

        print("\n📊 养老金给付（公共年金制）")
        print(f"  CPP: ${d['CPP_Annual']:,.0f}/年 | OAS: ${d['OAS_Annual']:,.0f}/年")
        print(f"  合计: ${d['Total_Annual']:,.0f}/年 ≈ ${d['Total_Monthly']:,.0f}/月")
        print(f"  替代率（对比末年年薪）: {d['Replacement_vs_LastYear']*100:.1f}%")

        print("\n💰 CPP 累计缴费（仅统计口径）")
        print(f"  费率: 员工 5.95% + 雇主 5.95%（第一层；第二层各 4%）")
        print(f"  员工累计: ${d['CPP_EmployeeContrib']:,.0f} | 雇主累计: ${d['CPP_EmployerContrib']:,.0f} | 合计: ${d['CPP_TotalContrib']:,.0f}")
        print(f"  平均可计缴工资: ${d['AvgPensionable']:,.0f} (比例: {d['AvgRatio']*100:.1f}%)")

        print("\nℹ️ 说明：CPP 与 OAS 为公共年金（DB/准DB），不计算总收益、投资回报率与回本年龄。")
        print("    OAS = 734.95(2025Q3, 65–74) × 12 × (居住年限/40) = 734.95×12×(35/40) ≈ 7,716.98/年")
        print("    CPP 满额口径采用：17,196/年（2025），并按年资与平均可计缴工资比例折算")

    p("加拿大-高收入（¥50k RMB/月）", high)
    p("加拿大-低收入（¥5k RMB/月）", low)
