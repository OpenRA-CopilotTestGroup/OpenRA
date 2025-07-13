#!/bin/bash

# 尝试获取窗口位置（Safari 可替换为 XQuartz 或你实际的应用名）
WINDOW_BOUNDS=$(osascript -e 'try
  tell application "XQuartz" to get bounds of window 1
end try' 2>/dev/null)

# 如果获取失败，使用全屏
if [ -z "$WINDOW_BOUNDS" ]; then
  echo "❌ 获取窗口失败，使用全屏捕获"
  ffmpeg -f avfoundation -pixel_format bgr0 -framerate 30 -i "1:none" \
    -vf "format=yuvj420p" \
    -f mjpeg -q:v 4 http://localhost:8080/video.ffm
else
  echo "✅ 成功获取窗口位置：$WINDOW_BOUNDS"

  # 拆分坐标
  IFS=', ' read -r LEFT TOP RIGHT BOTTOM <<< "$WINDOW_BOUNDS"
  WIDTH=$((RIGHT - LEFT))
  HEIGHT=$((BOTTOM - TOP))

  echo "📐 捕获区域: $WIDTH x $HEIGHT @ ($LEFT, $TOP)"

  ffmpeg -f avfoundation -pixel_format bgr0 -framerate 15 -i "1:none" \
    -vf "crop=${WIDTH}:${HEIGHT}:${LEFT}:${TOP},format=yuvj420p" \
    -f mjpeg -q:v 4 http://localhost:8080/video.ffm
fi
