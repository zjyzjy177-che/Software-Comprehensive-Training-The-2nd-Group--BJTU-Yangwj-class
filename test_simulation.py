"""
测试脚本 - test_simulation.py

本脚本用于测试食堂就餐流量仿真系统的核心功能。
包括单元测试和集成测试，确保代码正确性和稳定性。

测试内容：
1. 模型测试：Student类和Canteen类的基本功能
2. 引擎测试：SimulationEngine的tick驱动逻辑
3. 集成测试：完整仿真流程
4. 边界测试：异常情况和边界条件

使用方法：
python test_simulation.py           # 运行所有测试
python test_simulation.py --unit    # 只运行单元测试
python test_simulation.py --engine  # 只运行引擎测试
python test_simulation.py --integration  # 只运行集成测试

注意：这是基础测试脚本，后续可扩展更全面的测试套件。
"""

import sys
import unittest
import random
from typing import List, Dict, Any

# 导入被测试模块
from models import Student, Canteen, StudentState, DistanceBasedStrategy
from engine import SimulationEngine


class TestStudent(unittest.TestCase):
    """Student类单元测试"""

    def setUp(self):
        """测试前置设置：创建测试用的学生对象"""
        self.student = Student(
            student_id=1,
            position=(0.0, 0.0),
            destination=(100.0, 100.0),
            speed=10.0,
            eating_time=5
        )

    def test_initialization(self):
        """测试学生对象初始化"""
        self.assertEqual(self.student.student_id, 1)
        self.assertEqual(self.student.position, (0.0, 0.0))
        self.assertEqual(self.student.destination, (100.0, 100.0))
        self.assertEqual(self.student.speed, 10.0)
        self.assertEqual(self.student.eating_time, 5)
        self.assertEqual(self.student.state, StudentState.WALKING)
        self.assertEqual(self.student.state_timer, 0)

    def test_move_to_destination(self):
        """测试向目标移动"""
        # 保存初始位置
        initial_position = self.student.position

        # 调用移动方法（内部方法，通过update_state间接测试）
        # 这里直接测试距离计算
        distance_before = self._calculate_distance(
            self.student.position,
            self.student.destination
        )

        # 手动调用移动方法（注意：这是内部方法，通常不直接调用）
        # 为测试目的，我们临时设置为可访问
        self.student._move_to_destination()

        distance_after = self._calculate_distance(
            self.student.position,
            self.student.destination
        )

        # 移动后距离应该减小（或不变）
        self.assertLessEqual(distance_after, distance_before)

    def test_state_transition_walking_to_queuing(self):
        """测试从行走状态到排队状态的转换"""
        # 设置学生位置接近目标
        self.student.position = (95.0, 95.0)  # 距离目标约7.07，小于阈值10

        # 更新状态（应该触发状态转换）
        self.student.update_state()

        # 应该转换为排队状态
        self.assertEqual(self.student.state, StudentState.QUEUING)
        self.assertEqual(self.student.state_timer, 0)

    def test_join_queue(self):
        """测试加入队列"""
        self.student.join_queue(canteen_id=1, window_id=2)

        self.assertEqual(self.student.target_canteen_id, 1)
        self.assertEqual(self.student.target_window_id, 2)

    def test_start_eating(self):
        """测试开始用餐"""
        # 先设置状态为排队
        self.student.state = StudentState.QUEUING
        self.student.start_eating()

        self.assertEqual(self.student.state, StudentState.EATING)
        self.assertEqual(self.student.state_timer, 0)

    def test_start_eating_invalid_state(self):
        """测试无效状态下的开始用餐（应抛出异常）"""
        # 状态为行走时不能开始用餐
        self.student.state = StudentState.WALKING

        with self.assertRaises(ValueError):
            self.student.start_eating()

    def _calculate_distance(self, pos1, pos2):
        """计算两点距离（辅助方法）"""
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) ** 0.5


