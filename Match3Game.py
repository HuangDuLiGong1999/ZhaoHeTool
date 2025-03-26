# -*- coding: utf-8 -*-
# @Author  : XieSiR
# @Time    : 2025/3/26 18:09
# @Function: 游戏核心逻辑，消除规则，参考https://www.taptap.cn/moment/15225564524708777

from collections import defaultdict

# 一个格子的定义
class Cell:
    def __init__(self, family: str, level: int):
        self.family = family
        self.level = level
        self.combo_id = None  # 当前轮次的消除编号

    def __repr__(self):
        return f"{self.family}{self.level}"


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
        total_removed = 0
        round = 0
        while True:
            removed = self.step(round)
            if removed == 0:
                break
            total_removed += removed
            round += 1
        self.swap_points = set()
        return total_removed


    def step(self, round):
        self.reset_combo_ids()
        combos, combo_points = self.detect_combinations(round)
        if not combos:
            return 0

        removed = self.apply_combinations(combos, combo_points)
        self.apply_gravity()
        return removed


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
                            # 有两个不同编号，合并到较近那个
                            dist = lambda xy: abs(xy[0] - i) + abs(xy[1] - j)
                            nearer = min(coords, key=dist)
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
        for cid, positions in combos.items():
            ci, cj = combo_points[cid]
            sample_i, sample_j = positions[0]
            sample_cell = self.grid[sample_i][sample_j]
            new_level = min(5, sample_cell.level + 1)
            new_cell = Cell(sample_cell.family, new_level)

            for i, j in positions:
                self.grid[i][j] = None
                total_removed += 1

            self.grid[ci][cj] = new_cell

        return total_removed


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
        """
        穷举所有不相同的格子对，返回会产生最多合成的交换动作。
        返回: ((i1, j1), (i2, j2), max_combos)
        """
        best_swap = None
        max_combos = 0

        for i1 in range(self.rows):
            for j1 in range(self.cols):
                for i2 in range(self.rows):
                    for j2 in range(self.cols):
                        if (i1, j1) == (i2, j2):
                            continue  # 忽略同一个点

                        # 跳过两个都是 None 的格子
                        if not self.grid[i1][j1] and not self.grid[i2][j2]:
                            continue
                        if self.grid[i1][j1].family == self.grid[i2][j2].family and self.grid[i1][j1].level == self.grid[i2][j2].level:
                            continue

                        # 拷贝 grid
                        test_grid = [[cell if cell is None else Cell(cell.family, cell.level)
                                      for cell in row] for row in self.grid]

                        test_game = GameBoard(test_grid)
                        combo_count = test_game.run_swap((i1, j1), (i2, j2))
                        #print(((i1, j1), (i2, j2)), combo_count)
                        if combo_count >= max_combos:
                            max_combos = combo_count
                            best_swap = ((i1+1, j1+1), (i2+1, j2+1))

        return best_swap, max_combos



    def print_board(self):
        for row in self.grid:
            print(['.' if cell is None else str(cell) for cell in row])
        print()


grid = [
    [Cell('A', 1), Cell('A', 1), None],
    [None,         Cell('A', 1), Cell('A', 1)],
    [None,         None,         Cell('B', 1)]
]

game = GameBoard(grid)
print("初始状态：")
game.print_board()

game.run_swap((2, 2), (1, 2))

print("最终状态：")
game.print_board()
