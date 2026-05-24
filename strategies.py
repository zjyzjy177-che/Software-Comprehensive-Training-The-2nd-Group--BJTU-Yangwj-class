"""
策略模块 - strategies.py

本模块实现多食堂选择算法。
由组员B（算法与数据）负责实现。

核心功能：
1. CanteenSelector类：综合考虑距离和排队人数的食堂选择器
2. 多种选择策略：距离优先、排队优先、综合评分等
3. 权重动态调整：根据仿真状态智能调整选择策略
4. 与models.py的策略模式接口对齐

教育要点：
1. 算法设计：如何权衡多个因素做出最优选择
2. 策略模式：灵活替换不同算法，不影响主体逻辑
3. 参数调优：通过实验找到最佳权重参数
4. 性能优化：高效计算大量学生的选择

注意：所有算法必须与engine.py的SimulationEngine接口对齐。
"""

import math
from typing import List, Dict, Tuple, Any, Optional
from models import Canteen, Student, CanteenSelectionStrategy


class CanteenSelector:
    """
    食堂选择器类

    综合考虑距离和排队人数，为每个学生选择最优食堂。
    支持多种选择策略，可动态切换。

    设计原则：
    1. 可配置性：通过参数调整算法行为
    2. 可扩展性：易于添加新的选择策略
    3. 高效性：支持大量学生的快速选择
    4. 公平性：避免所有学生涌向同一食堂

    算法核心思想：
    对于每个学生，计算每个食堂的得分：
    score = α × normalized_distance + β × normalized_queue_length
    其中：
    - α: 距离权重（0-1），越大表示距离越重要
    - β: 排队权重（0-1），越大表示排队人数越重要
    - normalized_*: 归一化后的值（0-1范围）
    选择得分最低的食堂（得分越低表示越优）。
    """

    def __init__(self, algorithm_params: Dict[str, Any] = None,
                 simulation_params: Dict[str, Any] = None):
        """
        初始化食堂选择器

        参数：
        algorithm_params: 算法参数字典，包含distance_weight、queue_weight等
        simulation_params: 仿真参数字典，包含window_counts、service_rates等

        如果未提供参数，使用config.py中的默认值。
        """
        # 使用默认参数（与config.py对齐）
        if algorithm_params is None:
            algorithm_params = {}
        if simulation_params is None:
            simulation_params = {}

        # 从algorithm_params获取参数，使用config.py默认值
        self.distance_weight = algorithm_params.get('distance_weight', 0.3)
        self.queue_weight = algorithm_params.get('queue_weight', 0.7)
        self.max_walk_distance = algorithm_params.get('max_walk_distance', 1000.0)
        self.prefer_near_canteen = algorithm_params.get('prefer_near_canteen', True)

        # 从simulation_params获取食堂配置
        self.window_counts = simulation_params.get('window_counts', [])
        self.service_rates = simulation_params.get('service_rates', [])

        # 验证权重
        if self.distance_weight < 0 or self.queue_weight < 0:
            raise ValueError("权重不能为负数")
        if self.distance_weight + self.queue_weight == 0:
            raise ValueError("权重之和不能为0")

        # 道路网络（用于计算路径距离，替代欧几里得距离）
        self.road_network = None

        # 统计信息
        self.selection_count = 0
        self.average_score = 0.0
        self.strategy_usage = {
            'distance_based': 0,
            'queue_based': 0,
            'balanced': 0
        }

        print(f"食堂选择器初始化：距离权重={self.distance_weight}, 排队权重={self.queue_weight}, "
              f"最大步行距离={self.max_walk_distance}米")

    def _get_canteen_window_count(self, canteen: Canteen) -> int:
        """
        获取食堂的窗口数量

        优先从配置的window_counts列表中获取，如果不存在则使用canteen.window_count
        """
        if self.window_counts and 0 <= canteen.canteen_id < len(self.window_counts):
            return self.window_counts[canteen.canteen_id]
        # 回退到canteen对象的window_count属性
        return canteen.window_count if hasattr(canteen, 'window_count') else 5

    def _get_canteen_service_rate(self, canteen: Canteen) -> float:
        """
        获取食堂的服务速率

        优先从配置的service_rates列表中获取，如果不存在则使用默认值1.0
        """
        if self.service_rates and 0 <= canteen.canteen_id < len(self.service_rates):
            return self.service_rates[canteen.canteen_id]
        # 默认服务速率
        return 1.0

    def select_best_canteen(self, student_pos: Tuple[float, float],
                           canteens: List[Canteen]) -> Optional[Canteen]:
        """
        选择最优食堂（核心方法）

        参数：
        student_pos: 学生当前位置坐标(x, y)
        canteens: 可用食堂列表

        返回：
        Optional[Canteen]: 最优食堂对象，如果无可用食堂则返回None

        算法步骤：
        1. 过滤：排除距离过远的食堂
        2. 计算：为每个可用食堂计算综合得分
        3. 选择：返回得分最低的食堂
        4. 更新：记录选择统计信息
        """
        if not canteens:
            return None

        # 步骤1：过滤可用食堂
        available_canteens = []
        for canteen in canteens:
            distance = self._get_distance(student_pos, canteen.position)
            if distance <= self.max_walk_distance:
                available_canteens.append((canteen, distance))

        if not available_canteens:
            # 没有可用食堂，返回最近的食堂（即使超过最大距离）
            print(f"警告：所有食堂距离都超过{self.max_walk_distance}米，选择最近的食堂")
            return self._select_nearest_canteen(student_pos, canteens)

        # 步骤2：计算综合得分
        best_score = float('inf')
        best_canteen = None
        best_distance = 0.0

        # 首先计算距离和排队人数的范围（用于归一化）
        distances = [dist for _, dist in available_canteens]
        queue_lengths = [canteen.get_total_queue_length() for canteen, _ in available_canteens]

        max_distance = max(distances) if distances else 1.0
        max_queue = max(queue_lengths) if queue_lengths else 1.0

        # 避免除零错误
        if max_distance == 0:
            max_distance = 1.0
        if max_queue == 0:
            max_queue = 1.0

        for (canteen, distance) in available_canteens:
            # 归一化距离（0-1范围）
            normalized_distance = distance / max_distance

            # 归一化排队人数（0-1范围）
            queue_length = canteen.get_total_queue_length()
            normalized_queue = queue_length / max_queue

            # 获取食堂的窗口数量和服务速率
            window_count = self._get_canteen_window_count(canteen)
            service_rate = self._get_canteen_service_rate(canteen)

            # 计算窗口效率因子（窗口越多、服务越快，效率越高）
            # 避免除零，最小效率因子为0.1
            efficiency_factor = max(window_count * service_rate, 0.1)

            # 调整排队分数：效率越高，排队影响越小
            adjusted_queue = normalized_queue / efficiency_factor

            # 计算综合得分
            score = (self.distance_weight * normalized_distance +
                    self.queue_weight * adjusted_queue)

            # 考虑食堂容量（排队人数接近容量时惩罚）
            capacity = canteen.capacity
            if capacity > 0:
                utilization = queue_length / capacity
                if utilization > 0.8:  # 利用率超过80%时增加惩罚
                    penalty = utilization * 0.5  # 惩罚系数
                    score *= (1 + penalty)

            if score < best_score:
                best_score = score
                best_canteen = canteen
                best_distance = distance

        # 步骤3：选择最优食堂
        if best_canteen:
            # 步骤4：更新统计信息
            self.selection_count += 1
            self.average_score = ((self.average_score * (self.selection_count - 1) +
                                 best_score) / self.selection_count)

            # 记录策略使用情况（基于选择的依据）
            if best_distance < max_distance * 0.3:  # 距离很近
                self.strategy_usage['distance_based'] += 1
            elif queue_lengths[available_canteens.index((best_canteen, best_distance))] == min(queue_lengths):
                self.strategy_usage['queue_based'] += 1
            else:
                self.strategy_usage['balanced'] += 1

            # 打印调试信息（可选）
            if self.selection_count % 50 == 0:
                print(f"食堂选择统计：已选择{self.selection_count}次，平均得分{self.average_score:.3f}")

        return best_canteen

    def _select_nearest_canteen(self, student_pos: Tuple[float, float],
                               canteens: List[Canteen]) -> Optional[Canteen]:
        """
        选择最近的食堂（备用方法）

        当所有食堂都超过最大步行距离时使用。
        简单选择欧几里得距离最近的食堂。
        """
        if not canteens:
            return None

        min_distance = float('inf')
        nearest_canteen = None

        for canteen in canteens:
            distance = self._calculate_distance(student_pos, canteen.position)
            if distance < min_distance:
                min_distance = distance
                nearest_canteen = canteen

        return nearest_canteen

    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        计算两点之间的欧几里得距离

        参数：
        pos1: 第一个点的坐标(x1, y1)
        pos2: 第二个点的坐标(x2, y2)

        返回：
        float: 两点之间的距离
        """
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def set_road_network(self, road_network) -> None:
        """设置道路网络，后续距离计算将使用道路路径长度"""
        self.road_network = road_network

    def _get_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """获取两点间距离：优先使用道路路径长度，否则欧几里得距离"""
        if self.road_network:
            return self.road_network.path_length(pos1, pos2)
        return self._calculate_distance(pos1, pos2)

    def update_weights(self, distance_weight: float, queue_weight: float) -> None:
        """
        动态更新权重参数

        参数：
        distance_weight: 新的距离权重
        queue_weight: 新的排队权重

        可用于根据仿真状态调整算法行为。
        例如：在高峰时段增加排队权重，在平峰时段增加距离权重。
        """
        if distance_weight < 0 or queue_weight < 0:
            raise ValueError("权重不能为负数")
        if distance_weight + queue_weight == 0:
            raise ValueError("权重之和不能为0")

        old_distance = self.distance_weight
        old_queue = self.queue_weight

        self.distance_weight = distance_weight
        self.queue_weight = queue_weight

        print(f"更新权重：距离权重 {old_distance:.2f}→{distance_weight:.2f}, "
              f"排队权重 {old_queue:.2f}→{queue_weight:.2f}")

    def adjust_weights_by_time(self, current_tick: int, max_ticks: int) -> None:
        """
        根据仿真时间调整权重

        参数：
        current_tick: 当前仿真周期
        max_ticks: 总仿真周期数

        模拟真实场景：在高峰时段（仿真中期）更关注排队人数，
        在非高峰时段（仿真开始/结束）更关注距离。
        """
        # 计算仿真进度（0-1范围）
        progress = current_tick / max_ticks if max_ticks > 0 else 0

        # 高峰时段模型：在进度0.3-0.7之间为高峰
        if 0.3 <= progress <= 0.7:
            # 高峰时段：更关注排队人数
            distance_weight = 0.4
            queue_weight = 0.6
        else:
            # 非高峰时段：更关注距离
            distance_weight = 0.8
            queue_weight = 0.2

        self.update_weights(distance_weight, queue_weight)

    def get_selection_stats(self) -> Dict[str, Any]:
        """
        获取选择统计信息

        返回：
        Dict[str, Any]: 包含统计信息的字典

        用于分析算法性能和调整参数。
        """
        total_usage = sum(self.strategy_usage.values())
        if total_usage > 0:
            usage_percent = {k: v/total_usage*100 for k, v in self.strategy_usage.items()}
        else:
            usage_percent = {k: 0.0 for k in self.strategy_usage.keys()}

        return {
            'selection_count': self.selection_count,
            'average_score': self.average_score,
            'strategy_usage': self.strategy_usage.copy(),
            'strategy_percentage': usage_percent,
            'distance_weight': self.distance_weight,
            'queue_weight': self.queue_weight,
            'max_walk_distance': self.max_walk_distance
        }

    def print_stats(self) -> None:
        """打印选择统计信息"""
        stats = self.get_selection_stats()

        print("\n食堂选择器统计：")
        print(f"  总选择次数: {stats['selection_count']}")
        print(f"  平均得分: {stats['average_score']:.3f}")
        print(f"  距离权重: {stats['distance_weight']:.2f}")
        print(f"  排队权重: {stats['queue_weight']:.2f}")

        print(f"  策略使用情况:")
        for strategy, count in stats['strategy_usage'].items():
            percentage = stats['strategy_percentage'][strategy]
            print(f"    {strategy}: {count}次 ({percentage:.1f}%)")


# 策略模式实现：基于距离的选择策略
class EnhancedDistanceStrategy(CanteenSelectionStrategy):
    """
    增强版距离选择策略

    继承自CanteenSelectionStrategy基类，与models.py的策略模式接口对齐。
    主要考虑距离，但也会适当考虑排队情况。
    """

    def __init__(self, algorithm_params: Dict[str, Any] = None,
                 simulation_params: Dict[str, Any] = None,
                 max_distance: float = None):
        """
        初始化距离优先策略

        参数：
        algorithm_params: 算法参数字典，优先使用
        simulation_params: 仿真参数字典
        max_distance: 最大步行距离（向后兼容，优先使用algorithm_params中的max_walk_distance）
        """
        if algorithm_params is None:
            algorithm_params = {}
        if simulation_params is None:
            simulation_params = {}

        # 优先使用algorithm_params中的max_walk_distance，否则使用max_distance参数
        max_walk_distance = algorithm_params.get('max_walk_distance')
        if max_walk_distance is None and max_distance is not None:
            max_walk_distance = max_distance
        elif max_walk_distance is None:
            max_walk_distance = 500.0  # 默认值

        # 设置距离优先的权重（距离权重0.9，排队权重0.1）
        algorithm_params = algorithm_params.copy()  # 避免修改原始字典
        algorithm_params['distance_weight'] = algorithm_params.get('distance_weight', 0.9)
        algorithm_params['queue_weight'] = algorithm_params.get('queue_weight', 0.1)
        algorithm_params['max_walk_distance'] = max_walk_distance

        self.max_distance = max_walk_distance
        self.selector = CanteenSelector(algorithm_params, simulation_params)

    def select_canteen(self, student: Student, canteens: List[Canteen]) -> Optional[Canteen]:
        """选择食堂（实现基类方法）"""
        return self.selector.select_best_canteen(student.position, canteens)


# 策略模式实现：基于排队人数的选择策略
class EnhancedQueueStrategy(CanteenSelectionStrategy):
    """
    增强版排队选择策略

    主要考虑排队人数，适合高峰时段使用。
    """

    def __init__(self, algorithm_params: Dict[str, Any] = None,
                 simulation_params: Dict[str, Any] = None,
                 max_distance: float = None):
        """
        初始化排队优先策略

        参数：
        algorithm_params: 算法参数字典，优先使用
        simulation_params: 仿真参数字典
        max_distance: 最大步行距离（向后兼容，优先使用algorithm_params中的max_walk_distance）
        """
        if algorithm_params is None:
            algorithm_params = {}
        if simulation_params is None:
            simulation_params = {}

        # 优先使用algorithm_params中的max_walk_distance，否则使用max_distance参数
        max_walk_distance = algorithm_params.get('max_walk_distance')
        if max_walk_distance is None and max_distance is not None:
            max_walk_distance = max_distance
        elif max_walk_distance is None:
            max_walk_distance = 500.0  # 默认值

        # 设置排队优先的权重（距离权重0.3，排队权重0.7）
        algorithm_params = algorithm_params.copy()  # 避免修改原始字典
        algorithm_params['distance_weight'] = algorithm_params.get('distance_weight', 0.3)
        algorithm_params['queue_weight'] = algorithm_params.get('queue_weight', 0.7)
        algorithm_params['max_walk_distance'] = max_walk_distance

        self.max_distance = max_walk_distance
        self.selector = CanteenSelector(algorithm_params, simulation_params)

    def select_canteen(self, student: Student, canteens: List[Canteen]) -> Optional[Canteen]:
        """选择食堂（实现基类方法）"""
        return self.selector.select_best_canteen(student.position, canteens)


# 策略模式实现：平衡选择策略
class BalancedStrategy(CanteenSelectionStrategy):
    """
    平衡选择策略

    综合考虑距离和排队人数，使用动态权重调整。
    """

    def __init__(self, algorithm_params: Dict[str, Any] = None,
                 simulation_params: Dict[str, Any] = None,
                 max_distance: float = None):
        """
        初始化平衡选择策略

        参数：
        algorithm_params: 算法参数字典，优先使用
        simulation_params: 仿真参数字典
        max_distance: 最大步行距离（向后兼容，优先使用algorithm_params中的max_walk_distance）
        """
        if algorithm_params is None:
            algorithm_params = {}
        if simulation_params is None:
            simulation_params = {}

        # 优先使用algorithm_params中的max_walk_distance，否则使用max_distance参数
        max_walk_distance = algorithm_params.get('max_walk_distance')
        if max_walk_distance is None and max_distance is not None:
            max_walk_distance = max_distance
        elif max_walk_distance is None:
            max_walk_distance = 500.0  # 默认值

        # 设置平衡权重（距离权重0.7，排队权重0.3）
        algorithm_params = algorithm_params.copy()  # 避免修改原始字典
        algorithm_params['distance_weight'] = algorithm_params.get('distance_weight', 0.7)
        algorithm_params['queue_weight'] = algorithm_params.get('queue_weight', 0.3)
        algorithm_params['max_walk_distance'] = max_walk_distance

        self.max_distance = max_walk_distance
        self.selector = CanteenSelector(algorithm_params, simulation_params)

    def select_canteen(self, student: Student, canteens: List[Canteen]) -> Optional[Canteen]:
        """选择食堂（实现基类方法）"""
        return self.selector.select_best_canteen(student.position, canteens)


# 便捷函数：创建选择器
def create_canteen_selector(strategy_type: str = "balanced",
                           algorithm_params: Dict[str, Any] = None,
                           simulation_params: Dict[str, Any] = None,
                           **kwargs) -> CanteenSelector:
    """
    创建食堂选择器

    参数：
    strategy_type: 策略类型，可选值："distance", "queue", "balanced"
    algorithm_params: 算法参数字典，包含distance_weight、queue_weight等
    simulation_params: 仿真参数字典，包含window_counts、service_rates等
    **kwargs: 向后兼容的额外参数（如max_distance）

    返回：
    CanteenSelector: 食堂选择器对象
    """
    strategy_map = {
        "distance": EnhancedDistanceStrategy,
        "queue": EnhancedQueueStrategy,
        "balanced": BalancedStrategy
    }

    if strategy_type not in strategy_map:
        raise ValueError(f"未知策略类型：{strategy_type}，可选值：{list(strategy_map.keys())}")

    strategy_class = strategy_map[strategy_type]

    # 处理向后兼容：如果algorithm_params和simulation_params未提供，尝试从kwargs提取
    if algorithm_params is None:
        algorithm_params = kwargs.get('algorithm_params', {})
    if simulation_params is None:
        simulation_params = kwargs.get('simulation_params', {})

    # 提取max_distance参数（向后兼容）
    max_distance = kwargs.get('max_distance')

    return strategy_class(algorithm_params=algorithm_params,
                         simulation_params=simulation_params,
                         max_distance=max_distance)


def create_selector_from_config(config: Any, strategy_type: str = "balanced") -> CanteenSelector:
    """
    从BJTUConfig对象创建食堂选择器

    参数：
    config: BJTUConfig配置对象或包含algorithm_params和simulation_params的字典
    strategy_type: 策略类型，可选值："distance", "queue", "balanced"

    返回：
    CanteenSelector: 食堂选择器对象

    此函数从config对象中提取algorithm_params和simulation_params，
    然后创建相应的选择器。
    """
    # 动态导入以避免循环导入
    try:
        from config import BJTUConfig
        is_bjtu_config = isinstance(config, BJTUConfig)
    except ImportError:
        # 如果无法导入BJTUConfig，假设config是字典
        is_bjtu_config = False

    if is_bjtu_config:
        # 从BJTUConfig对象获取参数
        algorithm_params = config.algorithm_params
        simulation_params = config.simulation_params
    elif isinstance(config, dict):
        # 从字典获取参数
        algorithm_params = config.get('algorithm_params', {})
        simulation_params = config.get('simulation_params', {})
    else:
        raise TypeError(f"config必须是BJTUConfig类型或字典，实际类型：{type(config)}")

    # 创建选择器
    return create_canteen_selector(
        strategy_type=strategy_type,
        algorithm_params=algorithm_params,
        simulation_params=simulation_params
    )


# 测试代码（当模块直接运行时执行）
if __name__ == "__main__":
    print("strategies.py 模块测试")
    print("=" * 50)

    # 创建测试食堂
    canteens = []
    positions = [(100.0, 100.0), (300.0, 300.0), (500.0, 100.0)]

    for i, pos in enumerate(positions):
        canteen = Canteen(
            canteen_id=i,
            name=f"测试食堂{i+1}",
            position=pos,
            window_count=3,
            capacity=100
        )
        # 设置不同的排队人数
        if i == 0:
            canteen.total_queue_length = 5
        elif i == 1:
            canteen.total_queue_length = 20
        else:
            canteen.total_queue_length = 10

        canteens.append(canteen)

    # 测试1：使用字典配置创建选择器
    print("\n测试1：使用字典配置创建选择器")
    algorithm_params = {
        'distance_weight': 0.3,
        'queue_weight': 0.7,
        'max_walk_distance': 1000.0,
        'prefer_near_canteen': True
    }
    simulation_params = {
        'window_counts': [10, 15, 3, 20],
        'service_rates': [1.0, 1.0, 1.0, 1.0]
    }

    selector = CanteenSelector(algorithm_params=algorithm_params,
                              simulation_params=simulation_params)

    # 测试选择
    student_pos = (50.0, 50.0)
    best_canteen = selector.select_best_canteen(student_pos, canteens)

    if best_canteen:
        print(f"最优食堂：{best_canteen.name}")
        print(f"  位置：{best_canteen.position}")
        print(f"  排队人数：{best_canteen.get_total_queue_length()}")

    # 测试2：使用策略模式
    print("\n测试2：策略模式测试")
    balanced_strategy = BalancedStrategy(algorithm_params=algorithm_params,
                                        simulation_params=simulation_params)
    student = Student(student_id=1, position=(50.0, 50.0), destination=(0, 0))
    selected = balanced_strategy.select_canteen(student, canteens)

    if selected:
        print(f"平衡策略选择的食堂：{selected.name}")

    # 测试3：使用create_canteen_selector函数
    print("\n测试3：使用create_canteen_selector函数")
    distance_selector = create_canteen_selector(
        strategy_type="distance",
        algorithm_params=algorithm_params,
        simulation_params=simulation_params
    )
    selected2 = distance_selector.select_best_canteen(student_pos, canteens)
    if selected2:
        print(f"距离优先策略选择的食堂：{selected2.name}")

    # 测试4：使用create_selector_from_config函数（模拟config字典）
    print("\n测试4：使用create_selector_from_config函数")
    mock_config = {
        'algorithm_params': algorithm_params,
        'simulation_params': simulation_params
    }
    config_selector = create_selector_from_config(mock_config, strategy_type="queue")
    selected3 = config_selector.select_best_canteen(student_pos, canteens)
    if selected3:
        print(f"排队优先策略选择的食堂：{selected3.name}")

    # 打印统计信息
    print("\n选择器统计信息：")
    selector.print_stats()

    print("\n测试完成！")