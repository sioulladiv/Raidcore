from pytmx.util_pygame import load_pygame
import pygame

class TiledMap:
    def __init__(self, filename, ):
        self.tmx_data = load_pygame(filename)
        self.width = self.tmx_data.width * self.tmx_data.tilewidth  
        self.height = self.tmx_data.height * self.tmx_data.tileheight
        self.lever_states = {
            'lever1': False,
            'lever2': False,
            'lever3': False,
            'lever4': False
        }
        self.current_level = 1  
        self.all_levers_pulled = False  # Track if all levers are pulled
        
    def set_current_level(self, level):
        self.current_level = level
        
    def render_layer(self, surface, layer, visible_bounds=None):
        for x, y, gid in layer:
            # Skip tiles outside visible bounds if culling is enabled
            if visible_bounds:
                start_x, start_y, end_x, end_y = visible_bounds
                if x < start_x or x >= end_x or y < start_y or y >= end_y:
                    continue
                    
            tile = self.tmx_data.get_tile_image_by_gid(gid)
            if tile:
                position = (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight)
                surface.blit(tile, position)
                
    def render_group_layers(self, surface, group_name, visible_bounds=None):
        try:
            group = self.tmx_data.get_layer_by_name(group_name)
            for layer in group:
                if hasattr(layer, 'data'):
                    self.render_layer(surface, layer, visible_bounds)
        except ValueError:
            print(f"Group '{group_name}' not found.")
                
    def render_all_layers(self, surface, visible_bounds=None):
        for layer in self.tmx_data.layers:
            if hasattr(layer, 'data'):
                # Skip lever layers if we're on level 2 and the corresponding lever isn't pulled
                if self.current_level == 2 and layer.name in ['lever1', 'lever2', 'lever3', 'lever4']:
                    if not self.lever_states.get(layer.name, False):
                        continue
                # Only show spikes2 layer when all levers are pulled on level 2
                elif self.current_level == 2 and layer.name == 'spikes2':
                    if not self.all_levers_pulled:
                        continue
                self.render_layer(surface, layer, visible_bounds)
            elif hasattr(layer, 'layers'):
                for sublayer in layer.layers:
                    if hasattr(sublayer, 'data'):
                        # Skip lever layers if we're on level 2 and the corresponding lever isn't pulled
                        if self.current_level == 2 and sublayer.name in ['lever1', 'lever2', 'lever3', 'lever4']:
                            if not self.lever_states.get(sublayer.name, False):
                                continue
                        # Only show spikes2 layer when all levers are pulled on level 2
                        elif self.current_level == 2 and sublayer.name == 'spikes2':
                            if not self.all_levers_pulled:
                                continue
                        self.render_layer(surface, sublayer, visible_bounds)

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

    def lever_layer(self, layer_name: str):
        self.lever_tiles = []
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
            for x, y, gid in layer:
                tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                if tile_image:
                    self.lever_tiles.append({
                        'x': x * self.tmx_data.tilewidth,
                        'y': y * self.tmx_data.tileheight,
                        'type': 'lever'  
                    })
        except ValueError:
            print(f"Lever layer '{layer_name}' not found.")
        return self.lever_tiles

    def update_lever_state(self, lever_name, is_pulled):
        """Update the state of a specific lever (level 2 only)"""
        if self.current_level == 2 and lever_name in self.lever_states:
            self.lever_states[lever_name] = is_pulled
            self.all_levers_pulled = all(self.lever_states.values())
            return True
        return False

    def set_all_levers_pulled(self, all_pulled):
        """Manually set the all_levers_pulled state"""
        self.all_levers_pulled = all_pulled

    def make_map(self, visible_bounds=None):
        map_surface = pygame.Surface((self.width, self.height))
        map_surface.fill((0, 0, 0)) 
        self.render_all_layers(map_surface, visible_bounds)
        return map_surface
    
    def render_to_screen(self, screen, camera, visible_bounds):
        """
        Render only visible tiles directly to the screen with camera transformation.
        This is more efficient than creating a full map surface.
        """
        total_tiles_rendered = 0
        
        for layer in self.tmx_data.layers:
            if hasattr(layer, 'data'):
                # Skip lever layers if we're on level 2 and the corresponding lever isn't pulled
                if self.current_level == 2 and layer.name in ['lever1', 'lever2', 'lever3', 'lever4']:
                    if not self.lever_states.get(layer.name, False):
                        continue
                # Only show spikes2 layer when all levers are pulled on level 2
                elif self.current_level == 2 and layer.name == 'spikes2':
                    if not self.all_levers_pulled:
                        continue
                total_tiles_rendered += self._render_layer_to_screen(screen, layer, camera, visible_bounds)
            elif hasattr(layer, 'layers'):
                for sublayer in layer.layers:
                    if hasattr(sublayer, 'data'):
                        # Skip lever layers if we're on level 2 and the corresponding lever isn't pulled
                        if self.current_level == 2 and sublayer.name in ['lever1', 'lever2', 'lever3', 'lever4']:
                            if not self.lever_states.get(sublayer.name, False):
                                continue
                        # Only show spikes2 layer when all levers are pulled on level 2
                        elif self.current_level == 2 and sublayer.name == 'spikes2':
                            if not self.all_levers_pulled:
                                continue
                        total_tiles_rendered += self._render_layer_to_screen(screen, sublayer, camera, visible_bounds)
        
        return total_tiles_rendered
    
    def _render_layer_to_screen(self, screen, layer, camera, visible_bounds):
        """Helper method to render a single layer directly to screen."""
        start_x, start_y, end_x, end_y = visible_bounds
        
        # Count rendered tiles for performance metrics (optional debug info)
        tiles_rendered = 0
        
        for x, y, gid in layer:
            # Skip tiles outside visible bounds
            if x < start_x or x >= end_x or y < start_y or y >= end_y:
                continue
                
            tile = self.tmx_data.get_tile_image_by_gid(gid)
            if tile:
                tiles_rendered += 1
                
                # Calculate world position
                world_x = x * self.tmx_data.tilewidth
                world_y = y * self.tmx_data.tileheight
                
                # Apply camera transformation
                screen_x = world_x * camera.zoom + camera.offset_x
                screen_y = world_y * camera.zoom + camera.offset_y
                
                # Scale tile if necessary
                if camera.zoom != 1.0:
                    scaled_width = int(self.tmx_data.tilewidth * camera.zoom)
                    scaled_height = int(self.tmx_data.tileheight * camera.zoom)
                    tile = pygame.transform.scale(tile, (scaled_width, scaled_height))
                
                screen.blit(tile, (screen_x, screen_y))
                
        return tiles_rendered

    def change_single_tile(self, layer_name, tile_x, tile_y, new_gid):
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
            if hasattr(layer, 'data'):
                index = tile_y * self.tmx_data.width + tile_x
                
                if 0 <= index < len(layer.data):
                    layer.data[index] = new_gid
                    return True
                else:
                    print(f"Tile position ({tile_x}, {tile_y}) out of bounds")
        except ValueError:
            print(f"Layer '{layer_name}' not found.")
        return False
    
    def change_tile_at_world_pos(self, layer_name, world_x, world_y, new_gid):
        tile_x = world_x // self.tmx_data.tilewidth
        tile_y = world_y // self.tmx_data.tileheight
        return self.change_single_tile(layer_name, tile_x, tile_y, new_gid)

class Tile:
    def __init__(self, x, y, image, width=16, height=16):
        self.image = image
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, surface, camera_offset_x, camera_offset_y):
        start_x = max(0, int(-camera_offset_x / tile_size) - 1)
        start_y = max(0, int(-camera_offset_y / tile_size) - 1)
        end_x = min(self.level_width, int((-camera_offset_x + self.screen_width) / tile_size) + 2)
        end_y = min(self.level_height, int((-camera_offset_y + self.screen_height) / tile_size) + 2)

        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                tile = self.get_tile(x, y)
                if tile:
                    draw_x = x * tile_size + camera_offset_x
                    draw_y = y * tile_size + camera_offset_y
                    surface.blit(tile, (draw_x, draw_y))