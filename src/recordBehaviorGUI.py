"""
Modules

"""

# GUI modules
import tkinter as tk
from tkinter import font as tkFont
from tkinter import messagebox
from threading import Thread
from PIL import ImageTk, Image
import os
import ntplib
from datetime import datetime
from pathlib import Path

# Cameras and IMU
import imagingcontrol4 as ic4
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
import cv2
import time
import numpy as np
import serial


"""
Application

"""

class recordBehaviorGUI:
    
    """
    Set up GUI

    """
    
    def __init__(self, mainWindow, configurationData):
        
        
        """
        GUI Layout
        
        """
        
        # Geometry and location
        self.mainWindow = mainWindow
        self.mainWindow.title('Record Behavior')
        windowWidth = 900
        windowHeight = 700
        screenWidth = self.mainWindow.winfo_screenwidth()
        screenHeight = self.mainWindow.winfo_screenheight()
        x = (screenWidth/1.35) - (windowWidth/2)
        y = (screenHeight/2) - (windowHeight/2)
        self.mainWindow.geometry('%dx%d+%d+%d' % (windowWidth, windowHeight, x, y))
        self.backGroundColor = self.mainWindow.cget('bg')
        buttonFont = tkFont.Font(family = 'helvetica', size = 12)
        
        # Frame 1: Top Down Camera
        frame1 = tk.Frame(self.mainWindow, width = 300, height = 500) #, bg = 'red')
        frame1.grid(row = 0, column = 0, sticky = 'news')
        
        # Frame 2: Eye Camera
        frame2 = tk.Frame(self.mainWindow, width = 300, height = 500) #, bg = "green")
        frame2.grid(row = 0, column = 1, sticky = 'news')
        
        # Frame 3: IMU
        frame3 = tk.Frame(self.mainWindow, width = 300, height = 500) #, bg = "blue")
        frame3.grid(row = 0, column = 2, sticky = 'news')
        
        # Frame 4: Session Info
        frame4 = tk.Frame(self.mainWindow, width = 900, height = 100) #, bg = "green")
        frame4.grid(row = 1, column = 0, columnspan = 3, sticky = 'news')
        
        # Frame 5: Master controller
        frame5 = tk.Frame(self.mainWindow, width = 900, height = 100) #, bg = "red")
        frame5.grid(row = 2, column = 0, columnspan = 3, sticky = 'news')
        
        
        """
        Session Info
        
        """
        
        # Session booleans
        self.isAnyRecordingOn = False
        self.isAnyPreviewOn = False
            
        # Frame 41: Session Info
        frame41 = tk.Frame(frame4, width = 1050, height = 150)
        frame41.place(anchor = "c", relx = 0.5, rely = 0.5)
        
        # Session info labels
        self.experimentDataLabel = tk.Label(frame41, font = buttonFont, text = "Experiment Data", width = 12, anchor  = 'c')
        self.experimentDataLabel.grid(row = 0, column = 0, columnspan = 6, padx = 10, pady = 10, sticky = 'we')
        entryLabels0 = ["rig", "animal", "block"]
        entryLabels1 = ["user", "path"]
        nCol = 0
        for i in range(len(entryLabels0)):
            tk.Label(frame41, font = buttonFont, text = entryLabels0[i], width = 8, anchor  = 'e').grid(row = 1, column = nCol, padx = 10)
            nCol += 2
        nCol = 0
        for i in range(len(entryLabels1)):
            tk.Label(frame41, font = buttonFont, text = entryLabels1[i], width = 8, anchor  = 'e').grid(row = 2, column = nCol, padx = 10)
            nCol += 2
        
        # Rig ID entry
        self.rigID = configurationData["sessionInfo"]["rigID"]
        self.rigVar = tk.StringVar(value = self.rigID)
        self.rigVar.trace_add("write", self.updatePath)
        self.rigEntry = tk.Entry(frame41, font = 8, width = 14, textvariable = self.rigVar)
        self.rigEntry.grid(row = 1, column = 1, sticky ='w')
        self.rigIDifEmpty = "bestRigInTown"
        
        # Animal ID entry
        self.animalID = configurationData["sessionInfo"]["animalID"]
        self.animalVar = tk.StringVar(value = self.animalID)
        self.animalVar.trace_add("write", self.updatePath)
        self.animalEntry = tk.Entry(frame41, font = 8, width = 14, textvariable = self.animalVar)
        self.animalEntry.grid(row = 1, column = 3, sticky = 'w')
        self.animalIDifEmpty = "mightyMouse"
        
        # Block ID entry
        self.blockID = configurationData["sessionInfo"]["blockID"]
        self.blockVar = tk.StringVar(value = self.blockID)
        self.blockVar.trace_add("write", self.updatePath)
        self.blockEntry = tk.Entry(frame41, font = 8, width = 14, textvariable = self.blockVar)
        self.blockEntry.grid(row = 1, column = 5, sticky = 'w')
        self.blockIDchanged = False
        self.blockIDifEmpty = "0"
        
        # User ID entry
        self.userID = configurationData["sessionInfo"]["user"]
        self.userVar = tk.StringVar(value = self.userID)
        self.userVar.trace_add("write", self.updatePath)
        self.userEntry = tk.Entry(frame41, font = 8, width = 14, textvariable = self.userVar)
        self.userEntry.grid(row = 2, column = 1, sticky ='w')
        self.userIDifEmpty = "heWhoRemains"
        
        # Set up path for saving data
        self.windowsUserName = os.path.basename(os.environ.get('USERPROFILE'))
        self.currentDate = datetime.today().strftime("%y%m%d")
        self.rootDir = configurationData["sessionInfo"]["rootDir"]
        self.defaultPath()
        
        # Path entry
        tk.Label(frame41, font = buttonFont, text = "path", width = 8, anchor  = 'e').grid(row = 2, column = 3, padx = 10)
        self.path = tk.StringVar(value = self.pathForSavingData)
        self.pathEntry = tk.Entry(frame41, font = 8, width = 40, textvariable = self.path)
        self.pathEntry.grid(row = 2, column = 3, columnspan = 6, sticky ='w')
        self.pathEntry.config(state = 'disabled')
        
        # Path checkBox
        self.useCustomPath = tk.BooleanVar(value = False)
        self.customPathBox = tk.Checkbutton(frame41, text = "custom", font = 8, variable = self.useCustomPath, onvalue = True, offvalue = False, command = self.editPath)
        self.customPathBox.grid(row = 2, column = 6, sticky = 'w')
        
        
        """
        Top Down Camera
        
        """
        
        # Initialize the Top Down Camera Class
        self.topDownCam = topDownCamera(self)
        
        # Frame 11: Logo
        frame11 = tk.Frame(frame1, width = 300, height = 200)
        frame11.place(anchor = "c", relx = 0.55, rely = 0.225)
        
        # Frame 12: Camera settings
        frame12 = tk.Frame(frame1, width = 300, height = 225)
        frame12.place(anchor = "c", relx = 0.55, rely = 0.62)
        
        # Frame 13: Preview and Record
        frame13 = tk.Frame(frame1, width = 300, height = 75)
        frame13.place(anchor = "c", relx = 0.55, rely = 0.89)
        
        # Logo
        imagePath = "assets/topDownCamLogo.png"
        img = Image.open(imagePath)
        img = img.resize((200, 200))
        img = ImageTk.PhotoImage(master = frame11, width = 200, height = 200, image = img)
        logo = tk.Label(frame11, image = img)
        logo.place(anchor = "c", relx = 0.5, rely = 0.5)
        logo.image = img
        frame11.lift()
        
        # Top Down Camera settings labels
        self.topDownCamSettingLabel = tk.Label(frame12, font = buttonFont, text = "Top Down Camera Settings", width = 12, anchor  = 'c')
        self.topDownCamSettingLabel.grid(row = 0, column = 0, columnspan = 2, padx = 10, pady = 10, sticky = 'we')
        entryLabels = ["cameraID", "duration", "fps", "width", "height"]
        nrow = 1
        for i in range(len(entryLabels)):
            tk.Label(frame12, font = buttonFont, text = entryLabels[i], width = 8, anchor  = 'e').grid(row = nrow, column = 0, padx = 10)
            nrow += 1
        
        # Camera ID entry
        self.topDownCamID = int(configurationData["topDownCamera"]["cameraID"])
        self.topDownCamIDEntry = tk.Entry(frame12, font = 8, width = 14)
        self.topDownCamIDEntry.insert(0, self.topDownCamID)
        self.topDownCamIDEntry.grid(row = 1, column = 1, sticky ='w')
        
        # Recording duration entry
        self.topDownCamRecordingDuration = int(configurationData["topDownCamera"]["recordingDuration"]) # in seconds
        self.topDownCamDurationEntry = tk.Entry(frame12, font = 8, width = 14)
        self.topDownCamDurationEntry.insert(0, self.topDownCamRecordingDuration)
        self.topDownCamDurationEntry.grid(row = 2, column = 1, sticky ='w')
        
        # Frame rate entry
        self.topDownCamFrameRate = int(configurationData["topDownCamera"]["frameRate"])
        self.topDownCamFrameRateEntry = tk.Entry(frame12, font = 8, width = 14)
        self.topDownCamFrameRateEntry.insert(0, self.topDownCamFrameRate)
        self.topDownCamFrameRateEntry.grid(row = 3, column = 1, sticky ='w')
        
        # Frame width entry
        self.topDownCamFrameWidth = int(configurationData["topDownCamera"]["frameWidth"])
        self.topDownCamFrameWidthEntry = tk.Entry(frame12, font = 8, width = 14)
        self.topDownCamFrameWidthEntry.insert(0, self.topDownCamFrameWidth)
        self.topDownCamFrameWidthEntry.grid(row = 4, column = 1, sticky = 'w')
        
        # Frame height entry
        self.topDownCamFrameHeight = int(configurationData["topDownCamera"]["frameHeight"])
        self.topDownCamFrameHeightEntry = tk.Entry(frame12, font = 8, width = 14)
        self.topDownCamFrameHeightEntry.insert(0, self.topDownCamFrameHeight)
        self.topDownCamFrameHeightEntry.grid(row = 5, column = 1, sticky = 'w')
        
        # Preview button
        self.topDownCamPreviewButton = tk.Button(frame13, text = 'Preview Off', font = buttonFont, width = 12, command = self.topDownCam.previewCamera)
        self.topDownCamPreviewButton.grid(row = 0, column = 0, padx = 10, pady = 10)
        self.topDownCamPreviewButton.bind('<Enter>', lambda e: self.topDownCamPreviewButton.config(fg = 'Black', bg ='#A9C6E3'))
        self.topDownCamPreviewButton.bind('<Leave>', lambda e: self.topDownCamPreviewButton.config(fg = 'Black', bg ='SystemButtonFace'))
        
        # Record button
        self.topDownCamRecordButton = tk.Button(frame13, text = 'Record', font = buttonFont, width = 12, command = self.topDownCam.recordVideo)
        self.topDownCamRecordButton.grid(row = 0, column = 1, padx = 10, pady = 10)
        self.topDownCamRecordButton.bind('<Enter>', lambda e: self.topDownCamRecordButton.config(fg = 'Black', bg ='#DC5B5B'))
        self.topDownCamRecordButton.bind('<Leave>', lambda e: self.topDownCamRecordButton.config(fg = 'Black', bg ='SystemButtonFace'))
        
        
        """
        Eye Camera
        
        """
        
        # Initialize the Eye Camera Class
        self.eyeCam = eyeCamera(self)
       
        # Frame 21: Logo
        frame21 = tk.Frame(frame2, width = 300, height = 200)
        frame21.place(anchor = "c", relx = 0.5, rely = 0.225)
        
        # Frame 22: Camera settings
        frame22 = tk.Frame(frame2, width = 300, height = 225)
        frame22.place(anchor = "c", relx = 0.5, rely = 0.62)
        
        # Frame 23: Preview and Record
        frame23 = tk.Frame(frame2, width = 300, height = 75)
        frame23.place(anchor = "c", relx = 0.5, rely = 0.89)
        
        # Logo
        imagePath = "assets/eyeCamLogo.png"
        img = Image.open(imagePath)
        img = img.resize((200, 200))
        img = ImageTk.PhotoImage(master = frame21, width = 200, height = 200, image = img)
        logo = tk.Label(frame21, image = img)
        logo.place(anchor = "c", relx = 0.5, rely = 0.5)
        logo.image = img
        frame21.lift()
        
        # Eye Camera settings labels
        self.eyeCamSettingLabel = tk.Label(frame22, font = buttonFont, text = "Eye Camera Settings", width = 12, anchor  = 'c')
        self.eyeCamSettingLabel.grid(row = 0, column = 0, columnspan = 2, padx = 10, pady = 10, sticky = 'we')
        entryLabels = ["cameraID", "duration", "fps", "width", "height"]
        nrow = 1
        for i in range(len(entryLabels)):
            tk.Label(frame22, font = buttonFont, text = entryLabels[i], width = 8, anchor  = 'e').grid(row = nrow, column = 0, padx = 10)
            nrow += 1
        
        # Camera ID entry
        self.eyeCamID = int(configurationData["eyeCamera"]["cameraID"])
        self.eyeCamIDEntry = tk.Entry(frame22, font = 8, width = 14)
        self.eyeCamIDEntry.insert(0, self.eyeCamID)
        self.eyeCamIDEntry.grid(row = 1, column = 1, sticky ='w')
        
        # Recording duration entry
        self.eyeCamRecordingDuration = int(configurationData["eyeCamera"]["recordingDuration"]) # in seconds
        self.eyeCamDurationEntry = tk.Entry(frame22, font = 8, width = 14)
        self.eyeCamDurationEntry.insert(0, self.eyeCamRecordingDuration)
        self.eyeCamDurationEntry.grid(row = 2, column = 1, sticky ='w')
        
        # Frame rate entry
        self.eyeCamFrameRate = int(configurationData["eyeCamera"]["frameRate"])
        self.eyeCamFrameRateValue = tk.IntVar(value = self.eyeCamFrameRate)
        self.eyeCamFrameRateEntry = tk.Entry(frame22, font = 8, width = 14, textvariable = self.eyeCamFrameRateValue)
        self.eyeCamFrameRateEntry.grid(row = 3, column = 1, sticky ='w')
        
        # Frame width entry
        self.eyeCamFrameWidth = int(configurationData["eyeCamera"]["frameWidth"])
        self.eyeCamFrameWidthValue = tk.IntVar(value = self.eyeCamFrameWidth)
        self.eyeCamFrameWidthEntry = tk.Entry(frame22, font = 8, width = 14, textvariable = self.eyeCamFrameWidthValue)
        self.eyeCamFrameWidthEntry.grid(row = 4, column = 1, sticky = 'w')
        
        # Frame height entry
        self.eyeCamFrameHeight = int(configurationData["eyeCamera"]["frameHeight"])
        self.eyeCamFrameHeightValue = tk.IntVar(value = self.eyeCamFrameHeight)
        self.eyeCamFrameHeightEntry = tk.Entry(frame22, font = 8, width = 14, textvariable = self.eyeCamFrameHeightValue)
        self.eyeCamFrameHeightEntry.grid(row = 5, column = 1, sticky = 'w')
        
        # Preview button
        self.eyeCamPreviewButton = tk.Button(frame23, text = 'Preview Off', font = buttonFont, width = 12, command = self.eyeCam.previewCamera)
        self.eyeCamPreviewButton.grid(row = 0, column = 0, padx = 10, pady = 10)
        self.eyeCamPreviewButton.bind('<Enter>', lambda e: self.eyeCamPreviewButton.config(fg = 'Black', bg ='#A9C6E3'))
        self.eyeCamPreviewButton.bind('<Leave>', lambda e: self.eyeCamPreviewButton.config(fg = 'Black', bg ='SystemButtonFace'))

        # Record button
        self.eyeCamRecordButton = tk.Button(frame23, text = 'Record', font = buttonFont, width = 12, command = self.eyeCam.recordVideo)
        self.eyeCamRecordButton.grid(row = 0, column = 1, padx = 10, pady = 10)
        self.eyeCamRecordButton.bind('<Enter>', lambda e: self.eyeCamRecordButton.config(fg = 'Black', bg ='#DC5B5B'))
        self.eyeCamRecordButton.bind('<Leave>', lambda e: self.eyeCamRecordButton.config(fg = 'Black', bg ='SystemButtonFace'))
        
        
        """
        IMU
        
        """
        
        # Initialize the IMU Class
        self.IMU = IMU(self)
        
        # Frame 31: Logo
        frame31 = tk.Frame(frame3, width = 300, height = 200)
        frame31.place(anchor = "c", relx = 0.45, rely = 0.225)
        
        # Frame 32: IMU settings
        frame32 = tk.Frame(frame3, width = 300, height = 150)
        frame32.place(anchor = "c", relx = 0.45, rely = 0.55)
        
        # Frame 33: Connect
        frame33 = tk.Frame(frame3, width = 300, height = 75)
        frame33.place(anchor = "c", relx = 0.45, rely = 0.79)
        
        # Frame 34: Preview and Record
        frame34 = tk.Frame(frame3, width = 300, height = 75)
        frame34.place(anchor = "c", relx = 0.45, rely = 0.89)
        
        # Logo
        imagePath = "assets/imuGUILogo.png"
        img = Image.open(imagePath)
        img = img.resize((200, 200))
        img = ImageTk.PhotoImage(master = frame31, width = 200, height = 200, image = img)
        logo = tk.Label(frame31, image = img)
        logo.place(anchor = "c", relx = 0.5, rely = 0.5)
        logo.image = img
        frame31.lift()
        
        # IMU settings labels
        self.IMUSettingLabel = tk.Label(frame32, font = buttonFont, text = "IMU Settings", width = 12, anchor  = 'c')
        self.IMUSettingLabel.grid(row = 0, column = 0, columnspan = 2, padx = 10, pady = 10, sticky = 'we')
        entryLabels = ["COM", "duration"]
        nrow = 1
        for i in range(len(entryLabels)):
            tk.Label(frame32, font = buttonFont, text = entryLabels[i], width = 8, anchor  = 'e').grid(row = nrow, column = 0, padx = 10)
            nrow += 1
        
        # COM ID entry
        self.IMUcomID = int(configurationData["IMU"]["comID"])
        self.IMUcomIDEntry = tk.Entry(frame32, font = 8, width = 14)
        self.IMUcomIDEntry.insert(0, self.IMUcomID)
        self.IMUcomIDEntry.grid(row = 1, column = 1, sticky ='w')
        
        # Recording duration entry
        self.IMUrecordingDuration = int(configurationData["IMU"]["recordingDuration"]) # in seconds
        self.IMUdurationEntry = tk.Entry(frame32, font = 8, width = 14)
        self.IMUdurationEntry.insert(0, self.IMUrecordingDuration)
        self.IMUdurationEntry.grid(row = 2, column = 1, sticky ='w')
        
        # Initialize button
        self.IMUinitializeButton = tk.Button(frame33, text = 'IMU off', font = buttonFont, width = 12, command = self.IMU.initializeIMU)
        self.IMUinitializeButton.grid(row = 0, column = 0, padx = 10, pady = 10)
        self.IMUinitializeButton.bind('<Enter>', lambda e: self.IMUinitializeButton.config(fg = 'Black', bg ='#99D492'))
        self.IMUinitializeButton.bind('<Leave>', lambda e: self.IMUinitializeButton.config(fg = 'Black', bg ='SystemButtonFace'))

        # Preview button
        self.IMUpreviewButton = tk.Button(frame34, text = 'Preview Off', font = buttonFont, width = 12, command = self.IMU.previewIMUdata)
        self.IMUpreviewButton.grid(row = 0, column = 0, padx = 10, pady = 10)
        self.IMUpreviewButton.bind('<Enter>', lambda e: self.IMUpreviewButton.config(fg = 'Black', bg ='#A9C6E3'))
        self.IMUpreviewButton.bind('<Leave>', lambda e: self.IMUpreviewButton.config(fg = 'Black', bg ='SystemButtonFace'))
        
        # Record button
        self.IMUrecordButton = tk.Button(frame34, text = 'Record', font = buttonFont, width = 12, command = self.IMU.recordIMUdata)
        self.IMUrecordButton.grid(row = 0, column = 1, padx = 10, pady = 10)
        self.IMUrecordButton.bind('<Enter>', lambda e: self.IMUrecordButton.config(fg = 'Black', bg ='#DC5B5B'))
        self.IMUrecordButton.bind('<Leave>', lambda e: self.IMUrecordButton.config(fg = 'Black', bg ='SystemButtonFace'))
        
        
        """ 
        Time Offset

        """
        
        self.timeOffsetOn = False
        
        
        """
        GUI Buttons
        
        """
        
        # Frame 51: GUI buttons
        frame51 = tk.Frame(frame5, width = 900, height = 150)
        frame51.place(anchor = "c", relx = 0.5, rely = 0.5)
        
        # Preview button
        self.previewAllButton = tk.Button(frame51, text = 'Preview All', font = buttonFont, width = 15, command = self.previewAll)
        self.previewAllButton.grid(row = 0, column = 0, padx = 20, pady = 10)
        self.previewAllButton.bind('<Enter>', lambda e: self.previewAllButton.config(fg = 'Black', bg ='#A9C6E3'))
        self.previewAllButton.bind('<Leave>', lambda e: self.previewAllButton.config(fg = 'Black', bg ='SystemButtonFace'))
        
        # Record button
        self.recordAllButton = tk.Button(frame51, text = 'Record All', font = buttonFont, width = 15, command = self.recordAll)
        self.recordAllButton.grid(row = 0, column = 1, padx = 20, pady = 10)
        self.recordAllButton.bind('<Enter>', lambda e: self.recordAllButton.config(fg = 'Black', bg ='#DC5B5B'))
        self.recordAllButton.bind('<Leave>', lambda e: self.recordAllButton.config(fg = 'Black', bg ='SystemButtonFace'))

        # Close app button
        self.closeButton = tk.Button(frame51, text = 'Close App', font = buttonFont, width = 15, command = self.closeMainWindow)
        self.closeButton.grid(row = 0, column = 2, padx = 20, pady = 10)
        self.closeButton.bind('<Enter>', lambda e: self.closeButton.config(fg='Black', bg='#AFAFAA'))
        self.closeButton.bind('<Leave>', lambda e: self.closeButton.config(fg='Black', bg='SystemButtonFace'))
        self.mainWindow.protocol('WM_DELETE_WINDOW', self.closeMainWindow)
        
    """ 
    GUI Functions
    
    """
       
    def makePath(self):
        
        # Read current session info
        self.updatePath()
        
        print(self.pathForSavingData)
        
        # Prepare directory to save data
        try:
            Path(self.pathForSavingData).mkdir(parents = True, exist_ok = True)
        except:
            self.defaultPath()
            self.defaultSessionInfo()
            Path(self.pathForSavingData).mkdir(parents = True, exist_ok = True)
            
            
    def defaultPath(self):
        
        try:
            self.pathForSavingData = self.rootDir + self.userID + "\\" + self.animalID + "_" + self.currentDate + "_" + self.blockID + "\\"
        except:
            self.pathForSavingData = "C:\\Users\\" + self.windowsUserName + "\\Documents\\recordBehavior\\Data\\" + self.currentDate + "\\"
            print(" ")
            print(f"WARNING: Path changed to {self.pathForSavingData}")
            print("Make sure there is enough space on disk for your data.")
            print(" ")
    
    def defaultSessionInfo(self):
        
        # Path
        self.topDownCam.pathForSavingData = self.pathForSavingData
        self.eyeCam.pathForSavingData = self.pathForSavingData
        self.IMU.pathForSavingData = self.pathForSavingData
        
        # Rig
        self.topDownCam.rigID = self.rigIDifEmpty
        self.eyeCam.rigID = self.rigIDifEmpty
        self.IMU.rigID = self.rigIDifEmpty
        
        # Animal
        self.topDownCam.animalID = self.animalIDifEmpty
        self.eyeCam.animalID = self.animalIDifEmpty
        self.IMU.animalID = self.animalIDifEmpty
        
        # Block
        self.topDownCam.blockID = self.blockIDifEmpty
        self.eyeCam.blockID = self.blockIDifEmpty
        self.IMU.blockID = self.blockIDifEmpty
        
    def editPath(self):
        
        useCustomPath = bool(self.useCustomPath.get())
        
        if useCustomPath is False:
            
            # Disable path entry
            self.pathEntry.config(state = 'disabled')
            self.userEntry.config(state = 'normal')
            self.pathEntry.update_idletasks()
            
        elif useCustomPath is True:
            
            # Enable path entry
            self.pathEntry.config(state = 'normal')
            self.userEntry.config(state = 'disabled')
            self.pathEntry.update_idletasks()
        
    def updatePath(self, *args):
        
        # Update session info
        self.userID = str(self.userVar.get() or self.userIDifEmpty)
        self.rigID = str(self.rigVar.get() or self.rigIDifEmpty)
        self.animalID = str(self.animalVar.get() or self.animalIDifEmpty)
        self.blockID = str(self.blockVar.get() or self.blockIDifEmpty)
        self.updateInfoSessionForEachTask()
        
        # Automatically ppdate path if not custom
        useCustomPath = bool(self.useCustomPath.get())
        if useCustomPath is False:
            path = self.rootDir + self.userID + "\\" + self.animalID + "_" + self.currentDate + "_" + self.blockID + "\\"
            self.path.set(path)
            self.pathForSavingData = self.rootDir + self.userID + "\\" + self.animalID + "_" + self.currentDate + "_" + self.blockID + "\\"
        # Read from path entry if custom
        elif useCustomPath is True:
            self.pathForSavingData = str(self.pathEntry.get())

    def updateInfoSessionForEachTask(self):
        
        # Path
        self.topDownCam.pathForSavingData = self.pathForSavingData
        self.eyeCam.pathForSavingData = self.pathForSavingData
        self.IMU.pathForSavingData = self.pathForSavingData
        
        # Rig
        self.topDownCam.rigID = self.rigID
        self.eyeCam.rigID = self.rigID
        self.IMU.rigID = self.rigID
        
        # Animal
        self.topDownCam.animalID = self.animalID
        self.eyeCam.animalID = self.animalID
        self.IMU.animalID = self.animalID
        
        # Block
        self.topDownCam.blockID = self.blockID
        self.eyeCam.blockID = self.blockID
        self.IMU.blockID = self.blockID

    def updateTopDownCamEntries(self, state):
        
        # Update settings entries
        entryBoxes = [self.topDownCamSettingLabel, self.topDownCamIDEntry, self.topDownCamDurationEntry, self.topDownCamFrameRateEntry, self.topDownCamFrameWidthEntry, self.topDownCamFrameHeightEntry]
        for i in range(len(entryBoxes)):
            entryBoxes[i].config(state = state)
            entryBoxes[i].update_idletasks()
        
    def updateEyeCamEntries(self, state):
        
        # Update settings entries
        entryBoxes = [self.eyeCamSettingLabel, self.eyeCamIDEntry, self.eyeCamDurationEntry, self.eyeCamFrameRateEntry, self.eyeCamFrameWidthEntry, self.eyeCamFrameHeightEntry]
        for i in range(len(entryBoxes)):
            entryBoxes[i].config(state = state)
            entryBoxes[i].update_idletasks()
            
    def updateIMUEntries(self, state):
        
        # Update settings entries
        entryBoxes = [self.IMUSettingLabel, self.IMUcomIDEntry, self.IMUdurationEntry]
        for i in range(len(entryBoxes)):
            entryBoxes[i].config(state = state)
            entryBoxes[i].update_idletasks()
        
    def previewAll(self):
        
        if self.isAnyPreviewOn is False:
            
            # Top Down Camera
            topDownCamPreview = Thread(target = self.topDownCamPreviewThread)
            topDownCamPreview.start()
            # Eye Camera
            eyeCamPreview = Thread(target = self.eyeCamPreviewThread)
            eyeCamPreview.start()
            # IMU
            self.IMU.previewIMUdata()
            
        elif self.isAnyPreviewOn is True:
            
            # Check if any task is not in preview mode
            if self.topDownCam.isPreviewOn is False:
                # Top Down Camera
                topDownCamPreview = Thread(target = self.topDownCamPreviewThread)
                topDownCamPreview.start()
            if self.eyeCam.isPreviewOn is False:
                # Eye Camera
                eyeCamPreview = Thread(target = self.eyeCamPreviewThread)
                eyeCamPreview.start()
            if self.IMU.isPreviewOn is False:
                # IMU
                self.IMU.previewIMUdata()
        
            # Turn off preview mode for all tasks
            if self.topDownCam.isPreviewOn is True and self.eyeCam.isPreviewOn is True and self.IMU.isPreviewOn is True:
                # Top Down Camera
                topDownCamPreview = Thread(target = self.topDownCamPreviewThread)
                topDownCamPreview.start()
                # Eye Camera
                eyeCamPreview = Thread(target = self.eyeCamPreviewThread)
                eyeCamPreview.start()
                # IMU
                self.IMU.previewIMUdata()

    def topDownCamPreviewThread(self):
        
        self.topDownCam.previewCamera()
        
    def eyeCamPreviewThread(self):
        
        self.eyeCam.previewCamera()
        
    def checkPreviewButtonState(self):
        
        self.checkTasks()
        
        if self.isAnyPreviewOn is True:
            
            if self.topDownCam.isPreviewOn is True and self.eyeCam.isPreviewOn is True and self.IMU.isPreviewOn is True:
                
                self.previewAllButton.config(fg = 'Blue', bg = '#A9C6E3', relief = 'sunken', text = 'All in Preview...')
                self.previewAllButton.bind('<Enter>', lambda e: self.previewAllButton.config(fg = 'Blue', bg ='#A9C6E3'))
                self.previewAllButton.bind('<Leave>', lambda e: self.previewAllButton.config(fg = 'Blue', bg = '#A9C6E3'))
                self.previewAllButton.update_idletasks()
                
            if self.topDownCam.isPreviewOn is False or self.eyeCam.isPreviewOn is False or self.IMU.isPreviewOn is False:
            
                self.previewAllButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Not All in Preview')
                self.previewAllButton.bind('<Enter>', lambda e: self.previewAllButton.config(fg = 'Black', bg ='#A9C6E3'))
                self.previewAllButton.bind('<Leave>', lambda e: self.previewAllButton.config(fg = 'Black', bg = 'SystemButtonFace'))
                self.previewAllButton.update_idletasks()
                
        elif self.isAnyPreviewOn is False:
            
            self.previewAllButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Preview All')
            self.previewAllButton.bind('<Enter>', lambda e: self.previewAllButton.config(fg = 'Black', bg ='#A9C6E3'))
            self.previewAllButton.bind('<Leave>', lambda e: self.previewAllButton.config(fg = 'Black', bg = 'SystemButtonFace'))
            self.previewAllButton.update_idletasks()
        
    def recordAll(self):
        
        if self.isAnyRecordingOn is False:
            # Top Down Camera
            recordTopDownCam = Thread(target = self.topDownCamRecordThread)
            recordTopDownCam.start()
            # Eye Camera
            recordeyeCam = Thread(target = self.eyeCamRecordThread)
            recordeyeCam.start()
            # IMU
            self.IMU.recordIMUdata()
            
        elif self.isAnyRecordingOn is True:
            
            # Check if any task is not in recording
            if self.topDownCam.isRecordingOn is False:
                # Top Down Camera
                recordTopDownCam = Thread(target = self.topDownCamRecordThread)
                recordTopDownCam.start()
            if self.eyeCam.isRecordingOn is False:
                # Eye Camera
                recordeyeCam = Thread(target = self.eyeCamRecordThread)
                recordeyeCam.start()
            if self.IMU.isRecordingOn is False:
                # IMU
                self.IMU.recordIMUdata()
                
            # Stop recordings for all tasks
            if self.topDownCam.isRecordingOn is True and self.eyeCam.isRecordingOn is True and self.IMU.isRecordingOn is True:
                # Top Down Camera
                recordTopDownCam = Thread(target = self.topDownCamRecordThread)
                recordTopDownCam.start()
                # Eye Camera
                recordeyeCam = Thread(target = self.eyeCamRecordThread)
                recordeyeCam.start()
                # IMU
                self.IMU.recordIMUdata()
            
    def topDownCamRecordThread(self):
        
        self.topDownCam.recordVideo()
        
    def eyeCamRecordThread(self):
        
        self.eyeCam.recordVideo()
    
    def checkRecordButtonState(self):

        self.checkTasks()
        
        if self.isAnyRecordingOn is True:
            
            if self.topDownCam.isRecordingOn is True and self.eyeCam.isRecordingOn is True and self.IMU.isRecordingOn is True:
                
                self.recordAllButton.config(fg = 'Black', bg = '#DC5B5B', relief = 'sunken', text = 'Recording All...')
                self.recordAllButton.bind('<Enter>', lambda e: self.recordAllButton.config(fg = 'Black', bg ='#DC5B5B'))
                self.recordAllButton.bind('<Leave>', lambda e: self.recordAllButton.config(fg = 'Black', bg = '#DC5B5B'))
                self.recordAllButton.update_idletasks()
                
            if self.topDownCam.isRecordingOn is False or self.eyeCam.isRecordingOn is False or self.IMU.isRecordingOn is False:
            
                self.recordAllButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Not All Recording')
                self.recordAllButton.bind('<Enter>', lambda e: self.recordAllButton.config(fg = 'Black', bg ='#DC5B5B'))
                self.recordAllButton.bind('<Leave>', lambda e: self.recordAllButton.config(fg = 'Black', bg = 'SystemButtonFace'))
                self.recordAllButton.update_idletasks()
                
        elif self.isAnyRecordingOn is False:
            
            self.recordAllButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Record All')
            self.recordAllButton.bind('<Enter>', lambda e: self.recordAllButton.config(fg = 'Black', bg ='#DC5B5B'))
            self.recordAllButton.bind('<Leave>', lambda e: self.recordAllButton.config(fg = 'Black', bg = 'SystemButtonFace'))
            self.recordAllButton.update_idletasks()
            
    def checkTasks(self):
        
        # Is any preview on?
        if self.topDownCam.isPreviewOn is True or self.eyeCam.isPreviewOn is True or self.IMU.isPreviewOn is True:
            self.isAnyPreviewOn = True
        else:
            self.isAnyPreviewOn = False
        
        # Is any recording on?
        if self.topDownCam.isRecordingOn is True or self.eyeCam.isRecordingOn is True or self.IMU.isRecordingOn is True:
            self.isAnyRecordingOn = True 
        else:
            self.isAnyRecordingOn = False 
            
    def closeMainWindow(self):
        
        self.checkTasks()
        
        if self.isAnyRecordingOn is False and self.isAnyPreviewOn is False:
            if self.IMU.IMUIsOn is True:
                self.IMU.closeIMUconnection()
            self.mainWindow.destroy()
            self.mainWindow.quit()
        elif self.isAnyRecordingOn is True:
            print("There is at least one recording in progress... Please stop all recordings before closing this program.")
        elif self.isAnyPreviewOn is True:
            print("There is at least one preview task on... Please stop all preview tasks before closing this program.")
            
        
    
    
