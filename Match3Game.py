# -*- coding: utf-8 -*-
# @Author  : XieSiR
# @Time    : 2025/3/26 18:09
# @Function: 游戏核心逻辑，消除规则，参考https://www.taptap.cn/moment/15225564524708777

from collections import defaultdict

LEVEL_SCORES = {
    1: 10,
    2: 20,
    3: 80,
    4: 640,
}

# 一个格子的定义
class Cell:
    def __init__(self, family: str, level: int):
        self.family = family
        self.level = level
        self.combo_id = None  # 当前轮次的消除编号

    def __repr__(self):
        return f"{self.family}{self.level}{self.combo_id if self.combo_id is not None else ''}"


# 整个沙盘的逻辑封装
class GameBoard:
    def __init__(self, grid):
        """
        grid 是一个二维列表，每个元素为 None 或 Cell 实例
        """
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0
        self.directions = [(-1, 0), (-1, -1), (-1, 1), (0, -1)]  # 上、左上、右上、左
        self.swap_points = set()  # 存储当前轮次的交换点坐标（两个）

    def run_swap(self, pos1, pos2):
        self.manual_swap(pos1, pos2)
        total_score = 0
        round = 0
        while True:
            removed, score = self.step(round)
            if removed == 0:
                break
            total_score += score
            round += 1
        self.swap_points = set()
        return total_score

    def step(self, round):
        self.reset_combo_ids()
        combos, combo_points = self.detect_combinations(round)
        if not combos:
            return 0, 0
        removed, score = self.apply_combinations(combos, combo_points)
        self.apply_gravity()
        return removed, score



    def reset_combo_ids(self):
        for row in self.grid:
            for cell in row:
                if cell:
                    cell.combo_id = None

    def manual_swap(self, pos1, pos2):
        """
        手动交换两个格子内容，并记录交换点
        pos1, pos2: 均为 (i, j) 坐标
        """
        i1, j1 = pos1
        i2, j2 = pos2
        self.grid[i1][j1], self.grid[i2][j2] = self.grid[i2][j2], self.grid[i1][j1]
        self.swap_points = {pos1, pos2}

    def detect_combinations(self, round):
        combo_id_counter = 0
        combos = defaultdict(list)  # combo_id -> list of (i,j)
        combo_points = {}  # combo_id -> (i,j) as center

        for i in range(self.rows):
            for j in range(self.cols):
                cell = self.grid[i][j]
                if not cell:
                    continue

                for dx, dy in self.directions:
                    coords = []
                    for k in range(1, 3):
                        ni, nj = i + dx * k, j + dy * k
                        if 0 <= ni < self.rows and 0 <= nj < self.cols:
                            neighbor = self.grid[ni][nj]
                            if neighbor and neighbor.family == cell.family and neighbor.level == cell.level:
                                coords.append((ni, nj))
                            else:
                                break
                        else:
                            break

                    if len(coords) == 2:
                        involved = [(i, j)] + coords
                        ids = [self.grid[x][y].combo_id for x, y in involved]
                        unique_ids = list(set([cid for cid in ids if cid is not None]))
                        current_id = 0

                        if not unique_ids:
                            # 全部无编号，创建新 combo_id
                            for x, y in involved:
                                self.grid[x][y].combo_id = combo_id_counter
                                combos[combo_id_counter].append((x, y))
                            combo_points[combo_id_counter] = coords[0]  # 中间那个格子作为消除点
                            current_id = combo_id_counter
                            combo_id_counter += 1

                        elif len(unique_ids) == 1:
                            # 都已经是相同编号，补进去
                            cid = unique_ids[0]
                            current_id = unique_ids[0]
                            for x, y in involved:
                                if self.grid[x][y].combo_id != cid:
                                    self.grid[x][y].combo_id = cid
                                    combos[cid].append((x, y))

                        else:
                            # 有两个不同编号，合并到较近且有编号的那个
                            dist = lambda xy: abs(xy[0] - i) + abs(xy[1] - j)
                            valid_coords = [xy for xy in coords if self.grid[xy[0]][xy[1]].combo_id is not None]
                            nearer = min(valid_coords, key=dist)
                            cid = self.grid[nearer[0]][nearer[1]].combo_id
                            current_id = cid
                            for x, y in involved:
                                old_cid = self.grid[x][y].combo_id
                                if old_cid is not None and old_cid != cid:
                                    # 从旧 combo 列表中移除
                                    if (x, y) in combos[old_cid]:
                                        combos[old_cid].remove((x, y))
                                if self.grid[x][y].combo_id != cid:
                                    self.grid[x][y].combo_id = cid
                                    combos[cid].append((x, y))
                        if round == 0:
                            swap_involved = [pt for pt in involved if pt in self.swap_points]
                            if swap_involved:
                                combo_points[current_id] = swap_involved[0]

        return combos, combo_points

    def apply_combinations(self, combos, combo_points):
        total_removed = 0
        total_score = 0

        for cid, positions in combos.items():
            ci, cj = combo_points[cid]
            sample_i, sample_j = positions[0]
            sample_cell = self.grid[sample_i][sample_j]
            new_level = min(5, sample_cell.level + 1)
            new_cell = Cell(sample_cell.family, new_level)

            count = len(positions)
            score = (count - 2) * LEVEL_SCORES.get(sample_cell.level, 0)
            total_score += score

            for i, j in positions:
                self.grid[i][j] = None
                total_removed += 1

            self.grid[ci][cj] = new_cell

        return total_removed, total_score



    def apply_gravity(self):
        for col in range(self.cols):
            stack = []
            # 从下往上收集非空格子
            for row in reversed(range(self.rows)):
                if self.grid[row][col]:
                    stack.append(self.grid[row][col])
            # 重建该列
            for row in reversed(range(self.rows)):
                if stack:
                    self.grid[row][col] = stack.pop(0)
                else:
                    self.grid[row][col] = None

    def find_best_swap(self):
        best_swap = None
        max_score = 0

        for i1 in range(self.rows):
            for j1 in range(self.cols):
                for i2 in range(self.rows):
                    for j2 in range(self.cols):
                        if (i1, j1) == (i2, j2):
                            continue
                        if not self.grid[i1][j1] and not self.grid[i2][j2]:
                            continue
                        if self.grid[i1][j1] and self.grid[i2][j2]:
                            if self.grid[i1][j1].family == self.grid[i2][j2].family and self.grid[i1][j1].level == self.grid[i2][j2].level:
                                continue

                        test_grid = [[cell if cell is None else Cell(cell.family, cell.level)
                                      for cell in row] for row in self.grid]

                        test_game = GameBoard(test_grid)
                        score = test_game.run_swap((i1, j1), (i2, j2))
                        if score >= max_score:
                            max_score = score
                            best_swap = ((i1 + 1, j1 + 1), (i2 + 1, j2 + 1))

        return best_swap, max_score


    def print_board(self):
        for row in self.grid:
            print(['.' if cell is None else str(cell) for cell in row])
        print()
