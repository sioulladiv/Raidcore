from __future__ import annotations

import pygame
import math

from entities.player import Player


class Chest:
    """
    An interactable chest that the player can open to receive items or story
    content (e.g. the letter animation on level 1).

    """
    def __init__(self, x: float, y: float, task_type: str, height: int = 32, width: int = 32) -> None:
        """
        Create a chest.
        Args:
            x: x-coordinate of the top-left corner.
            y: y-coordinate of the top-left corner.
            task_type: Type tag (e.g. treasure).
            height: Sprite height in pixels (default 32).
            width: Sprite width in pixels (default 32).
        """
        self.type = task_type
        self.x = x
        self.y= y

        self.height = height
        self.width = width
        self.proximity_distance= 32
        self.interaction_distance= 32

    

    def get_rect(self) -> pygame.Rect:
        """Return the bounding rectangle for collision testing."""

        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_distance_to_player(self, player: Player) -> float:
        """Return the Euclidean distance between this chest's centre and the
        player's centre.

        Args:
            player: The player entity.

        Returns:
            Distance in world pixels.

        """

        chest_center_x = self.x + self.width// 2
        chest_center_y = self.y + self.height// 2
        player_center_x = player.x + player.width// 2
        player_center_y = player.y + player.height// 2
        
        dx = chest_center_x - player_center_x
        dy = chest_center_y - player_center_y
        return math.sqrt(dx * dx + dy * dy)

    def is_near_player(self, player: Player) -> bool:
        """Return True if the player is within the proximity range

        Args:
            player: The player entity.
        """
        return self.get_distance_to_player(player) <= self.proximity_distance

    def is_touching_player(self, player: Player) -> bool:
        """Return True if the player is within the interaction range.

        Args:

            player: The player entity.
        """
        return self.get_distance_to_player(player) <= self.interaction_distance

    def update(self, player: Player, dt: float, keys: pygame.key.ScancodeWrapper | None = None)-> bool:
        """Tick the chest logic.  Currently always returns False.

        Args:
            player: The player entity.
            dt: Delta time in milliseconds.
            keys: Keyboard state (reserved for future interaction logic).

        Returns:
            False (no state change this frame).
        """
        return False