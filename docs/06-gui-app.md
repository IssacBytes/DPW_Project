# 6. GUI 应用

**对应源文件**：`app.py`

## 6.1 技术栈

| 技术 | 用途 |
|------|------|
| **Dash** | Web 应用框架（基于 Flask + React） |
| **dash-bootstrap-components** | UI 组件库（按钮、卡片、布局） |
| **Plotly** | 交互式图表 |
| **pandas / numpy** | 数据处理 |

## 6.2 应用结构

```
app.py 结构：
├── 1. 导入依赖
├── 2. 数据加载（带 pickle 缓存）
├── 3. 指标定义（12 个分析指标）
├── 4. Dash 应用初始化
├── 5. 布局（Layout）
│   ├── 顶部导航栏（标题 + 退出按钮）
│   ├── 全局控件栏（指标选择、国家选择、对比选择）
│   ├── 标签页导航（8 个标签页）
│   ├── 标签页内容区
│   └── 底部页脚
├── 6. 标签页构建函数（8 个）
├── 7. 共享组件（统计卡片）
├── 8. 交互回调（Callbacks）
└── 9. 主入口（app.run）
```

## 6.3 布局详解

### 顶部导航栏

```python
html.Div([
    html.Span('COVID-19 Data Explorer', style={...}),  # 标题
    html.Span('| Our World in Data', style={...}),      # 副标题
    html.Button('Exit', id='exit-btn', ...)             # 退出按钮
])
```

### 全局控件栏

三个下拉框，在所有标签页中共享：

| 控件 | ID | 功能 |
|------|----|------|
| 指标选择 | `global-metric` | 选择 12 个分析指标之一 |
| 国家选择 | `global-country` | 选择主要分析的国家 |
| 对比选择 | `global-compare` | 选择要对比的其他国家（可多选，最多 6 个） |

### 8 个标签页

```python
TABS = [
    {'label': 'Data Pipeline',    'value': 'tab-pipeline'},
    {'label': 'Overview',         'value': 'tab-overview'},
    {'label': 'Global Trends',    'value': 'tab-global'},
    {'label': 'Country Comparison', 'value': 'tab-compare'},
    {'label': 'Country Deep Dive',  'value': 'tab-deepdive'},
    {'label': 'Rankings',         'value': 'tab-rankings'},
    {'label': 'Correlation',      'value': 'tab-correlation'},
    {'label': 'Continent Analysis', 'value': 'tab-continent'},
]
```

## 6.4 标签页构建函数

### `build_pipeline_tab()` — 数据管道

展示数据从加载到清洗的完整流程。

**三个步骤**：
1. **Step 1: Data Loading** — 源文件、总行数、总列数、日期范围
2. **Step 2: Data Cleaning** — 清洗操作列表 + 清洗前后对比统计
3. **Step 3: Column Overview** — 所有列的数据类型、空值数、示例值表格

**调用的模块函数**：
- `data_cleaner.get_cleaning_summary(df_raw, df)`
- `data_loader.get_columns_info(df)`

### `build_overview_tab(metric)` — 概览

快速了解数据集整体情况。

**组件**：
- 4 个统计卡片（国家总数、日期范围、总行数、全球总计）
- 可翻页的数据表格（前 100 行）

**调用的模块函数**：
- `data_analysis.descriptive_stats(df, metric)`

### `build_global_tab(metric)` — 全球趋势

通过地图和时间轴观察疫情在全球的时空演变。

**组件**：
- 世界地图（Choropleth Map）
- 全球统计面板（总计、平均、最大、国家数）
- 时间轴滑块（每月采样，带播放按钮）
- 趋势折线图

**调用的模块函数**：
- `visualization.plot_choropleth_map(df, metric, date)`
- `visualization.plot_trend_line(filtered_df, countries, metric)`

### `build_compare_tab(metric, country, compare_list)` — 国家对比

对比多个国家在同一指标上的表现。

**组件**：
- 多线折线图（最多 6 个国家）

**调用的模块函数**：
- `visualization.plot_trend_line(df, all_c, metric)`

### `build_deepdive_tab(metric, country)` — 国家深度分析

深入分析单个国家的疫情数据。

**组件**：
- 双轴图（指标 vs 疫苗接种率）
- 增长率分析图（上：数值，下：增长率）

**调用的模块函数**：
- `visualization.plot_dual_axis(df, country, metric, vacc_metric)`
- `visualization.plot_growth_rate(df, country, metric)`

### `build_rankings_tab(metric)` — 排名

