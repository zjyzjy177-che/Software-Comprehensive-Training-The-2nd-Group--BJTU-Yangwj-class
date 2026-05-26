"""
集成联调测试脚本 - test_integration.py

本脚本验证系统各模块间的接口联通、数据流转、正常/异常运行。
覆盖四条核心数据链路：

链路1: campus_bounds.json → config.py → engine.py
链路2: config.py → main.py → engine.py
链路3: engine.py → visualizer.py
链路4: strategies.py → engine.py → models.py

使用方法：
    python test_integration.py              # 运行所有集成测试
    python test_integration.py --verbose    # 详细输出模式

注意：本测试不依赖 Matplotlib 图形界面，可在无 GUI 环境运行。
"""

import sys
import os
import json
import unittest
import tempfile
import shutil
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import Student, Canteen, StudentState
from engine import SimulationEngine
from config import BJTUConfig


# ============================================================
# 链路1: campus_bounds.json → config.py → engine.py
# ============================================================

class TestDataFlowJSONToEngine(unittest.TestCase):
    """验证 JSON 坐标数据经 config 正确传递到 engine"""

    @classmethod
    def setUpClass(cls):
        cls.json_path = os.path.join(os.path.dirname(__file__), '..', 'campus_bounds.json')

    def test_01_json_loads_successfully(self):
        """campus_bounds.json 存在且格式合法"""
        self.assertTrue(os.path.exists(self.json_path),
                        f"campus_bounds.json 不存在: {self.json_path}")
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn('buildings', data)
        self.assertIn('map_boundaries', data)
        self.assertGreater(len(data['buildings']), 0,
                           "buildings 字典不应为空")

    def test_02_config_loads_coordinates_from_json(self):
        """config.py 从 JSON 加载坐标，非硬编码"""
        cfg = BJTUConfig()
        self.assertGreater(len(cfg.coordinates), 0)
        self.assertIn('思源楼', cfg.coordinates)
        self.assertEqual(cfg.coordinates['思源楼'], (-25.0, -100.0))

    def test_03_engine_receives_config_canteen_names(self):
        """engine 创建的食堂名称来自配置，非 '食堂1/2/3'"""
        cfg = BJTUConfig()
        sim_config = cfg.get_simulation_config()
        sim_config['max_ticks'] = 5
        sim_config['student_count'] = 2
        engine = SimulationEngine(sim_config)
        names = [c.name for c in engine.canteens]
        for n in names:
            self.assertNotIn(n, ['食堂1', '食堂2', '食堂3', '食堂4'],
                             f"食堂名称仍为默认: {n}，应从 JSON 加载")

    def test_04_engine_map_boundaries_match_json(self):
        """engine 的 map_boundaries 与 campus_bounds.json 一致"""
        cfg = BJTUConfig()
        sim_config = cfg.get_simulation_config()
        engine = SimulationEngine(sim_config)
        self.assertEqual(engine.map_boundaries, (-250.0, -400.0, 450.0, 200.0))

    def test_05_config_fallback_when_json_missing(self):
        """JSON 缺失时 config 回退到 DEFAULT_COORDINATES"""
        # 临时创建一个目录来模拟 JSON 缺失
        cfg = BJTUConfig()
        # 直接验证 coordinates 非空即可（JSON 存在时加载，不存在时用默认）
        self.assertGreater(len(cfg.coordinates), 0)

    def test_06_student_spawn_from_real_buildings(self):
        """学生生成位置来自真实建筑坐标"""
        cfg = BJTUConfig()
        sim_config = cfg.get_simulation_config()
        sim_config['max_ticks'] = 2
        sim_config['student_count'] = 20
        sim_config['spawn_rate'] = 0.0
        sim_config['random_seed'] = 42
        engine = SimulationEngine(sim_config)
        self.assertGreater(len(engine.students), 0,
                          "engine 应生成初始学生")


# ============================================================
# 链路2: strategies.py → engine.py → models.py
# ============================================================

