"""
仿真引擎模块 - engine.py

本模块定义了食堂就餐流量仿真系统的核心引擎：
SimulationEngine类：驱动整个仿真过程，管理时间周期（Tick）。

核心概念：
1. 离散时间驱动（Tick-driven）：仿真按固定时间周期推进
2. 周期（Tick）：仿真的基本时间单位，每个Tick更新所有实体状态
3. 状态更新：每个Tick更新所有学生和食堂的状态
4. 数据收集：每个Tick收集统计信息，用于分析和可视化

教育要点：
1. 离散事件仿真：通过固定时间步长模拟连续过程
2. 主循环设计：控制仿真流程的核心循环
3. 数据统计：实时收集和分析仿真数据
4. 可扩展架构：便于添加新功能（如可视化、复杂策略等）

注意：本引擎设计为高度可扩展，方便后续添加多食堂选择算法。
"""

import random
import time
from typing import List, Dict, Tuple, Any, Optional
from models import Student, Canteen, StudentState
from strategies import create_selector_from_config, CanteenSelector
from road_network import RoadNetwork


class SimulationEngine:
    """
    仿真引擎类 - 驱动整个食堂就餐流量仿真过程

    职责：
    1. 管理仿真时间（Tick周期）
    2. 管理所有学生和食堂实体
    3. 驱动每个Tick的状态更新
    4. 收集和记录统计信息
    5. 提供仿真控制和查询接口

    核心方法：
    - tick(): 推进一个仿真周期，更新所有实体状态
    - run(): 运行完整仿真（多个Tick）
    - reset(): 重置仿真状态
    - get_statistics(): 获取仿真统计数据

    属性说明：
    - students: 所有学生对象的列表
    - canteens: 所有食堂对象的列表
    - current_tick: 当前仿真周期数
    - max_ticks: 最大仿真周期数（仿真停止条件）
    - tick_history: 每周期的历史数据记录
    - global_statistics: 全局统计数据
    - config: 配置参数（预留接口）

    工作流程：
    初始化 → 循环执行tick() → 收集数据 → 输出结果
    """

    # 类常量（可配置）
    DEFAULT_MAX_TICKS = 1000  # 默认最大仿真周期数
    DEFAULT_SPAWN_RATE = 0.1  # 默认学生生成速率（每个Tick生成学生的概率）
    DEFAULT_STUDENT_COUNT = 100  # 默认初始学生数量
    DEFAULT_CANTEEN_COUNT = 3  # 默认食堂数量

    # 地图边界常量（与 campus_bounds.json 对齐）
    DEFAULT_MAP_BOUNDARIES = (-250.0, -400.0, 450.0, 200.0)  # (x_min, y_min, x_max, y_max)

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化仿真引擎

        参数：
        config: 配置字典，包含仿真参数。如果为None，使用默认配置。

        配置参数示例：
        {
            'max_ticks': 1000,           # 最大仿真周期数
            'spawn_rate': 0.1,           # 学生生成速率
            'student_count': 100,        # 初始学生数量
            'canteen_count': 3,          # 食堂数量
            'map_boundaries': (0,0,1000,800),  # 地图边界
            'enable_visualization': False,  # 是否启用可视化（预留）
            'random_seed': 42,           # 随机种子（确保可重复性）
        }

        注意：配置系统预留了config.py接口，后续可扩展。
        """
        # 合并配置（用户配置覆盖默认配置）
        self.config = self._merge_config(config)

        # 设置随机种子（确保仿真可重复）
        random_seed = self.config.get('random_seed')
        if random_seed is not None:
            random.seed(random_seed)

        # 仿真状态
        self.current_tick = 0
        self.max_ticks = self.config['max_ticks']
        self.is_running = False
        self.start_time = None
        self.end_time = None

        # 实体管理
        self.students = []  # 所有学生列表
        self.canteens = []  # 所有食堂列表
        self.active_students = []  # 仍在仿真中的学生（未离开）

        # 地图边界
        self.map_boundaries = self.config['map_boundaries']

        # 数据记录
        self.tick_history = []  # 每周期历史数据
        self.global_statistics = {
            'total_students_generated': 0,
            'total_students_served': 0,
            'total_wait_time': 0,
            'max_queue_length': 0,
            'average_wait_time': 0.0,
            'canteen_utilization': {},  # 食堂利用率
            'student_state_counts': {}  # 学生状态统计
        }

        # 食堂选择器（使用strategies.py中的算法）
        self.canteen_selector = self._create_canteen_selector()

        # 道路网络（所有学生移动必须沿道路）
        road_segments = self.config.get('road_segments', [])
        self.road_network = RoadNetwork(road_segments) if road_segments else None
        if self.road_network:
            self.canteen_selector.set_road_network(self.road_network)

        # 初始化环境
        self._initialize_environment()

        print(f"仿真引擎初始化完成")
        print(f"配置：最大周期={self.max_ticks}, 初始学生数={len(self.students)}, 食堂数={len(self.canteens)}")

    def _merge_config(self, user_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并用户配置和默认配置（内部方法）

        参数：
        user_config: 用户提供的配置字典

        返回：
        Dict[str, Any]: 合并后的完整配置
        """
        # 默认配置
        default_config = {
            'max_ticks': self.DEFAULT_MAX_TICKS,
            'spawn_rate': self.DEFAULT_SPAWN_RATE,
            'student_count': self.DEFAULT_STUDENT_COUNT,
            'canteen_count': self.DEFAULT_CANTEEN_COUNT,
            'map_boundaries': self.DEFAULT_MAP_BOUNDARIES,
            'enable_visualization': False,
            'random_seed': None,  # 默认不使用固定种子
            'canteen_positions': None,  # 食堂位置列表，None表示随机生成
            'student_start_positions': None,  # 学生起始位置，None表示随机生成
        }

        # 如果用户提供了配置，合并到默认配置中
        if user_config:
            # 深度合并（简单实现，只合并第一层）
            for key, value in user_config.items():
                default_config[key] = value

        return default_config

    def _create_canteen_selector(self) -> CanteenSelector:
        """
        创建食堂选择器（内部方法）

        从配置中提取算法参数和仿真参数，创建CanteenSelector对象。
        支持从config字典或BJTUConfig对象创建。

        返回：
        CanteenSelector: 食堂选择器对象
        """
        # 从配置中提取算法参数和仿真参数
        algorithm_params = self.config.get('algorithm_params', {})
        simulation_params = self.config.get('simulation_params', {})

        # 如果配置中没有algorithm_params，使用默认值
        if not algorithm_params:
            algorithm_params = {
                'distance_weight': 0.3,
                'queue_weight': 0.7,
                'max_walk_distance': 1000.0,
                'prefer_near_canteen': True
            }

        # 如果配置中没有simulation_params，从config中提取相关参数
        if not simulation_params:
            simulation_params = {
                'window_counts': self.config.get('window_counts', []),
                'service_rates': self.config.get('service_rates', []),
                'canteen_positions': self.config.get('canteen_positions', [])
            }

        # 创建选择器
        selector = CanteenSelector(
            algorithm_params=algorithm_params,
            simulation_params=simulation_params
        )

        print(f"食堂选择器创建完成：距离权重={algorithm_params.get('distance_weight', 0.3)}, "
              f"排队权重={algorithm_params.get('queue_weight', 0.7)}")
        return selector

    def _initialize_environment(self) -> None:
        """
        初始化仿真环境（内部方法）

        创建初始的学生和食堂。
        后续可扩展从配置文件加载环境数据。
        """
        # 创建食堂
        self._create_canteens()

        # 创建初始学生
        self._create_initial_students()

        # 更新活跃学生列表
        self.active_students = self.students.copy()

    def _create_canteens(self) -> None:
        """
        创建食堂（内部方法）

        根据配置创建指定数量的食堂。
        优先使用配置中的 canteen_positions、canteen_names、window_counts。
        """
        canteen_count = self.config['canteen_count']
        canteen_positions = self.config.get('canteen_positions')
        canteen_names_cfg = self.config.get('canteen_names', [])
        window_counts = self.config.get('window_counts', [])

        open_canteens = self.config.get('open_canteens', [])
        # 遍历所有可选位置，只创建勾选的食堂
        max_available = len(canteen_names_cfg) if canteen_names_cfg else 4
        created = 0
        for i in range(max_available):
            if created >= canteen_count:
                break
            # 确定食堂位置
            if canteen_positions and i < len(canteen_positions):
                position = tuple(canteen_positions[i])
            else:
                position = self._generate_random_position()

            # 确定食堂名称
            if i < len(canteen_names_cfg):
                name = canteen_names_cfg[i]
            else:
                name = f"食堂{i+1}"

            # 用户只开放了部分食堂
            if open_canteens and name not in open_canteens:
                continue

            created += 1

            # 确定窗口数量（优先使用配置）
            if i < len(window_counts):
                wc = window_counts[i]
            else:
                wc = random.randint(3, 8)

            # 获取该食堂的门位置
            canteen_doors_cfg = self.config.get('canteen_doors', {})
            doors = canteen_doors_cfg.get(name, None)

            canteen = Canteen(
                canteen_id=i,
                name=name,
                position=position,
                window_count=wc,
                capacity=random.randint(100, 300),
                doors=doors
            )

            self.canteens.append(canteen)
            print(f"创建食堂：{name}，位置：{position}，窗口数：{canteen.get_window_count()}，容量：{canteen.capacity}")

    def _create_initial_students(self) -> None:
        """
        创建初始学生（内部方法）

        仿真从 sim_start_time（默认07:00）开始，此时仅有少量学生从宿舍出发。
        大量学生由课表事件（下课/午高峰）在后续 tick 中动态生成。
        """
        student_count = self.config['student_count']
        start_positions = self.config.get('student_start_positions')

        # 初始生成约 1/6 学生，非营业时段不生成
        h, m = self._tick_to_sim_time(0)
        if not self._is_canteen_open(f"{h:02d}:{m:02d}"):
            return
        initial_count = max(5, student_count // 6)

        # 优先从宿舍生成
        building_coords = self.config.get('building_coords', {})
        dorm_positions = []
        for name, coord in building_coords.items():
            if self._classify_building(name) == 'dorm':
                dorm_positions.append(coord)

        for i in range(initial_count):
            if start_positions and i < len(start_positions):
                position = start_positions[i]
            elif dorm_positions:
                position = random.choice(dorm_positions)
            else:
                position = self._get_spawn_position()

            self._spawn_single_student(position=position)

        print(f"创建初始学生：{len(self.students)}名（清晨宿舍出发，共预配置{student_count}人规模）")

    def _generate_random_position(self) -> Tuple[float, float]:
        """
        生成随机位置（内部方法）

        返回：
        Tuple[float, float]: 随机坐标(x, y)，在地图边界内
        """
        x_min, y_min, x_max, y_max = self.map_boundaries
        x = random.uniform(x_min, x_max)
        y = random.uniform(y_min, y_max)
        return (x, y)

    def _get_spawn_position(self) -> Tuple[float, float]:
        """
        获取学生生成位置（按建筑人数权重加权随机选取）

        使用 building_weights 作为权重，人数多的建筑（如嘉园4000人）
        比人数少的建筑（如校史馆100人）更可能生成学生。
        """
        building_coords = self.config.get('building_coords', {})
        building_weights = self.config.get('building_weights', {})

        if building_coords and building_weights:
            # 筛选有坐标且有正权重的建筑
            valid_names = [n for n in building_coords
                          if n in building_weights and building_weights[n] > 0]
            if valid_names:
                w = [building_weights[n] for n in valid_names]
                chosen = random.choices(valid_names, weights=w, k=1)[0]
                return building_coords[chosen]

        # 回退：uniform 随机
        spawn_positions = self.config.get('spawn_positions')
        if spawn_positions:
            return tuple(random.choice(spawn_positions))
        return self._generate_random_position()

    def _random_student_speed(self) -> float:
        """从 config 的 student_speed_range 中随机取速度"""
        lo, hi = self.config.get('student_speed_range', (3.0, 15.0))
        return random.uniform(lo, hi)

    def _random_eating_time(self) -> int:
        """从 config 的 eating_time_range 中随机取用餐时间"""
        lo, hi = self.config.get('eating_time_range', (20, 60))
        return random.randint(lo, hi)

    def tick(self) -> bool:
        """
        推进一个仿真周期（核心方法）

        每个Tick执行以下步骤：
        1. 生成新学生（按生成速率）
        2. 更新所有学生状态
        3. 更新所有食堂状态
        4. 清理已离开的学生
        5. 记录周期数据

        返回：
        bool: 仿真是否应继续（True表示继续，False表示达到停止条件）

        注意：这是离散时间驱动的核心，每个Tick代表一个固定的时间单位。
        """
        # 检查停止条件
        if self.current_tick >= self.max_ticks:
            print(f"达到最大仿真周期数：{self.max_ticks}，仿真停止")
            return False

        # 记录Tick开始时间（用于性能监控）
        tick_start_time = time.time()

        # Tick计数增加
        self.current_tick += 1

        if self.current_tick % 100 == 0:
            print(f"Tick {self.current_tick}/{self.max_ticks}，活跃学生：{len(self.active_students)}")

        # 步骤1：生成新学生
        self._spawn_students()

        # 步骤2：更新所有学生状态
        self._update_all_students()

        # 步骤3：更新所有食堂状态
        self._update_all_canteens()

        # 步骤4：清理已离开的学生
        self._cleanup_left_students()

        # 步骤5：记录周期数据
        self._record_tick_data(tick_start_time)

        return True

    # ============================================================
    # 时间与课表辅助方法
    # ============================================================

    def _time_str_to_minutes(self, time_str: str) -> int:
        """将 'HH:MM' 格式转换为从午夜开始的分钟数"""
        h, m = map(int, time_str.split(':'))
        return h * 60 + m

    def _tick_to_sim_time(self, tick: int) -> tuple:
        """将tick序号转换为模拟时间 (hour, minute)"""
        start_time = self.config.get('sim_start_time', '07:00')
        start_minutes = self._time_str_to_minutes(start_time)
        tick_seconds = self.config.get('tick_duration_seconds', 60)
        elapsed_minutes = (tick * tick_seconds) / 60.0
        total_minutes = start_minutes + elapsed_minutes
        hours = int(total_minutes / 60) % 24
        minutes = int(total_minutes % 60)
        return hours, minutes

    def _classify_building(self, name: str) -> str:
        """根据建筑名称关键词分类: 'teaching' | 'dorm' | 'canteen' | 'other'"""
        canteen_kw = ['食堂', '留园']
        dorm_kw = ['宿舍', '嘉园', '公寓']
        teaching_kw = ['教', '楼', '逸夫', '思源', '土木', '电气', '机械',
                       '校史馆', '科学会堂', '计算中心', '图书馆']

        if any(kw in name for kw in canteen_kw):
            return 'canteen'
        if any(kw in name for kw in dorm_kw):
            return 'dorm'
        if any(kw in name for kw in teaching_kw):
            return 'teaching'
        return 'other'

    def _is_peak_hour(self, hour: int, minute: int) -> bool:
        """判断当前时间是否在就餐高峰期（11:30-12:20 或 18:00-19:00）"""
        # 午餐高峰 11:30-12:20
        if hour == 11 and minute >= 30:
            return True
        if hour == 12 and minute <= 20:
            return True
        # 晚餐高峰 18:00-19:00
        if hour == 18:
            return True
        return False

    def _is_canteen_open(self, current_time: str) -> bool:
        """检查当前时间是否有食堂在营业"""
        canteen_hours = self.config.get('canteen_hours', [])
        if not canteen_hours:
            return True  # 没配置营业时间则默认全时段开放
        for slot in canteen_hours:
            if slot['start'] <= current_time <= slot['end']:
                return True
        return False
        return False

    def _get_schedule_events(self, current_time: str) -> tuple:
        """
        获取当前时间点的课表事件

        返回:
        tuple: (class_ends, class_starts) — 下课和上课的建筑名称列表
        """
        class_schedules = self.config.get('class_schedules', {})
        class_ends = []
        class_starts = []

        for building_name, schedules in class_schedules.items():
            for slot in schedules:
                if slot['end'] == current_time:
                    class_ends.append(building_name)
                if slot['start'] == current_time:
                    class_starts.append(building_name)

        return class_ends, class_starts

    # ============================================================
    # 学生生成辅助方法
    # ============================================================

    def _spawn_single_student(self, position: Tuple[float, float] = None) -> None:
        """生成单个学生，上限为 student_count × 5 保证课表波次不断"""
        max_students = self.config.get('student_count', 100) * 5
        if len(self.students) >= max_students:
            return

        if position is None:
            position = self._get_spawn_position()

        # 吸附到最近道路
        snapped_pos = position
        if self.road_network:
            snapped_pos, _ = self.road_network.snap_to_road(position)

        student_id = len(self.students)

        # 选择目标食堂（使用智能选择器，传入吸附后位置）
        target_canteen = None
        if self.canteens and hasattr(self, 'canteen_selector') and self.canteen_selector:
            target_canteen = self.canteen_selector.select_best_canteen(snapped_pos, self.canteens)

        if target_canteen is None and self.canteens:
            target_canteen = random.choice(self.canteens)

        if target_canteen:
            speed = self._random_student_speed()
            eating_time = self._random_eating_time()
            # 从最近的门进入食堂
            target_door = target_canteen.get_nearest_door(snapped_pos)
            student = Student(
                student_id=student_id,
                position=snapped_pos,
                destination=target_door,
                speed=speed,
                eating_time=eating_time
            )
            student.target_canteen_id = target_canteen.canteen_id

            # 计算道路路径点到最近的门
            if self.road_network:
                waypoints = self.road_network.find_path(snapped_pos, target_door)
                student.waypoints = waypoints
                student.current_waypoint_idx = 0

            self.students.append(student)
            self.active_students.append(student)
            self.global_statistics['total_students_generated'] += 1

    def _spawn_class_end_burst(self, building_name: str, burst_size: int,
                               total_ends: int = 1, total_scheduled: int = 7) -> None:
        """
        下课时段爆发式生成学生

        两种模式：
        - 错峰时段（仅部分教学楼下课，如12:00仅思源/9教/土木下课）：
          60%从该教学楼出，30%从宿舍出（按权重），10%从其他教学楼出（按权重）
        - 共享时段（多数教学楼同时下课，如09:50六栋楼一起下课）：
          所有建筑按权重等比例生成
        """
        building_coords = self.config.get('building_coords', {})
        building_weights = self.config.get('building_weights', {})
        building_pos = building_coords.get(building_name)

        if building_pos is None or not building_coords:
            return

        # 按实际学生规模缩放 burst（权重是最大容量上限，需与当前学生数成比例）
        total_weight = sum(building_weights.values())
        actual_students = len(self.students) + self.config.get('student_count', 100)
        scale = min(1.0, actual_students / max(total_weight * 0.05, 1))
        burst_size = max(10, int(burst_size * scale))

        # 判断错峰还是共享：下课建筑数 <= 总课表建筑数的一半 → 错峰
        is_staggered = total_ends <= total_scheduled / 2

        # 分类收集建筑（含权重）
        dorm_items = []
        other_teaching_items = []

        for name, coord in building_coords.items():
            if name == building_name:
                continue
            btype = self._classify_building(name)
            w = building_weights.get(name, 100)
            if btype == 'dorm' and w > 0:
                dorm_items.append((name, coord, w))
            elif btype == 'teaching' and w > 0:
                other_teaching_items.append((name, coord, w))

        if is_staggered:
            # ---- 错峰：6:3:1 分布 ----
            num_from_building = int(burst_size * 0.6)
            num_from_dorms = int(burst_size * 0.3)
            num_from_other = burst_size - num_from_building - num_from_dorms

            # 60% 从该教学楼出来
            for _ in range(num_from_building):
                self._spawn_single_student(position=building_pos)

            # 30% 从宿舍出来（按权重加权）
            if dorm_items:
                d_names = [it[0] for it in dorm_items]
                d_weights = [it[2] for it in dorm_items]
                for _ in range(num_from_dorms):
                    chosen = random.choices(d_names, weights=d_weights, k=1)[0]
                    self._spawn_single_student(position=building_coords[chosen])
            else:
                for _ in range(num_from_dorms):
                    self._spawn_single_student()

            # 10% 从其他教学楼出来（按权重加权）
            if other_teaching_items:
                ot_names = [it[0] for it in other_teaching_items]
                ot_weights = [it[2] for it in other_teaching_items]
                for _ in range(num_from_other):
                    chosen = random.choices(ot_names, weights=ot_weights, k=1)[0]
                    self._spawn_single_student(position=building_coords[chosen])
            else:
                for _ in range(num_from_other):
                    self._spawn_single_student()
        else:
            # ---- 共享时段：所有建筑按权重等比例生成 ----
            all_items = [(building_name, building_pos,
                         building_weights.get(building_name, 2000))]
            all_items.extend(dorm_items)
            all_items.extend(other_teaching_items)

            all_names = [it[0] for it in all_items]
            all_weights = [it[2] for it in all_items]
            for _ in range(burst_size):
                chosen = random.choices(all_names, weights=all_weights, k=1)[0]
                self._spawn_single_student(position=building_coords[chosen])

    # ============================================================
    # 主要生成逻辑
    # ============================================================

    def _spawn_students(self) -> None:
        """
        生成新学生（内部方法）—— 基于课表时间，仅在食堂营业时段生成
        """
        hour, minute = self._tick_to_sim_time(self.current_tick)
        current_time = f"{hour:02d}:{minute:02d}"

        # 食堂全部关闭时不生成新学生（已有学生可继续移动）
        if not self._is_canteen_open(current_time):
            return

        # 检查课表事件（下课/上课）
        class_ends, class_starts = self._get_schedule_events(current_time)

        # 判断是否在就餐高峰期
        in_peak = self._is_peak_hour(hour, minute)

        # ---- 下课时间：爆发式生成 ----
        # 就餐高峰下课（12:00/12:20/18:10）→ 满额爆发
        # 课间下课（09:50等）→ 少量生成（平时换教室也会有人顺路去食堂）
        total_scheduled = len(self.config.get('class_schedules', {}))
        for building_name in class_ends:
            if in_peak:
                burst_size = self.config.get('class_end_burst_size', 50)
                mode = '错峰' if len(class_ends) <= total_scheduled / 2 else '共享'
            else:
                burst_size = max(5, self.config.get('class_end_burst_size', 50) // 5)
                mode = '课间'
            self._spawn_class_end_burst(building_name, burst_size,
                                        len(class_ends), total_scheduled)
            if self.current_tick % 50 == 0:
                print(f"Tick {self.current_tick} ({current_time}): "
                      f"{building_name}下课({mode})，爆发生成{burst_size}名学生")

        # ---- 高峰期：按学生规模每tick生成多个学生 ----
        if in_peak:
            student_count = self.config.get('student_count', 100)
            multiplier = self.config.get('peak_spawn_multiplier', 5.0)
            base_peak = max(2, int(student_count * multiplier / 100))
            num_spawn = random.randint(base_peak, base_peak * 2)
            for _ in range(num_spawn):
                self._spawn_single_student()
            if self.current_tick % 20 == 0:
                print(f"Tick {self.current_tick} ({current_time}): "
                      f"就餐高峰期，生成{num_spawn}名学生")

        # ---- 课间/正常时间：按基础概率生成 ----
        elif not class_ends:
            spawn_rate = self.config['spawn_rate']
            if random.random() < spawn_rate:
                self._spawn_single_student()

    def _update_all_students(self) -> None:
        """
        更新所有学生状态（内部方法）

        遍历所有活跃学生，调用其update_state方法。
        同时处理学生加入食堂队列的逻辑。
        """
        # 临时列表，记录本Tick需要从活跃列表移除的学生（已离开）
        students_to_remove = []

        for student in self.active_students:
            # 更新学生状态
            is_active = student.update_state(self.map_boundaries)

            # 检查学生是否需要加入食堂队列（仅尚未分配到窗口的学生）
            if (student.state == StudentState.QUEUING
                    and student.target_canteen_id is not None
                    and student.target_window_id is None):
                target_canteen = self._find_canteen_by_id(student.target_canteen_id)
                if target_canteen:
                    target_canteen.add_student_to_queue(student)

            # 如果学生已离开，标记为待移除
            if not is_active:
                students_to_remove.append(student)

        # 从活跃列表中移除已离开的学生
        for student in students_to_remove:
            if student in self.active_students:
                self.active_students.remove(student)

    def _find_canteen_by_id(self, canteen_id: int) -> Optional[Canteen]:
        """
        根据ID查找食堂（内部方法）

        参数：
        canteen_id: 食堂ID

        返回：
        Optional[Canteen]: 找到的食堂对象，如果未找到则返回None
        """
        for canteen in self.canteens:
            if canteen.canteen_id == canteen_id:
                return canteen
        return None

    def _update_all_canteens(self) -> None:
        """
        更新所有食堂状态（内部方法）

        遍历所有食堂，调用其update_windows方法。
        每个食堂负责更新自己的窗口状态。
        """
        for canteen in self.canteens:
            canteen.update_windows()

    def _cleanup_left_students(self) -> None:
        """
        清理已离开的学生（内部方法）

        检查所有学生，将状态为LEFT的学生从活跃列表中移除。
        同时更新全局统计。
        """
        # 注意：这个清理已经在_update_all_students中部分完成
        # 这里进行额外的清理和统计更新

        # 统计本Tick离开的学生数量
        left_count = 0
        for student in self.students:
            if student.state == StudentState.LEFT and student in self.active_students:
                self.active_students.remove(student)
                left_count += 1

        if left_count > 0 and self.current_tick % 50 == 0:
            print(f"Tick {self.current_tick}: {left_count}名学生离开仿真")

    def _record_tick_data(self, tick_start_time: float) -> None:
        """
        记录周期数据（内部方法）

        收集本Tick的统计数据，添加到历史记录中。
        同时更新全局统计数据。

        参数：
        tick_start_time: 本Tick开始的时间戳（用于计算Tick耗时）
        """
        # 计算Tick耗时（性能监控）
        tick_duration = time.time() - tick_start_time

        # 收集学生状态统计
        state_counts = {
            StudentState.WALKING: 0,
            StudentState.QUEUING: 0,
            StudentState.EATING: 0,
            StudentState.LEAVING: 0,
            StudentState.LEFT: 0
        }

        for student in self.students:
            if student.state in state_counts:
                state_counts[student.state] += 1

        # 收集食堂统计
        canteen_stats = []
        total_queue_length = 0
        max_queue_length = 0

        for canteen in self.canteens:
            canteen_stat = canteen.get_status()
            canteen_stats.append(canteen_stat)

            total_queue_length += canteen_stat['total_queue_length']
            if canteen_stat['total_queue_length'] > max_queue_length:
                max_queue_length = canteen_stat['total_queue_length']

        # 计算平均等待时间（简化）
        total_students = len(self.students)
        total_wait_time = sum(student.total_wait_time for student in self.students)
        avg_wait_time = total_wait_time / total_students if total_students > 0 else 0

        self.global_statistics['current_tick'] = self.current_tick
        self.global_statistics['total_students_served'] = sum(canteen.served_count for canteen in self.canteens)
        self.global_statistics['total_wait_time'] = total_wait_time
        self.global_statistics['max_queue_length'] = max(
            self.global_statistics['max_queue_length'],
            max_queue_length
        )
        self.global_statistics['average_wait_time'] = avg_wait_time
        self.global_statistics['student_state_counts'] = state_counts
        self.global_statistics['final_active_students'] = len(self.active_students)
        # 各食堂统计数据
        canteen_stats = {}
        for c in self.canteens:
            canteen_stats[c.name] = {
                'served': c.served_count,
                'max_queue': c.max_queue_length,
                'current_queue': c.get_total_queue_length(),
                'capacity': c.capacity,
                'window_count': getattr(c, 'window_count', len(c.windows)),
            }
        self.global_statistics['canteen_statistics'] = canteen_stats

        # 记录Tick历史
        tick_record = {
            'tick_number': self.current_tick,
            'timestamp': time.time(),
            'duration': tick_duration,
            'active_students': len(self.active_students),
            'state_counts': state_counts,
            'total_queue_length': total_queue_length,
            'max_queue_length': max_queue_length,
            'average_wait_time': avg_wait_time,
            'canteen_stats': canteen_stats,
            'global_statistics': self.global_statistics.copy()  # 浅拷贝
        }

        self.tick_history.append(tick_record)

        # 每100个Tick打印简要统计
        if self.current_tick % 100 == 0:
            self._print_tick_summary(tick_record)

    def _print_tick_summary(self, tick_record: Dict[str, Any]) -> None:
        """
        打印Tick摘要（内部方法）

        参数：
        tick_record: 本Tick的数据记录
        """
        print(f"\nTick {self.current_tick} 摘要:")
        print(f"  活跃学生: {tick_record['active_students']}")
        print(f"  学生状态: 行走{tick_record['state_counts'][StudentState.WALKING]}, "
              f"排队{tick_record['state_counts'][StudentState.QUEUING]}, "
              f"用餐{tick_record['state_counts'][StudentState.EATING]}, "
              f"离开{tick_record['state_counts'][StudentState.LEAVING]}")
        print(f"  总排队人数: {tick_record['total_queue_length']}")
        print(f"  最大排队人数: {tick_record['max_queue_length']}")
        print(f"  平均等待时间: {tick_record['average_wait_time']:.2f}周期")
        print(f"  Tick耗时: {tick_record['duration']:.4f}秒")

    def run(self, verbose: bool = True) -> None:
        """
        运行完整仿真

        参数：
        verbose: 是否打印详细进度信息

        连续调用tick()方法，直到达到停止条件。
        这是仿真的主循环。
        """
        if self.is_running:
            print("仿真已经在运行中")
            return

        print("=" * 50)
        print("开始运行仿真")
        print(f"最大周期数: {self.max_ticks}")
        print(f"初始学生数: {len(self.students)}")
        print(f"食堂数量: {len(self.canteens)}")
        print("=" * 50)

        self.is_running = True
        self.start_time = time.time()

        # 主循环
        while self.tick():
            # 可以在这里添加暂停、速度控制等逻辑
            # 目前简单实现，连续运行
            pass

        self.end_time = time.time()
        self.is_running = False

        # 打印仿真总结
        self.print_summary()

    def print_summary(self) -> None:
        """打印仿真总结报告"""
        if not self.tick_history:
            print("没有仿真数据可总结")
            return

        total_duration = self.end_time - self.start_time if self.end_time else 0

        print("\n" + "=" * 50)
        print("仿真总结报告")
        print("=" * 50)
        print(f"仿真周期数: {self.current_tick}")
        print(f"总耗时: {total_duration:.2f}秒")
        print(f"平均每Tick耗时: {total_duration/self.current_tick:.4f}秒" if self.current_tick > 0 else "N/A")
        print(f"总生成学生数: {self.global_statistics['total_students_generated']}")
        print(f"总服务学生数: {self.global_statistics['total_students_served']}")
        print(f"最大排队人数: {self.global_statistics['max_queue_length']}")
        print(f"平均等待时间: {self.global_statistics['average_wait_time']:.2f}周期")
        print(f"最终活跃学生数: {len(self.active_students)}")

        # 食堂详细统计
        print("\n食堂统计:")
        for canteen in self.canteens:
            stats = canteen.get_status()
            print(f"  {canteen.name}: 服务{stats['served_count']}人, "
                  f"最大排队{stats['max_queue_length']}人, "
                  f"平均等待{stats['average_wait_time']:.2f}周期")

        print("=" * 50)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取仿真统计数据

        返回：
        Dict[str, Any]: 包含全局统计数据的字典

        用于外部程序获取仿真结果。
        """
        return self.global_statistics.copy()

    def get_tick_history(self) -> List[Dict[str, Any]]:
        """
        获取Tick历史记录

        返回：
        List[Dict[str, Any]]: 所有Tick的历史记录列表

        用于数据分析和可视化。
        """
        return self.tick_history.copy()

    def reset(self) -> None:
        """
        重置仿真状态

        清空所有数据，恢复初始状态。
        便于多次运行仿真进行对比。
        """
        print("重置仿真引擎...")

        # 重置状态变量
        self.current_tick = 0
        self.is_running = False
        self.start_time = None
        self.end_time = None

        # 清空实体列表
        self.students.clear()
        self.canteens.clear()
        self.active_students.clear()

        # 清空数据记录
        self.tick_history.clear()
        self.global_statistics = {
            'total_students_generated': 0,
            'total_students_served': 0,
            'total_wait_time': 0,
            'max_queue_length': 0,
            'average_wait_time': 0.0,
            'canteen_utilization': {},
            'student_state_counts': {}
        }

        # 重新初始化环境
        self._initialize_environment()

        print("仿真重置完成")

    def get_current_state(self) -> Dict[str, Any]:
        """
        获取当前仿真状态

        返回：
        Dict[str, Any]: 包含当前仿真状态的字典

        用于实时监控和可视化。
        """
        return {
            'current_tick': self.current_tick,
            'max_ticks': self.max_ticks,
            'is_running': self.is_running,
            'active_students': len(self.active_students),
            'total_students': len(self.students),
            'canteen_count': len(self.canteens),
            'global_statistics': self.global_statistics.copy()
        }


# 辅助函数：创建默认配置
def create_default_config() -> Dict[str, Any]:
    """
    创建默认配置

    返回：
    Dict[str, Any]: 默认配置字典

    便于用户快速创建配置。
    """
    return {
        'max_ticks': 500,
        'spawn_rate': 0.05,
        'student_count': 50,
        'canteen_count': 2,
        'map_boundaries': (0.0, 0.0, 800.0, 600.0),
        'enable_visualization': False,
        'random_seed': 42,  # 固定种子，确保可重复性
        'canteen_positions': [(200.0, 300.0), (600.0, 300.0)],  # 两个食堂的位置
        'student_start_positions': None  # 随机生成学生起始位置
    }


# 测试代码（当模块直接运行时执行）
if __name__ == "__main__":
    print("engine.py 模块测试")
    print("=" * 50)

    # 创建默认配置
    config = create_default_config()

    # 创建仿真引擎
    engine = SimulationEngine(config)

    # 运行少量Tick进行测试
    print("\n运行10个Tick进行测试...")
    for i in range(10):
        engine.tick()

    # 打印当前状态
    state = engine.get_current_state()
    print(f"\n当前状态：")
    print(f"  Tick: {state['current_tick']}/{state['max_ticks']}")
    print(f"  活跃学生: {state['active_students']}")
    print(f"  总学生数: {state['total_students']}")

    print("\n测试完成！")
    print("=" * 50)