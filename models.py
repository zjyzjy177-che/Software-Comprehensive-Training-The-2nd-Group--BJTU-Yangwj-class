"""
数据模型模块 - models.py

本模块定义了食堂就餐流量仿真系统的核心数据模型：
1. Student类：模拟单个学生的行为，实现有限状态机（FSM）
2. Window类：食堂窗口，管理排队队列和服务逻辑
3. Canteen类：食堂实体，包含多个窗口，管理整体服务流程

状态机设计：
行走(WALKING) → 排队(QUEUING) → 用餐(EATING) → 离开(LEAVING)

教育要点：
1. 有限状态机：通过明确的状态和转换条件管理复杂行为
2. 面向对象设计：将学生、食堂、窗口抽象为类，提高代码可维护性
3. 队列管理：使用FIFO（先进先出）队列模拟真实排队场景
4. 坐标计算：使用欧几里得距离计算移动，支持真实地图坐标

注意：所有坐标使用浮点数，支持BJTU真实地图比例。
"""

import math
import random
from typing import List, Tuple, Optional


# 状态常量定义
class StudentState:
    """学生状态常量类"""
    WALKING = "WALKING"    # 行走状态：正在前往食堂
    QUEUING = "QUEUING"    # 排队状态：在食堂窗口排队
    EATING = "EATING"      # 用餐状态：正在用餐
    LEAVING = "LEAVING"    # 离开状态：离开食堂区域
    LEFT = "LEFT"          # 完成状态：已离开仿真区域


