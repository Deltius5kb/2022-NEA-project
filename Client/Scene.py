import pygame, threading, socket, json
from ClientSocket import ClientSocket
from InputHandler import InputHandler
from Boxes import InputBox, TextBox
from Button import Button
from Text import Text

class Scene:
    def __init__(self, window, resolution, socket : ClientSocket = None) -> None:
        self.userQuit = False
        self.socket = socket

        #Whether or not these are held down
        self._shift = False
        self._alt = False
        self._ctrl = False
        self._backspace = False

        self._timeSinceLastBackspace = 0

        #Used to redner things on screen
        self._listOfBoxObjects = []
        self._listOfButtonObjects = []
        self._listOfTextObjects = []

        self._window = window
        self._resolution = resolution

        self._clock = pygame.time.Clock()
        self._inputHandler = InputHandler()

        #Helps performance to have a surface object instead of filling the entire screen every frame
        self._backgroundSurface = pygame.Surface((int(self._resolution[0] * 1920), int(self._resolution[1] * 1080)))
        self._backgroundSurface.fill((0,0,0))

    def main(self):
        self._clock.tick()
        self._timeSinceLastBackspace += self._clock.get_time()

        self._HandleInputs()

        #Automatic removal of text every 50 milliseconds
        if self._backspace and self._timeSinceLastBackspace >= 50:
            for box in self._listOfBoxObjects:
                if box.isActive:
                    box.RemoveLetter(self._ctrl)
            self._timeSinceLastBackspace = 0

        for buttonObject in self._listOfButtonObjects:
            if buttonObject.CheckForCollision(pygame.mouse.get_pos()):
                buttonObject.SetActive()
            else:
                buttonObject.SetInactive()

        self._Render()

    def _Render(self):
        self._window.blit(self._backgroundSurface, (0,0))
        for box in self._listOfBoxObjects:
            box.Render(self._window)
        for button in self._listOfButtonObjects:
            button.Render(self._window)
        for textObject in self._listOfTextObjects:
            textObject.Render(self._window)

    def _HandleInputs(self):
        self._inputHandler.CheckInputs()
        i = 0
        while i < len(self._inputHandler.inputsList):            
            if self._inputHandler.inputsList[i] == "QUIT":
                self.userQuit = True
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i] == "SHIFTDOWN":
                self._shift = True
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i] == "SHIFTUP":
                self._shift = False
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i] == "ALTDOWN":
                self._alt = True
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i] == "ALTUP":
                self._alt = False
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i] == "CONTROLDOWN":
                self._ctrl = True
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i] == "CONTROLUP":
                self._ctrl = False
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i] == "BACKSPACEDOWN":
                self._backspace = True
                self._timeSinceLastBackspace = -200
                for box in self._listOfBoxObjects:
                    if box.isActive:
                        box.RemoveLetter(self._ctrl)
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i] == "BACKSPACEUP":
                self._backspace = False
                self._inputHandler.inputsList.pop(i)
            else:
                i += 1

#Displays text that changes in the middle of the screen
class ConnectionScreen(Scene):
    def __init__(self, window, resolution, socket=None) -> None:
        super().__init__(window, resolution, socket)
        self.connected = False

        #Used for changing the number of dots in the text
        self.__timeSinceLastMessageUpdate = 0
        self.__numberOfDots = 0

        self.__font = pygame.font.SysFont("Calibri", int(72 * self._resolution[1]))

        textSize = self.__font.size("Connecting to server...")
        textLocation = (int((self._resolution[0] * 1920 - textSize[0]) / 2), int((self._resolution[1] * 1080 - textSize[1]) / 2))

        self.__textToRender = "Connecting to server"
        self.__textObject = Text(self.__font, text=self.__textToRender, location=textLocation)

        self._listOfTextObjects = [self.__textObject]
        
        #Used for connecting to server
        self.__serverSearchThread = threading.Thread(target=self.__ConnectToServer, daemon=True)
        self.__serverSearchThread.start()

    def main(self):
        super().main()
        self.__timeSinceLastMessageUpdate += self._clock.get_time()
        if self.__timeSinceLastMessageUpdate >= 700:
            self.__textToRender = "Connecting to server" + "." * self.__numberOfDots
            self.__textObject.SetText(self.__textToRender)
            self.__numberOfDots += 1
            if self.__numberOfDots == 4:
                self.__numberOfDots = 0
            self.__timeSinceLastMessageUpdate = 0

    def __ConnectToServer(self):
        while not self.connected:
            try:
                self.socket = ClientSocket()
                self.connected = True
            except socket.error:
                pass

    def _HandleInputs(self):
        super()._HandleInputs()
        #Empties list so inputs dont carry over to next scene
        self._inputHandler.inputsList = []

