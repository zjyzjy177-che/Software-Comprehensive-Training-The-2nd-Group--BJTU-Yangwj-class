"""
道路网络模块 - road_network.py

本模块实现校园道路网络：
1. RoadNetwork类：加载道路段，构建连通图
2. 位置吸附：将任意坐标吸附到最近道路
3. 路径规划：基于道路网络的A*/Dijkstra最短路径

道路段格式：((x_min, x_max), (y_min, y_max))，矩形区域
连通判定：矩形重叠（含容差）

图结构（v2）：节点=道路交叉口（交叠区域中心），而非路段中心。
同一条路段上的所有交叉口节点之间用欧氏距离连边，
使得Dijkstra直接使用真实的沿路行走距离，消除长路段偏差。
"""

import math
import heapq
from collections import defaultdict
from typing import List, Tuple, Optional


class RoadNetwork:
    """校园道路网络，管理道路段连通图和路径规划"""

    def __init__(self, road_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
                 overlap_tolerance: float = 5.0):
        """
        初始化道路网络

        参数：
        road_segments: 道路段列表，每项为 ((x_min,x_max),(y_min,y_max))
        overlap_tolerance: 矩形重叠判定的容差
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

        # 图结构：节点 = 道路交叉口（交叠区域中心）
        self.nodes: List[Tuple[float, float]] = []       # 节点坐标
        self.adj: List[List[Tuple[int, float]]] = []      # 邻接表
        self.seg_to_nodes: dict = defaultdict(list)       # 路段 → 其上的节点索引
        self.pair_to_node: dict = {}                      # (seg_i, seg_j) → 节点索引

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

    def _connection_point(self, i: int, j: int) -> Tuple[float, float]:
        """两路段交叠区域中心（即道路交叉口），作为图节点"""
        (x1_min, x1_max), (y1_min, y1_max) = self.segments[i]
        (x2_min, x2_max), (y2_min, y2_max) = self.segments[j]
        ox_min = max(x1_min, x2_min)
        ox_max = min(x1_max, x2_max)
        oy_min = max(y1_min, y2_min)
        oy_max = min(y1_max, y2_max)
        return ((ox_min + ox_max) / 2, (oy_min + oy_max) / 2)

    def _build_graph(self) -> None:
        """构建以交叉口为节点的图，同路段上所有节点用欧氏距离连边"""
        n = len(self.segments)

        # 第一遍：为每对重叠路段创建交叉口节点
        for i in range(n):
            for j in range(i + 1, n):
                if self._rectangles_overlap(i, j):
                    cp = self._connection_point(i, j)
                    node_idx = len(self.nodes)
                    self.nodes.append(cp)
                    self.pair_to_node[(i, j)] = node_idx
                    self.pair_to_node[(j, i)] = node_idx
                    self.seg_to_nodes[i].append(node_idx)
                    self.seg_to_nodes[j].append(node_idx)

        # 初始化邻接表
        num_nodes = len(self.nodes)
        self.adj = [[] for _ in range(num_nodes)]

        # 第二遍：同路段上的所有节点两两连边（沿路行走）
        for seg_idx, node_list in self.seg_to_nodes.items():
            for a in range(len(node_list)):
                for b in range(a + 1, len(node_list)):
                    u = node_list[a]
                    v = node_list[b]
                    d = self._distance(self.nodes[u], self.nodes[v])
                    self.adj[u].append((v, d))
                    self.adj[v].append((u, d))

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
        """规划道路网上从起点到终点的最短路径

        用交叉口节点图 + 虚拟起/终节点做Dijkstra，路径点落在交叉口上。
        """
        start_point, start_seg = self.snap_to_road(start_pos)
        end_point, end_seg = self.snap_to_road(end_pos)

        if start_seg == end_seg:
            return [start_point, end_point, end_pos]

        start_nodes = self.seg_to_nodes.get(start_seg, [])
        end_nodes = self.seg_to_nodes.get(end_seg, [])

        # 起/终路段无交叉口 → 直接走
        if not start_nodes or not end_nodes:
            return [start_point, end_pos]

        base = len(self.nodes)
        virtual_start = base
        virtual_end = base + 1
        total = base + 2

        # 构建扩展邻接表（含虚拟节点）
        ext_adj = self.adj + [[], []]
        for ni in start_nodes:
            d = self._distance(start_point, self.nodes[ni])
            ext_adj[virtual_start].append((ni, d))
            ext_adj[ni].append((virtual_start, d))
        for ni in end_nodes:
            d = self._distance(end_point, self.nodes[ni])
            ext_adj[virtual_end].append((ni, d))
            ext_adj[ni].append((virtual_end, d))

        # Dijkstra
        dist = [float('inf')] * total
        prev = [-1] * total
        dist[virtual_start] = 0
        pq = [(0.0, virtual_start)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            if u == virtual_end:
                break
            for v, w in ext_adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))

        if dist[virtual_end] == float('inf'):
            return [start_point, end_pos]

        # 重建路径（跳过虚拟节点，保留交叉口节点）
        node_path = []
        u = virtual_end
        while u != -1:
            node_path.append(u)
            u = prev[u]
        node_path.reverse()

        waypoints = [start_point]
        for ni in node_path:
            if ni == virtual_start or ni == virtual_end:
                continue
            waypoints.append(self.nodes[ni])
        waypoints.append(end_point)
        waypoints.append(end_pos)
        return waypoints

    def path_length(self, start_pos: Tuple[float, float],
                    end_pos: Tuple[float, float]) -> float:
        """计算道路网路径总长度（累加find_path的各段）"""
        path = self.find_path(start_pos, end_pos)
        total = 0.0
        for i in range(len(path) - 1):
            total += self._distance(path[i], path[i + 1])
        return total

    def get_segment_rects(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """返回所有道路段矩形（供可视化使用）"""
        return self.segments.copy()
