import { useMemo, useState } from 'react'
import { COUNTRY_MODULES, COUNTRY_ORDER } from './calc'
import { CURRENCY_NAMES, convertAmount } from './calc/currency'
import SingleCountryDetail from './components/SingleCountryDetail'
import CompareTable from './components/CompareTable'

const INPUT_CURRENCIES = ['CNY', 'USD', 'SGD', 'TWD', 'JPY', 'EUR', 'GBP', 'HKD']

function App() {
  const [amountInput, setAmountInput] = useState('300000')
  const [currency, setCurrency] = useState('CNY')
  const [selected, setSelected] = useState<string[]>(['CN'])

  const amount = useMemo(() => {
    const parsed = Number(amountInput)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 0
  }, [amountInput])

  function toggleCountry(code: string) {
    setSelected((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]))
  }

  // Monthly salary in each selected country's local currency, converted from the input amount (treated as an annual figure).
  const monthlySalaries = useMemo(() => {
    const result: Record<string, number> = {}
    for (const code of selected) {
      const mod = COUNTRY_MODULES[code]
      const localAnnual = convertAmount(amount, currency, mod.currency)
      result[code] = localAnnual / 12
    }
    return result
  }, [amount, currency, selected])

  return (
    <>
      <h1>💰 退休金对比系统</h1>
      <p className="subtitle">输入年收入，选择一个或多个国家/地区，纯前端计算养老金、社保与个税 — 数据不会发送到任何服务器。</p>

      <div className="disclaimer">
        ⚠️ 本工具仅用于教育与研究目的，参数（通胀率 2%、投资回报率 5%、社保基金回报率 3%、30 岁起缴费）均为固定假设，实际请以各国官方政策为准。
      </div>

      <div className="card">
        <div className="form-row">
          <div className="field">
            <label htmlFor="amount">年收入</label>
            <input id="amount" type="number" min="0" value={amountInput} onChange={(e) => setAmountInput(e.target.value)} placeholder="例如 300000" />
          </div>
          <div className="field">
            <label htmlFor="currency">货币</label>
            <select id="currency" value={currency} onChange={(e) => setCurrency(e.target.value)}>
              {INPUT_CURRENCIES.map((c) => (
                <option key={c} value={c}>
                  {c} {CURRENCY_NAMES[c] ? `(${CURRENCY_NAMES[c]})` : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="field" style={{ marginTop: 16 }}>
          <label>选择国家/地区（可多选）</label>
          <div className="country-picker">
            {COUNTRY_ORDER.map((code) => {
              const mod = COUNTRY_MODULES[code]
              const isSelected = selected.includes(code)
              return (
                <div key={code} className={`country-chip${isSelected ? ' selected' : ''}`} onClick={() => toggleCountry(code)}>
                  <span>{mod.flag}</span>
                  <span>{mod.name}</span>
                </div>
              )
            })}
          </div>
        </div>
        <p className="hint">默认假设该收入为年收入，按各国本地货币汇率换算后再按月计算。</p>
      </div>

      {amount <= 0 && <div className="card">请输入大于 0 的年收入。</div>}

      {amount > 0 && selected.length === 0 && <div className="card">请至少选择一个国家/地区。</div>}

      {amount > 0 && selected.length === 1 && <SingleCountryDetail countryCode={selected[0]} monthlySalary={monthlySalaries[selected[0]]} />}

      {amount > 0 && selected.length > 1 && <CompareTable countryCodes={selected} monthlySalaries={monthlySalaries} />}

      <footer>
        计算逻辑移植自{' '}
        <a href="https://github.com/mediapig/Comparison-of-pensions" target="_blank" rel="noreferrer">
          Comparison-of-pensions
        </a>{' '}
        项目的 Python 插件，全部在浏览器本地运行。
      </footer>
    </>
  )
}

export default App
