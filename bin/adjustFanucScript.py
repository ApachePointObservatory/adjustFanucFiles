#!/usr/bin/env python
"""Adjust plFanuc drilling files

History:
2015-1-21 CS initial creation
2015-10-09 CS allow for North and South in the fanuc file names.
2019-08-12 CS add adjustFanucFiles.dat to repo (was looking for it in users home dir)
"""
import argparse
import os
import glob
import re

import RO

from adjustFanucFiles import getModel, processFile

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Script to apply quadrapole correction to plFaunuc files")
    parser.add_argument('path', type=str,
                        help='a path to a directory or plFanuc file. If directory, all plFanuc files within that directory are converted.')

    args = parser.parse_args()
    absPath = os.path.abspath(args.path)
    if os.path.isdir(absPath):
        # grab all drill files for conversion
        basePath = absPath
        globStr = os.path.join(absPath, "pl*Fanuc*.par")
        fileList = glob.glob(globStr)
    else:
        # verify a file was passed and it has the right name
        basePath, fileName = os.path.split(absPath)
        if not "FanucUnadjusted" in fileName:
            raise RuntimeError("%s is not a %s file!"%(fileName, "plFanuc"))
        fileList = [fileName]

    productDir = os.getenv("ADJUSTFANUCFILES_DIR")
    configPath = os.path.join(productDir, "etc", "adjustFanucFiles.dat")

    model = getModel(configPath)
    plateNums = []
    for f in fileList:
        plateNums.append(int(re.split("[-.]", f)[1]))
        processFile(f, model)