#Displays username and password input boxes
class LoginScreen(Scene):
    def __init__(self, window, resolution, socket=None) -> None:
        super().__init__(window, resolution, socket)
        self.loggedIn = False
        self.userWantsToCreateAccount = False
        self.__detailsSent = False

        inputBoxFont = pygame.font.SysFont("Courier New", int(36 * self._resolution[1]))

        #Need 2 inputboxes, 2 text and 1 button
        inputBoxSize = (int(625 * self._resolution[0]), int(60 * self._resolution[1]))
        #Button needs to be centred and 400 pixels down
        usernameBoxLocation = (int((self._resolution[0] * 1920 - inputBoxSize[0]) / 2), int(400 * self._resolution[1]))
        passwordBoxLocation = (int((self._resolution[0] * 1920 - inputBoxSize[0]) / 2), int(540 * self._resolution[1]))
        usernameRect = pygame.Rect(usernameBoxLocation[0], usernameBoxLocation[1], inputBoxSize[0], inputBoxSize[1])
        passwordRect = pygame.Rect(passwordBoxLocation[0], passwordBoxLocation[1], inputBoxSize[0], inputBoxSize[1])
        self.__usernameBox = InputBox(usernameRect, inputBoxFont, self._resolution, (40,40,40), (25,25,25), (255,255,255), "")
        self.__passwordBox = InputBox(passwordRect, inputBoxFont, self._resolution, (40,40,40), (25,25,25), (255,255,255), "", hashed=True)

        #Button size for continue and register buttons
        buttonSize = (400 * self._resolution[0], 60 * self._resolution[1])
        #Button needs to be centred and 680 pixels down
        continueButtonLocation = (int((self._resolution[0] * 1920 - buttonSize[0]) / 2), int(680 * self._resolution[1]))
        continueButtonRect = pygame.Rect(continueButtonLocation[0], continueButtonLocation[1], buttonSize[0], buttonSize[1])
        self.__continueButton = Button(continueButtonRect, (40,40,40), (25,25,25), (255,255,255), text="Continue")
        
        #Need register button same size as continue button
        registerButtonLocation = (int(1400 * self._resolution[0]), int(950 * self._resolution[1]))
        resgisterButtonRect = pygame.Rect(registerButtonLocation, buttonSize)
        self.__registerButton = Button(resgisterButtonRect, (40,40,40), (25,25,25), (255,255,255), text="Register")

        #Text needs to be 5 pixels to the right of the corresponding box and needs to be 25 pixels above (so 25 pixels and the height of the text itself)
        usernameTextSize = inputBoxFont.size("Username")
        usernameTextLocation = (int(usernameBoxLocation[0] + 5 * self._resolution[0]), int(usernameBoxLocation[1] - 25 * self._resolution[1] - usernameTextSize[1]))
        self.__usernameText = Text(inputBoxFont, text="Username", location=usernameTextLocation)
        passwordTextSize = inputBoxFont.size("Password")
        passwordTextLocation = (int(passwordBoxLocation[0] + 5 * self._resolution[0]), int(passwordBoxLocation[1] - 25 * self._resolution[1] - passwordTextSize[1]))
        self.__passwordText = Text(inputBoxFont, text="Password", location=passwordTextLocation)

        #These lists are used to render things on the screen, they are iterated through
        self._listOfBoxObjects = [self.__usernameBox, self.__passwordBox]
        self._listOfButtonObjects = [self.__continueButton, self.__registerButton]
        self._listOfTextObjects = [self.__usernameText, self.__passwordText]

    def main(self):
        super().main()
        if self.__continueButton.clicked:
            if not self.__detailsSent:
                username = self.__usernameBox.text
                password = self.__passwordBox.text
                self.socket.msgsToSend.append(f"!LOGIN:{username},{password}")
                self.__detailsSent = True
            else:
                self.__HandleMessages()

    def __HandleMessages(self):
        unusedMessages = []
        while len(self.socket.receivedMsgs) != 0:
            message = self.socket.receivedMsgs.pop()
            if message == "!PASSWORDCORRECT" or message == "!ALREADYLOGGEDIN":
                print("Logged in")
                self.loggedIn = True
            elif message == "!PASSWORDINCORRECT" or message == "!USERNAMENOTFOUND":
                self.__continueButton.clicked = False
                self.__detailsSent = False
                self.__usernameBox.text = ""
                self.__passwordBox.text = ""
                self.__continueButton.SetText("Continue")
        for box in self._listOfBoxObjects:
            box.UpdateRender()

    def _HandleInputs(self):
        super()._HandleInputs()
        if not self.__continueButton.clicked:
            i = 0
            while i < len(self._inputHandler.inputsList):
                if self._inputHandler.inputsList[i][:6] == "CLICK:":
                    clickLocation = self._inputHandler.inputsList[i][6:].split(",")
                    clickLocation = (int(clickLocation[0]), int(clickLocation[1]))
                    if self.__continueButton.CheckForCollision(clickLocation):
                        self.__continueButton.clicked = True
                        self.__continueButton.SetText("Checking...")
                    elif self.__registerButton.CheckForCollision(clickLocation):
                        self.__registerButton.clicked = True
                        self.userWantsToCreateAccount = True
                    else:
                        for box in self._listOfBoxObjects:
                            if box.CheckForCollisionWithMouse(clickLocation):
                                box.SetActive()
                            else:
                                box.SetInactive()
                    self._inputHandler.inputsList.pop(i)
                elif self._inputHandler.inputsList[i][:3] == "KD_":
                    key = self._inputHandler.inputsList[i][3:]
                    for box in self._listOfBoxObjects:
                        if box.isActive:
                            box.AddLetter(key)
                    self._inputHandler.inputsList.pop(i)
                #Sets the other box to be active than the one that is active
                elif self._inputHandler.inputsList[i] == "TABDOWN":
                    if self.__usernameBox.isActive:
                        self.__usernameBox.SetInactive()
                        self.__passwordBox.SetActive()
                    elif self.__passwordBox.isActive:
                        self.__usernameBox.SetActive()
                        self.__passwordBox.SetInactive()
                    self._inputHandler.inputsList.pop(i)
                elif self._inputHandler.inputsList[i] == "RETURNDOWN":
                    self.__continueButton.clicked = True
                    self.__continueButton.SetText("Checking...")
                    self._inputHandler.inputsList.pop(i)
                elif self._inputHandler.inputsList[i] == "RETURNUP":
                    #Returnup shouldnt be added back to queue
                    self._inputHandler.inputsList.pop(i)
                else:
                    i += 1

