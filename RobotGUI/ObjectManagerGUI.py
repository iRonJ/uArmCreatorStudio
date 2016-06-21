import cv2
from PyQt5                        import QtCore, QtWidgets, QtGui
from RobotGUI                     import Icons
from RobotGUI.CameraGUI           import CameraWidget, CameraSelector, cvToPixFrame
from RobotGUI.Logic.Global        import printf
from RobotGUI.Logic.ObjectManager import TrackableObject


class ObjectManagerWindow(QtWidgets.QDialog):


    def __init__(self, environment, parent):
        super(ObjectManagerWindow, self).__init__(parent)
        self.env                = environment
        self.vision             = environment.getVision()
        self.objManager         = environment.getObjectManager()
        self.cameraWidget       = CameraWidget(self.env.getVStream().getFilteredWithID, parent=self)

        # Global UI Variables
        self.deleteBtn          = QtWidgets.QPushButton("Delete")
        self.addSampleBtn       = QtWidgets.QPushButton("Add Sample")
        self.objList            = QtWidgets.QListWidget()
        self.selDescLbl         = QtWidgets.QLabel("")   # Description of selected object
        self.selImgLbl          = QtWidgets.QLabel("")   # A small picture of the object

        self.objList.itemSelectionChanged.connect(self.refreshSelected)
        self.deleteBtn.clicked.connect(self.deleteSelected)
        self.addSampleBtn.clicked.connect(self.addSample)

        # Initialize the UI
        self.initUI()
        self.cameraWidget.play()

        self.refreshObjectList()

        # For debugging
        # self.openObjectWizard()


    def initUI(self):
        self.deleteBtn.hide()   # Only visible when an object is selected
        self.addSampleBtn.hide()

        # CREATE OBJECTS AND LAYOUTS FOR ROW 1 COLUMN (ALL)
        createBtn    = QtWidgets.QPushButton("Create New")
        createBtn.setFixedWidth(130)
        createBtn.clicked.connect(self.openObjectWizard)
        self.objList.setMinimumWidth(260)


        # CREATE OBJECTS AND LAYOUTS FOR COLUMN 1
        listGBox     = QtWidgets.QGroupBox("Loaded Objects")
        listVLayout  = QtWidgets.QVBoxLayout()
        listVLayout.addWidget(self.objList)
        listGBox.setLayout(listVLayout)


        # CREATE OBJECTS AND LAYOUTS FOR COLUMN 2
        selectedGBox  = QtWidgets.QGroupBox("Selected Object")
        selObjVLayout = QtWidgets.QVBoxLayout()
        selObjVLayout.addWidget(self.selDescLbl)
        selObjVLayout.addWidget(self.selImgLbl)
        selObjVLayout.addWidget(self.deleteBtn)
        selObjVLayout.addWidget(self.addSampleBtn)
        selObjVLayout.addStretch(1)
        selectedGBox.setLayout(selObjVLayout)


        # Put everything into 1 row (top) and multiple columns just below the row
        row1 = QtWidgets.QHBoxLayout()
        col1 = QtWidgets.QVBoxLayout()
        col2 = QtWidgets.QVBoxLayout()
        col3 = QtWidgets.QVBoxLayout()

        row1.addWidget(createBtn)
        row1.addStretch(1)

        col1.addWidget(listGBox)
        col2.addWidget(selectedGBox)
        col3.addWidget(self.cameraWidget)


        # Place the row into the main vertical layout
        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addLayout(row1)
        mainHLayout = QtWidgets.QHBoxLayout()
        mainVLayout.addLayout(mainHLayout)


        # Place the columns into the main horizontal layout
        mainHLayout.addLayout(col1)
        mainHLayout.addLayout(col2)
        mainHLayout.addLayout(col3)


        # Set the layout and customize the window
        self.setLayout(mainVLayout)
        self.setWindowTitle('Object Manager')
        self.setWindowIcon(QtGui.QIcon(Icons.objectManager))

        # self.refreshSelectedObjMenu()



    def refreshObjectList(self, selectedItem=None):
        # Clear the objectList, and reload all object names from the environment
        # If selectedItem is a string, it will try to select the item. This is for obj's added through the ObjWizard
        # Clear the current objectList
        self.objList.clear()


        # Iterate through all the loaded objects and create a list item with their name on it
        objNames = self.objManager.getObjectIDList()
        objNames.sort()  # Make it in alphabetical order
        self.vision.trackerEndStopClear()
        for i, name in enumerate(objNames):
            self.objList.addItem(name)

            if name == selectedItem:
                self.objList.item(i).setSelected(True)

    def refreshSelected(self):
        # Modifies self.selectedObjVLayout to show the currently selected object, it's name, description, etc.

        def hideLabels():
            # If something breaks, hide all the "selected object" labels
            self.deleteBtn.hide()
            self.addSampleBtn.hide()
            self.selDescLbl.hide()
            self.selImgLbl.hide()

        # Get the selected object
        selectedObjects = self.objList.selectedItems()
        if not len(selectedObjects):
            hideLabels()
            return


        # Get the planarObject from Environment
        selObject = selectedObjects[0].text()
        obj       = self.objManager.getObject(selObject)

        if obj is None:
            printf("ObjectManager.refreshSelectedObjMenu(): ERROR: ObjectManager returned None for a requested obj!")
            self.vision.trackerEndStopClear()
            hideLabels()
            return


        # Start Tracking the selected object
        self.vision.clearTargets()
        self.vision.trackerAddStartTrack(obj.getSamples())

        samples = obj.getSamples()
        if len(samples) == 0:
            printf("ObjectManager.refreshSelectedObjMenu(): ERROR: Object returned ZERO samples!")
            hideLabels()
            return

        # Create a pretty icon for the object, so it's easily recognizable. Use the first sample in the objectt
        sample                 = samples[0]
        icon = cvToPixFrame(obj.getIcon(150, 350))
        self.selImgLbl.setPixmap(icon)


        # Get the "Average" number of keypoints for this object
        totalPoints = 0
        for sample in samples:
            target = self.vision.tracker.getTarget(sample.image, sample.rect)
            totalPoints += len(target.descrs)
        avgPoints = int(totalPoints / len(samples))


        # Create and set the description for this object
        self.selDescLbl.setText("Name:\n\t"         + obj.name          + "\n\n"
                                "# of Points: \n"   + str(avgPoints)    + "\n\n"
                                "Samples:\n\t"      + str(len(samples)) + "\n\n\n\n"
                                "Image:")

        # Show all the labels
        self.deleteBtn.show()
        self.addSampleBtn.show()
        self.selDescLbl.show()
        self.selImgLbl.show()

    def addSample(self):
        # Add samples to an already created object
        pass


    def deleteSelected(self):
        # Get the selected object
        selectedObjects = self.objList.selectedItems()
        if not len(selectedObjects):
            printf("ObjectManager.deleteSelected(): ERROR: Delete button was pressed but no objects were selected!")
            return
        selObject = selectedObjects[0].text()


        # Warn the user of the consequences of continuing
        reply = QtWidgets.QMessageBox.question(self, 'Warning',
                                       "Deleting this object will delete it's object files permanently.\n"
                                       "Do you want to continue??",
                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.objManager.deleteObject(selObject)

        self.refreshObjectList()

    def openObjectWizard(self):
        # Close the objectManager and open the ObjectWizard.

        printf("ObjectManager.openObjectWizard(): Opening Object Wizard!")

        self.cameraWidget.pause()

        # Get the object information from the user using the Object Wizard
        oWizard = ObjectWizard(self.env, self)
        oWizard.exec_()


        # Close objectWizard, make sure that even if "cancel" was pressed, the window still closes
        oWizard.close()
        oWizard.deleteLater()

        # If the user finished the wizard, then extract the information from the objectWizard to build a new object
        if oWizard.result():
            oWizard.addNewObject()
            self.refreshObjectList(selectedItem=oWizard.getNewObject().name)


        self.cameraWidget.play()


    def closeEvent(self, event):
        # This ensures that the cameraWidget will no longer be open when the window closes
        self.vision.trackerEndStopClear()
        self.cameraWidget.close()


# Object WIZARD
class ObjectWizard(QtWidgets.QWizard):
    def __init__(self, environment, parent):
        super(ObjectWizard, self).__init__(parent)

        # Since there are camera modules in the wizard, make sure that all tracking is off
        vision = environment.getVision()
        vision.trackerEndStopClear()
        self.objManager = environment.getObjectManager()
        self.vision     = environment.getVision()

        self.newObject  = None  # Is set in self.close()

        self.page1 = OWPage1(self.objManager.getObjectIDList(), parent=self)
        self.page2 = OWPage2(                      environment, parent=self)
        self.page3 = OWPage3(                      environment, parent=self)

        self.page2.newObject.connect(lambda: self.page3.setObject(self.page2.object))  # Link page3 to page2's object


        self.addPage(self.page1)
        self.addPage(self.page2)
        self.addPage(self.page3)
        self.setWindowTitle("Object Wizard")
        self.setWindowIcon(QtGui.QIcon(Icons.objectWizard))

    def addNewObject(self):
        # Call this after the wizard has been run, to generate and add the new object to the objectManager

        # Here is where the objectWizard will add a new object to the ObjectManager
        objName     = self.page1.nameTxt.text()
        pickupRect  = self.page3.pickupRect
        objSample   = self.page2.object
        image       = objSample.image.copy()
        rect        = objSample.rect

        finalSample = self.vision.tracker.getTarget(image, rect, name=objName, pickupRect=pickupRect)

        # Create an actual TrackableObject with this information
        self.newObject   = TrackableObject(objName)
        self.newObject.addSample(finalSample)
        self.objManager.saveNewObject(self.newObject)

    def getNewObject(self):
        # Call this after self.addNewObject() has been run, to get a reference to the object
        return self.newObject

    def closeEvent(self, event):
        # Close any pages that have active widgets, such as the cameraWidget. This will trigger each page's close func.
        self.page1.close()
        self.page2.close()
        self.page3.close()


class OWPage1(QtWidgets.QWizardPage):
    def __init__(self, objNameLst, parent):
        super(OWPage1, self).__init__(parent)

        # Create GUI objects
        self.forbiddenNames = ['TrackerObject', 'Robot Marker'] + objNameLst
        self.errorLbl       = QtWidgets.QLabel("")  # Tells the user why the name is invalid
        self.nameTxt        = QtWidgets.QLineEdit()

        self.nameTxt.textChanged.connect(self.completeChanged)

        self.initUI()

    def initUI(self):
        self.nameTxt.setMaximumWidth(260)

        welcomeLbl = QtWidgets.QLabel("Welcome to the Object Wizard!\n")
        introLbl   = QtWidgets.QLabel("This will walk you through teaching the software how to recognize a new object.")
        step1Lbl   = QtWidgets.QLabel("\n\nStep 1: Naming")
        promptLbl  = QtWidgets.QLabel("Please enter a unique name for this object.")


        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step1Lbl.setFont(bold)
        self.errorLbl.setFont(bold)


        # Make the title larger
        bold.setPointSize(15)
        welcomeLbl.setFont(bold)


        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(welcomeLbl)
        col1.addWidget(introLbl)
        col1.addWidget(step1Lbl)
        col1.addWidget(promptLbl)
        col1.addWidget(self.nameTxt)
        col1.addStretch(1)
        col1.addWidget(self.errorLbl)
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setMinimumHeight(750)
        self.setMinimumWidth(700)
        self.setLayout(mainHLayout)

    def isComplete(self):
        # Check if the user entered a valid name name is valid
        if len(self.nameTxt.text()) == 0:
            self.errorLbl.setText('')
            return False

        # Make sure the first letter is uppercase, and any spaces are converted to underscores
        name = self.nameTxt.text()
        name = name.replace(name[0], name[0].upper())
        name = name.replace('_', ' ')
        self.nameTxt.setText(name)


        # Record any characters that wre not valid
        validChars   = "0123456789abcdefghijklmnopqrstuvwxyz- "
        invalidChars = []
        name         = self.nameTxt.text()
        for char in name:
            if char.lower() not in validChars:
                invalidChars.append(char)
        invalidChars = list(set(invalidChars))


        # If there were errors, then display a message explaining why
        if len(invalidChars) > 0:
            self.errorLbl.setText('You cannot have the following characters in your object name: ' +
                                  ''.join(invalidChars))
            return False

        if name in self.forbiddenNames:
            self.errorLbl.setText('There is already an object named ' + name + '! \n'
                                  ' If you want to replace it, delete the objects folder and reload the program!')
            return False
        # If there were no errors, then turn the "next" button enabled, and make the error message dissapear
        self.errorLbl.setText('')
        return True


class OWPage2(QtWidgets.QWizardPage):
    newObject = QtCore.pyqtSignal()  # This emits when a valid object is selected, so that KPWPage3 can update

    def __init__(self, environment, parent):
        super(OWPage2, self).__init__(parent)

        # The final object is stored here:
        self.object       = None

        # The instructions are set in self.setStep(step) function, and are changed as needed
        self.stepLbl      = QtWidgets.QLabel("")
        self.howToLbl     = QtWidgets.QLabel("")
        self.hintLbl      = QtWidgets.QLabel("")  # This will tell the user if the object is good or bad

        # Create the camera widget and set it up
        self.vision       = environment.getVision()
        self.cameraWidget = CameraSelector(environment.getVStream().getFilteredWithID, parent=self)
        self.cameraWidget.play()
        self.cameraWidget.declinePicBtn.clicked.connect(self.tryAgain)
        self.cameraWidget.objSelected.connect(self.objectSelected)


        self.initUI()
        self.setStep(1)


    def initUI(self):
        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        self.stepLbl.setFont(bold)
        self.hintLbl.setFont(bold)

        # Create a special row for the camera that will force it to remain in the center, regardless of size changes
        camRow = QtWidgets.QHBoxLayout()
        camRow.addWidget(self.cameraWidget)
        camRow.addStretch(1)

        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(self.stepLbl)
        col1.addWidget(self.howToLbl)
        col1.addWidget(self.hintLbl)
        col1.addLayout(camRow)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)

    def setStep(self, step):
        if step == 1:
            s = "\n\nStep 2: Select the Object"
            h = "Please place the object you want to recognize in the center of the cameras view.\n\n"  +\
                "Make sure the background is consistent and there is nothing on the screen except the object. The" +\
                "\nwork area should be well lit, but not cause too much glare on the object if it's shiny. The video" +\
                "\nshould be focused, and the object in the orientation that it will be recognized in. \n\n" +\
                "When ready, Click the mouse on the corner of the object, drag it tightly over the object, then" + \
                "\nrelease the mouse button."

        if step == 2:
            s = "\n\nStep 3: Verify"
            h = "-test text-"
        self.stepLbl.setText(s)
        self.howToLbl.setText(h)


    def objectSelected(self):
        """
            Runs when the user has selected an object on the CameraSelector widget.
            It will verify if the object is trackable (has enough points), if so, it will set the vision to tracking
            mode, generate a "trackable" object, and set the camera to play.

            Then, it will display information about the object next to the camera, so that the user can decide if
            they want to keep this selected object or try again.

            If there are not enough keypoints, the program will warn the user that this is a bad idea. If there are
            zero keypoints, it won't allow the user to track it, and will automatically revert the camera to
            selection mode.
        """

        frame, rect = self.cameraWidget.getSelected()


        # Get the "target" object from the image and rectangle
        target = self.vision.tracker.getTarget(frame, rect)

        # Analyze it, and make sure it's a valid target. If not, return the camera to selection mode.
        if len(target.descrs) == 0 or len(target.keypoints) == 0:

            self.cameraWidget.takeAnother()
            return

        self.object = target
        self.completeChanged.emit()


        # Do all the necessary things: Change the instructions, the step
        self.setStep(2)
        des = "Good job, you have selected an object. Try moving the object around to see how accurate the" + \
            "\ntracking is. If it's not good enough, click 'Try Again'' on the bottom right of the camera to"       + \
            "\nreselect the object.\n\n" + \
            "Your selected object has " + str(len(self.object.descrs)) + " points to describe it. " + \
            "The more detail on the object, the more points"   + \
            "\nwill be found, and the better the tracking will be. If you are having trouble tracking, try adding" + \
            "\ndetail to the object by drawing on it or putting a sticker on it. \n"
        self.howToLbl.setText(des)


        # If the object was not very good, warn the user. Otherwise, state the # of points on the object
        if len(target.descrs) < 150:
            self.hintLbl.setText("Your selected object is not very detailed, or is too small. "
                                 "Tracking may not be very accurate.")
        else:
            self.hintLbl.setText("Tracking " + str(len(self.object.descrs)) + " Points")


        # Turn on the camera, and start tracking
        self.cameraWidget.play()
        self.vision.tracker.addTarget(self.object.name, self.object.image, self.object.rect)
        self.vision.startTracker()
        self.vision.addTrackerFilter()
        self.newObject.emit()

    def tryAgain(self):
        self.object = None
        self.completeChanged.emit()
        self.hintLbl.setText("")
        self.setStep(1)
        self.cameraWidget.play()
        self.cameraWidget.takeAnother()
        self.vision.trackerEndStopClear()


    def isComplete(self):
        return self.object is not None

    def close(self):
        self.cameraWidget.close()
        self.vision.clearTargets()
        self.vision.endTracker()
        self.vision.endTrackerFilter()


