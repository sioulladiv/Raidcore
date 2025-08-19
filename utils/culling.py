import pygame

"""
Frustum Culling Implementation for Dungeon Escape Game

This module implements frustum culling to optimize rendering performance by only drawing 
objects that are visible within the camera's view. This can significantly improve performance
especially on large maps with many entities.

Key features:
- Tile culling: Only renders tiles visible on screen
- Entity culling: Only draws enemies, particles, and bullets within screen bounds
- Maintains pathfinding: Enemy pathfinding grid is unaffected by rendering optimizations
- Debug support: Optional performance statistics to measure culling effectiveness

Performance improvements:
- Reduces number of draw calls
- Decreases memory bandwidth usage
- Improves frame rate on large scenes
- Scales better with map size and entity count
"""

class FrustumCuller:
    """
    Handles frustum culling for the game to optimize rendering performance.
    Only renders objects that are visible within the camera's view.
    """
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Debug statistics
        self.debug_enabled = False
        self.culled_count = 0
        self.total_count = 0
    
    def enable_debug(self, enabled=True):
        """Enable debug statistics for culling performance."""
        self.debug_enabled = enabled
        if enabled:
            self.culled_count = 0
            self.total_count = 0
    
    def get_debug_stats(self):
        """Get debug statistics."""
        if self.total_count > 0:
            cull_percentage = (self.culled_count / self.total_count) * 100
            return f"Culled: {self.culled_count}/{self.total_count} ({cull_percentage:.1f}%)"
        return "No culling data"
    
    def is_rect_visible(self, rect, camera):
        """
        Check if a rectangle is visible within the camera's view.
        
        Args:
            rect: pygame.Rect object in world coordinates
            camera: Camera object
            
        Returns:
            bool: True if the rectangle is visible, False otherwise
        """
        # Transform world coordinates to screen coordinates
        screen_x = rect.x * camera.zoom + camera.offset_x
        screen_y = rect.y * camera.zoom + camera.offset_y
        screen_width = rect.width * camera.zoom
        screen_height = rect.height * camera.zoom
        
        # Check if the transformed rectangle intersects with the screen
        return (screen_x + screen_width >= 0 and 
                screen_x <= self.screen_width and
                screen_y + screen_height >= 0 and 
                screen_y <= self.screen_height)
    
    def is_point_visible(self, x, y, camera, margin=0):
        """
        Check if a point is visible within the camera's view with optional margin.
        
        Args:
            x, y: World coordinates
            camera: Camera object
            margin: Additional margin around the screen (useful for objects slightly off-screen)
            
        Returns:
            bool: True if the point is visible, False otherwise
        """
        screen_x = x * camera.zoom + camera.offset_x
        screen_y = y * camera.zoom + camera.offset_y
        
        return (screen_x >= -margin and 
                screen_x <= self.screen_width + margin and
                screen_y >= -margin and 
                screen_y <= self.screen_height + margin)
    
    def is_entity_visible(self, entity, camera, margin=50):
        """
        Check if an entity is visible within the camera's view.
        
        Args:
            entity: Entity object with x, y, width, height attributes
            camera: Camera object
            margin: Additional margin around the screen for early culling
            
        Returns:
            bool: True if the entity is visible, False otherwise
        """
        entity_rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
        
        # Transform to screen coordinates
        screen_x = entity.x * camera.zoom + camera.offset_x
        screen_y = entity.y * camera.zoom + camera.offset_y
        screen_width = entity.width * camera.zoom
        screen_height = entity.height * camera.zoom
        
        # Check with margin for smooth transitions
        return (screen_x + screen_width >= -margin and 
                screen_x <= self.screen_width + margin and
                screen_y + screen_height >= -margin and 
                screen_y <= self.screen_height + margin)
    
    def get_visible_tile_bounds(self, camera, tile_size):
        """
        Calculate which tiles are visible based on camera position and zoom.
        
        Args:
            camera: Camera object
            tile_size: Size of each tile in pixels
            
        Returns:
            tuple: (start_x, start_y, end_x, end_y) tile coordinates
        """
        # Calculate world coordinates of screen corners
        top_left_world_x = (-camera.offset_x) / camera.zoom
        top_left_world_y = (-camera.offset_y) / camera.zoom
        bottom_right_world_x = (self.screen_width - camera.offset_x) / camera.zoom
        bottom_right_world_y = (self.screen_height - camera.offset_y) / camera.zoom
        
        # Convert to tile coordinates with some margin
        margin_tiles = 2
        start_x = max(0, int(top_left_world_x // tile_size) - margin_tiles)
        start_y = max(0, int(top_left_world_y // tile_size) - margin_tiles)
        end_x = int(bottom_right_world_x // tile_size) + margin_tiles
        end_y = int(bottom_right_world_y // tile_size) + margin_tiles
        
        return start_x, start_y, end_x, end_y
    
    def filter_visible_entities(self, entities, camera, margin=50):
        """
        Filter a list of entities to only include visible ones.
        
        Args:
            entities: List of entity objects
            camera: Camera object
            margin: Additional margin for culling
            
        Returns:
            list: Filtered list of visible entities
        """
        visible_entities = []
        for entity in entities:
            if self.debug_enabled:
                self.total_count += 1
            
            if self.is_entity_visible(entity, camera, margin):
                visible_entities.append(entity)
            elif self.debug_enabled:
                self.culled_count += 1
                
        return visible_entities
