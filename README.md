# Improvement and Redesign of Web Interface in Connection with Drone Inspections

## Installer Version 
To install the virtual environment simply run the "unix_start.sh" file or "windows_start.bat" file depending on the operating system. Unix should work on Mac OS as well. 
Running the start script again afterwards does not install everything again, it checks if the virtual environment already is installed.

We have made changes to the file "limic/serve.py" and everything in the "leaflet" folder. To see which functions we have added in LiMiC, look for the "ADDED JONAS EMIL" comment in the file "limic/serve.py". Everything in the "leaflet" folder is our own code.

To run this version Python 3.9 is required, if you get any errors while running, try changing "python3" to "python" in the executable files and run again, or vice versa. If it still doesn't work, use the pipenv version.

The pipenv version works similarly to our InstallerVersion, they just vary in the setup/virtual environment itself.

This version does NOT use pipenv to run LiMiC. 
