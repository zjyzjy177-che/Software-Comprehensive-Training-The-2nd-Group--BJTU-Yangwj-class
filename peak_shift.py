"""
错峰方案对比模块 - peak_shift.py

模拟不同下课时间差对食堂排队压力的影响。
gap_time=0  → 所有教学楼同时下课，集中涌向食堂（峰值最高）
gap_time>0  → 按建筑分批错开下课，学生分批到达（峰值降低）

核心机制：
  通过分批注入学生到 engine 来模拟错峰：
  - 无错峰：所有建筑学生同一 tick 注入
  - 错峰 N 分钟：按建筑人数权重分 4 波注入，间隔 N/4 tick

运行方式：
  python3 peak_shift.py                    # 默认对比
  python3 peak_shift.py --students 200
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any
from models import Student
from config import BJTUConfig

# 各建筑学生出发人数权重（反映实际规模差异）
BUILDING_WEIGHTS = {
    "思源楼": 1000, "思源西楼": 600, "思源东楼": 500,
    "逸夫楼": 800, "9教": 400, "7教＋5教": 350,
    "土木工程楼": 300, "电气工程楼": 250, "机械工程楼": 250,
    "16宿舍": 500, "嘉园": 600, "宿舍区": 400, "四号公寓": 350,
    "图书馆": 200, "科学会堂": 100, "校史馆": 50,
}


def _get_spawn_waves(total_students: int, gap_minutes: int, total_ticks: int) -> List[tuple]:
    """
    根据错峰时间生成分波方案
    返回: [(tick_offset, student_count), ...]
    """
    if gap_minutes == 0:
        # 无错峰：全部学生在 tick 0-3 集中释放
        return [(0, total_students)]

    # 错峰：分成 4 波，间隔 = gap_minutes 分钟映射的 tick 数
    # 假设 1 分钟 ≈ 2 tick, gap_minutes 分钟 → gap_ticks
    gap_ticks = gap_minutes * 2
    wave_interval = max(gap_ticks // 4, 3)

    # 按建筑权重分配人数：大教学楼多，小建筑少
    total_weight = sum(BUILDING_WEIGHTS.values())
    waves = []
    building_list = list(BUILDING_WEIGHTS.items())

    # 分 4 波，每波分配部分建筑
    buildings_per_wave = max(len(building_list) // 4, 1)
    assigned = 0
    for wave_idx in range(4):
        wave_buildings = building_list[wave_idx * buildings_per_wave:
                                       (wave_idx + 1) * buildings_per_wave]
        if not wave_buildings:
            wave_buildings = building_list[wave_idx * buildings_per_wave:]
        wave_weight = sum(w for _, w in wave_buildings)
        wave_students = int(total_students * wave_weight / total_weight)
        if wave_students > 0:
            tick = wave_idx * wave_interval
            waves.append((tick, wave_students))
        assigned += wave_students

    # 剩余未分配的学生补到最后一波
    remainder = total_students - assigned
    if remainder > 0 and waves:
        last_tick, last_count = waves[-1]
        waves[-1] = (last_tick, last_count + remainder)
    elif remainder > 0:
        waves.append((0, remainder))

    return waves


def run_staggered_simulation(gap_minutes: int, base_students: int = 200,
                             total_ticks: int = 300,
                             is_cancelled=None) -> Dict[str, Any]:
    """
    运行一次真错峰仿真：分批在不同 tick 注入学生

    is_cancelled: 可选回调 () -> bool，返回 True 时中止仿真
    """
    import random
    from engine import SimulationEngine

    cfg = BJTUConfig().get_simulation_config()
    cfg['max_ticks'] = total_ticks
    cfg['canteen_count'] = 3
    cfg['student_count'] = 0       # 不从 engine 自动生成
    cfg['spawn_rate'] = 0.0        # 关闭随机生成
    cfg['random_seed'] = 42 + gap_minutes  # 不同种子保持独立性

    random.seed(cfg['random_seed'])

    engine = SimulationEngine(cfg)

    # 计算分波方案
    waves = _get_spawn_waves(base_students, gap_minutes, total_ticks)
    pending_spawns = {}  # tick -> [positions]
    spawn_positions = cfg.get('spawn_positions', [(0, 0)])
    # 坐标→建筑名反向映射
    building_coords = cfg.get('building_coords', {})
    coord_to_name = {coord: name for name, coord in building_coords.items()}
    canteens = engine.canteens

    for tick_offset, count in waves:
        positions = []
        for _ in range(count):
            pos = tuple(random.choice(spawn_positions))
            positions.append(pos)
        pending_spawns[tick_offset] = positions

    # 运行仿真，在指定 tick 注入学生（每 tick 检查取消标志）
    student_id_counter = 0
    for tick in range(total_ticks):
        if is_cancelled and is_cancelled():
            return {'gap_minutes': gap_minutes, 'max_queue': 0, 'avg_wait': 0,
                    'total_served': 0, 'total_generated': 0, 'queue_history': [],
                    'cancelled': True}
        # 本 tick 该注入的学生
        if tick in pending_spawns:
            for pos in pending_spawns[tick]:
                target = None
                if canteens and engine.canteen_selector:
                    target = engine.canteen_selector.select_best_canteen(pos, canteens)
                if target is None and canteens:
                    target = random.choice(canteens)
                if target:
                    speed = random.uniform(*cfg.get('student_speed_range', (3.0, 15.0)))
                    eating_t = random.randint(*cfg.get('eating_time_range', (20, 60)))
                    s = Student(student_id=student_id_counter, position=pos,
                               destination=target.position, speed=speed, eating_time=eating_t,
                               origin_building=coord_to_name.get(pos, None))
                    s.target_canteen_id = target.canteen_id
                    engine.students.append(s)
                    engine.active_students.append(s)
                    engine.global_statistics['total_students_generated'] += 1
                    student_id_counter += 1

        if not engine.tick():
            break

    stats = engine.get_statistics()
    queue_history = [td.get('total_queue_length', 0) for td in engine.tick_history]

    return {
        'gap_minutes': gap_minutes,
        'max_queue': stats.get('max_queue_length', 0),
        'avg_wait': stats.get('average_wait_time', 0),
        'total_served': stats.get('total_students_served', 0),
        'total_generated': stats.get('total_students_generated', 0),
        'queue_history': queue_history,
    }


def run_comparison(gap_values: List[int], students: int = 200,
                   ticks: int = 300, verbose: bool = True) -> List[Dict]:
    results = []
    for gap in gap_values:
        label = "同时下课" if gap == 0 else f"错峰 {gap} 分钟"
        if verbose:
            print(f"  模拟: {label} ...", end=" ", flush=True)
        result = run_staggered_simulation(gap, students, ticks)
        results.append(result)
        if verbose:
            print(f"最大排队={result['max_queue']}, 平均等待={result['avg_wait']:.1f}")
    return results


def plot_comparison(results: List[Dict], output_prefix: str = "peak_shift"):
    try:
        plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'STHeiti',
                                            'SimHei', 'WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        pass

    gap_labels = [f"{r['gap_minutes']}min" if r['gap_minutes'] > 0 else "无错峰"
                  for r in results]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("错峰下课方案对比分析", fontsize=16, fontweight='bold')

    # 图1：最大排队柱状图
    ax1 = axes[0, 0]
    max_queues = [r['max_queue'] for r in results]
    colors = ['#E74C3C' if r['gap_minutes'] == 0 else '#3498DB' for r in results]
    bars = ax1.bar(gap_labels, max_queues, color=colors, edgecolor='black')
    ax1.set_title('最大排队人数对比')
    ax1.set_ylabel('最大排队人数')
    for bar, val in zip(bars, max_queues):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 str(val), ha='center', fontweight='bold')
    baseline = max_queues[0] if max_queues[0] > 0 else 1
    for i, val in enumerate(max_queues[1:], 1):
        reduction = (baseline - val) / baseline * 100
        if reduction > 0:
            ax1.annotate(f'↓{reduction:.0f}%', xy=(i, val),
                        xytext=(i, val + max(max_queues)*0.15),
                        ha='center', fontsize=9, color='green', fontweight='bold')

    # 图2：平均等待
    ax2 = axes[0, 1]
    avg_waits = [r['avg_wait'] for r in results]
    ax2.bar(gap_labels, avg_waits, color=colors, edgecolor='black')
    ax2.set_title('平均等待时间对比')
    ax2.set_ylabel('平均等待时间 (tick)')
    for i, val in enumerate(avg_waits):
        ax2.text(i, val + max(avg_waits)*0.02, f'{val:.1f}', ha='center', fontweight='bold')

    # 图3：排队曲线（全部显示）
    ax3 = axes[1, 0]
    for r in results:
        label = f"错峰{r['gap_minutes']}min" if r['gap_minutes'] > 0 else "无错峰(同时)"
        ax3.plot(r['queue_history'], label=label, linewidth=1.5, alpha=0.85)
    ax3.set_title('排队人数随时间变化')
    ax3.set_xlabel('仿真周期 (tick)')
    ax3.set_ylabel('排队人数')
    ax3.legend(fontsize=8)
    ax3.grid(True, linestyle='--', alpha=0.3)

    # 图4：服务对比
    ax4 = axes[1, 1]
    served = [r['total_served'] for r in results]
    generated = [r['total_generated'] for r in results]
    x = np.arange(len(gap_labels))
    width = 0.35
    ax4.bar(x - width/2, generated, width, label='总生成', color='#95A5A6', edgecolor='black')
    ax4.bar(x + width/2, served, width, label='已服务', color='#2ECC71', edgecolor='black')
    ax4.set_title('学生生成与服务对比')
    ax4.set_ylabel('学生数')
    ax4.set_xticks(x)
    ax4.set_xticklabels(gap_labels)
    ax4.legend()

    plt.tight_layout()
    filename = f"{output_prefix}_comparison.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n对比图表已保存: {filename}")
    plt.close()


def print_summary(results: List[Dict]):
    print("\n" + "=" * 70)
    print("  错峰下课方案对比 — 仿真结果汇总")
    print("=" * 70)
    print(f"{'方案':<14} {'最大排队':>8} {'平均等待':>8} {'服务人数':>8} {'排队峰降':>8}")
    print("-" * 70)
    baseline_queue = results[0]['max_queue'] if results else 1
    for r in results:
        label = "同时下课" if r['gap_minutes'] == 0 else f"错峰{r['gap_minutes']}分钟"
        reduction = (baseline_queue - r['max_queue']) / max(baseline_queue, 1) * 100
        red_str = f"↓{reduction:.0f}%" if r['gap_minutes'] > 0 and reduction > 0 else "-"
        print(f"{label:<14} {r['max_queue']:>8} {r['avg_wait']:>8.1f} {r['total_served']:>8} {red_str:>8}")
    print("-" * 70)

    best = min(results[1:], key=lambda r: r['max_queue'], default=results[0])
    if best['gap_minutes'] > 0:
        reduction = (baseline_queue - best['max_queue']) / max(baseline_queue, 1) * 100
        print(f"\n推荐方案：错峰 {best['gap_minutes']} 分钟")
        print(f"排队峰值降低 {reduction:.0f}%")
    print("=" * 70)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="BJTU食堂错峰下课方案对比")
    parser.add_argument("--students", type=int, default=200)
    parser.add_argument("--ticks", type=int, default=300)
    parser.add_argument("--gaps", type=str, default="0,5,10,15,20,30")
    parser.add_argument("--output", type=str, default="peak_shift")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()

    gap_values = [int(x.strip()) for x in args.gaps.split(",")]
    print(f"\n{'='*60}")
    print(f"  BJTU 食堂错峰下课方案对比（建筑分批注入模式）")
    print(f"{'='*60}")
    print(f"  学生总数: {args.students}  周期: {args.ticks}")
    print(f"  方案: {', '.join(f'{g}min' if g > 0 else '无错峰' for g in gap_values)}")

    results = run_comparison(gap_values, args.students, args.ticks)
    print_summary(results)
    if not args.no_plot:
        plot_comparison(results, args.output)
    print("\n分析完成。")


if __name__ == "__main__":
    main()
