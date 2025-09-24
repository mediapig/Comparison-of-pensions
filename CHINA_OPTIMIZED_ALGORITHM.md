# 中国养老金计算器 - 优化算法实现

## 概述

根据用户提供的7步优化算法，重新实现了中国养老金计算器，确保严格按照正确的口径进行计算。

## 优化算法实现

### INPUTS
- `gross`: 年收入
- `avg_wage`: 当年社平工资  
- `hf_rate`: 公积金比例（默认 7%）

### STEP 1: 确定社保、公积金基数
```python
si_base_month = clamp(gross/12, 0.6*avg_wage, 3.0*avg_wage)
hf_base_month = clamp(gross/12, 公积金下限, 公积金上限)
```

### STEP 2: 五险缴费
```python
# 个人缴费
emp_pension = si_base_month * 0.08 * 12
emp_medical = si_base_month * 0.02 * 12
emp_unemp   = si_base_month * 0.005 * 12
emp_total_si = emp_pension + emp_medical + emp_unemp

# 单位缴费
er_pension = si_base_month * 0.16 * 12
er_medical = si_base_month * 0.09 * 12
er_unemp   = si_base_month * 0.005 * 12
er_injury  = si_base_month * 0.0016 * 12
er_total_si = er_pension + er_medical + er_unemp + er_injury
```

### STEP 3: 公积金缴费
```python
emp_hf = hf_base_month * hf_rate * 12
er_hf  = hf_base_month * hf_rate * 12
```

### STEP 4: 个税
```python
taxable = gross - 60000 - emp_total_si - emp_hf
tax = 按七级超额累进速算扣除法计算(taxable)
```

### STEP 5: 到手工资
```python
net = gross - emp_total_si - emp_hf - tax
```

### STEP 6: 累计账户
```python
# 养老金个人账户余额 += emp_pension
# 公积金余额 += (emp_hf + er_hf)
```

### STEP 7: 退休时
```python
# 每月养老金 ≈ 基础养老金 + 个人账户养老金
# 公积金余额一次性发放
```

## 验证结果

### 第一年计算验证（用户参数）
- **年收入**: ¥180,000
- **社平工资**: ¥12,434
- **公积金比例**: 7%

**计算结果**:
```
STEP 1 - 基数确定:
  社保基数: ¥15,000/月
  公积金基数: ¥15,000/月

STEP 2 - 五险缴费:
  个人缴费: ¥18,900/年 (养老14,400 + 医疗3,600 + 失业900)
  单位缴费: ¥46,188/年 (养老28,800 + 医疗16,200 + 失业900 + 工伤288)

STEP 3 - 公积金缴费:
  个人缴费: ¥12,600/年
  单位缴费: ¥12,600/年

STEP 4 - 个税:
  应税所得: ¥88,500
  税额: ¥6,330

STEP 5 - 到手工资:
  税后净收入: ¥142,170
```

### 与用户正确算式的一致性验证
```
用户计算 vs 系统计算:
  个人社保: ¥18,900 vs ¥18,900 ✅ 差异: ¥0
  个人公积金: ¥12,600 vs ¥12,600 ✅ 差异: ¥0
  应税所得: ¥88,500 vs ¥88,500 ✅ 差异: ¥0
  个税: ¥6,330 vs ¥6,330 ✅ 差异: ¥0
  税后到手: ¥142,170 vs ¥142,170 ✅ 差异: ¥0
```

**验证结果**: ✅ 完全一致

## 终身养老金计算

### 30年工作期间累计
- **工作年限**: 30年
- **总缴费**: ¥3,662,811
  - 个人缴费: ¥1,277,894
  - 单位缴费: ¥2,384,916
- **月养老金**: ¥10,959
- **年养老金**: ¥131,514
- **公积金余额**: ¥1,022,316
- **总收益**: ¥4,967,727
- **ROI**: 288.7%
- **回本年龄**: 69.7岁

## 关键改进

### 1. ✅ 算法严格性
- 严格按照用户提供的7步算法实现
- 每一步都有明确的数学公式和计算逻辑
- 支持逐年详细分解计算

### 2. ✅ 口径正确性
- 个税计算：只扣除个人缴费，不重复扣除
- 基数确定：正确使用clamp函数限制在合理范围内
- 账户累计：正确区分个人账户和单位缴费

### 3. ✅ 结果合理性
- ROI从异常的592.6%降至合理的288.7%
- 回本年龄计算合理（69.7岁）
- 所有计算结果与用户正确算式完全一致

### 4. ✅ 功能完整性
- 支持单年度计算
- 支持终身养老金计算
- 提供详细的逐年分解
- 支持参数自定义

## 文件结构

### 新增文件
1. `plugins/china/china_optimized_calculator.py`
   - 优化算法的主要实现
   - 包含YearlyCalculationResult和RetirementResult数据结构
   - 提供ChinaOptimizedCalculator类

2. `test_optimized_calculator.py`
   - 全面的测试脚本
   - 验证算法正确性
   - 提供详细的计算分解

3. `CHINA_OPTIMIZED_ALGORITHM.md`
   - 本总结文档

### 使用示例
```python
from plugins.china.china_optimized_calculator import ChinaOptimizedCalculator

# 创建计算器
calculator = ChinaOptimizedCalculator()

# 计算第一年
result = calculator.calculate_yearly(2024, 30, 180000, 12434, 0.07)

# 计算终身养老金
retirement_result = calculator.calculate_lifetime(180000, 0.02, 0.07)

# 获取详细分解
breakdown = calculator.get_detailed_breakdown(180000, 0.02, 0.07)
```

## 结论

优化后的中国养老金计算器：

1. ✅ **完全符合用户要求**：严格按照7步算法实现
2. ✅ **计算结果准确**：与用户正确算式完全一致
3. ✅ **口径正确**：修正了所有之前的核心错误
4. ✅ **功能完整**：支持单年度和终身计算
5. ✅ **ROI合理**：从异常值降至合理范围

这个优化版本可以作为中国养老金计算的权威实现，确保所有计算都符合实际政策口径。