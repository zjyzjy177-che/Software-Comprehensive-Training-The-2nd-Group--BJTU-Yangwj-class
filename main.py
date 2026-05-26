"""
主程序模块 - main.py

本模块是食堂就餐流量仿真系统的集成入口。
负责协调各个模块，提供命令行接口，并预留可视化模块和配置模块的调用接口。

主要功能：
1. 解析命令行参数或加载配置文件
2. 初始化仿真引擎（SimulationEngine）
3. 运行仿真（可选择完整运行或逐步运行）
4. 输出仿真结果（控制台、文件、图表等）
5. 提供可视化接口（预留visualizer.py调用）
6. 提供配置接口（预留config.py调用）

教育要点：
1. 模块集成：如何将多个模块组合成完整系统
2. 命令行接口：提供用户友好的命令行交互
3. 配置管理：支持多种配置方式（命令行、配置文件、默认值）
4. 接口设计：预留扩展接口，支持后续功能添加

注意：本模块设计为高度可扩展，方便后续添加GUI界面、Web接口等。
"""

import sys
import argparse
import json
import time
from typing import Dict, Any, Optional

# 导入核心模块
from engine import SimulationEngine
from config import BJTUConfig


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数

    返回：
    argparse.Namespace: 包含解析后的参数对象

    支持的命令行参数：
    --ticks: 仿真周期数
    --students: 初始学生数量
    --canteens: 食堂数量
    --spawn-rate: 学生生成速率
    --config: 配置文件路径
    --visualize: 启用可视化（预留）
    --output: 输出文件路径
    --quiet: 安静模式（减少输出）
    --test: 运行测试模式（少量周期）
    """
    parser = argparse.ArgumentParser(
        description="北京交通大学食堂就餐流量仿真系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python main.py                         # 使用默认配置运行仿真
  python main.py --ticks 500 --students 100  # 自定义参数
  python main.py --config my_config.json     # 从配置文件加载
  python main.py --test                     # 运行测试模式
  python main.py --visualize                # 启用可视化（预留）
        """
    )

    # 仿真参数
    parser.add_argument("--ticks", type=int, default=1000,
                       help="仿真周期数（默认：1000）")
    parser.add_argument("--students", type=int, default=100,
                       help="初始学生数量（默认：100）")
    parser.add_argument("--canteens", type=int, default=3,
                       help="食堂数量（默认：3）")
    parser.add_argument("--spawn-rate", type=float, default=0.1,
                       help="学生生成速率（默认：0.1）")

    # 文件参数
    parser.add_argument("--config", type=str,
                       help="配置文件路径（JSON格式）")
    parser.add_argument("--output", type=str, default="simulation_results.json",
                       help="输出文件路径（默认：simulation_results.json）")

    # 功能开关
    parser.add_argument("--visualize", action="store_true",
                       help="启用可视化（预留功能）")
    parser.add_argument("--quiet", action="store_true",
                       help="安静模式，减少控制台输出")
    parser.add_argument("--test", action="store_true",
                       help="测试模式，运行少量周期并输出详细信息")
    parser.add_argument("--benchmark", action="store_true",
                       help="性能测试模式，输出运行耗时")

    # 其他参数
    parser.add_argument("--seed", type=int,
                       help="随机种子（确保仿真可重复）")

    return parser.parse_args()