class RegisterScreen(Scene):
    def __init__(self, window, resolution, socket: ClientSocket = None) -> None:
        super().__init__(window, resolution, socket)

        self.backbuttonPressed = False
        self.registered = False
        self.__submitButtonPressed = False

        boxFont = pygame.font.SysFont("Courier New", int(28 * self._resolution[1]))
        boxColourActive = (40,40,40)
        boxColourInactive = (25,25,25)

        boxRectSize = (int(625 * self._resolution[0]), int(60 * self._resolution[1]))
        
        #Usernamebox
        usernameRectLocation = (int((self._resolution[0] * 1920 - boxRectSize[0]) / 2), int(400 * self._resolution[1]))
        usernameRect = pygame.Rect(usernameRectLocation, boxRectSize)
        self.__usernameBox = InputBox(usernameRect, boxFont, self._resolution, boxColourActive, boxColourInactive, (255,255,255), "")
        
        #Passwordbox
        passwordRectLocation = (int((self._resolution[0] * 1920 - boxRectSize[0]) / 2), int(570 * self._resolution[1]))
        passwordRect = pygame.Rect(passwordRectLocation, boxRectSize)
        self.__passwordBox = InputBox(passwordRect, boxFont, self._resolution, boxColourActive, boxColourInactive, (255,255,255), "", hashed=True)

        #Password confirm box
        confirmRectLocation = (int((self._resolution[0] * 1920 - boxRectSize[0]) / 2), int(740 * self._resolution[1]))
        confirmRect = pygame.Rect(confirmRectLocation, boxRectSize)
        self.__confirmBox = InputBox(confirmRect, boxFont, self._resolution, boxColourActive, boxColourInactive, (255,255,255), "", hashed=True)

        self._listOfBoxObjects = [self.__usernameBox, self.__passwordBox, self.__confirmBox]

        buttonSize = (int(300 * self._resolution[0]), int(60 * self._resolution[1]))

        #Back button
        backButtonLocation = (int(650 * self._resolution[0]), int(830 * self._resolution[1]))
        backButtonRect = pygame.Rect(backButtonLocation, buttonSize)
        self.__backButton = Button(backButtonRect, boxColourActive, boxColourInactive, (255,255,255), text="Back")

        #Submit button
        submitButtonLocation = (int(980 * self._resolution[0]), int(830 * self._resolution[1]))
        submitButtonRect = pygame.Rect(submitButtonLocation, buttonSize)
        self.__submitButton = Button(submitButtonRect, boxColourActive, boxColourInactive, (255,255,255), text="Submit")

        self._listOfButtonObjects = [self.__backButton, self.__submitButton]

        #Username text
        textFont = pygame.font.SysFont("Courier New", int(36 * self._resolution[1]))
        self.__usernameText = Text(textFont, text="Username", location=(int(655 * self._resolution[0]), int(350 * self._resolution[1])))
        self.__passwordText = Text(textFont, text="Password", location=(int(655 * self._resolution[0]), int(520 * self._resolution[1])))
        self.__confirmText = Text(textFont, text="Confirm password", location=(int(655 * self._resolution[0]), int(690 * self._resolution[1])))

        self._listOfTextObjects = [self.__usernameText, self.__passwordText, self.__confirmText]

    def main(self):
        super().main()

        #Checks if buttons were pressed
        for button in self._listOfButtonObjects:
            if button.clicked:
                if button == self.__backButton:
                    self.backbuttonPressed = True
                elif button == self.__submitButton:
                    if self.__passwordBox.text == self.__confirmBox.text and self.__passwordBox.text != "":
                        self.socket.msgsToSend.append(f"!REGISTER:{self.__usernameBox.text},{self.__passwordBox.text}")
                        self.__submitButtonPressed = True
                    else:
                        self.__submitButton.clicked = False
                        button.clicked = False
                        for box in self._listOfBoxObjects:
                            box.text = ""

        while self.__submitButtonPressed and not self.registered:
            self.__HandleMessages()

    def __HandleMessages(self):
        i = 0
        while i < len(self.socket.receivedMsgs):
            if self.socket.receivedMsgs[i] == "!REGISTEREDSUCCESFULLY":
                self.registered = True
                self.socket.receivedMsgs.pop(i)
            elif self.socket.receivedMsgs[i] == "!ANERROROCCURRED":
                self.__submitButtonPressed = False
                self.__submitButton.clicked = False
                self.socket.receivedMsgs.pop(i)
            else:
                i += 1

    def _HandleInputs(self):
        super()._HandleInputs()
        #Need to check for clicks, tab or keys being pressed
        i = 0
        while i < len(self._inputHandler.inputsList):
            if self._inputHandler.inputsList[i][:6] == "CLICK:":
                clickLocation = self._inputHandler.inputsList[i][6:].split(",")
                clickLocation = (int(clickLocation[0]), int(clickLocation[1]))
                for box in self._listOfBoxObjects:
                    #If clicked on box
                    if box.CheckForCollisionWithMouse(clickLocation):
                        box.SetActive()
                    else:
                        box.SetInactive()
                for button in self._listOfButtonObjects:
                    if button.CheckForCollision(clickLocation):
                        button.clicked = True
                self._inputHandler.inputsList.pop(i)
            #Adds letters to textbox
            elif self._inputHandler.inputsList[i][:3] == "KD_":
                key = self._inputHandler.inputsList[i][3:]
                #Checks if the key is a letter and not a special character
                if key.isalpha():
                    for box in self._listOfBoxObjects:
                        if box.isActive:
                            box.AddLetter(key)
                self._inputHandler.inputsList.pop(i)
            #Switches active textbox
            elif self._inputHandler.inputsList[i] == "TABDOWN":
                if self.__usernameBox.isActive:
                    self.__usernameBox.SetInactive()
                    self.__passwordBox.SetActive()
                elif self.__passwordBox.isActive:
                    self.__passwordBox.SetInactive()
                    self.__confirmBox.SetActive()
                elif self.__confirmBox.isActive:
                    self.__confirmBox.SetInactive()
                    self.__usernameBox.SetActive()
                self._inputHandler.inputsList.pop(i)
            else:
                i += 1

