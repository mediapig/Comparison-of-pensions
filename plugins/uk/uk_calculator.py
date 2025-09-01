from typing import Dict, Any, List
import math
from datetime import date
from dataclasses import dataclass
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

@dataclass
class UKTaxBands:
    """UK Tax Bands and Rates (2024/25 Tax Year)"""
    personal_allowance: float = 12570.0
    basic_rate_threshold: float = 37700.0  # £12,570 - £50,270
    higher_rate_threshold: float = 125140.0  # £50,270 - £125,140
    additional_rate_threshold: float = float('inf')  # £125,140+
    
    basic_tax_rate: float = 0.20
    higher_tax_rate: float = 0.40
    additional_tax_rate: float = 0.45
    
    # National Insurance rates
    ni_lower_earnings_limit: float = 6240.0  # LEL
    ni_primary_threshold: float = 12570.0  # PT
    ni_upper_earnings_limit: float = 50270.0  # UEL
    
    ni_employee_rate_main: float = 0.12  # 12% between PT and UEL
    ni_employee_rate_additional: float = 0.02  # 2% above UEL
    ni_employer_rate_main: float = 0.138  # 13.8% above PT
    ni_employer_rate_allowance: float = 5000.0  # Employment allowance

@dataclass
class UKPensionParams:
    """Enhanced UK Pension Parameters"""
    # Workplace pension auto-enrollment
    min_employee_rate: float = 0.05  # 5% minimum employee contribution
    min_employer_rate: float = 0.03  # 3% minimum employer contribution
    max_employee_rate: float = 0.10  # Typical maximum employee contribution
    max_employer_rate: float = 0.08  # Typical maximum employer contribution
    
    # Auto-enrollment thresholds
    ae_lower_earnings_limit: float = 6240.0  # £6,240 per year
    ae_upper_earnings_limit: float = 50270.0  # £50,270 per year
    
    # Annual and lifetime allowances
    annual_allowance: float = 60000.0  # Annual contribution allowance
    money_purchase_annual_allowance: float = 10000.0  # For those with pension access
    
    # State pension
    full_state_pension_weekly: float = 203.85  # 2024/25 rate
    qualifying_years_for_full_pension: int = 35
    minimum_qualifying_years: int = 10
    
    # Investment assumptions
    default_annual_return: float = 0.05  # 5% nominal return
    conservative_return: float = 0.04  # 4% conservative estimate
    optimistic_return: float = 0.06  # 6% optimistic estimate
    
    # Economic factors
    inflation_rate: float = 0.025  # 2.5% target inflation
    wage_growth_rate: float = 0.025  # 2.5% nominal wage growth
    
    # Retirement income options
    annuity_rate: float = 0.05  # Approximate annuity rate
    drawdown_rate: float = 0.04  # Sustainable drawdown rate

