# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ["nimble/launch.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "PyQt5.QtPrintSupport",
        "OpenGL",
        "glcontext",
        "moderngl.loaders.program",
        "moderngl_window.loaders.program",
        "moderngl_window.loaders.program.single",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
splash = Splash(
    "nimble/resources/img/splash.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash,
    splash.binaries,
    name="nimble",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon="nimble/resources/img/logo.ico",
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
