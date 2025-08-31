# 退休金对比系统

一个基于Python的插件化退休金计算和对比系统，支持多个国家的退休金计算，考虑通胀、工资增长、投资回报等复杂因素。

## 功能特点

- **插件化架构**：支持不同国家的退休金计算器
- **复杂因素考虑**：通胀、工资增长、投资回报率等
- **多维度对比**：月退休金、总缴费、ROI、回本年龄等
- **敏感性分析**：分析不同参数对结果的影响
- **详细报告**：生成完整的退休金分析报告

## 系统架构

```
pension_comparison/
├── core/                    # 核心模块
│   ├── models.py           # 数据模型
│   ├── base_calculator.py  # 抽象基类
│   └── pension_engine.py   # 计算引擎
├── plugins/                 # 国家插件
│   ├── china/              # 中国退休金计算器
│   └── usa/                # 美国退休金计算器
├── utils/                   # 工具模块
│   ├── inflation.py        # 通胀计算
│   ├── salary_growth.py    # 工资增长模型
│   └── investment.py       # 投资回报计算
└── examples/                # 使用示例
    └── comparison_example.py
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 基本使用

```python
from core.pension_engine import PensionEngine
from plugins.china.china_calculator import ChinaPensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from datetime import date

# 创建计算引擎
engine = PensionEngine()
engine.register_calculator(ChinaPensionCalculator())

# 创建个人信息
person = Person(
    name="张三",
    birth_date=date(1990, 1, 1),
    gender=Gender.MALE,
    employment_type=EmploymentType.EMPLOYEE,
    start_work_date=date(2015, 7, 1)
)

# 创建工资档案
salary_profile = SalaryProfile(
    base_salary=8000,
    annual_growth_rate=0.05
)

# 创建经济因素
economic_factors = EconomicFactors(
    inflation_rate=0.03,
    investment_return_rate=0.07,
    social_security_return_rate=0.05
)

# 计算退休金
result = engine.calculate_all_countries(person, salary_profile, economic_factors)
```

### 2. 多国家对比

```python
# 注册多个国家计算器
engine.register_calculator(ChinaPensionCalculator())
engine.register_calculator(USAPensionCalculator())

# 对比不同国家的退休金
comparison = engine.compare_pensions(person, salary_profile, economic_factors)
print(comparison)
```

### 3. 敏感性分析

```python
# 分析通胀率对退休金的影响
inflation_analysis = engine.sensitivity_analysis(
    person, salary_profile, economic_factors, 'inflation_rate',
    [0.01, 0.02, 0.03, 0.04, 0.05]
)
```

## 支持的国家

### 中国 (CN)
- 企业职工、公务员、自由职业者、农民
- 个人账户养老金 + 基础养老金
- 考虑社保缴费基数上下限

### 美国 (US)
- 社会保障金计算
- 基于AIME和PIA的计算方法
- 考虑提前退休的减少

## 核心概念

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

## 扩展新国家

要添加新的国家支持，需要：

1. 在 `plugins/` 目录下创建新的国家目录
2. 继承 `BasePensionCalculator` 类
3. 实现必要的方法：
   - `_get_retirement_ages()`
   - `_get_contribution_rates()`
   - `calculate_pension()`
   - `calculate_contribution_history()`

示例：

```python
from core.base_calculator import BasePensionCalculator

class JapanPensionCalculator(BasePensionCalculator):
    def __init__(self):
        super().__init__("JP", "日本")

    def _get_retirement_ages(self):
        return {"male": 65, "female": 65}

    def _get_contribution_rates(self):
        return {"employee": 0.0915}

    def calculate_pension(self, person, salary_profile, economic_factors):
        # 实现日本退休金计算逻辑
        pass
```

## 运行示例

```bash
cd examples
python comparison_example.py
```

## 注意事项

1. **数据准确性**：本系统主要用于教育和研究目的，实际退休金计算请参考官方政策
2. **参数设置**：通胀率、投资回报率等参数需要根据实际情况调整
3. **货币单位**：不同国家使用不同货币，注意单位转换
4. **政策变化**：退休金政策可能发生变化，需要及时更新计算逻辑

## 贡献

欢迎提交Issue和Pull Request来改进这个系统！

## 许可证

MIT License
