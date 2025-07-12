#!/bin/bash

PORT=${COPILOT_PORT:-7445}
SAVE=${SAVE_FILE:-Test01}

echo "[RUN] Starting OpenRA with port $PORT and save file $SAVE..."

# 如果你用 wine 编译出的 EXE 版本
./OpenRA\ -\ Copilot.app/Contents/MacOS/Launcher Game.CopilotPort=$PORT Game.LoadSave=$SAVE