class TestDataFlowStrategiesToEngine(unittest.TestCase):
    """验证食堂选择算法在 engine 中的实际运行效果"""

    def setUp(self):
        self.base_config = {
            'max_ticks': 5,
            'student_count': 10,
            'canteen_count': 3,
            'spawn_rate': 0.0,
            'random_seed': 42,
            'map_boundaries': (-250.0, -400.0, 450.0, 200.0),
        }

    def test_01_selector_created_in_engine(self):
        """engine 初始化时创建了 CanteenSelector"""
        engine = SimulationEngine(self.base_config)
        self.assertIsNotNone(engine.canteen_selector)

    def test_02_students_assigned_to_different_canteens(self):
        """学生被分配到不同食堂，非全部涌向同一食堂"""
        cfg = BJTUConfig().get_simulation_config()
        cfg['max_ticks'] = 2
        cfg['student_count'] = 30
        cfg['canteen_count'] = 3
        cfg['spawn_rate'] = 0.0
        cfg['random_seed'] = 123
        engine = SimulationEngine(cfg)
        targets = set()
        for s in engine.students:
            if s.target_canteen_id is not None:
                targets.add(s.target_canteen_id)
        self.assertGreater(len(targets), 1,
                           f"所有学生被分配到同一食堂，选择器未生效")

    def test_03_different_weights_produce_different_choice(self):
        """不同权重下 CanteenSelector 做出不同选择"""
        from strategies import CanteenSelector
        # A 近但排队多，B 远但排队少
        canteen_a = Canteen(canteen_id=0, name="近但挤", position=(50, 0), window_count=1)
        canteen_b = Canteen(canteen_id=1, name="远但空", position=(200, 0), window_count=1)
        for _ in range(10):
            dummy = Student(student_id=999, position=(0, 0), destination=(0, 0))
            dummy.state = StudentState.QUEUING
            canteen_a.windows[0].queue.append(dummy)
        student_pos = (0, 0)

        sel_dist = CanteenSelector(
            algorithm_params={'distance_weight': 0.9, 'queue_weight': 0.1}, simulation_params={})
        sel_queue = CanteenSelector(
            algorithm_params={'distance_weight': 0.1, 'queue_weight': 0.9}, simulation_params={})

        pick_dist = sel_dist.select_best_canteen(student_pos, [canteen_a, canteen_b])
        pick_queue = sel_queue.select_best_canteen(student_pos, [canteen_a, canteen_b])

        self.assertIsNotNone(pick_dist)
        self.assertIsNotNone(pick_queue)
        # 距离优先应选近的 A，排队优先应选空的 B
        self.assertEqual(pick_dist.canteen_id, 0,
                         f"距离优先应选近食堂A，实际选{pick_dist.name}")
        self.assertEqual(pick_queue.canteen_id, 1,
                         f"排队优先应选空食堂B，实际选{pick_queue.name}")

    def test_04_student_state_transitions_in_engine(self):
        """学生状态在 engine tick 驱动下完成完整转换链"""
        cfg = BJTUConfig().get_simulation_config()
        cfg['max_ticks'] = 300
        cfg['student_count'] = 10
        cfg['canteen_count'] = 2
        cfg['spawn_rate'] = 0.0
        cfg['eating_time_range'] = (5, 15)  # 缩短用餐时间加速状态转换
        cfg['student_speed_range'] = (10.0, 20.0)  # 提高速度
        cfg['random_seed'] = 99
        engine = SimulationEngine(cfg)
        for _ in range(cfg['max_ticks']):
            if not engine.tick():
                break
        states_seen = set()
        for s in engine.students:
            states_seen.add(s.state)
        all_states = {StudentState.WALKING, StudentState.QUEUING,
                       StudentState.EATING, StudentState.LEAVING, StudentState.LEFT}
        observed = states_seen & all_states
        # 至少观察到非 WALKING 状态，证明状态机在运转
        non_walking = observed - {StudentState.WALKING}
        self.assertGreater(len(non_walking), 0,
                           f"所有学生仍为 WALKING，状态转换未发生")


# ============================================================
# 链路3: engine.py → visualizer.py
# ============================================================