查看各国在选定指标上的排名。

**组件**：
- 前 20 名水平柱状图（按大洲着色）

**调用的模块函数**：
- `data_analysis.top_countries(df, metric, n=20)`
- `visualization.plot_bar_chart(top_df, ...)`

### `build_correlation_tab(metric)` — 相关性

探索两个指标之间的关联性。

**组件**：
- 散点图（按大洲着色）

**自动匹配相关指标**：
- 病例 → 死亡
- 死亡 → 病例
- 疫苗 → 病例

**调用的模块函数**：
- `visualization.plot_scatter(plot_df, ...)`

### `build_continent_tab(metric)` — 大洲分析

从大洲维度观察疫情分布。

**组件**：
- 大洲汇总水平柱状图

**调用的模块函数**：
- `visualization.plot_bar_chart(cont_df, ...)`

## 6.5 交互回调（Callbacks）

### 标签页切换回调

```python
@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('global-compare', 'value')]
)
def render_tab(tab, metric, country, compare_list):
    # 根据 tab 值调用对应的 build_*_tab() 函数
```

### 地图更新回调

```python
@app.callback(
    Output('global-map', 'figure'),
    [Input('global-metric', 'value'),
     Input('global-slider', 'value')]
)
def update_global_map(metric, slider_val):
    return plot_choropleth_map(df, metric, MONTHLY_DATES[slider_val])
```

### 趋势图更新回调（带二分查找优化）

```python
@app.callback(
    Output('global-trend-chart', 'figure'),
    [Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('global-compare', 'value'),
     Input('global-slider', 'value')]
)
def update_global_trend(metric, country, compare_list, slider_val):
    # 使用 np.searchsorted 快速过滤日期
    max_date = pd.Timestamp(MONTHLY_DATES[slider_val])
    idx = np.searchsorted(date_values, max_date, side='right')
    filtered_df = df_sorted.iloc[:idx]
    return plot_trend_line(filtered_df, all_c, metric)
```

### 时间轴播放回调

```python
# 点击播放按钮切换 Interval 的启用状态
@app.callback(
    Output('play-interval', 'disabled'),
    Input('global-play', 'n_clicks'),
    State('play-interval', 'disabled')
)
def toggle_play(n_clicks, disabled):
    return not disabled

# Interval 每次触发时推进滑块
@app.callback(
    Output('global-slider', 'value'),
    Input('play-interval', 'n_intervals'),
    State('global-slider', 'value')
)
def advance_play(n_intervals, current):
    next_val = current + 1
    if next_val >= len(MONTHLY_DATES):
        return 0  # 循环播放
    return next_val
```

### 退出按钮回调（客户端）

```python
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.close();
        }
        return 'Exit';
    }
    """,
    Output('exit-btn', 'children'),
    Input('exit-btn', 'n_clicks')
)
```

## 6.6 12 个分析指标

| 指标 ID | 显示名称 | 分组 |
|---------|----------|------|
| `new_cases_smoothed` | Daily New Cases | Cases |
| `new_deaths_smoothed` | Daily New Deaths | Deaths |
| `new_cases_smoothed_per_million` | New Cases per Million | Cases |
| `new_deaths_smoothed_per_million` | New Deaths per Million | Deaths |
| `total_cases_per_million` | Total Cases per Million | Cases |
| `total_deaths_per_million` | Total Deaths per Million | Deaths |
| `people_fully_vaccinated_per_hundred` | Fully Vaccinated (%) | Vaccination |
| `people_vaccinated_per_hundred` | Vaccinated (%) | Vaccination |
| `total_boosters_per_hundred` | Boosters (%) | Vaccination |
| `positive_rate` | Positive Test Rate | Testing |
| `stringency_index` | Stringency Index | Policy |
| `reproduction_rate` | Reproduction Rate | Epidemiology |

## 6.7 性能优化

| 优化 | 说明 |
|------|------|
| **Pickle 缓存** | 缓存清洗后的 DataFrame，二次启动仅需 0.5 秒 |
| **二分查找过滤** | `np.searchsorted()` 实现 57 万行数据的快速日期过滤 |
| **时间轴采样** | 每月采样一个日期，减少滑块卡顿 |
| **关闭 debug 模式** | 避免 Flask 双重重载 |

---

## 6.8 扩展版组件清单（`app_extended.py`）

扩展版在基础版 8 个标签页之上新增 5 个高级分析标签页，共 13 个标签页。布局采用**左侧可折叠侧栏导航**替代传统的横向 `dcc.Tabs`。

