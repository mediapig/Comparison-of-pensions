// Port of plugins/china/china_optimized_calculator.py (the "7-step algorithm" used by ChinaPlugin.calculate_pension)
// plus plugins/china/china_social_security_calculator.py (used by ChinaDetailedAnalyzer for the single-year /
// lifetime breakdown shown in the detail view).
import { bisectionIrr, clamp, type CountryModule, type PensionResult, type SocialSecurityResult, type TaxResult } from './types'

const TAX_BRACKETS: Array<[number, number, number, number]> = [
  [0, 36000, 0.03, 0],
  [36000, 144000, 0.10, 2520],
  [144000, 300000, 0.20, 16920],
  [300000, 420000, 0.25, 31920],
  [420000, 660000, 0.30, 52920],
  [660000, 960000, 0.35, 85920],
  [960000, Infinity, 0.45, 181920],
]

function calcTaxQuickDeduction(taxableIncome: number): number {
  if (taxableIncome <= 0) return 0
  for (const [min, max, rate, deduction] of TAX_BRACKETS) {
    if (taxableIncome > min && taxableIncome <= max) {
      return taxableIncome * rate - deduction
    }
  }
  return 0
}

const PARAMS = {
  empPensionRate: 0.08,
  empMedicalRate: 0.02,
  empUnempRate: 0.005,
  erPensionRate: 0.16,
  erMedicalRate: 0.09,
  erUnempRate: 0.005,
  erInjuryRate: 0.0016,
  hfRateDefault: 0.07,
  hfBaseLower: 2690,
  hfBaseUpper: 36921,
  basicDeduction: 60000,
  retirementAge: 62,
  startAge: 30,
  avgWage2024: 12434,
  avgWageGrowthRate: 0.0,
}

function getAvgWage(year: number): number {
  if (year <= 2024) return PARAMS.avgWage2024
  return PARAMS.avgWage2024 * Math.pow(1 + PARAMS.avgWageGrowthRate, year - 2024)
}

interface YearlyResult {
  year: number
  age: number
  siBaseMonth: number
  hfBaseMonth: number
  empPension: number
  empMedical: number
  empUnemp: number
  empTotalSi: number
  erTotalSi: number
  emphf: number
  erhf: number
  taxableIncome: number
  taxAmount: number
  netIncome: number
  pensionAccountBalance: number
  housingFundBalanceYear: number
}

function calculateYearly(year: number, age: number, grossIncome: number, avgWage: number, hfRate: number): YearlyResult {
  const monthlyIncome = grossIncome / 12
  const siBaseMonth = clamp(monthlyIncome, 0.6 * avgWage, 3.0 * avgWage)
  const hfBaseMonth = clamp(monthlyIncome, PARAMS.hfBaseLower, PARAMS.hfBaseUpper)

  const empPension = siBaseMonth * PARAMS.empPensionRate * 12
  const empMedical = siBaseMonth * PARAMS.empMedicalRate * 12
  const empUnemp = siBaseMonth * PARAMS.empUnempRate * 12
  const empSi = empPension + empMedical + empUnemp

  const erPension = siBaseMonth * PARAMS.erPensionRate * 12
  const erMedical = siBaseMonth * PARAMS.erMedicalRate * 12
  const erUnemp = siBaseMonth * PARAMS.erUnempRate * 12
  const erInjury = siBaseMonth * PARAMS.erInjuryRate * 12
  const erTotalSi = erPension + erMedical + erUnemp + erInjury

  const empHf = hfBaseMonth * hfRate * 12
  const erHf = hfBaseMonth * hfRate * 12

  const taxableIncome = Math.max(0, grossIncome - PARAMS.basicDeduction - empSi - empHf)
  const taxAmount = calcTaxQuickDeduction(taxableIncome)
  const netIncome = grossIncome - empSi - empHf - taxAmount

  return {
    year,
    age,
    siBaseMonth,
    hfBaseMonth,
    empPension,
    empMedical,
    empUnemp,
    empTotalSi: empSi,
    erTotalSi,
    emphf: empHf,
    erhf: erHf,
    taxableIncome,
    taxAmount,
    netIncome,
    pensionAccountBalance: empPension,
    housingFundBalanceYear: empHf + erHf,
  }
}

