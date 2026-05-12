"""
可视化模块 - visualizer.py

本模块实现食堂就餐流量仿真的动态可视化。
由组员C（UI/可视化）负责实现。

核心功能：
1. 2D平面动态渲染：显示学生移动和食堂位置
2. 实时统计图：排队人数曲线动态刷新
3. 跨平台字体适配：自动检测系统并加载中文字体
4. 交互控制：支持暂停、继续、速度调整
5. 性能优化：大数据量下的流畅渲染

教育要点：
1. Matplotlib动画：使用FuncAnimation实现动态更新
2. 多子图布局：同时显示地图和统计图表
3. 跨平台开发：处理不同操作系统的字体问题
4. 性能优化：增量更新、渲染优化技术

注意：必须确保在大数据量（1000+学生）下绘图不卡顿。
"""

import sys
import os
import platform
import time
import matplotlib

# ============================================================
# 关键：在 import pyplot 之前设置后端，否则动画无法工作
# ============================================================
_SYSTEM = platform.system()
if _SYSTEM == 'Darwin':
    matplotlib.use('TkAgg')  # 使用 TkAgg 与 Tkinter GUI 兼容，避免 MacOSX Cocoa 冲突
elif _SYSTEM == 'Windows':
    matplotlib.use('TkAgg')
else:
    # Linux：尝试 TkAgg，失败则回退 Agg
    try:
        matplotlib.use('TkAgg')
    except ImportError:
        matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from models import Student, Canteen, StudentState


