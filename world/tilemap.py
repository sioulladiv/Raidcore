from __future__ import annotations

from pytmx.util_pygame import load_pygame
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.camera import Camera


class TiledMap:
    """
     Wraps a pytmx map and provides rendering helpers.

    Supports multi-layer rendering with frustum culling, per-level collision,
    and data extraction for chests, levers and end-level trigger zones.
    """
    def __init__(self, filename: str) -> None:
        """
        Load a TMX map file

        Args:
            filename: Path to the ".tmx" file from root.
        """
        self.tmx_data = load_pygame(filename)

        self.width = self.tmx_data.width*self.tmx_data.tilewidth  
        self.height = self.tmx_data.height*self.tmx_data.tileheight

        self.lever_states = {
            'lever1': False,
            'lever2': False,
            'lever3': False,
            'lever4': False
        }
        self.current_level = 1  
        self.all_levers_pulled = False  # Track if all levers are pulled
        
        # Cache for scaled tiles to avoid repeated transform.scale
        self.scaled_tile_cache = {}
        self.last_zoom = 1.0
        
    def set_current_level(self, level: int) -> None:
        """
        Store current level number so lever/spike visibility rules can
        be applied

        Args:
            level: Integer level index.
        """
        self.current_level = level
        
    def render_layer(self, surface: pygame.Surface, layer:object,visible_bounds: tuple[int, int, int,int]| None =None) -> None:
        """
        Render a single tile layer onto surface.

        Args:
            surface:Pygame surface to draw onto.
            layer: A pytmx tile-layer object.

            visible_bounds: Optional (start_x, start_y, end_x, end_y) tile
                coordinate window for culling; when None all tiles render.
        """

        for x,y,gid in layer:
            # Skip tiles outside visible bounds if culling enabled

            if visible_bounds:
                start_x, start_y, end_x, end_y = visible_bounds
                if x < start_x or x >= end_x or y < start_y or y >= end_y:
                    continue
                    
            tile = self.tmx_data.get_tile_image_by_gid(gid)
            
            if tile:

                position = (x*self.tmx_data.tilewidth, y*self.tmx_data.tileheight)
                surface.blit(tile, position)
                
    def render_group_layers(self,surface:pygame.Surface,group_name: str, visible_bounds: tuple[int, int, int, int] | None = None) -> None:
        """
        Render tile layers inside named layer group.

        Args:
            surface: Pygame surface to draw onto
            group_name:Name of the group layer in the TMX file.
            visible_bounds
        """
        try:
            group = self.tmx_data.get_layer_by_name(group_name)

            for layer in group:

                if hasattr(layer, 'data'):
                    self.render_layer(surface, layer, visible_bounds)

        except ValueError:

            print(f"Group'{group_name}' not found.")
                
    def render_all_layers(self, surface: pygame.Surface, visible_bounds: tuple[int, int, int, int] | None = None) -> None:
        """Render every tile layer in the map, respecting lever/spike state.

        Args:
            surface: Pygame surface to draw onto.
            visible_bounds: Optional culling window (see :meth:`render_layer`).
        """
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

    def collision_layer(self, layer_name: list[str]) -> list[pygame.Rect]:
        """
        Extract solid collision rects from one or more named layers.

        Args:
            layer_name: list of TMX layer names whose tiles should be treated
                as solid obstacles.

        Returns:
            List of pygame.Rect objects in world pixel coordinates.
        """
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
    
    def endlevel_layer(self, layer_name: str) -> list[pygame.Rect]:
        """
        Return the trigger rectangles for the level-exit zone.

        Args:
            layer_name: Name of the end-level object layer in the TMX file.

        Returns:
            List of pygame.Rect objects that trigger a level transition.
        """
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

    def chests_layer(self,layer_name:str) -> list[dict]:
        """
        Extract chest object data from the named layer.

        Args:
            layer_name: Name of the chests object layer in the TMX file.

        Returns:
            List of dicts with keys x, y and type .
        """
        self.chest_tiles = []
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
            for x, y, gid in layer:
                tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                if tile_image:

                    self.chest_tiles.append({
                        'x': x*self.tmx_data.tilewidth,
                        'y': y*self.tmx_data.tileheight,
                        'type': 'treasure'  
                    })

        except ValueError:
            print(f"Chest layer'{layer_name}' not found.")
        return self.chest_tiles

    def lever_layer(self, layer_name:str) ->list[dict]:
        """
        Extract lever object data from named layer.

        Args:
            layer_name: Name of the levers object layer in the TMX file.

        Returns:
            List of dicts with keys x, y andtype.
        """
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

    def update_lever_state(self, lever_name:str, is_pulled: bool) -> bool:
        """Update the state of a specific lever (level 2 only) """
        if self.current_level == 2 and lever_name in self.lever_states:
            self.lever_states[lever_name] = is_pulled
            self.all_levers_pulled = all(self.lever_states.values())
            
            return True
        return False

    def set_all_levers_pulled(self, all_pulled:bool) -> None:
        """ 
        set the all_levers_pulled state
         """
        self.all_levers_pulled =all_pulled

    def make_map(self, visible_bounds: tuple[int, int, int, int] | None = None) -> pygame.Surface:
        """
        return a full-size map surface all layers together.

        Args:
            visible_bounds: a culling window fro the renderers.

        Returns:
            A new pygame.Surface containing the full rendered map.
        """
        map_surface =pygame.Surface(( self.width, self.height))
        map_surface.fill((0, 0,0)) 

        self.render_all_layers(map_surface, visible_bounds)
        return map_surface
    
    def render_to_screen(self, screen: pygame.Surface,camera: Camera, visible_bounds: tuple[int, int, int, int]) -> int:
        """
        Render only visible tiles directly to the screen with camera transformation.

        This is more efficient than creating a full map surface.

        Args:
            screen: the main display surface.
            camera: active camera for world to screen transformation.
            visible_bounds:   start_x, start_y, end_x, end_y 
                coordinates from :class  utils.culling.FrustumCuller` .

        Returns:
            Total number of tiles rendered that frame.
        
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
    
    def _render_layer_to_screen(self, screen:pygame.Surface, layer: object, camera: Camera,visible_bounds: tuple[int, int, int, int]) -> int:
        """Render a single tile layer directly to screen, using a scaled-tile
        cache to avoid repeated ``transform.scale`` calls.

        Args:
            screen: The main display surface.
            layer: A pytmx tile-layer object.
            camera: Active camera.
            visible_bounds: start_x, start_y, end_x, end_y .

        Returns:
            Number of tiles rendered.
        """
        start_x, start_y, end_x, end_y = visible_bounds
        
        # Clear cache if zoom changed significantly
        if abs(camera.zoom - self.last_zoom) > 0.01:
            self.scaled_tile_cache.clear()
            self.last_zoom = camera.zoom
        
        # Count rendered tiles for performance metrics
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
                
                #scale tile if necessary using cache
                if camera.zoom != 1.0:
                    scaled_width = int(self.tmx_data.tilewidth * camera.zoom)
                    scaled_height = int(self.tmx_data.tileheight * camera.zoom)
                    
                    
                    
                    # Use cache to avoid repeated scaling of same tile
                   
                    cache_key = (gid, scaled_width, scaled_height)
                    if cache_key not in self.scaled_tile_cache:
                        
                        
                        self.scaled_tile_cache[cache_key] = pygame.transform.scale(tile, (scaled_width, scaled_height))
                    tile = self.scaled_tile_cache[cache_key]
                
                screen.blit(tile, (screen_x, screen_y))
                
        return tiles_rendered

    def change_single_tile(self, layer_name: str, tile_x: int, tile_y: int, new_gid: int) -> bool:
        """Swap a single tile in a layer by its tile-grid coordinates.

        Args:
            layer_name: Name of the layer to modify
            tile_x: Column index of the tile
            tile_y: row index of the tile
            new_gid: Replacement global tile ID

        Returns:
            True for success False if the layer or tile was not found.
        """
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
    
    def change_tile_at_world_pos(self, layer_name: str, world_x: float, world_y: float, new_gid: int) -> bool:
        """
        swap a tile at a world pixel position.

        Converts the world coordinates to tile coordinates then delegates to the method change_single_tile.

        Args:
            layer_name: Name of the layer to modify
            world_x: world x-coordinate in pixels
            world_y: world y-coordinate in pixels
            new_gid: replacement global tile ID

        Returns:
            True on success, False otherwise
        """
        tile_x = world_x // self.tmx_data.tilewidth
        tile_y = world_y // self.tmx_data.tileheight
        return self.change_single_tile(layer_name, tile_x, tile_y, new_gid)

class Tile:
    """
    A single renderable tile with a rect and an associated image surface
    """

    def __init__(self, x:float, y: float, image:pygame.Surface,width: int = 16,height: int = 16) -> None:
        """Create a tile.

        Args:
            x: worldx-coordinate.
            y: World y-coordinate.
            image: pre-loaded tile image surface.
            width: Tile width in pixels (default 16).
            height: Tile height in pixels (default 16).
        
        """
        self.image = image
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, surface, camera_offset_x, camera_offset_y):
        start_x = max(0, int(-camera_offset_x/tile_size) -1)
        start_y= max(0, int(-camera_offset_y/tile_size)- 1)
        end_x =min(self.level_width, int((-camera_offset_x + self.screen_width)/tile_size)+ 2)
        end_y= min(self.level_height, int((-camera_offset_y +self.screen_height) /tile_size)+ 2)

        for x in range(start_x, end_x):
            for y in range(start_y,end_y):
                tile =self.get_tile(x, y)
                if tile:
                    draw_x = x*tile_size + camera_offset_x
                    draw_y = y*tile_size + camera_offset_y
                    surface.blit(tile,(draw_x, draw_y))