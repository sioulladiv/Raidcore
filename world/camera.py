import pygame
class Camera:
    def __init__(self, width, height, zoom=1.0):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = zoom
        self.ratio = 15
    
    def update(self, target):
        target_center_x = target.x + (target.width / 2)
        target_center_y = target.y + (target.height / 2)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        real_mouse_x = (mouse_x - self.offset_x) / self.zoom
        real_mouse_y = (mouse_y - self.offset_y) / self.zoom 
        focus_x = ( self.ratio * target_center_x + real_mouse_x) / ( self.ratio+1)
        focus_y = ( self.ratio * target_center_y + real_mouse_y) /  (self.ratio+1)
        self.offset_x = self.width // 2 - int(focus_x * self.zoom)
        self.offset_y = self.height // 2 - int(focus_y * self.zoom)
    
    def apply_rect(self, rect):
        return pygame.Rect(
            int(rect.x * self.zoom) + self.offset_x,
            int(rect.y * self.zoom) + self.offset_y,
            int(rect.width * self.zoom),
            int(rect.height * self.zoom)
        )
        
    def apply_zoom(self, value):
        return int(value * self.zoom)
