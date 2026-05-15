# 6. GUI 应用

**对应源文件**：`app.py`（基础版）、`app_extended.py`（扩展版）

## 6.1 技术栈

| 技术 | 用途 |
|------|------|
| **Dash** | Web 应用框架（基于 Flask + React） |
| **dash-bootstrap-components** | UI 组件库（按钮、卡片、布局） |
| **Plotly** | 交互式图表 |
| **pandas / numpy** | 数据处理 |
| **scikit-learn** | 聚类分析（扩展版） |

## 6.2 基础版应用结构 (app.py)

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

## 6.3 扩展版应用结构 (app_extended.py)

### 6.3.1 布局结构

```
┌──────────┬──────────────────────────────────────────┐
│  侧栏    │  Header (标题 + Exit)                     │
│  (可折叠) ├──────────────────────────────────────────┤
│          │  全局控制栏 (Metric | Country | Compare)   │
│  O 概览  ├──────────────────────────────────────────┤
│  ├─Global│                                          │
│  ├─Stats │  tab-content (内容区)                    │
│  └─Time  │                                          │
│  C 对比  │                                          │
│  ├─Cntry │                                          │
│  ├─Cont  │                                          │
│  └─Rank  │                                          │
│  T 趋势  │                                          │
│  ├─Series│                                          │
│  ├─MA    │                                          │
│  ├─Growth│                                          │
│  └─Fatal │                                          │
│  R 关系  │                                          │
│  ├─Corr  │                                          │
│  └─Lag   │                                          │
│  AI 高级 │                                          │
│  ├─Clus  │                                          │
│  └─Anom  │                                          │
│          │  Footer                                   │
└──────────┴──────────────────────────────────────────┘
```

### 6.3.2 设计系统

扩展版使用完整的设计 Token 系统，确保 UI 一致性：

```python
# 字体
FONT_FAMILY = "'Inter', 'Segoe UI', Arial, sans-serif"

# 排版层级
TYPOGRAPHY = {
    'page_title':     {'fontSize': '30px', 'fontWeight': '700', 'color': '#111827'},
    'page_subtitle':  {'fontSize': '14px', 'fontWeight': '500', 'color': '#6b7280'},
    'section_title':  {'fontSize': '20px', 'fontWeight': '650', 'color': '#111827'},
    'section_subtitle': {'fontSize': '14px', 'fontWeight': '400', 'color': '#6b7280'},
    'kpi_number':     {'fontSize': '32px', 'fontWeight': '700', 'color': '#17172e'},
    'kpi_label':      {'fontSize': '11px', 'fontWeight': '700', 'color': '#7b8190'},
    'kpi_subtitle':   {'fontSize': '13px', 'fontWeight': '400', 'color': '#9ca3af'},
    'body_text':      {'fontSize': '14px', 'fontWeight': '400', 'color': '#4b5563'},
    'control_label':  {'fontSize': '11px', 'fontWeight': '700', 'color': '#6b7280'},
}

# 卡片样式
CARD_STYLE = {
    'background': '#ffffff',
    'borderRadius': '12px',
    'boxShadow': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
    'padding': '22px 24px',
    'border': 'none',
}

# 背景色
BG_COLOR = '#f0f2f5'

# 侧栏配色
SIDEBAR_BG = '#1e1e2e'
SIDEBAR_HOVER = '#2a2a3e'
SIDEBAR_ACTIVE_BG = '#2563eb'
SIDEBAR_TEXT = '#c8c8d0'
SIDEBAR_TEXT_MUTED = '#6b6b80'
```

### 6.3.3 侧栏导航（Sidebar）

侧栏可折叠为窄条（仅显示短标签），点击 `◀`/`▶` 按钮切换。

**5 个导航分组：**

| 分组 | 图标 | 子页面 |
|------|:----:|--------|
| **Overview** | O | Global Trends, Summary Statistics, Pandemic Timeline |
| **Comparison Analysis** | C | Country Comparison, Continent Comparison, Rankings |
| **Trend Analysis** | T | Time Series, Moving Average, Growth Rate, Fatality Trend |
| **Relationship Analysis** | R | Correlation, Lead-Lag Analysis |
| **Advanced Analytics** | AI | Clustering, Anomaly Detection |

