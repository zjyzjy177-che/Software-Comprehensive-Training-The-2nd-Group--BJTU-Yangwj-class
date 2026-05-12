# BJTU 校园就餐流量仿真系统 — 集成联调测试报告

> **阶段**: 第10-12周 系统集成联调测试
> **小组**: 第二小组
> **日期**: 2026年__月__日

---

## 1. 接口联通测试

### 1.1 模块间接口矩阵

| 调用方 | 被调用方 | 接口/函数 | 联通状态 | 备注 |
|--------|---------|----------|---------|------|
| main.py | config.py | `BJTUConfig()` | ☐ 通过 / ☐ 失败 | |
| main.py | config.py | `config.get_simulation_config()` | ☐ 通过 / ☐ 失败 | |
| main.py | engine.py | `SimulationEngine(config)` | ☐ 通过 / ☐ 失败 | |
| main.py | visualizer.py | `initialize_visualization(config)` | ☐ 通过 / ☐ 失败 | |
| main.py | visualizer.py | `update_visualization(vis, tick, students, canteens)` | ☐ 通过 / ☐ 失败 | |
| engine.py | strategies.py | `create_selector_from_config(config)` | ☐ 通过 / ☐ 失败 | |
| engine.py | strategies.py | `selector.select_best_canteen(pos, canteens)` | ☐ 通过 / ☐ 失败 | |
| engine.py | models.py | `Student.update_state(boundaries)` | ☐ 通过 / ☐ 失败 | |
| engine.py | models.py | `Canteen.add_student_to_queue(student)` | ☐ 通过 / ☐ 失败 | |
| config.py | campus_bounds.json | `json.load(bounds_file)` | ☐ 通过 / ☐ 失败 | |

### 1.2 联通性问题记录

| 编号 | 问题描述 | 严重程度 | 修复状态 |
|------|---------|---------|---------|
| I-001 | | 高/中/低 | 已修复/待修复 |
| I-002 | | 高/中/低 | 已修复/待修复 |

---

## 2. 数据流转测试

### 2.1 数据流链路验证

| 链路 | 数据起点 | 经过模块 | 数据终点 | 验证结果 |
|------|---------|---------|---------|---------|
| L1: 坐标数据流 | campus_bounds.json | config.py → main.py → engine.py | engine.canteens[].position | ☐ 通过 / ☐ 失败 |
| L2: 配置参数流 | main.py CLI/GUI | config.py → engine.py | engine.config | ☐ 通过 / ☐ 失败 |
| L3: 学生状态流 | engine._spawn_students | engine.tick → models.Student | Student.state 序列 | ☐ 通过 / ☐ 失败 |
| L4: 可视化数据流 | engine.tick() | main.py → visualizer.py | visualizer.draw_frame() | ☐ 通过 / ☐ 失败 |
| L5: 食堂选择流 | student.position | strategies.py → engine.py | student.target_canteen_id | ☐ 通过 / ☐ 失败 |

### 2.2 关键数据一致性检查

| 检查项 | 期望 | 实际 | 一致? |
|--------|------|------|------|
| JSON 建筑数 vs config.coordinates 数量 | 32 | ___ | ☐ |
| config.canteen_count vs engine.canteens 数量 | 相等 | ___ | ☐ |
| Student.target_canteen_id 对应的食堂存在 | 全部有效 | ___ | ☐ |
| engine.tick 序号 vs visualizer 收到的 tick | 一致 | ___ | ☐ |
| engine.get_statistics() 中 served_count 与各食堂之和 | 一致 | ___ | ☐ |

### 2.3 数据流转问题记录

| 编号 | 问题描述 | 影响范围 | 修复状态 |
|------|---------|---------|---------|
| D-001 | | | |
| D-002 | | | |

---

## 3. 正常场景运行测试

### 3.1 测试场景一：测试模式（小规模快速验证）

```
命令: python3 main.py --test
参数: max_ticks=150, student_count=30, canteen_count=2, spawn_rate=0.08
```

