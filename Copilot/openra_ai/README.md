# Whisper Mic
This repo is based on the work done [here](https://github.com/openai/whisper) by OpenAI.  This repo allows you use use a mic as demo. This repo copies some of the README from the original project.

## build wheel
```python -m build```

## Setup from git repo

1. Create a venv of your choice.
2. Run ```pip install .```

## Setup from wheel

1. Create a venv of your choice.
2. Run ```pip install <wheel file>```. The wheel file can be found under dist folder if you have run ``` python -m build```.

## Run whisper_mic

1. ```whisper_mic [--config <config json>]```
2. Wait util the command show Listening
3. Say something. It will cache the partial commands until you say ```执行命令```.
3. Say ```执行命令```. It will trigger the command running .

