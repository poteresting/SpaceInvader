import os
import time
import random
from typing import List
from pynput import keyboard
from pynput.keyboard import Key

SCENE_WIDTH = 11
SCENE_HEIGHT = 15

class Position2D(object):
    def __init__(self, x, y, isDirection=False):
        super().__init__()
        self.__isDirection = isDirection
        self.__x = x
        self.__y = y

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, val):
        if self.__isDirection or 0 <= val < SCENE_WIDTH:
            self.__x = val

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, val):
        if self.__isDirection or 0 <= val < SCENE_HEIGHT:
            self.__y = val


class Vector2D(Position2D):
    def __init__(self, x, y):
        super().__init__(x, y, isDirection=True)


class Element(object):
    def __init__(self):
        super().__init__()
        self._position = Position2D(0, 0)
        self._char = '⬜️'

    @property
    def char(self):
        return self._char

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos

    def draw(self, scene):
        pos_x = int(self.position.x)
        pos_y = int(self.position.y)
        scene[pos_y][pos_x] = self.char

    def update(self, delta_time):
        pass

    def checkCollision(self, other):
        isCollision = False
        if int(other.position.x) == int(self.position.x) and \
                int(other.position.y) == int(self.position.y):
            isCollision = True
        return isCollision


class Wall(Element):
    def __init__(self, position):
        super().__init__()
        self._char = '🧱'
        self._position = position


class Explosion(Element):
    def __init__(self, position):  # constructor
        super().__init__()
        self._char = '💥'
        self._position = position
        self._life = 0.5

    def update(self, delta_time):
        self._life -= delta_time
        if self._life < 0:
            GameState.instance().elements.remove(self)


class MovableElement(Element):
    def __init__(self):
        super().__init__()
        self._char = '🛸'
        self._speed = 1.0
        self._direction = Position2D(x=0, y=0, isDirection=True)

    def update(self, delta_time):
        self.position.x += self._direction.x * self._speed * delta_time
        self.position.y += self._direction.y * self._speed * delta_time

    def stop(self):
        self._direction.x = 0
        self._direction.y = 0

    def left(self):
        self._direction.x = -1
        self._direction.y = 0

    def right(self):
        self._direction.x = 1
        self._direction.y = 0

    def up(self):
        self._direction.x = 0
        self._direction.y = -1

    def down(self):
        self._direction.x = 0
        self._direction.y = 1


class Rocket(MovableElement):
    def __init__(self, pos: Position2D, ch= '🔺', up=True):
        super().__init__()
        self.position = pos
        self._speed = 1.5
        self._char = ch
        if not up:
            self.char = '🔻'

    @property
    def char(self):
        return self._char

    @char.setter
    def char(self, ch):
        self._char = ch

    def update(self, delta_time):
        super().update(delta_time)
        if int(self.position.y) == 0:
            GameState.instance().elements.remove(self)

        if int(self.position.y) == 14 and scene[int(self.position.y)][int(self.position.x)] != Player().char: 
            GameState.instance().elements.remove(self)          


class Player(MovableElement):
    def __init__(self):
        super().__init__()
        self._speed = 1.5
        self._char = '🚀'
        self._patience = 0
    
    def resetPatience(self):
        self._patience = 2.5

    def fireRocket(self):
        rocket = Rocket(pos=Position2D(
            int(self.position.x), int(self.position.y)))
        rocket.up()
        GameState.instance().elements.append(rocket)
        self.resetPatience()

    def bottomCollision(self, other):
        if type(other) == Alien:
            isCollision = super(Player, self).checkCollision(other)
        return isCollision

    def update(self, deltaTime):
        super(Player, self).update(deltaTime)
        self._patience -= deltaTime


