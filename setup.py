from setuptools import find_packages
from distutils.core import setup, Command
from distutils.command.build import build
import os, sys
import os.path
import glob

__HERE__ = os.path.abspath(os.path.dirname(__file__))
__VERSION_FILE__ = os.path.join(__HERE__, 'arc1pyqt', 'version.txt')
__VERSION_SEMVER__ = open(__VERSION_FILE__).read().splitlines()[1].strip()

__NAME__ = "arc1_pyqt"
__DESC__ = "ArC1 Control Interface"
__MAINTAINER__ = "Spyros Stathopoulos"
__EMAIL__ = "devel@arc-instruments.co.uk"
__VERSION__ = __VERSION_SEMVER__.replace('-','')
__URL__ = "http://www.arc-instruments.co.uk/products/arc-one/"

if os.path.exists(os.path.join(__HERE__, "README.md")):
    with open(os.path.join(__HERE__, "README.md"), encoding='utf-8') as readme:
        __LONG_DESC__ = readme.read()
else:
    __LONG_DESC__ = __DESC__


requirements = [
    'numpy>=1.18.0',
    'PyQt5>=5.12.0',
    'pyqtgraph>=0.12.3',
    'pyserial>=3.0',
    'requests>=2.20.0',
    'scipy>=1.3.0',
    'semver>=2.7.0',
    "importlib-resources>=1.1.0; python_version < '3.7'",
    "dataclasses>=0.7; python_version < '3.7'",
    "pywin32>=222; sys_platform == 'win32'"
]


class BuildUIs(Command):

    description = "Generate python files from Qt UI files"
    user_options = []

    def compile_ui(self, src, dst):
        """
        Compile UI file `src` into the python file `dst`. This is similar to
        what the pyuic script is doing but with some predefined values.
        """

        import PyQt5.uic as uic

        out = open(dst, 'w', encoding='utf-8')

        # see the docstring of PyQt5.uic.compileUi for more!
        uic.compileUi(src, out, execute=False, indent=4)
        out.close()

    def compile_all_uis(self):

        # Find the current working directory (ie. the folder this script resides
        # in). Then find out where the UI files are stored and setup the output
        # directory.
        uidir = os.path.join(__HERE__, 'uis')
        outdir = os.path.join(__HERE__, 'arc1pyqt', 'GeneratedUiElements')

        # Check if outdir exists but is not a directory; in that case
        # bail out!
        if not os.path.isdir(outdir) and os.path.exists(outdir):
            print("%s exists but is not a directory; aborting" % outdir)
            sys.exit(1)

        # Load up all UI files from `uidir`...
        uis = glob.glob(os.path.join(uidir, "*.ui"))
        generated = []

        # ... and convert them into python classes in `outdir`.
        for ui in uis:
            # target filename is the same as source with the .py suffix instead
            # of .ui.
            fname = os.path.splitext(os.path.basename(ui))[0]
            target = os.path.join(outdir, "%s.py" % fname)

            print("[UIC] Generating %s " % target, file=sys.stderr)
            self.compile_ui(ui, target)
            generated.append(target)

        # clean up py files with no UI mapping
        for pyfile in glob.glob(os.path.join(outdir, "*.py")):
            if pyfile not in generated:
                # but please keep __init__.py
                if os.path.basename(pyfile).lower() == "__init__.py":
                    continue
                print("[UIC] Cleaning unmapped file %s" % pyfile, \
                        file=sys.stderr)
                os.remove(pyfile)

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        self.compile_all_uis()


class Build(build):

    user_options = build.user_options + []

    def run(self):
        self.run_command("build_uis")
        super().run()


cmdclass = {}
cmdclass['build_uis'] = BuildUIs
cmdclass['build'] = Build

# make sure we are not bundling local dev versions of pyqtgraph
packages = find_packages(exclude=['pyqtgraph', 'pyqtgraph.*'],
    include=['arc1pyqt', 'arc1pyqt.*'])

setup(
    name = __NAME__,
    version = __VERSION__,
    description = __DESC__,
    long_description = __LONG_DESC__,
    long_description_content_type='text/markdown',
    author = __MAINTAINER__,
    author_email = __EMAIL__,
    url = __URL__,
    project_urls={
        "Bug Tracker": "https://github.com/arc-instruments/arc1_pyqt/issues",
        "Source Code": "https://github.com/arc-instruments/arc1_pyqt"
    },
    license = 'GPL3',
    platforms = ['any'],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",

    ],
    packages = packages,
    python_requires = '>=3.6',
    install_requires = requirements,
    entry_points = {
        'console_scripts': ['arc1pyqt = arc1pyqt.main:main']
    },
    package_data = {
        'arc1pyqt': ['Graphics/*png', 'Graphics/*svg', 'Graphics/*ico',\
            'version.txt', 'Helper/*']
    },
    cmdclass = cmdclass
)