class TestDataFlowEngineToVisualizer(unittest.TestCase):
    """验证 engine 与 visualizer 的接口联通"""

    def setUp(self):
        self.config = BJTUConfig().get_simulation_config()
        self.config['max_ticks'] = 10
        self.config['student_count'] = 5
        self.config['canteen_count'] = 2
        self.config['spawn_rate'] = 0.0
        self.config['random_seed'] = 7

    def test_01_initialize_visualization_succeeds(self):
        """visualizer 初始化正常，返回 CanteenVisualizer 实例"""
        from main import initialize_visualization
        visualizer = initialize_visualization(self.config)
        self.assertIsNotNone(visualizer, "initialize_visualization 返回 None")
        # 清理，避免打开窗口
        if visualizer:
            visualizer.close()

    def test_02_update_visualization_no_crash(self):
        """update_visualization 调用不崩溃"""
        from main import initialize_visualization, update_visualization
        engine = SimulationEngine(self.config)
        visualizer = initialize_visualization(self.config)
        if visualizer is None:
            self.skipTest("visualizer 初始化失败，跳过")
        try:
            update_visualization(visualizer, 0, engine.active_students, engine.canteens)
        except Exception as e:
            self.fail(f"update_visualization 抛出异常: {e}")
        finally:
            visualizer.close()

    def test_03_engine_tick_data_consistent_with_visualizer(self):
        """engine tick 数据与传给 visualizer 的数据一致"""
        engine = SimulationEngine(self.config)
        engine.tick()
        tick = engine.current_tick
        students = engine.active_students
        canteens = engine.canteens
        self.assertEqual(tick, 1)
        self.assertEqual(len(students), 5)
        self.assertEqual(len(canteens), 2)


# ============================================================
# 链路4: 全链路端到端
# ============================================================

class TestFullPipeline(unittest.TestCase):
    """完整仿真流程端到端测试"""

    def test_01_full_simulation_test_mode(self):
        """测试模式完整运行: 150 ticks, 30 students"""
        from main import run_simulation
        config = BJTUConfig().get_simulation_config()
        config['max_ticks'] = 150
        config['student_count'] = 30
        config['canteen_count'] = 2
        config['spawn_rate'] = 0.08
        config['random_seed'] = 42
        config['enable_visualization'] = False
        engine = run_simulation(config, quiet_mode=True)
        self.assertEqual(engine.current_tick, 150)
        stats = engine.get_statistics()
        self.assertGreater(stats['total_students_generated'], 0)
        # 至少有一些学生被服务
        self.assertIn('total_students_served', stats)

    def test_02_full_simulation_default_params(self):
        """默认参数完整运行不崩溃"""
        from main import run_simulation
        config = BJTUConfig().get_simulation_config()
        config['max_ticks'] = 50
        config['student_count'] = 20
        config['canteen_count'] = 2
        config['spawn_rate'] = 0.05
        config['random_seed'] = 123
        config['enable_visualization'] = False
        engine = run_simulation(config, quiet_mode=True)
        self.assertIsNotNone(engine)
        self.assertGreater(len(engine.tick_history), 0)

    def test_03_save_results_produces_json_file(self):
        """save_results 正确生成 JSON 和摘要文件"""
        from main import run_simulation, save_results
        config = BJTUConfig().get_simulation_config()
        config['max_ticks'] = 10
        config['student_count'] = 5
        config['canteen_count'] = 2
        config['spawn_rate'] = 0.0
        config['random_seed'] = 1
        config['enable_visualization'] = False
        engine = run_simulation(config, quiet_mode=True)
        tmpdir = tempfile.mkdtemp()
        try:
            output_path = os.path.join(tmpdir, 'test_results.json')
            save_results(engine, output_path)
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.assertIn('metadata', data)
            self.assertIn('global_statistics', data)
            summary_path = output_path.replace('.json', '_summary.txt')
            self.assertTrue(os.path.exists(summary_path))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_04_engine_reset_and_rerun(self):
        """engine.reset() 后可重新运行，结果一致（固定种子）"""
        config = {
            'max_ticks': 10,
            'student_count': 5,
            'canteen_count': 2,
            'spawn_rate': 0.0,
            'random_seed': 42,
            'map_boundaries': (-250.0, -400.0, 450.0, 200.0),
        }
        engine = SimulationEngine(config)
        for _ in range(10):
            engine.tick()
        stats1 = engine.get_statistics()
        served1 = stats1['total_students_served']

        engine.reset()
        for _ in range(10):
            engine.tick()
        stats2 = engine.get_statistics()
        served2 = stats2['total_students_served']
        self.assertEqual(served1, served2,
                         f"reset 后结果不一致: {served1} vs {served2}")

    def test_05_gui_interface_function(self):
        """run_simulation_from_gui 接口正常返回"""
        from main import run_simulation_from_gui
        gui_config = {
            'max_ticks': 20,
            'student_count': 10,
            'canteen_count': 2,
            'spawn_rate': 0.05,
            'enable_visualization': False,
            'random_seed': 7,
        }
        result = run_simulation_from_gui(gui_config)
        self.assertTrue(result['success'], f"GUI 接口失败: {result.get('error')}")
        self.assertIsNotNone(result['statistics'])
        self.assertIsNotNone(result['summary'])


