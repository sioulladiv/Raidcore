import pygame

class ExperienceBar:
    def __init__(self, x, y, width, height, displaySize):
        self.displaySize = displaySize
        self.x = x
        self.y = y
        self.heart_width = 325 * self.displaySize
        self.heart_height = 100 * self.displaySize
        self.experience = 100
        self.previous_experience = 100

        # Load frames sprite_healthbar00 → sprite_healthbar10
        self.frames = []
        for i in range(11):  
            img = pygame.image.load(f"./Dungeon/frames/sprite_experience{i:02}.png")
            img = pygame.transform.scale(img, (self.heart_width, self.heart_height))
            self.frames.append(img)

        # Animation control
        self.frame_index = 0
        self.animation_speed = 100  
        self.animation_timer = 0

    def update(self, experience):
        if experience != self.experience:
            self.previous_experience = self.experience
            self.experience = max(0, min(100, experience))
            print(f"Experience updated to: {self.experience}")

    def update_animation(self, dt):
        """Advance animation timer"""
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self, screen):
        """Pick correct frame based on experience (0=full → 10=empty)"""
        frame_index = int((100 - self.experience) / 10)
        frame_index = max(0, min(10, frame_index))

        screen.blit(self.frames[frame_index], (self.x, self.y))