### 6.8.1 布局结构

```
┌──────────┬──────────────────────────────────────────┐
│  侧栏    │  Header (标题 + Exit)                     │
│  (可折叠) ├──────────────────────────────────────────┤
│          │  全局控制栏 (Metric | Country | Compare)   │
│  📊 数据  ├──────────────────────────────────────────┤
│  ├─Pipeline│                                         │
│  ├─Overview│  tab-content (内容区)                   │
│  └─Global │                                         │
│  📈 分析  │                                         │
│  ├─Compare│                                         │
│  ├─DeepDive│                                        │
│  ├─Rankings│                                        │
│  ├─Correl.│                                         │
│  └─Continent│                                       │
│  🔬 高级  │                                         │
│  ├─MovAvg │                                         │
│  ├─Anomaly│                                         │
│  ├─Fatality│                                        │
│  ├─LeadLag│                                         │
│  └─Cluster│                                         │
│          │  Footer                                   │
└──────────┴──────────────────────────────────────────┘
```

### 6.8.2 侧栏导航（Sidebar）

侧栏可折叠为窄条（仅显示分组图标），点击 `◀`/`▶` 按钮切换。

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `sidebar-container` | `html.Div` | 侧栏容器（深色背景，flex 列布局） |
| `sidebar-collapsed` | `html.Div` | 折叠状态（仅显示 📊 📈 🔬 图标） |
| `sidebar-expanded` | `html.Div` | 展开状态（完整导航面板） |
| `sidebar-toggle` | `html.Div` | 折叠/展开切换按钮（◀ / ▶） |
| `sidebar-state` | `dcc.Store` | 存储侧栏状态（collapsed / active_tab） |
| `group-states` | `dcc.Store` | 存储各分组展开/折叠状态 |

**3 个导航分组：**

| 分组 | 图标 | 子页面 |
|------|:----:|--------|
| **Data Overview** | 📊 | Data Pipeline, Overview, Global Trends |
| **Analysis Tools** | 📈 | Country Comparison, Country Deep Dive, Rankings, Correlation, Continent Analysis |
| **Advanced** | 🔬 | Moving Avg, Anomalies, Fatality, Lead-Lag, Clusters |

**分组交互组件：**

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `group-header-{group_id}` | `html.Div` | 分组标题（点击展开/折叠） |
| `group-arrow-{group_id}` | `html.Span` | 箭头指示器（▾ 展开 / ▸ 折叠） |
| `group-items-{group_id}` | `html.Div` | 子页面列表容器 |
| `sidebar-item-{nav_id}` | `html.Div` | 子页面按钮（点击切换内容，`nav_id` 保证复用同一 tab 的入口也有唯一组件 ID） |

### 6.8.3 顶层容器

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | 整个页面的根容器（`app.layout`） |

### 6.8.4 Header（顶部栏）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | Header 容器（flex 布局，标题 + Exit 按钮） |
| — | `html.Span` | 标题文字 "COVID-19 Data Explorer \| Extended Edition" |
| `exit-btn` | `html.Button` | Exit 按钮（点击关闭浏览器标签页） |

### 6.8.5 全局控制栏（Global Controls）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | 控制栏容器（flex 布局，3 个下拉框） |
| `global-metric` | `dcc.Dropdown` | 指标选择（12 个指标） |
| `global-country` | `dcc.Dropdown` | 国家选择（262 个国家） |
| `global-compare` | `dcc.Dropdown` | 对比国家选择（多选，最多 6 国） |

### 6.8.6 标签页内容区

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `tab-content` | `html.Div` | 内容容器，根据侧栏选中项动态渲染 |

### 6.8.7 各标签页内部组件

#### Data Pipeline

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | Step 1 数据加载（4 个信息卡片） |
| — | `html.Div` | Step 2 数据清洗（清洗操作 + 结果对比） |
| — | `dash_table.DataTable` | Step 3 列概览表格（列名/类型/非空/空值/示例值） |

#### Overview

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | 4 个 `stat_card` | 统计卡片（国家数/日期范围/总行数/全球总计） |
| `overview-key-metrics` | `html.Div` | 关键指标（总病例/总死亡/疫苗接种数/接种率） |
| `overview-country-filter` | `dcc.Dropdown` | 国家筛选下拉框（ALL + 各国） |
| `overview-date-range` | `dcc.DatePickerRange` | 日期范围选择器 |
| `data-table` | `dash_table.DataTable` | 数据表格（7 列，分页显示） |

