// Port of plugins/singapore/cpf_calculator.py, plugins/singapore/singapore_tax_calculator_enhanced.py,
// plugins/singapore/plugin.py and utils/irr_calculator.py's CPF-specific cash-flow model.
import { bisectionIrr, type CountryModule, type PensionResult, type SocialSecurityResult, type TaxResult } from './types'

const START_AGE = 30
const RETIREMENT_AGE = 65

const CPF = {
  employeeRate: 0.20,
  employerRate: 0.17,
  owAnnualCeiling: 81600,
  cpfAnnualLimit: 37740,
  oaAllocationRate: 0.23,
  saAllocationRate: 0.06,
  maAllocationRate: 0.08,
  oaInterestRate: 0.025,
  saInterestRate: 0.04,
  maInterestRate: 0.04,
  raInterestRate: 0.04,
  extraInterestRate: 0.01,
  extraInterestThreshold: 60000,
  oaExtraInterestLimit: 20000,
  bhs2024: 71500,
  frs2024: 205800,
  annualGrowthRate: 0.03,
}

function getBhsLimit(year: number): number {
  return CPF.bhs2024 * Math.pow(1 + CPF.annualGrowthRate, year - 2024)
}

function getCohortBhsAt65(startYear: number, startAge: number): number {
  return getBhsLimit(startYear + (65 - startAge))
}

interface CpfModelResult {
  raAt65: number
  monthlyPayout: number
  totalPayout: number
  employeeContribTotal: number
  oaRemaining: number
  maRemaining: number
  terminalValue: number
}

/** Direct port of SingaporeCPFCalculator._cpf_model. */
function cpfModel(income: number, startAge: number, workYears: number): CpfModelResult {
  let employeeContribTotal = 0
  let OA = 0
  let SA = 0
  let MA = 0

  for (let yearOffset = 0; yearOffset < workYears; yearOffset++) {
    const age = startAge + yearOffset
    const year = 2024 + yearOffset

    const base = Math.min(income, CPF.owAnnualCeiling)
    let employeeContrib = base * CPF.employeeRate
    let employerContrib = base * CPF.employerRate
    let totalContrib = employeeContrib + employerContrib

    if (totalContrib > CPF.cpfAnnualLimit) {
      const scale = CPF.cpfAnnualLimit / totalContrib
      employeeContrib *= scale
      employerContrib *= scale
      totalContrib = CPF.cpfAnnualLimit
    }

    employeeContribTotal += employeeContrib

    let addOA = totalContrib * CPF.oaAllocationRate
    let addSA = totalContrib * CPF.saAllocationRate
    const addMA = totalContrib * CPF.maAllocationRate

    const bhsLimit = age < 65 ? getBhsLimit(year) : getCohortBhsAt65(2024, startAge)
    const maRoom = Math.max(0, bhsLimit - MA)
    const toMA = Math.min(addMA, maRoom)
    const overflow = addMA - toMA
    addSA += overflow

    OA += addOA
    SA += addSA
    MA += toMA

    OA *= 1 + CPF.oaInterestRate
    SA *= 1 + CPF.saInterestRate
    MA *= 1 + CPF.maInterestRate

    const totalBalance = OA + SA + MA
    if (totalBalance > 0) {
      const extraPool = Math.min(totalBalance, CPF.extraInterestThreshold) * CPF.extraInterestRate
      const oaEligible = Math.min(OA, CPF.oaExtraInterestLimit)
      const saEligible = SA
      const maEligible = MA
      const totalEligible = oaEligible + saEligible + maEligible
      if (totalEligible > 0) {
        OA += extraPool * (oaEligible / totalEligible)
        SA += extraPool * (saEligible / totalEligible)
        MA += extraPool * (maEligible / totalEligible)
      }
    }

    if (MA > bhsLimit + 1e-9) {
      const extra = MA - bhsLimit
      MA = bhsLimit
      SA += extra
    }
  }

  let RA = 0
  let OA_remaining = 0

  if (startAge + workYears >= 55) {
    const raTarget = CPF.frs2024 * Math.pow(1 + CPF.annualGrowthRate, 55 - startAge)

    const raAmount = Math.min(SA, raTarget)
    RA = raAmount
    SA -= raAmount

    const remainingTarget = raTarget - RA
    if (remainingTarget > 0) {
      const oaToRa = Math.min(OA, remainingTarget)
      RA += oaToRa
      OA -= oaToRa
    }
    OA_remaining = OA

    for (let i = 0; i < 10; i++) {
      RA *= 1 + CPF.raInterestRate
      OA_remaining *= 1 + CPF.oaInterestRate
      MA *= 1 + CPF.maInterestRate

      const bhsLimit2 = CPF.bhs2024 * Math.pow(1 + CPF.annualGrowthRate, 55 - startAge + i)
      if (MA > bhsLimit2 + 1e-9) {
        const extra = MA - bhsLimit2
        MA = bhsLimit2
        RA += extra
      }
    }
  } else {
    OA_remaining = OA
  }

  let payoutPerMonth = 0
  let totalPayout = 0
  if (RA > 0) {
    const annualRate = 0.035
    const years = 25
    const monthlyRate = annualRate / 12
    const months = years * 12
    payoutPerMonth = RA * (monthlyRate / (1 - Math.pow(1 + monthlyRate, -months)))
    totalPayout = payoutPerMonth * months
  }

  const terminalValue = OA_remaining + MA

  return { raAt65: RA, monthlyPayout: payoutPerMonth, totalPayout, employeeContribTotal, oaRemaining: OA_remaining, maRemaining: MA, terminalValue }
}

