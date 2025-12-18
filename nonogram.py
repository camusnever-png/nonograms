import sys, requests, pathlib, json

if len(sys.argv) != 4:
    print('Usage: nonogram.py [check|visualize] path/to/nonogram.clues path/to/nonogram.solution')
    sys.exit()

goal = sys.argv[1]
assert goal in {'check', 'visualize'}
clues = pathlib.Path(sys.argv[2]).read_text()
clue_lines = clues.splitlines()
solution_path = pathlib.Path(sys.argv[3])
solution = solution_path.read_text()

# solution file format is different on the server
for i, c in enumerate('-abcdefghi'):
    solution = solution.replace(c, str(i))

data = {
    'goal': goal,
    'clues': clues,
    'solution': 'anonymous problem\n' + clue_lines[0].split()[0] + '\n' + clue_lines[1] + '\n' + solution,
}

response = requests.get(f'http://jfschaefer.de:8973/verify/ws2425a31a/nonograms', data=json.dumps(data))

if goal == 'check':
    print(response.text)
else:
    path = solution_path.parent / (solution_path.name + '.html')
    print(f'Creating {path}')
    with open(path, 'w') as fp:
        fp.write(f'<html><body><div style="width: 10cm;">{response.text}</div></body></html>')
