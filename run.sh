#!/usr/bin/env bash
# This script ensures a Python virtual environment is set up, installs dependencies,
# then runs two Python scripts ('uploader' and 'collector') in parallel.
# It monitors both processes and terminates all scripts if any one of them stops.
# It also provides a live, combined log stream from both scripts.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- 1. Detect Operating System ---
# Determine if the host is Windows-based or Unix-based to use the correct paths and commands.
case "$OSTYPE" in
  linux*|darwin*)
    OS_TYPE="unix"
    PYTHON_CMD="python3"
    ;;
  msys*|cygwin*|win32*)
    OS_TYPE="windows"
    PYTHON_CMD="python"
    ;;
  *)
    echo "Warning: Unknown OSTYPE '$OSTYPE', assuming Unix-like."
    OS_TYPE="unix"
    PYTHON_CMD="python3"
    ;;
esac
echo "✅ Detected OS: $OS_TYPE"

# --- 2. Create Virtual Environment if it doesn't exist ---
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Creating Python virtual environment in ./$VENV_DIR ..."
  # Use the python command determined by the OS detection step.
  "$PYTHON_CMD" -m venv "$VENV_DIR"
  echo "✅ Virtual environment created."
fi

# --- 3. Activate Virtual Environment ---
# Activate the venv using the correct script for the detected OS.
if [ "$OS_TYPE" = "windows" ]; then
  source "$VENV_DIR/Scripts/activate"
else
  source "$VENV_DIR/bin/activate"
fi
echo "✅ Activated venv: $(which python) ($(python --version))"

# --- 4. Install Python Dependencies ---
# Check for a requirements.txt file and install the packages listed within it.
# This ensures that modules like 'requests' are available to the scripts.
if [ -f "requirements.txt" ]; then
  echo "📦 Installing/updating dependencies from requirements.txt..."
  python -m pip install -r requirements.txt
  echo "✅ Dependencies are up to date."
else
  echo "⚠️ Warning: requirements.txt not found. Skipping dependency installation."
  echo "   Your scripts may fail if they have external dependencies."
fi

# --- 5. Prepare Log Directory ---
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
# Clear old logs for a clean run
> "$LOG_DIR/uploader.log"
> "$LOG_DIR/collector.log"

# --- 6. Define Cleanup Function ---
# This function will be called to ensure all background processes are stopped.
cleanup() {
  echo
  echo "🛑 Terminating processes..."
  # The 'kill' command might fail if the process is already dead.
  # '2>/dev/null' suppresses "No such process" errors.
  # The '|| true' ensures the script doesn't exit with an error if kill fails.
  kill $PID_UPLOADER $PID_COLLECTOR $TAIL_PID 2>/dev/null || true
  echo "✅ Cleanup complete."
}

# --- 7. Set Trap for Graceful Shutdown ---
# The 'trap' command catches signals and executes the 'cleanup' function.
# SIGINT is sent on Ctrl+C.
# SIGTERM is a generic termination signal.
# EXIT is triggered whenever the script finishes, ensuring cleanup always runs.
trap cleanup SIGINT SIGTERM EXIT

# --- 8. Run Scripts in Parallel ---
echo "🚀 Starting uploader/main.py ..."
python -u -X utf8 uploader/main.py > "$LOG_DIR/uploader.log" 2>&1 &
PID_UPLOADER=$!

echo "🚀 Starting collector/main.py ..."
python -u -X utf8 collector/main.py > "$LOG_DIR/collector.log" 2>&1 &
PID_COLLECTOR=$!

echo
echo "🔥 Both processes are running in the background:"
echo "   • Uploader (PID $PID_UPLOADER) → logs/uploader.log"
echo "   • Collector (PID $PID_COLLECTOR) → logs/collector.log"
echo

# --- 9. Show Live Logs ---
echo "📜 Tailing logs in real-time. Press Ctrl+C to stop everything."
echo "------------------------------------------------------------"
# Start tailing the log files in the background and save its PID.
tail -f "$LOG_DIR/uploader.log" "$LOG_DIR/collector.log" &
TAIL_PID=$!

# --- 10. Monitor Processes ---
# This loop is the key to the new logic. It checks if both python processes are still running.
# If the loop exits, it means at least one process has stopped. The EXIT trap will then trigger the cleanup.
while kill -0 $PID_UPLOADER >/dev/null 2>&1 && kill -0 $PID_COLLECTOR >/dev/null 2>&1; do
  # Sleep for a short duration to avoid consuming too much CPU.
  sleep 1
done

echo "------------------------------------------------------------"
echo "🚦 One of the Python processes has stopped. Initiating shutdown of all processes."

# The EXIT trap will now automatically handle the cleanup.
