import sqlite3, random
from PasswordHandling import CheckPW, GenHash
from Player import Player

#An object that will be able to handle all the operations needed related to the database
class DatabaseHandler:
    def __init__(self):
        #Connects to database 
        self.__connection = None
        self.__cursor = None
        self.Open()

        #Creates the tables needed if they do not exist
        command = """
        CREATE TABLE IF NOT EXISTS
        Users(
            Username TEXT PRIMARY KEY,
            Password BLOB, 
            WordsTyped INTEGER, 
            TimePlayed INTEGER, 
            Elo INTEGER, 
            HighestElo INTEGER, 
            GamesWon INTEGER, 
            GamesPlayed INTEGER, 
            LongestStreak INTEGER, 
            LargestWinMargin FLOAT, 
            LettersTyped INTEGER,
            LettersTypedCorrectly INTEGER,
            SumOfOpponentsELo INTEGER,
            CurrentWinstreak INTEGER
            )"""
        self.__cursor.execute(command)
        self.Close()

    def Close(self):
        self.__connection.commit()
        self.__connection.close()

    def Open(self):
        self.__connection = sqlite3.connect("db.db")
        self.__cursor = self.__connection.cursor()

    def LoadUser(self, player : Player):
        self.Open()
        params = (player.username,)
        command = """
        SELECT * FROM Users
        WHERE Username = (?)
        """
        self.__cursor.execute(command, params)
        data = self.__cursor.fetchall()[0]
        player.wordsTyped = int(data[2])
        player.timePlayed = int(data[3])
        player.Elo = int(data[4])
        player.highestElo = int(data[5])
        player.gamesWon = int(data[6])
        player.gamesPlayed = int(data[7])
        player.longestStreak = int(data[8])
        player.largestWinMargin = float(data[9])
        player.lettersTyped = int(data[10])
        player.lettersTypedCorrectly = int(data[11])
        player.sumOfOpponentsElo = int(data[12])
        player.currentWinstreak = int(data[13])
        self.Close()
        return data

    def SaveUser(self, player : Player):
        self.Open()

        wordsTyped = player.wordsTyped
        timePlayed = player.timePlayed
        Elo = player.Elo
        highestElo = player.highestElo
        gamesWon = player.gamesWon
        gamesPlayed = player.gamesPlayed
        longestStreak = player.longestStreak
        largestWinMargin = player.largestWinMargin
        lettersTyped = player.lettersTyped
        lettersTypedCorrectly = player.lettersTypedCorrectly
        sumOfOpponentsElo = player.sumOfOpponentsElo
        currentWinstreak = player.currentWinstreak

        params = (wordsTyped, timePlayed, Elo, highestElo, gamesWon, gamesPlayed, longestStreak, largestWinMargin, lettersTyped, lettersTypedCorrectly, sumOfOpponentsElo, currentWinstreak, player.username)
        command = """
        UPDATE Users
        SET WordsTyped = (?), 
            TimePlayed = (?), 
            Elo = (?), 
            HighestElo = (?), 
            GamesWon = (?), 
            GamesPlayed = (?), 
            LongestStreak = (?), 
            LargestWinMargin = (?), 
            LettersTyped = (?),
            LettersTypedCorrectly = (?),
            SumOfOpponentsELo = (?),
            CurrentWinstreak = (?)
        WHERE Username = (?)
        """
        self.__cursor.execute(command, params)

        self.Close()

    def CreateNewUser(self, username, password):
        self.Open()

        password = GenHash(password)
        wordsTyped = 0
        timePlayed = 0
        Elo = 1000
        highestElo = 1000
        gamesWon = 0
        gamesPlayed = 0
        longestStreak = 0
        largestWinMargin = 0
        lettersTyped = 0
        lettersTypedCorrectly = 0
        sumOfOpponentsElo = 0
        currentWinstreak = 0

        params = (str(username), password, wordsTyped, timePlayed, Elo, highestElo, gamesWon, gamesPlayed, longestStreak, largestWinMargin, lettersTyped, lettersTypedCorrectly, sumOfOpponentsElo, currentWinstreak)
        command = """
        INSERT INTO Users
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        self.__cursor.execute(command, params)
        
        self.Close()

    #!Used for testing
    def CreateRandomUser(self, username, password):
        self.Open()

        password = GenHash(password)
        wordsTyped = random.randint(0,1000000)
        timePlayed = random.randint(0,999999999)
        Elo = random.randint(500, 4000)
        highestElo = random.randint(Elo, Elo + 200)
        gamesPlayed = random.randint(0, 100000)
        gamesWon = random.randint(0, gamesPlayed)
        longestStreak = random.randint(0, gamesWon)
        largestWinMargin = random.randint(0, 100)
        lettersTyped = random.randint(0, 99999999999999)
        lettersTypedCorrectly = random.randint(0, lettersTyped)
        sumOfOpponentsELo = random.randint(0, 9999999999999999)
        currentWinstreak = random.randint(0, longestStreak)

        params = (username, password, wordsTyped, timePlayed, Elo, highestElo, gamesWon, gamesPlayed, longestStreak, largestWinMargin, lettersTyped, lettersTypedCorrectly, sumOfOpponentsELo, currentWinstreak)
        command = """
        INSERT INTO Users
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        self.__cursor.execute(command, params)

        self.Close()

    def CheckIfUsernameInDB(self, username):
        self.Open()

        params = (username,)
        command = """SELECT * FROM Users WHERE Username = ?"""

        self.__cursor.execute(command, params)
        fetchResults = self.__cursor.fetchall()

        self.Close()

        if fetchResults == []:
            return False

        else:
            return True

    def CheckPassword(self, username, password):
        self.Open()

        params = (username,)
        command = """
        SELECT Password FROM Users 
        WHERE Username = (?)
        """
        self.__cursor.execute(command, params)
        fetchResult = self.__cursor.fetchall()
        correctPasswordHash = fetchResult[0][0]

        self.Close()

        #Uses bcrypt library to check password against hash
        return CheckPW(password, correctPasswordHash)


# # player = Player(None, None)
# # player.username = "Username0"

# # dbHandler.LoadUser(player)
# dbHandler = DatabaseHandler()

# player1 = Player(None, None)
# player1.username = "300"
# player1.Elo = 300
# player2 = Player(None, None)
# player2.username = "900"
# player2.Elo = 900

# dbHandler.CreateNewUser("900", "900")

# dbHandler.SaveUser(player1)
# dbHandler.SaveUser(player2)