class Alien(MovableElement):
    def __init__(
        self,
        pos: Position2D,
        dir: Vector2D,
        listenerAliens
    ):
        super().__init__()
        self.position = pos
        self._direction = dir
        self._listenerAliens = listenerAliens
        self._speed = 0.5
        self._char = '👾'
        self._listenerAliens.append(self.notify)
        self._patience = 0
        self.resetPatience()

    def resetPatience(self):
        self._patience = 5 + random.random() * 5

    def notify(self, event):
        if type(event) == EventAlienDirection:
            self._direction = event.newDir
            self._position.y += 1
        elif type(event) == EventAlienFire:
            self.resetPatience()

    def checkBorder(self):
        isBorder = False
        if round(self.position.x) == 0 or round(self.position.x) == SCENE_WIDTH:
            isBorder = True
            self._direction.x *= -1
            event = EventAlienDirection(
                newDir= self._direction
            )
            for listener in self._listenerAliens:
                listener(event)
        return isBorder

    def fireRocket(self):
            event = EventAlienFire()
            for listener in self._listenerAliens:
                listener(event)
            if round(self.position.y) < SCENE_HEIGHT-1:
                rocket = Rocket(
                    pos=Position2D(int(self.position.x), int(self.position.y + 1)),
                    up = False
                )
                rocket.down()
                GameState.instance().elements.append(rocket)

    def update(self, deltaTime):
        super(Alien, self).update(deltaTime)

        islowerAlien = True
        for elem in GameState.instance().elements:
            if type(elem) == Alien:
                if elem != self:
                    if int(elem.position.x) == int(self.position.x):
                        if int(elem.position.y) > int(self.position.y):
                            islowerAlien = False
                            break

        self._patience -= deltaTime
        if self._patience < 0:
            self.resetPatience()
            if islowerAlien:
                self.fireRocket()


class EventAlien(object):
    def __init__(self):
        super().__init__()
        pass


class EventAlienDirection(EventAlien):
    def __init__(self, newDir):
        super().__init__()
        self.newDir = newDir


class EventAlienFire(EventAlien):
    def __init__(self):
        super().__init__()


class AlienShip(MovableElement):
    def __init__(self, pos: Position2D, dir: Vector2D):
        super().__init__()
        self.position = pos
        self._speed = 1
        self._char = '🛸'
        self._direction = dir

        self._patience = 0
        self.resetPatience()

    def resetPatience(self):
        self._patience = 2.5 + random.random() * 5

    def checkBorder(self):
        isBorder = False
        if round(self.position.x) == 0 or round(self.position.x) == SCENE_WIDTH:
            isBorder = True
            self._direction.x *= -1
        return isBorder

    def fireRocket(self):
        rocket = Rocket(
            pos=Position2D(int(self.position.x), int(self.position.y + 1)),
            up = False
        )
        rocket.char = '🔥'
        rocket.down()
        GameState.instance().elements.append(rocket)

    def update(self, deltaTime):
        super(AlienShip, self).update(deltaTime)
        self._patience -= deltaTime
        if self._patience < 0:
            self.resetPatience()
            self.fireRocket()


class GameState(object):
    def __init__(self):
        super().__init__()
        if self._instance is not None:
            raise Exception('Two Singleton instances not possible')
        self._instance = self

        posMiddle = Position2D(
            x=int(SCENE_WIDTH/2),
            y=int(SCENE_HEIGHT)-1
        )
        randDir = random.choice([-1.0, 1.0])

        self.player = Player()
        self.ship = AlienShip(pos= Position2D(int(SCENE_WIDTH/2), 1), dir= Vector2D(randDir, 0.0))
        self.player.position = posMiddle
        self.elements: List = [
            self.player,
            self.ship,
            Wall(position=Position2D(2, SCENE_HEIGHT-4)),
            Wall(position=Position2D(4, SCENE_HEIGHT-4)),
            Wall(position=Position2D(6, SCENE_HEIGHT-4)),
            Wall(position=Position2D(8, SCENE_HEIGHT-4))
        ]

        self.lives = 3
        self.score = 0
        self.bottomCollision = False

        self.listenerAliens = []

        for i in range(5):
            for j in range(2):
                self.elements.append(
                    Alien(
                        pos=Position2D(i+3, j+3),
                        dir=Vector2D(-randDir, 0.0),
                        listenerAliens=self.listenerAliens
                    )
                )

        self.isGameRunning = True
    _instance = None

    @staticmethod
    def instance():
        if GameState._instance is None:
            GameState._instance = GameState()
        return GameState._instance


