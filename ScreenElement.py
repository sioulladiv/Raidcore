import pygame  
class healthBar:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.life = 100
        self.previous_life = 100
        self.frames = []
        for i in range(1, 14):
            img = pygame.image.load(f"./Dungeon/ScreenElement/sprite_heart{'0' + str(i) if i < 10 else str(i)}.png")
            img = pygame.transform.scale(img, (width, height))
            self.frames.append(img)
        
       
        self.heart_states = [0, 0, 0, 0, 0]  
        self.target_states = [0, 0, 0, 0, 0]  
        self.animation_speed = 0.2  
        self.animation_timer = 0
        
    def update(self, life):
        if life != self.previous_life:
            self.previous_life = self.life
            self.life = life
            
            health_per_heart = 100 / 5
            for i in range(5):
                remaining_health_percent = max(0, min(100, self.life - (i * health_per_heart)))
                
                if remaining_health_percent >= health_per_heart:
                    self.target_states[i] = 0
                elif remaining_health_percent <= 0:
                    self.target_states[i] = len(self.frames) - 1
                else:
                    percentage_of_heart = remaining_health_percent / health_per_heart
                    self.target_states[i] = int((1 - percentage_of_heart) * (len(self.frames) - 1))
        
    def damage(self, damage):
        self.update(self.life - damage)
        
    def update_animation(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            
            for i in range(5):
                if self.heart_states[i] < self.target_states[i]:
                    self.heart_states[i] += 1
                elif self.heart_states[i] > self.target_states[i]:
                    self.heart_states[i] -= 1
    
    def draw(self, screen):
        heart_spacing = 10 
        
        for i in range(5):
            heart_x = self.x + i * (self.width + heart_spacing)
            
            frame_index = min(len(self.frames) - 1, max(0, self.heart_states[i]))
            screen.blit(self.frames[frame_index], (heart_x, self.y))
