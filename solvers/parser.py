import pathlib

def parse_clues(path):
    """
    解析 .clues 文件，支持矩形 (rect) 和任意大小的六边形 (hex) 格式。
    """
    p = pathlib.Path(path)
    try:
        txt = p.read_text(encoding='utf-8').splitlines()
    except UnicodeDecodeError:
        txt = p.read_text(encoding='latin-1').splitlines()

    if not txt:
        raise ValueError('空的 .clues 文件')

    first = txt[0].split()
    
    if first[0] == 'rect':
        height, width = int(first[1]), int(first[2])
        colors = txt[1].split()
        expected_clues = height + width
        raw_clues = [line.rstrip() for line in txt[2:2 + expected_clues]]

        cells = [(r, c) for r in range(height) for c in range(width)]
        lines = []
        for r in range(height): lines.append([(r, c) for c in range(width)])
        for c in range(width): lines.append([(r, c) for r in range(height)])
            
        return {
            'kind': 'rect', 'height': height, 'width': width, 'colors': colors, 'cells': cells,
            'lines': [{'clue': raw_clues[i], 'cells': lines[i]} for i in range(len(lines))]
        }

    elif first[0] == 'hex':
        size = int(first[1])
        colors = txt[1].split()
        expected = 3 * (2 * size - 1)
        raw_clues = [line.rstrip() for line in txt[2:2 + expected]]

        if len(raw_clues) != expected:
             raise ValueError(f'线索数量错误: 文件 "{p.name}" 需要 {expected} 条, 但找到 {len(raw_clues)} 条。')
        
        # 1. 生成轴向坐标 (q, r), s = -q-r
        coords = []
        for q in range(-(size - 1), size):
            for r in range(-(size - 1), size):
                if abs(-q - r) < size:
                    coords.append((q, r))

        # 2. 按逆时针规则和箭头方向，定义三个方向的线索组
        dir_group1, dir_group2, dir_group3 = [], [], []
        
        # 组 1: 水平线 (r 为常数)。箭头 -> (q 递增)
        for r_val in range(-(size - 1), size):
            line = sorted([c for c in coords if c[1] == r_val], key=lambda x: x[0])
            dir_group1.append(line)

        # 组 2: 垂直/斜向 (q 为常数)。箭头 ^ (r 递减)
        for q_val in range(-(size - 1), size):
            line = sorted([c for c in coords if c[0] == q_val], key=lambda x: x[1], reverse=True)
            dir_group2.append(line)
            
        # 组 3: 另一斜向 (s 为常数)。箭头 \ (q 递减)
        for s_val in range(-(size - 1), size):
            line = sorted([c for c in coords if -c[0]-c[1] == s_val], key=lambda x: x[0], reverse=True)
            dir_group3.append(line)

        # 3. 按照 r -> q -> s (一个可能的、符合逆时针的组序) 组合所有线索
        all_lines = dir_group1 + dir_group2 + dir_group3
        
        return {
            'kind': 'hex', 'size': size, 'colors': colors, 'cells': coords,
            'lines': [{'clue': raw_clues[i], 'cells': all_lines[i]} for i in range(expected)]
        }
    else:
        raise NotImplementedError('不支持的拼图类型: ' + first[0])
