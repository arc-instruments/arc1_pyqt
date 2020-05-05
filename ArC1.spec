# PyInstaller spec file. This only targets Windows presently
# The script is driven from the following environment variables
#
# ARC_PYI_PATHEX (mandatory): This is the full path of the arc1_pyqt source
# ARC_PYI_CONSOLE (optional): Set to 0 to disable the console window

import os
import os.path

try:
    PATHEX = os.environ['ARC_PYI_PATHEX']
except KeyError:
    raise ValueError("Environment variable ARC_PYI_PATHEX must be set to the "
            "full path of your arc1_pyqt source")

CONSOLE = bool(int(os.environ.get('ARC_PYI_CONSOLE', 1)))

added_files = [('arc1pyqt/Graphics/*.png','arc1pyqt/Graphics'),
        ('arc1pyqt/ProgPanels/*.py','arc1pyqt/ProgPanels'),
        ('arc1pyqt/GeneratedUiElements/*.py','arc1pyqt/GeneratedUiElements'),
        ('arc1pyqt/ProgPanels/Basic/*.py','arc1pyqt/ProgPanels/Basic'),
        ('arc1pyqt/ProgPanels/Basic/Loops/*.py','arc1pyqt/ProgPanels/Basic/Loops'),
        ('arc1pyqt/Helper/*.txt','arc1pyqt/Helper'),
        ('arc1pyqt/source.txt','arc1pyqt')]


a = Analysis(['main.py'],
        pathex=[PATHEX],
        binaries=None,
        datas=added_files,
        hiddenimports=['arc1pyqt', 'scipy', 'scipy.optimize',
            'scipy.linalg', 'scipy.stats'],
        hookspath=[],
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=None)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz,
        a.scripts,
        exclude_binaries=True,
        name='ArC ONE Control',
        debug=False,
        strip=False,
        upx=True,
        icon=os.path.join('Graphics', 'applogo.ico'),
        console=CONSOLE)

coll = COLLECT(exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='ArC ONE Control')

# vim:ft=python
