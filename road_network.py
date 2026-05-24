"""
道路网络模块 - road_network.py

本模块实现校园道路网络：
1. RoadNetwork类：加载道路段，构建连通图
2. 位置吸附：将任意坐标吸附到最近道路
3. 路径规划：基于道路网络的A*/Dijkstra最短路径

道路段格式：((x_min, x_max), (y_min, y_max))，矩形区域
连通判定：矩形重叠（含容差）
"""

import math
import heapq
from typing import List, Tuple, Optional


class RoadNetwork:
    """校园道路网络，管理道路段连通图和路径规划"""

    def __init__(self, road_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
                 overlap_tolerance: float = 5.0):
        """
        初始化道路网络

        参数：
        road_segments: 道路段列表，每项为 ((x_min,x_max),(y_min,y_max))
        overlap_tolerance: 矩形重叠判定的容差（用于连接相邻但未接触的段）
        """
        # 规范化：确保 min < max
        self.segments = []
        for (x_min, x_max), (y_min, y_max) in road_segments:
            if x_min > x_max:
                x_min, x_max = x_max, x_min
            if y_min > y_max:
                y_min, y_max = y_max, y_min
            self.segments.append(((x_min, x_max), (y_min, y_max)))

        self.tolerance = overlap_tolerance
        self.adj = []  # 邻接表: [(neighbor_idx, distance)]
        self._build_graph()

    def _segment_center(self, idx: int) -> Tuple[float, float]:
        (x_min, x_max), (y_min, y_max) = self.segments[idx]
        return ((x_min + x_max) / 2, (y_min + y_max) / 2)

    @staticmethod
    def _distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def _rectangles_overlap(self, i: int, j: int) -> bool:
        (x1_min, x1_max), (y1_min, y1_max) = self.segments[i]
        (x2_min, x2_max), (y2_min, y2_max) = self.segments[j]
        t = self.tolerance
        x_overlap = x1_min - t <= x2_max and x2_min - t <= x1_max
        y_overlap = y1_min - t <= y2_max and y2_min - t <= y1_max
        return x_overlap and y_overlap

    def _build_graph(self) -> None:
        n = len(self.segments)
        self.adj = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                if self._rectangles_overlap(i, j):
                    d = self._distance(self._segment_center(i), self._segment_center(j))
                    self.adj[i].append((j, d))
                    self.adj[j].append((i, d))

    def snap_to_road(self, position: Tuple[float, float]) -> Tuple[Tuple[float, float], int]:
        """
        将坐标吸附到最近道路段

        返回：
        (吸附后坐标, 道路段索引)
        """
        px, py = position
        best_dist = float('inf')
        best_point = position
        best_idx = 0

        for i, ((x_min, x_max), (y_min, y_max)) in enumerate(self.segments):
            cx = max(x_min, min(px, x_max))
            cy = max(y_min, min(py, y_max))
            d = self._distance(position, (cx, cy))
            if d < best_dist:
                best_dist = d
                best_point = (cx, cy)
                best_idx = i

        return best_point, best_idx

    def find_path(self, start_pos: Tuple[float, float],
                  end_pos: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        规划道路网上从起点到终点的最短路径

        返回：
        路径点列表 [start_snapped, ...segment_centers..., end_actual]
        """
        start_point, start_seg = self.snap_to_road(start_pos)
        end_point, end_seg = self.snap_to_road(end_pos)

        if start_seg == end_seg:
            return [start_point, end_pos]

        # Dijkstra
        n = len(self.segments)
        dist = [float('inf')] * n
        prev = [-1] * n
        dist[start_seg] = 0
        pq = [(0.0, start_seg)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            if u == end_seg:
                break
            for v, w in self.adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))

        # 无路径时回退到直线
        if dist[end_seg] == float('inf'):
            return [start_point, end_pos]

        # 重建路径
        seg_path = []
        u = end_seg
        while u != -1:
            seg_path.append(u)
            u = prev[u]
        seg_path.reverse()

        waypoints = [start_point]
        for idx in seg_path:
            waypoints.append(self._segment_center(idx))
        waypoints.append(end_pos)
        return waypoints

    def path_length(self, start_pos: Tuple[float, float],
                    end_pos: Tuple[float, float]) -> float:
        """计算道路网路径总长度"""
        start_point, start_seg = self.snap_to_road(start_pos)
        end_point, end_seg = self.snap_to_road(end_pos)

        if start_seg == end_seg:
            return (self._distance(start_pos, start_point) +
                    self._distance(start_point, end_point) +
                    self._distance(end_point, end_pos))

        n = len(self.segments)
        dist = [float('inf')] * n
        dist[start_seg] = 0
        pq = [(0.0, start_seg)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            if u == end_seg:
                break
            for v, w in self.adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))

        road_dist = dist[end_seg]
        if road_dist == float('inf'):
            return self._distance(start_pos, end_pos)

        return (self._distance(start_pos, start_point) +
                road_dist +
                self._distance(end_point, end_pos))

    def get_segment_rects(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """返回所有道路段矩形（供可视化使用）"""
        return self.segments.copy()
