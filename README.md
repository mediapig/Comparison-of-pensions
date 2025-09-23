# 退休金对比系统

一个基于Python的插件化退休金计算和对比系统，支持多个国家的退休金计算，考虑通胀、工资增长、投资回报等复杂因素。**新增综合分析功能，包含养老金、社保、个税和实际到手金额的完整分析。**

## 🆕 最新更新 - 外部库集成

**v3.0 重大更新**: 集成多个开源税务和养老金计算库，提供更专业和准确的计算结果！

### 🔬 集成的专业库
- **🇺🇸 美国**: `taxcalc` (PSL官方) + `Open Social Security`
- **🇬🇧 英国**: `CoolTaxTool` + `UK Tax Calculator` + `taxman`
- **🌐 通用**: `numpy-financial` + `OpenFisca` + `scipy`
- **📊 智能回退**: 外部库不可用时自动使用内置实现

### 🚀 立即体验
```bash
# 一键安装所有外部库
python scripts/install_external_libs.py

# 测试集成状态
python scripts/test_external_integrations.py
```

📖 **详细集成指南**: [EXTERNAL_LIBRARIES_GUIDE.md](EXTERNAL_LIBRARIES_GUIDE.md)

## 🚀 功能特点

- **插件化架构**：支持不同国家的退休金计算器
- **🆕 外部库集成**：集成专业开源库，计算更精确
- **综合分析**：养老金、社保、个税、实际到手金额的完整分析
- **复杂因素考虑**：通胀、工资增长、投资回报率等
- **多维度对比**：月退休金、总缴费、ROI、回本年龄等
- **敏感性分析**：分析不同参数对结果的影响
- **详细报告**：生成完整的退休金分析报告
- **个税计算**：各国个人所得税计算，包含社保扣除
- **实际到手**：扣除社保和个税后的实际到手金额
- **🔧 智能回退**：外部库不可用时自动使用内置实现

## 🏗️ 系统架构

```
pension_comparison/
├── core/                    # 核心模块
│   ├── models.py           # 数据模型
│   ├── base_calculator.py  # 抽象基类
│   └── pension_engine.py   # 计算引擎
├── plugins/                 # 国家插件
│   ├── china/              # 中国退休金计算器 + 综合分析器
│   ├── usa/                # 美国退休金计算器 + 综合分析器
│   ├── singapore/          # 新加坡退休金计算器 + 综合分析器
│   ├── canada/             # 加拿大退休金计算器 + 综合分析器
│   ├── australia/          # 澳大利亚退休金计算器 + 综合分析器
│   ├── hongkong/           # 香港退休金计算器 + 综合分析器
│   ├── taiwan/             # 台湾退休金计算器 + 综合分析器
│   ├── japan/              # 日本退休金计算器 + 综合分析器
│   ├── uk/                 # 英国退休金计算器 + 综合分析器
│   └── norway/             # 挪威退休金计算器 + 综合分析器
├── utils/                   # 工具模块
│   ├── inflation.py        # 通胀计算
│   ├── salary_growth.py    # 工资增长模型
│   ├── investment.py       # 投资回报计算
│   ├── tax_manager.py      # 税收管理
│   ├── currency_converter.py # 货币转换
│   └── external_library_adapters.py # 🆕 外部库适配器
├── scripts/                 # 🆕 脚本工具
│   ├── install_external_libs.py # 外部库安装脚本
│   └── test_external_integrations.py # 集成测试脚本
└── main.py                  # 主程序入口
```

## 📦 安装依赖

### 基础安装
```bash
pip install -r requirements.txt
```

### 🆕 增强安装 (推荐)
```bash
# 安装所有外部专业库
python scripts/install_external_libs.py

# 或者分步安装
pip install numpy-financial taxcalc  # 核心金融库
pip install git+https://github.com/wozniakpawel/cooltaxtool.git  # 英国税收
```

## 🚀 快速开始

### 1. 命令行使用（推荐）

```bash
# 分析单个国家
python3 main.py --cn    # 中国
python3 main.py --sg    # 新加坡
python3 main.py --us    # 美国
python3 main.py --ca    # 加拿大
python3 main.py --au    # 澳大利亚
python3 main.py --hk    # 香港
python3 main.py --tw    # 台湾
python3 main.py --jp    # 日本
python3 main.py --uk    # 英国
python3 main.py --no    # 挪威

# 多国对比
python3 main.py cn,us,au    # 对比中国、美国、澳大利亚
python3 main.py sg,hk,tw    # 对比新加坡、香港、台湾
python3 main.py no,se,dk    # 对比挪威、瑞典、丹麦
```

### 2. 程序化使用

```python
from core.pension_engine import PensionEngine
from plugins.china.china_comprehensive_analyzer import ChinaComprehensiveAnalyzer
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from datetime import date

# 创建计算引擎
engine = PensionEngine()

# 使用综合分析器
analyzer = ChinaComprehensiveAnalyzer(engine)
analyzer.analyze_comprehensive(30000)  # 月薪3万人民币
```

