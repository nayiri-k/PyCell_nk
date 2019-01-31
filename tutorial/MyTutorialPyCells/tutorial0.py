__version__ = "$Revision: #3 $"

class Shape:
    def __init__(self): 
        self.layer = 'metal1'
    def getLayer(self): 
        return(self.layer)
    def setLayer(self, layer): 
        self.layer = layer


class  Rectangle(Shape):
    def __init__(self, width, height): 
        Shape.__init__(self)
        self.width = width
        self.height = height
    def getWidth(self):
        return(self.width)
    def getHeight(self):
        return(self.height)
    def setWidth(self, width):
        self.width = width
    def setHeight(self, height):
        self.height = height
    def Area(self):
        return(self.width * self.height)
