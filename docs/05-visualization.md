# 5. 可视化模块

**对应源文件**：`src/visualization.py`

## 5.1 模块职责

使用 Plotly 生成交互式数据可视化图表，采用 OWID（Our World in Data）风格：简洁、学术、高信息密度。

## 5.2 设计风格

### 配色方案

```python
# 10 种区分度高的线条颜色
LINE_COLORS = ['#2a4d8f', '#b91f1f', '#1a7a3a', '#d4a017', '#6b3fa0',
               '#c85a17', '#1a5b7a', '#8b4513', '#2d6a4f', '#9b2226']

# 按指标类型自动选择配色
COLOR_SCALES = {
    'cases': 'Reds',       # 病例 → 红色系
    'deaths': 'Greys',     # 死亡 → 灰色系
    'vaccinations': 'Blues', # 疫苗 → 蓝色系
    'testing': 'Purples',  # 检测 → 紫色系
    'default': 'YlOrRd'    # 默认 → 黄橙红
}
```

### 基础样式

```python
OWID_BASE = {
    'font': {'family': 'Arial, Helvetica, sans-serif', 'size': 12, 'color': '#333'},
    'plot_bgcolor': '#fafafa',   # 浅灰背景
    'paper_bgcolor': '#ffffff',  # 白色画布
}
```

### 通用样式函数

| 函数 | 作用 |
|------|------|
| `_apply_base(fig)` | 设置字体（Arial）和背景色 |
| `_apply_axes(fig)` | 设置坐标轴网格线（`#e8e8e8`）和刻度 |

## 5.3 图表类型详解

### 5.3.1 世界地图：`plot_choropleth_map()`

```python
def plot_choropleth_map(df, metric, date_str, title=None) -> go.Figure:
```

**类型**：Choropleth Map（等值区域图）

**用途**：展示全球各国在某个日期的指标分布。

**参数**：
- `df`：完整 DataFrame
- `metric`：要展示的指标列名
- `date_str`：日期字符串（`YYYY-MM-DD`）

**交互**：
- 鼠标悬停显示：国家名、指标数值、大洲、人口
- 颜色越深表示数值越高

**配色**：按指标类型自动选择
- `death` 相关 → `Greys`（灰色系）
- `vaccin` 相关 → `Blues`（蓝色系）
- `case` 相关 → `Reds`（红色系）
- 其他 → `YlOrRd`（黄橙红）

**地图设置**：
- Natural Earth 投影
- 显示国界、海岸线、海洋
- 纬度范围：-55 到 75
- 经度范围：-170 到 190

### 5.3.2 趋势折线图：`plot_trend_line()`

```python
def plot_trend_line(df, countries, metric, title=None) -> go.Figure:
```

**类型**：多线折线图

**用途**：对比多个国家在同一指标上的时间趋势。

**参数**：
- `df`：DataFrame
- `countries`：国家列表
- `metric`：指标列名
- `title`：图表标题

**交互**：
- `hovermode='x unified'` — 鼠标悬停时统一显示所有线条在该日期的数值
- 每条线颜色不同，图例在顶部水平排列

### 5.3.3 排名柱状图：`plot_bar_chart()`

```python
def plot_bar_chart(df, x_col, y_col, title, color_col=None) -> go.Figure:
```

**类型**：水平柱状图

**用途**：展示排名（如 Top 20 国家）。

**参数**：
- `df`：DataFrame
- `x_col`：数值列（柱状图长度）
- `y_col`：分类列（柱状图标签）
- `color_col`：着色列（如按大洲着色）

**排序**：按数值升序排列（底部最高）

### 5.3.4 双轴图：`plot_dual_axis()`

```python
def plot_dual_axis(df, country, metric_left, metric_right) -> go.Figure:
```

**类型**：双 Y 轴折线图

**用途**：对比两个不同量级的指标（如新增病例 vs 疫苗接种率）。

**参数**：
- `df`：DataFrame
- `country`：国家名
- `metric_left`：左轴指标（如新增病例）
- `metric_right`：右轴指标（如疫苗接种率）

**交互**：
- `hovermode='x unified'` — 统一显示两个指标

### 5.3.5 增长率图：`plot_growth_rate()`

```python
def plot_growth_rate(df, country, metric) -> go.Figure:
```

**类型**：上下双面板图

**用途**：分析疫情的增长/下降趋势。

**面板**：
- **上方面板**：每日数值折线图
- **下方面板**：每日增长率柱状图

**内部调用**：`data_analysis.growth_rate_analysis()` 计算增长率数据

### 5.3.6 散点图：`plot_scatter()`

```python
def plot_scatter(df, x_col, y_col, color_col=None, title=None) -> go.Figure:
```

**类型**：散点图

**用途**：探索两个指标之间的相关性。

**参数**：
- `df`：DataFrame
- `x_col`：X 轴指标
- `y_col`：Y 轴指标
- `color_col`：着色列（按大洲着色）

**交互**：
- 鼠标悬停显示：国家名、X 值、Y 值
- 每个点代表一个国家

### 5.3.7 迷你图：`plot_sparkline()`

```python
def plot_sparkline(series, height=30, width=120) -> go.Figure:
```

**类型**：迷你趋势线

**用途**：在表格或提示框中嵌入小图。

**特点**：
- 无坐标轴、无标签
- 极小尺寸（30px 高）
- 透明背景

## 5.4 图表与标签页对应关系

| 标签页 | 图表函数 | 图表类型 |
|--------|----------|----------|
| Global Trends | `plot_choropleth_map()` | 世界地图 |
| Global Trends | `plot_trend_line()` | 趋势折线图 |
| Country Comparison | `plot_trend_line()` | 多线折线图 |
| Country Deep Dive | `plot_dual_axis()` | 双轴图 |
| Country Deep Dive | `plot_growth_rate()` | 增长率图 |
| Rankings | `plot_bar_chart()` | 排名柱状图 |
| Correlation | `plot_scatter()` | 散点图 |
| Continent Analysis | `plot_bar_chart()` | 大洲柱状图 |

## 5.5 图表配置

所有图表使用统一的 Plotly 配置：

```python
PLOTLY_CONFIG = {
    'displayModeBar': True,      # 显示工具栏
    'displaylogo': False,        # 隐藏 Plotly logo
    'modeBarButtonsToRemove': [  # 移除多余按钮
        'sendDataToCloud', 'lasso2d', 'select2d',
        'autoScale2d', 'toggleSpikelines',
        'hoverClosestCartesian', 'hoverCompareCartesian',
        'zoomIn2d', 'zoomOut2d'
    ]
}
```

工具栏只保留 3 个核心按钮：
- ✋ **平移/拖动** — 移动图表视图
- 🔍 **框选缩放** — 框选区域放大
- 🔄 **重置视图** — 恢复默认显示范围