#Displays main menu for user to make choice what to see
class MainMenu(Scene):
    def __init__(self, window, resolution, socket=None) -> None:
        super().__init__(window, resolution, socket)
        self.userChoice = None
        colourActive = (40,40,40)
        colourInactive = (25,25,25)
        textColour = (255,255,255)

        self.__titleFont = pygame.font.SysFont("Calibri", int(140 * self._resolution[1]))

        boxSize = (int(2/5 * self._resolution[0] * 1920), int(150 * self._resolution[1]))
        boxX = int((self._resolution[0] * 1920 - boxSize[0]) / 2)

        #Needs 4 buttons and a title text
        playButtonRect = pygame.Rect(boxX, int(320 * self._resolution[1]), boxSize[0], boxSize[1])
        statisticsButtonRect = pygame.Rect(boxX, int(500 * self._resolution[1]), boxSize[0], boxSize[1])
        settingsButtonRect = pygame.Rect(boxX, int(680 * self._resolution[1]), boxSize[0], boxSize[1])
        quitButtonRect = pygame.Rect(boxX, int(860 * self._resolution[1]), boxSize[0], boxSize[1])
    
        self.__playButton = Button(playButtonRect, colourActive, colourInactive, textColour, text="Play")
        self.__statisticsButton = Button(statisticsButtonRect, colourActive, colourInactive, textColour, text="Statistics")
        self.__settingsButton = Button(settingsButtonRect, colourActive, colourInactive, textColour, text = "Settings")
        self.__quitButton = Button(quitButtonRect, colourActive, colourInactive, textColour, text="Quit")

        self._listOfButtonObjects = [self.__playButton, self.__statisticsButton, self.__settingsButton, self.__quitButton]

        #Need title text
        titleSize = self.__titleFont.size("SpeedTyper")
        titleLocation = (int((self._resolution[0] * 1920 - titleSize[0]) / 2), int(160 * self._resolution[1]))
        self.__titleText = Text(self.__titleFont, text="SpeedTyper", location=titleLocation, colour=(255,165,0))
        
        self._listOfTextObjects = [self.__titleText]

    def main(self):
        super().main()
        for button in self._listOfButtonObjects:
            if button.clicked:
                if button.text == "Quit":
                    self.userQuit = True
                else:
                    self.userChoice = button.text

    def _HandleInputs(self):
        super()._HandleInputs()
        i = 0
        while i < len(self._inputHandler.inputsList):
            if self._inputHandler.inputsList[i][:6] == "CLICK:":
                clickLocation = self._inputHandler.inputsList[i][6:].split(",")
                clickLocation = (int(clickLocation[0]), int(clickLocation[1]))
                for button in self._listOfButtonObjects:
                    if button.CheckForCollision(clickLocation):
                        button.clicked = True
                self._inputHandler.inputsList.pop(i)
            else:
                i += 1