class Student:
    """
    学生类 - 代表仿真中的一个学生个体

    职责：
    1. 管理学生的位置和移动
    2. 实现有限状态机，管理状态转换
    3. 记录个人统计信息（等待时间、用餐时间等）
    4. 与食堂交互（加入队列、接受服务等）

    状态转换规则：
    1. 行走 → 排队：到达食堂（距离小于阈值）
    2. 排队 → 用餐：被食堂窗口服务
    3. 用餐 → 离开：用餐时间结束
    4. 离开 → 完成：离开仿真区域

    属性说明：
    - position: 当前位置坐标(x, y)，使用浮点数支持真实坐标
    - destination: 目标食堂坐标
    - speed: 行走速度（单位/周期），控制移动快慢
    - state: 当前状态，使用StudentState常量
    - state_timer: 在当前状态的停留时间（周期数）
    - total_wait_time: 总等待时间统计
    - eating_time: 用餐所需时间（周期数）
    """

    # 类常量
    ARRIVAL_THRESHOLD = 5.0  # 到达食堂的距离阈值（单位：坐标距离）
    DEFAULT_SPEED = 2.0      # 默认行走速度
    DEFAULT_EATING_TIME = 10  # 默认用餐时间（周期数）

    def __init__(self, student_id: int, position: Tuple[float, float],
                 destination: Tuple[float, float], speed: float = None,
                 eating_time: int = None, origin_building: str = None,
                 spawn_tick: int = 0):
        """
        初始化学生对象

        参数：
        student_id: 学生唯一标识，用于区分不同学生
        position: 初始位置坐标(x, y)
        destination: 目标食堂坐标(x, y)
        speed: 行走速度，默认使用DEFAULT_SPEED
        eating_time: 用餐时间，默认使用DEFAULT_EATING_TIME

        注意：坐标使用浮点数，支持真实地图比例。
        """
        self.student_id = student_id
        self.position = position  # 当前位置
        self.destination = destination  # 目标食堂位置
        self.speed = speed if speed is not None else self.DEFAULT_SPEED

        # 状态相关属性
        self.state = StudentState.WALKING  # 初始状态为行走
        self.state_timer = 0  # 在当前状态的停留时间
        self.eating_time = eating_time if eating_time is not None else self.DEFAULT_EATING_TIME

        # 道路网络路径点（由 RoadNetwork.find_path 生成）
        self.waypoints = []  # 路径点列表 [(x,y), ...]
        self.current_waypoint_idx = 0  # 当前前往的路径点索引

        # 出发建筑（用于按来源着色）
        self.origin_building = origin_building
        self.spawn_tick = spawn_tick

        # 目标食堂和窗口
        self.target_canteen_id = None  # 目标食堂ID，在choose_canteen方法中设置
        self.target_window_id = None   # 目标窗口ID，在join_queue方法中设置

        # 统计信息
        self.total_wait_time = 0  # 总等待时间（周期数）
        self.total_eat_time = 0   # 总用餐时间（周期数）
        self.arrival_time = None  # 到达食堂时间（周期数）
        self.leave_time = None    # 离开食堂时间（周期数）

        # 可扩展性：食堂选择策略
        self.selection_strategy = None  # 食堂选择策略，后续可扩展

        # 验证初始位置
        self._validate_position(self.position)

    def _validate_position(self, position: Tuple[float, float]) -> None:
        """
        验证坐标是否有效（内部方法）

        参数：
        position: 要验证的坐标(x, y)

        目前只进行基本验证，后续可扩展边界检查。
        实际边界检查应在SimulationEngine中实现。
        """
        x, y = position
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
            raise ValueError(f"坐标必须是数字类型: ({x}, {y})")

    def update_state(self, boundaries: Optional[Tuple[float, float, float, float]] = None) -> bool:
        """
        更新学生状态（核心方法）

        根据当前状态执行相应行为：
        - WALKING: 向目标食堂移动，检查是否到达
        - QUEUING: 在队列中等待，计时等待时间
        - EATING: 用餐计时，检查用餐是否结束
        - LEAVING: 离开食堂区域，检查是否离开仿真范围

        参数：
        boundaries: 地图边界(x_min, y_min, x_max, y_max)，用于坐标边界检查

        返回：
        bool: 学生是否还在仿真中（True表示还在，False表示已离开）

        状态转换逻辑：
        1. 行走 → 排队：距离食堂小于ARRIVAL_THRESHOLD
        2. 排队 → 用餐：由Canteen类的serve_next_student方法触发
        3. 用餐 → 离开：用餐时间达到eating_time
        4. 离开 → 完成：离开仿真区域（由边界检查判断）
        """
        # 增加在当前状态的停留时间
        self.state_timer += 1

        if self.state == StudentState.WALKING:
            # 行走状态：向目标食堂移动
            self._move_to_destination()

            # 检查是否到达食堂（距离小于阈值）
            distance_to_dest = self._calculate_distance(self.position, self.destination)
            if distance_to_dest < self.ARRIVAL_THRESHOLD:
                # 到达食堂，状态转换为排队
                self.arrival_time = self.state_timer  # 记录行走耗时
                self.state = StudentState.QUEUING
                self.state_timer = 0  # 重置状态计时器
                print(f"学生{self.student_id}已到达食堂，开始排队")

        elif self.state == StudentState.QUEUING:
            # 排队状态：在队列中等待
            # 等待时间计入总等待时间
            self.total_wait_time += 1

            # 注意：从排队状态转换到用餐状态由Canteen类的serve_next_student方法触发
            # 该方法会将学生的状态设置为EATING

        elif self.state == StudentState.EATING:
            # 用餐状态：正在用餐
            self.total_eat_time += 1

            # 检查用餐是否结束
            if self.state_timer >= self.eating_time:
                # 用餐结束，状态转换为离开
                self.leave_time = self.state_timer  # 记录用餐耗时
                self.state = StudentState.LEAVING
                self.state_timer = 0
                print(f"学生{self.student_id}用餐结束，准备离开")

        elif self.state == StudentState.LEAVING:
            # 离开状态：原地停留3 tick后消失
            if self.state_timer >= 3:
                self.state = StudentState.LEFT
                return False  # 学生已离开

        # 坐标边界检查（如果提供了边界）
        if boundaries and self.state != StudentState.LEFT:
            self._enforce_boundaries(boundaries)

        return self.state != StudentState.LEFT

    def _move_to_destination(self) -> None:
        """沿道路路径点向目标移动，没有路径点时直接走向目标"""
        # 确定当前目标点
        if self.waypoints and self.current_waypoint_idx < len(self.waypoints):
            target = self.waypoints[self.current_waypoint_idx]
        else:
            target = self.destination

        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            self._advance_waypoint()
            return

        # 归一化并移动
        step = min(self.speed, distance)
        dx = dx / distance * step
        dy = dy / distance * step
        self.position = (self.position[0] + dx, self.position[1] + dy)

        # 到达当前目标点时推进到下一个路径点
        if self._calculate_distance(self.position, target) < self.ARRIVAL_THRESHOLD:
            self._advance_waypoint()

    def _advance_waypoint(self) -> None:
        """推进到下一个路径点，全部完成后到达终点"""
        if self.waypoints and self.current_waypoint_idx < len(self.waypoints):
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(self.waypoints):
                self.position = self.destination

    def _enforce_boundaries(self, boundaries: Tuple[float, float, float, float]) -> None:
        """
        强制坐标在边界内（内部方法）

        参数：
        boundaries: 地图边界(x_min, y_min, x_max, y_max)

        如果坐标超出边界，则修正到边界。
        防止坐标溢出导致仿真错误。
        """
        x_min, y_min, x_max, y_max = boundaries
        x, y = self.position

        # 边界检查，如果超出则修正到边界
        x = max(x_min, min(x, x_max))
        y = max(y_min, min(y, y_max))

        self.position = (x, y)

    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        计算两点之间的欧几里得距离（内部方法）

        参数：
        pos1: 第一个点的坐标(x1, y1)
        pos2: 第二个点的坐标(x2, y2)

        返回：
        float: 两点之间的距离
        """
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def join_queue(self, canteen_id: int, window_id: int) -> None:
        """
        加入食堂窗口队列

        参数：
        canteen_id: 食堂ID
        window_id: 窗口ID

        当学生到达食堂后，调用此方法加入指定窗口的队列。
        该方法由Canteen类的add_student_to_queue方法调用。
        """
        self.target_canteen_id = canteen_id
        self.target_window_id = window_id
        print(f"学生{self.student_id}加入食堂{canteen_id}的窗口{window_id}队列")

    def start_eating(self) -> None:
        """
        开始用餐

        当学生被食堂窗口服务时，调用此方法开始用餐。
        该方法由Canteen类的serve_next_student方法调用。
        """
        # 验证状态转换合法性：只能从QUEUING转换到EATING
        if self.state != StudentState.QUEUING:
            raise ValueError(f"无效状态转换：当前状态为{self.state}，不能开始用餐")

        self.state = StudentState.EATING
        self.state_timer = 0  # 重置用餐计时器
        print(f"学生{self.student_id}开始用餐")

    def choose_canteen(self, canteens: List['Canteen']) -> Optional['Canteen']:
        """
        选择食堂（可扩展方法）

        参数：
        canteens: 可用食堂列表

        返回：
        Optional[Canteen]: 选择的食堂，如果无法选择则返回None

        目前实现简单策略：选择最近的食堂。
        后续可通过设置selection_strategy属性实现更复杂的策略。
        """
        if not canteens:
            return None

        # 如果有选择策略，使用策略选择
        if self.selection_strategy:
            return self.selection_strategy.select_canteen(self, canteens)

        # 默认策略：选择最近的食堂
        min_distance = float('inf')
        selected_canteen = None

        for canteen in canteens:
            distance = self._calculate_distance(self.position, canteen.position)
            if distance < min_distance:
                min_distance = distance
                selected_canteen = canteen

        return selected_canteen

    def get_status(self) -> dict:
        """
        获取学生当前状态信息

        返回：
        dict: 包含学生状态信息的字典

        用于调试和统计。
        """
        return {
            'student_id': self.student_id,
            'position': self.position,
            'state': self.state,
            'state_timer': self.state_timer,
            'total_wait_time': self.total_wait_time,
            'total_eat_time': self.total_eat_time,
            'target_canteen_id': self.target_canteen_id,
            'target_window_id': self.target_window_id
        }


class Window:
    """
    食堂窗口类 - 代表食堂的一个服务窗口

    职责：
    1. 管理排队队列（FIFO）
    2. 服务队列中的学生
    3. 记录服务状态和计时

    属性说明：
    - queue: 排队队列，使用Python列表实现FIFO
    - is_serving: 是否正在服务学生
    - current_student: 当前正在服务的学生对象
    - service_timer: 服务计时器（已服务的时间周期数）
    """

    def __init__(self, window_id: int, service_rate: float = 1.0):
        """
        初始化窗口对象

        参数：
        window_id: 窗口唯一标识
        service_rate: 服务速率，表示每个周期能服务的学生数量
                     实际实现中，service_rate可以影响服务时间
        """
        self.window_id = window_id
        self.service_rate = service_rate

        # 队列管理
        self.queue = []  # 排队队列，FIFO（先进先出）
        self.is_serving = False  # 是否正在服务
        self.current_student = None  # 当前服务的学生
        self.service_timer = 0  # 服务计时器

        # 统计信息
        self.served_count = 0  # 已服务学生数
        self.max_queue_length = 0  # 历史最大队列长度

    def add_student(self, student: Student) -> bool:
        """
        添加学生到队列

        参数：
        student: 要添加的学生对象

        返回：
        bool: 是否成功添加

        实现FIFO队列：学生添加到队列末尾。
        """
        # 检查学生是否有效
        if student is None:
            return False

        # 添加学生到队列末尾
        self.queue.append(student)

        # 更新最大队列长度统计
        if len(self.queue) > self.max_queue_length:
            self.max_queue_length = len(self.queue)

        print(f"窗口{self.window_id}：学生{student.student_id}加入队列，当前队列长度：{len(self.queue)}")
        return True

    def serve_next_student(self) -> bool:
        """
        服务队列中的下一个学生

        返回：
        bool: 是否成功开始服务新学生

        实现FIFO逻辑：从队列头部取出学生开始服务。
        如果窗口正在服务，需要先完成当前服务。
        """
        # 如果窗口正在服务，检查当前服务是否完成
        if self.is_serving:
            # 增加服务计时器
            self.service_timer += 1

            # 检查服务是否完成：服务时间 5-10 tick，配合 service_rate 微调
            if self.service_timer >= max(5, int(10 / max(self.service_rate, 0.1))):
                # 完成当前服务
                self.is_serving = False
                self.current_student = None
                self.service_timer = 0
                print(f"窗口{self.window_id}：完成当前服务")

        # 如果窗口空闲且队列不为空，开始服务下一个学生
        if not self.is_serving and len(self.queue) > 0:
            # 从队列头部取出学生（FIFO）
            student = self.queue.pop(0)

            # 开始服务该学生
            self.current_student = student
            self.is_serving = True
            self.service_timer = 0
            self.served_count += 1

            # 通知学生开始用餐
            student.start_eating()

            print(f"窗口{self.window_id}：开始服务学生{student.student_id}，队列剩余：{len(self.queue)}")
            return True

        return False

    def get_queue_length(self) -> int:
        """
        获取当前队列长度

        返回：
        int: 队列中的学生数量
        """
        return len(self.queue)

    def get_status(self) -> dict:
        """
        获取窗口当前状态信息

        返回：
        dict: 包含窗口状态信息的字典
        """
        return {
            'window_id': self.window_id,
            'queue_length': len(self.queue),
            'is_serving': self.is_serving,
            'current_student': self.current_student.student_id if self.current_student else None,
            'served_count': self.served_count,
            'max_queue_length': self.max_queue_length
        }


class Canteen:
    """
    食堂类 - 代表一个食堂实体

    职责：
    1. 管理多个服务窗口
    2. 协调学生分配到各个窗口
    3. 收集食堂级别的统计数据
    4. 提供食堂整体状态信息

    属性说明：
    - windows: 窗口列表，包含多个Window对象
    - capacity: 食堂总容量（最大同时容纳学生数）
    - total_queue_length: 所有窗口的总排队人数
    - served_count: 食堂总共服务的学生数
    - queue_history: 排队历史记录，用于统计和分析
    """

    def __init__(self, canteen_id: int, name: str, position: Tuple[float, float],
                 window_count: int = 5, capacity: int = 200,
                 doors: List[Tuple[float, float]] = None):
        """
        初始化食堂对象

        参数：
        canteen_id: 食堂唯一标识
        name: 食堂名称（如"四食堂"、"明湖食堂"）
        position: 食堂坐标(x, y)，使用真实地图坐标
        window_count: 窗口数量，默认5个
        capacity: 食堂总容量，默认200人
        doors: 门/入口位置列表 [(x,y), ...]，默认使用position作为唯一入口
        """
        self.canteen_id = canteen_id
        self.name = name
        self.position = position
        self.capacity = capacity
        self.doors = doors if doors else [position]  # 无门时回退到中心位置

        # 创建窗口
        self.windows = []
        for i in range(window_count):
            # 简单假设所有窗口服务速率相同，后续可扩展
            window = Window(window_id=i, service_rate=1.0)
            self.windows.append(window)

        # 统计信息
        self.total_queue_length = 0
        self.served_count = 0
        self.max_queue_length = 0
        self.queue_history = []  # 每周期的排队人数历史

        # 性能指标
        self.average_wait_time = 0.0
        self.utilization_rate = 0.0  # 利用率（服务时间/总时间）

    def add_student_to_queue(self, student: Student) -> bool:
        """
        将学生添加到食堂的某个窗口队列

        参数：
        student: 要添加的学生对象

        返回：
        bool: 是否成功添加到队列

        策略：选择当前队列最短的窗口。
        后续可扩展更复杂的分配策略。
        """
        # 检查食堂容量
        current_total = self.get_total_queue_length()
        if current_total >= self.capacity:
            print(f"食堂{self.name}（ID:{self.canteen_id}）容量已满，无法接受更多学生")
            return False

        # 选择队列最短的窗口
        target_window = self._find_shortest_queue_window()
        if target_window is None:
            return False

        # 添加学生到窗口队列
        success = target_window.add_student(student)
        if success:
            # 学生加入队列后，设置其目标食堂和窗口
            student.join_queue(self.canteen_id, target_window.window_id)

            # 更新食堂统计
            self.total_queue_length = self.get_total_queue_length()

            # 更新历史最大队列长度
            if self.total_queue_length > self.max_queue_length:
                self.max_queue_length = self.total_queue_length

        return success

    def _find_shortest_queue_window(self) -> Optional[Window]:
        """
        寻找队列最短的窗口（内部方法）

        返回：
        Optional[Window]: 队列最短的窗口，如果所有窗口都满则返回None

        用于将学生分配到最合适的窗口。
        """
        if not self.windows:
            return None

        # 初始化最短队列长度和对应窗口
        min_length = float('inf')
        target_window = None

        for window in self.windows:
            queue_length = window.get_queue_length()
            if queue_length < min_length:
                min_length = queue_length
                target_window = window

        return target_window

    def update_windows(self) -> None:
        """
        更新所有窗口状态

        每个仿真周期调用一次，驱动所有窗口的服务流程。
        包括：服务队列中的学生、更新窗口状态等。
        """
        # 更新每个窗口
        for window in self.windows:
            window.serve_next_student()

        # 更新食堂统计信息
        self._update_statistics()

    def _update_statistics(self) -> None:
        """
        更新食堂统计信息（内部方法）

        每个仿真周期调用，记录排队历史和其他统计指标。
        """
        # 记录当前排队人数到历史
        current_queue_length = self.get_total_queue_length()
        self.queue_history.append(current_queue_length)

        # 更新总排队人数
        self.total_queue_length = current_queue_length

        # 更新总服务人数
        total_served = sum(window.served_count for window in self.windows)
        self.served_count = total_served

        # 计算平均等待时间（简化实现）
        # 实际应根据学生的实际等待时间计算
        if self.served_count > 0 and len(self.queue_history) > 0:
            # 简单估算：平均排队长度 / 服务速率
            avg_queue_length = sum(self.queue_history) / len(self.queue_history)
            total_windows = len(self.windows)
            self.average_wait_time = avg_queue_length / total_windows if total_windows > 0 else 0

    def get_total_queue_length(self) -> int:
        """
        获取食堂总排队人数

        返回：
        int: 所有窗口的排队人数总和
        """
        total = 0
        for window in self.windows:
            total += window.get_queue_length()
        return total

    def get_nearest_door(self, pos: Tuple[float, float]) -> Tuple[float, float]:
        """返回离给定坐标最近的门位置"""
        best = self.position
        best_dist = float('inf')
        for door in self.doors:
            d = math.sqrt((pos[0] - door[0])**2 + (pos[1] - door[1])**2)
            if d < best_dist:
                best_dist = d
                best = door
        return best

    def get_window_count(self) -> int:
        """
        获取窗口数量

        返回：
        int: 窗口数量
        """
        return len(self.windows)

    def get_status(self) -> dict:
        """
        获取食堂当前状态信息

        返回：
        dict: 包含食堂状态信息的字典

        用于调试、统计和可视化。
        """
        window_statuses = [window.get_status() for window in self.windows]

        return {
            'canteen_id': self.canteen_id,
            'name': self.name,
            'position': self.position,
            'total_queue_length': self.total_queue_length,
            'max_queue_length': self.max_queue_length,
            'served_count': self.served_count,
            'window_count': len(self.windows),
            'average_wait_time': self.average_wait_time,
            'window_statuses': window_statuses
        }


# 可扩展性：食堂选择策略基类（预留接口）
class CanteenSelectionStrategy:
    """
    食堂选择策略基类

    采用策略模式，便于后续扩展多食堂选择算法。
    具体策略类应继承此类并实现select_canteen方法。
    """

    def select_canteen(self, student: Student, canteens: List[Canteen]) -> Optional[Canteen]:
        """
        选择食堂的策略方法

        参数：
        student: 需要选择食堂的学生
        canteens: 可用的食堂列表

        返回：
        Optional[Canteen]: 选择的食堂，如果无法选择则返回None

        子类必须实现此方法。
        """
        raise NotImplementedError("子类必须实现select_canteen方法")


# 示例策略：基于距离的选择策略
class DistanceBasedStrategy(CanteenSelectionStrategy):
    """
    基于距离的食堂选择策略

    选择距离学生最近的食堂。
    这是最简单的策略，可作为默认策略。
    """

    def select_canteen(self, student: Student, canteens: List[Canteen]) -> Optional[Canteen]:
        """选择最近的食堂"""
        if not canteens:
            return None

        min_distance = float('inf')
        selected_canteen = None

        for canteen in canteens:
            # 计算学生当前位置到食堂的距离
            distance = math.sqrt(
                (student.position[0] - canteen.position[0])**2 +
                (student.position[1] - canteen.position[1])**2
            )

            if distance < min_distance:
                min_distance = distance
                selected_canteen = canteen

        return selected_canteen


# 示例策略：基于排队人数的选择策略
class QueueAwareStrategy(CanteenSelectionStrategy):
    """
    基于排队人数的食堂选择策略

    综合考虑距离和排队人数，选择"最优"食堂。
    使用加权评分：score = 距离权重 × 距离 + 排队权重 × 排队人数
    """

    def __init__(self, distance_weight: float = 0.7, queue_weight: float = 0.3):
        """
        初始化策略

        参数：
        distance_weight: 距离权重（0-1）
        queue_weight: 排队人数权重（0-1）

        注意：权重之和应为1，但代码不强制要求。
        """
        self.distance_weight = distance_weight
        self.queue_weight = queue_weight

    def select_canteen(self, student: Student, canteens: List[Canteen]) -> Optional[Canteen]:
        """综合考虑距离和排队人数选择食堂"""
        if not canteens:
            return None

        best_score = float('inf')
        selected_canteen = None

        for canteen in canteens:
            # 计算距离
            distance = math.sqrt(
                (student.position[0] - canteen.position[0])**2 +
                (student.position[1] - canteen.position[1])**2
            )

            # 获取排队人数
            queue_length = canteen.get_total_queue_length()

            # 计算综合评分
            # 注意：距离和排队人数可能量纲不同，需要归一化处理
            # 这里简化处理，假设坐标范围和排队人数范围已知
            # 实际应用中可能需要更复杂的归一化
            score = (self.distance_weight * distance / 1000) + \
                    (self.queue_weight * queue_length / 50)

            if score < best_score:
                best_score = score
                selected_canteen = canteen

        return selected_canteen


# 测试代码（当模块直接运行时执行）
if __name__ == "__main__":
    print("models.py 模块测试")
    print("=" * 50)

    # 创建测试食堂
    canteen = Canteen(
        canteen_id=1,
        name="四食堂",
        position=(100.0, 200.0),
        window_count=3,
        capacity=100
    )

    # 创建测试学生
    student = Student(
        student_id=1,
        position=(50.0, 50.0),
        destination=(100.0, 200.0),
        speed=5.0,
        eating_time=5
    )

    print(f"食堂状态：{canteen.get_status()}")
    print(f"学生状态：{student.get_status()}")
    print("测试完成！")