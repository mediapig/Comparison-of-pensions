import { COUNTRY_MODULES, getChinaDetailAnalysis } from '../calc'
import { formatCurrency } from '../calc/currency'

export default function SingleCountryDetail({ countryCode, monthlySalary }: { countryCode: string; monthlySalary: number }) {
  const mod = COUNTRY_MODULES[countryCode]
  const currency = mod.currency
  const annualIncome = monthlySalary * 12

  const pension = mod.calculatePension(monthlySalary)
  const tax = mod.calculateTax(annualIncome)
  const ss = mod.calculateSocialSecurity(monthlySalary, pension.workYears)

  const totalIncome = annualIncome * pension.workYears
  const totalTaxLifetime = tax.totalTax * pension.workYears
  const totalNetIncome = totalIncome - ss.totalEmployee - totalTaxLifetime

  const fmt = (v: number) => formatCurrency(v, currency)

  return (
    <div className="card">
      <h2>
        {mod.flag} {mod.name}（{mod.code}）详细分析
      </h2>

      <div className="section-title">🏦 养老金分析</div>
      <div className="stat-grid">
        <div className="stat">
          <div className="label">月退休金</div>
          <div className="value">{fmt(pension.monthlyPension)}</div>
        </div>
        <div className="stat">
          <div className="label">工作期总缴费</div>
          <div className="value">{fmt(pension.totalContribution)}</div>
        </div>
        <div className="stat">
          <div className="label">ROI</div>
          <div className="value">{pension.roi.toFixed(1)}%</div>
        </div>
        {pension.irr != null && (
          <div className="stat">
            <div className="label">IRR</div>
            <div className="value">{(pension.irr * 100).toFixed(2)}%</div>
          </div>
        )}
        <div className="stat">
          <div className="label">回本年龄</div>
          <div className="value">{pension.breakEvenAge != null ? `${pension.breakEvenAge.toFixed(1)}岁` : '无法回本'}</div>
        </div>
        <div className="stat">
          <div className="label">退休年龄 / 工作年限</div>
          <div className="value">
            {mod.getRetirementAge()}岁 / {pension.workYears}年
          </div>
        </div>
      </div>

      <div className="section-title">💰 收入分析（第一年）</div>
      <div className="kv-grid">
        <div className="kv-row">
          <span className="k">年收入</span>
          <span className="v">{fmt(annualIncome)}</span>
        </div>
        <div className="kv-row">
          <span className="k">社保/公积金 员工月缴费</span>
          <span className="v">{fmt(ss.monthlyEmployee)}</span>
        </div>
        <div className="kv-row">
          <span className="k">社保/公积金 雇主月缴费</span>
          <span className="v">{fmt(ss.monthlyEmployer)}</span>
        </div>
        <div className="kv-row">
          <span className="k">年度所得税</span>
          <span className="v">{fmt(tax.totalTax)}</span>
        </div>
        <div className="kv-row">
          <span className="k">有效税率</span>
          <span className="v">{tax.effectiveRate.toFixed(2)}%</span>
        </div>
        <div className="kv-row">
          <span className="k">年度税后净收入</span>
          <span className="v">{fmt(tax.netIncome)}</span>
        </div>
      </div>

      <div className="section-title">📊 全生命周期总结（工作期 {pension.workYears} 年，假设薪资不增长）</div>
      <div className="kv-grid">
        <div className="kv-row">
          <span className="k">工作期总收入</span>
          <span className="v">{fmt(totalIncome)}</span>
        </div>
        <div className="kv-row">
          <span className="k">社保/公积金 员工总缴费</span>
          <span className="v">{fmt(ss.totalEmployee)}</span>
        </div>
        <div className="kv-row">
          <span className="k">社保/公积金 雇主总缴费</span>
          <span className="v">{fmt(ss.totalEmployer)}</span>
        </div>
        <div className="kv-row">
          <span className="k">工作期总税费（估算）</span>
          <span className="v">{fmt(totalTaxLifetime)}</span>
        </div>
        <div className="kv-row">
          <span className="k">工作期总净收入（估算）</span>
          <span className="v">{fmt(totalNetIncome)}</span>
        </div>
      </div>

      {countryCode === 'CN' && <ChinaExtraDetail monthlySalary={monthlySalary} pension={pension} />}

      <p className="hint">
        本页仅使用各国插件核心计算公式（养老金 / 社保 / 个税），未复刻命令行版本各国专属的长篇详细分析器（如台湾的劳保+健保+个人账户三支柱模型、日本的国税/住民税细分等）；多国对比数值与命令行完全一致。
      </p>
    </div>
  )
}

function ChinaExtraDetail({ monthlySalary, pension }: { monthlySalary: number; pension: ReturnType<typeof COUNTRY_MODULES.CN.calculatePension> }) {
  const detail = getChinaDetailAnalysis(monthlySalary, 0.0, pension)
  const fmt = (v: number) => formatCurrency(v, 'CNY')

  return (
    <>
      <div className="section-title">🇨🇳 中国专项：社保 / 公积金第一年细分</div>
      <div className="kv-grid">
        <div className="kv-row">
          <span className="k">社保缴费基数</span>
          <span className="v">{fmt(detail.firstYear.ssContribution.contributionBase)}</span>
        </div>
        <div className="kv-row">
          <span className="k">养老保险（员工）</span>
          <span className="v">{fmt(detail.firstYear.ssContribution.employeePension * 12)}</span>
        </div>
        <div className="kv-row">
          <span className="k">医疗保险（员工）</span>
          <span className="v">{fmt(detail.firstYear.ssContribution.employeeMedical * 12)}</span>
        </div>
        <div className="kv-row">
          <span className="k">住房公积金（个人+单位）</span>
          <span className="v">{fmt(detail.firstYear.hfContribution.totalContribution * 12)}</span>
        </div>
        <div className="kv-row">
          <span className="k">工作期公积金总额（个人+单位）</span>
          <span className="v">{fmt(detail.lifetime.totalHfEmployee + detail.lifetime.totalHfEmployer)}</span>
        </div>
        <div className="kv-row">
          <span className="k">退休后总领取（{detail.retirement.retirementYears} 年）</span>
          <span className="v">{fmt(detail.retirement.totalRetirementPayout)}</span>
        </div>
      </div>
    </>
  )
}
