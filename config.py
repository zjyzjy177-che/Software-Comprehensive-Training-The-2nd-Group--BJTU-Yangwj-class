"""
配置模块 - config.py

本模块定义BJTU校园地图坐标和仿真配置参数。
由组员B（算法与数据）负责实现。

主要功能：
1. 定义BJTU关键建筑坐标字典（思源楼、12号楼、食堂等）
2. 提供配置管理类，支持动态修改参数
3. 支持从JSON文件加载和保存配置
4. 与engine.py的SimulationEngine接口对齐

教育要点：
1. 配置管理：集中管理仿真参数，便于调整和实验
2. 坐标系统：基于真实地图的坐标映射
3. 数据验证：确保配置参数的有效性和一致性

注意：所有坐标使用浮点数，单位为米，基于BJTU实际地图比例。
"""

import json
import os
from typing import Dict, List, Tuple, Any, Optional


class BJTUConfig:
    """
    BJTU仿真配置类

    管理所有仿真参数，包括：
    - 建筑坐标：教学楼、宿舍楼、食堂位置
    - 仿真参数：周期数、学生数量、生成速率等
    - 算法参数：食堂选择算法权重、下课时间差等

    设计原则：
    1. 单一数据源：所有配置集中管理
    2. 验证机制：参数设置时进行有效性检查
    3. 序列化：支持JSON格式保存和加载
    4. 默认值：提供合理的默认配置
    """

    # BJTU关键建筑坐标（示例坐标，需根据实际地图调整）
    # 坐标格式：(x, y)，单位：米，原点可自定义（如以思源楼为原点）
    DEFAULT_COORDINATES = {
  # 教学楼
"思源楼": (-25.0, -100.0),#2000人
"思源西楼": (-75.0, -100.0),#2000人
"思源东楼": (50.0, -100.0),#2000人
"校史馆": (-75.0, -150.0),#100人
"逸夫楼": (300.0, -175.0),#2000人
"7教＋5教": (75.0, -175.0),#300人
"9教": (75.0, -275.0),#300人
"土木工程楼": (350.0, -325.0),#1000人
"电气工程楼": (300.0, -200.0),#1000人
"机械工程楼": (380.0, -200.0),#1000人

# 宿舍楼
"16宿舍": (170.0, 110.0),#200人
"四号公寓": (250.0, -340.0),#700人
"宿舍区":(-130.0,-200.0),#3000人
"嘉园": (40.0, -350.0),#大概4000人

# 食堂
"四食堂": (222.0, -302.0),#500人
"一食堂":(144, 43),#600人
"留园": (262.0, -280.0),#200人
"学活食堂":(-175,-80),#1000人

# 其他关键地点
"图书馆": (175.0, 100.0),#200人
"计算中心": (-80.0, -80.0),#300人
"运动场":(260.0,100.0),#100人
"运动场区":(-150,50),#500人
"科学会堂": (50.0, -50.0),#300人
"明湖": (110.0, -70.0),#50人
"芳华园": (200.0, -180.0),#100人
"学活": (-200.0, -150.0),#200人
"天佑会堂": (-80.0, -220.0),#400人
"红果园宾馆": (170.0, -250.0),#150人
"东门": (400.0, -150.0),#500人
"西门": (-250.0, -20.0),#1000人
"西北门": (-45.0, 10.0),#500
"南门": (-10.0, -350.0)#1000人
# 道路
#1((-233,215),(0,-30))
#2((-158,-148),(0,-300))
#3((-115,-105),(0,-300))
#4((-158,-105),(-56,-73))
#4((-158,-105),(-99,-116))
#4((-158,420),(-134,-151))
#4((-158,-105),(-176,-195))
#4((-158,-105),(-212,-230))
#5((-52,-39),(84,-350))
#6((-115,-39),(-84,-94))
#6((-115,-39),(-180,-200))
#7((10,21),(0,-350))
#8((-52,21),(-62,-76))
#8((-52,21),(-127,-151))
#8((-52,21),(-237,-350))
#9((75,83),(0,-151))
#10((10,83),(-84,-95))
#11((116,133),(120,-314))
#12((10,133),(-224,-246))
#13((-52,214),(-292,-314))
#14((194,214),(0,-314))
#15((116,260),(-192,-205))
#16((197,420),(-241,-260))
#17((279,296),(-241,-352))
#18((334,359),(-134,-260))


#食堂门信息：
#学活（-187至-160，-33.5），（-160，-35.5至-81）
#一食堂（133，84至0）
#留园（215，-260至-291）
#四食堂（215，-291至-327），（278，-291至-327）
    }


    # 道路网络：矩形道路段 ((x_min,x_max),(y_min,y_max))
    ROAD_SEGMENTS = [
        ((-233, 215), (0, -30)),
        ((-158, -148), (0, -300)),
        ((-115, -105), (0, -300)),
        ((-158, -105), (-56, -73)),
        ((-158, -105), (-99, -116)),
        ((-158, 420), (-134, -151)),
        ((-158, -105), (-176, -195)),
        ((-158, -105), (-212, -230)),
        ((-52, -39), (84, -350)),
        ((-115, -39), (-84, -94)),
        ((-115, -39), (-180, -200)),
        ((10, 21), (0, -350)),
        ((-52, 21), (-62, -76)),
        ((-52, 21), (-127, -151)),
        ((-52, 21), (-237, -350)),
        ((75, 83), (0, -151)),
        ((10, 83), (-84, -95)),
        ((116, 133), (120, -314)),
        ((10, 133), (-224, -246)),
        ((-52, 214), (-292, -314)),
        ((194, 214), (0, -314)),
        ((116, 260), (-192, -205)),
        ((197, 420), (-241, -260)),
        ((279, 296), (-241, -352)),
        ((334, 359), (-134, -260)),
    ]

    # 食堂门/入口位置（学生从最近的门进入食堂）
    # 每个食堂2-4个门，分布在建筑各侧，确保与道路网络连通
    CANTEEN_DOORS = {
        "一食堂": [
            (136, 43),   # 西门 — 面向道路#11
            (144, 35),   # 北门
            (152, 43),   # 东门
        ],
        "留园": [
            (254, -280),  # 西门
            (270, -280),  # 东门
            (262, -290),  # 南门
        ],
        "四食堂": [
            (214, -302),  # 西门
            (230, -302),  # 东门
            (222, -294),  # 北门
        ],
        "学活食堂": [
            (-166, -80),  # 东门
            (-175, -72),  # 南门
            (-184, -80),  # 西门
        ],
    }

    # 各建筑人数权重（最大容量上限，实际生成按 student_count 比例缩放）
    # 权重用于课表驱动的学生生成分布：错峰时段6:3:1，共享时段等概率
    DEFAULT_BUILDING_WEIGHTS = {
        # 教学楼
        "思源楼": 2000,
        "思源西楼": 2000,
        "思源东楼": 2000,
        "校史馆": 100,
        "逸夫楼": 2000,
        "7教＋5教": 300,
        "9教": 300,
        "土木工程楼": 1000,
        "电气工程楼": 1000,
        "机械工程楼": 1000,
        # 宿舍楼
        "16宿舍": 200,
        "四号公寓": 700,
        "宿舍区": 3000,
        "嘉园": 4000,
        # 食堂
        "四食堂": 500,
        "一食堂": 600,
        "留园": 200,
        "学活食堂": 1000,
        # 其他关键地点
        "图书馆": 200,
        "计算中心": 300,
        "运动场": 100,
        "运动场区": 500,
        "科学会堂": 300,
        "明湖": 50,
        "芳华园": 100,
        "学活": 200,
        "天佑会堂": 400,
        "红果园宾馆": 150,
        "东门": 500,
        "西门": 1000,
        "西北门": 500,
        "南门": 1000,
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置

        参数：
        config_file: 配置文件路径，如果提供则从文件加载，否则使用默认配置

        坐标优先级：campus_bounds.json > DEFAULT_COORDINATES > 配置文件
        数据流：campus_bounds.json（唯一权威坐标源）→ config.py → engine.py → strategies.py/visualizer.py
        """
        # ============================================================
        # 第1步：从 campus_bounds.json 加载权威坐标（唯一坐标数据源）
        # ============================================================
        bounds_file = os.path.join(os.path.dirname(__file__), 'campus_bounds.json')
        self._loaded_bounds = None  # 保存从JSON加载的原始数据
        self.coordinates = {}

        if os.path.exists(bounds_file):
            try:
                with open(bounds_file, 'r', encoding='utf-8') as f:
                    campus_data = json.load(f)
                self._loaded_bounds = campus_data

                # 从JSON中提取所有建筑坐标
                # campus_bounds.json 格式为扁平字典: {"buildings": {"思源楼": [x, y], ...}}
                raw_buildings = campus_data.get('buildings', {})
                for name, info in raw_buildings.items():
                    # info 可能是 [x, y] 列表，直接转换
                    if isinstance(info, list) and len(info) == 2:
                        self.coordinates[name] = tuple(info)

                print(f"从 campus_bounds.json 加载了 {len(self.coordinates)} 个建筑坐标")
            except Exception as e:
                print(f"警告：加载 campus_bounds.json 失败: {e}，回退到 DEFAULT_COORDINATES")

        # 第2步：如果加载失败，使用 DEFAULT_COORDINATES 作为后备
        if not self.coordinates:
            self.coordinates = self.DEFAULT_COORDINATES.copy()
            print(f"使用 DEFAULT_COORDINATES 后备坐标（{len(self.coordinates)} 个建筑）")

        # ============================================================
        # 第3步：仿真参数（与engine.py的SimulationEngine对齐）
        # ============================================================
        self.simulation_params = {
            'max_ticks': 1000,           # 最大仿真周期数
            'spawn_rate': 0.1,           # 学生生成速率
            'student_count': 100,        # 初始学生数量
            'canteen_count': 4,          # 食堂数量
            'map_boundaries': tuple(campus_data.get('map_boundaries', [-250.0, -400.0, 450.0, 200.0]))
                if self._loaded_bounds
                else (-250.0, -400.0, 450.0, 200.0),

            # 时间参数
            'gap_time': 15,              # 下课时间差（分钟）[关键参数]
            'class_schedules': {
                '思源楼': [
                    {'start': '08:00', 'end': '09:50'},
                    {'start': '10:10', 'end': '12:00'},
                    {'start': '14:10', 'end': '16:00'},
                    {'start': '16:20', 'end': '18:10'},
                    {'start': '19:00', 'end': '20:50'},
                ],
                '逸夫楼': [
                    {'start': '08:00', 'end': '09:50'},
                    {'start': '10:30', 'end': '12:20'},
                    {'start': '14:10', 'end': '16:00'},
                    {'start': '16:20', 'end': '18:10'},
                    {'start': '19:00', 'end': '20:50'},
                ],
                '思源东楼': [
                    {'start': '08:00', 'end': '09:50'},
                    {'start': '10:30', 'end': '12:20'},
                    {'start': '14:10', 'end': '16:00'},
                    {'start': '16:20', 'end': '18:10'},
                    {'start': '19:00', 'end': '20:50'},
                ],
                '思源西楼': [
                    {'start': '08:00', 'end': '09:50'},
                    {'start': '10:30', 'end': '12:20'},
                ],
                '第九教学楼': [
                    {'start': '08:00', 'end': '09:50'},
                    {'start': '10:10', 'end': '12:00'},
                    {'start': '14:10', 'end': '16:00'},
                    {'start': '16:20', 'end': '18:10'},
                    {'start': '19:00', 'end': '20:50'},
                ],
                '土木工程楼': [
                    {'start': '08:00', 'end': '09:50'},
                    {'start': '10:10', 'end': '12:00'},
                    {'start': '14:10', 'end': '16:00'},
                    {'start': '16:20', 'end': '18:10'},
                    {'start': '19:00', 'end': '20:50'},
                ],
                '运动场': [
                    {'start': '08:00', 'end': '09:30'},
                    {'start': '10:10', 'end': '11:40'},
                    {'start': '14:10', 'end': '15:40'},
                    {'start': '16:20', 'end': '17:50'},
                    {'start': '19:00', 'end': '20:30'},
                ],
            },

            # 食堂参数 — 从 coordinates 字典中动态提取，确保与 campus_bounds.json 一致
            'canteen_positions': self._derive_canteen_positions(),
            'window_counts': [10, 15, 3, 20],
            'service_rates': [1.0, 1.0, 1.0, 1.0],

            # 学生参数（基于地图700m×600m，1 tick ≈ 若干秒）
            'student_speed_range': (3.0, 15.0),  # 学生速度范围（m/tick），300m需20-100tick到达
            'eating_time_range': (20, 60),       # 用餐时间范围（tick），足够长才会形成排队

            # 时间映射参数（将tick映射为实际时间，用于课表驱动）
            'sim_start_time': '07:00',          # 仿真开始时间（HH:MM格式）
            'tick_duration_seconds': 60,        # 每tick对应的实际秒数（60=1tick/分钟）
            'peak_hours': {                     # 就餐高峰期定义
                'lunch': ('11:30', '12:20'),    # 午餐高峰期
                'dinner': ('18:00', '19:00'),   # 晚餐高峰期
            },
            'class_end_burst_size': 120,
            'peak_spawn_multiplier': 2.0,
            # 食堂营业时间（24h制），非营业时段已有学生继续服务但不接收新生
            'canteen_hours': [
                {'start': '07:00', 'end': '09:00'},
                {'start': '11:30', 'end': '13:50'},
                {'start': '17:30', 'end': '19:00'},
                {'start': '21:00', 'end': '23:00'},
            ],

            # 其他参数
            'random_seed': None,         # 随机种子
            'enable_visualization': False,  # 是否启用可视化
            'output_file': 'simulation_results.json',  # 输出文件路径
        }

        # 算法参数（用于多食堂选择算法）
        self.algorithm_params = {
            'distance_weight': 0.3,      # 距离权重（α）
            'queue_weight': 0.7,         # 排队人数权重（β）
            'max_walk_distance': 1000.0,  # 最大步行距离（米）
            'prefer_near_canteen': True, # 是否优先选择近的食堂
        }

        # 第4步：外部配置文件覆盖（如果提供了 JSON 配置文件）
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)

        # 第5步：验证所有配置
        self._validate_config()

    def _derive_canteen_positions(self) -> List[Tuple[float, float]]:
        """
        从坐标字典中动态提取食堂位置（内部方法）

        遍历 self.coordinates，按名称关键词匹配食堂（'食堂' 或 '留园'），
        返回按 canteen_count 截断的位置列表。

        食堂数量不足 canteen_count 时用随机坐标补齐（不应发生）。

        返回：
        List[Tuple[float, float]]: 食堂位置列表，与 canteen_count 长度一致
        """
        # 候选食堂名称关键词
        canteen_keywords = ['食堂', '留园']
        positions = []
        for name, coord in self.coordinates.items():
            if any(kw in name for kw in canteen_keywords):
                positions.append(coord)
        return positions  # 返回全部食堂，由 engine 按 open_canteens 过滤

    def _validate_config(self) -> None:
        """
        验证配置参数的有效性

        确保所有参数在合理范围内，防止仿真错误。
        包括：坐标范围、参数类型、数值范围等。
        """
        # 验证坐标
        for name, coord in self.coordinates.items():
            if not isinstance(coord, tuple) or len(coord) != 2:
                raise ValueError(f"坐标格式错误：{name} = {coord}")
            x, y = coord
            if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                raise ValueError(f"坐标必须是数字类型：{name} = {coord}")

        # 验证仿真参数
        if self.simulation_params['max_ticks'] <= 0:
            raise ValueError("max_ticks必须大于0")
        if not (0 <= self.simulation_params['spawn_rate'] <= 1):
            raise ValueError("spawn_rate必须在0-1范围内")
        if self.simulation_params['student_count'] < 0:
            raise ValueError("student_count不能为负数")
        if self.simulation_params['canteen_count'] <= 0:
            raise ValueError("canteen_count必须大于0")
        if self.simulation_params['gap_time'] < 0:
            raise ValueError("gap_time不能为负数")

        # 验证算法参数
        weights_sum = (self.algorithm_params['distance_weight'] +
                      self.algorithm_params['queue_weight'])
        if abs(weights_sum - 1.0) > 0.001:  # 允许微小浮点误差
            print(f"警告：算法权重之和为{weights_sum:.3f}，建议调整为1.0")

        # 验证食堂位置（如果提供了自定义位置）
        canteen_positions = self.simulation_params['canteen_positions']
        if canteen_positions is not None:
            if len(canteen_positions) != self.simulation_params['canteen_count']:
                raise ValueError("食堂位置数量与canteen_count不匹配")
            for pos in canteen_positions:
                if not isinstance(pos, tuple) or len(pos) != 2:
                    raise ValueError(f"食堂位置格式错误：{pos}")

    def get_coordinate(self, building_name: str) -> Tuple[float, float]:
        """
        获取建筑坐标

        参数：
        building_name: 建筑名称

        返回：
        Tuple[float, float]: 建筑坐标(x, y)

        如果建筑不存在，抛出KeyError。
        """
        if building_name not in self.coordinates:
            raise KeyError(f"建筑'{building_name}'不在坐标字典中")
        return self.coordinates[building_name]

    def set_coordinate(self, building_name: str, coordinate: Tuple[float, float]) -> None:
        """
        设置建筑坐标

        参数：
        building_name: 建筑名称
        coordinate: 新坐标(x, y)

        可用于动态调整建筑位置。
        """
        if not isinstance(coordinate, tuple) or len(coordinate) != 2:
            raise ValueError("坐标必须是长度为2的元组")
        x, y = coordinate
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
            raise ValueError("坐标必须是数字类型")

        self.coordinates[building_name] = coordinate
        print(f"更新建筑坐标：{building_name} = {coordinate}")

    def get_simulation_config(self) -> Dict[str, Any]:
        """
        获取仿真配置字典

        返回：
        Dict[str, Any]: 仿真配置字典

        用于直接传递给SimulationEngine。
        格式与engine.py的create_default_config()对齐。
        """
        config = self.simulation_params.copy()

        # 添加算法参数（供strategies.py使用）
        config['algorithm_params'] = self.algorithm_params

        # 添加食堂名称（从 coordinates 中动态提取）
        canteen_keywords = ['食堂', '留园']
        canteen_names = []
        for name in self.coordinates:
            if any(kw in name for kw in canteen_keywords):
                canteen_names.append(name)
        config['canteen_names'] = canteen_names  # 不截断，由 engine 按 open_canteens 过滤

        # 添加学生生成位置（教学楼和宿舍楼坐标）
        spawn_building_keywords = ['教学楼', '教', '宿舍', '嘉园', '公寓', '楼']
        spawn_positions = []
        for name, coord in self.coordinates.items():
            if any(kw in name for kw in spawn_building_keywords) and name not in canteen_names:
                spawn_positions.append(coord)
        if not spawn_positions:
            spawn_positions = list(self.coordinates.values())
        config['spawn_positions'] = spawn_positions

        # 传递建筑名称→坐标映射，供 engine 按类型分类建筑
        config['building_coords'] = self.coordinates.copy()

        # 传递建筑权重（用于加权学生生成）
        config['building_weights'] = self.DEFAULT_BUILDING_WEIGHTS.copy()

        # 传递道路网络数据（用于道路约束的学生移动）
        config['road_segments'] = list(self.ROAD_SEGMENTS)

        # 传递食堂门位置（用于多入口路径规划）
        config['canteen_doors'] = {k: list(v) for k, v in self.CANTEEN_DOORS.items()}

        return config

    def update_gap_time(self, gap_time: int) -> None:
        """
        更新下课时间差参数

        参数：
        gap_time: 新的下课时间差（分钟）

        这是项目的关键参数，影响学生到达食堂的时间分布。
        """
        if gap_time < 0:
            raise ValueError("gap_time不能为负数")

        self.simulation_params['gap_time'] = gap_time
        print(f"更新下课时间差：{gap_time}分钟")

        # 根据时间差调整生成速率（示例逻辑，可自定义）
        # 时间差越大，生成速率应该更平缓
        if gap_time > 30:
            self.simulation_params['spawn_rate'] = 0.05  # 低生成速率
        elif gap_time > 15:
            self.simulation_params['spawn_rate'] = 0.1   # 中生成速率
        else:
            self.simulation_params['spawn_rate'] = 0.2   # 高生成速率

    def load_from_file(self, config_file: str) -> None:
        """
        从JSON文件加载配置

        参数：
        config_file: JSON配置文件路径

        文件格式示例：
        {
            "coordinates": {
                "思源楼": [100, 300],
                "四食堂": [300, 400],
                ...
            },
            "simulation_params": {
                "max_ticks": 1000,
                "gap_time": 15,
                ...
            },
            "algorithm_params": {
                "distance_weight": 0.7,
                ...
            }
        }
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载坐标
            if 'coordinates' in data:
                for key, value in data['coordinates'].items():
                    self.coordinates[key] = tuple(value)

            # 加载仿真参数
            if 'simulation_params' in data:
                self.simulation_params.update(data['simulation_params'])

            # 加载算法参数
            if 'algorithm_params' in data:
                self.algorithm_params.update(data['algorithm_params'])

            print(f"成功加载配置文件：{config_file}")

        except FileNotFoundError:
            print(f"警告：配置文件未找到：{config_file}")
        except json.JSONDecodeError as e:
            print(f"错误：配置文件格式无效：{e}")
        except Exception as e:
            print(f"错误：加载配置文件时发生错误：{e}")

    def save_to_file(self, config_file: str) -> None:
        """
        保存配置到JSON文件

        参数：
        config_file: 输出文件路径
        """
        try:
            data = {
                'coordinates': self.coordinates,
                'simulation_params': self.simulation_params,
                'algorithm_params': self.algorithm_params
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"配置已保存到：{config_file}")

        except Exception as e:
            print(f"错误：保存配置文件时发生错误：{e}")

    def print_summary(self) -> None:
        """打印配置摘要"""
        print("=" * 60)
        print("BJTU食堂仿真配置摘要")
        print("=" * 60)

        print(f"\n建筑坐标（共{len(self.coordinates)}个）：")
        for i, (name, coord) in enumerate(list(self.coordinates.items())[:5]):  # 只显示前5个
            print(f"  {name}: {coord}")
        if len(self.coordinates) > 5:
            print(f"  ... 还有{len(self.coordinates)-5}个建筑")

        print(f"\n关键仿真参数：")
        print(f"  最大周期数: {self.simulation_params['max_ticks']}")
        print(f"  初始学生数: {self.simulation_params['student_count']}")
        print(f"  食堂数量: {self.simulation_params['canteen_count']}")
        print(f"  生成速率: {self.simulation_params['spawn_rate']}")
        print(f"  下课时间差: {self.simulation_params['gap_time']}分钟")

        print(f"\n算法参数：")
        print(f"  距离权重: {self.algorithm_params['distance_weight']}")
        print(f"  排队权重: {self.algorithm_params['queue_weight']}")
        print(f"  最大步行距离: {self.algorithm_params['max_walk_distance']}米")

        print("=" * 60)


# 便捷函数：时间字符串转换
def time_str_to_minutes(time_str: str) -> int:
    """
    将 'HH:MM' 格式的时间字符串转换为从午夜开始的分钟数

    参数：
    time_str: 时间字符串，如 '08:00', '11:30'

    返回：
    int: 从00:00开始的分钟数
    """
    h, m = map(int, time_str.split(':'))
    return h * 60 + m


def classify_building(name: str) -> str:
    """
    根据建筑名称关键词分类建筑类型

    参数：
    name: 建筑名称

    返回：
    str: 'teaching' | 'dorm' | 'canteen' | 'other'
    """
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


# 便捷函数：创建默认配置
def create_default_config() -> BJTUConfig:
    """
    创建默认配置对象

    返回：
    BJTUConfig: 默认配置对象
    """
    return BJTUConfig()


# 测试代码（当模块直接运行时执行）
if __name__ == "__main__":
    print("config.py 模块测试")
    print("=" * 50)

    # 创建默认配置
    config = create_default_config()

    # 打印摘要
    config.print_summary()

    # 测试坐标获取
    try:
        coord = config.get_coordinate("思源楼")
        print(f"\n思源楼坐标：{coord}")
    except KeyError as e:
        print(f"\n错误：{e}")

    # 测试参数更新
    config.update_gap_time(20)
    print(f"\n更新后的生成速率：{config.simulation_params['spawn_rate']}")

    # 测试配置字典生成
    sim_config = config.get_simulation_config()
    print(f"\n仿真配置字典键数量：{len(sim_config)}")

    print("\n测试完成！")