| 指标 | 期望 | 实际结果 |
|------|------|---------|
| 仿真完成 tick 数 | 150 | ___ |
| 总生成学生 >= 30 | >=30 | ___ |
| 程序退出码 | 0 | ___ |
| 输出文件 simulation_results.json | 生成 | ___ |

### 3.2 测试场景二：标准模式

```
命令: python3 main.py --ticks 500 --students 100 --canteens 3
参数: max_ticks=500, student_count=100, canteen_count=3, spawn_rate=0.1
```

| 指标 | 期望 | 实际结果 |
|------|------|---------|
| 仿真完成 tick 数 | 500 | ___ |
| 总服务学生 > 0 | >0 | ___ |
| 最大排队人数 > 0 | >0 | ___ |
| 无异常退出 | exit 0 | ___ |

### 3.3 测试场景三：可视化模式

```
命令: python3 main.py --test --visualize
```

| 指标 | 期望 | 实际结果 |
|------|------|---------|
| Matplotlib 窗口弹出 | 正常显示 | ___ |
| 动画运行至结束 | 150 tick 完成 | ___ |
| 交互控制（空格暂停/继续） | 正常响应 | ___ |
| 窗口关闭无 TclError | 无报错 | ___ |

### 3.4 正常场景问题记录

| 编号 | 问题描述 | 复现步骤 | 修复状态 |
|------|---------|---------|---------|
| N-001 | | | |
| N-002 | | | |

---

## 4. 异常场景测试

### 4.1 异常输入测试用例

| 编号 | 异常场景 | 输入 | 预期行为 | 实际结果 | 通过? |
|------|---------|------|---------|---------|------|
| E-01 | 缺失 campus_bounds.json | 删除 JSON 文件后运行 | 回退到 DEFAULT_COORDINATES，打印警告 | ___ | ☐ |
| E-02 | JSON 格式错误 | JSON 语法错误 | config 回退，打印警告 | ___ | ☐ |
| E-03 | canteen_count=0 | `--canteens 0` | config 验证报 ValueError | ___ | ☐ |
| E-04 | max_ticks <= 0 | `--ticks -1` | config 验证报 ValueError | ___ | ☐ |
| E-05 | spawn_rate > 1 | spawn_rate=5.0 | config 验证报 ValueError | ___ | ☐ |
| E-06 | 非法配置文件路径 | `--config nonexist.json` | 打印错误退出 | ___ | ☐ |
| E-07 | visualizer.py 缺失 | 删除 visualizer.py 后 --visualize | 回退到无可视化模式，不崩溃 | ___ | ☐ |
| E-08 | 极大 tick 数 | `--ticks 1000000` | 正常运行不 OOM | ___ | ☐ |
| E-09 | 缺失 campus_map.png | 无底图文件 | 打印提示，地图正常渲染 | ___ | ☐ |
| E-10 | 查询不存在建筑 | `config.get_coordinate('不存在')` | 抛出 KeyError | ___ | ☐ |

### 4.2 异常场景问题记录

| 编号 | 问题描述 | 异常类型 | 修复状态 |
|------|---------|---------|---------|
| A-001 | | | |
| A-002 | | | |

---

## 5. 发现的问题及修复汇总

| 编号 | 发现阶段 | 问题描述 | 负责人 | 修复方案 | 状态 |
|------|---------|---------|--------|---------|------|
| | | | | | |
| | | | | | |

---

## 6. 测试结论

- [ ] 接口联通：所有模块间接口联通正常（__/10 项通过）
- [ ] 数据流转：4 条数据链路数据传递正确
- [ ] 正常运行：典型参数下系统运行正常，输出符合预期
- [ ] 异常处理：__ 种异常场景下系统行为符合预期
- [ ] **系统集成联调测试通过，可进入下一阶段**

---

### 附录：集成测试运行命令

```bash
# 运行全链路集成测试
python3 test_integration.py --verbose

# 运行原有单元测试
python3 test_simulation.py --all

# 测试 GUI 接口
python3 -c "from main import run_simulation_from_gui; print(run_simulation_from_gui({'max_ticks':10,'student_count':5,'canteen_count':2,'spawn_rate':0.1}))"
```
