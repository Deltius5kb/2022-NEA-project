class Queue:
    def __init__(self) -> None:
        self.__list = []

    def Enqueue(self, itemToAdd):
        self.__list.append(itemToAdd)
    
    def Dequeue(self):
        return self.__list.pop(0)

    def GetLength(self):
        return len(self.__list)