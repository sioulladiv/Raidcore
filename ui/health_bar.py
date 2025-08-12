import pygame
class HealthBar:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.heart_width = height  
        self.heart_height = height
        self.life = 100
        self.previous_life = 100
        self.frames = []
        
        heart_images = [
            "./Dungeon/frames/ui_heart_full.png",
            "./Dungeon/frames/ui_heart_half.png", 
            "./Dungeon/frames/ui_heart_empty.png"
        ]
        for img_path in heart_images:
            img = pygame.image.load(img_path)
            img = pygame.transform.scale(img, (self.heart_width, self.heart_height))
            self.frames.append(img)
        
        self.heart_states = [0, 0, 0, 0, 0]  
        self.target_states = [0, 0, 0, 0, 0]  
        self.animation_speed = 200  
        self.animation_timer = 0
        self.calculate_heart_states()
        
    def calculate_heart_states(self):
        """Calculate target heart states based on current life"""
        health_per_heart = 20  
        
        for i in range(5):
            heart_health_start = i * health_per_heart
            heart_health_end = (i + 1) * health_per_heart
            
            if self.life >= heart_health_end:
                self.target_states[i] = 0 
            elif self.life <= heart_health_start:
                self.target_states[i] = 2 
            else:
                remaining_in_heart = self.life - heart_health_start
                if remaining_in_heart >= health_per_heart // 2:
                    self.target_states[i] = 0  
                else:
                    self.target_states[i] = 1  
        
        self.heart_states = self.target_states.copy()
        
    def update(self, life):
        if life != self.life:
            self.previous_life = self.life
            self.life = max(0, min(100, life)) 
            self.calculate_heart_states()
            print(f"Health updated to: {self.life}, Heart states: {self.heart_states}")
        
    def damage(self, damage_amount):
        new_life = self.life - damage_amount
        print(f"Taking {damage_amount} damage. Health: {self.life} -> {new_life}")
        self.update(new_life)
        
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
        heart_spacing = 5  
        
        for i in range(5):
            heart_x = self.x + i * (self.heart_width + heart_spacing)
            
            frame_index = min(len(self.frames) - 1, max(0, self.heart_states[i]))
            screen.blit(self.frames[frame_index], (heart_x, self.y))
