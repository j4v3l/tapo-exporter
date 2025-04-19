#!/bin/bash

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Upgrade pip and install build tools
pip install --upgrade pip
pip install --upgrade build twine

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

echo "Development environment setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate" 