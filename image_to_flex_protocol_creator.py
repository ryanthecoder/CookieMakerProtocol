# Imports
import sys
import pygame
import csv
import math

#CASEY NOTES:
# This app was hobbled together out of a cannibalized tutorial for a drawing game
# To use it, run `pip install pygame` followed by `python3 image_to_flex_protocol_creator.py`

# It works by mapping the drawn image to waypoints keyed by color
# It coorrelates those waypoints to a given line Id by mouse up/down events, so we can draw cleanly
# Saving the drawing outputs a output_waypoints.csv file usable as a run time parameter

# in order to export that protocol actually what I can do is track the individual "cirles" dropped as "waypoints"
# now THATS a killer idea^


# Pygame Configuration
pygame.init()
fps = 300
fpsClock = pygame.time.Clock()
width, height = 1280, 720
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
pygame.display.set_caption('Opentrons Tough Cookie Maker')
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
MIN_WAYPOINT_DIST = 2

# Drawing Area Size
# Each brush stroke is a single unit of icing
plateSize = [127, 85]
canvasScale = 5
canvasSize = [plateSize[0]*canvasScale, plateSize[1]*canvasScale]

# Canvas
canvas = pygame.Surface(canvasSize)
canvas.fill((250, 227, 171))

# Waypoints tracker
waypoints = []
lineId = -1
oldLineId = -1

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


# File handling text box setup
input_box = pygame.Rect(280, 10, 200, 32)
color_inactive = pygame.Color('lightskyblue3')
color_active = pygame.Color('dodgerblue2')
color = color_inactive
active = False
textbox = ''

def determine_color(color: str) -> list:
    match color:
        case 'Red':
            return [255, 0, 0]
        case'Blue':
            return [0, 0, 255]
        case 'Green': 
            return [0, 255, 0]
        case 'Yellow':
            return [255, 255, 0]
        case 'White': 
            return [255, 255, 255]
    return [255,0,0]


def rerender_canvas():
    # Re-render the image by line ID
    last_waypt = None
    canvas.fill((250, 227, 171))
    for waypt in waypoints:
        # Convert the waypoints back to canvas plot points
        dx = canvasScale * (float(waypt[2])+ 127/2)
        dy = canvasScale * ((-1 * float(waypt[3])) - 85/2 + 85)
        pygame.draw.circle(
            canvas,
            determine_color(waypt[1]),
            [dx, dy],
            brushSize,
        )
        if last_waypt is not None:
            if last_waypt[0] == waypt[0]:
                last_dx = canvasScale * (float(last_waypt[2])+ 127/2)
                last_dy = canvasScale * ((-1 * float(last_waypt[3])) - 85/2 + 85)
                pygame.draw.line(
                    canvas,
                    determine_color(waypt[1]),
                    [last_dx, last_dy],
                    [dx, dy],
                    width=brushSize,
                )
        last_waypt = waypt

def undo():
    waypoints_with_line_removed = []
    global waypoints
    global lineId
    line_to_remove = waypoints[-1][0]
    for waypoint in waypoints:
        if waypoint[0] != line_to_remove:
            waypoints_with_line_removed.append(waypoint)
    
    waypoints = waypoints_with_line_removed
    lineId = line_to_remove

    rerender_canvas()


def load_existing_file():
    file_path = textbox
    if len(file_path) == 0:
        # If they haven't entered a file name, do not load
        print("File name not provided, could not load.")
        return
    
    if '.csv' not in file_path:
        file_path = file_path+'.csv'
    # import the waypoints as individual points with line IDs
    print(f"Opening: {file_path}")
    with open(file_path, 'r', newline='') as csvfile:
        global waypoints
        waypoints = []
        rows = csv.reader(csvfile)
        for row in rows:
            waypoints.append( (row[0], row[1], float(row[2]), float(row[3]), "LOADED_POINT") )
    
    # Re-render the image by line ID
    rerender_canvas()

    global oldLineId
    oldLineId = len(waypoints)
    global lineId
    lineId = len(waypoints) + 1


# Save the surface to the Disk
def save():
    file_path = textbox
    clean_waypoints = []
    for waypt in waypoints:
        if waypt not in clean_waypoints:
            # do not store waypoints closer than 3 mm apart when drawing in point mode
            if len(clean_waypoints) > 0 and waypt[4] == "Point":
                waypt_x = waypt[2]
                waypt_y = waypt[3]
                waypt_x2 = clean_waypoints[len(clean_waypoints)-1][2]
                waypt_y2 = clean_waypoints[len(clean_waypoints)-1][3]
                dist = math.sqrt(((waypt_x2 - waypt_x) ** 2) + ((waypt_y2 - waypt_y) ** 2))
                if dist >= MIN_WAYPOINT_DIST:
                    clean_waypoints.append((waypt[0], waypt[1], waypt[2], waypt[3]))
                elif (waypt[0] != clean_waypoints[len(clean_waypoints)-1][0]):
                    clean_waypoints.append((waypt[0], waypt[1], waypt[2], waypt[3]))
            elif len(clean_waypoints) > 0 and waypt[4] == "Line":
                clean_waypoints.append((waypt[0], waypt[1], waypt[2], waypt[3]))
            else:
                clean_waypoints.append((waypt[0], waypt[1], waypt[2], waypt[3]))
    if len(file_path) == 0:
        # If they haven't entered a file name, do not save
        print("File name not provided, could not save.")
        return
    
    if '.csv' not in file_path:
        file_path = file_path+'.csv'

    with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(clean_waypoints)
    
    print(f"Saved changes to \'{file_path}\'.")
        

