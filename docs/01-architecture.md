# 1. 项目架构总览

## 文件结构

```
covid19-data-explorer/
├── run.bat                 # 启动入口（基础版，Windows 双击运行）
├── run_extended.bat        # 启动入口（扩展版，Windows 双击运行）
├── app.py                  # GUI 主程序（基础版，8 个标签页）
├── app_extended.py         # GUI 主程序（扩展版，14 个标签页 + 侧栏导航）
├── compact.csv             # 原始 COVID-19 数据集（570,606 行）
├── compact_cleaned.csv     # 清洗后的数据集（可选导出）
├── data_cache.pkl          # 数据缓存（自动生成，加速启动）
├── requirements.txt        # Python 依赖列表
├── README.md               # 项目说明文档
├── docs/                   # 技术文档目录
│   ├── README.md           # 文档目录
│   ├── 01-architecture.md  # 本文件
│   ├── 02-data-loading.md
│   ├── 03-data-cleaning.md
│   ├── 04-data-analysis.md
│   ├── 05-visualization.md
│   ├── 06-gui-app.md
│   └── 07-data-flow.md
├── src/                    # 核心模块目录
│   ├── __init__.py         # 包初始化
│   ├── data_loader.py      # 数据加载模块
│   ├── data_cleaner.py     # 数据清洗模块
│   ├── data_analysis.py    # 数据分析模块
│   ├── advanced_analysis.py # 高级分析模块
│   └── visualization.py    # 可视化模块
├── assets/
│   └── animations.css      # 页面动画样式
├── output/figures/         # 图表输出目录（可选）
└── clean/                  # 数据预处理脚本
    ├── preprocess_covid_data.py
    ├── check_data.py
    └── data_check.html
```

## 四层架构

整个项目采用 **四层架构**，各层职责清晰，下层为上层提供服务：

```
┌─────────────────────────────────────────────┐
│              GUI 层 (app.py / app_extended.py)│
│  Dash Web 界面、侧栏导航、标签页布局、交互回调 │
│  用户操作 → 调用分析/可视化函数 → 展示结果    │
├─────────────────────────────────────────────┤
│           可视化层 (visualization.py)         │
│  Plotly 图表生成                             │
│  地图 / 折线图 / 柱状图 / 双轴图 / 散点图    │
├─────────────────────────────────────────────┤
│           分析层 (data_analysis.py +         │
│                  advanced_analysis.py)       │
│  统计计算、趋势分析、对比分析、相关性分析      │
│  移动平均、异常检测、病死率、聚类、滞后分析    │
├─────────────────────────────────────────────┤
│         数据层 (data_loader + data_cleaner)  │
│  CSV 加载、数据清洗、缺失值处理、过滤          │
│  返回可执行的 pandas DataFrame               │
└─────────────────────────────────────────────┘
```

## 数据流向

```
compact.csv (原始数据)
    │
    ▼
┌─────────────────┐
│  数据加载层      │  data_loader.load_data()
│  CSV → DataFrame │  CovidDataPreprocessor.load_data()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  数据清洗层      │  data_cleaner.clean_data()
│  去重 / 排序     │  CovidDataPreprocessor.clean_data()
│  填充缺失值      │  handle_missing_values()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  数据分析层      │  data_analysis.descriptive_stats()
│  统计 / 趋势     │  data_analysis.country_trend()
│  对比 / 排名     │  data_analysis.compare_countries()
│  增长率 / 相关   │  data_analysis.top_countries()
│  高级分析        │  advanced_analysis.moving_average()
│  移动平均 / 异常  │  advanced_analysis.anomaly_detection()
│  病死率 / 聚类   │  advanced_analysis.fatality_trend()
│  滞后分析        │  advanced_analysis.cross_lag_correlation()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  可视化层        │  visualization.plot_choropleth_map()
│  地图 / 折线图   │  visualization.plot_trend_line()
│  柱状图 / 散点图 │  visualization.plot_bar_chart()
│  双轴图 / 增长率 │  visualization.plot_dual_axis()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GUI 层          │  app.py (基础版: 8 标签页)
│  Dash Web 界面   │  app_extended.py (扩展版: 14 标签页 + 侧栏)
└─────────────────┘
```

## 各层职责总结

| 层 | 输入 | 输出 | 关键文件 |
|----|------|------|----------|
| 数据层 | CSV 文件 | 清洗后的 DataFrame | `data_loader.py`, `data_cleaner.py` |
| 分析层 | DataFrame | 统计结果 / 处理后的 DataFrame | `data_analysis.py`, `advanced_analysis.py` |
| 可视化层 | DataFrame | Plotly Figure 对象 | `visualization.py` |
| GUI 层 | 用户操作 | HTML 页面 + 交互图表 | `app.py`, `app_extended.py` |

## 两个版本对比

| 特性 | 基础版 (app.py) | 扩展版 (app_extended.py) |
|------|:---------------:|:------------------------:|
| 标签页数量 | 8 | 14 |
| 导航方式 | 横向 `dcc.Tabs` | 左侧可折叠侧栏 |
| 高级分析 | ❌ | ✅ 移动平均、异常检测、病死率、滞后分析、聚类 |
| 设计系统 | 基础样式 | 完整设计 Token（字体、颜色、卡片、间距） |
| 端口 | 8050 | 8051 |
