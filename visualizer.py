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
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle, Polygon, Wedge
from matplotlib.lines import Line2D
import numpy as np
import math
from typing import List, Dict, Tuple, Any, Optional
from models import Student, Canteen, StudentState


# ====================== 图表文字三语翻译 ======================
_VIZ_TEXTS = {
    "zh_CN": {
        "window_title": "BJTU食堂就餐流量仿真",
        "map_title": "学生移动与食堂分布",
        "xlabel": "X坐标 (米)",
        "ylabel": "Y坐标 (米)",
        "stats_title": "排队人数变化曲线",
        "stats_xlabel": "仿真周期",
        "stats_ylabel": "排队人数",
        "pie_title": "学生状态分布",
        "pie_total": "总数",
        "info_loading": "仿真信息加载中...",
        "info_tick": "仿真周期",
        "info_students": "学生总数",
        "info_walking": "行走",
        "info_queuing": "排队",
        "info_eating": "用餐",
        "info_leaving": "离开",
        "info_canteens": "食堂数量",
        "info_queue": "总排队人数",
        "info_speed": "动画速度",
        "info_status": "动画状态",
        "info_running": "运行",
        "info_paused": "暂停",
        "canteen_header": "-- 食堂排队详情 --",
        "canteen_remaining": "还有{count}个食堂未显示",
        "legend_walking": "行走",
        "legend_queuing": "排队",
        "legend_eating": "用餐",
        "legend_leaving": "离开",
        "legend_canteen": "食堂",
        "no_students": "无学生数据",
        "perf_mode": "性能优化模式",
        "view_reset": "视图已重置",
    },
    "zh_TW": {
        "window_title": "BJTU食堂就餐流量模擬",
        "map_title": "學生移動與食堂分佈",
        "xlabel": "X坐標 (米)",
        "ylabel": "Y坐標 (米)",
        "stats_title": "排隊人數變化曲線",
        "stats_xlabel": "模擬週期",
        "stats_ylabel": "排隊人數",
        "pie_title": "學生狀態分佈",
        "pie_total": "總數",
        "info_loading": "模擬資訊加載中...",
        "info_tick": "模擬週期",
        "info_students": "學生總數",
        "info_walking": "行走",
        "info_queuing": "排隊",
        "info_eating": "用餐",
        "info_leaving": "離開",
        "info_canteens": "食堂數量",
        "info_queue": "總排隊人數",
        "info_speed": "動畫速度",
        "info_status": "動畫狀態",
        "info_running": "運行",
        "info_paused": "暫停",
        "canteen_header": "-- 食堂排隊詳情 --",
        "canteen_remaining": "還有{count}個食堂未顯示",
        "legend_walking": "行走",
        "legend_queuing": "排隊",
        "legend_eating": "用餐",
        "legend_leaving": "離開",
        "legend_canteen": "食堂",
        "no_students": "無學生数据",
        "perf_mode": "效能優化模式",
        "view_reset": "視圖已重置",
    },
    "en": {
        "window_title": "BJTU Canteen Dining Simulation",
        "map_title": "Student Movement & Canteen Distribution",
        "xlabel": "X Coordinate (m)",
        "ylabel": "Y Coordinate (m)",
        "stats_title": "Queue Length Over Time",
        "stats_xlabel": "Simulation Tick",
        "stats_ylabel": "Queue Length",
        "pie_title": "Student Status Distribution",
        "pie_total": "Total",
        "info_loading": "Loading simulation info...",
        "info_tick": "Simulation Tick",
        "info_students": "Total Students",
        "info_walking": "Walking",
        "info_queuing": "Queuing",
        "info_eating": "Eating",
        "info_leaving": "Leaving",
        "info_canteens": "Canteen Count",
        "info_queue": "Total Queue",
        "info_speed": "Anim Speed",
        "info_status": "Anim Status",
        "info_running": "Running",
        "info_paused": "Paused",
        "canteen_header": "-- Canteen Queue Details --",
        "canteen_remaining": "{count} more canteens not shown",
        "legend_walking": "Walking",
        "legend_queuing": "Queuing",
        "legend_eating": "Eating",
        "legend_leaving": "Leaving",
        "legend_canteen": "Canteen",
        "no_students": "No students",
        "perf_mode": "Performance Mode",
        "view_reset": "View Reset",
    },
}