class CanteenVisualizer:
    """
    食堂仿真可视化器

    职责：
    1. 初始化Matplotlib图形界面
    2. 绘制2D地图：学生（点）、食堂（矩形）、路径（线）
    3. 绘制实时统计图：排队人数曲线、状态分布饼图
    4. 处理用户交互：暂停、继续、速度控制
    5. 管理动画循环和性能优化

    设计原则：
    1. 模块化：地图绘制、统计绘制、交互控制分离
    2. 可配置：颜色、大小、布局参数可调整
    3. 高性能：增量更新，避免全量重绘
    4. 健壮性：处理各种边界情况和异常
    """

    def __init__(self, map_boundaries: Tuple[float, float, float, float] = (-250, -400, 450, 200),
                 title: str = "BJTU食堂就餐流量仿真"):
        """
        初始化可视化器

        参数：
        map_boundaries: 地图边界 (x_min, y_min, x_max, y_max)
        title: 窗口标题

        关键步骤：
        1. 配置Matplotlib参数（中文字体、DPI等）
        2. 创建图形窗口和子图布局
        3. 初始化图形元素（空集合）
        4. 设置交互控件和事件处理
        """
        # 地图边界
        self.x_min, self.y_min, self.x_max, self.y_max = map_boundaries
        self.map_width = self.x_max - self.x_min
        self.map_height = self.y_max - self.y_min

        # 图形状态
        self.fig = None
        self.ax_map = None          # 地图子图
        self.ax_stats = None        # 统计子图
        self.ax_pie = None          # 饼图子图
        self.animation = None       # 动画对象
        self.is_paused = False      # 暂停状态
        self.animation_speed = 200  # 动画速度（毫秒），默认较慢便于观察

        # 图形元素集合
        self.student_points = []    # 学生点对象
        self.canteen_rects = []     # 食堂矩形对象
        self.queue_bars = []        # 排队柱状图
        self.stat_lines = []        # 统计曲线
        self.text_labels = []       # 文本标签

        # 数据历史（用于统计图）
        self.tick_history = []      # 周期历史
        self.queue_history = []     # 排队人数历史
        self.wait_time_history = [] # 等待时间历史

        # 颜色配置
        self.colors = {
            'background': '#F5F5F5',
            'grid': '#CCCCCC',
            'student_walking': '#3498DB',    # 蓝色：行走
            'student_queuing': '#E74C3C',    # 红色：排队
            'student_eating': '#2ECC71',     # 绿色：用餐
            'student_leaving': '#9B59B6',    # 紫色：离开
            'canteen': '#F39C12',            # 橙色：食堂
            'canteen_busy': '#E67E22',       # 深橙色：繁忙食堂
            'text': '#2C3E50',               # 深灰色：文本
            'queue_bar': '#1ABC9C',          # 青色：排队柱状图
            'stat_line': '#E74C3C',          # 红色：统计曲线
        }

        # 尺寸配置
        self.point_size = 8         # 学生点大小
        self.canteen_size = 20      # 食堂标记大小
        self.font_size = 10         # 字体大小

        # 性能优化
        self.last_update_time = 0
        self.update_interval = 0.1  # 最小更新间隔（秒）
        self.max_history_length = 200  # 最大历史记录长度

        # 初始化Matplotlib
        self._setup_matplotlib()

        # 创建图形窗口
        self._create_figure(title)

        # 设置事件处理
        self._setup_events()

        print("可视化器初始化完成")
        print(f"地图范围: ({self.x_min}, {self.y_min}) - ({self.x_max}, {self.y_max})")
        print(f"系统平台: {platform.system()}")

    def _setup_matplotlib(self) -> None:
        """
        配置Matplotlib参数

        关键任务：
        1. 检测操作系统并加载中文字体
        2. 设置Matplotlib全局参数
        3. 配置后端（根据平台优化）

        跨平台字体适配：
        - Windows: 使用系统默认中文字体
        - macOS: 使用PingFang或系统字体
        - Linux: 使用文泉驿或系统字体
        """
        # 设置Matplotlib参数
        matplotlib.rcParams['figure.figsize'] = [14, 8]
        matplotlib.rcParams['figure.dpi'] = 100
        matplotlib.rcParams['savefig.dpi'] = 300
        matplotlib.rcParams['axes.titlesize'] = 12
        matplotlib.rcParams['axes.labelsize'] = 10
        matplotlib.rcParams['xtick.labelsize'] = 8
        matplotlib.rcParams['ytick.labelsize'] = 8

        # 检测操作系统并配置中文字体
        system = platform.system()
        font_path = None

        if system == 'Darwin':  # macOS
            # macOS常用中文字体
            font_candidates = [
                '/System/Library/Fonts/PingFang.ttc',      # PingFang
                '/System/Library/Fonts/STHeiti Light.ttc', # 黑体
                '/System/Library/Fonts/STHeiti Medium.ttc',
                '/Library/Fonts/Arial Unicode.ttf',        # Arial Unicode
            ]
        elif system == 'Windows':
            # Windows常用中文字体
            font_candidates = [
                'C:\\Windows\\Fonts\\msyh.ttc',           # 微软雅黑
                'C:\\Windows\\Fonts\\simhei.ttf',         # 黑体
                'C:\\Windows\\Fonts\\simsun.ttc',         # 宋体
            ]
        else:  # Linux及其他
            # Linux常用中文字体
            font_candidates = [
                '/usr/share/fonts/wenquanyi/wqy-microhei.ttc',  # 文泉驿微米黑
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            ]

        # 尝试加载字体
        for candidate in font_candidates:
            if os.path.exists(candidate):
                font_path = candidate
                break

        if font_path:
            try:
                # 添加字体到Matplotlib
                font_prop = fm.FontProperties(fname=font_path)
                matplotlib.rcParams['font.sans-serif'] = [font_prop.get_name()]
                matplotlib.rcParams['axes.unicode_minus'] = False
                print(f"成功加载中文字体: {font_path}")
            except Exception as e:
                print(f"警告：加载字体失败 {font_path}: {e}")
                print("将使用默认字体，中文可能显示为方框")
        else:
            print("警告：未找到中文字体，中文可能显示异常")
            print("请安装中文字体或指定字体路径")

        # 后端已在模块导入时设置（import pyplot 之前），此处无需再设

    def _create_figure(self, title: str) -> None:
        """
        创建图形窗口和子图布局

        参数：
        title: 窗口标题

        布局设计：
        左侧：2D地图（70%宽度）
        右侧：统计图表（30%宽度）
          上方：排队人数曲线
          下方：学生状态分布饼图
        """
        # 创建图形窗口
        self.fig = plt.figure(figsize=(14, 8), facecolor=self.colors['background'])
        self.fig.suptitle(title, fontsize=16, fontweight='bold', color=self.colors['text'])

        # 创建网格布局
        gs = self.fig.add_gridspec(2, 2, width_ratios=[7, 3], height_ratios=[7, 3],
                                  left=0.05, right=0.95, top=0.9, bottom=0.1,
                                  wspace=0.15, hspace=0.2)

        # 子图1：2D地图（左上，占大部分空间）
        self.ax_map = self.fig.add_subplot(gs[0, 0])
        self.ax_map.set_xlim(self.x_min - 10, self.x_max + 10)
        self.ax_map.set_ylim(self.y_min - 10, self.y_max + 10)
        self.ax_map.set_xlabel('X坐标 (米)', fontsize=10)
        self.ax_map.set_ylabel('Y坐标 (米)', fontsize=10)
        self.ax_map.set_title('学生移动与食堂分布', fontsize=12, fontweight='bold')
        self.ax_map.grid(True, linestyle='--', alpha=0.3, color=self.colors['grid'])
        self.ax_map.set_facecolor('#FFFFFF')

        # 加载真实校园底图图片（如有）
        try:
            import matplotlib.image as mpimg
            img_path = os.path.join(os.path.dirname(__file__), 'campus_map.png')
            if os.path.exists(img_path):
                img = mpimg.imread(img_path)
                self.ax_map.imshow(img, extent=[self.x_min, self.x_max, self.y_min, self.y_max], aspect='auto', alpha=0.6, zorder=0)
                print(f"已加载底图: {img_path}")
            else:
                print(f"未找到底图图片: {img_path}")
        except Exception as e:
            print(f"底图加载失败: {e}")

        # 设置等比例，确保地图不变形
        self.ax_map.set_aspect('equal', adjustable='box')

        # 子图2：排队人数曲线（右上）
        self.ax_stats = self.fig.add_subplot(gs[0, 1])
        self.ax_stats.set_xlabel('仿真周期', fontsize=9)
        self.ax_stats.set_ylabel('排队人数', fontsize=9)
        self.ax_stats.set_title('排队人数变化曲线', fontsize=11, fontweight='bold')
        self.ax_stats.grid(True, linestyle='--', alpha=0.3, color=self.colors['grid'])
        self.ax_stats.set_facecolor('#FFFFFF')

        # 子图3：学生状态分布饼图（右下）
        self.ax_pie = self.fig.add_subplot(gs[1, 1])
        self.ax_pie.set_title('学生状态分布', fontsize=11, fontweight='bold')
        self.ax_pie.set_facecolor('#FFFFFF')

        # 子图4：信息面板（左下）
        ax_info = self.fig.add_subplot(gs[1, 0])
        ax_info.axis('off')  # 不显示坐标轴

        # 添加信息文本（初始占位）
        self.info_text = ax_info.text(0.05, 0.95, '仿真信息加载中...',
                                     transform=ax_info.transAxes,
                                     fontsize=10, verticalalignment='top',
                                     color=self.colors['text'])

        # 添加图例（在地图子图上）
        self._add_legend()

        # 调整布局
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

    def _add_legend(self) -> None:
        """
        添加图例到地图子图

        显示学生状态颜色对应关系。
        使用自定义图例，避免与图形元素冲突。
        """
        # 创建图例元素
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.colors['student_walking'],
                      markersize=8, label='行走'),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.colors['student_queuing'],
                      markersize=8, label='排队'),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.colors['student_eating'],
                      markersize=8, label='用餐'),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.colors['student_leaving'],
                      markersize=8, label='离开'),
            plt.Line2D([0], [0], marker='s', color='w',
                      markerfacecolor=self.colors['canteen'],
                      markersize=10, label='食堂'),
        ]

        # 添加图例
        self.ax_map.legend(handles=legend_elements, loc='upper left',
                          fontsize=8, framealpha=0.9)

    def _setup_events(self) -> None:
        """
        设置交互事件处理

        支持功能：
        1. 空格键：暂停/继续动画
        2. 上/下键：调整动画速度
        3. 鼠标点击：显示详细信息
        4. 窗口关闭：清理资源
        """
        # 连接键盘事件
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)

        # 连接鼠标事件
        self.fig.canvas.mpl_connect('button_press_event', self._on_mouse_click)

        # 连接关闭事件
        self.fig.canvas.mpl_connect('close_event', self._on_close)

    def _on_key_press(self, event):
        """键盘事件处理"""
        if event.key == ' ':
            # 空格键：暂停/继续
            self.is_paused = not self.is_paused
            status = "暂停" if self.is_paused else "继续"
            print(f"动画{status}")
            self._update_info_text(f"动画状态: {status}")

        elif event.key == 'up':
            # 上箭头：加快速度
            self.animation_speed = max(10, self.animation_speed - 10)
            if self.animation:
                self.animation.event_source.interval = self.animation_speed
            print(f"动画速度: {self.animation_speed}ms")
            self._update_info_text(f"动画速度: {self.animation_speed}ms")

        elif event.key == 'down':
            # 下箭头：减慢速度
            self.animation_speed = min(500, self.animation_speed + 10)
            if self.animation:
                self.animation.event_source.interval = self.animation_speed
            print(f"动画速度: {self.animation_speed}ms")
            self._update_info_text(f"动画速度: {self.animation_speed}ms")

        elif event.key == 'r':
            # R键：重置视图
            self.ax_map.set_xlim(self.x_min - 10, self.x_max + 10)
            self.ax_map.set_ylim(self.y_min - 10, self.y_max + 10)
            self.fig.canvas.draw_idle()
            print("视图已重置")
            self._update_info_text("视图已重置")

    def _on_mouse_click(self, event):
        """鼠标点击事件处理"""
        if event.inaxes == self.ax_map:
            # 在地图子图上点击
            x, y = event.xdata, event.ydata
            print(f"点击坐标: ({x:.1f}, {y:.1f})")
            # 这里可以添加显示详细信息的功能

    def _on_close(self, event):
        """窗口关闭事件处理"""
        print("可视化窗口关闭，清理资源...")
        if self.animation:
            self.animation.event_source.stop()
        self.animation = None

    def _update_info_text(self, message: str) -> None:
        """
        更新信息面板文本

        参数：
        message: 要显示的信息

        用于显示实时状态和用户提示。
        """
        self.info_text.set_text(message)
        self.fig.canvas.draw_idle()

    def draw_frame(self, tick: int, students: List[Student], canteens: List[Canteen]) -> None:
        """
        绘制单帧画面（核心方法）

        参数：
        tick: 当前仿真周期
        students: 学生列表
        canteens: 食堂列表

        绘制内容：
        1. 清除上一帧的图形元素
        2. 绘制食堂位置和排队状态
        3. 绘制学生位置和状态（不同颜色）
        4. 更新统计图表
        5. 更新信息面板

        性能优化：
        1. 增量更新：只更新变化的元素
        2. 批处理：相似元素一起绘制
        3. 限制历史数据：避免内存溢出
        4. 节流更新：控制最小更新间隔
        """
        # 性能优化：控制更新频率
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval and len(students) > 100:
            return  # 跳过太快更新
        self.last_update_time = current_time

        # 清除上一帧的图形元素
        self._clear_frame()

        # 绘制食堂
        self._draw_canteens(canteens)

        # 绘制学生
        self._draw_students(students)

        # 更新统计图表
        self._update_statistics(tick, students, canteens)

        # 更新信息面板
        self._update_info_panel(tick, students, canteens)

        # 刷新画布
        self.fig.canvas.draw_idle()

    def _clear_frame(self) -> None:
        """清除上一帧的图形元素"""
        # 清除学生点
        for point in self.student_points:
            if point in self.ax_map.collections:
                point.remove()
        self.student_points.clear()

        # 清除食堂矩形
        for rect in self.canteen_rects:
            if rect in self.ax_map.patches:
                rect.remove()
        self.canteen_rects.clear()

        # 清除排队柱状图
        for bar in self.queue_bars:
            if bar in self.ax_map.patches:
                bar.remove()
        self.queue_bars.clear()

    def _draw_canteens(self, canteens: List[Canteen]) -> None:
        """
        绘制食堂位置和状态

        每个食堂显示为矩形，大小表示容量，颜色表示繁忙程度。
        排队人数用柱状图叠加显示。
        """
        for canteen in canteens:
            x, y = canteen.position
            queue_length = canteen.get_total_queue_length()
            capacity = canteen.capacity

            # 计算食堂繁忙程度（0-1）
            busyness = min(queue_length / max(capacity, 1), 1.0)

            # 选择颜色（根据繁忙程度）
            if busyness > 0.7:
                color = self.colors['canteen_busy']
            else:
                color = self.colors['canteen']

            # 绘制食堂矩形
            rect_size = self.canteen_size * (0.5 + 0.5 * busyness)
            rect = Rectangle((x - rect_size/2, y - rect_size/2),
                            rect_size, rect_size,
                            facecolor=color, edgecolor='black',
                            alpha=0.8, linewidth=1)
            self.ax_map.add_patch(rect)
            self.canteen_rects.append(rect)

            # 添加食堂名称标签
            label = self.ax_map.text(x, y + rect_size/2 + 5, canteen.name,
                                    fontsize=self.font_size - 2,
                                    ha='center', va='bottom',
                                    color=self.colors['text'])
            self.text_labels.append(label)

            # 绘制排队柱状图（在食堂上方）
            if queue_length > 0:
                bar_width = rect_size * 0.8
                bar_height = min(queue_length * 2, 50)  # 限制最大高度
                bar = Rectangle((x - bar_width/2, y + rect_size/2),
                               bar_width, bar_height,
                               facecolor=self.colors['queue_bar'],
                               edgecolor='black', alpha=0.7, linewidth=1)
                self.ax_map.add_patch(bar)
                self.queue_bars.append(bar)

                # 排队人数标签
                queue_text = self.ax_map.text(x, y + rect_size/2 + bar_height/2,
                                             str(queue_length),
                                             fontsize=self.font_size - 3,
                                             ha='center', va='center',
                                             color='white', fontweight='bold')
                self.text_labels.append(queue_text)

    def _draw_students(self, students: List[Student]) -> None:
        """
        绘制学生位置和状态

        不同状态使用不同颜色：
        - 行走：蓝色
        - 排队：红色
        - 用餐：绿色
        - 离开：紫色

        性能优化：使用散点图批处理绘制，而不是逐个绘制点。
        """
        # 按状态分组学生
        students_by_state = {
            StudentState.WALKING: [],
            StudentState.QUEUING: [],
            StudentState.EATING: [],
            StudentState.LEAVING: [],
        }

        for student in students:
            if student.state in students_by_state:
                students_by_state[student.state].append(student)

        # 按状态批处理绘制
        for state, student_list in students_by_state.items():
            if not student_list:
                continue

            # 获取颜色
            if state == StudentState.WALKING:
                color = self.colors['student_walking']
            elif state == StudentState.QUEUING:
                color = self.colors['student_queuing']
            elif state == StudentState.EATING:
                color = self.colors['student_eating']
            elif state == StudentState.LEAVING:
                color = self.colors['student_leaving']
            else:
                color = 'gray'

            # 提取坐标
            x_coords = [student.position[0] for student in student_list]
            y_coords = [student.position[1] for student in student_list]

            # 批量绘制点（性能优化）
            points = self.ax_map.scatter(x_coords, y_coords,
                                        s=self.point_size**2,
                                        c=color, alpha=0.8,
                                        edgecolors='black', linewidths=0.5)
            self.student_points.append(points)

        # 性能提示（当学生数量多时）
        if len(students) > 500:
            self.ax_map.set_title(f'学生移动与食堂分布 ({len(students)}名学生 - 性能优化模式)',
                                 fontsize=12, fontweight='bold')

    def _update_statistics(self, tick: int, students: List[Student], canteens: List[Canteen]) -> None:
        """
        更新统计图表

        包括：
        1. 排队人数历史曲线
        2. 学生状态分布饼图
        3. 其他统计信息
        """
        # 计算总排队人数
        total_queue = sum(canteen.get_total_queue_length() for canteen in canteens)

        # 记录历史数据
        self.tick_history.append(tick)
        self.queue_history.append(total_queue)

        # 限制历史数据长度（性能优化）
        if len(self.tick_history) > self.max_history_length:
            self.tick_history = self.tick_history[-self.max_history_length:]
            self.queue_history = self.queue_history[-self.max_history_length:]

        # 更新排队人数曲线
        self.ax_stats.clear()
        self.ax_stats.plot(self.tick_history, self.queue_history,
                          color=self.colors['stat_line'], linewidth=2)
        self.ax_stats.fill_between(self.tick_history, 0, self.queue_history,
                                  color=self.colors['stat_line'], alpha=0.3)
        self.ax_stats.set_xlabel('仿真周期', fontsize=9)
        self.ax_stats.set_ylabel('排队人数', fontsize=9)
        self.ax_stats.set_title(f'排队人数变化曲线 (当前: {total_queue}人)', fontsize=11, fontweight='bold')
        self.ax_stats.grid(True, linestyle='--', alpha=0.3, color=self.colors['grid'])
        self.ax_stats.set_facecolor('#FFFFFF')

        # 自动调整Y轴范围（留一些边距）
        if self.queue_history:
            max_queue = max(self.queue_history)
            self.ax_stats.set_ylim(0, max_queue * 1.1 + 1)

        # 更新学生状态分布饼图
        self._update_pie_chart(students)

    def _update_pie_chart(self, students: List[Student]) -> None:
        """
        更新学生状态分布饼图

        显示各状态学生的比例，使用对应颜色。
        """
        # 统计各状态学生数量
        state_counts = {
            '行走': 0,
            '排队': 0,
            '用餐': 0,
            '离开': 0,
        }

        for student in students:
            if student.state == StudentState.WALKING:
                state_counts['行走'] += 1
            elif student.state == StudentState.QUEUING:
                state_counts['排队'] += 1
            elif student.state == StudentState.EATING:
                state_counts['用餐'] += 1
            elif student.state == StudentState.LEAVING:
                state_counts['离开'] += 1

        # 过滤掉数量为0的状态
        labels = []
        sizes = []
        colors = []

        for label, count in state_counts.items():
            if count > 0:
                labels.append(label)
                sizes.append(count)

                # 根据状态选择颜色
                if label == '行走':
                    colors.append(self.colors['student_walking'])
                elif label == '排队':
                    colors.append(self.colors['student_queuing'])
                elif label == '用餐':
                    colors.append(self.colors['student_eating'])
                elif label == '离开':
                    colors.append(self.colors['student_leaving'])

        # 更新饼图
        self.ax_pie.clear()
        if sizes:
            self.ax_pie.pie(sizes, labels=labels, colors=colors,
                           autopct='%1.1f%%', startangle=90,
                           textprops={'fontsize': 9})
            self.ax_pie.set_title(f'学生状态分布 (总数: {len(students)})',
                                 fontsize=11, fontweight='bold')
        else:
            self.ax_pie.text(0.5, 0.5, '无学生数据',
                            ha='center', va='center',
                            fontsize=12, color=self.colors['text'])

        self.ax_pie.set_facecolor('#FFFFFF')

    def _update_info_panel(self, tick: int, students: List[Student], canteens: List[Canteen]) -> None:
        """
        更新信息面板

        显示实时仿真信息：
        - 当前周期
        - 学生总数和状态分布
        - 食堂排队情况
        - 性能指标
        """
        # 计算统计信息
        total_students = len(students)
        total_queue = sum(canteen.get_total_queue_length() for canteen in canteens)
        canteen_count = len(canteens)

        # 计算各状态学生数量
        walking_count = sum(1 for s in students if s.state == StudentState.WALKING)
        queuing_count = sum(1 for s in students if s.state == StudentState.QUEUING)
        eating_count = sum(1 for s in students if s.state == StudentState.EATING)
        leaving_count = sum(1 for s in students if s.state == StudentState.LEAVING)

        # 构建信息文本
        info_lines = [
            f"仿真周期: {tick}",
            f"学生总数: {total_students}",
            f"  行走: {walking_count} ({walking_count/total_students*100:.1f}%)",
            f"  排队: {queuing_count} ({queuing_count/total_students*100:.1f}%)",
            f"  用餐: {eating_count} ({eating_count/total_students*100:.1f}%)",
            f"  离开: {leaving_count} ({leaving_count/total_students*100:.1f}%)",
            f"食堂数量: {canteen_count}",
            f"总排队人数: {total_queue}",
            f"动画速度: {self.animation_speed}ms",
            f"动画状态: {'暂停' if self.is_paused else '运行'}",
        ]

        # 添加食堂详细信息（最多显示3个）
        info_lines.append("\n食堂排队情况:")
        for i, canteen in enumerate(canteens[:3]):
            queue_len = canteen.get_total_queue_length()
            capacity = canteen.capacity
            utilization = queue_len / max(capacity, 1) * 100
            info_lines.append(f"  {canteen.name}: {queue_len}/{capacity} ({utilization:.1f}%)")

        if len(canteens) > 3:
            info_lines.append(f"  ... 还有{len(canteens)-3}个食堂")

        # 更新信息文本
        info_text = "\n".join(info_lines)
        self.info_text.set_text(info_text)

    def start_animation(self, update_func, interval: int = 50) -> None:
        """
        启动动画

        参数：
        update_func: 更新函数，每个动画帧调用，返回(tick, students, canteens)
        interval: 动画间隔（毫秒），默认50ms

        使用Matplotlib的FuncAnimation实现动画循环。
        """
        # 包装更新函数，处理暂停状态
        def wrapped_update(frame):
            if not self.is_paused:
                tick, students, canteens = update_func()
                self.draw_frame(tick, students, canteens)
            return []

        # 创建动画
        self.animation = FuncAnimation(self.fig, wrapped_update,
                                      interval=interval,
                                      blit=False, cache_frame_data=False)

        # 设置动画速度
        self.animation_speed = interval

        print(f"动画已启动，间隔: {interval}ms")
        self._update_info_text(f"动画已启动，间隔: {interval}ms")

    def show(self) -> None:
        """显示图形窗口（阻塞模式）"""
        print("显示可视化窗口...")
        print("控制说明:")
        print("  空格键: 暂停/继续动画")
        print("  上箭头: 加快动画速度")
        print("  下箭头: 减慢动画速度")
        print("  R键: 重置视图")
        print("  关闭窗口: 退出可视化")

        try:
            plt.show()
        except KeyboardInterrupt:
            print("\n可视化被用户中断")
        except Exception as e:
            print(f"可视化错误: {e}")
        finally:
            self.close()

    def close(self) -> None:
        """关闭可视化窗口，清理资源"""
        if self.animation:
            self.animation.event_source.stop()
            self.animation = None

        plt.close('all')
        print("可视化窗口已关闭")

    def save_frame(self, filename: str = "simulation_frame.png") -> None:
        """
        保存当前帧为图片

        参数：
        filename: 输出文件名

        用于生成仿真截图或创建动画帧。
        """
        try:
            self.fig.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"帧已保存到: {filename}")
        except Exception as e:
            print(f"保存帧失败: {e}")


