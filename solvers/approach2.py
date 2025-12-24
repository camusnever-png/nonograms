"""
Approach 2: Block-start variables with block-color selection.
"""
from .varmap import VarManager
from .approach1 import parse_clue_line

def encode(puzzle, vm: VarManager):
    clauses = []
    colors = puzzle['colors']
    ncolors = len(colors)

    # 1. Cell color variables: Exactly one color per cell
    for coord in puzzle['cells']:
        cvars = [vm.new(('cell', coord, c)) for c in range(ncolors)]
        clauses.append(cvars)
        for i in range(ncolors):
            for j in range(i + 1, len(cvars)):
                clauses.append([-cvars[i], -cvars[j]])

    # 2. Encode each line
    for lidx, line in enumerate(puzzle['lines']):
        cells = line['cells']
        blocks = parse_clue_line(line['clue'])
        L, K = len(cells), len(blocks)
        
        if K == 0:
            for coord in cells:
                clauses.append([vm.get(('cell', coord, 0))])
            continue

        # 2a. Create all block-related variables (starts and colors)
        b_starts = []
        b_cols = []
        for b_i, (sz, fix_c) in enumerate(blocks):
            if sz > L:
                clauses.append([])
                break
            b_starts.append([vm.new(('start', lidx, b_i, p)) for p in range(L - sz + 1)])
            b_cols.append([vm.new(('b_col', lidx, b_i, c)) for c in range(1, ncolors)])
        if not clauses or clauses[-1] == []: continue

        # 2b. Add constraints for these variables (exactly-one start/color)
        for b_i, (sz, fix_c) in enumerate(blocks):
            clauses.append(b_starts[b_i])
            for i in range(len(b_starts[b_i])):
                for j in range(i + 1, len(b_starts[b_i])):
                    clauses.append([-b_starts[b_i][i], -b_starts[b_i][j]])
            
            if fix_c is not None:
                clauses.append([b_cols[b_i][fix_c]])
            else:
                clauses.append(b_cols[b_i])
            if len(b_cols[b_i]) > 1:
                for i in range(len(b_cols[b_i])):
                    for j in range(i + 1, len(b_cols[b_i])):
                        clauses.append([-b_cols[b_i][i], -b_cols[b_i][j]])
                        
        # 2c. Link Block start/color to Cell color (Forward constraint)
        for b_i, (sz, _) in enumerate(blocks):
            for p, s_var in enumerate(b_starts[b_i]):
                for t in range(p, p + sz):
                    for c_idx in range(1, ncolors):
                        clauses.append([-s_var, -b_cols[b_i][c_idx-1], vm.get(('cell', cells[t], c_idx))])

        # 2d. UNIFIED Spacing and Ordering Constraint
        for b_i in range(K - 1):
            sz_curr = blocks[b_i][0]
            for p, s_curr in enumerate(b_starts[b_i]):
                for q, s_next in enumerate(b_starts[b_i + 1]):
                    if q < p + sz_curr:
                        clauses.append([-s_curr, -s_next])
                        continue
                    if q == p + sz_curr:
                        for c_idx in range(1, ncolors):
                            clauses.append([-s_curr, -s_next, -b_cols[b_i][c_idx-1], -b_cols[b_i+1][c_idx-1]])

        # 2e. THE FINAL FIX: Background Color Constraint (Reverse constraint)
        for pos, coord in enumerate(cells):
            bg_var = vm.get(('cell', coord, 0))
            
            # Collect all possible start variables that could cover this cell
            starts_that_cover_pos = []
            for b_i, (sz, _) in enumerate(blocks):
                for p in range(max(0, pos - sz + 1), pos + 1):
                    if p < len(b_starts[b_i]):
                        starts_that_cover_pos.append(b_starts[b_i][p])

            # Constraint: cell_is_background IFF no block covers it
            # This is equivalent to:
            # 1. cell_is_background => no block start is active
            #    -bg_var => -s_var for all s_var in starts_that_cover_pos
            #    Which is [-bg_var, -s_var]
            for s_var in starts_that_cover_pos:
                clauses.append([-bg_var, -s_var])

            # 2. no block start is active => cell_is_background
            #    AND(-s_var for all s_var) => bg_var
            #    Which is [bg_var, s_var_1, s_var_2, ...]
            clauses.append([bg_var] + starts_that_cover_pos)

    return clauses