function calculateLifetime(initialGrossIncome: number, salaryGrowthRate = 0.0, hfRate = PARAMS.hfRateDefault) {
  const workYears = PARAMS.retirementAge - PARAMS.startAge
  let currentGrossIncome = initialGrossIncome

  let totalEmployeeContributions = 0
  let totalEmployerContributions = 0
  let pensionAccountBalance = 0
  let housingFundBalance = 0

  const yearlyResults: YearlyResult[] = []

  for (let yearOffset = 0; yearOffset < workYears; yearOffset++) {
    const year = 2024 + yearOffset
    const age = PARAMS.startAge + yearOffset
    const avgWage = getAvgWage(year)

    const yearly = calculateYearly(year, age, currentGrossIncome, avgWage, hfRate)
    yearlyResults.push(yearly)

    totalEmployeeContributions += yearly.empTotalSi + yearly.emphf
    totalEmployerContributions += yearly.erTotalSi + yearly.erhf
    pensionAccountBalance += yearly.pensionAccountBalance
    housingFundBalance += yearly.housingFundBalanceYear

    currentGrossIncome *= 1 + salaryGrowthRate
  }

  const avgWageAtRetirement = getAvgWage(2024 + workYears)
  const basicPension = avgWageAtRetirement * workYears * 0.01
  const personalAccountPension = pensionAccountBalance / 139
  const monthlyPension = basicPension + personalAccountPension
  const annualPension = monthlyPension * 12

  const retirementYears = 90 - PARAMS.retirementAge
  const totalBenefits = annualPension * retirementYears + housingFundBalance

  const roi = totalEmployeeContributions > 0 ? (totalBenefits - totalEmployeeContributions) / totalEmployeeContributions : 0

  const cashFlows: number[] = []
  for (const r of yearlyResults) cashFlows.push(-(r.empTotalSi + r.emphf))
  for (let year = 0; year < retirementYears; year++) {
    cashFlows.push(year === 0 ? annualPension + housingFundBalance : annualPension)
  }
  const irr = bisectionIrr(cashFlows) ?? 0

  let breakEvenAge: number | null = null
  if (monthlyPension > 0) {
    const monthsToBreakEven = totalEmployeeContributions / monthlyPension
    const candidate = PARAMS.retirementAge + monthsToBreakEven / 12
    breakEvenAge = candidate > 90 ? null : candidate
  }

  return {
    workYears,
    totalEmployeeContributions,
    totalEmployerContributions,
    totalContributions: totalEmployeeContributions + totalEmployerContributions,
    finalHousingFundBalance: housingFundBalance,
    monthlyPension,
    totalBenefits,
    roi,
    irr,
    breakEvenAge,
    yearlyResults,
  }
}

function calculatePension(monthlySalary: number): PensionResult {
  const annualIncome = monthlySalary * 12
  const result = calculateLifetime(annualIncome, 0.0, PARAMS.hfRateDefault)

  return {
    monthlyPension: result.monthlyPension,
    totalContribution: result.totalContributions,
    totalBenefit: result.totalBenefits,
    retirementAccountBalance: result.finalHousingFundBalance,
    breakEvenAge: result.breakEvenAge,
    roi: result.roi,
    irr: result.irr,
    currency: 'CNY',
    retirementAge: PARAMS.retirementAge,
    workYears: result.workYears,
    details: {
      housingFundBalance: result.finalHousingFundBalance,
      totalEmployeeContributions: result.totalEmployeeContributions,
      totalEmployerContributions: result.totalEmployerContributions,
    },
  }
}

function calculateTax(annualIncome: number): TaxResult {
  const totalDeductions = PARAMS.basicDeduction
  const taxableIncome = annualIncome - totalDeductions
  if (taxableIncome <= 0) {
    return { totalTax: 0, taxableIncome: 0, effectiveRate: 0, netIncome: annualIncome }
  }
  const totalTax = calcTaxQuickDeduction(taxableIncome)
  return {
    totalTax,
    taxableIncome,
    effectiveRate: annualIncome > 0 ? (totalTax / annualIncome) * 100 : 0,
    netIncome: annualIncome - totalTax,
  }
}

