import sys
from .parser import parse_clues
from .varmap import VarManager
def write_dimacs(nvars, clauses, path):
    with open(path, 'w') as fp:
        fp.write(f'p cnf {nvars} {len(clauses)}\n')
        for cl in clauses:
            fp.write(' '.join(str(x) for x in cl) + ' 0\n')
import argparse
import os
from pathlib import Path
import pprint


def choose_encoder(n):
    if n == 1:
        from .approach1 import encode
    elif n == 2:
        from .approach2 import encode
    elif n == 4:
        from .approach4 import encode
    else:
        raise ValueError('unsupported approach')
    return encode


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output', nargs='?', default=None, help='optional output CNF path or directory')
    parser.add_argument('--approach', type=int, default=1, choices=[1,2,3,4], help='which encoding approach')
    parser.add_argument('--solve', action='store_true', help='also solve the generated CNF with PySAT and write a .solution file')
    parser.add_argument('--solution', default=None, help='path to write the .solution file when using --solve')
    parser.add_argument('--dump-puzzle', action='store_true', help='print the parsed puzzle structure and skip encoding')
    args = parser.parse_args(argv[1:])
    inp = args.input; out = args.output
    encoder = choose_encoder(args.approach)

    def process_one(clue_path: Path, out_arg: str):
        try:
            puzzle = parse_clues(str(clue_path))
        except Exception as e:
            print(f'Error parsing {clue_path}:', e)
            return 1

        if args.dump_puzzle:
            print(f'Parsed puzzle for {clue_path}:')
            pprint.pprint(puzzle)
            return 0

        vm = VarManager()
        try:
            clauses = encoder(puzzle, vm)
        except Exception as e:
            print(f'Error encoding {clue_path}:', e)
            return 1
        nvars = vm.nvars()

        # Determine CNF output path using same logic as single-file mode
        inp_path = Path(clue_path)
        clue_stem = inp_path.stem
        if out_arg is None:
            cnf_dir = Path('cnf')
            cnf_dir.mkdir(exist_ok=True)
            out_path = cnf_dir / (f"{clue_stem}_a{args.approach}.cnf")
        else:
            out_path = Path(out_arg)
            if str(out_arg).endswith(os.path.sep) or out_path.is_dir():
                out_path = out_path / (f"{clue_stem}_a{args.approach}.cnf")
            else:
                if out_path.parent == Path('.') or str(out_path.parent) == '':
                    cnf_dir = Path('cnf')
                    cnf_dir.mkdir(exist_ok=True)
                    out_path = cnf_dir / out_path.name
                else:
                    out_path.parent.mkdir(parents=True, exist_ok=True)

        write_dimacs(nvars, clauses, str(out_path))
        print(f'Wrote {out_path} with {nvars} vars and {len(clauses)} clauses (approach {args.approach})')

        if args.solve:
            solpath = args.solution
            if solpath is None:
                sol_dir = Path('solutions')
                sol_dir.mkdir(exist_ok=True)
                solpath = sol_dir / (f"{clue_stem}_a{args.approach}.solution")
            else:
                solpath = Path(solpath)
                if str(args.solution).endswith(os.path.sep) or solpath.is_dir():
                    solpath = solpath / (f"{clue_stem}_a{args.approach}.solution")
                else:
                    if solpath.parent == Path('.') or str(solpath.parent) == '':
                        sol_dir = Path('solutions')
                        sol_dir.mkdir(exist_ok=True)
                        solpath = sol_dir / solpath.name
                    else:
                        solpath.parent.mkdir(parents=True, exist_ok=True)
            try:
                from .solver_pysat import solve_cnf, write_solution_file
            except Exception as e:
                print('PySAT integration not available:', e)
                return 1
            print('Solving using PySAT...')
            grid = solve_cnf(vm, clauses)
            if grid is None:
                print('UNSAT (no solution)')
                return 10
            write_solution_file(str(solpath), grid)
            print(f'Wrote solution to {solpath}')
        return 0

    # If input is a directory, iterate all .clues files
    inp_path = Path(inp)
    if inp_path.is_dir():
        files = sorted(inp_path.glob('*.clues'))
        if not files:
            print('No .clues files found in', inp_path)
            return 2
        failures = 0
        for p in files:
            print('Processing', p)
            rc = process_one(p, out)
            if rc != 0:
                failures += 1
        if failures:
            print(f'Completed with {failures} failures')
            return 3
        return 0

    # single-file mode
    return process_one(Path(inp), out)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
