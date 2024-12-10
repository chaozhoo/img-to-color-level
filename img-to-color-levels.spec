# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import site
from PyInstaller.utils.hooks import collect_data_files

# 获取 tkdnd 相关文件
datas = collect_data_files('tkinterdnd2')

block_cipher = None

a = Analysis(
    ['img-to-color-levels.py'],
    pathex=[],
    binaries=[],
    datas=datas,  # 添加收集到的数据文件
    hiddenimports=['tkinterdnd2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 手动添加 tkdnd 文件
site_packages = site.getsitepackages()[0]
tkdnd_path = os.path.join(site_packages, 'tkinterdnd2')
if os.path.exists(tkdnd_path):
    for root, dirs, files in os.walk(tkdnd_path):
        for file in files:
            if file.startswith('tkdnd'):
                source = os.path.join(root, file)
                target = os.path.join('tkinterdnd2', file)
                a.datas += [(target, source, 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='img-to-color-levels',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 临时改为True以查看错误信息
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ico\\8bit-mofang_48x48.ico'
)
