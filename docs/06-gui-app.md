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