""" 
Top Down Camera Functions

"""
    
class topDownCamera:
    
    def __init__(self, recordBehavior):
        
        # GUI instance
        self.recordBehavior = recordBehavior
        
        # Initialize library
        ic4.Library.init()
        
        # Camera booleans
        self.keepCameraOn = False
        self.isPreviewOn = False
        self.isRecordingOn = False
        
        # Initial session info
        self.rigID = str(self.recordBehavior.rigVar.get() or self.recordBehavior.rigIDifEmpty)
        self.animalID = str(self.recordBehavior.animalVar.get() or self.recordBehavior.animalIDifEmpty)
        self.blockID = str(self.recordBehavior.blockVar.get() or self.recordBehavior.blockIDifEmpty)
        self.pathForSavingData = self.recordBehavior.pathForSavingData
        self.currentDate = self.recordBehavior.currentDate
        
    def resetVideoSettings(self):
        
        # Reset settings
        self.cameraID = int(self.recordBehavior.topDownCamIDEntry.get())
        self.recordingDuration = int(self.recordBehavior.topDownCamDurationEntry.get())
        self.frameRate = int(self.recordBehavior.topDownCamFrameRateEntry.get())
        self.frameWidth = int(self.recordBehavior.topDownCamFrameWidthEntry.get())
        self.frameHeight = int(self.recordBehavior.topDownCamFrameHeightEntry.get())
          
    def initializeCamera(self):
        
        # Reset settings
        self.resetVideoSettings()
        
        # Disable settings entries
        self.recordBehavior.updateTopDownCamEntries(state = 'disable')
        
        # Initialize IC4 Library and Device
        self.grabber = ic4.Grabber()
        self.device = ic4.DeviceEnum.devices()[self.cameraID]
        self.grabber.device_open(self.device)
        
        # Set Camera Settings. Warning: properties may vary by camera model
        try:
            self.grabber.device_property_map.set_value(ic4.PropId.ACQUISITION_FRAME_RATE, self.frameRate)
        except ic4.IC4Exception:
            print("Could not set frame rate. Check camera capabilities.")
        try:
            self.grabber.device_property_map.set_value(ic4.PropId.WIDTH, self.frameWidth)
        except ic4.IC4Exception:
            print("Could not set frame width. Check camera capabilities.")
        try:
            self.grabber.device_property_map.set_value(ic4.PropId.HEIGHT, self.frameHeight)
        except ic4.IC4Exception:
            print("Could not set frame height. Check camera capabilities.")
        
        # Create a FrameSnapSink
        # SnapSink allows grabbing single images or sequences from a live stream
        self.sink = ic4.SnapSink()
        
        # Estimate buffer timeout
        # Example: timeout of 100 ms (1000 ms / 100 Hz = 10 ms per frame, 100 ms is safe)
        self.bufferTimeout = int(10 * (1000 / self.frameRate))
        
        # Setup data stream and start acquisition
        # Setup the sink, making it the destination for images
        self.grabber.stream_setup(self.sink)
        
        # Preapre frame
        self.frame = np.zeros([self.frameWidth, self.frameHeight])
    
    def printCamSettings(self):
        
        # Tolerance: 500 ms for the camera to update its current exposure time, and 500 ms for printing it
        # This should work fine for frame rates higher than 2 Hz
        # Important: even if the exposure time is not accurate for low frame rates (1-5 Hz), the camera is recording at the desired frame rate...
        # ... it is just the printed value that does not have enough time to update
        while  time.time() - self.onStarted < 1:
            if time.time() - self.onStarted > 0.5:
                print(f"     Opened device: {self.device.model_name}")
                print(f"     Frame rate: {self.frameRate} Hz")
                print(f"     Frame width: {self.frameWidth}")
                print(f"     Frame height: {self.frameHeight}")
                currentExposure = self.grabber.device_property_map.get_value_str(ic4.PropId.EXPOSURE_TIME)
                currentExposure = currentExposure.rstrip('0')
                if currentExposure.endswith('.'):
                    currentExposure = currentExposure.rstrip('.')
                print(f"     Exposure Time: {currentExposure} µs")
                pixelFormat = self.grabber.device_property_map.get_value_str(ic4.PropId.PIXEL_FORMAT)
                print(f"     Data type: {pixelFormat}")
                break
    
    def checkFileNames(self):
        
        # Filenames
        self.videoFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "topDownCamera" + "_" + str(self.blockID) + ".mp4"
        self.timeStampsFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "topDownCameraTimeStamps" + "_" + str(self.blockID) + ".txt"
        
        # Check for existing files
        if not os.path.isfile(self.videoFileName):
            self.blockIDchanged = False
        else:
            while os.path.isfile(self.videoFileName) is True:
                self.blockID = Path(self.videoFileName).stem[-1]
                self.blockID = int(self.blockID)
                self.blockID += 1
                self.videoFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "topDownCamera" + "_" + str(self.blockID) + ".mp4"
                self.timeStampsFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "topDownCameraTimeStamps" + "_" + str(self.blockID) + ".txt"
                if not os.path.isfile(self.videoFileName):
                    self.blockIDchanged = True
                    break
                
    def prepareFiles(self):
        
        # Define the codec and create VideoWriter object
        self.videoObject = cv2.VideoWriter(self.videoFileName, 
                                           cv2.VideoWriter_fourcc(*'mp4v'), 
                                           self.frameRate,
                                           (self.frameWidth, self.frameHeight)
                                          )
        
        # Prepare time stamps file
        self.timeStampsFile = open(self.timeStampsFileName, 'w')
    
    def previewCamera(self):
        
        if self.isPreviewOn is False and self.isRecordingOn is False:
            
            # Initialize camera
            self.initializeCamera()
            
            # Threads to handle grabbing frames and live feed
            self.isPreviewOn = True
            self.keepCameraOn = True
            self.onStarted = time.time()
            grabFrame = Thread(target = self.grabFrame)
            grabFrame.start()
            cameraFeed = Thread(target = self.cameraFeed)
            cameraFeed.start()
            printCamSettings = Thread(target = self.printCamSettings)
            printCamSettings.start()

            # Update button
            self.recordBehavior.topDownCamPreviewButton.config(fg = 'Blue', bg = '#A9C6E3', relief = 'sunken', text = 'Preview On')
            self.recordBehavior.topDownCamPreviewButton.bind('<Enter>', lambda e: self.recordBehavior.topDownCamPreviewButton.config(fg = 'Blue', bg ='#A9C6E3'))
            self.recordBehavior.topDownCamPreviewButton.bind('<Leave>', lambda e: self.recordBehavior.topDownCamPreviewButton.config(fg = 'Blue', bg = '#A9C6E3'))
            self.recordBehavior.topDownCamPreviewButton.update_idletasks()
            
            # Check on 'Preview All' button
            self.recordBehavior.checkPreviewButtonState()
            
        elif self.isPreviewOn is True:
            
            self.stopPreview()
            
        elif self.isRecordingOn is True:
            print("Recording in progress... Please stop the ongoing recording before turning on preview mode.")
            
    def stopPreview(self):
        
        # Stop camera
        self.isPreviewOn = False
        self.keepCameraOn = False        
        self.stopCamera()
        
        # Update button
        self.recordBehavior.topDownCamPreviewButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Preview Off')
        self.recordBehavior.topDownCamPreviewButton.bind('<Enter>', lambda e: self.recordBehavior.topDownCamPreviewButton.config(fg = 'Black', bg ='#A9C6E3'))
        self.recordBehavior.topDownCamPreviewButton.bind('<Leave>', lambda e: self.recordBehavior.topDownCamPreviewButton.config(fg = 'Black', bg = 'SystemButtonFace'))
        self.recordBehavior.topDownCamPreviewButton.update_idletasks()
        
        # Check on 'Preview All' button
        self.recordBehavior.checkPreviewButtonState()
        
        print(" ")
        print("Top Down Camera: Preview stopped.")
    
    def recordVideo(self):
        
        if self.isRecordingOn is False and self.isPreviewOn is False:
            
            # Initialize camera
            self.initializeCamera()
            
            # Prepare files for recording
            self.recordBehavior.makePath()
            self.checkFileNames()
            self.prepareFiles()
            
            # Threads to handle grabbing frames and live feed
            self.isRecordingOn = True
            self.keepCameraOn = True
            self.onStarted = time.time()
            grabFrame = Thread(target = self.grabFrame)
            grabFrame.start()
            cameraFeed = Thread(target = self.cameraFeed)
            cameraFeed.start()
            printCamSettings = Thread(target = self.printCamSettings)
            printCamSettings.start()
            self.startTime = time.time()
            
            # Time offset
            if self.recordBehavior.timeOffsetOn is False:
                timeOffset(self)
                grabTimeOffset = Thread(target = timeOffset.grabTimeStamp)
                grabTimeOffset.start()
            
            # Update button
            self.recordBehavior.topDownCamRecordButton.config(fg = 'Black', bg = '#DC5B5B', relief = 'sunken', text = 'Recording')
            self.recordBehavior.topDownCamRecordButton.bind('<Enter>', lambda e: self.recordBehavior.topDownCamRecordButton.config(fg = 'Black', bg ='#DC5B5B'))
            self.recordBehavior.topDownCamRecordButton.bind('<Leave>', lambda e: self.recordBehavior.topDownCamRecordButton.config(fg = 'Black', bg = '#DC5B5B'))
            self.recordBehavior.topDownCamRecordButton.update_idletasks()
            
            # Check on 'Record All' button
            self.recordBehavior.checkRecordButtonState()
            
        elif self.isRecordingOn is True:
            
            self.stopRecording()
            
        elif self.isPreviewOn is True:
            print("Preview mode is on... Please close preview mode before starting a recording.")
        
    def stopRecording(self):
    
        # Stop camera
        self.isRecordingOn = False
        self.keepCameraOn = False
        self.stopCamera()
        
        # Update button
        self.recordBehavior.topDownCamRecordButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Record')
        self.recordBehavior.topDownCamRecordButton.bind('<Enter>', lambda e: self.recordBehavior.topDownCamRecordButton.config(fg = 'Black', bg ='#DC5B5B'))
        self.recordBehavior.topDownCamRecordButton.bind('<Leave>', lambda e: self.recordBehavior.topDownCamRecordButton.config(fg = 'Black', bg = 'SystemButtonFace'))
        self.recordBehavior.topDownCamRecordButton.update_idletasks()
        
        # Check on 'Record All' button
        self.recordBehavior.checkRecordButtonState()
        
        print(" ")
        print("Top Down Camera: Recording stopped.")
        
        if self.blockIDchanged is True:
        
            messagebox.showwarning("Data Saved", "Video and time stamps have been saved at " + self.pathForSavingData +
                                   "\n " +
                                   "\nHowever, the block number was changed to " + str(self.blockID) + " to avoid overwriting an existing file." +
                                   "\n"
                                   "\nIf other data was acquired, make sure block numbers match.")

    def grabFrame(self):
        
        try:
            
            print(" ")
            print("Top Down Camera:")
            if self.isPreviewOn is True:
                print("Preview started...")
            elif self.isRecordingOn is True:
                print("Recording in progress...")
                
            while self.keepCameraOn is True:
            
                try:
                    
                    # snap_single blocks until an image arrives, with a timeout
                    image = self.sink.snap_single(self.bufferTimeout)
                    
                    # Convert ic4 image to numpy array (OpenCV format)
                    frame = image.numpy_copy() 
                    frame = cv2.resize(frame, (self.frameWidth, self.frameHeight))
                    self.frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    
                    # Recording mode
                    if self.isRecordingOn is True:
                        
                        # Write Frame
                        self.videoObject.write(self.frame)
        
                        # Write timeStamp to file
                        timeStamp = time.time()
                        self.timeStampsFile.write(str(timeStamp) + '\n')
                        
                except:
                    
                    # Could not grab frame
                    ...
                    
                # Check for timeout
                if self.isRecordingOn is True:
                    if time.time() > self.startTime + self.recordingDuration:
                        break
                
        except ic4.IC4Exception as e:
            print(f"Error during acquisition: {e}")
            
        except KeyboardInterrupt:
            # Press Ctrl+C to stop recording mode
            if self.isRecordingOn is True:
                self.stopRecording()

    def cameraFeed(self):
        
        # Window could be resized, if needed
        self.windowName = 'Top Down Camera'
        cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.windowName, 300, 125)
        cv2.resizeWindow(self.windowName, self.frameWidth, self.frameHeight)

        # Live feed
        while self.keepCameraOn is True:
            # Display frame
            cv2.imshow(self.windowName, self.frame)
            # Press Esc to stop preview mode
            if cv2.waitKey(1) & 0xFF == 27:
                self.stopPreview()
                break
            # Check for timeout
            if self.isRecordingOn is True:
                if time.time() > self.startTime + self.recordingDuration:
                    break
                
    def stopCamera(self):
        
        # Close window and delete camera
        self.deleteCamera()
        
        # Enable settings entries
        self.recordBehavior.updateTopDownCamEntries(state = 'normal')
        
    def deleteCamera(self):
        
        self.grabber.stream_stop()
        self.grabber.device_close()
        self.sink.__del__
        cv2.destroyWindow(self.windowName)
        try:
            self.videoObject.release()
            self.timeStampsFile.close()
        except:
            pass
    
    
