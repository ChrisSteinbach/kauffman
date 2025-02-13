# Kauffman

Kauffman is a Python project containing a set of command-line tools for
analyzing software architecture. It uses Random Boolean Networks (RBNs) to
model and analyze system robustness, stability, and other properties.

## Features

- Simulation of Random Boolean Networks (RBNs).
- Analysis of architecture robustness to perturbations.
- Tools for generating and visualizing network properties.

## Installation

To use the project in a development environment, clone the repository and
install it in **editable mode**:

```bash
git clone https://github.com/ChrisSteinbach/kauffman.git
cd kauffman
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

This installs the project and its dependencies while allowing you to edit the
source code.

## Requirements

 - Python 3.8+
 - Dependencies listed in requirements.txt (installed as per instructions above).

## Usage

### Command-Line Tools

The tools are available as standalone scripts in the scripts/ directory. Here's
how to run the main simulation tool:

```bash
./scripts/simulation input_file.dot
```

```
positional arguments:
  dot_file              Input Graphviz .dot file

options:
  -h, --help            show this help message and exit
  -s STAGES, --stages STAGES
                        Number of stages (default: 8)
  -r RUNS, --runs RUNS  Number of runs per stage (default: 2000)
  -t STEPS, --steps STEPS
                        Number of steps per run (default: 40)
```

Note that on Linux and MacOS the simulation script copies the output file to
the clipboard. From there it can be pasted into a graphviz dot file viewer like
edotor.net.

And here's how to run the perturbation tool:

```bash
python ./scripts/perturbations.py input_file.dot
```

## Development

### Running Tests

The project uses pytest for testing. To run the tests, execute the following
command:

```bash
pytest
```

