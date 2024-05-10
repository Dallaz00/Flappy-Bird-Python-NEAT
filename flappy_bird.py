#import neat.config
import pygame
import neat
import time
import os
import random
import visualize
import pickle           # Save best bird
pygame.font.init()      # init font

# Set the window size
FLOOR = 730
WIN_WIDTH = 600
WIN_HEIGHT = 800
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird - NEAT")

#Image 2x & Load Img
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]

PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))

gen = 0

class Bird:     #Representing the Bird
    """
    Bird class representing the flappy bird
    """
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20    #Per rotation frame
    ANIMATION_TIME = 5

    def __init__(self, x, y):   #starting position of the bird, param x starting x position / param y starting y position (int)
        """
        Initialize the object
        :param x: starting x pos (int)
        :param y: starting y pos (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0           #Tilt Degree
        self.tick_count = 0     #Bird physics
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        make the bird jump
        :return: None
        """
        self.vel = -10.5        #falling velocity
        self.tick_count = 0     #To track the last jump
        self.height = self.y

    def move(self):
        """
        Command a Jump
        :return: None
        """
        self.tick_count += 1

        # Downward Acceleration
        displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2    # calculate displacement

        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # Tilt Up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        Draw the bird
        :Param win: pygame window or surface
        :return: None
        """
        self.img_count += 1
        # For animation of bird, loop through three images
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]     #If Animation is less than 5 ticks, will display FIRST flappy bird image
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]     #If Animation is less than 10 ticks, will display SECOND flappy bird image
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]     #If Animation is less than 15 ticks, will display LAST flappy bird image
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]     
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # So if the bird is pointing down at -80 degrees, It won't flip fully
        if self.tilt <= -80:        
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # Tilt the bird
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        """
        gets the mask for the current image of the bird
        :return: None
        """
        return pygame.mask.from_surface(self.img)
    
class Pipe:
    """
    Representing the Pipe Object
    """
    GAP = 200
    VEL = 5

    def __init__(self, x):
        """
        initialize pipe object
        :param x: int
        :param y: int
        :return" None
        """
        self.x = x
        self.height = 0
        # Draws the Top & Bottom of the Pipe
        self.top = 0            #Variables to Track Top of Pipe will be drawn
        self.bottom = 0         #Variables to Track Bottom of Pipe will be drawn
        
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)        #Flipping my 1 Pipe image to be opposite direction
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        """
        set the height of the pipe, from the top of the screen
        :return: None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        move pipe based on vel
        :return: None
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        draw both the top and bottom of the pipe
        :param win: pygame window/surface
        :return: None
        """
        # Draws Top
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # Draws Bottom
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird, win):       # Masking the collission area of the shape of the bird
        """
        returns if a point is colliding with the pipe
        :param bird: Bird object
        :return: Bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset) 
        t_point = bird_mask.overlap(bottom_mask, top_offset) 

        if b_point or t_point:
            return True
        
        return False

class Base: 
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        """
        Initialize the object
        :param y: int
        :return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Move floor so it looks like its scrolling
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:        #Checking if one base image is off screen completely / then cycle back
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draws the floor. This is two images that move together in infinite rotation.
        :param win: the pygame surface/window
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def blitRotateCenter(surf, image, topleft, angle):
    """
    Rotate a surface and blit it to the window
    :param surf: the surface to blit to
    :param image: the image surface to rotate
    :param topLeft: the top left position of the image
    :param angle: a float value for angle
    :return: None
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    """
    draws the windows for the main game loop
    :param win: pygame window surface
    :param bird: a Bird object
    :param pipes: List of pipes
    :param score: score of the game (int)
    :param gen: current generation
    :param pipe_ind: index of closest pipe
    :return: None
    """
    if gen == 0:
        gen = 1
    win.blit(BG_IMG, (0,0))      #Command to draw

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)    
    for bird in birds:    
        # Draw lines - Bird to Pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # Draws all the birds that are alive
        bird.draw(win)     
    
    # score
    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # generations
    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # alive
    score_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))

    pygame.display.update()

def eval_genomes(genomes, config):      #Evaluation of Genomes or def main
    """
    runs the simulation of the current population of
    birds and sets their fitness based on the distance they
    reach in the game.
    """
    global WIN, gen
    win = WIN
    gen += 1
    # starts by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    # bird object that uses that network to play
    nets = []
    ge = []
    birds = []      # Starting position
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230,350))
        genome.fitness = 0      # Start with fitness level of 0
        ge.append(genome)

    #base = Base (730)
    base = Base(FLOOR)
    pipes = [Pipe(400)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():          # Determines whether to use the first or second
                pipe_ind = 1                                                                        # Pipe on the screen for neural network input

        for x, bird in enumerate(birds):        # Give each bird a fitness of 0.1 for each frame it stays alive
            bird.move()
            ge[x].fitness += 0.1                # Encourage bird to continue

            # Send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output [0] > 0.5:                # Using a tanh activation function so result will be between -1 and 1. if over 0.5 jump
                bird.jump()
        
        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            #Bird Collisions
            for bird in birds:
                if pipe.collide(bird, win):
                    #Fitness for hitting the pipe, does better with higher score
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True   #Adding new pipe when the last one is passed by the bird

        if add_pipe:
            score += 1
            # Can add this line to give more reward for passing through a pipe (NOT REQUIRED)
            for genome in ge:                   #or "for g in ge"
                genome.fitness += 5             #Increasing fitness of surviving birds
            pipes.append(Pipe(480))             #Manual Pipe width.
            #pipes.append(Pipe(WIN_WIDTH))      #Alternatively, Auto Pipe width.

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)
        
        # break if score gets large enough
        '''if score > 20:
        Pickle.dump(nets[0],open("best.pickle", "wb"))
        break to transfer to pickle
        '''

def run(config_path):           #Pulling in the NEAT configs
    """
    Runs the NEAT Algorithm to Train a Neural Network to play the game.
    :param config_file: location of config file
    :return: None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    
    # Create the population of Birds, which is the top-level object for a NEAT run.
    p = neat.Population(config)
    
    # Adds a Reporter to Show Game Progress
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run for up to 50 generations.
    winner = p.run(eval_genomes, 100)     #Fitness generations based on survival

    # Show Final Stats
    print('\nBest genome:\n{!s}'.format(winner))

if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)