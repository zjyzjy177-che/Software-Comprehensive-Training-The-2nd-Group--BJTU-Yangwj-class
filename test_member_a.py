"""
组长A 测试脚本 - 核心引擎与系统集成
======================================
负责模块：models.py, engine.py, main.py（集成）
测试内容：
  1. Student 有限状态机（WALKING → QUEUING → EATING → LEAVING）
  2. Window FIFO 服务逻辑
  3. Canteen 多窗口队列管理
  4. SimulationEngine tick 驱动
  5. 完整仿真流程（含 BJTUConfig 集成）

运行方式：
  python3 test_member_a.py
  python3 test_member_a.py --full    # 含完整仿真（较慢）
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

TESTS_PASSED = 0
TESTS_FAILED = 0


def check(name, condition):
    global TESTS_PASSED, TESTS_FAILED
    if condition:
        TESTS_PASSED += 1
        print(f"  [PASS] {name}")
    else:
        TESTS_FAILED += 1
        print(f"  [FAIL] {name}")


# ============================================================
# 1. models.py 单元测试
# ============================================================
def test_models():
    print("=" * 60)
    print("1. models.py - Student & Canteen 模型测试")
    print("=" * 60)

    from models import Student, Canteen, StudentState, Window

    # --- Student 测试 ---
    print("\n--- Student 状态机 ---")
    s = Student(student_id=1, position=(0.0, 0.0), destination=(100.0, 0.0), speed=5.0, eating_time=3)

    check("初始状态为 WALKING", s.state == StudentState.WALKING)
    check("初始 position 正确", s.position == (0.0, 0.0))
    check("destination 正确", s.destination == (100.0, 0.0))

    # 移动测试
    s.update_state()
    check("移动后 x > 0", s.position[0] > 0)

    # 到达测试：直接把学生放到食堂门口
    s2 = Student(student_id=2, position=(99.0, 0.0), destination=(100.0, 0.0), speed=5.0, eating_time=3)
    s2.update_state()
    check("到达食堂后状态变为 QUEUING", s2.state == StudentState.QUEUING)

    # start_eating 测试
    s3 = Student(student_id=3, position=(0.0, 0.0), destination=(0.0, 0.0), speed=1.0, eating_time=3)
    s3.state = StudentState.QUEUING
    s3.start_eating()
    check("start_eating 后状态变为 EATING", s3.state == StudentState.EATING)

    # 无效状态转换应抛异常
    try:
        s3.start_eating()
        check("重复 start_eating 应抛异常", False)
    except ValueError:
        check("重复 start_eating 正确抛出 ValueError", True)

    # 用餐结束 → LEAVING
    for _ in range(4):
        s3.update_state()
    check("用餐结束后状态变为 LEAVING", s3.state == StudentState.LEAVING)

    # --- Window 测试 ---
    print("\n--- Window FIFO 队列 ---")
    w = Window(window_id=0, service_rate=1.0)
    s_q = Student(student_id=10, position=(0.0, 0.0), destination=(0.0, 0.0))
    s_q.state = StudentState.QUEUING

    w.add_student(s_q)
    check("加入队列后 queue_length=1", w.get_queue_length() == 1)
    w.serve_next_student()
    check("服务后学生状态变为 EATING", s_q.state == StudentState.EATING)
    check("服务后 queue_length=0", w.get_queue_length() == 0)

    # --- Canteen 测试 ---
    print("\n--- Canteen 多窗口管理 ---")
    c = Canteen(canteen_id=1, name="测试食堂", position=(100.0, 100.0), window_count=3, capacity=50)
    check("创建后窗口数=3", c.get_window_count() == 3)
    check("初始排队人数=0", c.get_total_queue_length() == 0)

    # 添加学生测试
    s_c = Student(student_id=20, position=(100.0, 100.0), destination=(100.0, 100.0))
    s_c.state = StudentState.QUEUING
    result = c.add_student_to_queue(s_c)
    check("添加学生成功", result is True)
    check("排队人数=1", c.get_total_queue_length() == 1)


# ============================================================
# 2. engine.py 测试
# ============================================================
def test_engine():
    print("\n" + "=" * 60)
    print("2. engine.py - SimulationEngine 集成测试")
    print("=" * 60)

    from engine import SimulationEngine
    from config import BJTUConfig

    print("\n--- 使用 BJTUConfig 初始化引擎 ---")
    config_obj = BJTUConfig()
    config = config_obj.get_simulation_config()
    config['max_ticks'] = 30
    config['student_count'] = 10
    config['canteen_count'] = 2
    config['spawn_rate'] = 0.1

    check("map_boundaries 来自 campus_bounds.json",
          config['map_boundaries'] == (-250.0, -400.0, 450.0, 200.0))

    canteen_names = config.get('canteen_names', [])
    check("canteen_names 非空", len(canteen_names) > 0)
    print(f"    食堂名称: {canteen_names}")

    spawn_positions = config.get('spawn_positions', [])
    check("spawn_positions 包含教学楼坐标", len(spawn_positions) > 5)
    print(f"    学生生成点: {len(spawn_positions)} 个建筑坐标")

    engine = SimulationEngine(config)
    check("引擎初始化成功", engine.current_tick == 0)
    check("食堂数量正确", len(engine.canteens) == 2)
    check("学生数量正确", len(engine.students) == 10)

    print("\n--- 运行 30 个 tick ---")
    for i in range(30):
        engine.tick()
    check("运行后 current_tick=30", engine.current_tick == 30)

    stats = engine.get_statistics()
    check("有学生生成", stats['total_students_generated'] > 0)
    print(f"    生成学生: {stats['total_students_generated']}, "
          f"服务学生: {stats['total_students_served']}")

    # 验证食堂使用了 campus_bounds.json 坐标
    for canteen in engine.canteens:
        print(f"    食堂: {canteen.name}, 位置: {canteen.position}, 窗口数: {canteen.get_window_count()}")
        check(f"{canteen.name} 位置在边界内",
              -250 <= canteen.position[0] <= 450 and -400 <= canteen.position[1] <= 200)


# ============================================================
# 3. 完整仿真流程测试（可选）
# ============================================================
def test_full_simulation():
    print("\n" + "=" * 60)
    print("3. 完整仿真流程测试（main.py 集成）")
    print("=" * 60)

    from engine import SimulationEngine
    from config import BJTUConfig

    config_obj = BJTUConfig()
    config = config_obj.get_simulation_config()
    config['max_ticks'] = 50
    config['student_count'] = 20
    config['canteen_count'] = 3
    config['spawn_rate'] = 0.1

    engine = SimulationEngine(config)
    engine.run(verbose=False)

    stats = engine.get_statistics()
    print(f"  周期数: {engine.current_tick}")
    print(f"  总生成: {stats['total_students_generated']}")
    print(f"  总服务: {stats['total_students_served']}")
    print(f"  最大排队: {stats['max_queue_length']}")
    print(f"  最终活跃: {len(engine.active_students)}")

    check("仿真正常结束", engine.current_tick == 50)
    check("有统计数据", len(engine.tick_history) > 0)


# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("组长A 测试 - 核心引擎与系统集成")
    print("=" * 60)

    test_models()
    test_engine()

    if "--full" in sys.argv:
        test_full_simulation()

    print("\n" + "=" * 60)
    print(f"结果: {TESTS_PASSED} 通过, {TESTS_FAILED} 失败")
    print("=" * 60)

    if TESTS_FAILED > 0:
        sys.exit(1)
