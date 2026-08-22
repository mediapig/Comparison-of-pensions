// Port of plugins/taiwan/pension_calculator.py, plugins/taiwan/tax_calculator.py and plugins/taiwan/plugin.py.
import type { CountryModule, PensionResult, SocialSecurityResult, TaxResult } from './types'

const RETIREMENT_AGE = 65
const WORK_YEARS = 35 // person.work_years is always 0 from the base create_person(), so the Python fallback of 35 is always used

const TAX_BRACKETS: Array<[number, number, number]> = [
  [0, 560000, 0.05],
  [560000, 1260000, 0.12],
  [1260000, 2520000, 0.20],
  [2520000, 4720000, 0.30],
  [4720000, Infinity, 0.40],
]

function calculateTax(annualIncome: number): TaxResult {
  const basicDeduction = 92000
  const laborInsuranceDeduction = Math.min(annualIncome * 0.02, 24000)
  const totalDeductions = basicDeduction + laborInsuranceDeduction
  const taxableIncome = Math.max(0, annualIncome - totalDeductions)

  if (taxableIncome <= 0) {
    return { totalTax: 0, taxableIncome: 0, effectiveRate: 0, netIncome: annualIncome }
  }

  let totalTax = 0
  for (const [min, max, rate] of TAX_BRACKETS) {
    if (taxableIncome > min) {
      const taxableInBracket = Math.min(taxableIncome - min, max - min)
      if (taxableInBracket > 0) totalTax += taxableInBracket * rate
    }
  }

  return {
    totalTax,
    taxableIncome,
    effectiveRate: annualIncome > 0 ? (totalTax / annualIncome) * 100 : 0,
    netIncome: annualIncome - totalTax,
  }
}

function calculateSocialSecurity(monthlySalary: number, years: number): SocialSecurityResult {
  const employeeRate = 0.02
  const employerRate = 0.07
  const monthlyEmployee = monthlySalary * employeeRate
  const monthlyEmployer = monthlySalary * employerRate
  return {
    monthlyEmployee,
    monthlyEmployer,
    totalEmployee: monthlyEmployee * 12 * years,
    totalEmployer: monthlyEmployer * 12 * years,
    totalLifetime: (monthlyEmployee + monthlyEmployer) * 12 * years,
  }
}

function calculatePension(monthlySalary: number): PensionResult {
  const employeeRate = 0.02
  const employerRate = 0.07

  const monthlyEmployee = monthlySalary * employeeRate
  const monthlyEmployer = monthlySalary * employerRate
  const monthlyTotal = monthlyEmployee + monthlyEmployer

  const totalContribution = monthlyTotal * 12 * WORK_YEARS

  const annualReturn = 0.03
  const totalBalance = totalContribution * Math.pow(1 + annualReturn, WORK_YEARS)

  const monthlyPension = monthlySalary * 0.6 // ~60% replacement rate (a simplification in the original source)

  const retirementYears = 20
  const totalBenefit = monthlyPension * 12 * retirementYears
  const roi = totalContribution > 0 ? ((totalBenefit / totalContribution) - 1) * 100 : 0

  const breakEvenAge = monthlyPension > 0 ? RETIREMENT_AGE + totalContribution / (monthlyPension * 12) : null

  return {
    monthlyPension,
    totalContribution,
    totalBenefit,
    retirementAccountBalance: totalBalance,
    breakEvenAge,
    roi,
    currency: 'TWD',
    retirementAge: RETIREMENT_AGE,
    workYears: WORK_YEARS,
    details: {
      laborInsuranceRate: 0.11,
    },
  }
}

export const taiwanModule: CountryModule = {
  code: 'TW',
  name: '台湾',
  nameEn: 'Taiwan',
  currency: 'TWD',
  flag: '🇹🇼',
  calculatePension,
  calculateTax,
  calculateSocialSecurity,
  getRetirementAge: () => RETIREMENT_AGE,
}