#### Global Trends

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `global-map` | `dcc.Graph` | 世界地图（Choropleth） |
| `global-stats` | `html.Div` | 全球统计面板（4 个 stat_card） |
| `global-date-label` | `html.Span` | 当前日期标签 |
| `global-slider` | `dcc.Slider` | 时间轴滑块（月采样） |
| `global-play` | `html.Button` | ▶ Play 播放按钮 |
| `global-trend-chart` | `dcc.Graph` | 趋势折线图 |
| `play-interval` | `dcc.Interval` | 播放定时器（400ms 间隔） |

#### Country Comparison

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `dcc.Graph` | 多国对比折线图（无 ID，直接传 figure） |

#### Country Deep Dive

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `dcc.Graph` | 双轴图（指标 vs 疫苗接种率） |
| — | `dcc.Graph` | 增长率分析图 |

#### Rankings

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `dcc.Graph` | 前 20 名水平柱状图 |

#### Correlation

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `dcc.Graph` | 散点图 |

#### Continent Analysis

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `dcc.Graph` | 大洲柱状图 |

#### Moving Avg（高级）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `ma-chart` | `dcc.Graph` | 移动平均线图 |

#### Anomalies（高级）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `anomaly-window` | `dcc.Dropdown` | 窗口选择（7/14/30 天） |
| `anomaly-threshold` | `dcc.Dropdown` | 阈值选择（1.5σ~3.0σ） |
| `anomaly-chart` | `dcc.Graph` | 异常检测图 |

#### Fatality（高级）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `fatality-chart` | `dcc.Graph` | 病死率双轴图 |
| `fatality-stats` | `html.Div` | 统计卡片（CFR/总病例/总死亡/峰值/趋势） |

#### Lead-Lag（高级）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `lag-x` | `dcc.Dropdown` | 领先指标选择 |
| `lag-y` | `dcc.Dropdown` | 滞后指标选择 |
| `lag-chart` | `dcc.Graph` | 滞后相关性柱状图 |

#### Clusters（高级）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `cluster-n` | `dcc.Dropdown` | 聚类数选择（k=3~7） |
| `cluster-scatter` | `dcc.Graph` | 聚类散点图 |
| `cluster-summary` | `html.Div` | 聚类摘要卡片 |

### 6.8.8 Footer（底部）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Hr` | 分隔线 |
| — | `html.Div` | 版权文字 "Data: Our World in Data \| Extended Analysis" |

### 6.8.9 组件统计汇总

| 类别 | 数量 |
|------|:----:|
| **有 ID 的组件** | **28 个**（可通过回调直接引用） |
| **无 ID 的组件** | 约 15 个（静态布局元素） |
| **dcc.Graph（图表）** | 12 个 |
| **dcc.Dropdown（下拉框）** | 9 个 |
| **dash_table.DataTable（表格）** | 2 个 |
| **dcc.Slider（滑块）** | 1 个 |
| **dcc.Interval（定时器）** | 1 个 |
| **html.Button（按钮）** | 2 个（Exit + Play） |
| **dcc.DatePickerRange（日期选择）** | 1 个 |

---

## 6.9 扩展版侧栏分组更新

`app_extended.py` 的侧栏按分析任务重新分组，只调整导航结构，不新增或删除分析功能，现有 tab value 和图表回调保持不变。

### Overview

| 页面 | 对应 tab |
|------|----------|
| Global Trends | `tab-global` |
| Summary Statistics | `tab-overview` |
| Pandemic Timeline | `tab-pipeline` |

### Comparison Analysis

| 页面 | 对应 tab |
|------|----------|
| Country Comparison | `tab-compare` |
| Continent Comparison | `tab-continent` |
| Rankings | `tab-rankings` |

### Trend Analysis

| 页面 | 对应 tab |
|------|----------|
| Time Series | `tab-deepdive` |
| Moving Average | `tab-ma` |
| Growth Rate | `tab-deepdive` |
| Fatality Trend | `tab-fatality` |

`Time Series` 和 `Growth Rate` 当前复用 Country Deep Dive 页面，因此都指向 `tab-deepdive`。侧栏内部使用独立 `nav_id` 区分两个入口，避免 Dash 组件 ID 重复。

### Relationship Analysis

| 页面 | 对应 tab |
|------|----------|
| Correlation | `tab-correlation` |
| Lead-Lag Analysis | `tab-lag` |

### Advanced Analytics

| 页面 | 对应 tab |
|------|----------|
| Clustering | `tab-cluster` |
| Anomaly Detection | `tab-anomaly` |
