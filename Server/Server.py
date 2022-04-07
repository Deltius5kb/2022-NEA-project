import socket, pygame, pickle
from Game import Game
from Player import Player
from Database import DatabaseHandler
from SearchingAlgorithms import LinearSearch

class Server:
    def __init__(self):
        self.HEADER = 8
        self.PORT = 5000
        self.SERVER = socket.gethostbyname(socket.gethostname()) #Gets the local IP address
        self.ADDRESS = (self.SERVER, self.PORT) #Makes a tuple for the address
        self.FORMAT = 'utf-8'

        self.running = True
        self.players = []
        self.playersInMatchmaking = []
        self.playersInGame = []

        self.currentGames = []
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET is for ipv4. SOCK_STREAM is for TCP, SOCK_DGRAM is UDP
        self.server.bind(self.ADDRESS)
        self.dbHandler = DatabaseHandler()
        print("[SERVER STARTED]")
        self.__clock = pygame.time.Clock()

    def Run(self):
        self.server.listen() #Looks for connections
        while self.running:
            self.__clock.tick()

            #Update how long a player has been in queue
            for player in self.playersInMatchmaking:
                player.timeWaited += self.__clock.get_time()
                #If player has waited 20 seconds in queue, their mmr range will increase
                #Player's mmr range increases by 50% every 20 seconds
                if player.timeWaited >= 20000:
                    player.matchmakingRange *= 1.5 ** (player.timeWaited // 20000)

            self.CheckForNewPlayers()
            self.PrintPlayers()

            #Creates game if there is more than 1 player in queue
            playersGameNotFound = []
            while len(self.playersInMatchmaking) >= 2:
                #Loop through each player
                #Check if any other players are within their elo range
                player1 : Player = self.playersInMatchmaking.pop(0)
                gameMade = False
                for i in range(len(self.playersInMatchmaking)):
                    if player1.Elo - player1.matchmakingRange < self.playersInMatchmaking[i].Elo < player1.Elo + player1.matchmakingRange:
                        player2 = self.playersInMatchmaking.pop(i)
                        player1.msgsToSend.Enqueue("!GAMEFOUND")
                        player2.msgsToSend.Enqueue("!GAMEFOUND")
                        self.playersInGame.append(player1)
                        self.playersInGame.append(player2)
                        self.currentGames.append(Game(player1, player2))
                        gameMade = True
                        break
                if not gameMade:
                    playersGameNotFound.append(player1)

            for player in playersGameNotFound:
                self.playersInMatchmaking.append(player)

            #Checks if any players in game have disconnected
            i = 0
            while i < len(self.playersInGame):
                if not self.playersInGame[i].connected:
                    self.playersInGame.pop(i)
                else:
                    i += 1

            #Handling messages
            self.GetMsgs(self.players)
            self.HandleMessagesForPlayersNotInQueue()
            self.SendMessageToPlayers(self.players)

            self.GetMsgs(self.playersInMatchmaking)
            self.HandleMessagesForPlayersInQueue()
            self.SendMessageToPlayers(self.playersInMatchmaking)

            self.GetMsgs(self.playersInGame)
            self.CheckIfPlayerFinishedGame()
            self.SendMessageToPlayers(self.playersInGame)
        self.dbHandler.Close()

    #Made to be used in a seperate thread
    #Checks each player for a message being sent
    #If a message is received it is appended to the list player.msgsReceived
    def GetMsgs(self, players):
        for player in players:
            player.connection.setblocking(False)
            try:
                msgLen = int(player.connection.recv(self.HEADER).decode(self.FORMAT)) #Waits for message with length 8 bytes to be received from the client and then decodes it 
                player.connection.setblocking(True)
                if msgLen > 0:  #First message will always be empty
                    msg = player.connection.recv(msgLen).decode(self.FORMAT) #Waits for a message with length msgLen to be received
                    player.msgsReceived.Enqueue(msg)       
                    print(f"Message Received:{msg}")
                player.connection.setblocking(True)
            except socket.error:
                player.connection.setblocking(True)

    #Made to be used in a seperate thread
    #Checks each player for a message that needs to be sent from player.msgsToSend list
    #If a message needs to be sent it will send it and remove it from the list
    def SendMessageToPlayers(self, listOfPlayers):
        #Checks queue for each player to send messages that need to be sent.
        for player in listOfPlayers:
            player.connection.setblocking(False)
            while player.msgsToSend.GetLength() != 0:
                message = player.msgsToSend.Dequeue()
                try:
                    conn = player.connection
                    try:
                        encMessage = message.encode(self.FORMAT) #encodes msg with utf-8
                        msgLen = len(encMessage)
                        msgLen = str(msgLen).encode(self.FORMAT) 
                        msgLen += b' ' * (self.HEADER - len(msgLen)) #makes the message length be 8 bytes long so the server recognises it
                        #b' ' means the byte representation of a space
                        conn.send(msgLen)
                        conn.send(encMessage)
                        print(f"Message sent:{message}")
                    #There will be an error if the message is a pickle as you cant encode a pickle
                    except:
                        msgLen = len(message)
                        msgLen = str(msgLen).encode(self.FORMAT) 
                        msgLen += b' ' * (self.HEADER - len(msgLen)) #makes the message length be 8 bytes long so the server recognises it
                        #b' ' means the byte representation of a space
                        conn.send(msgLen)
                        conn.send(message)    
                except socket.error:
                    player.msgsToSend.Enqueue(message)
            player.connection.setblocking(True)

    #Function to be used in the run function to look for new players and not block everything else that needs to happen
    #Ran in parallel by using threading module
    def CheckForNewPlayers(self):
        self.server.setblocking(False)
        try:
            conn, addr = self.server.accept() #When connection occurs
            thisPlayer = Player(addr, conn)
            self.players.append(thisPlayer)
        except:
            pass
        self.server.setblocking(True)

    def PrintPlayers(self):
        print(f"Players:{len(self.players)}, in matchmaking:{len(self.playersInMatchmaking)}, in game:{len(self.playersInGame)}", end="\r")

    def HandleMessagesForPlayersNotInQueue(self):
        playersQuit = []
        for player in self.players:
            while player.msgsReceived.GetLength() != 0:
                message = player.msgsReceived.Dequeue()
                if message == "!DISCONNECT":
                    playersQuit.append(player)
                
                elif player.loggedIn and message == "!QUEUE":
                    playersQuit.append(player)
                    self.playersInMatchmaking.append(player)
                    player.timeWaited = 0

                elif message[:7] == "!LOGIN:":
                    if not player.loggedIn:
                        details = message[7:].split(",")
                        username = details[0]
                        password = details[1]

                        #Checks password and sends message to user to confirm if they are signed in or not
                        if self.dbHandler.CheckIfUsernameInDB(username):
                            if self.dbHandler.CheckPassword(username, password):
                                player.loggedIn = True
                                player.username = username
                                self.dbHandler.LoadUser(player)
                                player.msgsToSend.Enqueue("!PASSWORDCORRECT")
                            else:
                                player.msgsToSend.Enqueue("!PASSWORDINCORRECT")
                        else:
                            player.msgsToSend.Enqueue("!USERNAMENOTFOUND")
                    else:
                        player.msgsToSend.Enqueue("!ALREADYLOGGEDIN")
                elif message[:10] == "!REGISTER:":
                    details = message[10:].split(",")
                    player.username = details[0]
                    try:
                        self.dbHandler.CreateNewUser(details[0], details[1])
                        player.username = details[0]
                        player.loggedIn = True
                        data = self.dbHandler.LoadUser(player)
                        player.msgsToSend.Enqueue("!REGISTEREDSUCCESFULLY")
                        player.msgsTosend.Enqueue(pickle.dumps(data))
                    except:
                        player.msgsToSend.Enqueue("!ANERROROCCURRED")
                elif message == "!STATISTICS":
                    data = self.dbHandler.LoadUser(player)
                    player.msgsToSend.Enqueue(pickle.dumps(data))
                    print("Pickle sent")
                            
        #Removes players who quit from the list of players
        for player in playersQuit:
            listIndex = LinearSearch(player, self.players)
            #Linear search returns None if item is not in list
            if listIndex is not None:
                self.players.pop(listIndex)

    def HandleMessagesForPlayersInQueue(self):
        playersQuit = []
        for player in self.playersInMatchmaking:
            while player.msgsReceived.GetLength() != 0:
                message = player.msgsReceived.Dequeue()
                print(message)
                if message == "!DISCONNECT":
                    playersQuit.append(player)
                elif message == "!DEQUEUE":
                    playersQuit.append(player)
                    self.players.append(player)
    
        #Removes players who quit from the list of players
        for player in playersQuit:
            listIndex = LinearSearch(player, self.playersInMatchmaking)
            #Linear search returns None if item is not in list
            if listIndex is not None:
                self.playersInMatchmaking.pop(listIndex)

    def CheckIfPlayerFinishedGame(self):
        playersQuit = []
        for player in self.playersInGame:
            if player.gameFinished:
                playersQuit.append(player)
                self.players.append(player)
            elif player.playerQuit:
                playersQuit.append(player)
        
        #Removes players who quit from the list of players
        for player in playersQuit:
            listIndex = LinearSearch(player, self.playersInGame)
            #Linear search returns None if item is not in list
            if listIndex is not None:
                self.playersInGame.pop(listIndex)

server = Server()
server.Run()