class UKPensionCalculator(BasePensionCalculator):
    """Enhanced UK pension calculator with comprehensive workplace and state pension calculations"""

    def __init__(self):
        self.tax_bands = UKTaxBands()
        self.pension_params = UKPensionParams()
        super().__init__("UK", "英国")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取英国退休年龄"""
        return {
            "male": 67,      # 国家养老金请领年龄 (升至67岁)
            "female": 67
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取英国缴费比例 (workplace pension auto-enrollment)"""
        employee_rate = self.pension_params.min_employee_rate
        employer_rate = self.pension_params.min_employer_rate
        return {
            "employee": employee_rate,        # 5% workplace pension employee
            "employer": employer_rate,        # 3% workplace pension employer
            "total": employee_rate + employer_rate,  # 8% total workplace pension
            "civil_servant": 0.055,   # 公务员平均缴费比例 (稍高)
            "self_employed": 0.05,    # 自雇人士可选择缴费比例
            "farmer": 0.05            # 农民可选择缴费比例
        }
    
    def calculate_income_tax(self, annual_income: float) -> float:
        """Calculate UK income tax"""
        if annual_income <= self.tax_bands.personal_allowance:
            return 0.0
        
        tax = 0.0
        taxable_income = annual_income - self.tax_bands.personal_allowance
        
        # Basic rate
        basic_band = min(taxable_income, self.tax_bands.basic_rate_threshold)
        tax += basic_band * self.tax_bands.basic_tax_rate
        
        if taxable_income > self.tax_bands.basic_rate_threshold:
            # Higher rate
            higher_band = min(taxable_income - self.tax_bands.basic_rate_threshold,
                            self.tax_bands.higher_rate_threshold - self.tax_bands.basic_rate_threshold)
            tax += higher_band * self.tax_bands.higher_tax_rate
            
            if taxable_income > self.tax_bands.higher_rate_threshold:
                # Additional rate
                additional_band = taxable_income - self.tax_bands.higher_rate_threshold
                tax += additional_band * self.tax_bands.additional_tax_rate
        
        return tax
    
    def calculate_national_insurance(self, annual_income: float) -> Dict[str, float]:
        """Calculate UK National Insurance contributions"""
        employee_ni = 0.0
        employer_ni = 0.0
        
        if annual_income > self.tax_bands.ni_primary_threshold:
            # Employee NI
            main_band = min(annual_income - self.tax_bands.ni_primary_threshold,
                          self.tax_bands.ni_upper_earnings_limit - self.tax_bands.ni_primary_threshold)
            employee_ni += main_band * self.tax_bands.ni_employee_rate_main
            
            if annual_income > self.tax_bands.ni_upper_earnings_limit:
                additional_band = annual_income - self.tax_bands.ni_upper_earnings_limit
                employee_ni += additional_band * self.tax_bands.ni_employee_rate_additional
            
            # Employer NI
            employer_ni = (annual_income - self.tax_bands.ni_primary_threshold) * self.tax_bands.ni_employer_rate_main
            # Apply employment allowance (simplified - assume it applies)
            employer_ni = max(0, employer_ni - self.tax_bands.ni_employer_rate_allowance)
        
        return {
            "employee_ni": employee_ni,
            "employer_ni": employer_ni,
            "total_ni": employee_ni + employer_ni
        }
    
    def calculate_workplace_pension_contributions(self, annual_salary: float, 
                                                employee_rate: float = None,
                                                employer_rate: float = None) -> Dict[str, float]:
        """Calculate workplace pension contributions with auto-enrollment rules"""
        
        # Use provided rates or defaults
        emp_rate = employee_rate or self.pension_params.min_employee_rate
        er_rate = employer_rate or self.pension_params.min_employer_rate
        
        # Auto-enrollment qualifying earnings (between £6,240 and £50,270)
        qualifying_earnings = max(0, 
            min(annual_salary, self.pension_params.ae_upper_earnings_limit) - 
            self.pension_params.ae_lower_earnings_limit)
        
        # Calculate contributions
        employee_contrib = qualifying_earnings * emp_rate
        employer_contrib = qualifying_earnings * er_rate
        
        # Apply annual allowance cap
        total_contrib = employee_contrib + employer_contrib
        if total_contrib > self.pension_params.annual_allowance:
            ratio = self.pension_params.annual_allowance / total_contrib
            employee_contrib *= ratio
            employer_contrib *= ratio
            total_contrib = self.pension_params.annual_allowance
        
        # Tax relief on employee contributions (20% basic rate assumption)
        tax_relief = employee_contrib * 0.20
        net_employee_contrib = employee_contrib - tax_relief
        
        return {
            "qualifying_earnings": qualifying_earnings,
            "employee_contribution": employee_contrib,
            "employer_contribution": employer_contrib,
            "total_contribution": total_contrib,
            "tax_relief": tax_relief,
            "net_employee_cost": net_employee_contrib
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """Calculate comprehensive UK pension including state pension and workplace pension"""
        # 1) 年限
        retirement_age = self.get_retirement_age(person)
        start_age = 30
        years = retirement_age - start_age   # 68-30 = 38

        if years <= 0:
            years = person.work_years

        # 2) 累积职场养老金（保持现有循环逻辑）
        monthly_salary_cny = salary_profile.base_salary
        cny_to_gbp_rate = 0.11  # 1 CNY = 0.11 GBP
        annual_salary_gbp = monthly_salary_cny * 12 * cny_to_gbp_rate
        
        balance = 0.0
        total_wp_contrib = 0.0
        wage_growth = self.pension_params.wage_growth_rate  # 2.5%
        annual_return = self.pension_params.default_annual_return  # 5%
        
        current_salary = annual_salary_gbp
        for year in range(years):
            # Calculate workplace pension contributions
            workplace_pension = self.calculate_workplace_pension_contributions(current_salary)
            annual_contrib = workplace_pension['total_contribution']
            
            # Add contribution and compound growth
            balance = balance * (1 + annual_return) + annual_contrib
            total_wp_contrib += annual_contrib
            
            # Apply wage growth for next year
            current_salary *= (1 + wage_growth)

        # 3) State Pension 按年限比例
        full_sp_annual = 11502.0  # 2024/25 full state pension per year
        qual_years = years
        sp_ratio = min(qual_years / 35.0, 1.0)
        state_pension_annual = full_sp_annual * sp_ratio
        monthly_sp = state_pension_annual / 12.0

        # 4) 职场养老金年金折算 (保持原有 i=0.03, n=20*12)
        i = 0.03 / 12  # 3% annual rate, monthly
        n = 20 * 12    # 20 years * 12 months
        if i > 0:
            monthly_wp = balance * i / (1 - (1 + i) ** -n)
        else:
            monthly_wp = balance / n

        # 5) ROI/总收益仅针对职场养老金
        final_wp_balance = balance
        total_return = final_wp_balance - total_wp_contrib
        roi_pct = (final_wp_balance / total_wp_contrib - 1.0) if total_wp_contrib > 0 else 0.0

        # 6) 总月养老金
        monthly_total = monthly_sp + monthly_wp

        # Debug output
        print(f"国家养老金（月）：£{monthly_sp:.2f}")
        print(f"职场养老金（月）：£{monthly_wp:.2f}")
        print(f"合计（月）：£{monthly_total:.2f}")
        print(f"职场养老金账户余额：£{final_wp_balance:,.2f}")
        print(f"职场养老金总缴费：£{total_wp_contrib:,.2f}")
        print(f"职场养老金总收益：£{total_return:,.2f}")
        print(f"职场养老金ROI：{roi_pct*100:.1f}%")

        # Calculate total benefit (life expectancy to 85)
        life_expectancy = 85
        retirement_years = life_expectancy - retirement_age
        total_benefit = monthly_total * 12 * retirement_years

        # Calculate break-even age based on workplace pension contributions only
        break_even_age = self._calculate_break_even_age(
            total_wp_contrib, monthly_total, retirement_age
        )

        return PensionResult(
            monthly_pension=monthly_total,
            total_contribution=total_wp_contrib,
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi_pct,
            original_currency="GBP",
            details={
                'state_pension_monthly': monthly_sp,
                'workplace_pension_monthly': monthly_wp,
                'workplace_pension_pot': final_wp_balance,
                'total_workplace_contribution': total_wp_contrib,
                'total_return': total_return,
                'work_years': years,
                'retirement_age': retirement_age,
                'qualifying_years': min(years, self.pension_params.qualifying_years_for_full_pension),
                'state_pension_annual': state_pension_annual,
                'workplace_pension_balance': final_wp_balance
            }
        )
    
    def _calculate_workplace_pension_pot(self, 
                                       contribution_history: List[Dict[str, Any]],
                                       economic_factors: EconomicFactors) -> float:
        """Calculate workplace pension pot with compound growth and inflation adjustment"""
        pot_value = 0.0
        annual_return = self.pension_params.default_annual_return
        inflation_rate = economic_factors.inflation_rate if hasattr(economic_factors, 'inflation_rate') else self.pension_params.inflation_rate
        
        # Use real return (nominal return - inflation)
        real_return = annual_return - inflation_rate
        
        for record in contribution_history:
            # Add annual contribution and compound growth
            annual_contribution = record.get('total_workplace_contribution', 0)
            pot_value = pot_value * (1 + real_return) + annual_contribution
        
        # Convert back to nominal terms
        years = len(contribution_history)
        inflation_factor = (1 + inflation_rate) ** years
        
        return pot_value * inflation_factor
    
    def _calculate_workplace_pension_income(self, pension_pot: float, retirement_age: int) -> float:
        """Calculate monthly income from workplace pension pot"""
        if pension_pot <= 0:
            return 0.0
        
        # Use drawdown approach (4% annual withdrawal rate)
        annual_income = pension_pot * self.pension_params.drawdown_rate
        return annual_income / 12

    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict[str, Any]]:
        """Calculate comprehensive contribution history including taxes, NI, and workplace pension"""
        retirement_age = self.get_retirement_age(person)
        start_age = 30
        work_years = retirement_age - start_age   # 68-30 = 38

        if work_years <= 0:
            work_years = person.work_years

        history = []
        current_age = person.age

        for year in range(work_years):
            age = current_age + year
            monthly_salary_cny = salary_profile.get_salary_at_age(age, person.age)

            # Convert CNY monthly salary to GBP annual salary
            cny_to_gbp_rate = 0.11  # 1 CNY = 0.11 GBP (2025 reference rate)
            annual_salary_gbp = monthly_salary_cny * 12 * cny_to_gbp_rate
            
            # Apply wage growth
            annual_salary_gbp *= (1 + self.pension_params.wage_growth_rate) ** year

            # Calculate income tax
            income_tax = self.calculate_income_tax(annual_salary_gbp)

            # Calculate National Insurance
            ni_calculations = self.calculate_national_insurance(annual_salary_gbp)

            # Calculate workplace pension contributions
            workplace_pension = self.calculate_workplace_pension_contributions(annual_salary_gbp)

            # Calculate net take-home pay
            gross_pay = annual_salary_gbp
            total_deductions = (income_tax + 
                              ni_calculations['employee_ni'] + 
                              workplace_pension['net_employee_cost'])
            net_pay = gross_pay - total_deductions

            history.append({
                'age': age,
                'year': person.start_work_date.year + year if hasattr(person, 'start_work_date') else 2025 + year,
                'monthly_salary_cny': monthly_salary_cny,
                'annual_salary_gbp': annual_salary_gbp,
                'income_tax': income_tax,
                'employee_ni': ni_calculations['employee_ni'],
                'employer_ni': ni_calculations['employer_ni'],
                'employee_contribution': workplace_pension['employee_contribution'],
                'employer_contribution': workplace_pension['employer_contribution'],
                'total_workplace_contribution': workplace_pension['total_contribution'],
                'tax_relief': workplace_pension['tax_relief'],
                'net_employee_cost': workplace_pension['net_employee_cost'],
                'qualifying_earnings': workplace_pension['qualifying_earnings'],
                'gross_pay': gross_pay,
                'net_pay': net_pay,
                # Legacy fields for compatibility
                'salary': monthly_salary_cny,
                'personal_contribution': workplace_pension['employee_contribution'],
                'total_contribution': workplace_pension['total_contribution']
            })

        return history

    def _calculate_state_pension(self,
                               contribution_history: List[Dict[str, Any]],
                               work_years: int,
                               economic_factors: EconomicFactors) -> float:
        """Calculate UK State Pension with enhanced logic"""
        
        # Full state pension amount (2024/25 rates)
        full_pension_weekly = self.pension_params.full_state_pension_weekly
        full_pension_monthly = full_pension_weekly * 52 / 12

        # Count qualifying years (years with sufficient NI contributions)
        qualifying_years = 0
        for record in contribution_history:
            # Need to earn above lower earnings limit and pay NI
            annual_salary = record.get('annual_salary_gbp', 0)
            if annual_salary >= self.tax_bands.ni_lower_earnings_limit:
                qualifying_years += 1

        # Apply state pension rules
        # Need minimum 10 qualifying years to get any state pension
        if qualifying_years < self.pension_params.minimum_qualifying_years:
            return 0.0

        # Calculate proportion based on qualifying years (max 35 years for full pension)
        max_qualifying_years = self.pension_params.qualifying_years_for_full_pension
        effective_years = min(qualifying_years, max_qualifying_years)
        
        adjustment_factor = effective_years / max_qualifying_years
        monthly_state_pension = full_pension_monthly * adjustment_factor

        return monthly_state_pension

    def _calculate_break_even_age(self,
                                total_contribution: float,
                                monthly_pension: float,
                                retirement_age: int) -> int:
        """Calculate break-even age for pension recovery"""
        if monthly_pension <= 0:
            return None

        months_to_break_even = total_contribution / monthly_pension
        years_to_break_even = months_to_break_even / 12

        return retirement_age + int(years_to_break_even)
    
    def format_currency_with_conversion(self, amount_gbp: float, cny_to_gbp_rate: float = 0.11) -> str:
        """Format GBP amount with CNY conversion"""
        amount_cny = amount_gbp / cny_to_gbp_rate
        return f"£{amount_gbp:,.2f} (¥{amount_cny:,.0f})"
    
    def generate_detailed_report(self, result: PensionResult, 
                               contribution_history: List[Dict[str, Any]],
                               person: Person) -> Dict[str, Any]:
        """Generate comprehensive pension report"""
        
        details = result.details
        cny_to_gbp_rate = 0.11
        
        # Summary statistics
        total_years = details['work_years']
        qualifying_years = details['qualifying_years']
        
        # Financial breakdown
        workplace_pot = details['workplace_pension_pot']
        state_pension_annual = details['state_pension_monthly'] * 12
        workplace_pension_annual = details['workplace_pension_monthly'] * 12
        total_annual_pension = result.monthly_pension * 12
        
        # Contribution analysis
        total_employee = details['total_employee_contribution']
        total_employer = details['total_employer_contribution'] 
        total_tax_relief = details['total_tax_relief']
        effective_cost = details['effective_employee_cost']
        
        # Performance metrics
        replacement_ratio = 0.0
        if contribution_history:
            final_salary = contribution_history[-1]['annual_salary_gbp']
            replacement_ratio = total_annual_pension / final_salary if final_salary > 0 else 0
        
        return {
            "summary": {
                "total_monthly_pension_gbp": result.monthly_pension,
                "total_monthly_pension_cny": result.monthly_pension / cny_to_gbp_rate,
                "state_pension_monthly_gbp": details['state_pension_monthly'],
                "workplace_pension_monthly_gbp": details['workplace_pension_monthly'],
                "workplace_pension_pot_gbp": workplace_pot,
                "replacement_ratio_percent": replacement_ratio * 100,
                "roi_percent": result.roi * 100,
                "break_even_age": result.break_even_age
            },
            "contributions": {
                "total_employee_contributions_gbp": total_employee,
                "total_employer_contributions_gbp": total_employer,
                "total_tax_relief_gbp": total_tax_relief,
                "effective_employee_cost_gbp": effective_cost,
                "years_contributing": total_years,
                "qualifying_years_state_pension": qualifying_years
            },
            "projections": {
                "life_expectancy_years": 85,
                "retirement_age": details['retirement_age'],
                "total_lifetime_benefit_gbp": result.total_benefit,
                "annual_pension_gbp": total_annual_pension,
                "state_pension_annual_gbp": state_pension_annual,
                "workplace_pension_annual_gbp": workplace_pension_annual
            },
            "formatted_summary": self._format_pension_summary(result, details, cny_to_gbp_rate)
        }
    
    def _format_pension_summary(self, result: PensionResult, details: Dict, cny_to_gbp_rate: float) -> str:
        """Format a readable pension summary"""
        
        summary = f"""
🇬🇧 UK PENSION CALCULATION SUMMARY
{'=' * 50}

💰 MONTHLY PENSION INCOME:
   State Pension: {self.format_currency_with_conversion(details['state_pension_monthly'], cny_to_gbp_rate)}
   Workplace Pension: {self.format_currency_with_conversion(details['workplace_pension_monthly'], cny_to_gbp_rate)}
   TOTAL MONTHLY: {self.format_currency_with_conversion(result.monthly_pension, cny_to_gbp_rate)}

🏦 PENSION POT AT RETIREMENT:
   Workplace Pension Pot: {self.format_currency_with_conversion(details['workplace_pension_pot'], cny_to_gbp_rate)}

💸 CONTRIBUTION SUMMARY:
   Employee Contributions: {self.format_currency_with_conversion(details['total_employee_contribution'], cny_to_gbp_rate)}
   Employer Contributions: {self.format_currency_with_conversion(details['total_employer_contribution'], cny_to_gbp_rate)}
   Tax Relief Received: {self.format_currency_with_conversion(details['total_tax_relief'], cny_to_gbp_rate)}
   Net Employee Cost: {self.format_currency_with_conversion(details['effective_employee_cost'], cny_to_gbp_rate)}

📊 PERFORMANCE:
   Return on Investment: {result.roi:.1%}
   Break-even Age: {result.break_even_age} years old
   Qualifying Years: {details['qualifying_years']}/{self.pension_params.qualifying_years_for_full_pension} for state pension
   
📈 LIFETIME PROJECTION:
   Total Lifetime Benefit: {self.format_currency_with_conversion(result.total_benefit, cny_to_gbp_rate)}
   Retirement Age: {details['retirement_age']} years old
   Working Years: {details['work_years']} years
        """
        
        return summary.strip()
