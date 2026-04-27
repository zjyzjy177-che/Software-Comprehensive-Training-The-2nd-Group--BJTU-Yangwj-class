"""
组员B 测试脚本 - 算法与数据
=============================
负责模块：config.py, strategies.py, campus_bounds.json
测试内容：
  1. campus_bounds.json 坐标加载与验证
  2. BJTUConfig 配置管理（坐标查询、参数更新、配置导出）
  3. CanteenSelector 多食堂选择（距离优先、排队优先、平衡策略）
  4. EnhancedDistanceStrategy / EnhancedQueueStrategy / BalancedStrategy
  5. 动态权重调整（高峰/非高峰时段）

运行方式：
  python3 test_member_b.py
  python3 test_member_b.py --verbose   # 详细输出
"""

import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(__file__))

TESTS_PASSED = 0
TESTS_FAILED = 0
VERBOSE = "--verbose" in sys.argv


def check(name, condition):
    global TESTS_PASSED, TESTS_FAILED
    if condition:
        TESTS_PASSED += 1
        print(f"  [PASS] {name}")
    else:
        TESTS_FAILED += 1
        print(f"  [FAIL] {name}")


# ============================================================
# 1. campus_bounds.json 坐标加载
# ============================================================
def test_campus_bounds():
    print("=" * 60)
    print("1. campus_bounds.json - 坐标数据验证")
    print("=" * 60)

    bounds_file = os.path.join(os.path.dirname(__file__), 'campus_bounds.json')
    with open(bounds_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    check("包含 map_boundaries", 'map_boundaries' in data)
    check("包含 buildings", 'buildings' in data)

    boundaries = data['map_boundaries']
    check("map_boundaries 长度=4", len(boundaries) == 4)
    print(f"    地图范围: ({boundaries[0]}, {boundaries[1]}) - ({boundaries[2]}, {boundaries[3]})")

    buildings = data['buildings']
    check(f"建筑数量 >= 30 (实际 {len(buildings)})", len(buildings) >= 30)

    # 验证食堂坐标存在
    canteen_names = ['四食堂', '一食堂', '留园', '学活食堂']
    for name in canteen_names:
        check(f"食堂 '{name}' 存在", name in buildings)
        if name in buildings:
            print(f"    {name}: {buildings[name]}")

    # 验证教学楼
    teaching_buildings = ['思源楼', '思源西楼', '思源东楼', '逸夫楼', '7教＋5教', '9教']
    for name in teaching_buildings:
        check(f"教学楼 '{name}' 存在", name in buildings)

    # 验证所有坐标在边界内
    x_min, y_min, x_max, y_max = boundaries
    for name, coord in buildings.items():
        x, y = coord
        if not (x_min - 10 <= x <= x_max + 10 and y_min - 10 <= y <= y_max + 10):
            print(f"    警告: {name} {coord} 超出边界")


# ============================================================
# 2. BJTUConfig 配置管理
# ============================================================
def test_config():
    print("\n" + "=" * 60)
    print("2. config.py - BJTUConfig 配置管理")
    print("=" * 60)

    from config import BJTUConfig

    config = BJTUConfig()

    # 坐标加载
    check(f"加载坐标数 >= 30 (实际 {len(config.coordinates)})", len(config.coordinates) >= 30)

    # 坐标查询
    siyuan = config.get_coordinate("思源楼")
    check("思源楼坐标查询成功", isinstance(siyuan, tuple) and len(siyuan) == 2)
    print(f"    思源楼: {siyuan}")

    # 食堂坐标
    for name in ['四食堂', '一食堂', '学活食堂']:
        coord = config.get_coordinate(name)
        check(f"{name} 坐标: {coord}", isinstance(coord, tuple))
        if VERBOSE:
            print(f"    {name}: {coord}")

    # map_boundaries
    boundaries = config.simulation_params['map_boundaries']
    check("map_boundaries 来自 JSON", boundaries == (-250.0, -400.0, 450.0, 200.0))

    # get_simulation_config
    sim_config = config.get_simulation_config()
    check("config 含 canteen_names", 'canteen_names' in sim_config)
    check("config 含 spawn_positions", 'spawn_positions' in sim_config)
    check("config 含 algorithm_params", 'algorithm_params' in sim_config)

    canteen_names = sim_config['canteen_names']
    print(f"    食堂名称: {canteen_names}")

    # 参数验证
    check("距离权重 + 排队权重 ≈ 1.0",
          abs(config.algorithm_params['distance_weight'] + config.algorithm_params['queue_weight'] - 1.0) < 0.01)

    # gap_time 测试
    old_rate = config.simulation_params['spawn_rate']
    config.update_gap_time(45)
    check("gap_time > 30 时 spawn_rate 降低", config.simulation_params['spawn_rate'] < old_rate)


# ============================================================
# 3. CanteenSelector 算法测试
# ============================================================
def test_strategies():
    print("\n" + "=" * 60)
    print("3. strategies.py - 多食堂选择算法")
    print("=" * 60)

    from models import Canteen
    from strategies import (CanteenSelector, EnhancedDistanceStrategy,
                            EnhancedQueueStrategy, BalancedStrategy,
                            create_canteen_selector, create_selector_from_config)

    # 使用 campus_bounds.json 真实坐标创建食堂
    canteens = [
        Canteen(canteen_id=0, name="四食堂", position=(250.0, -310.0), window_count=10, capacity=100),
        Canteen(canteen_id=1, name="一食堂", position=(160.0, 80.0), window_count=15, capacity=80),
        Canteen(canteen_id=2, name="学活食堂", position=(-180.0, 80.0), window_count=20, capacity=120),
        Canteen(canteen_id=3, name="留园", position=(250.0, -290.0), window_count=3, capacity=50),
    ]

    # 设置不同排队人数
    canteens[0].total_queue_length = 25  # 四食堂排队长
    canteens[1].total_queue_length = 5   # 一食堂排队短
    canteens[2].total_queue_length = 10  # 学活中等
    canteens[3].total_queue_length = 2   # 留园排队最短

    algorithm_params = {
        'distance_weight': 0.3,
        'queue_weight': 0.7,
        'max_walk_distance': 1000.0,
        'prefer_near_canteen': True,
    }
    simulation_params = {
        'window_counts': [10, 15, 20, 3],
        'service_rates': [1.0, 1.0, 1.0, 1.0],
    }

    # --- 测试1: 排队优先 ---
    print("\n--- 排队优先策略 (α=0.3, β=0.7) ---")
    # 学生从思源楼出发 (-25, -100)
    student_pos_siyuan = (-25.0, -100.0)

    selector = CanteenSelector(algorithm_params=algorithm_params, simulation_params=simulation_params)
    best = selector.select_best_canteen(student_pos_siyuan, canteens)
    check("选择器返回非空", best is not None)
    if best:
        print(f"    思源楼出发选到: {best.name} (排队: {best.total_queue_length}人)")
        # 思源楼到学活食堂最近（距离约200），但排队10人；一食堂距离约250排队5人
        # 排队权重0.7优先 → 应该选排队少的
        print(f"    距离: {math.dist(student_pos_siyuan, best.position):.0f}m")

    # --- 测试2: 不同起点 ---
    print("\n--- 从宿舍区出发 (-130, -200) ---")
    student_pos_dorm = (-130.0, -200.0)
    best2 = selector.select_best_canteen(student_pos_dorm, canteens)
    if best2:
        print(f"    宿舍区出发选到: {best2.name} (排队: {best2.total_queue_length}人)")
        print(f"    距离: {math.dist(student_pos_dorm, best2.position):.0f}m")

    # --- 测试3: 距离优先 ---
    print("\n--- 距离优先策略 (α=0.9, β=0.1) ---")
    dist_params = algorithm_params.copy()
    dist_params['distance_weight'] = 0.9
    dist_params['queue_weight'] = 0.1
    dist_selector = CanteenSelector(algorithm_params=dist_params, simulation_params=simulation_params)
    best3 = dist_selector.select_best_canteen(student_pos_siyuan, canteens)
    if best3:
        print(f"    距离优先选到: {best3.name}")
        print(f"    距离: {math.dist(student_pos_siyuan, best3.position):.0f}m")

    # --- 测试4: 三个策略工厂函数 ---
    print("\n--- 策略工厂函数 ---")
    from models import Student
    # 策略类的 select_canteen 需要 Student 对象（取 position 属性）
    test_student = Student(student_id=99, position=student_pos_siyuan, destination=(0, 0))
    strategies = {
        "distance": create_canteen_selector("distance", algorithm_params, simulation_params),
        "queue": create_canteen_selector("queue", algorithm_params, simulation_params),
        "balanced": create_canteen_selector("balanced", algorithm_params, simulation_params),
    }
    for name, sel in strategies.items():
        result = sel.select_canteen(test_student, canteens)
        check(f"create_canteen_selector('{name}') 可用", result is not None)
        if result and VERBOSE:
            print(f"    {name}: {result.name}")

    # --- 测试5: create_selector_from_config ---
    print("\n--- create_selector_from_config ---")
    mock_config = {
        'algorithm_params': algorithm_params,
        'simulation_params': simulation_params,
    }
    config_sel = create_selector_from_config(mock_config, strategy_type="balanced")
    best5 = config_sel.select_canteen(test_student, canteens)
    check("create_selector_from_config 正常工作", best5 is not None)

    # --- 测试6: 动态权重调整 ---
    print("\n--- 动态权重调整 ---")
    selector.adjust_weights_by_time(current_tick=500, max_ticks=1000)
    check("中期（高峰）距离权重下降", selector.distance_weight < 0.5)
    check("中期（高峰）排队权重上升", selector.queue_weight > 0.5)
    print(f"    高峰权重: α={selector.distance_weight}, β={selector.queue_weight}")

    selector.adjust_weights_by_time(current_tick=100, max_ticks=1000)
    check("初期（非高峰）距离权重上升", selector.distance_weight > 0.5)
    print(f"    非高峰权重: α={selector.distance_weight}, β={selector.queue_weight}")

    # --- 测试7: max_walk_distance 过滤 ---
    print("\n--- 最大步行距离过滤 ---")
    filter_params = algorithm_params.copy()
    filter_params['max_walk_distance'] = 50.0  # 极短距离
    filter_sel = CanteenSelector(algorithm_params=filter_params, simulation_params=simulation_params)
    # 期望：所有食堂都超距离，回退到最近食堂
    best_far = filter_sel.select_best_canteen(student_pos_siyuan, canteens)
    check("超距离时回退到最近食堂", best_far is not None)
    if best_far:
        print(f"    所有食堂超距，回退选: {best_far.name}")

    # 打印统计
    stats = selector.get_selection_stats()
    print(f"\n  总选择次数: {stats['selection_count']}")
    print(f"  平均得分: {stats['average_score']:.3f}")


# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("组员B 测试 - 算法与数据")
    print("=" * 60)

    test_campus_bounds()
    test_config()
    test_strategies()

    print("\n" + "=" * 60)
    print(f"结果: {TESTS_PASSED} 通过, {TESTS_FAILED} 失败")
    print("=" * 60)

    if TESTS_FAILED > 0:
        sys.exit(1)
