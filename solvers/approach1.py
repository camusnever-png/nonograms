"""
Approach 1: enumerate all valid arrangements for each line and link to cell color vars.
"""
from .varmap import VarManager

def parse_clue_line(clue_line):
    """
    Parse a clue line into a list of (length, color_index_or_None).
    """
    parts = clue_line.replace(',', ' ').split()
    parsed = []

    for token in parts:
        token = token.strip()
        if not token:
            continue
        if token[-1].isalpha() or token[-1] == '?':
            n = int(token[:-1])
            if token[-1] == '?':
                parsed.append((n, None))
            else:
                parsed.append((n, ord(token[-1]) - ord('a')))
        else:
            raise ValueError(f"Invalid clue token: {token}")

    return parsed

def enumerate_starts(length, blocks):
    k = len(blocks)
    def helper(i, minpos, acc):
        if i == k:
            yield list(acc)
            return

        size, _ = blocks[i]
        for s in range(minpos, length - size + 1):
            end = s + size
            remaining = sum(b[0] for b in blocks[i + 1 :])
            if length - end < remaining:
                continue

            acc.append(s)
            yield from helper(i + 1, end, acc)
            acc.pop()

    yield from helper(0, 0, [])

def enumerate_block_colors(blocks, ncolors):
    choices = []
    for _, color in blocks:
        if color is None:
            choices.append(list(range(ncolors - 1)))  # a,b,c,...
        else:
            choices.append([color])

    def helper(i, acc):
        if i == len(choices):
            yield list(acc)
            return
        for c in choices[i]:
            acc.append(c)
            yield from helper(i + 1, acc)
            acc.pop()

    yield from helper(0, [])

def same_color_spacing_ok(starts, blocks, colors):
    for i in range(1, len(blocks)):
        if colors[i] == colors[i - 1]:
            prev_start = starts[i - 1]
            prev_size = blocks[i - 1][0]
            if starts[i] < prev_start + prev_size + 1:
                return False
    return True

def encode(puzzle, vm: VarManager):
    clauses = []
    colors = puzzle['colors']
    ncolors = len(colors)

    for coord in puzzle['cells']:
        vars_cell = []
        for col in range(ncolors):
            vars_cell.append(vm.new(('cell', coord, col)))

        clauses.append(vars_cell[:])
        for i in range(len(vars_cell)):
            for j in range(i + 1, len(vars_cell)):
                clauses.append([-vars_cell[i], -vars_cell[j]])

    for lidx, line in enumerate(puzzle['lines']):
        blocks = parse_clue_line(line['clue'])
        cells = line['cells']
        line_len = len(cells)

        selectors = []

        for starts in enumerate_starts(line_len, blocks):
            for block_colors in enumerate_block_colors(blocks, ncolors):
                if not same_color_spacing_ok(starts, blocks, block_colors):
                    continue

                sel = vm.new(('line', lidx, 'arr', len(selectors)))
                selectors.append(sel)

                cell_colors = [0] * line_len
                for b_i, (size, _) in enumerate(blocks):
                    s = starts[b_i]
                    color_idx = block_colors[b_i]
                    for p in range(s, s + size):
                        cell_colors[p] = color_idx + 1

                for pos, col in enumerate(cell_colors):
                    coord = cells[pos]
                    v = vm.get(('cell', coord, col))
                    clauses.append([-sel, v])

        if not selectors:
            clauses.append([])
        else:
            clauses.append(selectors[:])
            for i in range(len(selectors)):
                for j in range(i + 1, len(selectors)):
                    clauses.append([-selectors[i], -selectors[j]])

    return clauses
