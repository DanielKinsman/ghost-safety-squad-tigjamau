#!/usr/bin/env python

import pygame
import random
import euclid
import math

class CrashPredictor(pygame.sprite.Sprite):
    def __init__(self, vehicle):
        super(CrashPredictor, self).__init__()
        self.vehicle = vehicle
        self.image = pygame.image.load('images/collider.png')
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        
    def update(self):
        xOff = (self.vehicle.image.get_width() / 2) + (self.image.get_width() / 2)
        if self.vehicle.velocity.x > 0:
            offset = euclid.Vector2(xOff, 0)
        else:
            offset = euclid.Vector2(-xOff, 0)
            
        self.rect.center = self.vehicle.position + offset

class Vehicle(pygame.sprite.DirtySprite):
    def __init__(self, image, maxVelocity):
        super(Vehicle, self).__init__()
        self.image = image
        self.position = euclid.Vector2(0, 0)
        self.velocity = euclid.Vector2(0, 0)
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.crashPredictor = CrashPredictor(self)
        self.maxVelocity = maxVelocity
        
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
    def __init__(self, image, stepLeftImage, stepRightImage, deadimage, deathsound):
        super(Person, self).__init__()
        self.baseimage = pygame.image.load(image)
        self.baseImageStepLeft = pygame.image.load(stepLeftImage)
        self.baseImageStepRight = pygame.image.load(stepRightImage)
        self.image = None
        self.deadimage = pygame.image.load(deadimage)
        self.position = euclid.Vector2(0, 0)
        self.rect = pygame.Rect(0, 0, self.baseimage.get_width(), self.baseimage.get_height())
        self.dead = False
        self.deathsound = deathsound
        self.goal = None
        self.speed = 1
        self.currentDirection = euclid.Vector2(0, 1)
        self.animationFrameCount = 0
        self.currentBaseImage = self.baseimage
        
    def update(self):
        if (not self.dead) and (self.goal is not None):
            self.currentDirection = (self.goal - self.position).normalize()
            velocity = self.currentDirection * self.speed
            self.position += velocity
        
            angle = math.degrees(self.currentDirection.angle(euclid.Vector2(0, 1)))
            
            # bit of a hack
            if self.currentDirection.x < 0:
                angle = -angle
            
            #frame = random.choice([self.baseimage, self.baseImageStepLeft, self.baseImageStepRight])
            self.animationFrameCount += 1
            if self.animationFrameCount % 30 == 0:
                self.animationFrameCount = 0
                if self.currentBaseImage is self.baseImageStepLeft:
                    self.currentBaseImage = self.baseImageStepRight
                else:
                    self.currentBaseImage = self.baseImageStepLeft
            
            self.image = pygame.transform.rotate(self.currentBaseImage, angle)
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
        
def vectorApproximatelyEqual(a, b, min_delta):
    if abs(a.x - b.x) >= min_delta:
        return False
        
    if abs(a.y - b.y) >= min_delta:
        return False
        
    return True

        
