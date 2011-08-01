from __future__ import with_statement
"""The Python portion of the script that builds AdjustFanucFiles

Usage:
% python setup.py [--quiet] py2app

History:
2011-02-28 ROwen    Adapted from the version for fitPlugPlateMeas
"""
import os
import shutil
import subprocess
import sys
from setuptools import setup

# add various bits to the path (but preferably use eups instead)
pkgRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pythonRoot = os.path.join(pkgRoot, "python", "adjustFanucFiles")
pathList = [pythonRoot]
if os.path.isfile("extraPaths.txt"):
    with file("extraPaths.txt") as pathFile:
        for pathStr in pathFile:
            pathStr = pathStr.strip()
            if not pathStr or pathStr.startswith("#"):
                continue
            pathList.append(pathStr)
sys.path = pathList + sys.path

import adjustFanucFiles

appName = "AdjustFanucFiles"
mainScript = "adjustFanucFiles.py"
mainProg = os.path.join(pythonRoot, mainScript)
appPath = os.path.join("dist", appName + ".app")
iconFile = "%s.icns" % appName
versStr = adjustFanucFiles.__version__

inclModules = (
#    "FileDialog",
)
# packages to include recursively
inclPackages = (
#    "RO",
)

# see plistlib for more info
plist = dict(
    CFBundleName                = appName,
    CFBundleExecutable          = appName,
    CFBundleShortVersionString  = versStr,
    CFBundleGetInfoString       = "%s %s" % (appName, versStr),
    CFBundleDocumentTypes       = [
        dict(
            CFBundleTypeName = "File",
            CFBundleTypeRole = "Editor",
            LSItemContentTypes = [
                "public.plain-text",
                "public.text",
                "public.data",
            ],
        ),
        dict(
            CFBundleTypeName = "Folder",
            CFBundleTypeRole = "Viewer",
            LSItemContentTypes = [
				"public.folder",
            ],
        ),
    ],
    LSPrefersPPC                = False,
)

setup(
    app = [mainProg],
    setup_requires = ["py2app"],
    options = dict(
        py2app = dict (
            plist = plist,
            iconfile = iconFile,
            includes = inclModules,
            packages = inclPackages,
        )
    ),
)

print "*** Creating disk image ***"
appName = "%s_%s_Mac" % (appName, versStr)
destFile = os.path.join("dist", appName)
args=("hdiutil", "create", "-srcdir", appPath, destFile)
retCode = subprocess.call(args=args)
