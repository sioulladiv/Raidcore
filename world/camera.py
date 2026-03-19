"""Camera: follows the player with mouse-offset smoothing and zoom support."""
import pygame


class Camera:
    """ 2D camera that tracks an entity while offsetting toward the mouse cursor.

    The camera computes offset_x / offset_y each frame so that the
    tracked entity stays near (but not fixed at) the screen centre, allowing
    the player to "look ahead" by moving the mouse.
    """
    def __init__(self, width: int, height: int, zoom: float = 1.0) -> None:
        """Create a camera.

        Args:
            width: Viewport width in pixels (typically the screen width).
            height: Viewport height in pixels.
            zoom: Initial zoom factor; values > 1 magnify the scene.
        """
        self.width = width

        self.height = height
        self.offset_x = 0
        self.offset_y = 0

        self.zoom = zoom
        self.ratio = 15
    
    def update(self, target: object) -> None:
        """Recompute offsets so the camera tracks *target* with mouse lead.

        Args:
            target: Any object with ``x``, ``y``, ``width`` and ``height``
                attributes (typically the :class:`~entities.player.Player`).    
        """
        target_center_x = target.x + (target.width / 2)
        target_center_y = target.y + (target.height / 2)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        real_mouse_x = (mouse_x -self.offset_x)/ self.zoom
        real_mouse_y = (mouse_y -self.offset_y)/ self.zoom 

        # focus_x = ( self.ratio * target_center_x + real_mouse_x)/ ( self.ratio+1)
        # focus_y = ( self.ratio * target_center_y + real_mouse_y)/  (self.ratio+1)
        self.offset_x = self.width// 2 - int((( self.ratio * target_center_x + real_mouse_x)/( self.ratio+1))*self.zoom)
        self.offset_y = self.height// 2 - int((( self.ratio * target_center_y + real_mouse_y)/ (self.ratio+1))*self.zoom)
    
    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """
        Transform a world space rectangle into screen space.

        Args:
            rect: pygame.Rect in world coordinates.

        Returns:
            A new pygame.Rect in screen-space coordinates.
        """
        return pygame.Rect(

            int(rect.x*self.zoom) + self.offset_x,
            int(rect.y*self.zoom) + self.offset_y,
            int(rect.width*self.zoom),
            int(rect.height*self.zoom)
        )
        
    def apply_zoom(self, value: float) -> int:
        """
        Scale a single world-space value by the current zoom factor.

        Args:
            value: Length / distance in world pixels.
        Returns:
            Equivalent length in screen pixels (integer).
        """
        return int(value*self.zoom)
