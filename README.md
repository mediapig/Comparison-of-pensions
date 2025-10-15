# 退休金对比系统

一个基于Python的插件化退休金计算和对比系统，支持多个国家的退休金计算，考虑通胀、工资增长、投资回报等复杂因素。**提供详细的综合分析功能，包含养老金、社保、个税和实际到手金额的完整分析。**

## 🚀 功能特点

- **插件化架构**：支持不同国家的退休金计算器
- **智能货币转换**：支持多种货币输入和实时汇率转换
- **综合分析**：养老金、社保、个税、实际到手金额的完整分析
- **复杂因素考虑**：通胀、工资增长、投资回报率等
- **多维度对比**：月退休金、总缴费、ROI、回本年龄等
- **详细报告**：生成完整的退休金分析报告
- **个税计算**：各国个人所得税计算，包含社保扣除
- **实际到手**：扣除社保和个税后的实际到手金额
- **实时汇率**：支持多种汇率API，自动缓存和更新
- **精确计算**：使用Decimal类型确保金融计算精度

## 🏗️ 系统架构

```
Comparison-of-pensions/
├── core/                           # 核心模块
│   ├── models.py                  # 数据模型
│   ├── base_plugin.py             # 基础插件类
│   ├── plugin_manager.py          # 插件管理器
│   ├── analysis_runner.py         # 分析运行器
│   └── exceptions.py              # 异常处理
├── plugins/                        # 国家插件
│   ├── china/                     # 中国退休金计算器
│   │   ├── plugin.py              # 主插件
│   │   ├── config.py              # 配置
│   │   ├── china_detailed_analyzer.py # 详细分析器
│   │   ├── china_optimized_calculator.py # 优化计算器
│   │   ├── china_social_security_calculator.py # 社保计算器
│   │   └── china_tax_calculator.py # 税务计算器
│   ├── usa/                       # 美国退休金计算器
│   │   ├── plugin.py              # 主插件
│   │   ├── config.py              # 配置（按年表管理）
│   │   ├── usa_detailed_analyzer.py # 详细分析器
│   │   ├── pension_calculator.py  # 养老金计算器
│   │   ├── tax_calculator.py      # 税务计算器
│   │   ├── usa_401k_calculator.py # 401k计算器
│   │   └── usa_401k_params.py     # 401k参数
│   ├── singapore/                 # 新加坡退休金计算器
│   │   ├── plugin.py              # 主插件
│   │   ├── constants.py           # 常量配置
│   │   ├── singapore_detailed_analyzer.py # 详细分析器
│   │   ├── cpf_calculator.py      # CPF计算器
│   │   └── singapore_tax_calculator_enhanced.py # 税务计算器
│   ├── taiwan/                    # 台湾退休金计算器
│   │   ├── plugin.py              # 主插件
│   │   ├── config.py              # 配置
│   │   ├── taiwan_detailed_analyzer.py # 详细分析器
│   │   ├── pension_calculator.py  # 养老金计算器
│   │   └── tax_calculator.py      # 税务计算器
│   └── japan/                     # 日本退休金计算器
│       ├── plugin.py              # 主插件
│       ├── config.py              # 配置
│       ├── japan_detailed_analyzer.py # 详细分析器
│       ├── japan_corrected_calculator.py # 修正计算器
│       └── tax_calculator.py      # 税务计算器
├── utils/                          # 工具模块
│   ├── smart_currency_converter.py # 智能货币转换器
│   ├── daily_exchange_rate_cache.py # 汇率缓存
│   ├── irr_calculator.py          # IRR计算器
│   ├── annual_analyzer.py         # 年度分析器
│   ├── inflation.py               # 通胀计算
│   ├── investment.py              # 投资回报计算
│   ├── tax_manager.py             # 税收管理
│   ├── common.py                  # 通用工具
│   └── json_analyzer.py           # JSON分析器
├── docs/                           # 文档
│   ├── coding_standards.md        # 编码标准
│   └── performance_optimization_guide.md # 性能优化指南
├── tests/                          # 测试
│   └── performance_test.py        # 性能测试
├── cache/                          # 缓存目录
│   └── exchange_rates.json        # 汇率缓存
├── main.py                         # 主程序入口
└── requirements.txt                # 依赖文件
```

## 📦 安装依赖

### 基础安装
```bash
pip install -r requirements.txt
```

## 🚀 快速开始

### 1. 命令行使用（推荐）

