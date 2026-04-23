# BJTU软件综合实训课程——第二小组
## 🎓 BJTU Canteen Simulation | 校园就餐流量仿真系统

## 📌 项目简介

本项目旨在通过**离散时间驱动（Tick-Driven）的仿真技术，模拟北京交通大学（BJTU）高峰时段的学生就餐流量。系统重点分析了教学楼（如思源楼）与宿舍区（如 12 号楼）人流汇聚对食堂（如四食堂、明湖食堂）造成的排队压力，并提供错峰下课方案**的定量评估支持。

## 🛠️ 技术架构

- **开发语言**：Python 3.10+
- **系统架构**：C/S (Client/Server) 架构
- **核心库**：
  - `Matplotlib`：负责实时排队曲线绘制及动态渲染。
  - `Tkinter`：负责参数配置界面的 GUI 搭建。
  - `Standard Library`：利用 `time`, `platform`, `random` 等实现底层仿真引擎。

## 🌟 核心功能

1. **校园环境数字化建模**：支持自定义教学楼、宿舍楼与食堂的坐标及服务效率。
2. **双重流量模拟**：同时模拟“下课放学”与“宿舍出发”两股人流的汇聚效应。
3. **多食堂并行算法**：学生会根据距离及实时拥挤度动态选择最优食堂。
4. **错峰方案对比**：一键生成不同时间偏移量下的排队峰值对比图表。

## 👥 团队分工

| 成员              | 角色              | 核心贡献                                          |
| ----------------- | ----------------- | ------------------------------------------------- |
| **同学 A (组长)** | **核心引擎/架构** | 负责仿真主循环、学生状态机及系统整体集成。        |
| **同学 B**        | **算法/环境建模** | 负责 BJTU 地图坐标映射、食堂选择逻辑及错峰算法。  |
| **同学 C**        | **UI/可视化**     | 负责 GUI 界面开发、跨平台字体适配及动态图表渲染。 |

## 🚀 快速开始

### 环境要求
- Python 3.10+
- 依赖库：无额外依赖（纯Python标准库实现）

### 安装与运行
```bash
# 克隆项目
git clone https://github.com/zjyzjy177-che/Software-Comprehensive-Training-The-2nd-Group--BJTU-Yangwj-class.git
cd Software-Comprehensive-Training-The-2nd-Group--BJTU-Yangwj-class

# 运行仿真
python main.py                         # 默认配置运行
python main.py --ticks 500 --students 100 --canteens 3  # 自定义参数
python main.py --test                  # 测试模式（50周期，少量学生）
python main.py --visualize             # 启用可视化（预留功能）
```

### 命令行参数
```
--ticks N         仿真周期数（默认：1000）
--students N      初始学生数量（默认：100）
--canteens N      食堂数量（默认：3）
--spawn-rate R    学生生成速率（默认：0.1）
--config FILE     配置文件路径（JSON格式）
--output FILE     输出文件路径（默认：simulation_results.json）
--visualize       启用可视化（预留）
--quiet           安静模式，减少输出
--test            测试模式，快速验证
--seed N          随机种子（确保可重复性）
```

## 📁 项目结构

```
bjtu_canteen_simulation/
├── models.py              # 数据模型：Student, Canteen, 策略接口
├── engine.py              # 仿真引擎：SimulationEngine（Tick驱动）
├── main.py                # 主程序入口：命令行接口
├── test_simulation.py     # 测试套件：单元测试、集成测试
├── config.py              # ✅ 配置模块：BJTU地图坐标、仿真参数（v1.3）
├── strategies.py          # 🔄 策略模块：多食堂选择算法（模板完成）
├── visualizer.py          # 🔄 可视化模块：Matplotlib动态渲染（模板完成）
├── campus_bounds.json     # ✅ 校园边界和建筑坐标文件（v0.1）
├── .gitignore             # Git忽略配置
├── README.md              # 项目文档
├── simulation_results.json # 仿真结果输出示例
└── simulation_results_summary.txt # 仿真结果摘要
```

## 🏗️ 核心模块说明

### 1. models.py - 数据模型层
- **Student类**：学生实体，实现有限状态机
  - 状态：行走(WALKING) → 排队(QUEUING) → 用餐(EATING) → 离开(LEAVING)
  - 坐标移动、边界检查、状态转换验证
- **Canteen类**：食堂实体，管理窗口队列
  - FIFO服务逻辑，智能窗口分配
  - 容量控制，统计数据收集
- **策略模式接口**：预留多食堂选择算法扩展
  - `CanteenSelectionStrategy`基类
  - `DistanceBasedStrategy`示例实现

### 2. engine.py - 仿真引擎层
- **SimulationEngine类**：离散时间驱动核心
  - `tick()`方法：每个周期更新所有实体状态
  - 学生生成、状态更新、食堂服务、数据收集
  - 地图边界检查，防止坐标溢出
- **配置系统**：支持命令行参数和JSON配置文件

### 3. main.py - 集成入口层
- 命令行参数解析
- 仿真流程控制
- 结果输出（JSON格式 + 文本摘要）
- 预留`visualizer.py`和`config.py`调用接口

### 4. test_simulation.py - 测试套件
- 单元测试：验证Student和Canteen核心功能
- 引擎测试：验证SimulationEngine正确性
- 集成测试：完整仿真流程验证

## 🔧 扩展开发指南

### 实现多食堂选择算法（组员B）
1. **config.py**：定义BJTU校园坐标字典
   ```python
   # 示例坐标（单位：米）
   BJTU_COORDINATES = {
       "思源楼": (100, 200),
       "12号楼": (300, 400),
       "四食堂": (500, 300),
       "明湖食堂": (700, 300),
       ...
   }
   ```
