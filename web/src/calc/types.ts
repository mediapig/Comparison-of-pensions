// Shared types for all country pension calculators.
// These mirror the shapes produced by the Python plugins in `plugins/{country}/plugin.py`.

export interface PensionResult {
  monthlyPension: number
  totalContribution: number
  totalBenefit: number
  retirementAccountBalance: number
  breakEvenAge: number | null
  /** Raw ROI value exactly as computed by the Python source (displayed with a trailing "%" by the CLI,
   *  even though for China it is not actually multiplied by 100 — a known quirk of the original code). */
  roi: number
  /** IRR as a fraction (e.g. 0.06 = 6%), when the country plugin computes one. */
  irr?: number | null
  currency: string
  retirementAge: number
  workYears: number
  details: Record<string, unknown>
}

export interface TaxResult {
  totalTax: number
  taxableIncome: number
  /** Percentage points, e.g. 12.3 means 12.3%. */
  effectiveRate: number
  netIncome: number
}

export interface SocialSecurityResult {
  monthlyEmployee: number
  monthlyEmployer: number
  totalEmployee: number
  totalEmployer: number
  totalLifetime: number
  details?: Record<string, unknown>
}

export interface CountryModule {
  code: string
  name: string
  nameEn: string
  currency: string
  flag: string
  calculatePension(monthlySalary: number): PensionResult
  calculateTax(annualIncome: number): TaxResult
  calculateSocialSecurity(monthlySalary: number, years: number): SocialSecurityResult
  getRetirementAge(): number
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(value, max))
}

/** Bisection-based IRR solver, mirroring the manual fallback used throughout the Python source
 *  (utils/irr_calculator.py and plugins/china/china_optimized_calculator.py both use the same approach). */
export function bisectionIrr(cashFlows: number[], precision = 1e-6, maxIterations = 100): number | null {
  if (cashFlows.length < 2) return null

  const npv = (rate: number) => cashFlows.reduce((acc, cf, i) => acc + cf / Math.pow(1 + rate, i), 0)

  const hasPositive = cashFlows.some((cf) => cf > 0)
  const hasNegative = cashFlows.some((cf) => cf < 0)
  if (!hasPositive || !hasNegative) return null

  let low = -0.99
  let high = 10.0

  for (let i = 0; i < maxIterations; i++) {
    const mid = (low + high) / 2
    const npvMid = npv(mid)

    if (Math.abs(npvMid) < precision) return mid

    if (npvMid > 0) {
      low = mid
    } else {
      high = mid
    }
  }

  return (low + high) / 2
}
