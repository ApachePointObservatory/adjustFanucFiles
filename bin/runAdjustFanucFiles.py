#!/usr/bin/env python
"""Adjust plFanuc drilling files

History:
2011-10-11 ROwen    Broken out from the the python library code.
"""
import sys
import Tkinter
import adjustFanucFiles

filePathList = sys.argv[1:]
# strip first argument if it starts with "-", as happens when run as a Mac application
if filePathList and filePathList[0].startswith("-"):
    filePathList = filePathList[1:]

root = Tkinter.Tk()
root.title("AdjustFanucFiles")

fitPlugPlateWdg = adjustFanucFiles.AdjustFanucFilesWdg(master=root, filePathList=filePathList)
fitPlugPlateWdg.pack(side="left", expand=True, fill="both")
root.mainloop()