// --- china_social_security_calculator.py port, used for the single-year / lifetime detail breakdown ---

const SS_PARAMS = {
  avgSalary2023: 12307,
  avgSalary2024: 12434,
  avgSalaryGrowthRate: 0.0,
  employerPensionRate: 0.16,
  employerMedicalRate: 0.09,
  employerUnemploymentRate: 0.005,
  employerInjuryRate: 0.0016,
  employeePensionRate: 0.08,
  employeeMedicalRate: 0.02,
  employeeUnemploymentRate: 0.005,
  housingFundBaseUpper: 36921,
  housingFundBaseLower: 2690,
  housingFundRateEmployer: 0.07,
  housingFundRateEmployee: 0.07,
  personalTaxBasicDeduction: 60000,
  socialSecurityBaseUpper: 36921,
}

function getAvgSalary(year: number): number {
  if (year <= 2023) return SS_PARAMS.avgSalary2023
  if (year === 2024) return SS_PARAMS.avgSalary2024
  return SS_PARAMS.avgSalary2024 * Math.pow(1 + SS_PARAMS.avgSalaryGrowthRate, year - 2024)
}

export interface SsContribution {
  contributionBase: number
  employerPension: number
  employerMedical: number
  employerUnemployment: number
  employerInjury: number
  employerTotal: number
  employeePension: number
  employeeMedical: number
  employeeUnemployment: number
  employeeTotal: number
  totalContribution: number
}

function calculateSsContribution(monthlySalary: number, year = 2024): SsContribution {
  const avgSalary = getAvgSalary(year)
  const baseUpper = avgSalary * 3.0
  const baseLower = avgSalary * 0.6
  const contributionBase = clamp(monthlySalary, baseLower, baseUpper)

  const employerPension = contributionBase * SS_PARAMS.employerPensionRate
  const employerMedical = contributionBase * SS_PARAMS.employerMedicalRate
  const employerUnemployment = contributionBase * SS_PARAMS.employerUnemploymentRate
  const employerInjury = contributionBase * SS_PARAMS.employerInjuryRate
  const employerTotal = employerPension + employerMedical + employerUnemployment + employerInjury

  const employeePension = contributionBase * SS_PARAMS.employeePensionRate
  const employeeMedical = contributionBase * SS_PARAMS.employeeMedicalRate
  const employeeUnemployment = contributionBase * SS_PARAMS.employeeUnemploymentRate
  const employeeTotal = employeePension + employeeMedical + employeeUnemployment

  return {
    contributionBase,
    employerPension,
    employerMedical,
    employerUnemployment,
    employerInjury,
    employerTotal,
    employeePension,
    employeeMedical,
    employeeUnemployment,
    employeeTotal,
    totalContribution: employerTotal + employeeTotal,
  }
}

export interface HfContribution {
  contributionBase: number
  employerContribution: number
  employeeContribution: number
  totalContribution: number
}

function calculateHfContribution(monthlySalary: number): HfContribution {
  const contributionBase = clamp(monthlySalary, SS_PARAMS.housingFundBaseLower, SS_PARAMS.housingFundBaseUpper)
  const employerContribution = contributionBase * SS_PARAMS.housingFundRateEmployer
  const employeeContribution = contributionBase * SS_PARAMS.housingFundRateEmployee
  return { contributionBase, employerContribution, employeeContribution, totalContribution: employerContribution + employeeContribution }
}

export interface PersonalTaxResult {
  taxableIncome: number
  taxAmount: number
  netIncome: number
  effectiveRate: number
}

function calculatePersonalTax(annualIncome: number, socialSecurityDeduction: number, housingFundDeduction: number): PersonalTaxResult {
  const taxableIncome = annualIncome - socialSecurityDeduction - housingFundDeduction - SS_PARAMS.personalTaxBasicDeduction
  const taxAmount = taxableIncome > 0 ? calcTaxQuickDeduction(taxableIncome) : 0
  const netIncome = annualIncome - socialSecurityDeduction - housingFundDeduction - taxAmount
  const effectiveRate = annualIncome > 0 ? taxAmount / annualIncome : 0
  return { taxableIncome, taxAmount, netIncome, effectiveRate }
}