class SettingsScreen(Scene):
    def __init__(self, window, resolution, settings, socket: ClientSocket = None) -> None:
        super().__init__(window, resolution, socket)
        self.__settings = settings
        self.backButtonPressed = False

        textColour = (255,255,255)
        activeColour = (40,40,40)
        inactiveColour = (25,25,25)

        #Settings title text
        titleFont = pygame.font.SysFont("Calibri", int(108 * self._resolution[1]))
        titleSize = titleFont.size("Settings")
        titleLocation = (int((self._resolution[0] * 1920 - titleSize[0]) / 2), int(105 * self._resolution[1]))
        self.__titleText = Text(titleFont, text="Settings", location=titleLocation)

        infoTextFont = pygame.font.SysFont("Calibri", int(48 * self._resolution[1]))
        
        #Volume text
        volumeLocation = (int(225 * self._resolution[0]), int(315 * self._resolution[1]))
        self.__volumeText = Text(infoTextFont, text=f'Volume(current value = {self.__settings["Volume"]}):', location=volumeLocation)
        #Resolution text
        resLocation = (int(235 * self._resolution[0]), int(390 * self._resolution[1]))
        self.__resolutionText = Text(infoTextFont, text="Resolution(seperated by x):", location=resLocation)

        self._listOfTextObjects = [self.__titleText, self.__volumeText, self.__resolutionText]

        #Boxes
        boxSize = (int(450 * self._resolution[0]), int(60 * self._resolution[1]))
        boxTextFont = pygame.font.SysFont("Courier New", int(48 * self._resolution[1]))
        
        volumeBoxLocation = (int(1000 * self._resolution[0]), int(305 * self._resolution[1]))
        volumeRect = pygame.Rect(volumeBoxLocation, boxSize)
        self.__volumeBox = InputBox(volumeRect, boxTextFont, self._resolution, activeColour, inactiveColour, textColour, "")

        resBoxLocation = (int(1000 * self._resolution[0]), int(385 * self._resolution[1]))
        resRect = pygame.Rect(resBoxLocation, boxSize)
        self.__resBox = InputBox(resRect, boxTextFont, self._resolution, activeColour, inactiveColour, textColour, "")

        self._listOfBoxObjects = [self.__volumeBox, self.__resBox]

        #Buttons
        buttonSize = (int(500 * self._resolution[0]), int(130 * self._resolution[1]))
        backButtonLocation = (int(446 * self._resolution[0]), int(840 * self._resolution[1])) 
        backButtonRect = pygame.Rect(backButtonLocation, buttonSize)
        self.__backButton = Button(backButtonRect, activeColour, inactiveColour, textColour, text="Back to main menu")
    
        saveButtonLocation = (int(980 * self._resolution[0]), int(840 * self._resolution[1]))
        saveButtonRect = pygame.Rect(saveButtonLocation, buttonSize)
        self.__saveButton = Button(saveButtonRect, activeColour, inactiveColour, textColour, text=("Save(restart to apply)"))

        self._listOfButtonObjects = [self.__backButton, self.__saveButton]

    def main(self):
        super().main()

        if self.__saveButton.clicked:
            try:
                newVolume = int(self.__volumeBox.text)
                if newVolume > 100:
                    newVolume = 100
                elif newVolume < 0:
                    newVolume = 0
            except:
                newVolume = self.__settings["Volume"]
            try:
                newRes = self.__resBox.text.split("x")
                int(newRes[0])
                int(newRes[1])
                newRes = f"{newRes[0]}x{newRes[1]}"
            except:
                newRes = self.__settings["Resolution"]

            self.__settings["Volume"] = newVolume
            self.__settings["Resolution"] = newRes

            file = open("settings.json", "w")
            jsonsettings = json.dumps(self.__settings)
            file.write(jsonsettings)
            file.close()
            self.__saveButton.clicked = False

    def _HandleInputs(self):
        super()._HandleInputs()
        i = 0
        while i < len(self._inputHandler.inputsList):
            if self._inputHandler.inputsList[i][:6] == "CLICK:":
                clickLocation = self._inputHandler.inputsList[i][6:].split(",")
                clickLocation = (int(clickLocation[0]), int(clickLocation[1]))
                if self.__saveButton.CheckForCollision(clickLocation):
                    self.__saveButton.clicked = True
                elif self.__backButton.CheckForCollision(clickLocation):
                    self.__backButton.clicked = True
                    self.backButtonPressed = True
                else:
                    for box in self._listOfBoxObjects:
                        if box.CheckForCollisionWithMouse(clickLocation):
                            box.SetActive()
                        else:
                            box.SetInactive()
                self._inputHandler.inputsList.pop(i)
            elif self._inputHandler.inputsList[i][:3] == "KD_":
                key = self._inputHandler.inputsList[i][3:]
                for box in self._listOfBoxObjects:
                    if box.isActive:
                        box.AddLetter(key)
                self._inputHandler.inputsList.pop(i)
            #Sets the other box to be active than the one that is active
            elif self._inputHandler.inputsList[i] == "TABDOWN":
                if self.__volumeBox.isActive:
                    self.__volumeBox.SetInactive()
                    self.__resBox.SetActive()
                elif self.__resBox.isActive:
                    self.__volumeBox.SetActive()
                    self.__resBox.SetInactive()
                self._inputHandler.inputsList.pop(i)
            else:
                i += 1