def load_config_file(config_path: str) -> Optional[Dict[str, Any]]:
    """
    从JSON文件加载配置

    参数：
    config_path: 配置文件路径

    返回：
    Optional[Dict[str, Any]]: 配置字典，如果加载失败则返回None

    配置文件格式示例：
    {
        "max_ticks": 1000,
        "student_count": 100,
        "canteen_count": 3,
        "spawn_rate": 0.1,
        "map_boundaries": [0, 0, 1000, 800],
        "canteen_positions": [[100, 200], [300, 400], [500, 600]],
        "enable_visualization": false,
        "random_seed": 42
    }
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"成功加载配置文件：{config_path}")
        return config
    except FileNotFoundError:
        print(f"错误：配置文件未找到：{config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"错误：配置文件格式无效：{e}")
        return None
    except Exception as e:
        print(f"错误：加载配置文件时发生未知错误：{e}")
        return None


def create_config_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    """
    从命令行参数创建配置字典

    使用 BJTUConfig（基于 campus_bounds.json 坐标）作为基础，
    然后用命令行参数覆盖。配置文件优先级最高（如果提供了--config参数）。

    参数：
    args: 解析后的命令行参数

    返回：
    Dict[str, Any]: 配置字典（由 BJTUConfig.get_simulation_config() 生成）
    """
    # 使用 BJTUConfig 加载 campus_bounds.json 坐标
    config_obj = BJTUConfig(config_file=args.config)

    # 用命令行参数覆盖默认值
    config_obj.simulation_params['max_ticks'] = args.ticks
    config_obj.simulation_params['student_count'] = args.students
    config_obj.simulation_params['canteen_count'] = args.canteens
    config_obj.simulation_params['spawn_rate'] = args.spawn_rate

    if args.seed is not None:
        config_obj.simulation_params['random_seed'] = args.seed

    config_obj.simulation_params['enable_visualization'] = args.visualize

    # 测试模式：快速验证
    if args.test:
        config_obj.simulation_params['max_ticks'] = 150
        config_obj.simulation_params['student_count'] = 30
        config_obj.simulation_params['canteen_count'] = 2
        config_obj.simulation_params['spawn_rate'] = 0.08
        print("测试模式：使用简化参数")

    if args.benchmark:
        config_obj.simulation_params['max_ticks'] = 500
        config_obj.simulation_params['student_count'] = 1000
        config_obj.simulation_params['canteen_count'] = 4
        config_obj.simulation_params['spawn_rate'] = 0.05
        config_obj.simulation_params['enable_visualization'] = False
        print("性能测试模式：1000人 × 500 ticks")

    # 生成引擎可用的配置字典
    config = config_obj.get_simulation_config()
    # 保留 config_obj 引用，供可视化使用
    config['_config_obj'] = config_obj

    return config


def save_results(engine: SimulationEngine, output_path: str) -> None:
    """
    保存仿真结果到文件

    参数：
    engine: 仿真引擎对象
    output_path: 输出文件路径

    保存格式：JSON，包含仿真统计数据和历史记录。
    文件可能较大，建议只保存关键数据或提供数据压缩选项。
    """
    try:
        # 准备结果数据
        results = {
            'metadata': {
                'simulation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                'total_ticks': engine.current_tick,
                'total_duration': engine.end_time - engine.start_time if engine.end_time else 0,
                'version': '1.0'
            },
            'global_statistics': engine.get_statistics(),
            'configuration': engine.config,
            'final_state': engine.get_current_state(),
            # 注意：tick_history可能非常大，实际使用时应考虑数据量
            # 'tick_history': engine.get_tick_history()  # 可选，数据量大时注释掉
        }

        # 保存到文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"仿真结果已保存到：{output_path}")

        # 同时保存简化的摘要信息
        summary_path = output_path.replace('.json', '_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(generate_summary_text(engine))

        print(f"仿真摘要已保存到：{summary_path}")

    except Exception as e:
        print(f"错误：保存结果时发生错误：{e}")


def generate_summary_text(engine: SimulationEngine) -> str:
    """
    生成文本格式的仿真摘要

    参数：
    engine: 仿真引擎对象

    返回：
    str: 格式化后的文本摘要

    用于生成人类可读的摘要报告。
    """
    stats = engine.get_statistics()
    state = engine.get_current_state()

    summary_lines = [
        "=" * 60,
        "北京交通大学食堂就餐流量仿真系统 - 仿真摘要",
        "=" * 60,
        f"仿真时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"仿真周期: {state['current_tick']}/{state['max_ticks']}",
        f"总耗时: {engine.end_time - engine.start_time:.2f}秒" if engine.end_time else "N/A",
        "",
        "全局统计:",
        f"  总生成学生数: {stats['total_students_generated']}",
        f"  总服务学生数: {stats['total_students_served']}",
        f"  最大排队人数: {stats['max_queue_length']}",
        f"  平均等待时间: {stats['average_wait_time']:.2f}周期",
        f"  总等待时间: {stats['total_wait_time']}周期",
        "",
        "学生状态分布:",
    ]

    # 添加学生状态统计
    if 'student_state_counts' in stats:
        state_counts = stats['student_state_counts']
        for state_name, count in state_counts.items():
            summary_lines.append(f"  {state_name}: {count}")

    summary_lines.append("")
    summary_lines.append("食堂统计:")

    # 添加食堂统计
    for canteen in engine.canteens:
        canteen_stats = canteen.get_status()
        summary_lines.append(
            f"  {canteen.name}: "
            f"服务{canteen_stats['served_count']}人, "
            f"最大排队{canteen_stats['max_queue_length']}人, "
            f"平均等待{canteen_stats['average_wait_time']:.2f}周期"
        )

    summary_lines.append("")
    summary_lines.append("配置参数:")
    for key, value in engine.config.items():
        summary_lines.append(f"  {key}: {value}")

    summary_lines.append("=" * 60)

    return "\n".join(summary_lines)


def run_simulation_from_gui(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    供 GUI 调用的仿真入口函数

    参数：
    config_dict: GUI 传来的配置字典，包含：
        - max_ticks, student_count, canteen_count, spawn_rate
        - 可选：algorithm_params (策略类型和权重)
        - 可选：enable_visualization

    返回：
    dict: 包含 statistics 和 summary 的字典，供 GUI 展示
        - success: bool
        - statistics: 仿真统计数据
        - summary: 文本摘要
        - error: 错误信息（仅失败时）
    """
    try:
        config = create_config_from_gui(config_dict)
        engine = run_simulation(config, quiet_mode=True)
        return {
            'success': True,
            'statistics': engine.get_statistics(),
            'summary': generate_summary_text(engine),
            'error': None,
            'engine': engine,
        }
    except Exception as e:
        import traceback
        return {
            'success': False,
            'statistics': None,
            'summary': None,
            'error': f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        }