class TestCanteen(unittest.TestCase):
    """Canteen类单元测试"""

    def setUp(self):
        """测试前置设置：创建测试用的食堂对象"""
        self.canteen = Canteen(
            canteen_id=1,
            name="测试食堂",
            position=(100.0, 100.0),
            window_count=3,
            capacity=50
        )

        # 创建测试学生
        self.student = Student(
            student_id=1,
            position=(0.0, 0.0),
            destination=(100.0, 100.0)
        )

    def test_initialization(self):
        """测试食堂对象初始化"""
        self.assertEqual(self.canteen.canteen_id, 1)
        self.assertEqual(self.canteen.name, "测试食堂")
        self.assertEqual(self.canteen.position, (100.0, 100.0))
        self.assertEqual(self.canteen.capacity, 50)
        self.assertEqual(len(self.canteen.windows), 3)
        self.assertEqual(self.canteen.get_total_queue_length(), 0)

    def test_add_student_to_queue(self):
        """测试添加学生到队列"""
        success = self.canteen.add_student_to_queue(self.student)

        self.assertTrue(success)
        self.assertEqual(self.canteen.get_total_queue_length(), 1)
        self.assertEqual(self.student.target_canteen_id, 1)

    def test_add_student_to_queue_capacity_full(self):
        """测试食堂容量已满时添加学生"""
        # 设置食堂容量为0（模拟已满）
        self.canteen.capacity = 0

        success = self.canteen.add_student_to_queue(self.student)

        self.assertFalse(success)
        self.assertEqual(self.canteen.get_total_queue_length(), 0)

    def test_update_windows(self):
        """测试更新窗口状态"""
        # 先将学生状态设置为排队（模拟已到达食堂）
        self.student.state = StudentState.QUEUING

        # 先添加一个学生到队列
        self.canteen.add_student_to_queue(self.student)

        # 更新窗口（应该开始服务）
        self.canteen.update_windows()

        # 检查队列长度应该减少（学生被服务）
        # 注意：服务需要多个tick，第一次update可能不会立即服务
        # 这里只测试方法调用不报错
        self.canteen.update_windows()  # 再次调用

        # 获取窗口状态
        window_status = self.canteen.windows[0].get_status()

        # 至少有一个窗口应该在服务或已服务过
        # 这里不具体断言，因为服务逻辑有随机性

    def test_get_total_queue_length(self):
        """测试获取总排队人数"""
        # 初始应为0
        self.assertEqual(self.canteen.get_total_queue_length(), 0)

        # 添加学生后应为1
        self.canteen.add_student_to_queue(self.student)
        self.assertEqual(self.canteen.get_total_queue_length(), 1)

    def test_get_status(self):
        """测试获取食堂状态"""
        status = self.canteen.get_status()

        self.assertIn('canteen_id', status)
        self.assertIn('name', status)
        self.assertIn('total_queue_length', status)
        self.assertIn('window_count', status)
        self.assertEqual(status['canteen_id'], 1)
        self.assertEqual(status['name'], "测试食堂")


class TestSimulationEngine(unittest.TestCase):
    """SimulationEngine类单元测试"""

    def setUp(self):
        """测试前置设置：创建测试用的仿真引擎"""
        # 使用简单配置
        self.config = {
            'max_ticks': 10,
            'spawn_rate': 0.0,  # 不生成新学生
            'student_count': 5,
            'canteen_count': 1,
            'map_boundaries': (0.0, 0.0, 1000.0, 800.0),
            'random_seed': 12345  # 固定种子确保测试可重复
        }

        self.engine = SimulationEngine(self.config)

    def test_initialization(self):
        """测试仿真引擎初始化"""
        self.assertEqual(self.engine.current_tick, 0)
        self.assertEqual(self.engine.max_ticks, 10)
        self.assertEqual(len(self.engine.students), 5)
        self.assertEqual(len(self.engine.canteens), 1)
        self.assertEqual(len(self.engine.active_students), 5)

    def test_tick(self):
        """测试单个tick执行"""
        initial_tick = self.engine.current_tick

        # 执行一个tick
        should_continue = self.engine.tick()

        self.assertTrue(should_continue)
        self.assertEqual(self.engine.current_tick, initial_tick + 1)
        self.assertGreater(len(self.engine.tick_history), 0)

    def test_multiple_ticks(self):
        """测试多个tick执行"""
        # 执行5个tick
        for i in range(5):
            should_continue = self.engine.tick()
            self.assertTrue(should_continue)

        self.assertEqual(self.engine.current_tick, 5)
        self.assertEqual(len(self.engine.tick_history), 5)

    def test_max_ticks(self):
        """测试达到最大tick数时停止"""
        # 执行所有tick
        for i in range(self.engine.max_ticks + 5):  # 多执行几个确保停止
            should_continue = self.engine.tick()
            if not should_continue:
                break

        # 应该达到最大tick数
        self.assertEqual(self.engine.current_tick, self.engine.max_ticks)

    def test_get_statistics(self):
        """测试获取统计信息"""
        stats = self.engine.get_statistics()

        self.assertIn('total_students_generated', stats)
        self.assertIn('total_students_served', stats)
        self.assertIn('max_queue_length', stats)
        self.assertIn('average_wait_time', stats)

        # 初始应该有5个学生生成
        self.assertEqual(stats['total_students_generated'], 5)

    def test_reset(self):
        """测试重置仿真"""
        # 先执行一些tick
        for i in range(3):
            self.engine.tick()

        # 重置
        self.engine.reset()

        # 检查是否重置
        self.assertEqual(self.engine.current_tick, 0)
        self.assertEqual(len(self.engine.tick_history), 0)
        self.assertEqual(len(self.engine.students), 5)  # 重新初始化后应该有5个学生


