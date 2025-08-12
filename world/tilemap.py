from pytmx.util_pygame import load_pygame
import pygame

class TiledMap:
    def __init__(self, filename):
        self.tmx_data = load_pygame(filename)
        self.width = self.tmx_data.width * self.tmx_data.tilewidth
        self.height = self.tmx_data.height * self.tmx_data.tileheight
        
    def render_layer(self, surface, layer):
        for x, y, gid in layer:
            tile = self.tmx_data.get_tile_image_by_gid(gid)
            if tile:
                position = (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight)
                surface.blit(tile, position)
                
    def render_group_layers(self, surface, group_name):
        try:
            group = self.tmx_data.get_layer_by_name(group_name)
            for layer in group:
                if hasattr(layer, 'data'):
                    self.render_layer(surface, layer)
        except ValueError:
            print(f"Group '{group_name}' not found.")
                
    def render_all_layers(self, surface):
        for layer in self.tmx_data.layers:
            if hasattr(layer, 'data'):
                self.render_layer(surface, layer)
            elif hasattr(layer, 'layers'):
                for sublayer in layer.layers:
                    if hasattr(sublayer, 'data'):
                        self.render_layer(surface, sublayer)

    def collision_layer(self, layer_name: list):
        self.collision_tiles = []
        for layer_i in layer_name:
            layer = self.tmx_data.get_layer_by_name(layer_i)
            for x, y, gid in layer:
                tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                if tile_image:
                    self.collision_tiles.append(pygame.Rect(
                        x * self.tmx_data.tilewidth, 
                        y * self.tmx_data.tileheight, 
                        self.tmx_data.tilewidth, 
                        self.tmx_data.tileheight
                    ))
        return self.collision_tiles
    
    def endlevel_layer(self, layer_name: str):
        self.endlevel_tiles = []
        layer = self.tmx_data.get_layer_by_name(layer_name)
        for x, y, gid in layer:
            tile_image = self.tmx_data.get_tile_image_by_gid(gid)
            if tile_image:
                self.endlevel_tiles.append(pygame.Rect(
                    x * self.tmx_data.tilewidth, 
                    y * self.tmx_data.tileheight, 
                    self.tmx_data.tilewidth, 
                    self.tmx_data.tileheight
                ))
        return self.endlevel_tiles

    def chests_layer(self, layer_name: str):
        self.chest_tiles = []
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
            for x, y, gid in layer:
                tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                if tile_image:
                    self.chest_tiles.append({
                        'x': x * self.tmx_data.tilewidth,
                        'y': y * self.tmx_data.tileheight,
                        'type': 'treasure'  
                    })
        except ValueError:
            print(f"Chest layer '{layer_name}' not found.")
        return self.chest_tiles

    def make_map(self):
        map_surface = pygame.Surface((self.width, self.height))
        map_surface.fill((0, 0, 0)) 
        self.render_all_layers(map_surface)
        return map_surface

class Tile:
    def __init__(self, x, y, image, width=16, height=16):
        self.image = image
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, surface, camera_offset_x, camera_offset_y):
        draw_pos = (self.rect.x + camera_offset_x, self.rect.y + camera_offset_y)
        surface.blit(self.image, draw_pos)