class inventory:
    def __init__(self):
        self.items = [{'item': None, 'slot': i} for i in range(8)]  # Single inventory with 8 slots
        self.active = True
        self.x = 0
        self.y = 0
        self.image = f"Dungeon/frames/inventory.png"
        self.devmode = False
        self.slot = 2
        self.images = []

        for i in range(8):
            self.images.append(f"Dungeon/frames/inventory ({i+1}).png")

    def set_active_slot(self, slot_index):
        if 0 <= slot_index < len(self.images):
            self.slot = slot_index
        else:
            self.slot = 0

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def add_item(self, item, slot):
        if 0 <= slot < len(self.items):
            self.items[slot]['item'] = item

    def drop_item(self, slot):
        if 0 <= slot < len(self.items):
            self.items[slot]['item'] = None

    def __repr__(self):
        items_str = ', '.join(f"{i['slot']}: {i['item']}" for i in self.items)
        return f"Inventory({items_str})"

    def find_slot(self, item):
        for slot in self.items:
            if slot['item'] == item:
                return slot['slot']
        return -1

    def draw(self, screen, player, camera, display_ratio=1.0):
        import pygame
        if self.active:
            img = pygame.image.load(self.images[self.slot]).convert_alpha()

            screen_w, screen_h = screen.get_width(), screen.get_height()
            orig_w, orig_h = img.get_width(), img.get_height()

            max_scale = min(screen_w / orig_w, screen_h / orig_h, 4) 
            scale_factor = min(1.0 * max_scale, 4)
            scaled_width = int(orig_w * scale_factor)
            scaled_height = int(orig_h * scale_factor)
            if scale_factor > 1:
                img_scaled = pygame.transform.scale(img, (scaled_width, scaled_height))  
            else:
                img_scaled = pygame.transform.smoothscale(img, (scaled_width, scaled_height))

            x = screen_w//2 - img_scaled.get_width() // 2
            y = screen_h*(4/5) - img_scaled.get_height() // 2
            screen.blit(img_scaled, (x, y))

            if getattr(self, 'devmode', False):
                grid_color = (0, 255, 0)
                cols, rows = 8, 1
                cell_w = scaled_width / cols
                cell_h = scaled_height / rows
                # Draw vertical lines (columns), including exterior edges
                for col in range(cols + 1):
                    gx = int(x + col * cell_w)
                    pygame.draw.line(screen, grid_color, (gx, y), (gx, y + scaled_height), 2)
                # Draw horizontal lines (rows), including exterior edges
                for row in range(rows + 1):
                    gy = int(y + row * cell_h)
                    pygame.draw.line(screen, grid_color, (x, gy), (x + scaled_width, gy), 2)

invent = inventory()
invent.add_item("Sword", 0)
invent.add_item("Shield", 1)

print(invent)