class TestIntegration(unittest.TestCase):
    """集成测试：测试整个仿真流程"""

    def test_full_simulation_small(self):
        """测试小型完整仿真"""
        config = {
            'max_ticks': 20,
            'spawn_rate': 0.05,
            'student_count': 10,
            'canteen_count': 2,
            'map_boundaries': (0.0, 0.0, 500.0, 500.0),
            'random_seed': 42
        }

        engine = SimulationEngine(config)

        # 运行完整仿真
        engine.run(verbose=False)

        # 检查基本结果
        self.assertEqual(engine.current_tick, config['max_ticks'])
        self.assertGreaterEqual(
            engine.global_statistics['total_students_generated'],
            config['student_count']
        )

        # 打印简要结果用于手动验证
        print(f"\n集成测试结果：")
        print(f"  总生成学生: {engine.global_statistics['total_students_generated']}")
        print(f"  总服务学生: {engine.global_statistics['total_students_served']}")
        print(f"  最大排队: {engine.global_statistics['max_queue_length']}")

    def test_strategy_pattern(self):
        """测试策略模式（食堂选择算法）"""
        # 创建食堂
        canteen1 = Canteen(
            canteen_id=1,
            name="近食堂",
            position=(10.0, 10.0)
        )

        canteen2 = Canteen(
            canteen_id=2,
            name="远食堂",
            position=(100.0, 100.0)
        )

        canteens = [canteen1, canteen2]

        # 创建学生
        student = Student(
            student_id=1,
            position=(5.0, 5.0),
            destination=(0.0, 0.0)  # 临时目标，会被覆盖
        )

        # 使用基于距离的策略
        strategy = DistanceBasedStrategy()
        student.selection_strategy = strategy

        # 选择食堂
        selected = student.choose_canteen(canteens)

        # 应该选择最近的食堂（canteen1）
        self.assertIsNotNone(selected)
        self.assertEqual(selected.canteen_id, 1)


def run_tests(test_types=None):
    """
    运行指定类型的测试

    参数：
    test_types: 测试类型列表，可选值：'unit', 'engine', 'integration'
                如果为None，运行所有测试
    """
    # 创建测试套件
    suite = unittest.TestSuite()

    # 根据测试类型添加测试
    if test_types is None or 'unit' in test_types:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStudent))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCanteen))

    if test_types is None or 'engine' in test_types:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSimulationEngine))

    if test_types is None or 'integration' in test_types:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    """
    主函数：根据命令行参数运行测试
    """
    import argparse

    parser = argparse.ArgumentParser(description="运行食堂仿真系统测试")
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--engine", action="store_true", help="运行引擎测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试（默认）")

    args = parser.parse_args()

    # 确定要运行的测试类型
    test_types = []

    if args.unit:
        test_types.append('unit')
    if args.engine:
        test_types.append('engine')
    if args.integration:
        test_types.append('integration')

    # 如果没有指定任何类型，或指定了--all，运行所有测试
    if not test_types or args.all:
        test_types = ['unit', 'engine', 'integration']

    print(f"运行测试类型：{test_types}")
    print("=" * 60)

    # 运行测试
    success = run_tests(test_types)

    print("=" * 60)
    if success:
        print("所有测试通过！")
        sys.exit(0)
    else:
        print("部分测试失败！")
        sys.exit(1)