def _viz_t(key, lang, **kwargs):
    """获取可视化图表文字"""
    text = _VIZ_TEXTS.get(lang, _VIZ_TEXTS["zh_CN"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


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
                 title: str = "BJTU食堂就餐流量仿真", lang: str = "zh_CN"):
        """
        初始化可视化器

        参数：
        map_boundaries: 地图边界 (x_min, y_min, x_max, y_max)
        title: 窗口标题
        lang: 语言代码 zh_CN / zh_TW / en

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

        # 语言
        self.lang = lang

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
        self.canteen_rects = []     # 食堂标记
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
            'student_walking': '#1E90FF',    # 亮蓝：行走
            'student_queuing': '#FF2D2D',    # 亮红：排队
            'student_eating': '#00E640',     # 亮绿：用餐
            'student_leaving': '#BF5FFF',    # 亮紫：离开
            'canteen': '#F39C12',            # 橙色：食堂
            'canteen_busy': '#E67E22',       # 深橙色：繁忙食堂
            'text': '#2C3E50',               # 深灰色：文本
            'queue_bar': '#1ABC9C',          # 青色：排队柱状图
            'stat_line': '#E74C3C',          # 红色：统计曲线
        }

        # 尺寸配置
        self.point_size = 5         # 学生点大小
        self.canteen_size = 20      # 食堂标记大小
        self.font_size = 10         # 字体大小

        # 性能优化
        self.last_update_time = 0
        self.update_interval = 0.1  # 最小更新间隔（秒）
        self.max_history_length = 200  # 最大历史记录长度

        # 地图缩放与拖动
        self.zoom_level = 1.0
        self.pan_x, self.pan_y = 0.0, 0.0
        self._drag_start = None
        self._view_mode = 0

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

        system = platform.system()
        if system == 'Darwin':
            _fonts = ['Microsoft YaHei', 'PingFang SC', 'Heiti SC', 'sans-serif']
        elif system == 'Windows':
            _fonts = ['Microsoft YaHei', 'SimHei', 'sans-serif']
        else:
            _fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'sans-serif']
        matplotlib.rcParams['font.sans-serif'] = _fonts
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.weight'] = 'bold'
        matplotlib.rcParams['axes.unicode_minus'] = False
        # 数字时钟用 Courier New
        matplotlib.rcParams['font.monospace'] = ['Courier New', 'Courier', 'monospace']

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
        self.fig.suptitle(_viz_t("window_title", self.lang), fontsize=16, fontweight='bold', color=self.colors['text'])

        # 背景底图（淡化为水印）
        try:
            bg_path = os.path.join(os.path.dirname(__file__), 'assets', 'SHIJIZHONG_BJTU.jpg')
            if os.path.exists(bg_path):
                bg_img = plt.imread(bg_path)
                bg_ax = self.fig.add_axes([0, 0, 1, 1], zorder=-100)
                bg_ax.imshow(bg_img, aspect='auto', alpha=0.22)
                bg_ax.axis('off')
        except Exception:
            pass

        # 创建网格布局：2×2 经典布局
        gs = self.fig.add_gridspec(2, 2, width_ratios=[7, 3], height_ratios=[7, 3],
                                  left=0.05, right=0.95, top=0.9, bottom=0.1,
                                  wspace=0.15, hspace=0.3)

        # 子图1：2D地图（左上，占大部分空间）
        self.ax_map = self.fig.add_subplot(gs[0, 0])
        self.ax_map.set_xlim(self.x_min - 10, self.x_max + 10)
        self.ax_map.set_ylim(self.y_min - 10, self.y_max + 10)
        self.ax_map.set_xlabel(_viz_t("xlabel", self.lang), fontsize=10)
        self.ax_map.set_ylabel(_viz_t("ylabel", self.lang), fontsize=10)
        self.ax_map.set_title(_viz_t("map_title", self.lang), fontsize=12, fontweight='bold')
        self.ax_map.grid(True, linestyle='--', alpha=0.3, color=self.colors['grid'])
        self.ax_map.set_facecolor('#FFFFFF')

        # 加载真实校园底图图片（如有）
        try:
            import matplotlib.image as mpimg
            img_path = os.path.join(os.path.dirname(__file__), 'assets', 'campus_map.png')
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
        self.ax_stats.set_xlabel(_viz_t("stats_xlabel", self.lang), fontsize=9)
        self.ax_stats.set_ylabel(_viz_t("stats_ylabel", self.lang), fontsize=9)
        self.ax_stats.set_title(_viz_t("stats_title", self.lang), fontsize=11, fontweight='bold')
        self.ax_stats.grid(True, linestyle='--', alpha=0.3, color=self.colors['grid'])
        self.ax_stats.set_facecolor('#FFFFFF')

        # 子图3：学生状态分布饼图（右下）
        self.ax_pie = self.fig.add_subplot(gs[1, 1])
        self.ax_pie.set_title(_viz_t("pie_title", self.lang), fontsize=11, fontweight='bold')
        self.ax_pie.set_facecolor('#FFFFFF')

        # 子图4：信息面板（左下 — 仿真数据 + 食堂排队详情，合并在一个 text 中）
        ax_info = self.fig.add_subplot(gs[1, 0])
        ax_info.axis('off')
        self.canteen_info_ax = ax_info  # 供视图切换引用

        self.info_text = ax_info.text(0.02, 0.98, _viz_t("info_loading", self.lang),
                                     transform=ax_info.transAxes,
                                     fontsize=8.5, verticalalignment='top',
                                     color=self.colors['text'])

        # 独立钟表 axes（图左上方）
        self.ax_clock = self.fig.add_axes([0.005, 0.87, 0.08, 0.10], facecolor='none')
        self.ax_clock.axis('off')

        self._popup_tab = None  # 详情弹窗已移除

        # 视图切换按钮（Figure 级别矩形块，标题栏下居中）
        self._toggle_buttons = []
        btn_names = ["地图", "折线图", "饼图", "综合"]
        btn_colors = ['#E74C3C', '#3498DB', '#2ECC71', '#95A5A6']
        for i, (name, color) in enumerate(zip(btn_names, btn_colors)):
            x0, y0 = 0.78 + i * 0.055, 0.95
            w, h = 0.048, 0.022
            rect = Rectangle((x0, y0), w, h, facecolor=color, edgecolor='white',
                            linewidth=1.5, transform=self.fig.transFigure, zorder=1000)
            self.fig.patches.append(rect)
            txt = self.fig.text(x0 + w/2, y0 + h/2, name, ha='center', va='center',
                               fontsize=8, fontweight='bold', color='white', zorder=1001)
            self._toggle_buttons.append((rect, txt, name))

        # 添加图例（在地图子图上）
        self._add_legend()

        # 调整布局
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

        # 保存原始位置供视图切换
        self._pos_map = self.ax_map.get_position()
        self._pos_stats = self.ax_stats.get_position()
        self._pos_pie = self.ax_pie.get_position()
        self._pos_info = ax_info.get_position()

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
                      markersize=8, label=_viz_t("legend_walking", self.lang)),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.colors['student_queuing'],
                      markersize=8, label=_viz_t("legend_queuing", self.lang)),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.colors['student_eating'],
                      markersize=8, label=_viz_t("legend_eating", self.lang)),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.colors['student_leaving'],
                      markersize=8, label=_viz_t("legend_leaving", self.lang)),
            plt.Line2D([0], [0], marker='^', color='w',
                      markerfacecolor='#FFD700', markeredgecolor='#CC9900',
                      markersize=10, label=_viz_t("legend_canteen", self.lang)),
        ]

        # 添加图例
        self.ax_map.legend(handles=legend_elements, loc='upper right',
                          fontsize=8, framealpha=0.9)

    def _setup_events(self) -> None:
        """设置交互事件：键盘 + 鼠标缩放/拖动 + 视图切换"""
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)
        self.fig.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.fig.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.fig.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.fig.canvas.mpl_connect('close_event', self._on_close)

    def _on_key_press(self, event):
        """键盘事件处理"""
        if event.key == ' ':
            # 空格键：暂停/继续
            self.is_paused = not self.is_paused
            status = _viz_t("info_paused", self.lang) if self.is_paused else _viz_t("info_running", self.lang)
            self._update_info_text(f"{_viz_t('info_status', self.lang)}: {status}")

        elif event.key == 'up':
            # 上箭头：加快速度
            self.animation_speed = max(10, self.animation_speed - 10)
            if self.animation:
                self.animation.event_source.interval = self.animation_speed
            self._update_info_text(f"{_viz_t('info_speed', self.lang)}: {self.animation_speed}ms")

        elif event.key == 'down':
            # 下箭头：减慢速度
            self.animation_speed = min(500, self.animation_speed + 10)
            if self.animation:
                self.animation.event_source.interval = self.animation_speed
            self._update_info_text(f"{_viz_t('info_speed', self.lang)}: {self.animation_speed}ms")

        elif event.key == 'r':
            # R键：重置视图 + 缩放
            self.zoom_level = 1.0
            self.pan_x, self.pan_y = 0.0, 0.0
            self._apply_map_view()
            self._update_info_text(_viz_t("view_reset", self.lang))

        elif event.key == 'v':
            # V键：切换视图模式 0→1→2→0
            self._view_mode = (self._view_mode + 1) % 3
            modes = ["合并视图", "纯地图", "纯图表"]
            self._update_info_text(f"视图: {modes[self._view_mode]}")
            self._apply_view_mode()

    # ---------- 鼠标缩放/拖动 ----------
    def _on_scroll(self, event):
        if event.inaxes == self.ax_map:
            if event.button == 'up':
                self.zoom_level = min(self.zoom_level * 1.15, 5.0)
            else:
                self.zoom_level = max(self.zoom_level / 1.15, 0.3)
            self._apply_map_view()

    def _on_mouse_press(self, event):
        if event.inaxes == self.ax_map and event.button == 1:
            self._drag_start = (event.xdata, event.ydata)
        elif event.button == 1:
            fx, fy = event.x / self.fig.bbox.width, event.y / self.fig.bbox.height
            # 视图切换按钮
            for rect, txt, name in self._toggle_buttons:
                x0, y0 = rect.get_x(), rect.get_y()
                w, h = rect.get_width(), rect.get_height()
                if x0 <= fx <= x0 + w and y0 <= fy <= y0 + h:
                    self._switch_to_view(name)
                    return

    def _on_mouse_release(self, event):
        self._drag_start = None

    def _on_mouse_move(self, event):
        if self._drag_start and event.inaxes == self.ax_map and event.xdata and event.ydata:
            dx = self._drag_start[0] - event.xdata
            dy = self._drag_start[1] - event.ydata
            self.pan_x += dx
            self.pan_y += dy
            self._drag_start = (event.xdata, event.ydata)
            self._apply_map_view()

    def _apply_map_view(self):
        """更新地图范围，先清旧标签再刷新（防拖动穿模）"""
        hw = (self.map_width / self.zoom_level) / 2
        hh = (self.map_height / self.zoom_level) / 2
        cx = (self.x_min + self.x_max) / 2 + self.pan_x
        cy = (self.y_min + self.y_max) / 2 + self.pan_y
        self.ax_map.set_xlim(cx - hw, cx + hw)
        self.ax_map.set_ylim(cy - hh, cy + hh)
        self.fig.canvas.draw_idle()

    def _apply_view_mode(self):
        """切换视图布局：0=合并 1=纯地图全屏 2=纯图�表全屏"""
        if self._view_mode == 0:
            # 合并视图：恢复原始 GridSpec 位置
            self.ax_map.set_position(self._pos_map)
            self.ax_stats.set_position(self._pos_stats)
            self.ax_pie.set_position(self._pos_pie)
            self.canteen_info_ax.set_position(self._pos_info)
            for ax in [self.ax_map, self.ax_stats, self.ax_pie, self.canteen_info_ax]:
                ax.set_visible(True)
        elif self._view_mode == 1:
            # 纯地图：地图占满整图
            self.ax_map.set_position([0.05, 0.1, 0.90, 0.78])
            self.ax_map.set_visible(True)
            self.ax_stats.set_visible(False)
            self.ax_pie.set_visible(False)
            self.canteen_info_ax.set_visible(False)
        elif self._view_mode == 2:
            # 纯图表：统计图上，饼图+信息下
            self.ax_map.set_visible(False)
            self.canteen_info_ax.set_visible(False)
            self.ax_stats.set_position([0.08, 0.52, 0.86, 0.36])
            self.ax_pie.set_position([0.08, 0.08, 0.40, 0.38])
            self.ax_stats.set_visible(True)
            self.ax_pie.set_visible(True)
        self.fig.canvas.draw_idle()

    def _switch_to_view(self, name):
        """切换到指定视图：地图全屏 / 折线图全屏 / 饼图全屏 / 综合"""
        all_axes = [self.ax_map, self.ax_stats, self.ax_pie, self.canteen_info_ax]
        for ax in all_axes:
            ax.set_visible(False)

        if name == "地图":
            self.ax_map.set_position([0.05, 0.1, 0.90, 0.78])
            self.ax_map.set_visible(True)
        elif name == "折线图":
            self.ax_stats.set_position([0.10, 0.18, 0.80, 0.62])
            self.ax_stats.set_visible(True)
        elif name == "饼图":
            self.ax_pie.set_position([0.15, 0.15, 0.70, 0.70])
            self.ax_pie.set_visible(True)
        else:  # 综合
            self.ax_map.set_position(self._pos_map)
            self.ax_stats.set_position(self._pos_stats)
            self.ax_pie.set_position(self._pos_pie)
            self.canteen_info_ax.set_position(self._pos_info)
            for ax in all_axes:
                ax.set_visible(True)

        self._update_toggle_buttons()
        self.fig.canvas.draw_idle()

    def _update_toggle_buttons(self):
        """根据当前可见面板高亮对应按钮"""
        for rect, txt, name in self._toggle_buttons:
            if name == "地图":
                active = self.ax_map.get_visible()
            elif name == "折线图":
                active = self.ax_stats.get_visible()
            elif name == "饼图":
                active = self.ax_pie.get_visible()
            else:
                active = all(a.get_visible() for a in [self.ax_map, self.ax_stats, self.ax_pie])
            rect.set_edgecolor('#FFD700' if active else 'white')
            rect.set_linewidth(3 if active else 1.5)

    def _on_mouse_click(self, event):
        pass

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

    def _draw_canteen_bars(self, canteens, lang):
        """在信息面板绘制横向进度条 + 弹窗内显示全量详情"""
        ax = self.canteen_info_ax
        # 清除旧的 bar patches（只清我们画的 bar，不清 text）
        for p in getattr(self, '_bar_patches', []):
            p.remove()
        for t in getattr(self, '_bar_texts', []):
            t.remove()
        self._bar_patches = []
        self._bar_texts = []

        max_show = 5
        bar_h = 0.045
        start_y = 0.55
        gap = 0.045

        ax.text(0.02, start_y + 0.02, _viz_t("canteen_header", lang),
                transform=ax.transAxes, fontsize=10, fontweight='bold',
                color='#8B0000', va='bottom')

        for i, canteen in enumerate(canteens[:max_show]):
            y0 = start_y - (i + 1) * (bar_h + gap) - 0.02
            if y0 < 0.02:
                break
            queue_len = canteen.get_total_queue_length()
            capacity = canteen.capacity
            ratio = min(queue_len / max(capacity, 1), 1.0)

            # 名称
            t = ax.text(0.02, y0 + bar_h/2, canteen.name, transform=ax.transAxes,
                       fontsize=9, va='center', color='#333333', fontweight='bold')
            self._bar_texts.append(t)

            # 进度条背景（粉色框）
            bar_x, bar_w = 0.22, 0.42
            bg = Rectangle((bar_x, y0), bar_w, bar_h, facecolor='none',
                          edgecolor='#FF69B4', linewidth=1.2,
                          transform=ax.transAxes)
            ax.add_patch(bg)
            self._bar_patches.append(bg)

            # 填充（蓝色）
            fill = Rectangle((bar_x, y0), bar_w * ratio, bar_h,
                            facecolor='#5DADE2', edgecolor='none',
                            alpha=0.85, transform=ax.transAxes)
            ax.add_patch(fill)
            self._bar_patches.append(fill)

            # 数字（大红色加粗）
            t2 = ax.text(bar_x + bar_w + 0.02, y0 + bar_h/2,
                        str(queue_len), transform=ax.transAxes,
                        fontsize=11, fontweight='bold', color='#CC0000', va='center')
            self._bar_texts.append(t2)

        if len(canteens) > max_show:
            t = ax.text(0.02, 0.01,
                       _viz_t("canteen_remaining", lang, count=len(canteens) - max_show),
                       transform=ax.transAxes, fontsize=9, color='#999999')
            self._bar_texts.append(t)

    def _draw_clock(self, tick: int):
        """在独立 axes 上绘制粉色模拟钟表 + 数字时钟"""
        self.ax_clock.clear()
        self.ax_clock.axis('off')
        # axes 坐标 (0-1)，中心在 (0.5, 0.5)，r=0.42
        cx, cy, r = 0.5, 0.5, 0.42

        # 粉色方形钟面 + 钟面数字
        sq = Rectangle((cx - r, cy - r), r * 2, r * 2, facecolor='#FFF0F5',
                       edgecolor='#FF69B4', linewidth=2.5, transform=self.ax_clock.transAxes)
        self.ax_clock.add_patch(sq)

        for i in range(12):
            ang = math.radians(90 - i * 30)  # 顺时针，12点指向正上方
            # 刻度线
            xi, yi = r * 0.75, r * 0.92
            self.ax_clock.add_line(Line2D(
                [cx + xi * math.cos(ang), cx + yi * math.cos(ang)],
                [cy + xi * math.sin(ang), cy + yi * math.sin(ang)],
                color='#FF69B4', linewidth=2, transform=self.ax_clock.transAxes))
            # 钟面数字
            num = i if i != 0 else 12
            nx, ny = cx + r * 0.58 * math.cos(ang), cy + r * 0.58 * math.sin(ang)
            self.ax_clock.text(nx, ny, str(num), fontsize=7, fontweight='bold',
                              color='#FF1493', ha='center', va='center',
                              transform=self.ax_clock.transAxes)

        # 时间计算
        total_sec = tick * 30
        h24 = (11 + (50 + total_sec // 60) // 60) % 24
        h12 = h24 % 12
        m = (50 + total_sec // 60) % 60
        h_display = h24  # 24小时制显示

        # 时针（用12小时制计算角度）
        ha = math.radians(90 - (h12 * 30 + m * 0.5))
        self.ax_clock.add_line(Line2D([cx, cx + r * 0.42 * math.cos(ha)],
                                      [cy, cy + r * 0.42 * math.sin(ha)],
                                      color='#FF1493', linewidth=3.5, transform=self.ax_clock.transAxes))

        # 分针
        ma = math.radians(90 - m * 6)
        self.ax_clock.add_line(Line2D([cx, cx + r * 0.65 * math.cos(ma)],
                                      [cy, cy + r * 0.65 * math.sin(ma)],
                                      color='#FF1493', linewidth=2, transform=self.ax_clock.transAxes))

        # 中心点
        self.ax_clock.add_patch(Circle((cx, cy), 0.04, facecolor='#FF1493',
                                       edgecolor='none', transform=self.ax_clock.transAxes))

        # 数字时钟（Courier New 加粗）
        self.ax_clock.text(cx, cy - r - 0.12, f"BJT {h24:02d}:{m:02d}",
                          fontsize=9, fontweight='bold', color='#FF1493',
                          ha='center', va='top', transform=self.ax_clock.transAxes,
                          family='monospace',
                          bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFF0F5',
                                   edgecolor='#FF69B4', alpha=0.9))

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

        # 粉色模拟钟表 + 数字时钟
        self._draw_clock(tick)

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

        # 清除文本标签（食堂名、排队数字等）
        for lbl in self.text_labels:
            if lbl in self.ax_map.texts:
                lbl.remove()
        self.text_labels.clear()

    def _draw_canteens(self, canteens: List[Canteen]) -> None:
        """绘制食堂位置和状态，文字裁剪到 axes 边界防穿模"""
        xlim = self.ax_map.get_xlim()
        ylim = self.ax_map.get_ylim()
        bbox = self.ax_map.bbox
        for canteen in canteens:
            x, y = canteen.position
            if not (xlim[0] - 30 < x < xlim[1] + 30 and ylim[0] - 30 < y < ylim[1] + 30):
                continue
            x, y = canteen.position
            queue_length = canteen.get_total_queue_length()
            capacity = canteen.capacity

            # 计算食堂繁忙程度（0-1）
            busyness = min(queue_length / max(capacity, 1), 1.0)

            # 黄色三角标记食堂位置
            tri_size = self.canteen_size
            tri = Polygon([
                (x, y + tri_size),          # 顶点
                (x - tri_size * 0.6, y),   # 左下
                (x + tri_size * 0.6, y),   # 右下
            ], facecolor='#FFD700', edgecolor='#CC9900', alpha=0.9, linewidth=1.5, zorder=5)
            self.ax_map.add_patch(tri)
            self.canteen_rects.append(tri)

            # 食堂名称标签（clip_box 防穿模）
            ly = y + tri_size + 4
            label = self.ax_map.text(x, ly, canteen.name,
                                    fontsize=self.font_size + 1,
                                    ha='center', va='bottom',
                                    color='#FF2222', fontweight='bold',
                                    clip_on=True, clip_box=bbox)
            self.text_labels.append(label)

            # 绘制排队柱状图（三角右侧远处，数字在柱子右边）
            if queue_length > 0:
                bar_x = x + tri_size + 14  # 三角右侧留足间距
                bar_width = 10
                bar_height = max(min(queue_length * 3, 70), 12)
                bar_bottom = y + tri_size * 0.5
                bar = Rectangle((bar_x, bar_bottom - bar_height),
                               bar_width, bar_height,
                               facecolor='#FF6600',
                               edgecolor='black', alpha=0.95, linewidth=1.5)
                self.ax_map.add_patch(bar)
                self.queue_bars.append(bar)

                # 排队人数标签（柱子右边，clip 防穿模）
                queue_text = self.ax_map.text(bar_x + bar_width + 3, bar_bottom - bar_height/2,
                                             str(queue_length),
                                             fontsize=self.font_size + 2,
                                             ha='left', va='center',
                                             color='#CC0000', fontweight='bold',
                                             clip_on=True, clip_box=self.ax_map.bbox)
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

            # 提取坐标，排队/用餐加随机偏移避免扎堆重叠
            import random as _rnd
            x_coords = []
            y_coords = []
            for s in student_list:
                px, py = s.position
                if s.state in (StudentState.QUEUING, StudentState.EATING):
                    px += _rnd.uniform(-14, 14)
                    py += _rnd.uniform(-14, 14)
                x_coords.append(px)
                y_coords.append(py)

            # 批量绘制点
            points = self.ax_map.scatter(x_coords, y_coords,
                                        s=self.point_size**2,
                                        c=color, alpha=0.8,
                                        edgecolors='black', linewidths=0.5)
            self.student_points.append(points)

        # 性能提示（当学生数量多时）
        if len(students) > 500:
            self.ax_map.set_title(f"{_viz_t('map_title', self.lang)} ({len(students)} {_viz_t('info_students', self.lang)} - {_viz_t('perf_mode', self.lang)})",
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
        self.ax_stats.set_xlabel(_viz_t("stats_xlabel", self.lang), fontsize=9)
        self.ax_stats.set_ylabel(_viz_t("stats_ylabel", self.lang), fontsize=9)
        self.ax_stats.set_title(f"{_viz_t('stats_title', self.lang)} ({_viz_t('info_queue', self.lang)}: {total_queue})", fontsize=11, fontweight='bold')
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
        lang = self.lang
        state_counts = {
            _viz_t("info_walking", lang): 0,
            _viz_t("info_queuing", lang): 0,
            _viz_t("info_eating", lang): 0,
            _viz_t("info_leaving", lang): 0,
        }

        walking_key = _viz_t("info_walking", lang)
        queuing_key = _viz_t("info_queuing", lang)
        eating_key = _viz_t("info_eating", lang)
        leaving_key = _viz_t("info_leaving", lang)

        for student in students:
            if student.state == StudentState.WALKING:
                state_counts[walking_key] += 1
            elif student.state == StudentState.QUEUING:
                state_counts[queuing_key] += 1
            elif student.state == StudentState.EATING:
                state_counts[eating_key] += 1
            elif student.state == StudentState.LEAVING:
                state_counts[leaving_key] += 1

        # 过滤掉数量为0的状态
        labels = []
        sizes = []
        colors = []

        for label, count in state_counts.items():
            if count > 0:
                labels.append(label)
                sizes.append(count)

                # 根据状态选择颜色
                if label == walking_key:
                    colors.append(self.colors['student_walking'])
                elif label == queuing_key:
                    colors.append(self.colors['student_queuing'])
                elif label == eating_key:
                    colors.append(self.colors['student_eating'])
                elif label == leaving_key:
                    colors.append(self.colors['student_leaving'])

        # 更新饼图
        self.ax_pie.clear()
        if sizes:
            self.ax_pie.pie(sizes, labels=labels, colors=colors,
                           autopct='%1.1f%%', startangle=90,
                           textprops={'fontsize': 9})
            self.ax_pie.set_title(f"{_viz_t('pie_title', self.lang)} ({_viz_t('pie_total', self.lang)}: {len(students)})",
                                 fontsize=11, fontweight='bold')
        else:
            self.ax_pie.text(0.5, 0.5, _viz_t("no_students", self.lang),
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

        lang = self.lang
        pct = lambda n: n / total_students * 100 if total_students > 0 else 0
        status_str = _viz_t('info_paused', lang) if self.is_paused else _viz_t('info_running', lang)
        info_lines = [
            f"{_viz_t('info_tick', lang)}:{tick} | {_viz_t('info_students', lang)}:{total_students} | {_viz_t('info_status', lang)}:{status_str}",
            f"{_viz_t('info_walking', lang)}:{walking_count}({pct(walking_count):.0f}%) {_viz_t('info_queuing', lang)}:{queuing_count}({pct(queuing_count):.0f}%) {_viz_t('info_eating', lang)}:{eating_count}({pct(eating_count):.0f}%) {_viz_t('info_leaving', lang)}:{leaving_count}({pct(leaving_count):.0f}%)",
            f"{_viz_t('info_canteens', lang)}:{canteen_count} | {_viz_t('info_queue', lang)}:{total_queue} | {_viz_t('info_speed', lang)}:{self.animation_speed}ms",
        ]

        # 更新左侧信息面板
        self.info_text.set_text("\n".join(info_lines))

        # 绘制食堂排队横条
        self._draw_canteen_bars(canteens, lang)

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

        self._update_info_text(f"{_viz_t('info_speed', self.lang)}: {interval}ms")

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