class StatisticsScreen(Scene):
    def __init__(self, window, resolution, data, socket: ClientSocket = None) -> None:
        super().__init__(window, resolution, socket)
        # These are here for reference as to what is in data, it has been copied from the generation of the database
        # Username TEXT PRIMARY KEY, 0
        # Password BLOB, 1
        # WordsTyped INTEGER, 2 
        # TimePlayed INTEGER, 3
        # Elo INTEGER, 4
        # HighestElo INTEGER, 5
        # GamesWon INTEGER, 6
        # GamesPlayed INTEGER, 7
        # LongestStreak INTEGER, 8
        # LargestWinMargin FLOAT, 9
        # LettersTyped INTEGER, 10
        # LettersTypedCorrectly INTEGER, 11
        # SumOfOpponentsELo INTEGER, 12
        # CurrentWinstreak INTEGER 13

        #Find WPM
        wordsTyped = data[2]
        timePlayed = data[3]
        if timePlayed > 0:
            avgWPM = round(wordsTyped / timePlayed, 2)
        else:
            avgWPM = 0

        #Winrate
        gamesWon = data[6]
        gamesPlayed = data[7]
        if gamesPlayed > 0:
            winrate = round(gamesWon / gamesPlayed * 100, 2)
        else:
            winrate = 0

        #Just data
        longestStreak = data[8]
        currentStreak = data[13]
        
        currentELo = round(data[4], 2)
        highestELo = round(data[5], 2)

        largestWinMargin = int(data[9])

        self.__font = pygame.font.SysFont("Courier New", int(36 * self._resolution[1]), bold=True)
        maxTextHeight = self.__font.size("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")[1]
        thingsToRender = [avgWPM, gamesPlayed, gamesWon, winrate, longestStreak, currentStreak, currentELo, highestELo, largestWinMargin]

        #Dimensions for area text is rendered in
        textBoxTopLeft = (int(140 * self._resolution[0]), int(260 * self._resolution[0]))
        maxWidth = self._resolution[0] * 1920 - 2 * textBoxTopLeft[0]
        charWidth = self.__font.size("a")[0]
        maxTextWidth = int(maxWidth / charWidth)

        text = "Average WPM (Words Per Minute):"
        lenText = len(text)
        avgWPM = text + "{info:>{width}}".format(info = avgWPM, width = maxTextWidth - lenText)

        text = "Games played:"
        lenText = len(text)
        gamesPlayed = text + "{info:>{width}}".format(info = gamesPlayed, width = maxTextWidth - lenText)

        text = "Games won:"
        lenText = len(text)
        gamesWon = text + "{info:>{width}}".format(info = gamesWon, width = maxTextWidth - lenText)

        text = "Winrate (%):"
        lenText = len(text)
        winrate = text + "{info:>{width}}".format(info = winrate, width = maxTextWidth - lenText)

        text = "Longest winstreak:"
        lenText = len(text)
        longestStreak = text + "{info:>{width}}".format(info = longestStreak, width = maxTextWidth - lenText)

        text = "Current winstreak:"
        lenText = len(text)
        currentStreak = text + "{info:>{width}}".format(info = currentStreak, width = maxTextWidth - lenText)

        text = "Current ELo:"
        lenText = len(text)
        currentELo = text + "{info:>{width}}".format(info = currentELo, width = maxTextWidth - lenText)

        text = "Highest ELo:"
        lenText = len(text)
        highestELo = text + "{info:>{width}}".format(info = highestELo, width = maxTextWidth - lenText)

        text = "Largest win margin:"
        lenText = len(text)
        largestWinMargin = text + "{info:>{width}}".format(info = largestWinMargin, width = maxTextWidth - lenText)

        textToRender = [avgWPM, gamesPlayed, gamesWon, winrate, longestStreak, currentStreak, currentELo, highestELo, largestWinMargin]

        textX = textBoxTopLeft[0]
        textY = textBoxTopLeft[1]
        #Make background black
        self._window.fill((0,0,0))
        
        #Render title text
        titleFont = pygame.font.SysFont("Calibri", int(108 * self._resolution[1]))
        titleRender = titleFont.render("Statistics", True, (255,255,255))
        titleSize = titleRender.get_size()
        titleLocation = (int((self._resolution[0] * 1920 - titleSize[0]) / 2), int(75 * self._resolution[1]))
        self._window.blit(titleRender, titleLocation)

        #Render information on screen
        for i in range(len(textToRender)):
            textRender = self.__font.render(textToRender[i], True, (255,255,255))
            renderLocation = (textX, textY + (maxTextHeight + 5) * i)
            self._window.blit(textRender, renderLocation)

        #For back button
        self.backButtonPressed = False
        backButtonSize = (int(500 * self._resolution[0]), int(130 * self._resolution[1]))
        backButtonLocation = (int(250 * self._resolution[0]), int(850 * self._resolution[1]))
        backRect = pygame.Rect(backButtonLocation, backButtonSize)
        self.__backButton = Button(backRect, (40,40,40), (25,25,25), (255,255,255), text="Back")

    def main(self):
        self._HandleInputs()

        if self.__backButton.CheckForCollision(pygame.mouse.get_pos()):
            self.__backButton.SetActive()
        else:
            self.__backButton.SetInactive()

        self._Render()

    def _Render(self):
        #Override to prevent background fill
        self.__backButton.Render(self._window)

    def _HandleInputs(self):
        super()._HandleInputs()
        i = 0
        while i < len(self._inputHandler.inputsList):
            if self._inputHandler.inputsList[i][:6] == "CLICK:":
                clickLocation = self._inputHandler.inputsList[i][6:].split(",")
                clickLocation = (int(clickLocation[0]), int(clickLocation[1]))
                if self.__backButton.CheckForCollision(clickLocation):
                    self.backButtonPressed = True
                    self.__backButton.clicked = True
                self._inputHandler.inputsList.pop(i)
            else:
                i += 1

#Displays message that they are in queue
class MatchmakingScreen(Scene):
    def __init__(self, window, resolution, socket=None) -> None:
        super().__init__(window, resolution, socket)
        self.gameFound = False
        self.userClickedBackButton = False

        #Used for changing the number of dots in the text
        self.__timeSinceLastMessageUpdate = 0
        self.__numberOfDots = 0

        self.__font = pygame.font.SysFont("Calibri", int(72 * self._resolution[1]))

        #Text for the screen
        textSize = self.__font.size("Looking for game...")
        textLocation = (int((self._resolution[0] * 1920 - textSize[0]) / 2), int((self._resolution[1] * 1080 - textSize[1]) / 2))

        self.__textToRender = "Looking for game"
        self.__textObject = Text(self.__font, text=self.__textToRender, location=textLocation)

        self._listOfTextObjects = [self.__textObject]

        #Button to dequeue
        backButtonSize = (400 * self._resolution[0], 60 * self._resolution[1])
        #Button needs to be centred and 680 pixels down
        backButtonLocation = ((self._resolution[0] * 1920 - backButtonSize[0]) / 2, 680 * self._resolution[1])
        backButtonRect = pygame.Rect(backButtonLocation[0], backButtonLocation[1], backButtonSize[0], backButtonSize[1])
        self.backButton = Button(backButtonRect, (40,40,40), (25,25,25), (255,255,255), text="Back")

        self._listOfButtonObjects = [self.backButton]

    def main(self):
        super().main()
        self.__TextAnimation()
        self.__HandleMessages()

    def __HandleMessages(self):
        i = 0
        while i < len(self.socket.receivedMsgs):
            if self.socket.receivedMsgs[i] == "!GAMEFOUND":
                self.gameFound = True
                self.socket.receivedMsgs.pop(i)
            else:
                i += 1

    def _HandleInputs(self):
        super()._HandleInputs()
        i = 0
        while i < len(self._inputHandler.inputsList):
            if self._inputHandler.inputsList[i][:6] == "CLICK:":
                clickLocation = self._inputHandler.inputsList[i][6:].split(",")
                clickLocation = (int(clickLocation[0]), int(clickLocation[1]))
                for button in self._listOfButtonObjects:
                    if button.CheckForCollision(clickLocation):
                        button.clicked = True
                        if button.text == "Back":
                            self.userClickedBackButton = True
                self._inputHandler.inputsList.pop(i)
            else:
                i += 1

    def __TextAnimation(self):
        #Used for animation of looking for game text
        self.__timeSinceLastMessageUpdate += self._clock.get_time()
        if self.__timeSinceLastMessageUpdate >= 700:
            self.__textToRender = "Looking for game" + "." * self.__numberOfDots
            self.__textObject.SetText(self.__textToRender)
            self.__numberOfDots += 1
            if self.__numberOfDots == 4:
                self.__numberOfDots = 0
            self.__timeSinceLastMessageUpdate = 0