""" 
Eye Camera Functions

"""
    
class eyeCamera:
    
    def __init__(self, recordBehavior):
        
        # GUI instance
        self.recordBehavior = recordBehavior
        
        # Camera booleans
        self.keepCameraOn = False
        self.isPreviewOn = False
        self.isRecordingOn = False
        self.useDirectShow = False
    
        # Initial session info
        self.rigID = str(self.recordBehavior.rigVar.get() or self.recordBehavior.rigIDifEmpty)
        self.animalID = str(self.recordBehavior.animalVar.get() or self.recordBehavior.animalIDifEmpty)
        self.blockID = str(self.recordBehavior.blockVar.get() or self.recordBehavior.blockIDifEmpty)
        self.pathForSavingData = self.recordBehavior.pathForSavingData
        self.currentDate = self.recordBehavior.currentDate
        
    def resetVideoSettings(self):
        
        # Reset settings
        self.cameraID = int(self.recordBehavior.eyeCamIDEntry.get())
        self.recordingDuration = int(self.recordBehavior.eyeCamDurationEntry.get())
        self.frameRate = int(self.recordBehavior.eyeCamFrameRateEntry.get())
        self.frameWidth = int(self.recordBehavior.eyeCamFrameWidthEntry.get())
        self.frameHeight = int(self.recordBehavior.eyeCamFrameHeightEntry.get())
        
    def initializeCamera(self):
        
        # Reset settings
        self.resetVideoSettings()
        
        # Disable settings entries
        self.recordBehavior.updateEyeCamEntries(state = 'disable')
        
        # Initialize videoCapture object for display
        if self.useDirectShow is True:
            # cv2.CAP_DSHOW is optional: backend API to use DirectShow
            # Default frame size: 640 x 480
            self.liveFeed = cv2.VideoCapture(self.cameraID, cv2.CAP_DSHOW)
        elif self.useDirectShow is False:
            # Default frame size: 720 x 576
            self.liveFeed = cv2.VideoCapture(self.cameraID)
        self.isCameraAvailable = self.liveFeed.isOpened()
        if self.isCameraAvailable is False:
            print("Error reading camera = " + str(self.cameraID) + ". Camera is not available.") 
        
        # Set Camera Settings. Warning: properties may vary by camera model
        print(" ")
        print("Eye Camera:")
        print("Setting up properties...")
        # Frame rate (StarTech USB3HDCAP FR = 23.97, 25, 29.97, 30, 50, 59.94, 60)
        self.liveFeed.set(cv2.CAP_PROP_FPS, self.frameRate)
        fps = self.liveFeed.get(cv2.CAP_PROP_FPS)
        if self.frameRate != round(fps, 2):
            self.frameRate = int(fps)
            self.recordBehavior.eyeCamFrameRateValue.set(self.frameRate)
            self.liveFeed.set(cv2.CAP_PROP_FPS, self.frameRate)
            print(f"     Could not set frame rate. Check camera capabilities. Using frame rate: {self.frameRate} Hz")
        # Frame width
        self.liveFeed.set(cv2.CAP_PROP_FRAME_WIDTH, self.frameWidth)
        width = self.liveFeed.get(cv2.CAP_PROP_FRAME_WIDTH)
        if self.frameWidth != width:
            self.frameWidth = int(width)
            self.recordBehavior.eyeCamFrameWidthValue.set(self.frameWidth)
            self.liveFeed.set(cv2.CAP_PROP_FRAME_WIDTH, self.frameWidth)
            print(f"     Could not set frame width. Check camera capabilities. Using frame width: {self.frameWidth}")            
        # Frame height
        self.liveFeed.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frameHeight)
        height = self.liveFeed.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if self.frameHeight != height:
            self.frameHeight = int(height)
            self.recordBehavior.eyeCamFrameHeightValue.set(self.frameHeight)
            self.liveFeed.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frameHeight)
            print(f"     Could not set frame height. Check camera capabilities. Using frame height: {self.frameHeight}")            
        
        # Preapre frame
        self.frame = np.zeros([self.frameHeight, self.frameWidth, 3])
    
    def printCamSettings(self):
        
        # Tolerance: 500 ms for the camera to update its current exposure time, and 500 ms for printing it
        # This should work fine for frame rates higher than 2 Hz
        # Important: even if the exposure time is not accurate for low frame rates (1-5 Hz), the camera is recording at the desired frame rate...
        # ... it is just the printed value that does not have enough time to update
        while  time.time() - self.onStarted < 1:
            if time.time() - self.onStarted > 0.5:
                print(f"     Opened device: cameraID = {self.cameraID}")
                print(f"     Frame rate: {self.frameRate} Hz (for saving video only; the real frame rate can be variable)")
                print(f"     Frame width: {self.frameWidth}")
                print(f"     Frame height: {self.frameHeight}")
                break
    
    def checkFileNames(self):
        
        # Filenames
        self.videoFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "eyeCamera" + "_" + str(self.blockID) + ".mp4"
        self.timeStampsFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "eyeCameraTimeStamps" + "_" + str(self.blockID) + ".txt"
        
        # Check for existing files
        if not os.path.isfile(self.videoFileName):
            self.blockIDchanged = False
        else:
            while os.path.isfile(self.videoFileName) is True:
                self.blockID = Path(self.videoFileName).stem[-1]
                self.blockID = int(self.blockID)
                self.blockID += 1
                self.videoFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "eyeCamera" + "_" + str(self.blockID) + ".mp4"
                self.timeStampsFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "eyeCameraTimeStamps" + "_" + str(self.blockID) + ".txt"
                if not os.path.isfile(self.videoFileName):
                    self.blockIDchanged = True
                    break
        
    def prepareFiles(self):
        
        # Define the codec and create VideoWriter object        
        self.eyeCamVideo = cv2.VideoWriter(self.videoFileName, 
                                               cv2.VideoWriter_fourcc(*'mp4v'), 
                                               self.frameRate,
                                               (self.frameWidth, self.frameHeight)
                                              )
        
        # Prepare time stamps file
        self.timeStampsFile = open(self.timeStampsFileName, 'w')
    
    def previewCamera(self):
        
        if self.isPreviewOn is False and self.isRecordingOn is False:
            
            # Update button
            self.recordBehavior.eyeCamPreviewButton.config(fg = 'Black', bg = '#A9C6E3', relief = 'sunken', text = 'opening...')
            self.recordBehavior.IMUinitializeButton.update_idletasks()
            
            # Initialize camera
            self.initializeCamera()
            
            if self.isCameraAvailable is True:
                
                # Threads to handle grabbing frames and live feed
                self.isPreviewOn = True
                self.keepCameraOn = True
                self.onStarted = time.time()
                grabFrame = Thread(target = self.grabFrame)
                grabFrame.start()
                cameraFeed = Thread(target = self.cameraFeed)
                cameraFeed.start()
                printCamSettings = Thread(target = self.printCamSettings)
                printCamSettings.start()
    
                # Update button
                self.recordBehavior.eyeCamPreviewButton.config(fg = 'Blue', bg = '#A9C6E3', relief = 'sunken', text = 'Preview On')
                self.recordBehavior.eyeCamPreviewButton.bind('<Enter>', lambda e: self.recordBehavior.eyeCamPreviewButton.config(fg = 'Blue', bg ='#A9C6E3'))
                self.recordBehavior.eyeCamPreviewButton.bind('<Leave>', lambda e: self.recordBehavior.eyeCamPreviewButton.config(fg = 'Blue', bg = '#A9C6E3'))
                self.recordBehavior.eyeCamPreviewButton.update_idletasks()
                
                # Check on 'Preview All' button
                self.recordBehavior.checkPreviewButtonState()
            
        elif self.isPreviewOn is True:
            
            self.stopPreview()
            
        elif self.isRecordingOn is True:
            print("Recording in progress... Please stop the ongoing recording before turning on preview mode.")
            
    def stopPreview(self):
        
        # Stop camera
        self.isPreviewOn = False
        self.keepCameraOn = False        
        self.stopCamera()
        
        # Update button
        self.recordBehavior.eyeCamPreviewButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Preview Off')
        self.recordBehavior.eyeCamPreviewButton.bind('<Enter>', lambda e: self.recordBehavior.eyeCamPreviewButton.config(fg = 'Black', bg ='#A9C6E3'))
        self.recordBehavior.eyeCamPreviewButton.bind('<Leave>', lambda e: self.recordBehavior.eyeCamPreviewButton.config(fg = 'Black', bg = 'SystemButtonFace'))
        self.recordBehavior.eyeCamPreviewButton.update_idletasks()
        
        # Check on 'Preview All' button
        self.recordBehavior.checkPreviewButtonState()
        
        print(" ")
        print("Eye Camera: Preview stopped.")
    
    def recordVideo(self):
        
        if self.isRecordingOn is False and self.isPreviewOn is False:
            
            # Initialize camera
            self.initializeCamera()
            
            if self.isCameraAvailable is True:
                
                # Prepare files for recording
                self.recordBehavior.makePath()
                self.checkFileNames()
                self.prepareFiles()
                
                # Threads to handle grabbing frames and live feed
                self.isRecordingOn = True
                self.keepCameraOn = True
                self.onStarted = time.time()
                grabFrame = Thread(target = self.grabFrame)
                grabFrame.start()
                cameraFeed = Thread(target = self.cameraFeed)
                cameraFeed.start()
                printCamSettings = Thread(target = self.printCamSettings)
                printCamSettings.start()
                self.startTime = time.time()
                
                # Time offset
                if self.recordBehavior.timeOffsetOn is False:
                    timeOffset(self)
                    grabTimeOffset = Thread(target = timeOffset.grabTimeStamp)
                    grabTimeOffset.start()
                    
                # Update button
                self.recordBehavior.eyeCamRecordButton.config(fg = 'Black', bg = '#DC5B5B', relief = 'sunken', text = 'Recording')
                self.recordBehavior.eyeCamRecordButton.bind('<Enter>', lambda e: self.recordBehavior.eyeCamRecordButton.config(fg = 'Black', bg ='#DC5B5B'))
                self.recordBehavior.eyeCamRecordButton.bind('<Leave>', lambda e: self.recordBehavior.eyeCamRecordButton.config(fg = 'Black', bg = '#DC5B5B'))
                self.recordBehavior.eyeCamRecordButton.update_idletasks()
                
                # Check on 'Record All' button
                self.recordBehavior.checkRecordButtonState()
                
        elif self.isRecordingOn is True:
            
            self.stopRecording()
            
        elif self.isPreviewOn is True:
            print("Preview mode is on... Please close preview mode before starting a recording.")
        
    def stopRecording(self):
    
        # Stop camera
        self.isRecordingOn = False
        self.keepCameraOn = False
        self.stopCamera()
        
        # Update button
        self.recordBehavior.eyeCamRecordButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Record')
        self.recordBehavior.eyeCamRecordButton.bind('<Enter>', lambda e: self.recordBehavior.eyeCamRecordButton.config(fg = 'Black', bg ='#DC5B5B'))
        self.recordBehavior.eyeCamRecordButton.bind('<Leave>', lambda e: self.recordBehavior.eyeCamRecordButton.config(fg = 'Black', bg = 'SystemButtonFace'))
        self.recordBehavior.eyeCamRecordButton.update_idletasks()
        
        # Check on 'Record All' button
        self.recordBehavior.checkRecordButtonState()
        
        print(" ")
        print("Eye Camera: Recording stopped.")
        
        if self.blockIDchanged is True:
        
            messagebox.showwarning("Data Saved", "Video and time stamps have been saved at " + self.pathForSavingData +
                                   "\n " +
                                   "\nHowever, the block number was changed to " + str(self.blockID) + " to avoid overwriting an existing file." +
                                   "\n"
                                   "\nIf other data was acquired, make sure block numbers match.")

    def grabFrame(self):
        
        try:
            
            if self.isPreviewOn is True:
                print("Preview started...")
            elif self.isRecordingOn is True:
                print("Recording in progress...")
                
            while self.keepCameraOn is True:
            
                try:
                    
                    # Grab frame
                    ret, frame = self.liveFeed.read()
                    
                    if ret:
                        self.frame = frame
                    
                    # Recording mode
                    if self.isRecordingOn is True:
                        
                        # Write Frame
                        self.eyeCamVideo.write(self.frame)
                        
                        # Write timeStamp to file
                        timeStamp = time.time()
                        self.timeStampsFile.write(str(timeStamp) + '\n')
                        
                except:
                    
                    # Could not grab frame
                    ...
                    
                # Check for timeout
                if self.isRecordingOn is True:
                    if time.time() > self.startTime + self.recordingDuration:
                        break
                    
        except KeyboardInterrupt:
            # Press Ctrl+C to stop recording mode
            if self.isRecordingOn is True:
                self.stopRecording()
                
    def cameraFeed(self):
            
        # Window could be resized, if needed
        self.windowName = 'Eye Camera'
        cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.windowName, 550, 200)
        cv2.resizeWindow(self.windowName, self.frameWidth, self.frameHeight)
        
        # Live feed
        while self.keepCameraOn is True:
            # Display frame
            cv2.imshow(self.windowName, self.frame)
            # Press Esc to stop preview mode
            if cv2.waitKey(1) & 0xFF == 27:
                self.stopPreview()
                break
            # Check for timeout
            if self.isRecordingOn is True:
                if time.time() > self.startTime + self.recordingDuration:
                    break
                
    def stopCamera(self):
        
        # Close window and delete camera
        self.deleteCamera()
        
        # Enable settings entries
        self.recordBehavior.updateEyeCamEntries(state = 'normal')
        
    def deleteCamera(self):
        
        self.liveFeed.release()
        cv2.destroyWindow(self.windowName)
        try:
            self.eyeCamVideo.release()
            self.timeStampsFile.close()
        except:
            pass
    
    
