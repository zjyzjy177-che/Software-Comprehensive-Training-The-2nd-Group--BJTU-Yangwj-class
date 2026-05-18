# BJTU软件综合实训课程——第二小组
## 🎓 BJTU Canteen Simulation | 校园就餐流量仿真系统

## 📌 项目简介

本项目旨在通过**离散时间驱动（Tick-Driven）的仿真技术，模拟北京交通大学（BJTU）高峰时段的学生就餐流量。系统重点分析了教学楼（如思源楼）与宿舍区（如 12 号楼）人流汇聚对食堂（如四食堂、明湖食堂）造成的排队压力，并提供错峰下课方案**的定量评估支持。

## 🛠️ 技术架构

- **开发语言**：Python 3.10+
- **系统架构**：C/S (Client/Server) 架构
- **依赖库**：

| 库 | 用途 | 使用模块 |
|----|------|---------|
| `matplotlib` | 2D 校园地图动态渲染、FuncAnimation 动画驱动、排队曲线、饼图、错峰对比图表 | visualizer.py, peak_shift.py |
| `tkinter` | GUI 登录界面、参数配置面板、仿真启动控制、多语言切换 | gui.py |
| `numpy` | 数值计算、数组操作（学生位置批量处理） | visualizer.py, peak_shift.py |
| `PIL/Pillow`（可选） | 校徽 logo 及校园图片加载与缩放 | gui.py |
| `PyInstaller`（部署用） | 将 Python 项目打包为 macOS .app / Windows .exe 独立可执行文件 | — |

- **标准库**：

| 模块 | 用途 |
|------|------|
| `random` | 学生速度/用餐时间随机化、建筑加权随机选取、验证码生成 |
| `math` | 欧几里得距离计算、学生移动向量 |
| `json` | campus_bounds.json 坐标加载、仿真结果导出、配置文件读写 |
| `threading` | GUI 非可视化模式异步运行仿真，避免界面冻结 |
| `unittest` | 74 项单元测试 + 24 项集成测试框架 |
| `argparse` | CLI 命令行参数解析 |
| `os` / `sys` / `platform` | 跨平台路径处理、系统检测、字体适配 |
| `time` | 仿真计时、性能基准测试、动画帧节流 |

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

### 同学 A（组长）— 核心引擎与系统集成

负责 [`models.py`](models.py)、[`engine.py`](engine.py)、[`main.py`](main.py) 及 [`test_simulation.py`](test_simulation.py)。设计 Student 有限状态机（WALKING → QUEUING → EATING → LEAVING）及 Window/Canteen 的 FIFO 服务队列模型。实现 SimulationEngine 离散时间驱动核心，管理 tick 主循环中的学生生成、状态更新、食堂服务与数据收集。将 BJTUConfig 集成到 main.py，打通 campus_bounds.json → config.py → engine.py → visualizer.py 全链路，支持 CLI 参数、可视化模式双轨运行。编写 `test_member_a.py`（25 项）验证引擎与模型正确性，并负责整体项目进度与代码评审。

### 同学 B — 算法与环境建模

负责 [`campus_bounds.json`](campus_bounds.json)、[`config.py`](config.py)、[`strategies.py`](strategies.py) 及 [`example_config.json`](example_config.json)。采集 BJTU 校园 32 个建筑真实坐标，建立笛卡尔坐标系并编写 campus_bounds.json 作为唯一权威数据源。实现 BJTUConfig 配置管理类，动态推导食堂名称、学生生成位置，支持 JSON 文件导入导出。设计 CanteenSelector 多食堂选择算法，加权综合距离（α）与排队人数（β），引入窗口效率因子与容量惩罚，支持距离优先/排队优先/平衡三种策略及动态权重调整。编写 `test_member_b.py`（34 项）验证坐标数据完整性与算法正确性。

### 同学 C — UI 与可视化

