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
"思源楼": (0.0, 0.0),
"思源西楼": (-50.0, 0.0),
"思源东楼": (50.0, 0.0),
"教4楼": (-50.0, -50.0),
"逸夫楼": (200.0, -50.0),
"7教＋5教": (50.0, -50.0),
"9教": (50.0, -100.0),
"土木工程楼": (250.0, -150.0),
"电气工程楼": (200.0, -100.0),
"机械工程楼": (300.0, -50.0),

# 宿舍楼
"16宿舍": (-150.0, 150.0),
"19宿舍": (-100.0, 100.0),
"四号公寓": (400.0, -300.0),
"宿舍区":(-100.0,0.0),
"嘉园": (50.0, -200.0),

# 食堂
"四食堂": (200.0, -150.0),
"一食堂":(150,150),
"留园": (200.0, -125.0),
"学活食堂":(-150,50),

# 其他关键地点
"图书馆": (150.0, 0.0),
"计算中心": (-50.0, 50.0),
"运动场":(200.0,0.0),
"运动场区":(-100,150),
"科学会堂": (50.0, 50.0),
"明湖": (100.0, 50.0),
"芳华园": (150.0, -50.0),
"学活": (-150.0, -50.0),
"天佑会堂": (-50.0, -100.0),
"红果园宾馆": (150.0, -125.0),
"东门": (350.0, 0.0),
"西门": (-200.0, 100.0),
"西北门": (-25.0, 150.0),
"南门": (0.0, -250.0)
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置

        参数：
        config_file: 配置文件路径，如果提供则从文件加载，否则使用默认配置

        配置优先级：文件配置 > 默认配置
        """
        # 建筑坐标
        self.coordinates = self.DEFAULT_COORDINATES.copy()

        # 仿真参数（与engine.py的SimulationEngine对齐）
        self.simulation_params = {
            'max_ticks': 1000,           # 最大仿真周期数
            'spawn_rate': 0.1,           # 学生生成速率
            'student_count': 100,        # 初始学生数量
            'canteen_count': 3,          # 食堂数量
            'map_boundaries': (0.0, 0.0, 1000.0, 800.0),  # 地图边界

            # 时间参数
            'gap_time': 15,              # 下课时间差（分钟）[关键参数]
            'class_start_time': '12:00', # 课程开始时间
            'class_end_time': '12:45',   # 课程结束时间

            # 食堂参数
            'canteen_positions': None,   # 食堂位置列表，None表示使用默认
            'window_counts': [5, 5, 5],  # 各食堂窗口数量
            'service_rates': [1.0, 1.0, 1.0],  # 各食堂服务速率

            # 学生参数
            'student_speed_range': (1.0, 5.0),  # 学生速度范围
            'eating_time_range': (5, 15),       # 用餐时间范围（周期数）

            # 其他参数
            'random_seed': None,         # 随机种子
            'enable_visualization': False,  # 是否启用可视化
            'output_file': 'simulation_results.json',  # 输出文件路径
        }

        # 算法参数（用于多食堂选择算法）
        self.algorithm_params = {
            'distance_weight': 0.7,      # 距离权重（α）
            'queue_weight': 0.3,         # 排队人数权重（β）
            'max_walk_distance': 500.0,  # 最大步行距离（米）
            'prefer_near_canteen': True, # 是否优先选择近的食堂
        }

        # 从文件加载配置（如果提供了配置文件）
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)

        # 验证配置
        self._validate_config()

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

        # 设置食堂位置（如果未指定，使用默认食堂位置）
        if config['canteen_positions'] is None:
            # 从坐标字典中提取食堂位置
            canteen_keys = [key for key in self.coordinates.keys() if '食堂' in key]
            canteen_positions = []
            for i in range(min(config['canteen_count'], len(canteen_keys))):
                pos = self.coordinates[canteen_keys[i]]
                canteen_positions.append(pos)
            config['canteen_positions'] = canteen_positions

        # 添加算法参数（供strategies.py使用）
        config['algorithm_params'] = self.algorithm_params

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