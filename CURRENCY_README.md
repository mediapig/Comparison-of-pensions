# 🌍 货币转换功能说明

## 概述

退休金对比系统现在支持**多货币计算和显示**，可以自动获取实时汇率，并在不同货币之间进行转换。

## 🎯 支持的货币

| 货币代码 | 货币名称 | 说明 |
|----------|----------|------|
| CNY | 人民币 | 系统默认基准货币 |
| USD | 美元 | 可选基准货币 |
| EUR | 欧元 | 欧盟主要货币 |
| GBP | 英镑 | 英国货币 |
| JPY | 日元 | 日本货币 |
| HKD | 港币 | 香港货币 |
| SGD | 新币 | 新加坡货币 |
| AUD | 澳币 | 澳大利亚货币 |
| CAD | 加币 | 加拿大货币 |
| TWD | 新台币 | 台湾货币 |

## 🔄 汇率获取方式

### 1. **免费API (推荐)**
- **ExchangeRate-API**: 无需注册，免费使用
- **更新频率**: 每小时自动更新
- **备用方案**: 如果API失败，使用内置默认汇率

### 2. **默认汇率**
系统内置了基于2024年的参考汇率，确保在API不可用时仍能正常工作。

## 💰 使用方法

### 基本货币转换

```python
from utils.currency_converter import converter

# 人民币转美元
cny_amount = 10000
usd_amount = converter.convert(cny_amount, "CNY", "USD")
print(f"¥{cny_amount} = ${usd_amount:.2f}")

# 美元转欧元
eur_amount = converter.convert(usd_amount, "USD", "EUR")
print(f"${usd_amount:.2f} = €{eur_amount:.2f}")
```

### 退休金计算中的货币转换

```python
from core.models import EconomicFactors

# 设置基准货币和显示货币
economic_factors = EconomicFactors(
    inflation_rate=0.03,
    investment_return_rate=0.07,
    social_security_return_rate=0.05,
    base_currency="CNY",      # 基准货币：人民币
    display_currency="USD"    # 显示货币：美元
)

# 计算结果会自动转换为美元显示
comparison_df = engine.compare_pensions(person, salary_profile, economic_factors)
```

### 货币格式化

```python
# 格式化货币显示
formatted_cny = converter.format_amount(1234.56, "CNY")  # ¥1,234.56
formatted_usd = converter.format_amount(1234.56, "USD")  # $1,234.56
formatted_eur = converter.format_amount(1234.56, "EUR")  # €1,234.56
```

## 🏗️ 系统架构

### 1. **汇率转换器 (CurrencyConverter)**
- 自动获取实时汇率
- 支持多种基准货币
- 内置汇率缓存和更新机制

### 2. **数据模型更新**
- `EconomicFactors`: 支持基准货币和显示货币设置
- `PensionResult`: 包含原始货币信息，支持货币转换

### 3. **计算引擎集成**
- 自动处理货币转换
- 支持多货币对比分析

## 📊 实际应用场景

### 1. **国际对比分析**
```python
# 以人民币为基准，美元显示
economic_factors = EconomicFactors(
    base_currency="CNY",
    display_currency="USD"
)

# 所有国家的退休金都会转换为美元进行对比
results = engine.compare_pensions(person, salary_profile, economic_factors)
```

### 2. **多货币报告**
```python
# 生成不同货币的报告
currencies = ["CNY", "USD", "EUR"]
for currency in currencies:
    economic_factors.display_currency = currency
    results = engine.compare_pensions(person, salary_profile, economic_factors)
    print(f"\n{currency} 货币报告:")
    print(results)
```

### 3. **汇率敏感性分析**
```python
# 分析汇率变化对退休金对比的影响
base_rates = converter.get_exchange_rates()
for currency in ["USD", "EUR", "GBP"]:
    # 模拟汇率变化
    new_rate = base_rates[currency] * 1.1  # 升值10%
    # 重新计算退休金对比
    # ...
```

## ⚙️ 配置选项

### 1. **基准货币设置**
```python
# 创建人民币基准的转换器
cny_converter = CurrencyConverter("CNY")

# 创建美元基准的转换器
usd_converter = CurrencyConverter("USD")
```

### 2. **更新频率设置**
```python
# 修改更新间隔（默认1小时）
converter.update_interval = timedelta(hours=2)
```

### 3. **强制更新汇率**
```python
# 强制更新汇率数据
rates = converter.get_exchange_rates(force_update=True)
```

## 🔧 故障排除

### 1. **API连接失败**
- 系统会自动使用默认汇率
- 检查网络连接
- 确认API服务状态

### 2. **汇率数据过期**
- 系统每小时自动更新
- 可手动强制更新
- 默认汇率确保基本功能

### 3. **货币不支持**
- 检查货币代码是否正确
- 确认货币在支持列表中
- 添加新货币支持

## 🚀 扩展功能

### 1. **添加新货币**
```python
# 在CurrencyConverter中添加新货币
self.supported_currencies['KRW'] = '韩元'
```

### 2. **自定义汇率源**
```python
# 实现自定义汇率获取逻辑
def _custom_exchange_rate_api(self):
    # 调用自定义API
    pass
```

### 3. **历史汇率支持**
```python
# 支持历史汇率查询
def get_historical_rate(self, date, from_currency, to_currency):
    # 实现历史汇率查询
    pass
```

## 📈 性能优化

- **汇率缓存**: 避免频繁API调用
- **批量转换**: 支持批量货币转换
- **异步更新**: 后台异步更新汇率数据

## 🔒 安全考虑

- **API限流**: 避免超过免费API限制
- **错误处理**: 优雅处理API失败情况
- **数据验证**: 验证汇率数据的有效性

---

通过货币转换功能，系统现在可以：
1. **自动获取实时汇率**
2. **支持多货币计算和显示**
3. **提供准确的国际对比分析**
4. **灵活配置基准和显示货币**

这大大增强了系统的国际化和实用性！🎉
