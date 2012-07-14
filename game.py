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
        self.direction = euclid.Vector2(0, 0)
        self.speed = 5
        
    def update(self):
        self.position += self.direction * self.speed
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
        self.goal = None
        self.speed = 1
        
    def update(self):
        if (not self.dead) and (self.goal is not None):
            velocity = (self.goal - self.position).normalize() * self.speed
            self.position += velocity
            
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

        
class Game(object):
    #constants
    WIDTH = 1024
    HEIGHT = 768
    SPAWN_PEOPLE_BELOW = 4
    SPAWN_CARS_BELOW = 2
        
    def __init__(self):
        self.screen = pygame.display.set_mode((Game.WIDTH, Game.HEIGHT))
        #self.screen = pygame.display.set_mode((Game.WIDTH, Game.HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        
        pygame.mixer.init()
        self.splat = pygame.mixer.Sound("sound/splat.ogg")
        
        self.background = pygame.image.load("images/background.png")
        
        self.carimage = pygame.image.load('images/car.png')
        self.carGroup = pygame.sprite.RenderUpdates()
        
        self.player = Player('images/player.png')
        self.player.position = euclid.Vector2(self.screen.get_width() / 2 + 20, self.screen.get_height() / 2 + 20)
        self.playerGroup = pygame.sprite.RenderUpdates(self.player)
        
        self.people = list()
        
        #person = Person('images/person.png', 'images/deadperson.png', self.splat)
        #person.position = euclid.Vector2(self.screen.get_width() / 2, self.screen.get_height() / 2)
        #self.people.append(person)
        
        #person = Person('images/person.png', 'images/deadperson.png', splat)
        #person.position = euclid.Vector2(self.screen.get_width() / 2, self.screen.get_height() / 4)
        #self.people.append(person)
        
        self.personGroup = pygame.sprite.RenderUpdates(self.people)
        
        self.possessToggle = False
        self.bail = False
    
    def run(self):
        clock = pygame.time.Clock()
        self.possessToggle = False
        self.bail = False
        while not self.bail:
            elapsed = clock.tick(60)
            if elapsed > 32:
                print("frametime:%(elapsed)03d" % {'elapsed': elapsed})
            
            #input
            self.processInput()
                    
            #sim
            self.carGroup.update()
            self.playerGroup.update()
            self.personGroup.update()
            
            self.runCars()
            self.runPeople()
            self.runPlayer()
            
            self.spawnPeople()
            self.spawnCars()
            
            #render
            self.screen.blit(self.background, (0, 0))
            self.carGroup.draw(self.screen)
            self.playerGroup.draw(self.screen)
            self.personGroup.draw(self.screen)
            pygame.display.flip()
        
        #clean up before exit
        pygame.display.quit()
        pygame.mixer.quit()
        
    def runPeople(self):
        for person in self.people:
            if not person.dead:
                collisions = pygame.sprite.spritecollide(person, self.carGroup, False)
                if len(collisions) > 0:
                    person.kill()
                elif offscreen(person, self.screen):
                    self.personGroup.remove(person)
                    self.people.remove(person)
            else:
                pass
            
    def runCars(self):
        for car in self.carGroup.sprites():
            if offscreen(car, self.screen):
                self.carGroup.remove(car)
            
    def runPlayer(self):
        if self.possessToggle:
            if self.player.host is None:
                collisions = pygame.sprite.spritecollide(self.player, self.personGroup, False)
                if len(collisions) > 0:
                    self.player.possess(collisions[0])
                else:
                    pass
            else:
                self.player.dispossess()
                
            self.possessToggle = False
        else:
            pass
        
    def spawnPeople(self):
        aliveCount = 0
        for person in self.people:
            if not person.dead:
                aliveCount += 1
            else:
                pass
            
        if aliveCount < Game.SPAWN_PEOPLE_BELOW:
            self.spawnPerson()
            
    def spawnPerson(self):
        #randomly choose top or bottom for y
        y = random.choice([0, self.screen.get_height()])
        goalY = self.screen.get_height() + 100 if y == 0 else -100
        
        #pick random x value
        x = random.randint(10, self.screen.get_width() - 10)
        
        #spawn person a x y
        person = Person('images/person.png', 'images/deadperson.png', self.splat)
        person.position = euclid.Vector2(x, y)
        person.goal = euclid.Vector2(x, goalY)
        self.people.append(person)
        self.personGroup.add(person)
        
    def spawnCars(self):
        if len(self.carGroup.sprites()) < Game.SPAWN_CARS_BELOW:
            car = Vehicle(self.carimage)
            #pick a random side (left or right)
            x = random.choice([0, self.screen.get_width()])
            xVelocity = 3 if x == 0 else -3
            y = self.screen.get_height() / 2
            y += 20 if x == 0 else -20
            car.velocity = euclid.Vector2(xVelocity, 0)
            car.position = euclid.Vector2(x, y)
            self.carGroup.add(car)
        
    def processInput(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.bail = True
                    break
                elif event.key == pygame.K_SPACE:
                    self.possessToggle = True
                else:
                    pass
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.possessToggle = False
                else:
                    pass
            else:
                pass
            
                
        pygame.event.clear()
        
        self.player.direction = euclid.Vector2(0, 0)
        
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_a]:
            self.player.direction.x -= 1
            
        if pressed[pygame.K_d]:
            self.player.direction.x += 1
            
        if pressed[pygame.K_w]:
            self.player.direction.y -= 1
            
        if pressed[pygame.K_s]:
            self.player.direction.y += 1
                

if __name__ == '__main__':
    Game().run()