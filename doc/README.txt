adjustFanucFiles

Applies a quadrupole correction to plFanuc files (plug plate drill files)
in an attempt to model out reproducible positioning error in our mill.

To use:
- Create a file in your home directory named ".adjustFanucFiles.dat" that looks like this (using "INI" file format; you may use : instead of = if you prefer):

[quadrupole]
mag = 32.0e-6
angle = -38.33

- Drop the files you wish to convert onto the Mac application (or run the application from the command line and specify the files to be converted on the command line).

For dependencies and build instructions see BuildForMac/README.html.