# 便捷函数：创建可视化器
def create_visualizer(map_boundaries: Tuple[float, float, float, float] = (-250, -400, 450, 200),
                     title: str = "BJTU食堂就餐流量仿真") -> CanteenVisualizer:
    """
    创建可视化器实例

    参数：
    map_boundaries: 地图边界
    title: 窗口标题

    返回：
    CanteenVisualizer: 可视化器对象
    """
    return CanteenVisualizer(map_boundaries, title)


# 测试代码（当模块直接运行时执行）
if __name__ == "__main__":
    print("visualizer.py 模块测试")
    print("=" * 50)

    # 创建测试数据
    from models import Student, Canteen, StudentState

    # 创建测试食堂（坐标来自 campus_bounds.json）
    canteens = [
        Canteen(canteen_id=1, name="四食堂", position=(250.0, -310.0), window_count=10, capacity=100),
        Canteen(canteen_id=2, name="一食堂", position=(160.0, 80.0), window_count=15, capacity=80),
        Canteen(canteen_id=3, name="学活食堂", position=(-180.0, 80.0), window_count=20, capacity=120),
    ]

    # 创建测试学生
    students = []
    canteen_positions = [(250.0, -310.0), (160.0, 80.0), (-180.0, 80.0)]
    for i in range(50):
        dest = canteen_positions[i % 3]
        student = Student(
            student_id=i,
            position=(np.random.uniform(-200, 400), np.random.uniform(-300, 150)),
            destination=dest,
            speed=np.random.uniform(1, 5)
        )
        # 随机分配状态
        states = [StudentState.WALKING, StudentState.QUEUING, StudentState.EATING, StudentState.LEAVING]
        student.state = np.random.choice(states, p=[0.6, 0.2, 0.1, 0.1])
        students.append(student)

    # 设置食堂排队人数（测试用）
    canteens[0].total_queue_length = 25
    canteens[1].total_queue_length = 15
    canteens[2].total_queue_length = 10

    # 创建可视化器
    visualizer = create_visualizer(title="BJTU食堂仿真测试")

    # 绘制单帧测试
    print("绘制测试帧...")
    visualizer.draw_frame(tick=1, students=students, canteens=canteens)

    # 保存测试帧
    visualizer.save_frame("test_frame.png")

    print("\n测试完成！")
    print("请检查 test_frame.png 文件查看可视化效果")

    # 注意：完整的动画测试需要与仿真引擎集成
    # 实际使用时，通过main.py的--visualize参数启用