#Scene for timer
class TimerScene(Scene):
    def __init__(self, window, resolution, socket=None) -> None:
        super().__init__(window, resolution, socket)
        self.timerFinished = False
        self.__font = pygame.font.SysFont("Calibri", int(72 * self._resolution[1]))

        #Text for the screen
        textSize = self.__font.size("Waiting for timer")
        textLocation = (int((self._resolution[0] * 1920 - textSize[0]) / 2), int((self._resolution[1] * 1080 - textSize[1]) / 2))
        self.__textObject = Text(self.__font, text="Waiting for timer", location=textLocation)
        self._listOfTextObjects = [self.__textObject]

    def main(self):
        super().main()
        self.__HandleMessages()

    def __HandleMessages(self):
        i = 0
        while i < len(self.socket.receivedMsgs):
            if self.socket.receivedMsgs[i][:10] == "!TIMELEFT:":
                timeLeft = self.socket.receivedMsgs[i][10:]
                #Updates timer on screen
                self.__UpdateTextObject(timeLeft)
                if int(timeLeft) == 0:
                    self.timerFinished = True
                #Removes message from list
                self.socket.receivedMsgs.pop(i)
            else:
                i += 1

    #Updates text and location to be centred
    def __UpdateTextObject(self, newText):
        textSize = self.__font.size(newText)
        textLocation = (int((self._resolution[0] * 1920 - textSize[0]) / 2), int((self._resolution[1] * 1080 - textSize[1]) / 2))
        self.__textObject.SetText(newText)
        self.__textObject.location = textLocation

    def _HandleInputs(self):
        super()._HandleInputs()
        #Empties inputs list so they dont carry over to the next scene
        self._inputHandler.inputsList = []

class RaceScene(Scene):
    def __init__(self, window, resolution, previewText, socket=None) -> None:
        super().__init__(window, resolution, socket)
        self.playerFinished = False
        self.gameOver = False
        #Colours for textbox        
        colourActive = (40,40,40)
        colourInactive = (25,25,25)
        previewTextColour = (160,160,160)
        incorrectTextColour = (255,0,0)

        #Main textbox
        textBoxFont = pygame.font.SysFont("Courier New", int(42 * self._resolution[1]))

        textBoxSize = (self._resolution[0] * 1920 * 2/5, 50 * self._resolution[1])
        textBoxLocation = ((self._resolution[0] * 1920 - textBoxSize[0]) / 2, 250 * self._resolution[1])
        textBoxRect = pygame.Rect(textBoxLocation[0], textBoxLocation[1], textBoxSize[0], textBoxSize[1])
        self.__textBox = TextBox(textBoxRect, textBoxFont, self._resolution, colourActive, colourInactive, (38, 191, 79), previewText, previewTextColour, incorrectTextColour)

        #Other player textbox
        #Box is 250 pixels above the bottom of the screen
        textBoxLocation = ((self._resolution[0] * 1920 - textBoxSize[0]) / 2, self._resolution[1] * 1080 - (250 + textBoxSize[1]) * self._resolution[1])
        textBoxRect = pygame.Rect(textBoxLocation[0], textBoxLocation[1], textBoxSize[0], textBoxSize[1])
        self.__opponentTextBox = TextBox(textBoxRect, textBoxFont, self._resolution, colourActive, colourInactive, (38, 191, 79), previewText, previewTextColour, incorrectTextColour)

        self._listOfBoxObjects = [self.__textBox, self.__opponentTextBox]

        #Needs to be attribute as it will be used to change text later on
        self.timerFinished = False
        self.__font = pygame.font.SysFont("Calibri", int(72 * self._resolution[1]))

        #Text for timer
        textSize = self.__font.size("30")
        textLocation = (int((self._resolution[0] * 1920 - textSize[0]) / 2), int((self._resolution[1] * 1080 - textSize[1]) / 2))
        self.__textObject = Text(self.__font, text="30", location=textLocation)
        self._listOfTextObjects = [self.__textObject]

    #Override for performance improvements
    def main(self):
        self._clock.tick()
        self._timeSinceLastBackspace += self._clock.get_time()

        self._HandleInputs()

        #Automatic removal of text every 50 milliseconds
        if self._backspace and self._timeSinceLastBackspace >= 50 and self.__textBox.isActive:
            self.__textBox.RemoveLetter(self._ctrl)
            self._timeSinceLastBackspace = 0

        self._Render()
        self.__HandleMessages()

    def _Render(self):
        self._window.blit(self._backgroundSurface, (0,0))
        self.__textBox.Render(self._window)
        self.__opponentTextBox.Render(self._window)
        self.__textObject.Render(self._window)

    def SetPreviewText(self, previewText):
        self.__textBox.previewText = previewText

    def __HandleMessages(self):
        unusedMessages = []
        #Code for receiving messages from server
        while self.socket.receivedMsgs != []:
            message = self.socket.receivedMsgs.pop(0)
            if message[:10] == "!TIMELEFT:":
                timeLeft = message[10:]
                #Updates timer on screen
                self.__UpdateTextObject(timeLeft)
                if timeLeft == 0:
                    self.timerFinished = True
            #Other player's text
            elif message[:17] == "!OTHERPLAYERTEXT:":
                text = message[17:]
                self.__opponentTextBox.SetText(text)
            #Time has run out, client has to send text
            elif message == "!GAMECOMPLETE":
                self.socket.msgsToSend.append(f"!FINALTEXT:{self.__textBox.text}")
                self.timerFinished = True
            #Server received both player's final text and game has finished
            #Emphasis on the D in completed, not the same as complete as it is for server asking for player's final text
            elif message == "!GAMECOMPLETED":
                self.gameOver = True
            else:
                unusedMessages.append(message)

        for message in unusedMessages:
            self.socket.receivedMsgs.append(message)

    #Updates text and location to be centred
    def __UpdateTextObject(self, newText):
        textSize = self.__font.size(newText)
        textLocation = (int((self._resolution[0] * 1920 - textSize[0]) / 2), int((self._resolution[1] * 1080 - textSize[1]) / 2))
        self.__textObject.location = textLocation
        self.__textObject.SetText(newText)

    def _HandleInputs(self):
        #Inputs can be handled directly in this, as there is no need to keep certain inputs to deal with in child classes
        for event in pygame.event.get():
            #If the player quit
            if event.type == pygame.QUIT:
                self.userQuit = True

            #If player clicks
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mousePos = pygame.mouse.get_pos()
                if self.__textBox.CheckForCollisionWithMouse(mousePos):
                    self.__textBox.SetActive()
                else:
                    self.__textBox.SetInactive()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self._backspace = True
                    self._timeSinceLastBackspace = -200
                    if self.__textBox.isActive:
                        self.__textBox.RemoveLetter(self._ctrl)
                elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self._ctrl = True
                else:
                    if self.__textBox.isActive and (event.unicode.isalpha() or event.unicode == " " or event.unicode == "-"):
                        self.__textBox.AddLetter(event.unicode)
                        if self.__textBox.CheckIfFinished():
                            self.socket.msgsToSend.append(f"!FINALTEXT:{self.__textBox.text}")
                        else: 
                            self.socket.msgsToSend.append(f"!TEXT:{self.__textBox.text}")

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    self._backspace = False
                elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self._ctrl = False