**侧栏组件：**

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `sidebar-container` | `html.Div` | 侧栏容器（深色背景，flex 列布局） |
| `sidebar-collapsed` | `html.Div` | 折叠状态（仅显示短标签） |
| `sidebar-expanded` | `html.Div` | 展开状态（完整导航面板） |
| `sidebar-toggle` | `html.Div` | 展开状态下的折叠按钮（◀） |
| `sidebar-toggle-collapsed` | `html.Div` | 折叠状态下的展开按钮（▶） |
| `sidebar-state` | `dcc.Store` | 存储侧栏状态（collapsed / active_tab / active_nav） |
| `group-states` | `dcc.Store` | 存储各分组展开/折叠状态 |
| `group-header-{group_id}` | `html.Div` | 分组标题（点击展开/折叠） |
| `group-arrow-{group_id}` | `html.Span` | 箭头指示器（▼ 展开 / ▶ 折叠） |
| `group-items-{group_id}` | `html.Div` | 子页面列表容器 |
| `sidebar-item-{nav_id}` | `html.Div` | 子页面按钮（点击切换内容） |
| `collapsed-item-{nav_id}` | `html.Div` | 折叠状态下的子页面按钮 |

### 6.3.4 14 个标签页

```python
ALL_TAB_VALUES = [
    'tab-global',      # Global Trends
    'tab-overview',    # Summary Statistics
    'tab-pipeline',    # Pandemic Timeline
    'tab-compare',     # Country Comparison
    'tab-continent',   # Continent Comparison
    'tab-rankings',    # Rankings
    'tab-timeseries',  # Time Series
    'tab-ma',          # Moving Average
    'tab-growthrate',  # Growth Rate
    'tab-fatality',    # Fatality Trend
    'tab-correlation', # Correlation
    'tab-lag',         # Lead-Lag Analysis
    'tab-cluster',     # Clustering
    'tab-anomaly',     # Anomaly Detection
]
```

### 6.3.5 顶层容器

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | 整个页面的根容器（`app.layout`） |
| `sidebar-state` | `dcc.Store` | 侧栏状态存储 |
| `group-states` | `dcc.Store` | 分组展开状态存储 |

### 6.3.6 Header（顶部栏）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | Header 容器（flex 布局，标题 + Exit 按钮） |
| — | `html.Span` | 标题文字 "COVID-19 Data Explorer" |
| — | `html.Span` | 副标题 "Extended Edition" |
| `exit-btn` | `html.Button` | Exit 按钮（点击关闭浏览器标签页） |

### 6.3.7 全局控制栏（Global Controls）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | 控制栏容器（flex 布局，3 个下拉框） |
| `global-metric` | `dcc.Dropdown` | 指标选择（12 个指标） |
| `global-country` | `dcc.Dropdown` | 国家选择（262 个国家） |
| `global-compare` | `dcc.Dropdown` | 对比国家选择（多选，最多 6 国） |

### 6.3.8 标签页内容区

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `tab-content` | `html.Div` | 内容容器，根据侧栏选中项动态渲染 |

### 6.3.9 各标签页内部组件

#### Pandemic Timeline

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | Step 1 数据加载（4 个信息卡片） |
| — | `html.Div` | Step 2 数据清洗（清洗操作 + 结果对比） |
| — | `dash_table.DataTable` | Step 3 列概览表格（列名/类型/非空/空值/示例值） |

#### Summary Statistics

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

#### Time Series

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | 6 个 `stat_card` | 统计卡片（最新值/峰值/平均/总计/增长率/最大增长） |
| — | `dcc.Graph` | 双轴图（指标 vs 疫苗接种率） |

#### Growth Rate

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `dcc.Graph` | 增长率分析图（上：数值，下：增长率） |

#### Rankings

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `dcc.Graph` | 前 20 名水平柱状图 |

#### Correlation

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `corr-x` | `dcc.Dropdown` | X 轴指标选择 |
| `corr-y` | `dcc.Dropdown` | Y 轴指标选择 |
| `corr-color` | `dcc.Dropdown` | 着色方式选择 |
| `correlation-insight` | `html.Div` | 相关性分析结论面板 |
| `correlation-chart` | `dcc.Graph` | 散点图 |

#### Continent Comparison

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `dcc.Graph` | 大洲柱状图 |

