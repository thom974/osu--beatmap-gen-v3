from pygame import *

init()
size = width, height = 1000, 700
screen = display.set_mode(size)
button = 0
BLACK = (0, 0, 0)
RED = (255, 0, 0)
blue = (0,0,255)
green = (0,255,0)
# define font
myFont = font.SysFont("Times New Roman", 30)

# states in the game

state_menu = 0
state_game = 1
state_help = 2
state_quit = 3

def drawMenu(screen, button, mx, my):
    draw.rect(screen, RED, (0, 0, width, height))
    blockwidth = width/3
    blockheight = height/7
    draw.rect(screen, green, (blockwidth, blockheight, blockwidth, blockheight))


def drawGame(screen, button, mx, my):
    draw.rect(screen, RED, (0, 0, width, height))


def drawHelp(screen, button, mx, my):
    draw.rect(screen, RED, (0, 0, width, height))


running = True
myClock = time.Clock()

state = state_menu
mx = my = 0
# Game Loop
while running:
    for e in event.get():  # checks all events that happen
        if e.type == QUIT:
            running = False
        if e.type == MOUSEBUTTONDOWN:
            mx, my = e.pos
            button = e.button
    if state == state_menu:
        drawMenu(screen, button, mx, my)
    elif state == state_game:
        drawGame(screen, button, mx, my)
    elif state == state_help:
        drawHelp(screen, button, mx, my)
    else:
      running = False

    display.flip()

    myClock.tick(60)  # waits long enough to have 60 fps

quit()