"""
Approach 4: automaton encoding per clue.
"""
from .varmap import VarManager
from .approach1 import parse_clue_line

def build_states_for_blocks(blocks, ncolors):
    """
    States:
      S: Start
      B{j}_{c}_{t}: Block j, Color c, cell t (1..size)
      G{j}: Gap after block j
      E: End
    """
    states = ['S']
    k = len(blocks)
    real_colors = range(1, ncolors) # 1-based indices for colors

    for j, (size, col) in enumerate(blocks):
        # Determine valid colors for this block
        if col is None:
            valid_cs = list(real_colors)
        else:
            valid_cs = [col + 1]

        for c in valid_cs:
            for t in range(1, size + 1):
                states.append(f'B{j}_{c}_{t}')
        
        if j < k - 1:
            states.append(f'G{j}')
            
    states.append('E')
    
    # Accepting states
    if k == 0:
        accepting = {'S', 'E'}
    else:
        accepting = {'E'}
        # Last block finished states
        last_blk_idx = k - 1
        last_size = blocks[last_blk_idx][0]
        last_col = blocks[last_blk_idx][1]
        
        if last_col is None:
            valid_cs = list(real_colors)
        else:
            valid_cs = [last_col + 1]
            
        for c in valid_cs:
            accepting.add(f'B{last_blk_idx}_{c}_{last_size}')
        
    return states, accepting

def encode(puzzle, vm: VarManager):
    clauses = []
    ncolors = len(puzzle['colors'])

    # Cell color vars
    for coord in puzzle['cells']:
        vars_cell = [vm.new(('cell', coord, c)) for c in range(ncolors)]
        clauses.append(vars_cell[:])
        for i in range(ncolors):
            for j in range(i+1, ncolors):
                clauses.append([-vars_cell[i], -vars_cell[j]])

    def process_line(lidx, line_cells, clue_line):
        N = len(line_cells)
        blocks = parse_clue_line(clue_line)
        states, accepting = build_states_for_blocks(blocks, ncolors)

        # State variables: state[p][sname]
        state_var = {}
        for p in range(0, N+1):
            for s in states:
                state_var[(p, s)] = vm.new(('state', lidx, p, s))

        # Exactly one state per position
        for p in range(0, N+1):
            vars_here = [state_var[(p, s)] for s in states]
            clauses.append(vars_here[:])
            for i in range(len(vars_here)):
                for j in range(i+1, len(vars_here)):
                    clauses.append([-vars_here[i], -vars_here[j]])

        # Init state
        clauses.append([state_var[(0, 'S')]])

        # Transitions
        for p in range(0, N):
            coord = line_cells[p]
            
            for sname in states:
                curr_s_var = state_var[(p, sname)]
                
                for col_idx in range(ncolors):
                    col_var = vm.get(('cell', coord, col_idx))
                    next_s = []

                    # ------------------------------------------------
                    # Transition Logic
                    # ------------------------------------------------
                    if sname == 'S':
                        if col_idx == 0:
                            next_s.append('S')
                        elif len(blocks) > 0:
                            # Try start first block
                            b0_sz, b0_c = blocks[0]
                            # Check if col_idx matches block req
                            if b0_c is None: # ? -> any non-bg
                                # Transition to the specific color chain
                                next_s.append(f'B0_{col_idx}_1')
                            else:
                                if col_idx == b0_c + 1:
                                    next_s.append(f'B0_{col_idx}_1')
                                
                    elif sname.startswith('B'):
                        # B{j}_{c}_{t}
                        parts = sname[1:].split('_')
                        j = int(parts[0])
                        c_chain = int(parts[1]) # The color of this block chain
                        t = int(parts[2])
                        size, _ = blocks[j]
                        
                        # Must match the chain color
                        if col_idx == c_chain:
                            if t < size:
                                next_s.append(f'B{j}_{c_chain}_{t+1}')
                            # else block finished, cannot continue in block
                        else:
                            # Mismatch or end of block
                            if t == size:
                                # Block ended. col_idx is next cell color.
                                if col_idx == 0:
                                    # To gap
                                    if j < len(blocks) - 1:
                                        next_s.append(f'G{j}')
                                    else:
                                        next_s.append('E')
                                else:
                                    # Direct transition to next block?
                                    if j < len(blocks) - 1:
                                        # Only if next block can be col_idx
                                        # AND col_idx != c_chain (must be different color)
                                        nxt_sz, nxt_c = blocks[j+1]
                                        
                                        valid_next_color = False
                                        if nxt_c is None: valid_next_color = True
                                        elif col_idx == nxt_c + 1: valid_next_color = True
                                        
                                        if valid_next_color and col_idx != c_chain:
                                            next_s.append(f'B{j+1}_{col_idx}_1')

                    elif sname.startswith('G'):
                        j = int(sname[1:])
                        if col_idx == 0:
                            next_s.append(f'G{j}')
                        elif j + 1 < len(blocks):
                            # Start next block
                            nxt_sz, nxt_c = blocks[j+1]
                            
                            valid_next_color = False
                            if nxt_c is None: valid_next_color = True
                            elif col_idx == nxt_c + 1: valid_next_color = True
                            
                            if valid_next_color:
                                next_s.append(f'B{j+1}_{col_idx}_1')
                                
                    elif sname == 'E':
                        if col_idx == 0:
                            next_s.append('E')

                    # ------------------------------------------------
                    
                    if not next_s:
                        clauses.append([-curr_s_var, -col_var])
                    else:
                        literals = [-curr_s_var, -col_var] + [state_var[(p+1, ns)] for ns in next_s]
                        clauses.append(literals)

        # Final acceptance
        acc_vars = [state_var[(N, s)] for s in accepting if (N, s) in state_var]
        clauses.append(acc_vars)

    for lidx, line in enumerate(puzzle['lines']):
        process_line(lidx, line['cells'], line['clue'])

    return clauses
