class Monster:
    def __init__(self, x, y, type, height=70, width=70, frames: list):
        self.x = x
        self.y = y
        self.type = type
        self.height = height
        self.width = width
        self.frames = frames
    
    def draw(self, surface, camera=None):
        if camera:
            draw_x = self.x * camera.zoom + camera.offset_x
            draw_y = self.y * camera.zoom + camera.offset_y
            scaled_image = pygame.transform.scale(self.frames[0], (int(self.width * camera.zoom), int(self.height * camera.zoom)))
            surface.blit(scaled_image, (draw_x, draw_y))
        else:
            surface.blit(self.frames[0], (self.x, self.y))