class OWPage3(QtWidgets.QWizardPage):
    """
    If anything is changed here, check the CoordWizard in CalibrationsGUI.py to make sure that it still works, since
    this class is used there.

    This page prompts the user to select the area of the object that can be picked up by the robot.

    Works with KPWPage2: Use setObject to set the picture. Every time a new object is set, it resets the widget somewhat
    and requets another picture. The isComplete() function returns true only when there is a selected rectangle.

    Only a rectangle is returned, to be used with PlaneTracker's pickupRect variable
    """
    def __init__(self, environment, parent):
        super(OWPage3, self).__init__(parent)


        # The final "rect" of the pickup area of the object is stored here: (x1,y1,x2,y2)
        self.pickupRect   = None

        self.yourDoneLbl  = QtWidgets.QLabel("")  # Displays a message to the user telling them they're all done!


        # Create the camera widget and set it up. The camera's image is set in self.setObject()
        self.vision       = environment.getVision()
        self.cameraWidget = CameraSelector(environment.getVStream().getFilteredWithID, parent=self)
        self.cameraWidget.pause()
        self.cameraWidget.declinePicBtn.clicked.connect(self.tryAgain)
        self.cameraWidget.objSelected.connect(self.rectSelected)

        self.initUI()


    def initUI(self):
        # Create the instructions
        desc = "You're almost done!\n\n" +\
               "Now that you have selected your object, please drag the mouse over the area of the object that is " +\
               "\nsmooth, flat, and able to be picked up by the robot's suction cup. \n\n" +\
               "\nThis information will be used in any commands that require the robot to pick up the object. If you" +\
               "\ndo not intend to use those functions, then just select an area around the center of the object.\n\n"

        stepLbl = QtWidgets.QLabel("Step 4: Select the Pickup Area")
        howToLbl = QtWidgets.QLabel(desc)


        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        stepLbl.setFont(bold)
        self.yourDoneLbl.setFont(bold)

        # Create a special row for the camera that will force it to remain in the center, regardless of size changes
        camRow = QtWidgets.QHBoxLayout()
        camRow.addStretch(1)
        camRow.addWidget(self.cameraWidget)
        camRow.addStretch(1)


        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(stepLbl)
        col1.addWidget(howToLbl)
        col1.addWidget(self.yourDoneLbl)
        col1.addStretch(1)
        col1.addLayout(camRow)
        col1.addStretch(1)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)


    def setObject(self, object):
        # Crop the image of just the object and display it on the Camera widget
        r       = object.rect
        cropped = object.image[r[1]:r[3], r[0]:r[2]]

        self.cameraWidget.setFrame(cropped)

        self.tryAgain()
        self.completeChanged.emit()

    def tryAgain(self):
        self.yourDoneLbl.setText("")
        self.pickupRect = None
        self.cameraWidget.takeAnother()
        self.completeChanged.emit()


    def rectSelected(self):
        # Runs when the user has selected an area on self.cameraWidget
        _, rect = self.cameraWidget.getSelected()
        self.pickupRect = rect
        self.yourDoneLbl.setText("Congratulations, you've created a new object! "
                                 "\nThis will now be saved in a seperate file, and can be used in any project.")
        self.completeChanged.emit()


    def isComplete(self):
        return self.pickupRect is not None

    def close(self):
        self.cameraWidget.close()