class Game(object):
    #constants
    VECTOR_COMPARE_MIN_DELTA = 0.0001
    WIDTH = 1024
    HEIGHT = 768
    SPAWN_PEOPLE_BELOW = 1
    SPAWN_CARS_BELOW = 4
    CAR_VELOCITY = 10
    TRUCK_VELOCITY = 6
    MOTORBIKE_VELOCITY = 15
    CAR_SPAWN_DELAY_AVERAGE = 1500
        
    def __init__(self):
        self.screen = pygame.display.set_mode((Game.WIDTH, Game.HEIGHT))
        #self.screen = pygame.display.set_mode((Game.WIDTH, Game.HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        
        pygame.mixer.init()
        self.splat = pygame.mixer.Sound("sound/splat.ogg")
        
        self.background = pygame.image.load("images/background.png")
        
        self.carimage = pygame.image.load('images/car.png')
        self.truckimage = pygame.image.load('images/truck.png')
        self.motorbikeimage = pygame.image.load('images/motorbike.png')
        self.carGroup = pygame.sprite.RenderUpdates()
        self.crashPredictGroup = pygame.sprite.RenderUpdates()
        
        self.carsSpawnDelay = Game.CAR_SPAWN_DELAY_AVERAGE
        self.carSpawnLast = 0
        
        self.player = Player('images/player.png')
        self.player.position = euclid.Vector2(self.screen.get_width() / 2 + 20, self.screen.get_height() / 2 + 20)
        self.playerGroup = pygame.sprite.RenderUpdates(self.player)
        
        self.people = list()
        self.personGroup = pygame.sprite.RenderUpdates(self.people)
        
        self.possessToggle = False
        self.bail = False
    
    def run(self):
        clock = pygame.time.Clock()
        self.possessToggle = False
        self.screen.blit(self.background, (0, 0))
        
        self.bail = False
        while not self.bail:
            elapsed = clock.tick(60)
            #if elapsed > 32:
            #    print("frametime:%(elapsed)03d" % {'elapsed': elapsed})
            
            #input
            self.processInput()
                    
            #sim
            self.spawnPeople()
            self.spawnCars()
            
            self.carGroup.update()
            self.playerGroup.update()
            self.personGroup.update()
            self.crashPredictGroup.update()
            
            self.runCars()
            self.runPeople()
            self.runPlayer()
            
            #render
            self.personGroup.clear(self.screen, self.background)
            self.carGroup.clear(self.screen, self.background)
            self.playerGroup.clear(self.screen, self.background)
            #self.crashPredictGroup.clear(self.screen, self.background) #debug only
            
            self.personGroup.draw(self.screen)
            self.carGroup.draw(self.screen)
            self.playerGroup.draw(self.screen)
            #self.crashPredictGroup.draw(self.screen) #debug only
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
                
            #slow down if there's an obstacle ahead
            collisions = pygame.sprite.spritecollide(car.crashPredictor, self.carGroup, False)
            collisions.extend(pygame.sprite.spritecollide(car.crashPredictor, self.personGroup, False))
            
            if len(collisions) > 0 and ((collisions[0] is not car) or (len(collisions) > 1)):
                car.velocity.x *= 0.9
            elif car.velocity.magnitude() < car.maxVelocity:
                car.velocity.x *= 1.1
                
                #if the car stops, give it a little push. This is a bit hackish, eh?
                if car.velocity.magnitude() < 1:
                    car.velocity.x = -1 if car.position.y > self.screen.get_height() / 2 else 1
                
                
            
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
        person = Person('images/person.png', 'images/personstepleft.png', 'images/personstepright.png', 'images/deadperson.png', self.splat)
        person.position = euclid.Vector2(x, y)
        person.goal = euclid.Vector2(x, goalY)
        self.people.append(person)
        self.personGroup.add(person)
        
    def spawnCars(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.carSpawnLast
        if elapsed < self.carsSpawnDelay:
            return
        
        self.carsSpawnDelay = Game.CAR_SPAWN_DELAY_AVERAGE + random.randint(-500, +500)
        self.carSpawnLast = now
        
        if len(self.carGroup.sprites()) < Game.SPAWN_CARS_BELOW:
            #car or truck?
            vehicleType = random.choice(['car', 'truck', 'motorbike'])
            if vehicleType == 'car':
                wheels = Vehicle(self.carimage, Game.CAR_VELOCITY)
            elif vehicleType == 'truck':
                wheels = Vehicle(self.truckimage, Game.TRUCK_VELOCITY)
            else:
                wheels = Vehicle(self.motorbikeimage, Game.MOTORBIKE_VELOCITY)
            
            #pick a random side (left or right)
            x = random.choice([-100, self.screen.get_width() + 100])
            y = self.screen.get_height() / 2
            
            if x <= 0:
                xVelocity = wheels.maxVelocity
                y += -200
            else:
                xVelocity = -wheels.maxVelocity
                y += 200
                wheels.image = pygame.transform.flip(wheels.image, True, False)
            
            wheels.velocity = euclid.Vector2(xVelocity, 0)
            wheels.position = euclid.Vector2(x, y)
            wheels.update()
            
            #see if there is another (non-dead) sprite occupying the space, if so, do nothing
            collisions = pygame.sprite.spritecollide(wheels, self.carGroup, False)
            if len(collisions) == 0:
                self.carGroup.add(wheels)
                self.crashPredictGroup.add(wheels.crashPredictor)
            else:
                wheels.crashPredictor.vehicle = None
                wheels.crashPredictor = None
        
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