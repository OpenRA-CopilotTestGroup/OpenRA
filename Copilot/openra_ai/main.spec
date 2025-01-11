# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

block_cipher = None

# Collect OpenRA_Copilot_Library files
openra_lib_files = collect_data_files('OpenRA_Copilot_Library')

# Collect Samples files
samples_files = collect_data_files('Samples')

# Config files in whisper_mic
config_files = [
    ('config/config.json', 'config'),
    ('config/config.yaml', 'config'),
    ('config/api.json', 'config')
]

# Combine all data files
#all_data_files = config_files + openra_lib_files + samples_files
all_data_files = openra_lib_files + samples_files

a = Analysis(
    ['./uni_mic/cli.py'],
    pathex=['.'],
    binaries=[],
    datas=all_data_files,
    hiddenimports=[
        'uni_mic.rafuncs',
        'uni_mic.utils',
        'uni_mic.gui',
        'uni_mic.config',
        'uni_mic.asr_module',
        'uni_mic.asr_manager',
        'uni_mic.audio_listener',
        'OpenRA_Copilot_Library',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'torch', 'tensorflow'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OpenRA_Copilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Changed to True to see any potential errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=False
)