""" 
IMU Functions

"""
    
class IMU:
    
    def __init__(self, recordBehavior):
        
        # GUI instance
        self.recordBehavior = recordBehavior
        
        # IMU booleans
        self.IMUIsOn = False
        self.isPreviewOn = False
        self.stopPreview = False
        self.isRecordingOn = False
        self.stopRecording = False
        
        # Initial session info
        self.rigID = str(self.recordBehavior.rigVar.get() or self.recordBehavior.rigIDifEmpty)
        self.animalID = str(self.recordBehavior.animalVar.get() or self.recordBehavior.animalIDifEmpty)
        self.blockID = str(self.recordBehavior.blockVar.get() or self.recordBehavior.blockIDifEmpty)
        self.pathForSavingData = self.recordBehavior.pathForSavingData
        self.currentDate = self.recordBehavior.currentDate
        
    def resetIMUSettings(self):
        
        # Reset settings
        self.comID = int(self.recordBehavior.IMUcomIDEntry.get())
        self.recordingDuration = int(self.recordBehavior.IMUdurationEntry.get())
        
    def initializeIMU(self):
        
        if self.IMUIsOn is False and self.isRecordingOn is False:
            
            print(" ")
            print("IMU:")
            print("Starting serial connection...")
            
            # Update button
            self.recordBehavior.IMUinitializeButton.config(fg = 'Black', bg = '#99D492', text = 'Connecting...', relief = 'sunken')
            self.recordBehavior.IMUinitializeButton.update_idletasks()
            
            # Read current settings
            self.resetIMUSettings()
            
            # Disable settings entries
            self.recordBehavior.updateIMUEntries(state = 'disable')
            
            # Connect to Arduino board: Arduino Giga R1 WiFi
            port = "COM" + str(self.comID)
            baudrate = 115200
            self.arduinoBoard = serial.Serial(port, baudrate, timeout = 1)
            self.arduinoBoard.reset_input_buffer()
            self.arduinoBoard.reset_output_buffer()
            time.sleep(2) # Wait for connection to stabilize
            self.IMUIsOn = True
            print("IMU on.")
            
            # Update button
            self.recordBehavior.IMUinitializeButton.config(fg = 'Blue', bg = '#99D492', relief = 'sunken', text = 'IMU On')
            self.recordBehavior.IMUinitializeButton.bind('<Enter>', lambda e: self.recordBehavior.IMUinitializeButton.config(fg = 'Blue', bg ='#99D492'))
            self.recordBehavior.IMUinitializeButton.bind('<Leave>', lambda e: self.recordBehavior.IMUinitializeButton.config(fg = 'Blue', bg = '#99D492'))
            self.recordBehavior.IMUinitializeButton.update_idletasks()
    
        elif self.IMUIsOn is True and self.isRecordingOn is False:
            
            self.closeIMUconnection()
            
        elif self.isRecordingOn is True:
            
            print("Recording in progress... Please stop the ongoing recording before turning IMU off.")
    
    def previewIMUdata(self):
        
        if self.IMUIsOn is True and self.isPreviewOn is False:
            
            # Serial monitor
            self.serialMonitor = tk.Tk()
            self.serialMonitor.wm_title("Serial Monitor")
            self.serialMonitor.geometry('%dx%d+%d+%d' % (600, 800, 50, 50))
            scrollBar = tk.Scrollbar(self.serialMonitor)
            scrollBar.pack(side = tk.RIGHT, fill = tk.Y)
            self.textBox = tk.Text(self.serialMonitor, width = 70, height = 48, takefocus = 0, bg = "black", fg = "white")
            self.textBox.pack()
            self.textBox.config(yscrollcommand = scrollBar.set)
            scrollBar.config(command = self.textBox.yview)
            
            # Thread to handle reading and writing IMU data
            self.isPreviewOn = True
            displayIMU = Thread(target = self.displayIMUdata)
            displayIMU.start()

            # Update button
            self.recordBehavior.IMUpreviewButton.config(fg = 'Blue', bg = '#A9C6E3', relief = 'sunken', text = 'Preview On')
            self.recordBehavior.IMUpreviewButton.bind('<Enter>', lambda e: self.recordBehavior.IMUpreviewButton.config(fg = 'Blue', bg ='#A9C6E3'))
            self.recordBehavior.IMUpreviewButton.bind('<Leave>', lambda e: self.recordBehavior.IMUpreviewButton.config(fg = 'Blue', bg = '#A9C6E3'))
            self.recordBehavior.IMUpreviewButton.update_idletasks()
            
            # Check on 'Preview All' button
            self.recordBehavior.checkPreviewButtonState()
            
            # Serial monitor mainloop
            self.serialMonitor.mainloop()
            
        elif self.IMUIsOn is True and self.isPreviewOn is True:
            
            self.stopPreview = True
            
        elif self.IMUIsOn is False and self.isPreviewOn is False:
            
            # Start IMU connection
            self.initializeIMU()
            
            # Display IMU data
            self.previewIMUdata()
    
    def displayIMUdata(self):
        
        print("Displaying IMU output...")
        
        while True:
            
            if self.arduinoBoard.in_waiting > 0:
                
                # Read line and decode from bytes to string
                line = self.arduinoBoard.readline().decode('utf-8').strip()
                
                if line:
                    
                    # Display timeStamp and IMU output
                    timeStamp = time.time()
                    IMUOutput = str(timeStamp) + ", " + line + '\n'
                    try:
                        self.textBox.insert('0.0', IMUOutput)
                    except:
                        pass
            
            # Check for manual stop
            if self.stopPreview is True:
                break
            
        # Close ongoing recording
        self.closePreview()
        self.stopPreview = False
            
    def closePreview(self):
        
        print(" ")
        print("IMU: Preview stopped.")
        
        # Close text file
        self.isPreviewOn = False
        
        # Close window
        try:
            self.serialMonitor.destroy()
            self.serialMonitor.quit()
        except:
            pass
        
        # Update button
        self.recordBehavior.IMUpreviewButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Preview Off')
        self.recordBehavior.IMUpreviewButton.bind('<Enter>', lambda e: self.recordBehavior.IMUpreviewButton.config(fg = 'Black', bg ='#A9C6E3'))
        self.recordBehavior.IMUpreviewButton.bind('<Leave>', lambda e: self.recordBehavior.IMUpreviewButton.config(fg = 'Black', bg = 'SystemButtonFace'))
        self.recordBehavior.IMUpreviewButton.update_idletasks()
        
        # Check on 'Preview All' button
        self.recordBehavior.checkPreviewButtonState()
        
    def checkFileName(self):
        
        # IMU data file
        self.IMUdataFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "IMUdata" + "_" + str(self.blockID) + ".txt"

        # Check for existing files
        if not os.path.isfile(self.IMUdataFileName):
            self.blockIDchanged = False
        else:
            while os.path.isfile(self.IMUdataFileName) is True:
                self.blockID = Path(self.IMUdataFileName).stem[-1]
                self.blockID = int(self.blockID)
                self.blockID += 1
                self.IMUdataFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "IMUdata" + "_" + str(self.blockID) + ".txt"
                if not os.path.isfile(self.IMUdataFileName):
                    self.blockIDchanged = True
                    break
    
    def recordIMUdata(self):
        
        if self.IMUIsOn is True and self.isRecordingOn is False:
            
            # Filename
            self.recordBehavior.makePath()
            self.checkFileName()
            
            # Prepare files for recording
            self.IMUdataFile = open(self.IMUdataFileName, 'w')
            
            # Thread to handle reading and writing IMU data
            self.isRecordingOn = True
            readIMU = Thread(target = self.readIMU)
            readIMU.start()
            self.startTime = time.time()
            
            # Time offset
            if self.recordBehavior.timeOffsetOn is False:
                timeOffset(self)
                grabTimeOffset = Thread(target = timeOffset.grabTimeStamp)
                grabTimeOffset.start()
                
            # Update button
            self.recordBehavior.IMUrecordButton.config(fg = 'Black', bg = '#DC5B5B', relief = 'sunken', text = 'Recording')
            self.recordBehavior.IMUrecordButton.bind('<Enter>', lambda e: self.recordBehavior.IMUrecordButton.config(fg = 'Black', bg ='#DC5B5B'))
            self.recordBehavior.IMUrecordButton.bind('<Leave>', lambda e: self.recordBehavior.IMUrecordButton.config(fg = 'Black', bg = '#DC5B5B'))
            self.recordBehavior.IMUrecordButton.update_idletasks()
            
            # Check on 'Record All' button
            self.recordBehavior.checkRecordButtonState()
            
        elif self.IMUIsOn is True and self.isRecordingOn is True:
            
            self.stopRecording = True
            
        elif self.IMUIsOn is False and self.isRecordingOn is False:
            
            # Start IMU connection
            self.initializeIMU()
            
            # Record IMU data
            self.recordIMUdata()
    
    def readIMU(self):
        
        print("Recording IMU data...")
        
        while True:
            
            if self.arduinoBoard.in_waiting > 0:
                
                # Read line and decode from bytes to string
                line = self.arduinoBoard.readline().decode('utf-8').strip()
                
                if line:
                    
                    # Write timeStamp and IMU output
                    timeStamp = time.time()
                    self.IMUdataFile.write(str(timeStamp) + ", " + line + '\n')
            
            # Check for timeout
            if time.time() > self.startTime + self.recordingDuration:
                break
            
            # Check for manual stop
            if self.stopRecording is True:
                break
            
        # Close ongoing recording
        self.closeOngoingRecording()
        self.stopRecording = False
    
    def closeOngoingRecording(self):
        
        print(" ")
        print("IMU: Recording stopped.")
        
        # Close text file
        self.IMUdataFile.close()
        self.isRecordingOn = False
        
        # Update button
        self.recordBehavior.IMUrecordButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'Record')
        self.recordBehavior.IMUrecordButton.bind('<Enter>', lambda e: self.recordBehavior.IMUrecordButton.config(fg = 'Black', bg ='#DC5B5B'))
        self.recordBehavior.IMUrecordButton.bind('<Leave>', lambda e: self.recordBehavior.IMUrecordButton.config(fg = 'Black', bg = 'SystemButtonFace'))
        self.recordBehavior.IMUrecordButton.update_idletasks()
        
        # Check on 'Record All' button
        self.recordBehavior.checkRecordButtonState()
        
        # Warning for changing block ID
        if self.blockIDchanged is True:
            messagebox.showwarning("Data Saved", "IMU data have been saved at " + self.pathForSavingData +
                                   "\n " +
                                   "\nHowever, the block number was changed to " + str(self.blockID) + " to avoid overwriting an existing file." +
                                   "\n"
                                   "\nIf other data was acquired, make sure block numbers match.")
            self.blockIDchanged = False
        
        # Close IMU connection too if recording is finished
        if time.time() > self.taskStartTime + self.recordingDuration:
            self.closeIMUconnection()
    
    
    """
    Close connection

    """
    
    def closeIMUconnection(self):
    
        # Close connection with Arduino
        self.arduinoBoard.reset_input_buffer()
        self.arduinoBoard.reset_output_buffer()
        self.arduinoBoard.close()
        self.IMUIsOn = False
        print(" ")
        print("IMU is off.")
        
        # Enable settings entries
        self.recordBehavior.updateIMUEntries(state = 'normal')
        
        # Update button
        self.recordBehavior.IMUinitializeButton.config(fg = 'Black', bg = 'SystemButtonFace', relief = 'raised', text = 'IMU Off')
        self.recordBehavior.IMUinitializeButton.bind('<Enter>', lambda e: self.recordBehavior.IMUinitializeButton.config(fg = 'Black', bg ='#99D492'))
        self.recordBehavior.IMUinitializeButton.bind('<Leave>', lambda e: self.recordBehavior.IMUinitializeButton.config(fg = 'Black', bg = 'SystemButtonFace'))
        self.recordBehavior.IMUinitializeButton.update_idletasks()
    
    
