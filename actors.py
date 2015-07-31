import random
import itertools
import pygame as pg

import prepare
import tools


SPRITE_SIZE = (32, 36)


class RPGSprite(pg.sprite.DirtySprite):
    """Base class for player and AI sprites."""
    def __init__(self, pos, speed, name, facing="DOWN", *groups):
        super(RPGSprite, self).__init__(*groups)
        self.speed = speed
        self.name = name
        self.direction = facing
        self.old_direction = None  
        self.direction_stack = []  
        self.redraw = True  
        self.animate_timer = 0.0
        self.animate_fps = 10.0
        self.walkframes = None
        self.walkframe_dict = self.make_frame_dict(self.get_frames(name))
        self.adjust_images()
        self.rect = self.image.get_rect(center=pos)
        self.hit_rect = pg.Rect(0, 0, 20, 20)
        self.hit_rect.midbottom = self.rect.midbottom
        self.dirty = 1

    def get_frames(self, character):
        """Get a list of all frames."""
        sheet = prepare.GFX["characters"][character]
        all_frames = tools.split_sheet(sheet, SPRITE_SIZE, 3, 4)
        return all_frames

    def make_frame_dict(self, frames):
        """Create a dictionary of animation cycles for each direction."""
        frame_dict = {}
        for i,direct in enumerate(prepare.DIRECTIONS):
            frame_dict[direct] = itertools.cycle([frames[i][0], frames[i][2]])
        return frame_dict

    def adjust_images(self, now=0):
        """Update the sprites walkframes as the sprite's direction changes."""
        if self.direction != self.old_direction:
            self.walkframes = self.walkframe_dict[self.direction]
            self.old_direction = self.direction
            self.redraw = True
        self.make_image(now)

    def make_image(self, now):
        """Update the sprite's animation as needed."""
        if self.redraw or now-self.animate_timer > 1000/self.animate_fps:
            self.image = next(self.walkframes)
            self.animate_timer = now
            self.dirty = 1
        self.redraw = False

    def add_direction(self, direction):
        """
        Add direction to the sprite's direction stack and change current
        direction.
        """
        if direction in self.direction_stack:
            self.direction_stack.remove(direction)
        self.direction_stack.append(direction)
        self.direction = direction

    def pop_direction(self, direction):
        """
        Remove direction from direction stack and change current direction
        to the top of the stack (if not empty).
        """
        if direction in self.direction_stack:
            self.direction_stack.remove(direction)
        if self.direction_stack:
            self.direction = self.direction_stack[-1]

    def update(self, now, screen_rect, obstacles):
        """Update image and position of sprite."""
        self.adjust_images(now)
        adjust_x = adjust_y = False
        if self.direction_stack:
            self.dirty = 1
            adjust_x = self.movement(obstacles, 0)
            adjust_y = self.movement(obstacles, 1)
            self.wrap_around(screen_rect)
        return adjust_x or adjust_y

    def wrap_around(self, screen_rect):
        """
        If the sprite leaves the screen, wrap it over to the opposite side
        of the map.
        """
        buffer = 10
        if self.rect.x+buffer >= screen_rect.right:
            self.rect.right = buffer
        elif self.rect.right-buffer <= screen_rect.x:
            self.rect.x = screen_rect.right-buffer
        if self.rect.y+buffer >= screen_rect.bottom:
            self.rect.bottom = buffer
        elif self.rect.bottom-buffer <= screen_rect.y:
            self.rect.y = screen_rect.bottom-buffer
        self.hit_rect.midbottom = self.rect.midbottom

    def movement(self, obstacles, i):
        """Move sprite and then check for collisions; adjust as necessary."""
        adjust = False
        direction_vector = prepare.DIRECT_DICT[self.direction]
        self.rect[i] += self.speed*direction_vector[i]
        self.hit_rect.midbottom = self.rect.midbottom
        collision = pg.sprite.spritecollideany(self, obstacles, 
                                               collided=tools.collide_other)
        while collision:
            adjust = True
            self.adjust_on_collision(self.hit_rect, collision, i)
            self.rect.midbottom = self.hit_rect.midbottom
            collision = pg.sprite.spritecollideany(self, obstacles, 
                                                  collided=tools.collide_other)
        return adjust

    def adjust_on_collision(self, rect_to_adjust, collide, i):
        """Adjust sprite's position if colliding with a solid block."""
        if rect_to_adjust[i] < collide.rect[i]:
            rect_to_adjust[i] = collide.rect[i]-rect_to_adjust.size[i]
        else:
            rect_to_adjust[i] = collide.rect[i]+collide.rect.size[i]
            
    def draw(self, surface):
        """Draw sprite to surface (not used if using group draw functions)."""
        surface.blit(self.image, self.rect)
        

class Player(RPGSprite):
    """This class will represent the user controlled character."""
    def __init__(self, pos, speed, name="warrior_m", facing="DOWN", *groups):
        super(Player, self).__init__(pos, speed, name, facing, *groups)

    def get_event(self, event):
        """Handle events pertaining to player control."""
        if event.type == pg.KEYDOWN:
            self.add_direction(event.key)
        elif event.type == pg.KEYUP:
            self.pop_direction(event.key)

    def add_direction(self, key):
        """Remove direction from stack if corresponding key is released."""
        if key in prepare.CONTROLS:
            super(Player, self).add_direction(prepare.CONTROLS[key])

    def pop_direction(self, key):
        """Add direction to stack if corresponding key is pressed."""
        if key in prepare.CONTROLS:
            super(Player, self).pop_direction(prepare.CONTROLS[key])


class AISprite(RPGSprite):
    """A non-player controlled sprite."""
    def __init__(self, pos, speed, name, facing, *groups):
        super(AISprite, self).__init__(pos, speed, name, facing, *groups)
        self.wait_range = (500, 2000)
        self.wait_delay = random.randint(*self.wait_range)
        self.wait_time = 0.0
        self.change_direction()

    def update(self, now, screen_rect, obstacles):
        """
        Choose a new direction if wait_time has expired or the sprite
        has collided with a solid tile.
        """
        if now-self.wait_time > self.wait_delay:
            self.change_direction(now)
        collided = super(AISprite, self).update(now, screen_rect, obstacles)
        if collided:
            self.change_direction(now)

    def change_direction(self, now=0):
        """
        Empty the stack and choose a new direction.  The sprite may also
        choose to go idle (choosing direction=None)
        """
        self.direction_stack = []
        direction = random.choice(prepare.DIRECTIONS+(None,))
        if direction:
            super(AISprite, self).add_direction(direction)
        self.wait_delay = random.randint(*self.wait_range)
        self.wait_time = now


class Obstacle(pg.sprite.DirtySprite):
    def __init__(self, pos, *groups):
        super(Obstacle, self).__init__(*groups)
        self.image = prepare.GFX["stone"]
        self.rect = self.image.get_rect(topleft=pos)
