# Imports
import sys
import pygame
import csv
import math

#CASEY NOTES:
#Drawn line should be continuous
# anchor and fix UI elements

# in order to export that protocol actually what I can do is track the individual "cirles" dropped as "waypoints"
# now THATS a killer idea^



# Pygame Configuration
pygame.init()
fps = 300
fpsClock = pygame.time.Clock()
width, height = 1280, 720
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

font = pygame.font.SysFont('Arial', 20)

# Variables

# Our Buttons will append themself to this list
objects = []

# Initial color
drawColor = [255, 0, 0]
colorName = "Red"

# Initial brush size
brushSize = 3
brushSizeSteps = 3

# Minimum waypoint distance
MIN_WAYPOINT_DIST = 3

# Drawing Area Size
# Each brush stroke is a single unit of icing
plateSize = [127, 85]
canvasScale = 5
canvasSize = [plateSize[0]*canvasScale, plateSize[1]*canvasScale]

# Waypoints tracker
waypoints = []

# Button Class
class Button():
    def __init__(self, x, y, width, height, buttonText='Button', onclickFunction=None, onePress=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.onePress = onePress

        self.fillColors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }

        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.buttonSurf = font.render(buttonText, True, (20, 20, 20))

        self.alreadyPressed = False

        objects.append(self)

    def process(self):

        mousePos = pygame.mouse.get_pos()

        self.buttonSurface.fill(self.fillColors['normal'])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.fillColors['hover'])

            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.fillColors['pressed'])

                if self.onePress:
                    self.onclickFunction()

                elif not self.alreadyPressed:
                    self.onclickFunction()
                    self.alreadyPressed = True

            else:
                self.alreadyPressed = False

        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width/2 - self.buttonSurf.get_rect().width/2,
            self.buttonRect.height/2 - self.buttonSurf.get_rect().height/2
        ])
        screen.blit(self.buttonSurface, self.buttonRect)


# Changing the Color
def changeColor(color, name):
    global drawColor
    drawColor = color
    global colorName
    colorName = name

# Save the surface to the Disk
def save():
    clean_waypoints = []
    for waypt in waypoints:
        if waypt not in clean_waypoints:
            # do not store waypoints closer than 3 mm apart
            if len(clean_waypoints) > 0:
                waypt_x = waypt[2]
                waypt_y = waypt[3]
                waypt_x2 = clean_waypoints[len(clean_waypoints)-1][2]
                waypt_y2 = clean_waypoints[len(clean_waypoints)-1][3]
                dist = math.sqrt(((waypt_x2 - waypt_x) ** 2) + ((waypt_y2 - waypt_y) ** 2))
                if dist >= MIN_WAYPOINT_DIST:
                    clean_waypoints.append(waypt)
            else:
                clean_waypoints.append(waypt)
    with open('output_waypoints.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(clean_waypoints)

# Button Variables.
buttonWidth = 120
buttonHeight = 35

# Buttons and their respective functions.
buttons = [
    ['Red', lambda: changeColor([255, 0, 0], 'Red')],
    ['Blue', lambda: changeColor([0, 0, 255], 'Blue')],
    ['Green', lambda: changeColor([0, 255, 0], 'Green')],
    ['Yellow', lambda: changeColor([255, 255, 0], 'Yellow')],
    ['White', lambda: changeColor([255, 255, 255], 'White')],
    ['Save', save],
]

# Making the buttons
for index, buttonName in enumerate(buttons):
    Button(index * (buttonWidth + 10) + 10, 10, buttonWidth,
           buttonHeight, buttonName[0], buttonName[1])

# Canvas
canvas = pygame.Surface(canvasSize)
canvas.fill((250, 227, 171))

# Game loop.
lineId = -1
oldLineId = -1
old_dx = 0
old_dy = 0
while True:
    screen.fill((30, 30, 30))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONUP:
            # this is almost working right here, BUT the only problem is that it isn't incrementing the number quite right yet
            # its incrementing when we click on color buttons
            lineId+=1

    # Drawing the Buttons
    for object in objects:
        object.process()

    # Draw the Canvas at the center of the screen
    x, y = screen.get_size()
    screen.blit(canvas, [x/2 - canvasSize[0]/2, y/2 - canvasSize[1]/2])

    # Drawing with the mouse
    if pygame.mouse.get_pressed()[0]:

        mx, my = pygame.mouse.get_pos()

        # Calculate Position on the Canvas
        dx = mx - x/2 + canvasSize[0]/2
        dy = my - y/2 + canvasSize[1]/2

        pygame.draw.circle(
            canvas,
            drawColor,
            [dx, dy],
            brushSize,
        )

        # linking dots:
        # since we never delete colors, as long as current lineId is the same as the last lineID used by the last waypoints 
        # made, draw a line between this dot and the last dot
        if lineId != -1 and lineId == oldLineId:
            # start linking the dots
            pygame.draw.line(
                canvas,
                drawColor,
                [old_dx, old_dy],
                [dx, dy],
                width=brushSize,
            )

        # start the dot tracking
        if lineId == -1:
            lineId = 0

        # These waypoints will mark the labware center
        # validate that these are correct by running a protocol that moves the pipette in a circle or something?
        # only drop waypoints when were inside the canvas
        if (0 <= dx <= (canvasSize[0])) and (0 <= dy <= canvasSize[1]):
            x_waypoint = round((dx/canvasScale - 127/2)) # bottom left = 0, bottom right = 127
            y_waypoint = round((85 - round(dy/canvasScale)) - 85/2) # top left = 0, bottom left = 85 
            waypoints.append( (lineId, colorName, x_waypoint, y_waypoint) )
        
        old_dx = dx
        old_dy = dy
        oldLineId = lineId

    # Reference Dot
    pygame.draw.circle(
        screen,
        drawColor,
        [100, 100],
        30,
    )

    pygame.display.flip()
    fpsClock.tick(fps)