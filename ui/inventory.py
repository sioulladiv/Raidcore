"""Player inventory: stores up to 8 weapon/item slots and renders the HUD bar."""
from __future__ import annotations


from entities.player import Player
from world.camera import Camera


class inventory:
    """
    8-slot item inventory with HUD rendering.

    Items are stored as ``{'item': object | None, 'slot': int}`` dicts.
    The active slot index drives which inventory image is displayed in the
    bottom-centre of the screen.
    """
    def __init__(self) -> None:
        """Initialise an empty 8-slot inventory."""

        #inventory with 8 slots total
        self.items = [{'item': None, 'slot':i} for i in range(8)]  
        self.active = True
        self.x = 0
        self.y = 0

        # image path for inventory bar
        self.image = f"Dungeon/frames/inventory.png"
        self.slot = 0
        self.images = []
        self._icon_cache = {}


        # Load each individual inventory slot image for when active
        for i in range(8):

            self.images.append(f"Dungeon/frames/inventory ({i+1}).png")

    def set_active_slot(self, slot_index: int) -> None:
        """Set the currently displayed slot index.

        Args:
            slot_index: Zero-based slot index; out-of-range values default to 0.
        """

        # validate slot index and set active slot, default is 0 if out of range
        if 0 <= slot_index < len(self.images):
            self.slot = slot_index
        else:
            self.slot = 0

    def __len__(self) -> int:
        """Return the total number of slots (always 8)."""
        return len(self.items)

    def __getitem__(self, index: int) -> dict:
        """Return the slot dict at *index* (``{'item': ..., 'slot': int}``)."""
        item = self.items[index]
        return item

    def add_item(self, item: object, slot: int) -> None:
        """Place *item* into the specified slot.

        Args:
            item: Any weapon or item object.
            slot: Zero-based slot index.
        """
        if 0 <= slot < len(self.items):
            self.items[slot]['item'] = item
        

    def drop_item(self, slot: int) -> None:
        """Remove the item in the specified slot.

        Args:
            slot: Zero-based slot index to clear.
        """
        if 0 <= slot < len(self.items):
            self.items[slot]['item'] = None

    def __repr__(self) -> str:
        """Return a debug-friendly string listing all slot contents."""

        # Create a string representation of the inventory showing each slot and its item
        items_str = ', '.join(f"{i['slot']}: {i['item']}" for i in self.items)
        return f"Inventory({items_str})"

    def find_slot(self, item: object) -> int:
        """Return the slot index that holds *item*, or -1 if not found.

        Args:
            item: The item object to search for.
        """
        # iterate through inventory slots to find one that contains specified item
        for slot in self.items:
            if slot['item'] == item:
                return slot['slot']
        return -1

    def draw(self, screen: object, player: Player, camera: Camera, display_ratio: float = 1.0) -> None:
        """Render the inventory bar at the bottom-centre of the screen.

        Scales the active slot image to fit the viewport.

        Args:
            screen: Pygame display surface.
            player: Player entity (currently unused, reserved for future).
            camera: Active camera (currently unused, reserved for future).
            display_ratio: Additional scale multiplier applied on top of the
                auto-scaling (default 1.0).
        """
        import pygame

        # Only draw if inventory is active; this allows toggling the HUD on or off
        if self.active:
            # load image for current actuve slot if slot index is valid, otherwise skip drawing
            img = pygame.image.load(self.images[self.slot]).convert_alpha()

            screen_w,screen_h = screen.get_width(),screen.get_height()
            orig_w, orig_h = img.get_width(), img.get_height()

            # scale inventory bar to fit screen width with a maximum scale limit
            max_scale = min(screen_w / orig_w, screen_h / orig_h, 4) 
            scale_factor = min(1.0 * max_scale, 4)
            scaled_width = int(orig_w * scale_factor)
            scaled_height = int(orig_h * scale_factor)

            # Use smooth scaling for better quality when scaling up. regular scaling when no scaling needed
            if scale_factor > 1: img_scaled = pygame.transform.scale(img, (scaled_width, scaled_height))  
            else: img_scaled = pygame.transform.smoothscale(img, (scaled_width, scaled_height))

            # Center the inventory bar at bottom of the screen
            x = screen_w//2 - img_scaled.get_width() // 2
            y = screen_h*(4/5) - img_scaled.get_height() // 2
            screen.blit(img_scaled, (x, y))

            # Draw item icons in each slot so equipped/owned items are visible.
            cols = 8
            cell_w = scaled_width / cols
            cell_h = scaled_height
            padding =max(2, int(min(cell_w, cell_h) * 0.18))
            
            # Iterate through each inventory slot and draw the item icon if present
            for slot_index, slot_data in enumerate(self.items):
                item_obj = slot_data.get('item')
                if item_obj is None:continue
                icon = self._get_item_icon(item_obj)
                if icon is None:continue

                
                src_w, src_h = icon.get_width(), icon.get_height()
                if src_w <= 0 or src_h <= 0:
                    continue

                # Calculate the maximum drawable area for the icon within the slot, accounting for padding
                max_w = max(1, int(cell_w) - padding * 2)
                max_h = max(1, int(cell_h) - padding * 2)

                scale = min(max_w / src_w, max_h / src_h)
                draw_w =max(1, int(src_w*scale))
                draw_h =max(1, int(src_h*scale))


                # Smoothly scale the icon to fit within the slot while keeping aspect ratio, then center it in slot
                scaled_icon = pygame.transform.smoothscale(icon, (draw_w, draw_h))
                cell_x = x + int(slot_index * cell_w)
                icon_x = cell_x + (int(cell_w) - draw_w) // 2
                icon_y = int(y) + (int(cell_h) - draw_h) // 2
                screen.blit(scaled_icon, (icon_x, icon_y))

    def _get_item_icon(self, item_obj: object) -> object | None:
        """Return a pygame surface for an inventory item icon.

        Items are expected to expose either:
        - ``image`` as a pygame.Surface, or
        - ``image`` as a path string to load.
        """
        import pygame

        item_image = getattr(item_obj, 'image', None)
        if item_image is None:
            return None

        # if image is path string, load and cache it, if already a surface, return directly, otherwise return None
        if isinstance(item_image, str):
            if item_image in self._icon_cache:
                return self._icon_cache[item_image]
            try:
                # Load the image from the file path and cache it for future use
                icon_surface = pygame.image.load(item_image).convert_alpha()
                self._icon_cache[item_image] = icon_surface
                return icon_surface
            except (pygame.error, FileNotFoundError):
                return None

        # if it's already a pygame surface, return it directly
        if hasattr(item_image, 'get_width') and hasattr(item_image, 'get_height'):
            return item_image

        return None

