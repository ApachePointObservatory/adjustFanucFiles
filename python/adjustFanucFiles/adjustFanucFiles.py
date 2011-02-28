#!/usr/bin/env python
from __future__ import with_statement
"""Adjust plFanuc drilling files

History:
2011-02-25 ROwen
"""
import math
import os.path
import re
import ConfigParser
import traceback
import Tkinter
import numpy
import scipy.optimize
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import RO.Constants
import RO.OS
import RO.StringUtil
import RO.Wdg
import fitPlugPlateMeas.fitData as fitData

__version__ = "1.0"

plateIDRE = re.compile(r"^Plug Plate: ([0-9a-zA-Z_]+) *(?:#.*)?$", re.IGNORECASE)
measDateRE = re.compile(r"^Date: ([0-9-]+) *(?:#.*)?$", re.IGNORECASE)

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
            font = "Courier 12", # want a fixed width font
        )
        
        self.numDig = 4 # number of digits after the decimal point for adjusted positions

        self.logWdg.addMsg("""Adjust Fanuc Files version %s""" % (__version__,))
        
        homeDir = RO.OS.getHomeDir()
        config = ConfigParser.RawConfigParser()
        configPath = os.path.join(homeDir, ".adjustFanucFiles.dat")
        try:
            config.read(configPath)
            qpMag = config.getfloat("quadrupole", "mag")
            qpAngle = config.getfloat("quadrupole", "angle")
            
            self.logWdg.addMsg("Config file: %s" % (configPath,))
            self.logWdg.addMsg("Quadrupole magnitude = %s, angle = %s deg" % (qpMag, qpAngle))

            self.model = fitData.QuadrupoleModel()
            self.model.setMagnitudeAngle(qpMag, qpAngle)
        except Exception, e:
            self.logWdg.addMsg("Error reading %s: %s" % (configPath, RO.StringUtil.strFromException(e)), severity=RO.Constants.sevError)
            self.logWdg.addMsg("Please quit, fix the config file and try again")

        self.lineRE = re.compile(r"^(.* )?G60 X([-0-9.]+) +Y([-0-9.]+)( .*)?$")
            
        if filePathList:
            self.processFileList(filePathList)

    def processFile(self, filePath):
        """Process one plFanuc file.
        
        Convert lines that look like this:
        ...G60 X... Y... ...
        """
        fileDir, fileName = os.path.split(filePath)
        
        baseName, ext = os.path.splitext(fileName)
        if ext.lower() != ".par":
            raise RuntimeError("Filename must end with .par")
        outFileName = "%sAdjusted%s" % (baseName, ext)
        outFilePath = os.path.join(fileDir, outFileName)
        
        qpMag, qpAngle = self.model.getMagnitudeAngle()
            
        self.logWdg.addMsg("Converting %s to %s" % (fileName, outFileName))
        adjComment = "(Adjusted qpMag=%s qpAngle=%s)\n" % (qpMag, qpAngle,)
        lineNum = 0
        with file(filePath, "rU") as inFile:
            with file(outFilePath, "w") as outFile:
                numAdj = 0
                for line in inFile:
                    lineNum += 1
                    if lineNum == 3:
                        outFile.write(adjComment)
                    if line.lower().startswith("(adjusted"):
                        raise RuntimeError("File has already been adjusted!")
                    match = self.lineRE.match(line)
                    if match:
                        prefix, xPos, yPos, postfix = match.groups("")
                        adjXYPos = self.model.applyOne([xPos, yPos], doInverse=True)
                        outFile.write("%sG60 X%0.*f Y%0.*f%s\n" % \
                            (prefix, self.numDig, adjXYPos[0], self.numDig, adjXYPos[1], postfix))
                        numAdj += 1
                    else:
                        outFile.write(line)
        self.logWdg.addMsg("    adjusted %s x,y positions" % (numAdj,))

if __name__ == "__main__":
    import sys
    filePathList = sys.argv[1:]
    # strip first argument if it starts with "-", as happens when run as a Mac application
    if filePathList and filePathList[0].startswith("-"):
        filePathList = filePathList[1:]

    root = Tkinter.Tk()
    root.title("AdjustFanucFiles")
    
    fitPlugPlateWdg = AdjustFanucFilesWdg(master=root, filePathList=filePathList)
    fitPlugPlateWdg.pack(side="left", expand=True, fill="both")
    root.mainloop()
