Assignment 3.1
==============


This repository contains the data for assignment 3.1:
* `clues/` contains clues for the nonograms that you should solve.
* `generated/` contains traditional nonograms (rectangular, single color, etc.) of different sizes that you can use to compare the performance of different approaches.
    It contains nonograms that we generated with different algorithms.


#### `nonogram.py`
You can use `nonogram.py` to check and visualize your solutions.
To do so, it will send them to a server for processing.
It requires the `requests` package (`python3 -m pip install requests`).

If you want to check a solution, you can run
```
python3 nonogram.py check path/to/nonogram.clues path/to/nonogram.solution
```
and if you want to visualize the solution, you can run
```
python3 nonogram.py visualize path/to/nonogram.clues path/to/nonogram.solution
```
The script will then generate an HTML file that visualizes the nonogram as an embedded SVG image.

Note: Both `nonogram.py` and the server backend were hacked together relatively quickly.
Please reach out if you face any problems.


#### `checkall.py`
You can use `checkall.py` to check the correctness of all your solutions.
