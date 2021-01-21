# virtual entry point for user provided panels
# all non-builtin modules are "mounted" under the namespace
# `arc1pyqt.ExtPanels`. This pseudo-module ensures that the
# package is available otherwise all internal resolution of
# modules will fail with "arc1pyqt.ExtPanels is not a
# package".
# Probably a more elegant solution is needed here by providing
# a custom module loader based on importlib.abc.Loader and
# a virtual module registry similar to
# https://github.com/brettlangdon/virtualmod
