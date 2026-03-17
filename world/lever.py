"""Lever interactive object used to deactivate traps on level 2."""
from __future__ import annotations

import pygame
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.player import Player


class Lever:
    """
     lever that the player can pull (once) to progress the level.

    On level 2, pulling all four levers deactivates the spike traps.
    """
    def __init__(self, x: float, y: float, task_type: str, height: int = 32, width: int = 32, lever_id: str | None = None) -> None:
        """Create a lever.

        Args:
            x: World x-coordinate of the top-left corner.
            y: World y-coordinate of the top-left corner.
            task_type: Type tag (e.g. ``'lever'``).
            height: Sprite height in pixels (default 32).
            width: Sprite width in pixels (default 32).
            lever_id: Unique identifier string (e.g. ``'lever1'``).
        """
        self.type = task_type
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.proximity_distance = 16
        self.interaction_distance = 16
        self.is_pulled = False
        self.lever_id = lever_id  

    def pull(self) -> bool:
        """Pull this lever.

        Returns:
            ``True`` if the lever was newly pulled, False if it was
            already in the pulled state.
        """
        if not self.is_pulled:
            self.is_pulled = True
            return True
        return False

    def get_rect(self) -> pygame.Rect:
        """Return the  rectangle for collision/proximity testing."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_distance_to_player(self, player: Player) -> float:
        """Return the Euclidean distance between this lever's centre and the
        player's centre.

        Args:
            player: The player entity.

        Returns:
            Distance in world pixels.
        """
        chest_center_x = self.x + self.width//2

        chest_center_y= self.y + self.height// 2
        player_center_x= player.x + player.width// 2
        player_center_y= player.y + player.height// 2
        
        dx = chest_center_x - player_center_x
        dy = chest_center_y - player_center_y

        return math.sqrt(dx*dx + dy*dy)

    def is_near_player(self,player: Player) -> bool:
        """Return True if the player is within the  range

        Args:
            player:The player entity.
        """
        return self.get_distance_to_player(player) <= self.proximity_distance

    def is_touching_player(self,player: Player) -> bool:
        """
        Return True if player within the interaction range.

        Args:
            player: The player entity.
        """
        return self.get_distance_to_player(player)<= self.interaction_distance

    def update(self, player: Player, dt: float, keys: pygame.key.ScancodeWrapper |None = None) -> bool:
        """Tick the lever logic.  Currently always returns False.

        Args:
            player: The player entity.
            dt: Delta time in milliseconds.
            keys: Keyboard state (reserved for future interaction logic).

        Returns:
            False).
        """
        return False