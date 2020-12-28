class Triangle:
    def __init__(self, left_corner, side_length, colour):
        self.x, self.y = left_corner
        self.side_length = side_length
        self.colour = colour

    def create_triangle(self):
        surface = pygame.Surface((self.side_length, self.side_length))