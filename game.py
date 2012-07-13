#!/usr/bin/env python

import pygame
import random
import euclid

class Vehicle(pygame.sprite.DirtySprite):
    def __init__(self, image):
        super(Vehicle, self).__init__()
        self.image = image
        self.position = euclid.Vector2(0, 0)
        self.velocity = euclid.Vector2(0, 0)
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        
    def update(self):
        self.position += self.velocity #need to include time elapsed here or the speed will depend on frame rate
        self.rect.center = self.position
        
        
class Player(pygame.sprite.DirtySprite):
    def __init__(self, image):
        super(Player, self).__init__()
        self.image = pygame.image.load(image)
        self.position = euclid.Vector2(0, 0)
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.host = None
        
    def update(self):
        self.rect.center = self.position
        
        if self.host is not None:
            if self.host.dead:
                self.dispossess()
            else:
                self.host.position = euclid.Vector2(self.position.x, self.position.y)
        
    def possess(self, person):
        self.host = person
        
    def dispossess(self):
        self.host = None
        
class Person(pygame.sprite.DirtySprite):
    def __init__(self, image, deadimage, deathsound):
        super(Person, self).__init__()
        self.image = pygame.image.load(image)
        self.deadimage = pygame.image.load(deadimage)
        self.position = euclid.Vector2(0, 0)
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.dead = False
        self.deathsound = deathsound
        
    def update(self):
        self.rect.center = self.position
        
    def kill(self):
        self.dead = True
        self.deathsound.play()
        self.image = self.deadimage
        
def offscreen(sprite, screen):
    if sprite.position.x < -sprite.rect.width:
        return True
        
    if sprite.position.y < -sprite.rect.height:
        return True
        
    if sprite.position.x > screen.get_width() + sprite.rect.width:
        return True
        
    if sprite.position.y > screen.get_height() + sprite.rect.height:
        return True

def run():
    #constants
    WIDTH = 1024
    HEIGHT = 768
    
    #init
    randy = random.Random()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    pygame.mixer.init()
    splat = pygame.mixer.Sound("sound/splat.ogg")
    
    carimage = pygame.image.load('images/car.png')
    carGroup = pygame.sprite.RenderUpdates()
    car = None
    
    player = Player('images/player.png')
    player.position = euclid.Vector2(screen.get_width() / 4 + 20, screen.get_height() / 4 + 20)
    playerGroup = pygame.sprite.RenderUpdates(player)
    
    person = Person('images/person.png', 'images/deadperson.png', splat)
    person.position = euclid.Vector2(screen.get_width() / 4, screen.get_height() / 4)
    personGroup = pygame.sprite.RenderUpdates(person)
    
    bail = False
    possessToggle = False
    while not bail:
        deltat = clock.tick(60)
        
        #input
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    bail = True
                    break
                elif event.key == pygame.K_SPACE:
                    possessToggle = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    possessToggle = False
                
        pygame.event.clear()
        
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_a]:
            player.position.x -= 1
            
        if pressed[pygame.K_d]:
            player.position.x += 1
            
        if pressed[pygame.K_w]:
            player.position.y -= 1
            
        if pressed[pygame.K_s]:
            player.position.y += 1
                
        #sim
        if car is None:
            car = Vehicle(carimage)
            car.velocity = euclid.Vector2(3, 3)
            carGroup.add(car)
            
        #car.velocity += (random.randint(-1, 1), random.randint(-1, 1))
        
        if offscreen(car, screen):
            car = None

        carGroup.update()
        playerGroup.update()
        personGroup.update()
        if not person.dead:
            collisions = pygame.sprite.spritecollide(person, carGroup, False)
            if len(collisions) > 0:
                person.kill()
                
            
            if possessToggle:
                if player.host is None:
                    collisions = pygame.sprite.spritecollide(player, personGroup, False)
                    #todo multiple people
                    if len(collisions) > 0:
                        player.possess(person)
                    else:
                        pass
                else:
                    player.dispossess()
                    
                possessToggle = False    
        
        #render
        screen.fill((0,0,0))
        carGroup.draw(screen)
        playerGroup.draw(screen)
        personGroup.draw(screen)
        pygame.display.flip()
    
    pygame.display.quit()
    pygame.mixer.quit()

if __name__ == '__main__':
    run()