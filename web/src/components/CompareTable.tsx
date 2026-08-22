import { COUNTRY_MODULES, type PensionResult } from '../calc'
import { convertAmount, formatCurrency } from '../calc/currency'

interface Row {
  code: string
  pension: PensionResult
}

export default function CompareTable({ countryCodes, monthlySalaries }: { countryCodes: string[]; monthlySalaries: Record<string, number> }) {
  const rows: Row[] = countryCodes.map((code) => {
    const mod = COUNTRY_MODULES[code]
    return { code, pension: mod.calculatePension(monthlySalaries[code]) }
  })

  return (
    <div className="card">
      <h2>📊 退休金对比（统一换算为人民币）</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>国家</th>
              <th>月退休金</th>
              <th>总缴费</th>
              <th>ROI</th>
              <th>退休年龄</th>
            </tr>
          </thead>
          <tbody>
            {rows
              .slice()
              .sort((a, b) => convertAmount(b.pension.monthlyPension, b.pension.currency, 'CNY') - convertAmount(a.pension.monthlyPension, a.pension.currency, 'CNY'))
              .map(({ code, pension }) => {
                const mod = COUNTRY_MODULES[code]
                const monthlyCny = convertAmount(pension.monthlyPension, pension.currency, 'CNY')
                const contributionCny = convertAmount(pension.totalContribution, pension.currency, 'CNY')
                return (
                  <tr key={code}>
                    <td>
                      {mod.flag} {mod.name}
                    </td>
                    <td>{formatCurrency(monthlyCny, 'CNY')}</td>
                    <td>{formatCurrency(contributionCny, 'CNY')}</td>
                    <td>{pension.roi.toFixed(1)}%</td>
                    <td>{mod.getRetirementAge()}岁</td>
                  </tr>
                )
              })}
          </tbody>
        </table>
      </div>
      <p className="hint">汇率为静态快照（基准：CNY，2025-09-25），仅供对比参考，不代表实时汇率。</p>
    </div>
  )
}