```bash
# 分析单个国家
python3 main.py cny30000 --CN        # 中国，3万人民币
python3 main.py usd50000 --US        # 美国，5万美元
python3 main.py sgd50000 --SG        # 新加坡，5万新币
python3 main.py twd2000000 --TW      # 台湾，200万新台币
python3 main.py jpy5000000 --JP      # 日本，500万日元

# 智能货币输入支持
python3 main.py cny10000 --CN        # 货币代码+金额
python3 main.py 10000CNY --CN        # 金额+货币代码
python3 main.py ¥10000 --CN          # 货币符号+金额
python3 main.py 10000 --CN           # 纯数字(默认为人民币)

# 对比多个国家
python3 main.py cny30000 --CN,US,SG  # 对比中国、美国、新加坡

# 系统管理命令
python3 main.py --list-plugins       # 列出所有插件
python3 main.py --test-plugins       # 测试插件功能
python3 main.py --supported-currencies # 显示支持的货币
```

### 2. 程序化使用

```python
from core.plugin_manager import plugin_manager
from core.models import Person, SalaryProfile, EconomicFactors
from utils.smart_currency_converter import SmartCurrencyConverter
from datetime import date

# 创建计算引擎
converter = SmartCurrencyConverter()
currency_amount = converter.parse_amount("cny30000")

# 获取中国插件
china_plugin = plugin_manager.get_plugin("CN")

# 创建测试数据
person = china_plugin.create_person(start_age=30)
salary_profile = SalaryProfile(
    monthly_salary=currency_amount.amount / 12,
    annual_growth_rate=0.0,
    contribution_start_age=30
)
economic_factors = EconomicFactors(
    inflation_rate=0.02,
    investment_return_rate=0.05,
    social_security_return_rate=0.03
)

# 计算退休金
pension_result = china_plugin.calculate_pension(person, salary_profile, economic_factors)
print(f"月退休金: {china_plugin.format_currency(pension_result.monthly_pension)}")
```

## 🌍 支持的国家和地区

### 📊 完整对比表格

| 国家/地区 | 代码 | 养老金系统 | 社保系统 | 个税特点 | 退休年龄 | 状态 |
|-----------|------|------------|----------|----------|----------|------|
| **中国** | CN | 基础养老金+个人账户 | 社保（养老+医疗+失业） | 专项附加扣除 | 男60/女55 | ✅ 完整 |
| **新加坡** | SG | CPF中央公积金 | CPF（OA+SA+MA+RA） | 累进税率，CPF扣除 | 65 | ✅ 完整 |
| **美国** | US | Social Security+401k | SS+Medicare | 标准扣除额，SS/Medicare扣除 | 67 | ✅ 完整 |
| **台湾** | TW | 劳保+劳退新制 | 劳保+健保 | 基本免税额，劳保/健保扣除 | 65 | ✅ 完整 |
| **日本** | JP | 厚生年金+国民年金 | 厚生年金+健康保险 | 基本控除，厚生年金/健保扣除 | 65 | ✅ 完整 |
| **英国** | UK | 国家养老金+职场养老金 | National Insurance+养老金 | 个人免税额，养老金扣除 | 68 | ✅ 完整 |

## 🔍 综合分析功能

### 📋 分析内容

每个国家的综合分析器都包含以下三个部分：

#### 1. 🏦 养老金分析
- 月退休金金额
- 总缴费金额
- 投资回报率 (ROI)
- 内部收益率 (IRR)
- 回本年龄
- 缴费率信息

#### 2. 💰 收入分析
- 社保缴费详情（员工+雇主）
- 个人所得税计算
- 实际到手金额
- 有效税率
- 扣除项明细

#### 3. 📊 全生命周期总结
- 工作期间总收入
- 社保缴费总额
- 个税总额
- 净收入总额
- 各项比例分析
- 月平均值

### 💡 使用场景

- **个人财务规划**：了解不同国家的实际到手收入
- **移民决策参考**：对比各国的税收负担和社保体系
- **企业国际化**：了解不同国家的用工成本
- **学术研究**：分析各国养老金和税收政策差异

## 💱 智能货币转换

### 支持的货币

系统支持18种主要货币，包括：

