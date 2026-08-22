# 退休金对比系统 — 前端 (Web)

纯前端的多国退休金 / 社保 / 个税对比计算器。所有计算逻辑都是 [`../plugins/*/`](../plugins) 下 Python 插件的 TypeScript 移植版本，运行在浏览器里，不依赖任何后端或 API。

## 本地开发

```bash
npm install
npm run dev
```

## 构建

```bash
npm run build   # 产物在 web/dist
npm run preview # 本地预览构建产物
```

## 部署

推送到 `main` 分支且改动了 `web/**` 时，`.github/workflows/deploy-pages.yml` 会自动构建并发布到 GitHub Pages（需要在仓库 Settings → Pages 中把 Source 设为 "GitHub Actions"）。

## 目录结构

```
src/
├── calc/            # 计算逻辑（移植自 Python 插件）
│   ├── types.ts      # 公共类型 + IRR 求解器
│   ├── currency.ts   # 静态汇率快照与货币转换
│   ├── china.ts       # plugins/china/*
│   ├── usa.ts          # plugins/usa/*
│   ├── singapore.ts    # plugins/singapore/*
│   ├── taiwan.ts        # plugins/taiwan/*
│   ├── japan.ts          # plugins/japan/*
│   └── index.ts       # 国家注册表
├── components/
│   ├── SingleCountryDetail.tsx  # 单国详细分析
│   └── CompareTable.tsx         # 多国对比表格
└── App.tsx           # 表单 + 页面
```

## 已知简化 / 与命令行版本的差异

- **多国对比**（选择 2 个以上国家）使用的公式与命令行版本 `main.py` 的 `compare_countries()` 完全一致（数值已逐项与 Python 源码交叉验证）。
- **单国详细分析**（只选 1 个国家）使用各插件 `calculate_pension()` / `calculate_tax()` / `calculate_social_security()` 的核心公式，但没有复刻命令行版本每个国家专属的 `*_detailed_analyzer.py`（例如台湾的劳保 + 健保 + 个人账户三支柱模型、日本的国税/住民税细分展示）。这些分析器包含大量与核心插件公式不同的额外展示逻辑，超出本页 MVP 范围。
- 汇率使用静态快照（`cache/exchange_rates.json`，2025-09-25），不会请求任何外部 API。
- 中国插件的 `get_retirement_age()`（60/55 岁）与 `calculate_pension()` 内部实际使用的退休年龄（62 岁）不一致 —— 这是原 Python 源码本身的差异，本页忠实保留（对比表格显示 60 岁，与命令行版本一致）。