class PostGame(Scene):
    def __init__(self, window, resolution, winloss, winmargin, ELodiff, socket: ClientSocket = None) -> None:
        super().__init__(window, resolution, socket)
        
        colourActive = (40,40,40)
        colourInactive = (25,25,25)

        #For button objects
        self.menuButtonPressed = False
        menuButtonSize = (int(560 * self._resolution[0]), int(130 * self._resolution[1]))
        menuButtonLocation = (int((self._resolution[0] * 1920 - menuButtonSize[0]) / 2), int(800 * self._resolution[1]))
        menuButtonRect = pygame.Rect(menuButtonLocation[0], menuButtonLocation[1], menuButtonSize[0], menuButtonSize[1])
        self.__menuButton = Button(menuButtonRect, colourActive, colourInactive, (255,255,255), text="Main Menu")

        self._listOfButtonObjects = [self.__menuButton]

        #For text objects
        self.__font = pygame.font.SysFont("Calibri", int(72 * self._resolution[1]))
        winlossTextSize = self.__font.size(winloss)
        winlossTextLocation = (int((self._resolution[0] * 1920 - winlossTextSize[0]) / 2), int(140 * self._resolution[1]))

        self.__winlossText = Text(self.__font, text=winloss, location=winlossTextLocation)
        
        self.__infoFont = pygame.font.SysFont("Calibri", int(48 * self._resolution[1]))

        if winloss == "WIN":
            infoText1 = f"Win margin: {winmargin} letters"
            infoText2 = f"ELo gained: {ELodiff}"
        elif winloss == "LOSS":
            infoText1 = f"Loss margin: {winmargin} letters"
            infoText2 = f"ELo lost: {ELodiff}"
        else:
            infoText1 = f"Win margin: {winmargin} letters"
            infoText2 = f"ELo gained: {ELodiff}"

        infoText1Location = (int(250 * self._resolution[0]), int(400 * self._resolution[1]))
        infoText2Location = (int(250 * self._resolution[0]), int(480 * self._resolution[1]))
        self.__infoText1 = Text(self.__infoFont, text=infoText1, location=infoText1Location)
        self.__infoText2 = Text(self.__infoFont, text=infoText2, location=infoText2Location)

        self._listOfTextObjects = [self.__winlossText, self.__infoText1, self.__infoText2]

    def _HandleInputs(self):
        super()._HandleInputs()
        i = 0
        while i < len(self._inputHandler.inputsList):
            if self._inputHandler.inputsList[i][:6] == "CLICK:":
                clickLocation = self._inputHandler.inputsList[i][6:].split(",")
                clickLocation = (int(clickLocation[0]), int(clickLocation[1]))
                if self.__menuButton.CheckForCollision(clickLocation):
                    self.menuButtonPressed = True
                    self.__menuButton.clicked = True
                self._inputHandler.inputsList.pop(i)
            else:
                i += 1