负责 [`visualizer.py`](visualizer.py)。实现 CanteenVisualizer 类，基于 Matplotlib 完成 2D 校园地图实时渲染，学生按状态分色显示（蓝行走/红排队/绿用餐/紫离开），食堂显示排队柱状图。实现 FuncAnimation 动画驱动、实时统计曲线（排队人数变化）与状态分布饼图。支持空格暂停/继续、上下箭头调速、R 键重置视图等交互控制。完成跨平台中文字体适配（Windows/macOS/Linux）及性能优化（增量更新、节流、历史数据裁剪）。修复 matplotlib 后端设置时机导致动画失效的 bug。编写 `test_member_c.py`（15 项）验证可视化初始化、帧渲染及 main.py 接口集成。

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
├── models.py                # 数据模型：Student FSM, Window FIFO队列, Canteen多窗口管理
├── engine.py                # 仿真引擎：SimulationEngine（Tick驱动），集成CanteenSelector
├── main.py                  # 主程序入口：CLI + 可视化 + run_simulation_from_gui供GUI调用
├── config.py                # ✅ 配置模块：BJTU地图坐标、仿真参数、JSON导入导出（v1.5）
├── strategies.py            # ✅ 策略模块：多食堂选择算法（α距离+β排队+效率因子）（v2.0）
├── visualizer.py            # ✅ 可视化模块：Matplotlib动画、三语支持、跨平台字体、TkAgg后端（v2.3.1）
├── gui.py                   # ✅ GUI模块：Tkinter登录/管理员/参数配置/错峰对比按钮（v2.5）
├── peak_shift.py            # ✅ 错峰对比模块：建筑分批注入+四图对比分析（v2.0）
├── campus_bounds.json       # ✅ 校园边界和32个建筑坐标（权威数据源）
├── .gitignore               # Git忽略配置（含gui_users.txt等运行时文件）
├── README.md                # 项目文档
├── INTEGRATION_REPORT.md    # ✅ 集成联调测试报告模板（v1.0）
├── simulation_results.json  # 仿真结果输出示例
├── simulation_results_summary.txt  # 仿真结果摘要
├── test_simulation.py       # 原始测试套件（单元+引擎+集成）
├── test_member_a.py         # ✅ 组长A测试：Student FSM、Window/Canteen、引擎集成（25项）
├── test_member_b.py         # ✅ 组员B测试：坐标验证、BJTUConfig、多食堂选择算法（34项）
├── test_member_c.py         # ✅ 组员C测试：可视化初始化、帧渲染、main.py接口（15项）
├── test_integration.py      # ✅ 集成联调测试：4条数据链路共24项用例（v1.0）
├── picture1-4.png           # ✅ 校园展示图片
├── school_logo.png          # ✅ 校徽logo
└── campus_map.png           # 校园底图（visualizer加载）
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

### 2. engine.py - 仿真引擎层（v1.2）
- **SimulationEngine类**：离散时间驱动核心
  - `tick()`方法：每个周期更新所有实体状态
  - 学生生成、状态更新、食堂服务、数据收集
  - 地图边界对齐campus_bounds.json：(-250,-400)-(450,200)
  - 学生从真实建筑坐标生成（教学楼/宿舍楼）
  - 食堂名称和窗口数从配置获取
- **配置系统**：支持命令行参数和JSON配置文件

### 3. main.py - 集成入口层（v2.0）
- 命令行参数解析
- 仿真流程控制
- 结果输出（JSON格式 + 文本摘要）
- **集成BJTUConfig**：自动从campus_bounds.json加载32个建筑坐标
- **可视化集成**：`initialize_visualization`和`update_visualization`已完成真实实现
- **双模式运行**：无可视化时批量运行，可视化模式逐tick驱动动画更新

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
1. **visualizer.py**：Matplotlib动态渲染（v1.1）
   - `__init__(map_boundaries, title)`：地图范围与campus_bounds.json对齐（-250,-400）-（450,200）
   - `draw_frame(tick, students, canteens)`：2D平面绘图，支持学生状态颜色区分（行走蓝/排队红/用餐绿/离开紫）
   - 校园底图加载：自动检测并加载campus_map.png作为底图背景
   - 实时统计图：排队人数曲线动态刷新 + 学生状态分布饼图 + 信息面板
   - 跨平台字体适配：支持Windows（微软雅黑）、macOS（PingFang）、Linux（文泉驿）
   - 交互控制：空格键暂停/继续、上下箭头调速、R键重置视图
2. **性能优化**：
   - 使用`FuncAnimation`实现动画
   - 增量更新，避免全量重绘
   - 更新频率节流（学生超过100人时限制最小间隔）
   - 历史数据长度限制（最大200条）防止内存溢出

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
- [x] 仿真引擎（engine.py）：加权建筑出发、错峰支持
- [x] 主程序入口（main.py）：CLI + 可视化 + GUI接口 + benchmark
- [x] 测试套件（test_simulation.py）
- [x] 配置模块（config.py）：BJTU地图坐标、spawn_weights建筑权重、仿真参数（v1.7）
- [x] 校园边界文件（campus_bounds.json）：32建筑坐标
- [x] 策略模块（strategies.py）：多食堂选择算法（v2.0）
- [x] 可视化模块（visualizer.py）：Matplotlib动画、BJT时钟、三语、黄三角食堂标（v2.9）
- [x] GUI界面（gui.py）：Tkinter登录/管理员/参数配置/错峰对比按钮（v2.5）
- [x] 错峰对比（peak_shift.py）：建筑分批注入，四图对比分析（v2.0）
- [x] 跨平台兼容：Win/Mac/Linux字体+后端、PyInstaller打包支持
- [x] 集成测试（test_integration.py）：24项全部通过
- [x] 单元测试：组长A 25项 + 组员B 34项 + 组员C 15项 = 74项
- [x] 联调测试报告（INTEGRATION_REPORT.md）
- [x] Git版本控制和文档

