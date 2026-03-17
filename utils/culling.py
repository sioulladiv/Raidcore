import pygame

class FrustumCuller:
    """
    Handles frustum culling for the game to optimize rendering performance.
    Only renders objects that are visible within the camera's view.
    """
    
    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height

    def is_rect_visible(self, rect: pygame.Rect, camera: object) -> bool:
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
    
    def is_point_visible(self, x: float, y: float, camera: object, margin: float = 0) -> bool:
        """
        Check if a point is visible within the camera's view with optional margin.
        
        Args:
            x, y: World coordinates
            camera: Camera object
            margin: Additional margin around the screen (useful for objects slightly off-screen)
            
        Returns:
            bool: True if the point is visible, False otherwise
        """

        # Transform world coordinates to screen coordinates
        screen_x = x * camera.zoom + camera.offset_x
        screen_y = y * camera.zoom + camera.offset_y
        
        # Check if the point is within the screen bounds plus margin
        return (screen_x >= -margin and 
                screen_x <= self.screen_width + margin and
                screen_y >= -margin and 
                screen_y <= self.screen_height + margin)
    
    def is_entity_visible(self, entity: object, camera: object, margin: float = 50) -> bool:
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
    
    def get_visible_tile_bounds(self, camera: object, tile_size: int) -> tuple[int, int, int, int]:
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
    
    def filter_visible_entities(self, entities: list, camera: object, margin: float = 50) -> list:
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
            if self.is_entity_visible(entity, camera, margin):
                visible_entities.append(entity)
                
        return visible_entities