elements = GameState.instance().elements
player = GameState.instance().player
ship = GameState.instance().ship

while GameState.instance().isGameRunning:
    cmdClear = 'clear'
    if os.name == 'nt':
        cmdClear = 'cls'
    os.system(cmdClear)

    scene = []
    for i in range(SCENE_HEIGHT):
        rows = []
        for j in range(SCENE_WIDTH):
            rows.append('⬛️')
        scene.append(rows)

    for elem in elements:
        elem.draw(scene)

    if GameState.instance().lives == 0 or GameState.instance().bottomCollision:
        scene[int(player.position.y)][int(player.position.x)] = '❌'

    sceneLines = []
    for line in scene:
        strLine = ''.join(line)
        sceneLines.append(strLine)
    strScene = '\n'.join(sceneLines)
    print(f'Score: {GameState.instance().score}  Lives:{GameState.instance().lives*"🚀"}')
    print(strScene)

    delay = 0.2
    timeStamp = time.time()

    with keyboard.Events() as events:
        keyPress = events.get(delay)

        if keyPress is not None:
            keyCode = keyPress.key
            if keyCode == Key.left:
                player.left()
            elif keyCode == Key.right:
                player.right()
            elif keyCode == Key.space:
                if player in elements and player._patience < 0:
                    player.fireRocket()
            elif keyCode == Key.esc:
                GameState.instance().isGameRunning = False
        else:
            player.stop()

    dt = delay - (time.time() - timeStamp)
    if dt > 0:
        time.sleep(dt)

    for elem in elements:
        if type(elem) == Alien:
            if elem.checkBorder():
                break
    for elem in elements:
        if type(elem) == AlienShip:
            if elem.checkBorder():
                break

    dt = time.time() - timeStamp
    for elem in elements:
        elem.update(dt)

    if GameState.instance().lives > 0 and player not in elements:
        player.position.x = int(SCENE_WIDTH/2)
        time.sleep(dt)
        elements.append(player)
        if ship not in elements:
            elements.append(ship)

    for elem in elements:
        if type(elem) == Alien:
            if player.bottomCollision(elem):
                GameState.instance().bottomCollision = True
                break
    
    if GameState.instance().lives == 0 or GameState.instance().bottomCollision:
        if scene[int(player.position.y)][int(player.position.x)] == '❌':
            print("👽 🇬 🇦 🇲 🇪  🇴 🇻 🇪 🇷 ❗")
            exit()
    
    if GameState.instance().lives > 0:
        won = True
        for elem in elements:
            if type(elem) == Alien or type(elem) == AlienShip:
                won = False
                break
        if won:
            print("🏆 🇾 🇴 🇺   🇼 🇴 🇳 ❗ 🌎")
            exit()

    isCollision = False
    for i in range(len(elements)):
        for j in range(i+1, len(elements)):
            if (type(elements[i]) != Rocket and type(elements[j]) == Rocket) or \
                (type(elements[j]) != Rocket and type(elements[i]) == Rocket):
                if (type(elements[i]) == Rocket and elements[i].char == '🔥' and type(elements[j]) == Alien) or \
                    (type(elements[j]) == Rocket and elements[j].char == '🔥' and type(elements[i]) == Alien):
                    break
                if elements[i].checkCollision(elements[j]):
                    pos = elements[i].position
                    if elements[i] == player or elements[j] == player:
                        GameState.instance().lives -= 1
                        GameState.instance().score -= 25
                    elif type(elements[i]) == Alien or type(elements[j]) == Alien:
                        GameState.instance().score += 5
                    elif type(elements[i]) == AlienShip or type(elements[j]) == AlienShip:
                        GameState.instance().score += 25
                    del elements[j]
                    del elements[i]
                    elements.append(Explosion(pos))
                    isCollision = True
                    break