def create_config_from_gui(gui_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 GUI 传来的参数转换为 engine 可用的配置字典

    参数：
    gui_config: GUI 传来的原始参数字典

    返回：
    Dict[str, Any]: engine 可用的配置字典
    """
    config_obj = BJTUConfig()

    # 如果 GUI 加载了 JSON 配置文件，用其中坐标覆盖 campus_bounds.json 默认值
    config_data = gui_config.get('_config_data')
    if config_data:
        if 'coordinates' in config_data:
            for name, coord in config_data['coordinates'].items():
                if isinstance(coord, list) and len(coord) == 2:
                    config_obj.coordinates[name] = tuple(coord)
        # 重新推导食堂位置（基于新坐标）
        config_obj.simulation_params['canteen_positions'] = config_obj._derive_canteen_positions()
        config_obj.simulation_params['canteen_count'] = gui_config.get('canteen_count',
                                            len(config_obj.simulation_params['canteen_positions']))

    # 参数校验
    max_ticks = gui_config.get('max_ticks', 150)
    canteen_count = gui_config.get('canteen_count', 2)
    spawn_rate = gui_config.get('spawn_rate', 0.08)

    if max_ticks <= 0:
        raise ValueError(f"max_ticks 必须大于 0，实际值: {max_ticks}")
    if canteen_count <= 0:
        raise ValueError(f"canteen_count 必须大于 0，实际值: {canteen_count}")
    if not (0 <= spawn_rate <= 1):
        raise ValueError(f"spawn_rate 必须在 [0, 1] 范围内，实际值: {spawn_rate}")

    config_obj.simulation_params['max_ticks'] = max_ticks
    config_obj.simulation_params['student_count'] = gui_config.get('student_count', 30)
    config_obj.simulation_params['canteen_count'] = canteen_count
    config_obj.simulation_params['spawn_rate'] = spawn_rate
    config_obj.simulation_params['enable_visualization'] = gui_config.get('enable_visualization', False)
    config_obj.simulation_params['lang'] = gui_config.get('lang', 'zh_CN')
    config_obj.simulation_params['sim_start_time'] = gui_config.get('sim_start_time', '07:00')
    config_obj.open_canteens = gui_config.get('open_canteens', [])

    if 'random_seed' in gui_config:
        config_obj.simulation_params['random_seed'] = gui_config['random_seed']

    if 'algorithm_params' in gui_config:
        config_obj.algorithm_params.update(gui_config['algorithm_params'])

    config = config_obj.get_simulation_config()
    config['_config_obj'] = config_obj
    config['open_canteens'] = getattr(config_obj, 'open_canteens', [])
    return config


def initialize_visualization(config: Dict[str, Any]):
    """
    初始化可视化模块

    参数：
    config: 配置字典（需包含 map_boundaries）

    返回：
    CanteenVisualizer: 可视化器实例，若失败则返回 None
    """
    try:
        from visualizer import CanteenVisualizer
        map_boundaries = config.get('map_boundaries', (-250, -400, 450, 200))
        lang = config.get('lang', 'zh_CN')
        sim_start = config.get('sim_start_time', '07:00')
        tick_sec = config.get('tick_duration_seconds', 60)
        road_segments = config.get('road_segments', [])
        visualizer = CanteenVisualizer(
            map_boundaries=tuple(map_boundaries), lang=lang,
            sim_start_time=sim_start, tick_duration_seconds=tick_sec,
            road_segments=road_segments
        )
        print("可视化模块初始化完成")
        return visualizer
    except ImportError:
        print("警告：可视化模块未找到，请确保 visualizer.py 存在")
        return None
    except Exception as e:
        print(f"警告：初始化可视化时发生错误：{e}")
        return None


def run_simulation(config: Dict[str, Any], quiet_mode: bool = False) -> SimulationEngine:
    """
    运行仿真（核心函数）

    参数：
    config: 配置字典（由 BJTUConfig.get_simulation_config() 生成）
    quiet_mode: 安静模式，减少控制台输出

    返回：
    SimulationEngine: 运行完成的仿真引擎对象

    两种运行模式：
    - 无可视化：调用 engine.run() 快速批量运行
    - 可视化模式：逐 tick 运行，通过 FuncAnimation 驱动更新
    """
    print("\n" + "=" * 60)
    print("北京交通大学食堂就餐流量仿真系统")
    print("=" * 60)

    print("初始化仿真引擎...")
    start_time = time.time()

    try:
        engine = SimulationEngine(config)
        init_time = time.time() - start_time
        print(f"仿真引擎初始化完成，耗时：{init_time:.2f}秒")

        enable_vis = config.get('enable_visualization', False)

        print("\n开始仿真运行...")
        print(f"最大周期数：{config['max_ticks']}")
        print(f"初始学生数：{config['student_count']}")
        print(f"食堂数量：{config['canteen_count']}")
        print("-" * 40)

        if enable_vis:
            # --- 可视化模式：逐 tick 运行 ---
            visualizer = initialize_visualization(config)
            if visualizer is None:
                print("可视化初始化失败，回退到无可视化模式")
                engine.run(verbose=not quiet_mode)
            else:
                engine.is_running = True
                engine.start_time = time.time()

                def update_frame():
                    """每帧动画回调：推进一个 tick 并返回当前状态"""
                    if engine.current_tick < engine.max_ticks:
                        engine.tick()
                    elif engine.is_running:
                        engine.end_time = time.time()
                        engine.is_running = False
                    return engine.current_tick, engine.active_students, engine.canteens

                def on_animation_done():
                    """动画结束后打印摘要"""
                    if not engine.end_time:
                        engine.end_time = time.time()
                    engine.print_summary()

                visualizer.start_animation(update_frame, interval=200)
                visualizer.show()
        else:
            # --- 无可视化模式：批量运行 ---
            engine.run(verbose=not quiet_mode)

        print("\n仿真运行完成！")
        return engine

    except KeyboardInterrupt:
        print("\n\n仿真被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误：仿真运行时发生错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main() -> None:
    """
    主函数 - 程序入口点

    执行流程：
    1. 解析命令行参数
    2. 加载配置（命令行参数 + 配置文件 + 默认值）
    3. 运行仿真
    4. 保存结果
    5. 显示摘要
    """
    # 解析命令行参数
    args = parse_arguments()

    # 加载配置
    config = None

    # 优先级1：配置文件（如果提供）
    if args.config:
        config = load_config_file(args.config)
        if config is None:
            print("错误：无法加载配置文件，退出程序")
            sys.exit(1)

    # 优先级2：命令行参数创建配置
    if config is None:
        config = create_config_from_args(args)

    # 确保配置有效
    if config is None:
        print("错误：配置创建失败，退出程序")
        sys.exit(1)

    # 运行仿真
    engine = run_simulation(config, quiet_mode=args.quiet)

    # 保存结果
    if not args.test:  # 测试模式不保存完整结果
        save_results(engine, args.output)

    # 显示摘要
    print("\n" + "=" * 60)
    print("仿真摘要")
    print("=" * 60)
    print(generate_summary_text(engine))

    # 测试模式额外信息
    if args.test:
        print("\n" + "=" * 60)
        print("测试模式额外信息")
        print("=" * 60)

        # 显示前几个Tick的历史数据
        print("\n前5个Tick的历史数据:")
        tick_history = engine.get_tick_history()
        for i, tick_data in enumerate(tick_history[:5]):
            print(f"Tick {tick_data['tick_number']}: "
                  f"活跃学生={tick_data['active_students']}, "
                  f"总排队={tick_data['total_queue_length']}")

        # 显示学生详细信息
        print("\n前10个学生的详细信息:")
        for i, student in enumerate(engine.students[:10]):
            status = student.get_status()
            print(f"学生{status['student_id']}: "
                  f"状态={status['state']}, "
                  f"等待时间={status['total_wait_time']}, "
                  f"用餐时间={status['total_eat_time']}")

        # 显示食堂详细信息
        print("\n所有食堂的详细信息:")
        for canteen in engine.canteens:
            stats = canteen.get_status()
            print(f"{canteen.name}: "
                  f"服务{stats['served_count']}人, "
                  f"窗口{stats['window_count']}个, "
                  f"最大排队{stats['max_queue_length']}人")

    print("\n仿真程序执行完成！")


# 预留配置模块接口
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置（使用 BJTUConfig，基于 campus_bounds.json）

    参数：
    config_path: 配置文件路径，如果为None则使用默认配置

    返回：
    Dict[str, Any]: 配置字典
    """
    config_obj = BJTUConfig(config_file=config_path)
    return config_obj.get_simulation_config()


def update_visualization(visualizer, tick: int, students, canteens) -> None:
    """
    更新可视化显示

    参数：
    visualizer: CanteenVisualizer 实例
    tick: 当前仿真周期
    students: 活跃学生列表
    canteens: 食堂列表
    """
    try:
        visualizer.draw_frame(tick, students, canteens)
    except Exception as e:
        print(f"可视化更新警告：{e}")


if __name__ == "__main__":
    main()