#### Moving Average

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `ma-stats` | `html.Div` | 6 个统计卡片 |
| `ma-range` | `dcc.Dropdown` | 时间段选择（全量/2020/2021/2022/2023/近180天） |
| `ma-show-raw` | `dcc.Checklist` | 是否显示原始数据 |
| `ma-main-chart` | `dcc.Graph` | 主趋势图（原始 + 7日MA + 30日MA） |
| `ma-recent-chart` | `dcc.Graph` | 窗口对比图（7/14/30 日 MA） |
| `ma-diff-chart` | `dcc.Graph` | 动量图（7日MA - 30日MA） |

#### Anomaly Detection

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `anomaly-window` | `dcc.Dropdown` | 窗口选择（7/14/30 天） |
| `anomaly-threshold` | `dcc.Dropdown` | 阈值选择（1.5σ~3.0σ） |
| `anomaly-chart` | `dcc.Graph` | 异常检测图 |

#### Fatality Trend

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `fatality-chart` | `dcc.Graph` | 病死率双面板图（上：CFR趋势，下：差距柱状图） |
| `fatality-stats` | `html.Div` | 5 个统计卡片（CFR/总病例/总死亡/峰值/趋势） |

#### Lead-Lag Analysis

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `lag-x` | `dcc.Dropdown` | 领先指标选择 |
| `lag-y` | `dcc.Dropdown` | 滞后指标选择 |
| `lag-insight` | `html.Div` | 滞后分析结论面板 |
| `lag-chart` | `dcc.Graph` | 滞后相关性柱状图 |

#### Clustering

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| `cluster-n` | `dcc.Dropdown` | 聚类数选择（k=3~7） |
| `cluster-scatter` | `dcc.Graph` | 聚类散点图 |
| `cluster-summary` | `html.Div` | 聚类摘要卡片 |

### 6.3.10 Footer（底部）

| 组件 ID | 类型 | 说明 |
|---------|------|------|
| — | `html.Div` | 版权文字 "Data: Our World in Data \| Extended Analysis" |

### 6.3.11 组件统计汇总

| 类别 | 数量 |
|------|:----:|
| **有 ID 的组件** | **约 40 个**（可通过回调直接引用） |
| **dcc.Graph（图表）** | 14 个 |
| **dcc.Dropdown（下拉框）** | 12 个 |
| **dash_table.DataTable（表格）** | 2 个 |
| **dcc.Slider（滑块）** | 1 个 |
| **dcc.Interval（定时器）** | 1 个 |
| **dcc.Store（状态存储）** | 2 个 |
| **dcc.Checklist（复选框）** | 1 个 |
| **dcc.DatePickerRange（日期选择）** | 1 个 |
| **html.Button（按钮）** | 2 个（Exit + Play） |

## 6.4 交互回调（Callbacks）

### 侧栏状态回调

```python
# 侧栏折叠/展开 + 导航切换
@app.callback(
    Output('sidebar-state', 'data'),
    [Input('sidebar-toggle', 'n_clicks'),
     Input('sidebar-toggle-collapsed', 'n_clicks')] +
    [Input(f'sidebar-item-{item["nav_id"]}', 'n_clicks') for item in ALL_TAB_ITEMS] +
    [Input(f'collapsed-item-{item["nav_id"]}', 'n_clicks') for item in ALL_TAB_ITEMS],
    State('sidebar-state', 'data')
)
def update_sidebar_state(*args):
    # 切换折叠状态或更新 active_tab
    ...

# 侧栏布局同步
@app.callback(
    [Output('sidebar-container', 'style'),
     Output('sidebar-collapsed', 'style'),
     Output('sidebar-expanded', 'style')] +
    [Output(f'sidebar-item-{item["nav_id"]}', 'style') for item in ALL_TAB_ITEMS] +
    [Output(f'collapsed-item-{item["nav_id"]}', 'style') for item in ALL_TAB_ITEMS],
    Input('sidebar-state', 'data')
)
def sync_sidebar_layout(state):
    # 根据 collapsed/active_nav 更新所有侧栏元素样式
    ...

# 分组展开/折叠
@app.callback(
    [Output(f'group-items-{group["group_id"]}', 'style') for group in SIDEBAR_GROUPS] +
    [Output(f'group-arrow-{group["group_id"]}', 'style') for group in SIDEBAR_GROUPS] +
    [Output(f'group-arrow-{group["group_id"]}', 'children') for group in SIDEBAR_GROUPS] +
    [Output('group-states', 'data')],
    [Input(f'group-header-{group["group_id"]}', 'n_clicks') for group in SIDEBAR_GROUPS],
    State('group-states', 'data')
)
def toggle_group(*args):
    # 切换分组的展开/折叠状态
    ...
```

