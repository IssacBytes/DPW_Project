# 技术文档目录

本文件夹包含 COVID-19 数据探索平台的详细技术文档，按模块拆分为独立文档。

## 文档列表

| 文档 | 内容 | 对应源文件 |
|------|------|------------|
| `01-architecture.md` | 项目架构总览 | 全部 |
| `02-data-loading.md` | 数据加载模块 | `src/data_loader.py` |
| `03-data-cleaning.md` | 数据清洗模块 | `src/data_cleaner.py` |
| `04-data-analysis.md` | 数据分析模块 | `src/data_analysis.py` |
| `05-visualization.md` | 可视化模块 | `src/visualization.py` |
| `06-gui-app.md` | GUI 应用 | `app.py` |
| `07-data-flow.md` | 数据流与函数调用链 | 全部 |

## 阅读顺序

建议按编号顺序阅读：

1. **架构总览** → 了解整体结构
2. **数据加载** → 数据从哪来
3. **数据清洗** → 数据怎么处理
4. **数据分析** → 数据怎么分析
5. **可视化** → 图表怎么生成
6. **GUI 应用** → 界面怎么交互
7. **数据流** → 串联所有环节