function calculateLifetimeCpf(monthlySalary: number, startAge = START_AGE, retirementAge = RETIREMENT_AGE) {
  const annualSalary = monthlySalary * 12
  const result = cpfModel(annualSalary, startAge, retirementAge - startAge)

  const totalLifetime = (result.employeeContribTotal * 0.37) / 0.20
  const totalEmployee = result.employeeContribTotal
  const totalEmployer = totalLifetime - totalEmployee

  return {
    totalLifetime,
    totalEmployee,
    totalEmployer,
    totalOA: totalLifetime * 0.62,
    totalSA: totalLifetime * 0.16,
    totalRA: result.raAt65,
    totalMA: result.maRemaining,
    finalBalances: {
      oaBalance: result.oaRemaining,
      saBalance: 0,
      raBalance: result.raAt65,
      maBalance: result.maRemaining,
    },
  }
}

// --- utils/irr_calculator.py's CPF-specific cash-flow model (a *different*, simpler model than cpfModel above) ---

const IRR_OW_CEILING = 102000

function calculateRaBalanceSimplified(annualSalary: number, startAge: number, retirementAge: number): number {
  let OA = 0
  let SA = 0
  let MA = 0
  for (let age = startAge; age < retirementAge; age++) {
    const base = Math.min(annualSalary, IRR_OW_CEILING)
    OA += base * 0.23
    SA += base * 0.06
    MA += base * 0.08
  }

  let RA: number
  if (retirementAge >= 55) {
    RA = SA + OA * 0.5
    let OA_remaining = OA * 0.5
    let MAv = MA
    for (let i = 0; i < 10; i++) {
      RA *= 1.04
      OA_remaining *= 1.025
      MAv *= 1.04
    }
    void OA_remaining
    void MAv
  } else {
    RA = SA + OA * 0.5
  }
  return RA
}

function calculateTerminalValueSimplified(annualSalary: number, startAge: number, retirementAge: number, terminalAge: number): number {
  let OA = 0
  let MA = 0
  for (let age = startAge; age < retirementAge; age++) {
    const base = Math.min(annualSalary, IRR_OW_CEILING)
    OA += base * 0.23
    MA += base * 0.08
  }

  let OA_remaining: number
  if (retirementAge >= 55) {
    OA_remaining = OA * 0.5
    for (let i = 0; i < 10; i++) {
      OA_remaining *= 1.025
      MA *= 1.04
    }
    for (let i = 0; i < terminalAge - retirementAge; i++) {
      OA_remaining *= 1.025
      MA *= 1.04
    }
  } else {
    OA_remaining = OA * 0.5
  }

  return OA_remaining + MA
}

function calculateCpfIrr(monthlySalary: number, startAge = START_AGE, retirementAge = RETIREMENT_AGE, terminalAge = 90) {
  const annualSalary = monthlySalary * 12
  const workYears = retirementAge - startAge
  const retirementYears = terminalAge - retirementAge

  const cashFlows: number[] = []
  for (let year = 0; year < workYears; year++) {
    const base = Math.min(annualSalary, IRR_OW_CEILING)
    cashFlows.push(-(base * 0.20))
  }

  const raBalance = calculateRaBalanceSimplified(annualSalary, startAge, retirementAge)
  const monthlyPayout = raBalance / 180
  const annualPayout = monthlyPayout * 12
  for (let year = 0; year < retirementYears; year++) cashFlows.push(annualPayout)

  const terminalValue = calculateTerminalValueSimplified(annualSalary, startAge, retirementAge, terminalAge)
  cashFlows.push(terminalValue)

  const irrValue = bisectionIrr(cashFlows)
  return { irrValue, irrPercentage: irrValue !== null ? irrValue * 100 : null }
}

