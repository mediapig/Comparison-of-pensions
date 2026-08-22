// Port of plugins/japan/japan_corrected_calculator.py (used for both calculate_pension and calculate_tax
// in plugins/japan/plugin.py).
import type { CountryModule, PensionResult, SocialSecurityResult, TaxResult } from './types'

const RETIREMENT_AGE = 65
const START_AGE = 30
const WORK_YEARS = RETIREMENT_AGE - START_AGE // person.age is always exactly 30, so work_years = 65 - 30 = 35

function calcSalaryDeduction(annualSalary: number): number {
  if (annualSalary <= 1_800_000) return annualSalary * 0.4 - 100_000
  if (annualSalary <= 3_600_000) return annualSalary * 0.3 + 80_000
  if (annualSalary <= 6_600_000) return annualSalary * 0.2 + 440_000
  if (annualSalary <= 8_500_000) return annualSalary * 0.1 + 1_100_000
  return 1_950_000
}

const INCOME_TAX_BRACKETS: Array<[number, number, number]> = [
  [0, 1_950_000, 0.05],
  [1_950_000, 3_300_000, 0.10],
  [3_300_000, 6_950_000, 0.20],
  [6_950_000, 9_000_000, 0.23],
  [9_000_000, 18_000_000, 0.33],
  [18_000_000, 40_000_000, 0.40],
  [40_000_000, Infinity, 0.45],
]

function calcIncomeTaxCorrected(taxableIncome: number): number {
  if (taxableIncome <= 0) return 0
  let tax = 0
  for (const [min, max, rate] of INCOME_TAX_BRACKETS) {
    if (taxableIncome > min) {
      const taxableInBracket = Math.min(taxableIncome - min, max - min)
      tax += taxableInBracket * rate
    }
  }
  return tax
}

interface SocialSecurityBreakdown {
  kosei: { employee: number; employer: number; total: number; base: number }
  kenko: { employee: number; employer: number; total: number; base: number }
  koyo: { employee: number; employer: number; total: number }
}

function calcSocialSecurityCorrected(monthlySalary: number): SocialSecurityBreakdown {
  const koseiBase = Math.min(monthlySalary, 650_000)
  const koseiTotal = koseiBase * 0.183
  const koseiEmployee = koseiTotal / 2
  const koseiEmployer = koseiTotal / 2

  const kenkoBase = Math.min(monthlySalary, 1_390_000)
  const kenkoTotal = kenkoBase * 0.10
  const kenkoEmployee = kenkoTotal / 2
  const kenkoEmployer = kenkoTotal / 2

  const koyoTotal = monthlySalary * 0.009
  const koyoEmployee = monthlySalary * 0.006
  const koyoEmployer = monthlySalary * 0.003

  return {
    kosei: { employee: koseiEmployee, employer: koseiEmployer, total: koseiTotal, base: koseiBase },
    kenko: { employee: kenkoEmployee, employer: kenkoEmployer, total: kenkoTotal, base: kenkoBase },
    koyo: { employee: koyoEmployee, employer: koyoEmployer, total: koyoTotal },
  }
}

function calcPensionCorrected(monthlySalary: number, workYears: number) {
  const monthsEnrolled = workYears * 12
  const fullKokuminMonth = 66_250
  const kokuminMonthly = fullKokuminMonth * Math.min(1.0, monthsEnrolled / 480.0)

  const avgStdWage = Math.min(monthlySalary, 650_000)
  const koseiMonthly = (avgStdWage * 5.481 / 1000 * monthsEnrolled) / 12

  return { kokuminMonthly, koseiMonthly, totalMonthly: kokuminMonthly + koseiMonthly }
}

function calculateTax(annualIncome: number): TaxResult {
  const monthlySalary = annualIncome / 12
  const socialSecurity = calcSocialSecurityCorrected(monthlySalary)
  const annualSsEmployee = (socialSecurity.kosei.employee + socialSecurity.kenko.employee + socialSecurity.koyo.employee) * 12

  const salaryDeduction = calcSalaryDeduction(annualIncome)
  const basicDeduction = 480_000
  const taxableIncome = Math.max(0, annualIncome - salaryDeduction - basicDeduction - annualSsEmployee)
  const incomeTax = calcIncomeTaxCorrected(taxableIncome)
  const residentTax = taxableIncome * 0.10
  const totalTax = incomeTax + residentTax

  return {
    totalTax,
    taxableIncome,
    effectiveRate: annualIncome > 0 ? (totalTax / annualIncome) * 100 : 0,
    netIncome: annualIncome - totalTax - annualSsEmployee,
  }
}

function calculateSocialSecurity(monthlySalary: number, years: number): SocialSecurityResult {
  const ss = calcSocialSecurityCorrected(monthlySalary)
  const monthlyEmployee = ss.kosei.employee + ss.kenko.employee + ss.koyo.employee
  const monthlyEmployer = ss.kosei.employer + ss.kenko.employer + ss.koyo.employer
  return {
    monthlyEmployee,
    monthlyEmployer,
    totalEmployee: monthlyEmployee * 12 * years,
    totalEmployer: monthlyEmployer * 12 * years,
    totalLifetime: (monthlyEmployee + monthlyEmployer) * 12 * years,
  }
}

function calculatePension(monthlySalary: number): PensionResult {
  const workYears = WORK_YEARS

  const socialSecurity = calcSocialSecurityCorrected(monthlySalary)
  const annualSsEmployee = (socialSecurity.kosei.employee + socialSecurity.kenko.employee + socialSecurity.koyo.employee) * 12

  const pensionInfo = calcPensionCorrected(monthlySalary, workYears)

  const retirementYears = 20
  const totalBenefit = pensionInfo.totalMonthly * 12 * retirementYears

  const totalPersonalContribution = annualSsEmployee * workYears
  const roi = totalPersonalContribution > 0 ? ((totalBenefit / totalPersonalContribution) - 1) * 100 : 0

  const breakEvenYears = pensionInfo.totalMonthly > 0 ? totalPersonalContribution / (pensionInfo.totalMonthly * 12) : 0
  const breakEvenAge = RETIREMENT_AGE + breakEvenYears

  return {
    monthlyPension: pensionInfo.totalMonthly,
    totalContribution: totalPersonalContribution,
    totalBenefit,
    retirementAccountBalance: totalPersonalContribution,
    breakEvenAge,
    roi,
    currency: 'JPY',
    retirementAge: RETIREMENT_AGE,
    workYears,
    details: {
      kokuminMonthly: pensionInfo.kokuminMonthly,
      koseiMonthly: pensionInfo.koseiMonthly,
      annualSsEmployee,
      annualSsEmployer: (socialSecurity.kosei.employer + socialSecurity.kenko.employer + socialSecurity.koyo.employer) * 12,
    },
  }
}

export const japanModule: CountryModule = {
  code: 'JP',
  name: '日本',
  nameEn: 'Japan',
  currency: 'JPY',
  flag: '🇯🇵',
  calculatePension,
  calculateTax,
  calculateSocialSecurity,
  getRetirementAge: () => RETIREMENT_AGE,
}
