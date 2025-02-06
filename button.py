import kivy
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image

class LitoButton(ButtonBehavior, Image):
    
    def __init__(self, **kwargs):
        super(LitoButton, self).__init__(**kwargs)
        self.keep_ratio = True
        self.allow_stretch = True

    #Ajusta la imagen al widget
    def fit_container(self):
        texture = self.texture
        containerRatio = self.size[0] / self.size[1]
        textureRatio = texture.width / texture.height

        if containerRatio < textureRatio:
            newWidth = int(texture.height*containerRatio)
            newHeight = texture.height
            self.texture = texture.get_region(int((texture.width - newWidth)/2), 0, newWidth, newHeight)
        else:
            newWidth = texture.width
            newHeight = int(texture.width/containerRatio)
            self.texture = texture.get_region(0, int((texture.height - newHeight)/2), newWidth, newHeight)