# Global draw type tracker
# current supports "point", the default which draws constantly as the mouse drags, and "line" which drops start and ends for line segments
drawType = "Point"
global pointCounter
pointCounter = 0
def set_draw_type(draw_type: str):
    global drawType
    drawType = draw_type

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
    ['Point', lambda: set_draw_type("Point")],
    ['Line', lambda: set_draw_type("Line")],
]

# Making the buttons
for index, buttonName in enumerate(buttons):
    Button(index * (buttonWidth + 10) + 10, buttonHeight + 20, buttonWidth,
           buttonHeight, buttonName[0], buttonName[1])
# File save and load button
Button(10, 10, buttonWidth, buttonHeight, 'Save', lambda: save())
Button(buttonWidth + 20, 10, buttonWidth, buttonHeight, 'Load', lambda: load_existing_file())
Button(1280 - buttonWidth - 10, 10, buttonWidth, buttonHeight, '← Undo', lambda: undo())

# Game loop.
old_dx = 0
old_dy = 0
while True:
    screen.fill((30, 30, 30))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONUP:
            if drawType == "Point":
                lineId+=1
                pointCounter = 0
            elif drawType == "Line":
                if pointCounter == 2:
                    lineId+=1
                    pointCounter = 0
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If user clicked on the input_box
            if input_box.collidepoint(event.pos):
                active = not active
            else:
                active = False
            color = color_active if active else color_inactive

        if event.type == pygame.KEYDOWN:
            if active:
                if event.key == pygame.K_RETURN:
                    # Filter out return keys
                    pass 
                elif event.key == pygame.K_BACKSPACE:
                    textbox = textbox[:-1]
                else:
                    textbox += event.unicode

    # Draw the file handling UI
    pygame.draw.rect(screen, color, input_box, 2)

    # Render text
    txt_surface = font.render(textbox, True, color)
    screen.blit(txt_surface, (input_box.x+5, input_box.y+5))

    # Resize box if text is too long
    input_box.w = max(200, txt_surface.get_width()+10)

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

        # start the dot tracking
        if lineId == -1:
            lineId = 0

        old_len = len(waypoints)

        # These waypoints will mark the labware center
        # only drop waypoints when we are inside the canvas
        if (0 <= dx <= (canvasSize[0])) and (0 <= dy <= canvasSize[1]):
            x_waypoint = (dx/canvasScale - 127/2) # bottom left = 0, bottom right = 127
            y_waypoint = (85 - round(dy/canvasScale)) - 85/2 # top left = 0, bottom left = 85 
            x_short = "%.3f" % x_waypoint
            y_short = "%.3f" % y_waypoint
            if drawType == "Point":
                pygame.draw.circle(
                    canvas,
                    drawColor,
                    [dx, dy],
                    brushSize,
                )
                waypoints.append( (lineId, colorName, float(x_short), float(y_short), drawType) )
            if drawType == "Line":
                dist = math.sqrt(((old_dx - dx) ** 2) + ((old_dy - dy) ** 2))
                if dist >= MIN_WAYPOINT_DIST and pointCounter < 2:
                        pygame.draw.circle(
                            canvas,
                            drawColor,
                            [dx, dy],
                            brushSize,
                        )
                        pointCounter+=1
                        waypoints.append( (lineId, colorName, float(x_short), float(y_short), drawType) )

        # linking dots:
        # since we never delete colors, as long as current lineId is the same as the last lineID used by the last waypoints 
        # made, draw a line between this dot and the last dot
        if lineId != -1 and lineId == oldLineId:
            # start linking the dots, only draw lines between points on the canvas
            if (
                (0 <= dx <= (canvasSize[0])) and (0 <= dy <= canvasSize[1])
                and (0 <= old_dx <= (canvasSize[0])) and (0 <= old_dy <= canvasSize[1])
                and old_len != len(waypoints)
            ):
                pygame.draw.line(
                    canvas,
                    drawColor,
                    [old_dx, old_dy],
                    [dx, dy],
                    width=brushSize,
                )

        old_dx = dx
        old_dy = dy
        oldLineId = lineId

    # Reference Dot
    pygame.draw.circle(
        screen,
        drawColor,
        [100, 135],
        30,
    )

    # Reference Draw Type
    draw_type_textarea = font.render(drawType, True, (255, 255, 255))
    text_rect = draw_type_textarea.get_rect()
    text_rect.topleft = (80, 175)
    screen.blit(draw_type_textarea, text_rect)

    pygame.display.flip()
    fpsClock.tick(fps)