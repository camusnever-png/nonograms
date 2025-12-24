import argparse
import time
import csv
from pathlib import Path
import solvers.parser as parser
from solvers.varmap import VarManager

# 动态导入指定的方法
def get_encoder(approach_num):
    if approach_num == 1:
        from solvers.approach1 import encode
    elif approach_num == 2:
        from solvers.approach2 import encode
    elif approach_num == 4:
        from solvers.approach4 import encode
    else:
        raise ValueError(f"不支持的方法: {approach_num}")
    return encode

def run_benchmark(clue_files, approaches_to_test, timeout_s=60):
    """
    对给定的文件和方法进行基准测试，并返回结果。
    """
    results = []
    
    for file_path in clue_files:
        print(f"\n--- 正在测试: {file_path.name} ---")
        try:
            puzzle = parser.parse_clues(str(file_path))
        except Exception as e:
            print(f"  -> 解析失败: {e}")
            continue

        for approach_num in approaches_to_test:
            print(f"  使用方法 {approach_num}...")
            
            # 创建新的 VarManager 和 encoder
            vm = VarManager()
            try:
                encoder = get_encoder(approach_num)
            except ImportError:
                print(f"  -> 无法导入方法 {approach_num}, 跳过。")
                continue

            start_time = time.time()
            try:
                # 注意：这里我们不真正运行求解器，只关注编码阶段的性能
                clauses = encoder(puzzle, vm)
                end_time = time.time()
                
                encoding_time = end_time - start_time
                num_vars = vm.nvars()
                num_clauses = len(clauses)
                
                if encoding_time > timeout_s:
                    print(f"  -> 编码超时 ( > {timeout_s}s )")
                    results.append([file_path.name, approach_num, -1, -1, encoding_time])
                else:
                    print(f"  -> 完成: {num_vars} 变量, {num_clauses} 子句, {encoding_time:.4f} 秒")
                    results.append([file_path.name, approach_num, num_vars, num_clauses, encoding_time])

            except Exception as e:
                print(f"  -> 编码时发生错误: {e}")
                results.append([file_path.name, approach_num, -1, -1, -1]) # -1 代表错误

    return results

def main():
    parser = argparse.ArgumentParser(description="对 Nonogram SAT 编码方法进行基准测试。")
    parser.add_argument("clues_dir", help="包含 .clues 文件的目录。")
    parser.add_argument("--approaches", nargs='+', type=int, required=True, help="要测试的方法编号 (例如: 1 2 4)。")
    parser.add_argument("--output", default="benchmark_results.csv", help="输出的 CSV 文件名。")
    parser.add_argument("--timeout", type=int, default=300, help="单个编码任务的超时时间（秒）。")

    args = parser.parse_args()

    clues_path = Path(args.clues_dir)
    if not clues_path.is_dir():
        print(f"错误: '{args.clues_dir}' 不是一个有效的目录。")
        return

    clue_files = sorted(list(clues_path.glob('*.clues')))
    if not clue_files:
        print(f"在 '{args.clues_dir}' 中未找到任何 .clues 文件。")
        return

    print(f"找到 {len(clue_files)} 个拼图文件。将使用方法 {args.approaches} 进行测试。")
    
    benchmark_data = run_benchmark(clue_files, args.approaches, args.timeout)

    # 写入 CSV 文件
    header = ['puzzle', 'approach', 'variables', 'clauses', 'encoding_time_s']
    with open(args.output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(benchmark_data)

    print(f"\n基准测试完成！结果已保存到 '{args.output}'。")
    print("您现在可以使用此 CSV 文件生成图表以进行性能比较。")


if __name__ == "__main__":
    main()