2. **strategies.py**：实现`CanteenSelector`类
   - `select_best_canteen(student_pos, canteens_status)`
   - 算法要求：综合考虑距离和排队人数
   - 权重公式：`score = α × 距离 + β × 排队人数`

### 实现可视化模块（组员C）
1. **visualizer.py**：Matplotlib动态渲染
   - `draw_frame(tick, students, canteens)`：2D平面绘图
   - 实时统计图：排队人数曲线动态刷新
   - 跨平台字体适配：自动检测macOS/Windows系统
2. **性能优化**：
   - 使用`FuncAnimation`实现动画
   - 增量更新，避免全量重绘
   - 大数据量下的渲染优化

### 接口对齐要求
- 所有模块必须与`engine.py`的`SimulationEngine`接口对齐
- 配置模块需支持`config['gap_time']`参数（下课时间差）
- 可视化模块需支持实时数据更新和暂停/继续控制

## 📊 仿真结果示例

```bash
# 运行测试仿真
python main.py --ticks 100 --students 50 --canteens 2

# 输出示例
仿真周期数: 100
总生成学生数: 52
总服务学生数: 15
最大排队人数: 8
平均等待时间: 12.5周期
食堂利用率: 四食堂(68%), 明湖食堂(72%)
```

## 🧪 测试与验证

```bash
# 运行完整测试套件
python test_simulation.py --all

# 运行特定测试类型
python test_simulation.py --unit      # 单元测试
python test_simulation.py --engine    # 引擎测试
python test_simulation.py --integration  # 集成测试
```

## ⚙️ 算法配置指南

### 1. 配置文件使用
系统支持JSON格式的配置文件，可通过`--config`参数指定：

```bash
python main.py --config example_config.json
```

配置文件包含三个主要部分：
- `coordinates`: BJTU校园建筑坐标
- `simulation_params`: 仿真参数（周期数、学生数量、食堂位置等）
- `algorithm_params`: 算法参数（距离权重、排队权重等）

### 2. 算法参数说明
在`algorithm_params`中可配置以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `distance_weight` | 0.3 | 距离权重（α），值越大表示距离越重要 |
| `queue_weight` | 0.7 | 排队人数权重（β），值越大表示排队人数越重要 |
| `max_walk_distance` | 1000.0 | 最大步行距离（米），超过此距离的食堂不考虑 |
| `prefer_near_canteen` | true | 是否优先选择近的食堂 |

**权重公式**：`score = α × 归一化距离 + β × 归一化排队人数`

### 3. 策略类型
系统支持三种选择策略，可通过修改`algorithm_params`调整：

1. **距离优先**：`distance_weight=0.9, queue_weight=0.1`
2. **排队优先**：`distance_weight=0.3, queue_weight=0.7`（默认）
3. **平衡策略**：`distance_weight=0.7, queue_weight=0.3`

### 4. 食堂效率因子
算法还考虑食堂的窗口数量和服务速率：
- **窗口数量**：窗口越多，排队处理能力越强
- **服务速率**：速率越高，服务速度越快
- **效率因子**：`窗口数量 × 服务速率`，效率越高排队影响越小

### 5. 示例配置
```json
{
  "algorithm_params": {
    "distance_weight": 0.4,
    "queue_weight": 0.6,
    "max_walk_distance": 800.0,
    "prefer_near_canteen": true
  },
  "simulation_params": {
    "window_counts": [10, 15, 3, 20],
    "service_rates": [1.0, 1.0, 1.0, 1.0]
  }
}
```

### 6. 动态权重调整
算法支持根据仿真进度动态调整权重：
- **高峰时段**（仿真中期）：增加`queue_weight`
- **非高峰时段**（仿真开始/结束）：增加`distance_weight`

## 📝 开发进度

### ✅ 已完成
- [x] 核心数据模型（models.py）
- [x] 仿真引擎（engine.py）
- [x] 主程序入口（main.py）
- [x] 测试套件（test_simulation.py）
- [x] 配置模块（config.py）：BJTU地图坐标、仿真参数、算法权重（v1.3）
- [x] 校园边界文件（campus_bounds.json）：包含校园边界和32个建筑坐标（v0.1）
- [x] 策略模块模板（strategies.py）：多食堂选择算法基础结构
- [x] 可视化模块模板（visualizer.py）：Matplotlib动态渲染基础结构
- [x] Git版本控制和文档

### 🔄 待实现
- [ ] visualizer.py：实现完整的Matplotlib动态可视化功能（模板已完成）
- [ ] 性能优化和大规模仿真测试
- [ ] 错峰方案对比功能实现
- [ ] GUI界面开发（Tkinter）

### ✅ 新增完成（2026/04/23）
- [x] strategies.py：完整的多食堂选择算法实现，支持：
  - 距离权重（α）和排队权重（β）配置
  - 食堂效率因子（窗口数量×服务速率）
  - 动态权重调整（高峰/非高峰时段）
  - 与config.py和engine.py的完整集成
  - 三种策略类型：距离优先、排队优先、平衡策略

## 👥 团队协作流程

1. **代码规范**：遵循PEP8，添加详细中文注释
2. **版本控制**：使用Git分支开发，PR合并到main
3. **测试驱动**：新功能需包含相应测试用例
4. **文档同步**：代码变更需更新README和接口文档
5. **定期同步**：每周进行代码评审和进度同步

## 📞 技术支持

如有问题或建议，请：
1. 查看详细代码注释和测试用例
2. 使用`--test`模式快速验证功能
3. 通过GitHub Issues提交问题
4. 团队成员间及时沟通协调

---

**项目状态**：核心仿真引擎已完成，配置模块（v1.3）和校园边界文件（v0.1）已就绪，**多食堂选择算法已完整实现并集成**，可视化模板已搭建，进入UI开发和可视化实现阶段

