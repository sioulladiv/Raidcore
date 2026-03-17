from __future__ import annotations

import pygame, sys
from pytmx.util_pygame import load_pygame
import math
from ui.menu import BunkerMenu
from entities.enemy import Enemy
from entities.player import Player
from entities.particle import Particle
from entities.dust_particle import DustParticleSystem
from world.tilemap import TiledMap, Tile
from world.lighting import Lighting
from world.camera import Camera
from world.chest import Chest
from weapons.gun import Gun
from weapons.bullet import Bullet
from ui.health_bar import HealthBar
from ui.experience import ExperienceBar
from ui.game_over import GameOverScreen
from ui.music import Music
from ui.level_logic import level2
from world.lever import Lever
from utils.culling import FrustumCuller
from config.game_settings import game_settings
from weapons.knife import Knife
from ui.inventory import inventory

import json
import os
import random

with open("data/enemy_data.json", "r") as f:
    enemy_data = json.load(f)

with open("data/level_data.json", "r") as f:
    level_data = json.load(f)

tile_size = 16


class Game:
    """
    Top level game object that owns all methods and runs the main loop.
    It intialises pygame and creates the display window
    loads tiled maps and spawns enemies and initialises UI elements
    runs the main while loop: event processing, updating all entities, renderingeverything to the screen, and managing level transitions
    """
    def __init__(self, screen_width: int, screen_height: int, displaySize: float, zoom_level: float = 1.0) -> None:
        """
        Initialise all game methods and loads the starting level.

        Args:
            screen_width: width of screen in pixels.
            screen_height: height of screen in pixels.
            displaySize: Scaling ratio(screen_width / 2560).
            zoom_level: Initial camera zoom factor(default 1.0).
        """
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.displaySize = displaySize
        self.zoom_level = zoom_level
        self.FPS = game_settings.get_fps_cap()
        self.inventory = inventory()
        
        #set initial weapons and we will add them later to the inventory
        #i will some more definition as I create more items
        self.gun = Gun(0, 0, "pistol", self.displaySize)
        self.knife= Knife(0, 0, "knife", self.displaySize)

        #added items to inventory

        self.inventory.add_item(self.gun, 0)
        self.inventory.add_item(self.knife, 1)

        # starting weapon index, index used to track weapon used and switch between them
        self.current_weapon_index = 0
        #fetch current weapon from inventory class
        self.current_weapon = self.inventory[self.current_weapon_index]['item']

        # vsync which basically sync framrate with monitor retfresh rate to avoid "tearing"
        try:
            if game_settings.get_vsync():
                self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), vsync=1)
            else:
                self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        except TypeError:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        
        #start on level 0 and set sound files and xp events list
        self.level = 0
        self.orb_sounds = []
        self.xp_sound_events = []  

        #set font for FPS display on top right
        self.fps_text_font = pygame.font.SysFont("Verdana", 20)
        
        
        # Load all sound files from the Orbs folder, copies of original with small changes in pitch like in minecraft
        orbs_folder ="Assets/Sounds/Orbs"

        if os.path.exists(orbs_folder):
            for filename in os.listdir(orbs_folder):

                if filename.lower().endswith(('.mp3','.ogg')): # check the different audio types as I am using different formats.
                    try:
                        sound_path = os.path.join(orbs_folder,filename)
                        sound = pygame.mixer.Sound(sound_path)
                        self.orb_sounds.append(sound)
                        #print(f"Loaded orb sound: {str(filename)}")
                        #print error if sound doesn't load
                    except pygame.error as error:
                        print( f"Failed to load {filename}: {error}")
        #if plings ounds array is empty, load default sound for orb, in case folder is missing
        if not self.orb_sounds:
            try:
                self.orb_sounds.append(pygame.mixer.Sound("Assets/Sounds/orb.mp3"))
                print("Loaded default orb sound: orb.mp3")
            except pygame.error as e:
                print(f"Failed to load default orb sound: {e}")
        self.bullets = []

        print(f"Total orb sounds loaded: {len(self.orb_sounds)}")
        pygame.display.set_caption("Dungeon Game")


        # load the initial map for the first level
        self.game_map = TiledMap(f"Tiled/level{self.level}.tmx")
        self.game_map.set_current_level(self.level)
        self.path_grid_cach = None  

        #set camera default
        self.camera = Camera(self.screen_width, self.screen_height, zoom_level)


        #initialise player and other entities and utils for the game
        self.player = Player(100, 100, 32, 32, (0, 255, 0), self.displaySize)
        self.enemies = []
        self.music = Music()
        self.light = Lighting(200)

        
        """ Initialise elements on screen like health bar and experience"""

        self.health_bar = HealthBar(int(0.5*screen_width) - 0.5*int(300*self.displaySize) ,int(screen_height-150*self.displaySize) ,
                        int(8* self.displaySize), int(3*self.displaySize), self.displaySize)

        #set bar to bottom right corner
        bar_width = int(30 * self.displaySize)

        bar_height = int(150 * self.displaySize)
        bar_x = self.screen_width - bar_width - int(100 * self.displaySize) #100 pixels on right side

        bar_y = self.screen_height - bar_height - int(100 * self.displaySize)  #100 pixels from bottom edge



        #set experience bar
        self.experience_bar = ExperienceBar(bar_x, bar_y, bar_width, bar_height, self.displaySize)
        
        # set functionality variables for the game
        self.player_damage_cooldown = 0 #cooldown timer to stop losing health too fast
        self.player_damage_cooldown_duration = 60  # invicibility duration in frames to avoid instantly dying ;:)
        self.xp = 0

        self.menu = BunkerMenu(self.screen_width // 2 - 150, self.screen_height // 2 - 150, self.displaySize)
        
        self.transition_timer = 0

        self.lightlevel = level_data["level1"]["lighting"]

        self.chest_sounds = {
            "open": "Assets/Sounds/chest_open.mp3",

            "close": "Assets/Sounds/chest_close.mp3"
        }
        self.player_sounds = {

            "hurt" : "Assets/Sounds/Player/player_hurt.mp3",

            "death" : "Assets/Sounds/Player/player_death.mp3"
        }

        self.lever_sound = pygame.mixer.Sound("Assets/Sounds/Pressure_plate.mp3")
        
        self.spike_retract = pygame.mixer.Sound("Assets/Sounds/spikes_retract.mp3")

        # set chest sounds for future use
        self.chest_sounds["open"] = pygame.mixer.Sound(self.chest_sounds["open"])
        
        self.chest_sounds["close"] = pygame.mixer.Sound(self.chest_sounds["close"])
        
        self.player_sounds["hurt"] = pygame.mixer.Sound(self.player_sounds["hurt"])
        self.player_sounds["death"] = pygame.mixer.Sound(self.player_sounds["death"])

        # set fade overlay variables for level transition effect
        self.fade_overlay_alpha = 0
        self.fade_overlay_duration = 1000  
        self.fade_overlay_timer = 0
        self.fade_overlay_active = False

        #dictionary to track individual level states.
        self.levers = {1: False, 2: False, 3: False, 4: False}

        #load images for press E prompt
        self.press_e_image = pygame.image.load("Assets/press_e.png")
        self.press_e_image = pygame.transform.scale(self.press_e_image, (240 * self.displaySize, 192 * self.displaySize))  
        self.show_press_e = False
        self.path_grid = self.make_path_grid()

        pygame.font.init()
        self.xp_font = pygame.font.Font(None, 36)

        #load all animations from letter_animation folder for letter opening animation on level 1 :)
        self.letter_frames = []
        letter_folder = "Assets/letter_animation"
        if os.path.exists(letter_folder):
            frame_files = sorted([f for f in os.listdir(letter_folder) if f.endswith('.png')])
            for frame_file in frame_files:
                # join folder path with file to get full path
                frame_path =os.path.join(letter_folder, frame_file)
                frame_image =pygame.image.load(frame_path)
                
                scale = min(self.screen_width/ 240, self.screen_height /180)* 0.8

                #get proportional scaling for letter animation relative to screen size
                frame_image = pygame.transform.scale(frame_image, (int(240 * scale), int(180 * scale)))
                self.letter_frames.append(frame_image)

        #settings all variables to properly time the animation
        self.show_letter = False
        self.letter_frame_index = 0
        self.letter_animation_timer = 0
        self.letter_animation_speed = 100  
        self.letter_anmation_complete = False

        #set position to the centre of screen for the beautiful letter animation
        if self.letter_frames:
            
            self.letter_x = (self.screen_width -self.letter_frames[0].get_width()) // 2
            self.letter_y = (self.screen_height- self.letter_frames[0].get_height()) // 2
        else:
            self.letter_x = 100
            self.letter_y = 100

        #instantiate game over screen
        self.game_over_screen = GameOverScreen(self.screen_width, self.screen_height)
        self.game_over = False
        self.death_sound_played = False
        self.spikes_deactivated_sound_played = False  

        #fetch player starting position from level data json file
        self.player.x , self.player.y = level_data[f"level{self.level}"]["start_pos"]
        
    def run(self) -> None:
        """
       run main loop until player quits
        """
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Dungeon Run")

        # settings frustrum culler for oprimisation especially for level 3 where there are many ennemies and 10000+ tiles (layering) to render at once
        # basically it only render tiles that are visible within the camera's view instead of rendering the whole surface every frame
        culler = FrustumCuller(self.screen_width, self.screen_height)

        #set healthbar and experience bar to current ones for easy access for future use
        self.current_health_bar = self.health_bar
        self.current_experience_bar = self.experience_bar
        health_bar = self.current_health_bar
        experience_bar = self.current_experience_bar
        health_bar.update(100)  
        experience_bar.update(0)

        #set lighting to 350 radius for better visibility
        #higher value = more visibile game
        light = Lighting(350)
        
        
        collision_tiles, spike_tiles = self.reload_collision_data()        
        endlevel_tiles = self.game_map.endlevel_layer("endlevel")

        #initialize weapons
        gun = self.gun
        knife =self.knife
        player_x = self.game_map.width// 2
        player_y = self.game_map.height// 2

        #set player
        self.player = Player(player_x, player_y, 16,28, (255, 0, 0),self.displaySize)

        #set enemies for the specific level
        self.loadEnemiesForLevel(self.enemies)

        zoom_level = self.displaySize * 13
        camera = Camera(self.screen_width, self.screen_height, zoom_level)

        #set clock which works as a timer since game was run
        clock = pygame.time.Clock()
        #clock is updated every frame to keep track of time passed
        #so that animation and movements are consistent depsite running on slower pc
        #don't want really fast pc running game twice as fast as slower pc :(
        
        running = True
        self.particles = []
        
        # Initialize dust particle system for lighting effects
        #self explanatory but if you increase num_particles you will get more particles but it will run slower
        
        self.dust_particles = DustParticleSystem(num_particles=60, light_radius=350)
        player_center_x = self.player.x + self.player.width/ 2
        player_center_y = self.player.y+ self.player.height / 2
        self.dust_particles.initialize(player_center_x, player_center_y)
    
        # This is used to track when spikes are deactivated so that you can go through it
        # without getting killed
        self.map_needs_collision_update = False
        self.last_all_levers_pulled = False

        # get all chest info into self.chests
        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        # add each chest to the chests list
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)
        #same for levers
        lever_data = self.game_map.lever_layer("levers")
        self.lever_list = []  
        #add all levers to lever list
        for i, lever_info in enumerate(lever_data):
            lever_id = f"lever{i+1}" 
            lever = Lever(lever_info['x'], lever_info['y'], lever_info['type'], lever_id=lever_id)
            self.lever_list.append(lever)

    
        while running:
            
            self.current_weapon = self.inventory[self.current_weapon_index]['item'] #fetch current weapon from inventory
            # print(f"x: {self.player.x}, y: {self.player.y}")  # Only for debugging
            self.life = self.health_bar.life #store life in healthbar class and fetch it here
            self.experience = self.experience_bar.experience #same but for experience points

            # logic for game over for sound effects and music to terminate when player dead
            if self.life <= 0 and not self.game_over:
                self.game_over = True
                if not self.death_sound_played:
                    volume = 0.7 * game_settings.get_sfx_volume()
                    self.player_sounds["death"].set_volume(volume)
                    self.player_sounds["death"].play() #fun song
                    self.death_sound_played = True
                self.music.play_game_over_music() #get music class to play song when player dies
            
            # this controls the framerate of the game, so that it doesn't run too fast on good PCs
            dt = clock.tick(self.FPS)
            
            # damage cooldown acts as invincibility so we track how long it lasts and decrement timer
            if self.player_damage_cooldown > 0: self.player_damage_cooldown -= 1

            if not self.game_over: self.music.update(self.level)
            if isinstance(self.current_weapon, Gun):
                self.current_weapon.update(camera, self.player, dt, collision_tiles)
            elif isinstance(self.current_weapon, Knife):
                self.current_weapon.update(camera, self.player, dt, collision_tiles)
            #update weapons based on current weapon selection
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False 

                #self defined events for delayed sounds, looking for range in case... Pretty neat :)
                elif event.type >= pygame.USEREVENT + 1 and event.type <= pygame.USEREVENT + 10:
                    # Handle delayed XP pling sounds like in minecraft
                    sound_index = event.type - pygame.USEREVENT - 1
                    delayed_sound_attr = f'delayed_pling_{sound_index + 1}'
                    # play the stored pling sound when player gains xp
                    # it works by playing a random sound from the orb_sounds list and setting a delay

                    #check if sound exists defined earlier for delayed_sound_attr
                    if hasattr(self, delayed_sound_attr):
                        # Play the stored sound
                        stored_sound = getattr(self, delayed_sound_attr)
                        stored_sound.play()
                        # Clean up the stored sound for performance
                        # otherwise you get memory leaks which is not good :(
                        delattr(self, delayed_sound_attr)
                    else:
                        # In case doesn't exist, select a random pling sound
                        # a bit slower but better than nothing
                        if self.orb_sounds:
                            orbsound = random.choice(self.orb_sounds)

                            # generate random number for volume between range for cool minecraft effect
                            # yes, a lot of this game is inspired by minecraft
                            # that's because it's a great game.
                            base_volume = random.uniform(0.3, 0.8)
                            final_volume = base_volume * game_settings.get_sfx_volume()
                            orbsound.set_volume(final_volume)
                            orbsound.play()
                    
                    # Disable this timer and remove from tracking
                    #otherwise it will keep triggering every frame
                    # also better for framerate
                    pygame.time.set_timer(event.type, 0)
                    if event.type in self.xp_sound_events:
                        self.xp_sound_events.remove(event.type)

                # Handle events for game over screen
                elif self.game_over:
                    result = self.game_over_screen.handle_events([ event])
                    # restart or quit based on user input
                    if result == "restart":
                        self.restart_game()
                    elif result == "quit":
                        running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not self.game_over:
                        pause_menu = BunkerMenu(
                            self.screen_width,
                            self.screen_height,
                            self.displaySize,
                            is_pause_menu=True,
                        )
                        pause_result = pause_menu.run()
                        if pause_result == "quit":
                            running = False
                            break
                        pygame.display.set_caption("Dungeon Run")
                        continue
                    
                    #debug check if inventpry working properly
                    #if event.key == pygame.K_z:
                        #print(f"inventory items {self.inventory.items}")
                    if event.key == pygame.K_e:
                        if self.level == 1:
                            # On level 1 there is a chest, if you get close enough a letter should popup when you press e
                            # This is the logic for showing the letter and playing the minecraft chest sound
                            
                            # Handles if case where letter is already open and player presses e to close it
                            if self.show_letter:
                                #game_settings is reponsible for game settings. So we are grabbing SFX volume from there
                                volume = 0.8 * game_settings.get_sfx_volume()
                                #play minectaft chest opening sound because it sounds good
                                self.chest_sounds["close"].set_volume(volume)
                                self.chest_sounds["close"].play()
                                self.show_letter = False
                                # reset animation so animation plays again next time
                                self.letter_anmation_complete = False
                                self.letter_frame_index = 0
                                self.letter_animation_timer = 0

                            # handles case where player is near chest and presses e to open it
                            elif self.show_press_e:

                                for chest in self.chests:

                                    #check if near player
                                    if chest.is_near_player(self.player):
                                        self.show_letter = True
                                        volume = 0.8 * game_settings.get_sfx_volume()
                                        self.chest_sounds["open"].set_volume(volume)
                                        self.chest_sounds["open"].play()
                                        self.letter_frame_index = 0
                                        self.letter_animation_timer = 0
                                        self.letter_anmation_complete = False
                                        break
                        elif self.level == 2:
                            #On level 2 the E key is used to interact with levers instead of chest
                            if self.level2.all_levers_pulled:
                                break
                            else:
                                for i, lever in enumerate(self.lever_list):
                                    # check if lever is near player
                                    if lever.is_near_player(self.player) and not lever.is_pulled:
                                        if lever.pull(): 
                                            # if lever is pulled increment lever_number and update lever state dictionary
                                            lever_number = i + 1
                                            self.levers[lever_number] = True
                                            lever_id = lever.lever_id or f"lever{lever_number}"
                                            # sound logic for lever
                                            if self.level2.pull_lever(lever_id):

                                                self.game_map.update_lever_state(lever_id, True)
                                                volume = 0.6 * game_settings.get_sfx_volume()
                                                #play minecraft lever pulled sound
                                                self.lever_sound.set_volume(volume)
                                                self.lever_sound.play()  
                                                #print(f"Pulled {lever_id}")
                                        break
                    # if number keys are pressed witch to inventory slot
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                        self.current_weapon_index = event.key - pygame.K_1
                        #update inventory slot to match current weapon set directly
                        self.inventory.slot = self.current_weapon_index

                    # press b to open inventory
                    if event.key == pygame.K_b:
                        self.inventory.active = not self.inventory.active

                    # cap index so it can't be too high
                    self.current_weapon_index = min(self.current_weapon_index,len(self.inventory) -1)
                    # a bit circular but it works; set game class local variable to current weapon from inventory
                    self.current_weapon = self.inventory[self.current_weapon_index]['item']
                    if self.current_weapon:
                        print(f"Swiched to{self.current_weapon}")

                #use wheel to witch weapons in addition to number keys for smoother experience
                    
                elif event.type == pygame.MOUSEWHEEL:
                    
                    #scroll up and update inventory accordingly
                    if event.y >0:
                        self.current_weapon_index = (self.current_weapon_index - 1) % len(self.inventory)
                        print("swithcing weapon down, current weapon {}, index{}".format(self.current_weapon, self.current_weapon_index))
                    #scroll down and update inventory accordingly
                    elif event.y< 0:
                        self.current_weapon_index= (self.current_weapon_index + 1) % len(self.inventory)
                        print("swithcing weapon up, current weapon {}, index{}".format(self.current_weapon,self.current_weapon_index ))

                    #update inventory slot so update animation of selecting slot
                    self.inventory.slot = self.current_weapon_index

                    self.current_weapon =self.inventory[self.current_weapon_index]['item']
                    if self.current_weapon:
                        print(f"Switched to {self.current_weapon}")

            #update all animations for player and health bar, dt used for consistent timing in miliseconds            
            self.player.update_animation( dt)
            health_bar.update_animation(dt) 
            keys =pygame.key.get_pressed()

            if not self.show_letter and not self.game_over:
                self.player.update(keys, collision_tiles, endlevel_tiles, self, spike_tiles)
                camera.update(self.player)
                light.update(self.player, camera, self.lightlevel)
                
                # Update dust particles
                player_center_x = self.player.x + self.player.width / 2
                player_center_y = self.player.y + self.player.height / 2
                self.dust_particles.update(dt, player_center_x, player_center_y, light.radius)

                self.show_press_e = False
                
                if self.level == 1:
                    for chest in self.chests:
                        if chest.is_near_player(self.player):
                            # show the popup to press e to interact with the chest
                            self.show_press_e = True
                            break
                
                elif self.level == 2:
                    for lever in self.lever_list:
                        if lever.is_near_player(self.player) and not lever.is_pulled:
                            # same as above but for the levers
                            self.show_press_e = True
                            break

                # update enemies every frame
                for enemy in list(self.enemies):
                    # Pass appropriate weapon data based on current weapon
                    if self.current_weapon == self.gun:
                        enemy.update(keys, collision_tiles, self.player, self.enemies, self.path_grid, gun.bullets, health_bar, self.particles, self)
                    elif self.current_weapon == self.knife:
                        # For knife, pass attack info if currently attacking
                        knife_attack = knife.get_attack_rect() if not knife.can_attack else None
                        enemy.update(keys, collision_tiles, self.player, self.enemies, self.path_grid, [], health_bar, self.particles, self, knife_attack, knife.damage if not knife.can_attack else 0)
                    # Clean up dead enemies that were removed during update
                    if enemy not in self.enemies:
                        enemy.cleanup()
                    else:
                        enemy.update_animation(dt)
            # update fade overlay for just after level change.
            # increase alpha value until it reaches 255 which is fully black
            if self.fade_overlay_active:
                self.fade_overlay_timer += dt
                #progress of fade based on time passed
                progress = self.fade_overlay_timer / self.fade_overlay_duration

                # more than 1.0 which means fully loaded
                if progress >= 1.0:
                    #disable the fade
                    self.fade_overlay_active = False
                    self.fade_overlay_alpha = 0
                else:
                    # linearly inrterpolate the value of the alpha based on the progress which makes it smooth
                    self.fade_overlay_alpha =int(255 *(1 -progress))

            # update letter animation changing frame
            if self.show_letter and not self.letter_anmation_complete and len(self.letter_frames) > 0:
                #update the beautiful letter animation frame by frame
                self.letter_animation_timer += dt
                if self.letter_animation_timer >= self.letter_animation_speed:
                    self.letter_animation_timer = 0
                    self.letter_frame_index += 1 #next frame
                    if self.letter_frame_index >= len(self.letter_frames):
                        # a bit hacky but it basicialy stops frame from spilling over limit
                        # and then stops animation completely
                        self.letter_frame_index = len(self.letter_frames) - 1
                        self.letter_anmation_complete = True

            # update every particle that was spawned when an enemy was killed
            # Use list comprehension for faster performance
            #better for framerate in long run for many particles

            #basically it updates each particl and filters out dead ones
            self.particles = [p for p in self.particles if ( p.update(dt), not p.is_dead())[1]]
            
            # Calculate visible tile bounds for culling
            tile_size = self.game_map.tmx_data.tilewidth 
            visible_bounds = culler.get_visible_tile_bounds(camera, tile_size)
            
            # render map with culling directly to screen instead of using map_surface
            self.screen.fill((0, 0, 0))  
            tiles_rendered = self.game_map.render_to_screen(self.screen, camera, visible_bounds)

            # # Reset culling stats for this frame if debugging
            # if culler.debug_enabled:
            #     culler.culled_count = 0
            #     culler.total_count = 0

            
            #draw player
            self.player.draw(self.screen, camera)

            # Cull and draw enemies
            visible_enemies = culler.filter_visible_entities(self.enemies, camera, margin=100)
            for enemy in visible_enemies:
                enemy.draw(self.screen, camera)

            # Cull and draw particles
            visible_particles = []
            for particle in self.particles:
                if culler.is_point_visible(particle.x, particle.y, camera, margin=50):
                    visible_particles.append(particle)
            
            for particle in visible_particles:
                particle.draw(self.screen, camera)

            # Draw dust particles in the light (before the light overlay)
            self.dust_particles.draw(self.screen, camera)
            

            # draw weapon based on current selection
            light.draw(self.screen, camera)
            if isinstance(self.current_weapon, Gun):
                self.current_weapon.draw(self.screen, camera, self.player, dt)
            elif isinstance(self.current_weapon, Knife):
                self.current_weapon.draw(self.screen, camera, self.player, dt)
        
            # Draw UI
            health_bar.draw(self.screen, self.player, camera)
            self.experience_bar.draw(self.screen)
            self.inventory.draw(self.screen, self.player, camera)

            #draw press e prompt if near chest or lever
            if self.show_press_e and not self.show_letter:
                prompt_x = self.screen_width - (1.5* 240) * self.displaySize
                prompt_y = self.screen_height -(1.5 * 192) *self.displaySize
                self.screen.blit(self.press_e_image, (prompt_x, prompt_y))

            #draw current frame of letter animation if letter popup is active
            
            if self.show_letter and len(self.letter_frames )> 0:
                
                current_frame = self.letter_frames[ self.letter_frame_index ]
                self.screen.blit(current_frame, (self.letter_x, self.letter_y))

            #draw fade overlay
            if self.fade_overlay_active and self.fade_overlay_alpha > 0:
                fade_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)

                fade_surface.fill((0, 0, 0, self.fade_overlay_alpha))
                self.screen.blit(fade_surface, (0, 0))

            if self.game_over:
                self.game_over_screen.draw(self.screen,self.level)
            # Removed os.system call - major performance bottleneck
            # print(self.FPS)  # Debug only

            #show fps...
            self.show_fps(clock)
            #if gun is selected draw ammo gui on bottom right
            if isinstance(self.current_weapon, Gun):
                self.current_weapon.ammo_gui(self.screen, self.screen_width,self.screen_height) 
            pygame.display.flip()

            #lever logic is for level 2 only
            if self.level == 2:
                #store locally if levers were all pulled previously
                previous_all_levers_pulled = self.level2.all_levers_pulled
                
                #update level 2 logic
                self.level2.update()

                #update map lever states based on level2 lever states
                self.game_map.set_all_levers_pulled(self.level2.all_levers_pulled)
                
                # Check if lever state changed and update collisions if needed
                if previous_all_levers_pulled != self.level2.all_levers_pulled:
                    self.map_needs_collision_update = True
                
                #check if all levers are pulled now and play spike retraction sound once
                if not previous_all_levers_pulled and self.level2.all_levers_pulled and not self.spikes_deactivated_sound_played:
                    
                    volume = 0.7 * game_settings.get_sfx_volume()
                    self.spike_retract.set_volume(volume)
                    self.spike_retract.play()
                    self.spikes_deactivated_sound_played = True

            # Update collision tiles when map state changes
            if self.map_needs_collision_update:
                collision_tiles, spike_tiles = self.reload_collision_data()
                
                
                # For level 2, handle spike tiles based on lever state
                if self.level == 2 and hasattr(self, 'level2') and self.level2.all_levers_pulled:
                    spike_tiles = []
                    #print("All levers pulled")
                
                # Update pathfinding grid when collision state changes
                self.path_grid = self.make_path_grid()
                    
                self.map_needs_collision_update = False
                endlevel_tiles = self.game_map.endlevel_layer("endlevel")
                endlevel_tiles = self.game_map.endlevel_layer("endlevel")

            
        pygame.quit()


    def show_fps(self, clock: pygame.time.Clock) -> None:
        """show current framrate in top right of screen

        Args:
            pygame.time.Clock for tracking time and calculating FPS
        """
        # Display FPS in the top-right corner
        text = self.fps_text_font.render(str(round(clock.get_fps(),2)), True, (255,255,255))
        self.screen.blit(text, (self.screen_width - 100, 50))

    def next_level(self) -> None:
        """
        clear all entities and call
        the method `level_transition`.
        """
        # Clean up current level entities

        self.enemies.clear()
        self.particles.clear()
        self.player.x, self.player.y =level_data[f"level{self.level}"]["start_pos"]

        self.camera.offset_x =0
        self.camera.offset_y = 0
        self.camera.zoom= 1.0
        
        self.camera.width = self.screen_width
        self.camera.height = self.screen_height
        #transition to next level
        self.level_transition()


    def level_transition(self) -> None:
        """Fade to black, increment the level counter, load the new map,
        respawn enemies, reset levers and restore collision data.
        """

        #fade transition logic 
        self.transition_timer = 500
        fade_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
       
        clock = pygame.time.Clock() 
        fade_out_duration = 1000 
        fade_out_start= pygame.time.get_ticks()
        while True:
            # get time elapsed since last frame to update fade animation smoothly
            dt= clock.tick(self.FPS) 
            elapsed =pygame.time.get_ticks() - fade_out_start

            if elapsed> fade_out_duration: break
            progress = elapsed/ fade_out_duration
            alpha = int(255 * (progress ** 0.5))  
            fade_surface.fill((0, 0, 0, alpha))
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.flip()

        #after transition increment level and load map accordingly
        self.level += 1
        #print("Transitioning from level{} to {}".format(self.level-1, self.level)) #debug
        next_level_path = f"Tiled/level{self.level}.tmx"
        print(next_level_path)

        try:
            self.game_map =TiledMap(next_level_path)
            self.game_map.set_current_level(self.level)
            self.path_grid = self.make_path_grid()

        #if next level file doesn't exist 
        except FileNotFoundError:
            print(f"No more levels file not found: {next_level_path}")
            return

        self.player.x , self.player.y = level_data[f"level{self.level}"]["start_pos"]

        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)

        # Clean up old enemies before clearing list
        for enemy in self.enemies:enemy.cleanup()
        self.enemies.clear()
        
        # Clean up particles
        for particle in self.particles:
            del particle
        self.particles.clear()
        
        # Clean up bullets
        if hasattr(self, 'bullets'):
            for bullet in self.bullets:
                del bullet
            self.bullets.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        self.loadEnemiesForLevel(self.enemies)

        #set camera zoom and update to player pos for new level
        self.zoom_level = 8.0
        self.camera.zoom = self.zoom_level
        self.camera.update(self.player)
        self.music.play_level_music(self.level)

        self.fade_overlay_active = True
        self.fade_overlay_alpha = 255
        self.fade_overlay_timer = 0
  
        #IMPORTANT: this reloads collision tiles for the new level
        self.map_needs_collision_update = True

        # Specific logic for second level: levers and retractable spikes
        if self.level == 2:
            self.level2 = level2()
            self.levers = {1: False, 2: False, 3: False, 4: False}  
            self.game_map.set_all_levers_pulled(False)  
            self.spikes_deactivated_sound_played = False  
            # find layer with levers and create a lever object for each
            lever_data = self.game_map.lever_layer("levers")
            self.lever_list = []
            #each lever has an id like lever1, lever2 etc for easy tracking in level2 class and map state
            for i, lever_info in enumerate(lever_data):
                lever_id = f"lever{i+1}"
                lever = Lever(lever_info['x'],lever_info['y'],  lever_info['type'],lever_id=lever_id)
                self.lever_list.append(lever)

         # get lighting level from json file for repective level
        self.lightlevel =level_data[f"level{self.level}"]["lighting"]

    def reload_collision_data(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        """
        Re-extract wall and spike collision tiles from the current map.

        Tires different layers names incase of inconsititent layer names
        Returns:
            A tuple pygame.Rect lists.
        """
        self.path_grid_cach = None 

        try:
            collision_tiles= self.game_map.collision_layer(["wall lining", "wall lining 2"])
            spike_tiles =self.game_map.collision_layer(["spikes"])
            return collision_tiles, spike_tiles

        except Exception as e:
            try:

                collision_tiles = self.game_map.collision_layer(["wall lining", "wall lining2"])
                spike_tiles =  self.game_map.collision_layer(["spikes"])
                return collision_tiles, spike_tiles
            
            except Exception as e1:
                try:
                    collision_tiles = self.game_map.collision_layer(["walllining1", "walllining2"])
                    spike_tiles = self.game_map.collision_layer(["spikes"])
                    return collision_tiles, spike_tiles

                except Exception as e2:
                    #error handling incase of different spelling of layer
                    collision_tiles =  self.game_map.collision_layer(["wall lining"])
                    spike_tiles =  []
                    return collision_tiles, spike_tiles

    def spawn_enemy(self, x: float, y: float, enemy_type: str) -> None:
        """
        spawn single enemy of the given type at world position (x, y).

        Args:
            x: x  coordinate.
            y: y  coordinate.
            enemy_type: Key for "enemy_data.json" file.
        """
        data = enemy_data[enemy_type]
        enemy = Enemy(x, y, enemy_type, data)
        self.enemies.append(enemy)
       
    def loadEnemiesForLevel(self, enemies_list: list[Enemy]) -> None:
        """
        Populate the enemies_list with all enemies that should spawn on
        current level using spawn locations from enemy_data.jso.

        Args:
            enemies_list: mutable list to add newly created enemies
        """
        level_key = f"level{self.level}"
        for enemy_type, data in enemy_data.items():

            if "spawn_locations" in data and level_key in data["spawn_locations"]:
                for spawnpoint in data[ "spawn_locations"][level_key]:

                    enemy = Enemy(spawnpoint["x" ], spawnpoint["y"], enemy_type,data)

                    enemies_list.append(enemy)

        #for i in range(2): 
        #    enemy_type = "chort"
         #   data = enemy_data[enemy_type]
        #    enemies.append(Enemy(player_x + (50 * i), player_y + (50 * i), enemy_type))
        
    def make_path_grid(self) -> list[list[int]]:
        """
        Build pathfinding grid for the current level.

        The grid is a 2D list with 1 for walkable cells and 0 for blocked
        cells.   Blocked cells are expanded by the largest enemy's footprint so
        enemies never path through tiles they can't physically fit through.

        Returns:
            2D  grid of integers(rows×columns) matching the map's tile dimensions.
        """

        # Return cached grid if available
        # This saves processing time so you don't need to recalculate the grid every time
        if self.path_grid_cach is not None: return self.path_grid_cach
        
        walkable_tiles =[]
        tile_size =16
        
        #calculate maximum enemy dimensions for pathfinding clearance
        #set default to 1 tile to avoid issue if enemy data is missing or zero
        max_enemy_width = 0
        max_enemy_height = 0
        
        for enemy_type, data in enemy_data.items():
            enemy_width_tiles = max(1, (data["width"] + tile_size - 1) // tile_size)  #round up
            enemy_height_tiles = max(1, (data["height"] + tile_size - 1) // tile_size)  #round up
            max_enemy_width = max(max_enemy_width, enemy_width_tiles)
            max_enemy_height = max(max_enemy_height, enemy_height_tiles)
        
        print(f"Pathfinding using clearance:{max_enemy_width}x{max_enemy_height} tiles")
        
        #get current collision tiles from the same method that works for player and enemy collision
        collision_tiles, spike_tiles = self.reload_collision_data()
        
        #for level 2, handle spike tiles based on lever state
        if self.level == 2 and hasattr(self, 'level2') and self.level2.all_levers_pulled:
            spike_tiles = []
        
        # Combine all obstacle tiles
        all_obstacle_tile = collision_tiles +spike_tiles
        # Create a set of blocked tile coordinates for fast lookup
        blocked_tiles = set()
        for tile_rect in all_obstacle_tile:
            #convert pixel coordinates to tile coordinates
            tile_x = tile_rect.x // tile_size
            tile_y = tile_rect.y // tile_size

            blocked_tiles.add((tile_x, tile_y))
        
        #  generate pathfinding grid
        for y in range(self.game_map.tmx_data.height):
            row = []

            for x in range(self.game_map.tmx_data.width):
                # Check if this tile or adjacent tiles (for enemy size) are blocked                
                blocked = False
                
                # Check if any tile within the largest enemy's footprint is blocked
                for check_y in range(y, min(self.game_map.tmx_data.height, y+ max_enemy_height)):                    
                    for  check_x in range(x,min(self.game_map.tmx_data.width, x +  max_enemy_width)):
                        if (check_x, check_y ) in blocked_tiles:
                            
                            blocked = True
                            break
                    if blocked:
                        break
                
                # 1 = walkable, 0 = blocked (pathfinding library expects this format)
                row.append(1 if not blocked else 0)
            walkable_tiles.append(row)
        
        # Cache the grid before returning
        self.path_grid_cach = walkable_tiles
        return walkable_tiles

    def player_damage(self, damage_amount: float) -> None:
        """
        Apply damage to the player if the invincibility cooldown at 0.

        Args:
            damage_amount: damage used to update health bar.
        """

        #if damaged check if not invisible and apply damage and play sound
        if self.player_damage_cooldown <= 0:
            self.health_bar.damage(damage_amount)
            volume = 0.6 * game_settings.get_sfx_volume()
            self.player_sounds["hurt"].set_volume(volume)
            self.player_sounds["hurt"].play()

            self.player_damage_cooldown = self.player_damage_cooldown_duration

    def collect_xp(self, xp_amount: int) -> None:
        """Collect XP when an enemy is elliminated, play pling sound and update XP bar."""
        self.xp += xp_amount
        
        #clear any existing XP sound timers first to prevent accumulating and memory leaks which are bad
        for event_id in self.xp_sound_events:
            pygame.time.set_timer(event_id, 0)  #0 disables the timer

        self.xp_sound_events.clear()       
        # Play multiple pling sounds based on XP amount
        num_sounds = max(1, min(xp_amount // 2, 5))  #At least 1, max 5 sounds       
        for i in range(num_sounds):
            #randomly select pling sound from the array

            if self.orb_sounds:
                orbsound = random.choice(self.orb_sounds)
                
                # Random volume variation (0.3 to 0.8 base, then apply settings)
                base_volume = random.uniform(0.3,0.8)

                final_volume= base_volume* game_settings.get_sfx_volume()
                orbsound.set_volume( final_volume)

                #play with small delays between sounds for a cascade effect
                if i==0:
                    orbsound.play()
                else:
                    # Store the sound in a way that the timer can access it
                    setattr(self, f'delayed_pling_{i}', orbsound)
                    event_id = pygame.USEREVENT + 1 + i
                    self.xp_sound_events.append(event_id)  #track event
                    pygame.time.set_timer(event_id, i* 70,1)  # 1 = fire once only
        self.experience_bar.update(self.xp)


    def restart_game(self) -> None:
        """Reset all game state back to level 0 for a new run."""
        # Reset level and game state
        self.level = 0
        self.game_over = False
        self.death_sound_played = False
        self.spikes_deactivated_sound_played = False
        
        # Reset health and player damage cooldown
        self.health_bar.life = 100
        self.health_bar.update(100)
        self.player_damage_cooldown = 0
        
        # Reset XP
        self.xp = 0
        
        #reset music
        self.music.play_level_music(0)
        
        # reload level 0 map
        self.game_map = TiledMap("Tiled/level0.tmx")

        self.game_map.set_current_level(self.level)
        self.path_grid = self.make_path_grid()
        
        # Reset level 2 states and levers

        self.level2 = level2()
        self.levers = {1:False, 2 : False , 3 : False, 4: False} 

        self.game_map.set_all_levers_pulled(False)
        self.lever_list = []  # Clear lever objects
        # Reset player position
        self.player.x, self.player.y = level_data[f"level{self.level}"]["start_pos"]
        # Clear all dynamic objects
        self.enemies.clear()
        self.particles.clear()
        self.bullets.clear()  # Clear bullets
        
        # Reload enemies for level 1
        self.loadEnemiesForLevel(self.enemies) 
        # Reset camera
        self.camera.zoom = 10
        self.camera.update(self.player)
        # Reset chests for level 1
        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)
        #reset animationstate
        self.show_letter =False
        self.letter_anmation_complete= False

        self.letter_frame_index = 0

        self.letter_animation_timer = 0
        self.show_press_e = False
        
         # reset fade overlay
        self.fade_overlay_alpha = 0
        self.fade_overlay_timer = 0
        self.fade_overlay_active = False        
        # Reset lighting level
        self.lightlevel = level_data["level0"]["lighting"]
        #collision data reload
        self.map_needs_collision_update = True