- **亚洲货币**：CNY(人民币)、SGD(新加坡元)、HKD(港币)、TWD(新台币)、JPY(日元)、KRW(韩元)
- **美洲货币**：USD(美元)、CAD(加拿大元)、AUD(澳大利亚元)、BRL(巴西雷亚尔)
- **欧洲货币**：EUR(欧元)、GBP(英镑)、NOK(挪威克朗)、SEK(瑞典克朗)、DKK(丹麦克朗)、CHF(瑞士法郎)
- **其他货币**：INR(印度卢比)、RUB(俄罗斯卢布)

### 实时汇率

- 支持多个汇率API（ExchangeRate-API、ExchangeRatesAPI等）
- 自动缓存汇率数据，避免频繁API调用
- 智能回退机制，API不可用时使用缓存数据
- 支持货币符号、代码、别名等多种输入方式
- 统一汇率转换，确保报表内汇率一致性

## 🧮 核心概念

### 1. 通胀计算
- 通胀调整后的金额
- 实际回报率计算
- 购买力损失分析

### 2. 工资增长模型
- 线性增长
- 复合增长
- 分阶段增长
- 职业生涯峰值模型

### 3. 投资回报计算
- 未来价值和现值
- 定期缴费计算
- 内部收益率(IRR)计算
- 回本年龄分析

### 4. 税收计算
- 各国个税税率表
- 社保缴费计算
- 税前扣除项
- 有效税率计算

## 🔧 扩展新国家

要添加新的国家支持，需要：

1. 在 `plugins/` 目录下创建新的国家目录
2. 创建 `plugin.py` 文件，继承 `BaseCountryPlugin`
3. 实现必要的计算方法：
   - `calculate_pension()` - 退休金计算
   - `calculate_tax()` - 个税计算
   - `calculate_social_security()` - 社保计算
   - `get_retirement_age()` - 退休年龄
4. 创建配置文件 `config.py`
5. 可选：创建详细分析器 `*_analyzer.py`

示例：

```python
class FrancePlugin(BaseCountryPlugin):
    COUNTRY_CODE = "FR"
    COUNTRY_NAME = "法国"
    CURRENCY = "EUR"

    def calculate_pension(self, person, salary_profile, economic_factors):
        # 实现法国退休金计算逻辑
        pass

    def calculate_tax(self, annual_income):
        # 实现法国个税计算逻辑
        pass
```

## 🎯 运行示例

### 查看帮助信息
```bash
python3 main.py
```

### 分析中国情况
```bash
python3 main.py cny30000 --CN
```

### 对比多个国家
```bash
python3 main.py cny30000 --CN,US,SG
```

### 分析高收入情况
```bash
python3 main.py usd500000 --US    # 美国50万美元
python3 main.py sgd500000 --SG    # 新加坡50万新币
```

## ⚠️ 注意事项

1. **数据准确性**：本系统主要用于教育和研究目的，实际退休金计算请参考官方政策
2. **参数设置**：通胀率、投资回报率等参数需要根据实际情况调整
3. **货币单位**：不同国家使用不同货币，系统自动转换显示
4. **政策变化**：退休金和税收政策可能发生变化，需要及时更新计算逻辑
5. **汇率波动**：货币转换使用实时汇率，但汇率会有波动
6. **API限制**：汇率API可能有调用限制，建议合理使用
7. **计算精度**：使用Decimal类型确保金融计算精度，避免浮点数误差

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个系统！

## 📄 许可证

MIT License

## 🔄 更新日志

### v4.0.0 (2024-12)
- **重构** 新加坡CPF计算器，实现完整的CPF LIFE计算
- **优化** 美国插件，修复社安金退休期总领取计算
- **新增** 按年表管理，支持2023-2025年各项限额
- **修复** Additional Medicare Tax计算
- **优化** 401(k)限额与年份对齐
- **改进** 应税所得计算精度
- **统一** 汇率转换一致性
- **清理** 删除冗余代码和文件

### v3.0.0 (2024)
- **新增** 智能货币转换功能
- **新增** 实时汇率API集成
- **新增** 年度详细分析功能
- **优化** 插件管理系统
- **优化** 输出格式和用户体验
- **修复** 各种计算错误和显示问题

### v2.0.0 (2024)
- **新增** 综合分析功能
- **新增** 各国个税计算
- **新增** 社保缴费计算
- **新增** 实际到手金额分析
- **新增** 全生命周期总结
- **新增** 英国、日本、台湾、香港综合分析器

### v1.0.0 (2023)
- 基础养老金计算功能
- 支持中国、美国、新加坡等国家
- 插件化架构设计