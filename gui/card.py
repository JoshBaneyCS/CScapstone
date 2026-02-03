import pygame
import pygame_gui
from pygame_gui.core import ObjectID

class Card:
    # ----- Globals/Constants -----
    CARD_WIDTH = 140
    CARD_HEIGHT = 215
    CARDFLIP_SIZE_DELTA = 8
    CARDFLIP_X_DELTA = 4

    def __init__(self, scene, location):
        self.front_surface: pygame.Surface = None
        self.back_surface: pygame.Surface = None
        self.flipping, self.flipped, self.front_showing = False, False, False
        self.location = location
        self.scene = scene
        self.card_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(self.location, (self.CARD_WIDTH+4, self.CARD_HEIGHT+4)),
            manager=self.scene.ui_manager,
            starting_height=0,
            container=self.scene.scene_container,
            object_id=ObjectID(class_id='@card_container'))
        self.set_back("red")
        self.image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((0,0), (self.CARD_WIDTH,self.CARD_HEIGHT)),
            image_surface= self.back_surface,
            manager=self.scene.ui_manager,
            container=self.card_container,
            object_id=ObjectID(class_id='@card'))

    def toggle_card_visibility(self):
        self.image.visible = not self.image.visible
        self.card_container.visible = not self.card_container.visible

    def set_front(self, identifier):
        card_image = self.scene.game.cardDict.get(identifier)
        self.front_surface = pygame.transform.scale(card_image, (self.CARD_WIDTH, self.CARD_HEIGHT))

    def set_back(self, color):
        back_image = self.scene.game.backingDict.get(color)
        self.back_surface = pygame.transform.scale(back_image, (self.CARD_WIDTH, self.CARD_HEIGHT))

    def change_card_image(self, card_surface, size_change, position_change):
        new_x = self.image.relative_rect.x + position_change
        new_location = (new_x, 0)
        new_width = self.image.relative_rect.width + size_change
        new_size = (new_width, self.CARD_HEIGHT)
        pygame.transform.scale(self.back_surface, (new_width, self.CARD_HEIGHT))
        self.image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(new_location, new_size),
            image_surface=card_surface,
            manager=self.scene.ui_manager,
            container=self.card_container,
            object_id=ObjectID(class_id='@card'))

    def flip_card(self):
        self.image.kill()
        if not self.flipped:
            if not self.front_showing:
                self.change_card_image(self.back_surface, -self.CARDFLIP_SIZE_DELTA, self.CARDFLIP_X_DELTA)
                if self.image.relative_rect.width <= self.CARDFLIP_SIZE_DELTA:
                    self.front_showing = True
            else:
                self.change_card_image(self.front_surface, self.CARDFLIP_SIZE_DELTA, -self.CARDFLIP_X_DELTA)
                if self.image.relative_rect.width >= self.CARD_WIDTH:
                    self.flipped, self.flipping = True, False
        else:
            if self.front_showing:
                self.change_card_image(self.front_surface, -self.CARDFLIP_SIZE_DELTA, self.CARDFLIP_X_DELTA)
                if self.image.relative_rect.width <= self.CARDFLIP_SIZE_DELTA:
                    self.front_showing = False
            else:
                self.change_card_image(self.back_surface, self.CARDFLIP_SIZE_DELTA, -self.CARDFLIP_X_DELTA)
                if self.image.relative_rect.width >= self.CARD_WIDTH:
                    self.flipped, self.flipping = False, False