## 🌍 支持的国家和地区

### 📊 完整对比表格

| 国家/地区 | 代码 | 养老金系统 | 社保系统 | 个税特点 | 退休年龄 | 综合分析 |
|-----------|------|------------|----------|----------|----------|----------|
| **中国** | CN | 基础养老金+个人账户 | 社保（养老+医疗+失业） | 专项附加扣除 | 男60/女55 | ✅ 完整 |
| **新加坡** | SG | CPF中央公积金 | CPF（OA+SA+MA） | 累进税率，CPF扣除 | 62 | ✅ 完整 |
| **加拿大** | CA | CPP+OAS | CPP+EI | 基本免税额，CPP/EI扣除 | 65 | ✅ 完整 |
| **澳大利亚** | AU | Superannuation | Superannuation | 基本免税额，Super雇主承担 | 67 | ✅ 完整 |
| **美国** | US | Social Security | SS+Medicare | 标准扣除额，SS/Medicare扣除 | 67 | ✅ 完整 |
| **香港** | HK | MPF强积金 | MPF | 基本免税额，MPF扣除 | 65 | ✅ 完整 |
| **台湾** | TW | 劳保+国民年金 | 劳保+健保 | 基本免税额，劳保/健保扣除 | 65 | ✅ 完整 |
| **日本** | JP | 厚生年金+国民年金 | 厚生年金+健康保险 | 基本控除，厚生年金/健保扣除 | 65 | ✅ 完整 |
| **英国** | UK | 国家养老金+职场养老金 | National Insurance+养老金 | 个人免税额，养老金扣除 | 68 | ✅ 完整 |
| **挪威** | NO | Folketrygden国民保险 | Folketrygden | 平税制+基本免税额 | 67 | ✅ 完整 |

### 💰 详细财务对比分析

**📋 完整对比结果请查看 [COMPARISON_RESULTS.md](COMPARISON_RESULTS.md)**

该文件包含：
- 示例场景的详细对比（仅供参考）
- 社保缴费率对比
- 个税税率对比
- 全生命周期财务总结
- 关键发现和投资回报率分析

## 🔍 综合分析功能

### 📋 分析内容

每个国家的综合分析器都包含以下三个部分：

#### 1. 🏦 养老金分析
- 月退休金金额
- 总缴费金额
- 投资回报率 (ROI)
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
- 蒙特卡洛模拟
- 序列回报风险

### 4. 税收计算
- **新增** 各国个税税率表
- **新增** 社保缴费计算
- **新增** 税前扣除项
- **新增** 有效税率计算

## 🔧 扩展新国家

要添加新的国家支持，需要：

1. 在 `plugins/` 目录下创建新的国家目录
2. 创建 `*_comprehensive_analyzer.py` 文件
3. 实现 `*_TaxCalculator` 类，包含：
   - 个税税率表
   - 社保缴费率
   - 个税计算方法
   - 社保缴费计算方法
4. 实现 `*_ComprehensiveAnalyzer` 类，包含：
   - `_analyze_pension()` 方法
   - `_analyze_income()` 方法
   - `_analyze_lifetime_summary()` 方法

示例：

```python
class FranceTaxCalculator:
    def __init__(self):
        self.tax_brackets = [...]  # 法国个税税率表
        self.social_rates = {...}  # 法国社保费率

    def calculate_income_tax(self, annual_income, deductions):
        # 实现法国个税计算逻辑
        pass

    def calculate_social_contribution(self, monthly_salary):
        # 实现法国社保缴费计算逻辑
        pass

class FranceComprehensiveAnalyzer:
    def __init__(self, engine):
        self.engine = engine
        self.tax_calculator = FranceTaxCalculator()

    def analyze_comprehensive(self, monthly_salary_cny):
        # 实现综合分析逻辑
        pass
```

## 🎯 运行示例

### 查看帮助信息
```bash
python3 main.py
```

### 分析中国情况
```bash
python3 main.py --cn
```

### 对比多个国家
```bash
python3 main.py cn,us,au
```

## ⚠️ 注意事项

1. **数据准确性**：本系统主要用于教育和研究目的，实际退休金计算请参考官方政策
2. **参数设置**：通胀率、投资回报率等参数需要根据实际情况调整
3. **货币单位**：不同国家使用不同货币，系统自动转换显示
4. **政策变化**：退休金和税收政策可能发生变化，需要及时更新计算逻辑
5. **汇率波动**：货币转换使用固定汇率，实际汇率会有波动

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个系统！

## 📄 许可证

MIT License

## 🔄 更新日志

### v2.0.0 (2024)
- **新增** 综合分析功能
- **新增** 各国个税计算
- **新增** 社保缴费计算
- **新增** 实际到手金额分析
- **新增** 全生命周期总结
- **新增** 英国、日本、台湾、香港综合分析器
- **优化** 输出格式统一化
- **修复** 各种计算错误和显示问题

### v1.0.0 (2023)
- 基础养老金计算功能
- 支持中国、美国、新加坡等国家
- 插件化架构设计
