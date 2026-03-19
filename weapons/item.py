
"""Base class for all equippable items in the gamen """


class Items:
    """Abstract base for weapons and other equippable items.

    Subclasses (e.g. :class:`~weapons.gun.Gun`,
    :class:`~weapons.knife.Knife`) extend this with attack logic.   
    """

    def __init__(self, x: float, y: float, item: str, height: int = 16, width: int = 16) -> None:
        """Initialise an item at the given position.

        Args:
            x: World x-coordinate.
            y: World y-coordinate.
            item: String identifier / type name of the item.
            height: Sprite height in pixels (default 16).
            width: Sprite width in pixels (default 16).
        """
        self.type = item
        self.x = x
        self.y = y
        self.height = height
        self.width = width