#!/usr/bin/env python 
import sys
import random
import pygame as pg

# Importing prepare initializes the display.
import tools
import prepare
import actors
        

MAX_NPCS = 15

            
class App(object):
    """This is the main class that runs the program."""
    def __init__(self):
        self.screen = pg.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.bg = tools.tile_surface(prepare.SCREEN_SIZE, prepare.GFX["grass"])
        self.clock  = pg.time.Clock()
        self.fps = 60
        self.done = False
        self.all_sprites = pg.sprite.LayeredDirty()
        self.player = actors.Player(self.screen_rect.center, 3)
        self.obstacles = self.make_obstacles()
        self.npcs = self.make_npcs()
        self.all_sprites.add(self.player)
        self.all_sprites.clear(self.screen, self.bg)         
        
    def make_npcs(self):
        """Create a group of NPCs and add them to the all_sprites group."""
        size = prepare.TILE_SIZE
        width, height = prepare.SCREEN_SIZE
        characters = list(prepare.GFX["characters"].keys())
        npcs = pg.sprite.Group()
        while len(npcs) < MAX_NPCS:
            name = random.choice(characters)
            if name != self.player.name:
                pos = [random.randint(size, width-size*2), 
                       random.randint(size, height-size*2)]
                speed = random.randint(1,2)
                way = random.choice(prepare.DIRECTIONS)
                npc = actors.AISprite(pos, speed, name, way)
                if not pg.sprite.spritecollideany(npc, self.obstacles):
                    npc.add(self.all_sprites, npcs)
        return npcs

    def make_obstacles(self):
        """
        Create some arbitrary obstacles for the sprites to run in to.
        """
        size = prepare.TILE_SIZE
        width, height = prepare.SCREEN_SIZE
        walls = pg.sprite.Group()
        for i in range(0, width, size):
            if i < width//2-size*2 or i >= width//2+size*2:
                actors.Obstacle((i,-size), walls)
                actors.Obstacle((i,0), self.all_sprites, walls)
                actors.Obstacle((i,height-size), self.all_sprites, walls)
                actors.Obstacle((i,height), walls)
            if size*4 <= i < size*7 or width-size*4 > i >= width-size*7:
                actors.Obstacle((i,size*4), self.all_sprites, walls)
                actors.Obstacle((i,height-size*5), self.all_sprites, walls)
        for j in range(size, height-size, size):
            if j < height//2-size*2 or j >= height//2+size*2:
                actors.Obstacle((-size,j), walls)
                actors.Obstacle((0,j), self.all_sprites, walls)
                actors.Obstacle((width-size,j), self.all_sprites, walls)
                actors.Obstacle((width,j), walls)
            if size*5 <= j < size*7 or height-size*5 > j >= height-size*7:
                actors.Obstacle((size*6,j), self.all_sprites, walls)
                actors.Obstacle((width-size*7,j), self.all_sprites, walls)
        return walls

    def event_loop(self):
        """
        Process all events.
        Send event to player so that they can also handle the event.
        """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            self.player.get_event(event)

    def display_fps(self):
        """Show the program's FPS in the window handle."""
        template = "{} - FPS: {:.2f}"
        caption = template.format(prepare.CAPTION, self.clock.get_fps())
        pg.display.set_caption(caption)

    def update(self):
        """Update all actors."""
        now = pg.time.get_ticks()
        self.all_sprites.update(now, self.screen_rect, self.obstacles)
        for sprite in self.all_sprites:
            layer = self.all_sprites.get_layer_of_sprite(sprite)
            if layer != sprite.rect.bottom:
                self.all_sprites.change_layer(sprite, sprite.rect.bottom)

    def render(self):
        """
        Render all actors.
        Only update portions of the screen that change.
        """
        dirty = self.all_sprites.draw(self.screen)
        pg.display.update(dirty)

    def main_loop(self):
        """
        The main game loop for the whole program.
        Process events; update; render.
        """
        while not self.done:
            self.event_loop()
            self.update()
            self.render()
            self.clock.tick(self.fps)
            self.display_fps()


def main():
    """Create an App and start the program."""
    App().main_loop()
    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
