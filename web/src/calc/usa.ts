// Port of plugins/usa/plugin.py, plugins/usa/pension_calculator.py, plugins/usa/usa_401k_calculator.py,
// plugins/usa/usa_401k_params.py and plugins/usa/tax_calculator.py.
import type { CountryModule, PensionResult, SocialSecurityResult, TaxResult } from './types'

const RETIREMENT_AGE = 67
const START_AGE = 30 // person.age is always exactly 30 for the default create_person(start_age=30)
const STANDARD_DEDUCTION_2024 = 14600

const TAX_BRACKETS: Array<[number, number, number]> = [
  [0, 11000, 0.10],
  [11000, 44725, 0.12],
  [44725, 95375, 0.22],
  [95375, 182050, 0.24],
  [182050, 231250, 0.32],
  [231250, 578125, 0.35],
  [578125, Infinity, 0.37],
]

function calculateTax(annualIncome: number): TaxResult {
  const taxableIncome = Math.max(0, annualIncome - STANDARD_DEDUCTION_2024)
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
  const maxTaxable = 160200 / 12
  const contributionBase = Math.min(monthlySalary, maxTaxable)
  const monthlyEmployee = contributionBase * 0.062
  const monthlyEmployer = contributionBase * 0.062
  return {
    monthlyEmployee,
    monthlyEmployer,
    totalEmployee: monthlyEmployee * 12 * years,
    totalEmployer: monthlyEmployer * 12 * years,
    totalLifetime: (monthlyEmployee + monthlyEmployer) * 12 * years,
  }
}

// --- pension_calculator.py: Social Security benefit estimate ---

function calculateSsPension(monthlySalary: number, retirementYears = 23) {
  const workYears = 35 // person.work_years is always 0 from the base create_person(), so the Python fallback of 35 is always used
  const ssRate = 0.062 * 2
  const maxTaxableEarnings = 168600 / 12
  const contributionBase = Math.min(monthlySalary, maxTaxableEarnings)

  const annualContribution = contributionBase * 12 * ssRate

  let replacementRate: number
  if (contributionBase <= 5000) replacementRate = 0.40
  else if (contributionBase <= 10000) replacementRate = 0.30
  else replacementRate = 0.20
  if (contributionBase > 13350) replacementRate = 0.15

  const monthlyBenefit = contributionBase * replacementRate
  const totalContribution = annualContribution * workYears
  const totalBenefit = monthlyBenefit * 12 * retirementYears
  const roi = totalContribution > 0 ? ((totalBenefit / totalContribution) - 1) * 100 : 0

  let breakEvenAge: number | null = null
  if (monthlyBenefit > 0) {
    const breakEvenMonths = totalContribution / monthlyBenefit
    const candidate = RETIREMENT_AGE + breakEvenMonths / 12
    breakEvenAge = candidate < 85 ? Math.trunc(candidate) : null
  }

  return { monthlyBenefit, totalContribution, totalBenefit, roi, breakEvenAge, workYears }
}

// --- usa_401k_params.py + usa_401k_calculator.py ---

const K401_PARAMS_2025 = {
  employeeDeferralLimit: 23500,
  catchUpLimit50Plus: 7500,
  superCatchUp6063: 11250,
  totalContributionLimit: 70000,
  compensationCap: 350000,
}

function getEmployeeContributionLimit(age: number) {
  const baseLimit = K401_PARAMS_2025.employeeDeferralLimit
  let catchUp: number
  if (age >= 60 && age <= 63) catchUp = K401_PARAMS_2025.superCatchUp6063
  else if (age >= 50) catchUp = K401_PARAMS_2025.catchUpLimit50Plus
  else catchUp = 0
  return { baseLimit, catchUpLimit: catchUp, totalLimit: baseLimit + catchUp }
}

function calculateEmployerMatch(employeeContribution: number, annualSalary: number): number {
  const compensationForMatch = Math.min(annualSalary, K401_PARAMS_2025.compensationCap)
  // tiered_3_2 preset: 100% match on first 3%, 50% match on next 2%
  const tier1Contribution = Math.min(employeeContribution, compensationForMatch * 0.03)
  const tier1Match = tier1Contribution * 1.0
  const remainingContribution = Math.max(0, employeeContribution - tier1Contribution)
  const tier2Contribution = Math.min(remainingContribution, compensationForMatch * 0.02)
  const tier2Match = tier2Contribution * 0.5
  return tier1Match + tier2Match
}

