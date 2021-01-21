# PyInstaller spec file. This only targets Windows presently
# The script is driven from the following environment variables
#
# ARC_PYI_PATHEX (mandatory): This is the full path of the arc1_pyqt source
# ARC_PYI_CONSOLE (optional): Set to 0 to disable the console window

import os
import sys
import os.path
import semver

try:
    PATHEX = os.environ['ARC_PYI_PATHEX']
except KeyError:
    raise ValueError("Environment variable ARC_PYI_PATHEX must be set to the "
            "full path of your arc1_pyqt source")

CONSOLE = bool(int(os.environ.get('ARC_PYI_CONSOLE', 1)))

__HERE__ = "."
__VERSION_FILE__ = os.path.join(__HERE__, 'arc1pyqt', 'version.txt')
__VERSION_RAW__ = open(__VERSION_FILE__).read().splitlines()[1].strip()
__VERSION_SEMVER__ = semver.VersionInfo.parse(__VERSION_RAW__)

tmpl = open("win32_version_info.tmpl").read()
version_keys = {'major': __VERSION_SEMVER__.major,
    'minor': __VERSION_SEMVER__.minor,
    'patch': __VERSION_SEMVER__.patch,
    'version_text': __VERSION_RAW__}
print(version_keys)
with open(os.path.join("build", "ArC1", "version_info.txt"), 'w') as version_file:
    version_file.write(tmpl.format(**version_keys))


added_files = [('arc1pyqt/Graphics/*.png','arc1pyqt/Graphics'),
        ('arc1pyqt/ProgPanels/*.py','arc1pyqt/ProgPanels'),
        ('arc1pyqt/ExtPanels/*.py','arc1pyqt/ExtPanels'),
        ('arc1pyqt/GeneratedUiElements/*.py','arc1pyqt/GeneratedUiElements'),
        ('arc1pyqt/ProgPanels/Basic/*.py','arc1pyqt/ProgPanels/Basic'),
        ('arc1pyqt/ProgPanels/Basic/Loops/*.py','arc1pyqt/ProgPanels/Basic/Loops'),
        ('arc1pyqt/Helper/*.txt','arc1pyqt/Helper'),
        ('arc1pyqt/version.txt','arc1pyqt')]

modimports=['arc1pyqt', 'scipy', 'scipy.optimize',
    'scipy.linalg', 'scipy.stats']

try:
    import arc1docs
    manual = os.path.join(arc1docs.__path__[0], arc1docs._fname)
    if os.path.exists(manual):
        modimports.append('arc1docs')
        added_files.append((manual, arc1docs.__name__))
except Exception as exc:
    print("Could not find arc1docs, skipping...", exc, file=sys.stderr)

a = Analysis(['run.py'],
        pathex=[PATHEX],
        binaries=None,
        datas=added_files,
        hiddenimports=modimports,
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
        icon=os.path.join('arc1pyqt', 'Graphics', 'applogo.ico'),
        console=CONSOLE,
        version=os.path.join("build", "ArC1", "version_info.txt"))

coll = COLLECT(exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='ArC ONE Control')

# vim:ft=python
