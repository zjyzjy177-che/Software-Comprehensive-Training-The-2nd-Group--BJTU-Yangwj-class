"""
组员C 测试脚本 - UI与可视化
=============================
负责模块：visualizer.py, main.py --visualize（集成）
测试内容：
  1. CanteenVisualizer 初始化（中文字体、图形窗口、事件绑定）
  2. 静态帧渲染（draw_frame）
  3. 信息面板更新
  4. 饼图和统计曲线
  5. 保存帧为 PNG
  6. [可选] 完整动画测试（需要 GUI 环境）

运行方式：
  python3 test_member_c.py              # 无 GUI 测试（生成 test_output.png）
  python3 test_member_c.py --animate    # 动画测试（需要显示器）
  python3 test_member_c.py --full       # 完整 GUI 集成测试
"""

import sys
import os
import random
import numpy as np

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
# 1. 可视化器初始化测试（使用非交互后端）
# ============================================================
def test_visualizer_init():
    print("=" * 60)
    print("1. visualizer.py - 可视化器初始化")
    print("=" * 60)

    # 使用非交互后端以支持无 GUI 环境
    import matplotlib
    matplotlib.use('Agg')

    from visualizer import CanteenVisualizer, create_visualizer

    # 使用 campus_bounds.json 的 map_boundaries
    map_bounds = (-250, -400, 450, 200)

    viz = CanteenVisualizer(map_boundaries=map_bounds, title="测试可视化")
    check("fig 已创建", viz.fig is not None)
    check("ax_map 已创建", viz.ax_map is not None)
    check("ax_stats 已创建", viz.ax_stats is not None)
    check("ax_pie 已创建", viz.ax_pie is not None)
    check("xlim 正确", viz.ax_map.get_xlim()[0] < -250)
    check("ylim 正确", viz.ax_map.get_ylim()[0] < -400)
    check("暂停状态初始为 False", viz.is_paused is False)
    check("animation_speed=200", viz.animation_speed == 200)

    print(f"    地图范围: {map_bounds}")
    print(f"    颜色配置: {list(viz.colors.keys())}")

    # 测试 create_visualizer 工厂函数
    viz2 = create_visualizer(map_boundaries=map_bounds)
    check("create_visualizer 正常", viz2 is not None)

    return viz


# ============================================================
# 2. 静态帧渲染测试
# ============================================================
def test_frame_rendering(viz):
    print("\n" + "=" * 60)
    print("2. static frame rendering - 静态帧渲染")
    print("=" * 60)

    from models import Student, Canteen, StudentState

    # 使用 campus_bounds.json 中的真实坐标
    canteens = [
        Canteen(canteen_id=1, name="四食堂", position=(250.0, -310.0), window_count=10, capacity=100),
        Canteen(canteen_id=2, name="一食堂", position=(160.0, 80.0), window_count=15, capacity=80),
        Canteen(canteen_id=3, name="学活食堂", position=(-180.0, 80.0), window_count=20, capacity=120),
    ]
    canteens[0].total_queue_length = 20
    canteens[1].total_queue_length = 8
    canteens[2].total_queue_length = 12

    # 在校园范围内生成测试学生
    random.seed(42)
    np.random.seed(42)
    students = []
    for i in range(60):
        s = Student(
            student_id=i,
            position=(random.uniform(-200, 400), random.uniform(-350, 150)),
            destination=random.choice(canteens).position,
            speed=random.uniform(1, 5),
            eating_time=random.randint(5, 15),
        )
        # 分配状态
        states = [StudentState.WALKING, StudentState.QUEUING, StudentState.EATING, StudentState.LEAVING]
        probs = [0.5, 0.25, 0.15, 0.10]
        s.state = np.random.choice(states, p=probs)
        students.append(s)

    # 渲染帧
    print(f"    学生数: {len(students)}, 食堂数: {len(canteens)}")
    viz.draw_frame(tick=42, students=students, canteens=canteens)

    # 保存帧
    output_file = os.path.join(os.path.dirname(__file__), "test_output_c.png")
    viz.save_frame(output_file)
    check(f"保存帧到 {output_file}", os.path.exists(output_file))

    if os.path.exists(output_file):
        size_kb = os.path.getsize(output_file) / 1024
        check(f"文件 > 1KB (实际 {size_kb:.1f}KB)", size_kb > 1)
        print(f"    文件大小: {size_kb:.1f} KB")
        print(f"    → 请打开 '{output_file}' 验证可视化效果")

    # 测试信息面板
    print("\n    信息面板内容预览:")
    info_text = viz.info_text.get_text()
    for line in info_text.split('\n')[:5]:
        print(f"    | {line}")

    # 测试多帧（验证不会崩溃）
    print("\n--- 多帧连续渲染 ---")
    for tick in range(1, 6):
        # 移动学生位置模拟
        for s in students:
            s.position = (s.position[0] + random.uniform(-1, 1),
                         s.position[1] + random.uniform(-1, 1))
        try:
            viz.draw_frame(tick=tick, students=students, canteens=canteens)
        except Exception as e:
            check(f"tick {tick} 渲染无异常", False)
            print(f"      错误: {e}")
            break
    else:
        check("连续 5 帧渲染无异常", True)

    viz.close()
    return True