function calculateSocialSecurity(monthlySalary: number, years: number): SocialSecurityResult {
  const ss = calculateSsContribution(monthlySalary)
  const hf = calculateHfContribution(monthlySalary)
  return {
    monthlyEmployee: ss.employeeTotal,
    monthlyEmployer: ss.employerTotal,
    totalEmployee: ss.employeeTotal * 12 * years,
    totalEmployer: ss.employerTotal * 12 * years,
    totalLifetime: (ss.employeeTotal + ss.employerTotal) * 12 * years,
    details: {
      housingFundEmployee: hf.employeeContribution,
      housingFundEmployer: hf.employerContribution,
      contributionBase: ss.contributionBase,
      housingFundBase: hf.contributionBase,
    },
  }
}

/** Detailed year-by-year breakdown, mirroring ChinaDetailedAnalyzer._generate_analysis_json. */
export interface ChinaDetailAnalysis {
  startAge: number
  retirementAge: number
  workYears: number
  firstYear: {
    annualIncome: number
    ssContribution: SsContribution
    hfContribution: HfContribution
    tax: PersonalTaxResult
  }
  lifetime: {
    totalSalary: number
    totalSsEmployee: number
    totalSsEmployer: number
    totalHfEmployee: number
    totalHfEmployer: number
    totalTax: number
  }
  retirement: {
    retirementYears: number
    totalRetirementPayout: number
  }
}

export function getChinaDetailAnalysis(monthlySalary: number, salaryGrowthRate: number, pensionResult: PensionResult): ChinaDetailAnalysis {
  const startAge = 30
  const retirementAge = 62
  const workYears = retirementAge - startAge

  const ssContribution = calculateSsContribution(monthlySalary)
  const hfContribution = calculateHfContribution(monthlySalary)
  const annualIncome = monthlySalary * 12
  const tax = calculatePersonalTax(annualIncome, ssContribution.employeeTotal * 12, hfContribution.employeeContribution * 12)

  let totalSalary = 0
  let totalSsEmployee = 0
  let totalSsEmployer = 0
  let totalHfEmployee = 0
  let totalHfEmployer = 0
  let totalTax = 0
  let currentSalary = monthlySalary

  for (let yearOffset = 0; yearOffset < workYears; yearOffset++) {
    const year = 2024 + yearOffset
    const annualSalary = currentSalary * 12
    totalSalary += annualSalary

    const ss = calculateSsContribution(currentSalary, year)
    totalSsEmployee += ss.employeeTotal * 12
    totalSsEmployer += ss.employerTotal * 12

    const hf = calculateHfContribution(currentSalary)
    totalHfEmployee += hf.employeeContribution * 12
    totalHfEmployer += hf.employerContribution * 12

    const t = calculatePersonalTax(annualSalary, ss.employeeTotal * 12, hf.employeeContribution * 12)
    totalTax += t.taxAmount

    currentSalary *= 1 + salaryGrowthRate
  }

  const retirementYears = 90 - retirementAge
  const totalRetirementPayout = pensionResult.monthlyPension * 12 * retirementYears

  return {
    startAge,
    retirementAge,
    workYears,
    firstYear: { annualIncome, ssContribution, hfContribution, tax },
    lifetime: { totalSalary, totalSsEmployee, totalSsEmployer, totalHfEmployee, totalHfEmployer, totalTax },
    retirement: { retirementYears, totalRetirementPayout },
  }
}

export const chinaModule: CountryModule = {
  code: 'CN',
  name: '中国',
  nameEn: 'China',
  currency: 'CNY',
  flag: '🇨🇳',
  calculatePension,
  calculateTax,
  calculateSocialSecurity,
  // Note: the Python plugin's get_retirement_age() reads ChinaConfig.retirement_ages (male: 60),
  // which is inconsistent with the 62 hardcoded inside calculate_pension() itself — a quirk of the
  // original source we replicate faithfully (the CLI's multi-country comparison table shows 60).
  getRetirementAge: () => 60,
}
