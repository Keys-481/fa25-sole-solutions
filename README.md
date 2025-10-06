# Senior Capstone Project

## Creators: 
John Halpin: <johnhalpin@u.boisestate.edu>

Chase Davis: <chasedavis233@u.boisestate.edu>

Nathan Rings: <nathanrings@u.boisestate.edu>

Ryan Macfarlane: <ryanmacfarlane@u.boisestate.edu>


[![Python application](https://github.com/Keys-481/fa25-sole-solutions/actions/workflows/python-app.yml/badge.svg)](https://github.com/Keys-481/fa25-sole-solutions/actions/workflows/python-app.yml)

## Building and running the executable:
 ### Usable enviorments -
 * Windows 10 / 11 (PowerShell or Git Bash)
 * macOS (Monterey 12+, Ventura, Sonoma)
 * Linux / WSL2 (Ubuntu recommended)

 ##### 💡 Python 3.12 is required for packaging — this ensures compatibility with Tkinter on all systems.

 # Step 1: Open a Terminal in the Project Directory

Navigate to the root of the cloned repository:

cd fa25-sole-solutions

# Step 2: Build the Application

Run the following command in your terminal:

PACKAGE=1 bash build.sh

(If using windows POWERSHELL USE THIS INSTEAD):

$env:PACKAGE="1"; bash build.sh

# Step 3: Locate the Executable

After the build completes, a new dist/ folder will appear in your project directory.

Depending on your system:


| OS | Output | How to Run |
| :------- | :------- | :------- |
| Windows | dist/SoleSolutions.exe | Double-click the .exe or run: .\dist\SoleSolutions.exe |
| macOS | dist/SoleSolutions.app | Run: open dist/SoleSolutions.app |
| Linux/WSL | dist/SoleSolutions | Run: ./dist/SoleSolutions |


⚠️ On macOS, if the app doesn’t open due to Gatekeeper, right-click → Open → confirm.


# Step 4: Rebuild or Clean (Optional)

If you need a fresh start before building again:

Run:
bash clean.sh


Then rebuild with:

PACKAGE=1 bash build.sh