""" 
Time Offset

"""
        
class timeOffset:
    
    def __init__(self, masterDevice):
        
        # GUI instance
        self.recordBehavior = masterDevice.recordBehavior
        
        # Initialize the client
        self.recordBehavior.timeOffsetOn = True
        self.timeServer = ntplib.NTPClient()
        
        # Settings
        self.startTime = masterDevice.startTime
        self.recordingDuration = masterDevice.recordingDuration
        self.pathForSavingData = masterDevice.pathForSavingData
        self.animalID = masterDevice.animalID
        self.currentDate = masterDevice.currentDate
        self.blockID = masterDevice.blockID
        
        # Prepare file for recording
        self.checkFileName()
        self.offsetDataFile = open(self.offsetDataFileName, 'w')
        
    def checkFileName(self):
        
        # Time offset data file
        self.offsetDataFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "timeOffset" + "_" + str(self.blockID) + ".txt"

        # Check for existing files
        if not os.path.isfile(self.offsetDataFileName):
            self.blockIDchanged = False
        else:
            while os.path.isfile(self.offsetDataFileName) is True:
                self.blockID = Path(self.offsetDataFileName).stem[-1]
                self.blockID = int(self.blockID)
                self.blockID += 1
                self.offsetDataFileName = self.pathForSavingData + self.animalID + "_" + self.currentDate + "_" + "timeOffset" + "_" + str(self.blockID) + ".txt"
                if not os.path.isfile(self.offsetDataFileName):
                    self.blockIDchanged = True
                    break
    
    def grabTimeStamp(self):
    
        while True:
            
            try:
                timeStampOffest = self.timeServer.request('pool.ntp.org').offset
            except:
                timeStampOffest = None
                
            # Write unix timeStamp and time offset
            timeStamp = time.time()
            self.offsetDataFile.write(str(timeStamp) + ", " + timeStampOffest + '\n')
    
            # Check for timeout
            if time.time() > self.startTime + self.recordingDuration:
                break
            
            # Wait for next request
            time.pause(2)
            
        self.recordBehavior.timeOffsetOn = False
    
        # Warning for changing block ID
        if self.blockIDchanged is True:
            messagebox.showwarning("Data Saved", "Time offset data have been saved at " + self.pathForSavingData +
                                   "\n " +
                                   "\nHowever, the block number was changed to " + str(self.blockID) + " to avoid overwriting an existing file." +
                                   "\n"
                                   "\nIf other data was acquired, make sure block numbers match.")
            self.blockIDchanged = False
            
            
"""
Main Block

"""

if __name__ == "__main__":
    recordBehaviorGUI = recordBehaviorGUI.__init__()
    topDownCamera = topDownCamera.__init__()
    eyeCamera = eyeCamera.__init__()
    IMU = IMU.__init__()
    timeOffset = timeOffset.__init__()
    