### 🔄 待完成
- 无（全部完成）

### ✅ 新增完成（2026/05/15 — 错峰对比 + 部署准备）
- [x] peak_shift.py v2.0：错峰下课方案对比模块
  - 按建筑权重分 4 波延迟注入学生，模拟真实错峰效果
  - 无错峰 vs 错峰 5/10/15/20/30 分钟，生成四图对比 + 文本摘要
  - 实测：0min 峰值 66 → 30min 峰值 24（↓64%）
- [x] config.py v1.7：新增 spawn_weights 建筑出发人数权重
  - 思源楼 1000、逸夫楼 800、嘉园 600、宿舍区 400…
- [x] engine.py v1.4：_get_spawn_position 改为加权随机选取
- [x] visualizer.py v2.9：
  - 地图左上角 BJT 实时时钟（11:50 起，1tick=30s）
  - 排队柱右移+数字独立显示、text_labels 清理修复数字叠加
  - 学生点缩小(8→5)+配色提亮+排队/用餐±14 随机偏移防扎堆
  - 食堂位置改为黄色三角标记+亮红粗体名称
  - 左下信息面板合并单 text 防重叠
- [x] gui.py v2.5：
  - 管理员入口重构为独立弹窗（下拉选择+密钥验证）
  - 管理员专属"用户管理"按钮（仅管理员可见）
  - "错峰对比分析"按钮（橙色，三语 ToolTip）
  - 用户文件路径改为 ~/.bjtu_canteen_users.txt（PyInstaller 兼容）
  - JSON 配置加载后坐标可覆盖 campus_bounds 默认值
- [x] main.py v2.5：新增 --benchmark 模式（1000人×500tick，0.67s）
- [x] PyInstaller 打包验证通过（macOS .app 双击运行）
### ✅ 新增完成（2026/05/12 — 集成阶段）
- [x] main.py v2.1.0：新增 `run_simulation_from_gui` 和 `create_config_from_gui` 函数，供 GUI 调用
- [x] test_integration.py v1.0：全链路集成测试脚本，覆盖4条数据链路24项用例：
  - 链路1：campus_bounds.json → config.py → engine.py（6项）
  - 链路2：strategies.py → engine.py → models.py（4项）
  - 链路3：engine.py → visualizer.py（3项）
  - 链路4：全链路端到端 + GUI接口 + 异常场景（11项）
- [x] INTEGRATION_REPORT.md v1.0：联调测试报告模板，含接口联通矩阵、数据流转验证、正常/异常场景用例
- [x] visualizer.py v2.3.1：macOS后端从MacOSX改为TkAgg，解决Tkinter GUI中动画窗口无法弹出
- [x] gui.py v2.1.1：模块顶部预置matplotlib.use('TkAgg')，防御性确保后端正确

### ✅ 新增完成（2026/05/09 — GUI开发）
- [x] gui.py v2.1：跨平台兼容性修复，包括：
  - SYSTEM_FONT自动检测（Windows/macOS/Linux中文字体适配）
  - 彩色按钮改为Frame+Label实现，解决macOS Aqua主题bg失效
  - 图片加载优雅降级（PIL未安装或图片缺失时静默跳过）
- [x] main.py v2.2.2：create_config_from_gui传递lang参数
- [x] visualizer.py v2.3：全图表标签/图例/状态面板支持简繁En三语

### ✅ 新增完成（2026/04/27）
- [x] visualizer.py v1.1：可视化模块功能完善
- [x] main.py v2.0：全模块集成完成
- [x] engine.py v1.2：坐标系统全面对齐
- [x] config.py v1.4：canteen_names和spawn_positions动态推导

### ✅ 新增完成（2026/04/23）
- [x] strategies.py v2.0：完整的多食堂选择算法实现，支持三种策略类型

### ✅ 新增完成（2026/04/初）
- [x] GUI v2.0：BJTUSimulationGUI完整Tkinter实现（组员C）
  - 登录验证（角色选择/验证码/注册/忘记密码/访客）
  - CAS风格宝蓝主题UI、校徽logo标题栏
  - 仿真参数配置面板、策略与权重调节
  - 四图横排展示栏、友情链接闪烁动画
  - 简繁En三语切换、版权栏
- [x] 组长A/B/C 三人各自单元测试脚本（共74项）

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

**项目状态**：全部模块完成——核心引擎/算法/可视化/GUI/错峰对比五大模块集成联调通过（24项），PyInstaller 打包验证通过（macOS .app 双击运行）。三人单元测试 74 项 + 集成测试 24 项全部通过。跨平台兼容（Win/Mac/Linux）、三语支持（简/繁/En）。**当前阶段：部署准备 + 联调报告收尾。**

