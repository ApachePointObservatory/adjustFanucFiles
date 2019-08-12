#!/usr/bin/env python

"""Adjust plFanuc drilling files

History:
2011-02-25 ROwen
2011-03-01 ROwen    Modified to handle mm or inches, or a mix.
                    Modified to ignore "Unadjusted" in file names when generating output file names.
                    Present a clearer error message if the configuration data file is missing.
2011-03-04 ROwen    Modified to always output 5 digits after the decimal point (and ignore inches vs. mm)
                    since the Fanuc controllers can take the extra digits.
                    When naming output files put Adjusted right after plFanuc if possible.
2011-08-01 ROwen    Version 1.2:
                    Modified to skip files whose name does not match plDrillPos*.par.
                    Modified to not overwrite existing files and log a warning instead.
                    Bug fix: if the name didn't contain "Unadjusted" then an error occurred.
2011-08-02 ROwen    Improved testing of adjusted files.
2011-10-11 ROwen    Added __all__; moved __main__ to a new script in bin/.
2015-10-09 CSayres  File names changed from plFaunic to pl(North|South)Faunic, fix filename naming conventions.
"""
import math
import os.path
import re
# import ConfigParser
from configparser import RawConfigParser
import traceback
# import Tkinter
import numpy
import scipy.optimize
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import RO.Constants
import RO.OS
import RO.StringUtil
import RO.Wdg
import fitPlugPlateMeas.fitData as fitData

__all__ = ["__version__", "AdjustFanucFilesWdg", "getModel", "processFile"]

__version__ = "1.2.2"

fileNameSubRE = re.compile("pl(.*)Fanuc(?:Unadjusted)?(.*)", re.IGNORECASE)
xyPosRE  = re.compile(r"^(.* )X([-0-9.]+) +Y([-0-9.]+)( .*)?$")

def getModel(configPath):
    if not os.path.isfile(configPath):
        raise RuntimeError("file not found")
    config = RawConfigParser()
    config.read(configPath)
    qpMag = config.getfloat("quadrupole", "mag")
    qpAngle = config.getfloat("quadrupole", "angle")

    model = fitData.QuadrupoleModel()
    model.setMagnitudeAngle(qpMag, qpAngle)
    return model

def processFile(filePath, model, logWdg=None):
    """Process one plFanuc file.

    Convert lines that look like this:
    ...G60 X... Y... ...
    """
    if not model:
        return
    fileDir, fileName = os.path.split(filePath)

    baseName, ext = os.path.splitext(fileName)
    # reject files with "adjusted" in their name without rejecting "unadjusted";
    # this test is for files where "adjusted" is in an odd location
    lowBaseName = baseName.lower()
    if "adjusted" in lowBaseName and "unadjusted" not in lowBaseName:
        return

    # output name = input name - "Unadjusted" + "Adjusted"
    # outBaseName = fileNameSubRE.sub(r"FanucAdjusted\1", baseName)
    outBaseName = baseName.replace("FanucUnadjusted", "FanucAdjusted")
    if outBaseName == baseName:
        outBaseName = outBaseName + "Adjusted"
    outFileName = outBaseName + ".txt"
    outFilePath = os.path.join(fileDir, outFileName)
    if os.path.exists(outFilePath):
        if logWdg:
            logWdg.addMsg("Skipping %s: %s already exists" % (fileName, outFileName), severity=RO.Constants.sevWarning)
        return

    qpMag, qpAngle = model.getMagnitudeAngle()

    # process the file by first reading in all the original data
    # and accumulating the output, then write it all at once;
    # that way if there is an error in the input file, no output file is written
    adjComment = "(Adjusted qpMag=%s qpAngle=%s version=%s)\n" % (qpMag, qpAngle, __version__)
    lineNum = 0
    outDataList = []
    with open(filePath, "rU") as inFile:
        numAdj = 0
        for line in inFile:
            lineNum += 1
            if lineNum == 3:
                outDataList.append(adjComment)
            if line.lstrip().lower().startswith("(adjusted"):
                if logWdg:
                    logWdg.addMsg("Skipping %s: already adjusted" % (fileName,), severity=RO.Constants.sevWarning)
                return
            match = xyPosRE.match(line)
            if match:
                prefix, xPos, yPos, postfix = match.groups("")
                adjXYPos = model.applyOne([xPos, yPos], doInverse=True)
                outDataList.append("%sX%0.5f Y%0.5f%s\n" % \
                    (prefix, adjXYPos[0], adjXYPos[1], postfix))
                numAdj += 1
            else:
                outDataList.append(line)
    with open(outFilePath, "w") as outFile:
        for line in outDataList:
            outFile.write(line)
    if logWdg:
        logWdg.addMsg("Wrote %s; adjusted %s x,y positions from %s" % (outFileName, numAdj, fileName))

class AdjustFanucFilesWdg(RO.Wdg.DropletApp):
    """Adjust plFanuc drilling files to compensate for systematic errors in the drilling machine.

    Apples a Quadrupole correction to the hole positions.

    The coefficients are contained in ~/.adjustFanucFiles.dat, which must have INI file format:
    [quadrupole]
    mag: <quadrupole magnitude>
    angle: <quadrupole angle in deg>
    """
    def __init__(self, master, filePathList=None):
        """Construct an AdjustFanucFilesWdg

        Inputs:
        - master: master widget; should be root
        - filePathList: list of files to process
        """
        RO.Wdg.DropletApp.__init__(self,
            master = master,
            width = 135,
            height = 20,
            recursionDepth = 1,
            patterns = "plFanuc*.par",
            exclPatterns = "plFanucAdjusted*.par",
            exclDirPatterns = ".*",
        )

        self.logWdg.addMsg("""Adjust Fanuc Files version %s""" % (__version__,))

        homeDir = RO.OS.getHomeDir()
        configPath = os.path.join(homeDir, ".adjustFanucFiles.dat")
        self.model = None
        try:
            self.model = getModel(configPath)

            self.logWdg.addMsg("Config file: %s" % (configPath,))
            self.logWdg.addMsg("Quadrupole magnitude = %s, angle = %s deg" % (qpMag, qpAngle))

        except Exception as e:
            self.logWdg.addMsg("Error reading %s: %s" % (configPath, RO.StringUtil.strFromException(e)), severity=RO.Constants.sevError)
            self.logWdg.addMsg("Please quit, fix the config file and try again", severity=RO.Constants.sevError)

        if filePathList:
            self.processFileList(filePathList)

    def processFile(self, filePath):
        return processFile(filePath, self.model, self.logWdg)
