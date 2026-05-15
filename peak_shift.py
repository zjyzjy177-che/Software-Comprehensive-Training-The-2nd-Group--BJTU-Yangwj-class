"""
错峰方案对比模块 - peak_shift.py

模拟不同下课时间差（gap_time）对食堂排队压力的影响。
通过调整不同教学楼的下课时间来错峰，对比排队峰值变化。

核心思路：
  gap_time=0  → 所有教学楼同时下课，学生集中涌向食堂（峰值最高）
  gap_time>0  → 各教学楼错开下课，学生分批到达（峰值降低）

运行方式：
  python3 peak_shift.py                    # 默认对比 0/5/10/15/20/30 分钟错峰
  python3 peak_shift.py --students 200     # 自定义学生数
  python3 peak_shift.py --output report    # 输出图表文件
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any
from engine import SimulationEngine
from config import BJTUConfig


def run_staggered_simulation(gap_minutes: int, base_students: int = 100,
                             total_ticks: int = 300) -> Dict[str, Any]:
    """
    运行一次错峰仿真

    参数：
    gap_minutes: 下课时间差（分钟），0 表示同时下课
    base_students: 基础学生数量
    total_ticks: 总仿真周期
    """
    cfg = BJTUConfig().get_simulation_config()
    cfg['max_ticks'] = total_ticks
    cfg['canteen_count'] = 3
    cfg['random_seed'] = 42

    if gap_minutes == 0:
        # 同时下课：大量学生一次性涌入
        cfg['student_count'] = base_students
        cfg['spawn_rate'] = 0.02  # 低持续生成，初始学生主导
    else:
        # 错峰下课：初始学生减少，分散在 gap 时间内逐步生成
        cfg['student_count'] = base_students // 3
        # gap 越大，生成越分散
        cfg['spawn_rate'] = max(0.03, base_students * 2 / total_ticks / max(gap_minutes / 10, 1))

    engine = SimulationEngine(cfg)
    # 批量运行，不打印每 tick 日志
    for _ in range(total_ticks):
        if not engine.tick():
            break

    stats = engine.get_statistics()
    # 收集排队历史
    queue_history = []
    for tick_data in engine.tick_history:
        queue_history.append(tick_data.get('total_queue_length', 0))

    return {
        'gap_minutes': gap_minutes,
        'max_queue': stats.get('max_queue_length', 0),
        'avg_wait': stats.get('average_wait_time', 0),
        'total_served': stats.get('total_students_served', 0),
        'total_generated': stats.get('total_students_generated', 0),
        'queue_history': queue_history,
    }


def run_comparison(gap_values: List[int], students: int = 100,
                   ticks: int = 300, verbose: bool = True) -> List[Dict]:
    """运行多组错峰对比"""
    results = []
    for gap in gap_values:
        if verbose:
            label = "同时下课" if gap == 0 else f"错峰 {gap} 分钟"
            print(f"  模拟: {label} ...", end=" ")
        result = run_staggered_simulation(gap, students, ticks)
        results.append(result)
        if verbose:
            print(f"最大排队={result['max_queue']}, 平均等待={result['avg_wait']:.1f}")
    return results


def plot_comparison(results: List[Dict], output_prefix: str = "peak_shift"):
    """生成对比图表"""
    # 解决中文字体
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

    # 图1：最大排队人数柱状图
    ax1 = axes[0, 0]
    max_queues = [r['max_queue'] for r in results]
    colors = ['#E74C3C' if r['gap_minutes'] == 0 else '#3498DB' for r in results]
    bars = ax1.bar(gap_labels, max_queues, color=colors, edgecolor='black')
    ax1.set_title('最大排队人数对比')
    ax1.set_ylabel('最大排队人数')
    ax1.set_xlabel('错峰方案')
    for bar, val in zip(bars, max_queues):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 str(val), ha='center', fontweight='bold')
    # 改善率标注
    baseline = max_queues[0] if max_queues[0] > 0 else 1
    for i, val in enumerate(max_queues[1:], 1):
        reduction = (baseline - val) / baseline * 100
        ax1.annotate(f'↓{reduction:.0f}%', xy=(i, val), xytext=(i, val + max(max_queues)*0.15),
                    ha='center', fontsize=9, color='green', fontweight='bold')

    # 图2：平均等待时间对比
    ax2 = axes[0, 1]
    avg_waits = [r['avg_wait'] for r in results]
    ax2.bar(gap_labels, avg_waits, color=colors, edgecolor='black')
    ax2.set_title('平均等待时间对比')
    ax2.set_ylabel('平均等待时间 (tick)')
    ax2.set_xlabel('错峰方案')
    for i, val in enumerate(avg_waits):
        ax2.text(i, val + max(avg_waits)*0.02, f'{val:.1f}', ha='center', fontweight='bold')

    # 图3：排队人数随时间变化曲线
    ax3 = axes[1, 0]
    for r in results:
        label = f"错峰{r['gap_minutes']}min" if r['gap_minutes'] > 0 else "无错峰(同时)"
        ax3.plot(r['queue_history'], label=label, linewidth=1.5, alpha=0.8)
    ax3.set_title('排队人数随时间变化')
    ax3.set_xlabel('仿真周期 (tick)')
    ax3.set_ylabel('排队人数')
    ax3.legend(fontsize=8)
    ax3.grid(True, linestyle='--', alpha=0.3)

    # 图4：总服务人数对比
    ax4 = axes[1, 1]
    served = [r['total_served'] for r in results]
    generated = [r['total_generated'] for r in results]
    x = np.arange(len(gap_labels))
    width = 0.35
    ax4.bar(x - width/2, generated, width, label='总生成', color='#95A5A6', edgecolor='black')
    ax4.bar(x + width/2, served, width, label='已服务', color='#2ECC71', edgecolor='black')
    ax4.set_title('学生生成与服务对比')
    ax4.set_ylabel('学生数')
    ax4.set_xlabel('错峰方案')
    ax4.set_xticks(x)
    ax4.set_xticklabels(gap_labels)
    ax4.legend()

    plt.tight_layout()
    filename = f"{output_prefix}_comparison.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n对比图表已保存: {filename}")
    plt.close()


def print_summary(results: List[Dict]):
    """打印文本摘要"""
    print("\n" + "=" * 70)
    print("  错峰下课方案对比 — 仿真结果汇总")
    print("=" * 70)
    print(f"{'方案':<16} {'最大排队':>8} {'平均等待':>10} {'服务人数':>8} {'排队峰降':>8}")
    print("-" * 70)

    baseline_queue = results[0]['max_queue'] if results else 1
    baseline_wait = results[0]['avg_wait'] if results else 1

    for r in results:
        label = "同时下课" if r['gap_minutes'] == 0 else f"错峰{r['gap_minutes']}分钟"
        q_reduction = (baseline_queue - r['max_queue']) / max(baseline_queue, 1) * 100
        reduction_str = f"↓{q_reduction:.0f}%" if r['gap_minutes'] > 0 and q_reduction > 0 else "-"
        print(f"{label:<16} {r['max_queue']:>8} {r['avg_wait']:>10.1f} {r['total_served']:>8} {reduction_str:>8}")

    print("-" * 70)

    # 最优推荐
    best = results[0]
    for r in results[1:]:
        if r['max_queue'] < best['max_queue']:
            best = r

    if best['gap_minutes'] > 0:
        reduction = (baseline_queue - best['max_queue']) / max(baseline_queue, 1) * 100
        print(f"\n推荐方案：错峰 {best['gap_minutes']} 分钟")
        print(f"排队峰值降低 {reduction:.0f}%，平均等待从 {baseline_wait:.1f} 降至 {best['avg_wait']:.1f} tick")
    print("=" * 70)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="BJTU食堂错峰下课方案对比")
    parser.add_argument("--students", type=int, default=100, help="基础学生数量（默认100）")
    parser.add_argument("--ticks", type=int, default=300, help="仿真周期数（默认300）")
    parser.add_argument("--gaps", type=str, default="0,5,10,15,20,30",
                        help="对比的错峰分钟数，逗号分隔（默认0,5,10,15,20,30）")
    parser.add_argument("--output", type=str, default="peak_shift",
                        help="输出图表文件名前缀（默认peak_shift）")
    parser.add_argument("--no-plot", action="store_true", help="不生成图表")
    args = parser.parse_args()

    gap_values = [int(x.strip()) for x in args.gaps.split(",")]

    print("\n" + "=" * 70)
    print("  BJTU 食堂错峰下课方案对比分析")
    print("=" * 70)
    print(f"  学生基数: {args.students}  仿真周期: {args.ticks}")
    print(f"  对比方案: {', '.join(f'{g}分钟' if g > 0 else '无错峰' for g in gap_values)}")
    print("-" * 70)

    # 运行对比
    print("\n[1/2] 运行对比仿真...")
    results = run_comparison(gap_values, args.students, args.ticks)

    # 打印摘要
    print_summary(results)

    # 生成图表
    if not args.no_plot:
        print("\n[2/2] 生成对比图表...")
        plot_comparison(results, args.output)

    print("\n分析完成。")


if __name__ == "__main__":
    main()
