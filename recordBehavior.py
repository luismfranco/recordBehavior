"""
Modules

"""

import sys; sys.path.append("src")
import json
import tkinter as tk
import recordBehaviorGUI


"""
Configuration

"""

f = open("config/package.json")
configurationData = json.load(f)
f.close()

""" 
Run Application

"""

mainWindow = tk.Tk()
recordBehaviorGUI.recordBehaviorGUI(mainWindow, configurationData)
mainWindow.mainloop()