# Kauffman

Kauffman is a Python project containing a set of command-line tools for analyzing software architecture. It leverages concepts like Random Boolean Networks (RBNs) to model and analyze system robustness, stability, and other properties.

## Features

- Simulation of Random Boolean Networks (RBNs).
- Analysis of architecture robustness to perturbations.
- Tools for generating and visualizing network properties.
- Command-line interface for running simulations and analyses.

## Installation

To use the project in a development environment, clone the repository and install it in **editable mode**:

```bash
git clone https://github.com/ChrisSteinbach/kauffman.git
cd kauffman
pip install -e .
```

This installs the project and its dependencies while allowing you to edit the source code.

## Requirements

 - Python 3.8+
 - Dependencies listed in requirements.txt (installed automatically).

## Usage

### Command-Line Tools

The tools are available as standalone scripts in the scripts/ directory. Here's how to run the main simulation tool:

```bash
./scripts/simulation input_file.txt
```

### Example Usage

1. Prepare your input files (examples can be found in the examples/ directory).
2. Run the simulation script:
   ```bash
   ./scripts/simulation examples/sample_input.txt
   ```

3. View or analyze the output file (e.g., combined_stages.dot) generated in the working directory.

## Development

### Running Tests

The project uses pytest for testing. To run the tests, execute the following command:

```bash
pytest
```