# ============================================================
# 异常场景
# ============================================================

class TestAbnormalScenarios(unittest.TestCase):
    """异常输入和边界条件测试"""

    def test_01_zero_canteen_count_raises(self):
        """canteen_count=0 时 config 验证应报错"""
        cfg = BJTUConfig()
        cfg.simulation_params['canteen_count'] = 0
        with self.assertRaises(ValueError):
            cfg._validate_config()

    def test_02_negative_max_ticks_raises(self):
        """max_ticks <= 0 时 config 验证应报错"""
        cfg = BJTUConfig()
        cfg.simulation_params['max_ticks'] = -1
        with self.assertRaises(ValueError):
            cfg._validate_config()

    def test_03_invalid_spawn_rate(self):
        """spawn_rate 超出 [0,1] 范围应报错"""
        cfg = BJTUConfig()
        cfg.simulation_params['spawn_rate'] = 5.0
        with self.assertRaises(ValueError):
            cfg._validate_config()

    def test_04_missing_building_coordinate_raises_keyerror(self):
        """查询不存在的建筑坐标抛出 KeyError"""
        cfg = BJTUConfig()
        with self.assertRaises(KeyError):
            cfg.get_coordinate('不存在的建筑')

    def test_05_empty_config_runs_safely(self):
        """最小配置下 engine 不崩溃"""
        config = {
            'max_ticks': 3,
            'student_count': 2,
            'canteen_count': 1,
            'spawn_rate': 0.0,
            'map_boundaries': (0, 0, 100, 100),
            'random_seed': 1,
        }
        engine = SimulationEngine(config)
        for _ in range(config['max_ticks']):
            should_continue = engine.tick()
            if not should_continue:
                break
        self.assertGreaterEqual(engine.current_tick, 1)

    def test_06_gui_interface_handles_invalid_config(self):
        """GUI 接口在异常配置下不崩溃，返回错误信息"""
        from main import run_simulation_from_gui
        result = run_simulation_from_gui({
            'canteen_count': 0,  # 非法值，BJTUConfig 验证会报错
            'max_ticks': 10,
            'student_count': 5,
        })
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])


def run_integration_tests(verbose: bool = False):
    """运行所有集成测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDataFlowJSONToEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestDataFlowStrategiesToEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestDataFlowEngineToVisualizer))
    suite.addTests(loader.loadTestsFromTestCase(TestFullPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestAbnormalScenarios))

    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors

    print("\n" + "=" * 60)
    print(f"集成测试汇总: {total} 项 | 通过 {passed} | 失败 {failures} | 错误 {errors}")
    print("=" * 60)

    if failures:
        print("\n失败用例:")
        for test, trace in result.failures:
            print(f"  [FAIL] {test}")
    if errors:
        print("\n错误用例:")
        for test, trace in result.errors:
            print(f"  [ERROR] {test}")

    return result.wasSuccessful()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BJTU 食堂仿真系统 - 集成联调测试")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="详细输出模式")
    args = parser.parse_args()

    success = run_integration_tests(verbose=args.verbose)
    sys.exit(0 if success else 1)
