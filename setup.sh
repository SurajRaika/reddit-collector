#!/bin/bash


# Detect OS and activate venv accordingly
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows"
    source venv/Scripts/activate
elif [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    echo "Detected Linux/macOS"
    source venv/bin/activate
else
    echo "Unsupported OS. Please activate manually."
fi

# Confirm activation
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment activated!"
else
    echo "Failed to activate virtual environment."
fi