// --- singapore_tax_calculator_enhanced.py: calculate_simple_tax path used by the plugin ---

const RESIDENT_BRACKETS: Array<[number, number]> = [
  [20000, 0.0],
  [30000, 0.02],
  [40000, 0.035],
  [80000, 0.07],
  [120000, 0.115],
  [160000, 0.15],
  [200000, 0.18],
  [240000, 0.19],
  [280000, 0.195],
  [320000, 0.20],
  [500000, 0.22],
  [1000000, 0.23],
  [Infinity, 0.24],
]

function computeProgressiveTax(chargeableIncome: number): number {
  let tax = 0
  let lower = 0
  for (const [upper, rate] of RESIDENT_BRACKETS) {
    const slab = Math.min(chargeableIncome, upper) - lower
    if (slab > 0) tax += slab * rate
    if (chargeableIncome <= upper) break
    lower = upper
  }
  return tax
}

function calculateTax(annualIncome: number): TaxResult {
  // No CPF top-up / donation deductions passed by the CLI, so chargeable income == gross employment cash.
  const grossEmploymentCash = annualIncome
  const chargeableIncome = grossEmploymentCash
  const taxPayable = computeProgressiveTax(chargeableIncome)
  return {
    totalTax: taxPayable,
    taxableIncome: chargeableIncome,
    effectiveRate: grossEmploymentCash > 0 ? (taxPayable / grossEmploymentCash) * 100 : 0,
    netIncome: grossEmploymentCash - taxPayable,
  }
}

function calculateSocialSecurity(monthlySalary: number, years: number, age = START_AGE): SocialSecurityResult {
  const lifetime = calculateLifetimeCpf(monthlySalary, age, age + years)
  const effectiveYears = years > 0 ? years : 35
  return {
    monthlyEmployee: lifetime.totalEmployee / (12 * effectiveYears),
    monthlyEmployer: lifetime.totalEmployer / (12 * effectiveYears),
    totalEmployee: lifetime.totalEmployee,
    totalEmployer: lifetime.totalEmployer,
    totalLifetime: lifetime.totalLifetime,
    details: {
      oaTotal: lifetime.totalOA,
      saTotal: lifetime.totalSA,
      raTotal: lifetime.totalRA,
      maTotal: lifetime.totalMA,
    },
  }
}

function calculatePension(monthlySalary: number): PensionResult {
  const workYears = RETIREMENT_AGE - START_AGE
  const lifetimeResult = calculateLifetimeCpf(monthlySalary)
  const totalContribution = lifetimeResult.totalLifetime

  const raBalance = lifetimeResult.finalBalances.raBalance
  const saBalance = lifetimeResult.finalBalances.saBalance
  const totalRaBalance = raBalance + saBalance

  const monthlyPension = totalRaBalance > 0 ? (totalRaBalance * 0.053) / 12 : 0
  const totalBenefit = totalRaBalance > 0 ? monthlyPension * 12 * 25 : 0

  const irrAnalysis = calculateCpfIrr(monthlySalary)
  const traditional = cpfModel(monthlySalary * 12, START_AGE, workYears)

  const employeeTotal = traditional.employeeContribTotal
  const monthlyPayout = traditional.monthlyPayout
  const terminalValue = traditional.terminalValue
  const totalBenefitCorrected = traditional.totalPayout + terminalValue

  const roi = irrAnalysis.irrPercentage !== null ? irrAnalysis.irrPercentage : employeeTotal > 0 ? (totalBenefitCorrected / employeeTotal - 1) * 100 : 0

  let breakEvenAge: number | null = null
  if (monthlyPayout > 0) {
    const breakEvenMonths = employeeTotal / monthlyPayout
    const candidate = RETIREMENT_AGE + breakEvenMonths / 12
    breakEvenAge = candidate < 90 ? Math.trunc(candidate) : null
  }

  return {
    monthlyPension,
    totalContribution,
    totalBenefit,
    retirementAccountBalance: raBalance,
    breakEvenAge,
    roi,
    irr: irrAnalysis.irrValue,
    currency: 'SGD',
    retirementAge: RETIREMENT_AGE,
    workYears,
    details: {
      cpfAccounts: { oaBalance: lifetimeResult.finalBalances.oaBalance, saBalance, raBalance, maBalance: lifetimeResult.finalBalances.maBalance },
      cpfPayoutMonthly: monthlyPension,
    },
  }
}

export const singaporeModule: CountryModule = {
  code: 'SG',
  name: '新加坡',
  nameEn: 'Singapore',
  currency: 'SGD',
  flag: '🇸🇬',
  calculatePension,
  calculateTax,
  calculateSocialSecurity,
  getRetirementAge: () => RETIREMENT_AGE,
}