interface K401YearlyContribution {
  employeeDeferral: number
  catchUpContribution: number
  totalEmployeeContribution: number
  employerMatch: number
  totalContribution: number
}

function calculate401kLifetime(startAge: number, retirementAge: number, initialAnnualSalary: number, salaryGrowthRate: number, deferralRate: number, investmentReturnRate: number) {
  const history: K401YearlyContribution[] = []
  let currentSalary = initialAnnualSalary

  for (let yearOffset = 0; yearOffset < retirementAge - startAge; yearOffset++) {
    const age = startAge + yearOffset
    const limits = getEmployeeContributionLimit(age)

    const targetDeferral = currentSalary * deferralRate
    const employeeDeferral = Math.min(targetDeferral, limits.baseLimit)
    const remainingDeferral = Math.max(0, targetDeferral - employeeDeferral)
    const catchUpContribution = limits.catchUpLimit > 0 ? Math.min(remainingDeferral, limits.catchUpLimit) : 0
    const totalEmployeeContribution = employeeDeferral + catchUpContribution

    const employerMatch = calculateEmployerMatch(employeeDeferral, currentSalary)
    const totalContribution = totalEmployeeContribution + employerMatch

    history.push({ employeeDeferral, catchUpContribution, totalEmployeeContribution, employerMatch, totalContribution })
    currentSalary *= 1 + salaryGrowthRate
  }

  let totalBalance = 0
  let totalEmployeeContributions = 0
  let totalEmployerContributions = 0
  for (let i = 0; i < history.length; i++) {
    const contrib = history[i]
    const yearsToRetirement = history.length - i - 1
    const futureValue = yearsToRetirement > 0 ? contrib.totalContribution * Math.pow(1 + investmentReturnRate, yearsToRetirement) : contrib.totalContribution
    totalBalance += futureValue
    totalEmployeeContributions += contrib.totalEmployeeContribution
    totalEmployerContributions += contrib.employerMatch
  }

  const annualWithdrawal = totalBalance * 0.04
  const monthlyWithdrawal = annualWithdrawal / 12

  const totalContributions = history.reduce((acc, c) => acc + c.totalContribution, 0)

  return {
    totalBalance,
    totalEmployeeContributions,
    totalEmployerContributions,
    annualWithdrawal,
    monthlyWithdrawal,
    totalContributions,
  }
}

function calculatePension(monthlySalary: number): PensionResult {
  const ss = calculateSsPension(monthlySalary)

  const initialAnnualSalaryUsd = monthlySalary * 12
  const k401 = calculate401kLifetime(START_AGE, RETIREMENT_AGE, initialAnnualSalaryUsd, 0.0, 0.10, 0.05)
  const k401RetirementYears = 85 - RETIREMENT_AGE
  const k401TotalBenefit = k401.annualWithdrawal * k401RetirementYears

  const totalMonthlyPension = ss.monthlyBenefit + k401.monthlyWithdrawal
  const totalContribution = ss.totalContribution + k401.totalContributions
  const totalBenefit = ss.totalBenefit + k401TotalBenefit
  const totalRoi = totalContribution > 0 ? ((totalBenefit / totalContribution) - 1) * 100 : 0

  return {
    monthlyPension: totalMonthlyPension,
    totalContribution,
    totalBenefit,
    retirementAccountBalance: k401.totalBalance,
    breakEvenAge: ss.breakEvenAge,
    roi: totalRoi,
    currency: 'USD',
    retirementAge: RETIREMENT_AGE,
    workYears: ss.workYears,
    details: {
      socialSecurityPension: ss.monthlyBenefit,
      k401Pension: k401.monthlyWithdrawal,
      k401Balance: k401.totalBalance,
      k401TotalContribution: k401.totalContributions,
      k401EmployerMatch: k401.totalEmployerContributions,
    },
  }
}

export const usaModule: CountryModule = {
  code: 'US',
  name: '美国',
  nameEn: 'USA',
  currency: 'USD',
  flag: '🇺🇸',
  calculatePension,
  calculateTax,
  calculateSocialSecurity,
  getRetirementAge: () => RETIREMENT_AGE,
}
