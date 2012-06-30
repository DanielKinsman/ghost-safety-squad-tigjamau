#!/usr/bin/env python

import pygame
import random

class Vehicle(pygame.sprite.DirtySprite):
    def __init__(self, image):
        super(Vehicle, self).__init__()
        self.image = pygame.image.load(image)
        self.x = 0
        self.y = 0
        self.rect = pygame.Rect(0, 0, 50, 50)
        
    def update(self):
        self.rect.center = (self.x, self.y)
        
class Player(pygame.sprite.DirtySprite):
    def __init__(self, image):
        super(Player, self).__init__()
        self.image = pygame.image.load(image)
        self.x = 0
        self.y = 0
        self.rect = pygame.Rect(0, 0, 50, 50)
        
    def update(self):
        self.rect.center = (self.x, self.y)

def run():
    #constants
    WIDTH = 1024
    HEIGHT = 768
    
    #init
    randy = random.Random()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    car = Vehicle('images/car.png')
    car.x = screen.get_width() / 2
    car.y = screen.get_height() / 2
    carGroup = pygame.sprite.RenderPlain(car)
    
    player = Vehicle('images/player.png')
    player.x = screen.get_width() / 4
    player.y = screen.get_height() / 4
    playerGroup = pygame.sprite.RenderPlain(player)
    
    pygame.mixer.init()
    splat = pygame.mixer.Sound("sound/splat.ogg")
    
    dead = False
    bail = False
    while not bail:
        deltat = clock.tick(60)
        
        #input
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    bail = True
                    break
                
        pygame.event.clear()
        
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_a]:
            player.x -= 1
            
        if pressed[pygame.K_d]:
            player.x += 1
            
        if pressed[pygame.K_w]:
            player.y -= 1
            
        if pressed[pygame.K_s]:
            player.y += 1
                
        #sim
        car.x += random.randint(-1, 1)
        car.y += random.randint(-1, 1)

        carGroup.update()
        playerGroup.update()
        if not dead:
            collisions = pygame.sprite.spritecollide(player, carGroup, False)
            if len(collisions) > 0:
                splat.play()
                dead = True
        
        #render
        screen.fill((0,0,0))
        carGroup.draw(screen)
        playerGroup.draw(screen)
        pygame.display.flip()
    
    pygame.display.quit()
    pygame.mixer.quit()

if __name__ == '__main__':
    run()
