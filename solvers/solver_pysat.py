"""
PySAT 求解器集成模块。
提供 `solve_cnf(vm, clauses)` 函数，该函数返回颜色索引网格，
以及辅助函数 `write_solution_file(path, grid)` 用于生成符合格式要求的 .solution 文件。
"""
from typing import List, Optional, Any

def solve_cnf(vm, clauses: List[List[int]]) -> Optional[List[List[str]]]:
    """
    使用 PySAT 求解 CNF 公式，并将变量赋值映射回拼图网格。
    """
    try:
        from pysat.solvers import Glucose3
    except ImportError:
        raise ImportError

    # 1. 初始化求解器并添加子句
    solver = Glucose3()
    for cl in clauses:
        solver.add_clause(cl)
    
    # 2. 求解
    sat = solver.solve()
    if not sat:
        return None
        
    model = solver.get_model()
    # 将模型转化为字典，便于快速查找变量的正负（True/False）
    assignment = {abs(lit): (lit > 0) for lit in model}

    # 3. 提取所有被设为 True 的单元格变量
    # 单元格变量在 VarManager 中的 key 格式为: ('cell', coord, color_index)
    cells = {}
    # 我们遍历模型中所有为真的变量
    for var, val in assignment.items():
        if not val:
            continue
        key = vm.key_of(var)
        if key and isinstance(key, tuple) and key[0] == 'cell':
            _, coord, col_idx = key
            # 存入坐标对应的颜色索引 (0为背景, 1为'a', 2为'b'...)
            # 注意：由于每个格子只能有一种颜色，逻辑正确时每个 coord 只会对应一个 col_idx
            cells[coord] = col_idx

    if not cells:
        return None

    # 4. 判断网格类型并格式化输出
    # 获取一个样本坐标来检查类型
    sample_coord = next(iter(cells.keys()))
    
    # 判断是否为矩形：坐标通常是 (row, col) 且均为非负整数
    # 这里我们通过检查坐标的最小值是否为 0 来辅助判断，或者根据业务逻辑区分
    is_rect = all(isinstance(x, int) and x >= 0 for x in sample_coord) and len(sample_coord) == 2
    
    # 如果所有坐标点的最小值不为0（或者存在负数），则基本可以判定为 Hex 轴向坐标
    min_val = min(min(c) for c in cells.keys())
    if min_val < 0:
        is_rect = False

    if is_rect:
        # --- 矩形网格格式化 ---
        max_r = max(r for (r, c) in cells.keys())
        max_c = max(c for (r, c) in cells.keys())
        H, W = max_r + 1, max_c + 1
        
        grid = []
        for r in range(H):
            row = []
            for c in range(W):
                col_idx = cells.get((r, c), 0)
                char = '-' if col_idx == 0 else chr(ord('a') + (col_idx - 1))
                row.append(char)
            grid.append(row)
        return grid
    else:
        # --- 六边形网格格式化 ---
        # 六边形通常按轴向坐标 r 分行，按 q 排序
        r_coords = sorted(set(c[1] for c in cells.keys()))
        
        grid = []
        for r in r_coords:
            # 获取当前行 (r固定) 的所有单元格并按 q 排序
            row_cells = sorted([c for c in cells.keys() if c[1] == r], key=lambda x: x[0])
            row_chars = []
            for coord in row_cells:
                col_idx = cells.get(coord, 0)
                char = '-' if col_idx == 0 else chr(ord('a') + (col_idx - 1))
                row_chars.append(char)
            grid.append(row_chars)
        return grid

def write_solution_file(path: str, grid: List[List[str]]):
    """
    将网格结果写入文件，每一行对应拼图的一个横行。
    """
    with open(path, 'w') as fp:
        for row in grid:
            fp.write(''.join(row) + '\n')