### 标签页渲染回调

```python
@app.callback(
    Output('tab-content', 'children'),
    [Input('sidebar-state', 'data'),
     Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('global-compare', 'value')]
)
def render_active_tab(sidebar_state, metric, country, compare_list):
    tab = (sidebar_state or {}).get('active_tab', DEFAULT_TAB)
    return html.Div(
        render_tab_content(tab, metric, country, compare_list),
        className='page-shell page-enter',
        key=f'{tab}-{metric}-{country}'
    )
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
    max_date = pd.Timestamp(MONTHLY_DATES[slider_val])
    idx = np.searchsorted(date_values, max_date, side='right')
    filtered_df = df_sorted.iloc[:idx]
    return plot_trend_line(filtered_df, all_c, metric, ...)
```

### 时间轴播放回调

```python
@app.callback(Output('play-interval', 'disabled'), Input('global-play', 'n_clicks'), State('play-interval', 'disabled'))
def toggle_play(n_clicks, disabled):
    return not disabled

@app.callback(Output('global-slider', 'value'), [Input('play-interval', 'n_intervals')], [State('global-slider', 'value')])
def advance_play(n_intervals, current):
    next_val = current + 1
    if next_val >= len(MONTHLY_DATES):
        return 0  # 循环播放
    return next_val
```

### 高级分析回调

```python
# 相关性
@app.callback(
    [Output('correlation-chart', 'figure'), Output('correlation-insight', 'children')],
    [Input('corr-x', 'value'), Input('corr-y', 'value'), Input('corr-color', 'value')]
)
def update_correlation_chart(x_metric, y_metric, color_col):
    return make_correlation_figure(...), correlation_insight(...)

# 移动平均
@app.callback(
    [Output('ma-main-chart', 'figure'), Output('ma-recent-chart', 'figure'),
     Output('ma-diff-chart', 'figure'), Output('ma-stats', 'children')],
    [Input('global-metric', 'value'), Input('global-country', 'value'),
     Input('ma-range', 'value'), Input('ma-show-raw', 'value')]
)
def update_moving_average(metric, country, view_range, show_raw_values):
    ...

# 异常检测
@app.callback(Output('anomaly-chart', 'figure'),
    [Input('global-metric', 'value'), Input('global-country', 'value'),
     Input('anomaly-window', 'value'), Input('anomaly-threshold', 'value')])
def update_anomaly(metric, country, window, threshold):
    ...

# 病死率
@app.callback(
    [Output('fatality-chart', 'figure'), Output('fatality-stats', 'children')],
    [Input('global-country', 'value'), Input('global-compare', 'value')])
def update_fatality(country, compare_list):
    ...

# 滞后分析
@app.callback(
    [Output('lag-chart', 'figure'), Output('lag-insight', 'children')],
    [Input('global-country', 'value'), Input('lag-x', 'value'), Input('lag-y', 'value')])
def update_lag(country, x_metric, y_metric):
    ...

# 聚类
@app.callback([Output('cluster-scatter', 'figure'), Output('cluster-summary', 'children')],
    [Input('cluster-n', 'value')])
def update_cluster(k):
    ...
```

### 退出按钮回调（客户端）

```python
app.clientside_callback(
    """function(n_clicks) { if (n_clicks > 0) { window.close(); } return 'Exit'; }""",
    Output('exit-btn', 'children'),
    Input('exit-btn', 'n_clicks')
)
```

## 6.5 12 个分析指标

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

## 6.6 性能优化

| 优化 | 说明 |
|------|------|
| **Pickle 缓存** | 缓存清洗后的 DataFrame，二次启动仅需 0.5 秒 |
| **二分查找过滤** | `np.searchsorted()` 实现 57 万行数据的快速日期过滤 |
| **时间轴采样** | 每月采样一个日期，减少滑块卡顿 |
| **预计算管道数据** | `PIPELINE_SUMMARY` 和 `PIPELINE_COLS_INFO` 启动时只计算一次 |
| **聚类缓存** | `CLUSTER_CACHE` 缓存不同 k 值的聚类结果，避免重复计算 |
| **关闭 debug 模式** | 避免 Flask 双重重载 |
