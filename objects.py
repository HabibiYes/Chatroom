class Message():
    def __init__(self, text:str, color:tuple[float, float, float] = (255, 255, 255)):
        self.text = text
        self.color = color