# ============================================================
# 3. main.py 可视化集成测试（无 GUI）
# ============================================================
def test_main_integration():
    print("\n" + "=" * 60)
    print("3. main.py - 可视化接口集成")
    print("=" * 60)

    from main import initialize_visualization, update_visualization
    from config import BJTUConfig

    config_obj = BJTUConfig()
    config = config_obj.get_simulation_config()

    check("enable_visualization 初始为 False",
          config.get('enable_visualization', True) is False)

    # 测试 initialize_visualization
    import matplotlib
    matplotlib.use('Agg')
    viz = initialize_visualization(config)
    check("initialize_visualization 返回非空", viz is not None)

    if viz:
        from models import Student, Canteen
        canteens = [
            Canteen(canteen_id=0, name="四食堂", position=(250.0, -310.0), window_count=10, capacity=100),
        ]
        students = [
            Student(student_id=0, position=(0.0, 0.0), destination=(250.0, -310.0)),
        ]
        update_visualization(viz, tick=1, students=students, canteens=canteens)
        check("update_visualization 正常执行", True)
        viz.close()

    return True


# ============================================================
# 4. 完整动画测试（需要 GUI）
# ============================================================
def test_full_animation():
    print("\n" + "=" * 60)
    print("4. 完整动画测试（GUI 模式）")
    print("=" * 60)
    print("  注意: 此测试会弹出 Matplotlib 窗口")
    print("  控制: 空格暂停/继续, ↑↓调速, R重置视图")
    print("  关闭窗口以继续...")
    print()

    from engine import SimulationEngine
    from config import BJTUConfig
    from main import initialize_visualization
    import time

    config_obj = BJTUConfig()
    config = config_obj.get_simulation_config()
    config['max_ticks'] = 200
    config['student_count'] = 30
    config['canteen_count'] = 3
    config['spawn_rate'] = 0.15

    engine = SimulationEngine(config)

    viz = initialize_visualization(config)
    if viz is None:
        print("  可视化初始化失败（可能是字体/后端问题）")
        return False

    engine.is_running = True
    engine.start_time = time.time()

    def update_frame():
        if engine.current_tick < engine.max_ticks:
            engine.tick()
        elif engine.is_running:
            engine.end_time = time.time()
            engine.is_running = False
        return engine.current_tick, engine.active_students, engine.canteens

    viz.start_animation(update_frame, interval=200)
    viz.show()
    engine.print_summary()

    check("动画完整运行", engine.current_tick == 200)
    return True


# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("组员C 测试 - UI与可视化")
    print("=" * 60)

    # 无 GUI 测试（必需）
    viz = test_visualizer_init()
    test_frame_rendering(viz)
    test_main_integration()

    # GUI 测试（可选）
    args = sys.argv[1:]
    if "--animate" in args or "--full" in args:
        print("\n" + "=" * 60)
        print("⚠️  即将启动 GUI 动画测试窗口")
        print("   请关闭 Matplotlib 窗口以完成测试")
        print("=" * 60)
        test_full_animation()

    print("\n" + "=" * 60)
    print(f"结果: {TESTS_PASSED} 通过, {TESTS_FAILED} 失败")
    print("=" * 60)

    if TESTS_FAILED > 0:
        sys.exit(1)
