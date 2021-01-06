import requests
import pygame
from pygame.time import Clock
import urllib.request
import urllib.parse
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time
import random
import os
from threading import Thread

starting_time = time.time()


# ------------------------------------------------------CLASSES----------------------------------------------------------


class Triangle:
    def __init__(self, left_corner, side_length, colour):
        self.starting_location = [random.randint(0, W), random.randint(0, H)]
        self.x, self.y = left_corner
        self.side_length = side_length
        self.colour = colour

    def create_triangle(self):
        surface = pygame.Surface((self.side_length, self.side_length))
        point_1 = (0, self.side_length)
        point_2 = (self.side_length // 2, self.side_length - ((3 ** 0.5) * self.side_length // 2))
        point_3 = (self.side_length, self.side_length)
        pygame.draw.polygon(surface, self.colour, (point_1, point_2, point_3), 0)
        surface.set_colorkey((0, 0, 0))  # make black transparent
        surface.set_alpha(100)
        return surface

    @staticmethod
    def create_triangles(num, width, height):
        triangle_surfaces = []
        osu_colours = [(252, 186, 3), (115, 223, 245), (187, 108, 230), (255, 92, 211)]
        for _ in range(num):
            left_corner = (random.randint(0, width), random.randint(0, height))
            side_length = random.randrange(50, 201, 2)  # random even number from 50 - 200
            colour = random.choice(osu_colours)
            triangle = Triangle(left_corner, side_length, colour)
            triangle_surface = triangle.create_triangle()
            triangle_location = triangle.starting_location
            triangle_surfaces.append([triangle_surface, triangle_location])
        return triangle_surfaces


class Button:
    def __init__(self, center, dimensions, font_colour, font):
        self.width, self.height = dimensions
        self.center_coords = center
        self.font_colour = font_colour
        self.font = font
        self.text = ""

    def create_button_elements(self):
        button_rect = pygame.Rect(0, 0, self.width, self.height)
        button_rect.center = self.center_coords
        button_font = self.font.render(self.text, True, self.font_colour)
        button_font_rect = button_font.get_rect()
        button_font_rect.center = self.center_coords
        return button_rect, button_font, button_font_rect


class Filter:
    def __init__(self, filter_name, value_range, font_size, num_of_values, decimals):
        self.filter_name = filter_name
        self.font = pygame.font.Font('resources/Aller_Bd.ttf', font_size)
        self.low, self.high = value_range
        self.slider_box_center = []
        self.segments = num_of_values
        self.deci_places = decimals

    def create_filter_box(self):
        surface = pygame.Surface((375, 125))
        surface.set_alpha(100)
        filter_text = self.font.render(self.filter_name, True, (255, 255, 255))
        filter_text_rect = filter_text.get_rect()
        filter_text_rect.center = (187, 30)
        surface.blit(filter_text, filter_text_rect)
        bar = pygame.Rect(0, 0, 220, 2)  # bar of the slider object
        bar.center = (187, 70)
        pygame.draw.rect(surface, (255, 255, 255), bar, 0)
        return surface

    def create_slider_box(self, mouse_pos, clicked, left_max, right_max, **kwargs):
        mx, my = mouse_pos
        box_rect = pygame.Rect(0, 0, 12, 30)
        box_rect.center = self.slider_box_center

        slider_location = self.slider_box_center[0] - left_max  # will always return a value from 0 - 200
        slider_location = slider_location if slider_location > 0 else 0

        # code for filter value (e.g stars = 7.1)
        if 'items' not in kwargs:
            if self.filter_name == "Number of Maps":
                to_format = "%." + str(self.deci_places) + "f"
            elif self.filter_name != "CS":
                to_format = "> %." + str(self.deci_places) + "f"
            else:
                to_format = "< %." + str(self.deci_places) + "f"
            val = round(slider_location / (200 / self.segments), self.deci_places)
            value_text = self.font.render(to_format % val, True, (255, 255, 255))
        else:  # solely for 'status' filter
            statuses = kwargs['items']
            to_format = "%s"
            val = statuses[int(slider_location // 28.57)] if int(slider_location // 28.57) != 7 else 'any'
            value_text = self.font.render(to_format % val, True, (255, 255, 255))

        value_text_rect = value_text.get_rect()
        surface = pygame.Surface((value_text_rect.width, value_text_rect.height))
        surface.blit(value_text, value_text_rect)
        surface.set_colorkey((0, 0, 0))

        # code for sliding the box
        if box_rect.collidepoint(mx, my) and clicked:
            if not self.slider_box_center[0] < left_max and not self.slider_box_center[0] > right_max:
                self.slider_box_center[0] = mx  # add some sort of offset later to improve
            else:
                self.slider_box_center[0] += 1 if self.slider_box_center[0] - 6 < left_max else -1

        # determine value depending on location of slider

        return [box_rect, surface, val]


class Backend(Thread):
    def __init__(self, filter_dict,direc,num):
        super().__init__()
        self.filters = filter_dict
        self.map_count = num
        self.directory = direc
        self.maps_downloaded = []
        self.finished = False
        self.searching = False
        self.filtering = False
        self.all_maps = []
        self.maps = []

    def run(self):
        self.all_maps = self.fetch_maps()
        self.maps = self.fetch_new_maps()
        self.download_maps()
        print(time.time() - starting_time, "seconds")

    def fetch_maps(self):
        self.searching = True
        generated_maps = []  # store all maps, format type unknown for now
        xpath = ".//div[@data-id]"
        all_xpath = ".//div[@class='categories-container container']//ul[@class='status left']//a[@data-value='all']"
        ranked_xpath = ".//div[@class='categories-container container']//ul[@class='mode right']//a[@data-value='std']"
        desired_map_count = self.map_count

        driver = webdriver.Chrome('user_files\chromedriver.exe')
        driver.get('https://beatconnect.io/')
        driver.maximize_window()  # maximize window, necessary for search to work
        element = driver.find_element_by_xpath(all_xpath)
        element_2 = driver.find_element_by_xpath(ranked_xpath)
        element.click()
        element_2.click()
        time.sleep(1)  # wait for elements to load

        while len(generated_maps) < desired_map_count:
            WebDriverWait(driver, timeout=5).until(return_sc)
            map_str = driver.find_elements_by_xpath(xpath)

            for beatmap in map_str:
                map_id = beatmap.get_attribute('data-id')

                if map_id not in generated_maps:
                    generated_maps.append(map_id)

                if len(generated_maps) >= desired_map_count:
                    desired_map_count = len(generated_maps)
                    break
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
        driver.quit()
        return generated_maps

    def download_maps(self):
        self.filtering = False
        print("this is the lst of beatmaps found", self.maps)
        osu_path = self.directory.replace("\\","/")

        for index, beatmap in enumerate(self.maps):
            url = "http://beatconnect.io/b/" + str(beatmap)
            req = urllib.request.Request(url, method='HEAD')
            r = urllib.request.urlopen(req)
            filename = urllib.parse.unquote(r.info().get_filename())  # decode the encoded non ASCII chars (e.g !)
            filesize = r.headers['Content-Length']
            path = osu_path + '/' + filename

            # check if the user already has the map
            try:
                path_test = os.path.getsize(path[:-4])
                print(path_test)
            except OSError:
                print(path[:-4], "doesn't exist!")
            else:
                print(path[:-4], "already exists!")
                continue

            self.maps_downloaded.append([filename,path,filesize])
            urllib.request.urlretrieve(url, path)
            print("finished downloading", str(index + 1), "map(s)! (" + filename + ")")
        else:
            self.finished = True

    def fetch_new_maps(self):
        self.searching = False
        self.filtering = True
        maps_to_filter = self.all_maps
        new_maps = []

        with open('user_files/access_token.txt', 'r') as f:
            access_token = f.readline().rstrip("\n")
        token_header = {'Authorization': 'Bearer ' + access_token}

        for map_id in maps_to_filter:
            beatmapset_info = requests.get("https://osu.ppy.sh/api/v2/beatmapsets/" + str(map_id),
                                           headers=token_header).json()

            beatmapset_diffs = beatmapset_info['beatmaps']  # holds all difficulties of the map set

            diff_star_ratings = [dct['difficulty_rating'] for dct in
                                 beatmapset_diffs]  # holds the star rating of each diff
            diff_star_ratings.sort()

            if map_filter(beatmapset_diffs, self.filters):
                new_maps.append(beatmapset_diffs[-1]['beatmapset_id'])

        return new_maps


# --------------------------------------FUNCTIONALITY--------------------------------------------------------------------


def return_sc(driver):
    return driver.page_source


def has_access_token():
    with open('user_files/access_token.txt', 'r') as f:
        access_token = f.readline().rstrip("\n")

    token_header = {'Authorization': 'Bearer ' + access_token}
    verify_token = requests.get("https://osu.ppy.sh/api/v2/beatmapsets/652412", headers=token_header).json()

    if 'authentication' in verify_token and verify_token['authentication'] == 'basic':
        return False

    return True


# def fetch_maps(num):
#     generated_maps = []  # store all maps, format type unknown for now
#     xpath = ".//div[@data-id]"
#     desired_map_count = num
#
#     driver = webdriver.Chrome('user_files\chromedriver.exe')
#     driver.get('https://beatconnect.io/')
#
#     while len(generated_maps) < desired_map_count:
#         WebDriverWait(driver, timeout=5).until(return_sc)
#         map_str = driver.find_elements_by_xpath(xpath)
#
#         for beatmap in map_str:
#             map_id = beatmap.get_attribute('data-id')
#
#             if map_id not in generated_maps:
#                 generated_maps.append(map_id)
#
#             if len(generated_maps) >= desired_map_count:
#                 desired_map_count = len(generated_maps)
#                 break
#
#         driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
#     driver.quit()
#     return generated_maps


def fetch_access_token(**kwargs):
    # parameters used to construct initial authorization url for the client
    req_user_perm = {'client_id': '1659',
                     'redirect_uri': 'https://osu.ppy.sh/beatmapsets',
                     'response_type': 'code',
                     'scope': 'public'
                     }
    # from the response object, grab url
    if kwargs.get('fetch_auth_link') and kwargs['fetch_auth_link']:
        constructed_url = requests.get('https://osu.ppy.sh/oauth/authorize', params=req_user_perm).url
        with open('user_files/auth_link.txt', 'w') as f:
            f.write(constructed_url)
        return True

    # fetch the auth_token from redirected URL
    if kwargs.get('code_passed') and kwargs['code_passed']:
        with open('user_files/redirect_link.txt', 'r') as f:
            code_for_auth = f.readline().split("=")[1].rstrip("\n")

        # fetch authorization token
        auth_body_data = {'client_id': '1659',
                          'client_secret': 'kQYctkFBxE2vVWNlSzZdmPlLtBYdFE8a2m3cPrlE',
                          'code': code_for_auth,
                          'grant_type': 'authorization_code',
                          'redirect_uri': 'https://osu.ppy.sh/beatmapsets'
                          }
        code_response_text = requests.post('https://osu.ppy.sh/oauth/token', data=auth_body_data).text

        try:  # test if code is valid
            access_token = code_response_text.split(",")[2].split(":")[1][1:-1]
        except IndexError:
            return False

        with open('user_files/access_token.txt', 'w') as f:
            f.write(access_token)

        return True


# how the maps are filtered
def map_filter(dct, map_filters):
    beatmapset_diffs = dct

    # find top diff
    diff_star_ratings = [dct['difficulty_rating'] for dct in beatmapset_diffs]  # holds the star rating of each diff
    diff_star_ratings.sort()
    for diff in beatmapset_diffs:
        if diff['difficulty_rating'] == diff_star_ratings[-1]:
            top_diff = diff
            break

    # check star rating
    if not diff_star_ratings[-1] > map_filters['stars']:
        return False

    # check map set total play count
    diff_play_counts = sum([dct['playcount'] for dct in beatmapset_diffs])
    if not diff_play_counts >= 100:
        return False

    # check length of map
    diff_length = top_diff['total_length']
    if not diff_length >= map_filters['len']:
        return False

    # check ar of map
    diff_ar = top_diff['ar']
    if not diff_ar >= map_filters['ar']:
        return False

    # check bpm of map
    diff_bpm = top_diff['bpm']
    if not diff_bpm >= map_filters['bpm']:
        return False

    # check cs of map
    diff_cs = top_diff['cs']
    if not diff_cs <= map_filters['cs']:
        return False

    # check status
    diff_status = top_diff['status']
    if not diff_status == map_filters['status'] and map_filters['status'] != 'any':
        return False

    return True


def fetch_new_maps(lst, map_filters):
    maps_to_filter = lst
    new_maps = []

    with open('user_files/access_token.txt', 'r') as f:
        access_token = f.readline().rstrip("\n")
    token_header = {'Authorization': 'Bearer ' + access_token}

    for map_id in maps_to_filter:
        beatmapset_info = requests.get("https://osu.ppy.sh/api/v2/beatmapsets/" + str(map_id),
                                       headers=token_header).json()

        beatmapset_diffs = beatmapset_info['beatmaps']  # holds all difficulties of the map set

        diff_star_ratings = [dct['difficulty_rating'] for dct in beatmapset_diffs]  # holds the star rating of each diff
        diff_star_ratings.sort()

        if map_filter(beatmapset_diffs, map_filters):
            new_maps.append(beatmapset_diffs[-1]['beatmapset_id'])

    return new_maps


# def download_maps(lst,direc):
#     print("this is the lst of beatmaps found", lst)
#     osu_path = direc
#     for index, beatmap in enumerate(lst):
#         url = "http://beatconnect.io/b/" + str(beatmap)
#         req = urllib.request.Request(url, method='HEAD')
#         r = urllib.request.urlopen(req)
#         filename = urllib.parse.unquote(r.info().get_filename())  # decode the encoded non ASCII chars (e.g !)
#         print(filename)
#         urllib.request.urlretrieve(url, osu_path + '/' + filename)
#         print("finished downloading", str(index + 1), "map(s)! (" + filename + ")")


# function for drawing wrapped text, not my own
def draw_text(surface, text, color, rect, font, aa=False, bkg=None):
    rect = pygame.Rect(rect)
    y = rect.top
    lineSpacing = 1

    # get the height of the font
    fontHeight = font.size("Tg")[1]

    while text:
        i = 1

        # determine if the row of text will be outside our area
        if y + fontHeight > rect.bottom:
            break

        # determine maximum width of line
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1

        # if we've wrapped the text, then adjust the wrap to the last word
        if i < len(text):
            i = text.rfind(" ", 0, i) + 1

        # render the line and blit it to the surface
        if bkg:
            image = font.render(text[:i], 1, color, bkg)
            image.set_colorkey(bkg)
        else:
            image = font.render(text[:i], aa, color)

        surface.blit(image, (rect.left, y))
        y += fontHeight + lineSpacing

        # remove the text we just blitted
        text = text[i:]

    return text


# ----------------------------------------PYGAME GUI---------------------------------------------------------------------
# set up pygame
pygame.init()
pygame.display.set_caption("osu!")
W, H = 900, 600
FPS = 120
screen = pygame.display.set_mode((W, H))
bg = pygame.Surface((W, H))
bg.fill((51, 57, 84))
osu_font = pygame.font.Font('resources/Aller_Bd.ttf', 30)
osu_font_small = pygame.font.Font('resources/Aller_Bd.ttf', 16)
clock = Clock()


def no_access_token_message():  # not needed
    # load in surface and fonts
    surface = pygame.Surface((600, 300))
    osu_font_token = pygame.font.Font('resources/Aller_Bd.ttf', 20)
    osu_font_token_text = osu_font_token.render('You have not authorized this app with your osu! account yet!', True,
                                                (255, 255, 255))
    font_rect = osu_font_token_text.get_rect()
    font_rect.center = 600 // 2, 300 // 2
    surface.blit(osu_font_token_text, font_rect)
    surface.set_colorkey((0, 0, 0))
    return surface


def transition(width, height, copy):
    running = True
    so = 400  # starting offset
    offset = 1
    while running:
        screen.blit(copy, (0, 0))

        # all rect. points (could make more efficient?)
        rect_1_points = ((200 - so, 200 - so), (350 - so, 50 - so), (650 + offset - so, 350 + offset - so),
                         (500 + offset - so, 500 + offset - so))
        rect_2_points = ((-100 - so, 200 - so), (50 - so, 50 - so), (350 + offset - so, 350 + offset - so),
                         (200 + offset - so, 500 + offset - so))
        rect_3_points = ((500 - so, 200 - so), (650 - so, 50 - so), (950 + offset - so, 350 + offset - so),
                         (800 + offset - so, 500 + offset - so))
        rect_4_points = ((800 - so, 200 - so), (950 - so, 50 - so), (1250 + offset - so, 350 + offset - so),
                         (1100 + offset - so, 500 + offset - so))
        rect_5_points = ((-400 - so, 200 - so), (-250 - so, 50 - so), (50 + offset - so, 350 + offset - so),
                         (-100 + offset - so, 500 + offset - so))

        if rect_5_points[2][1] > height + 1000:
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        pygame.draw.polygon(screen, (252, 186, 3), rect_1_points, 0)
        pygame.draw.polygon(screen, (115, 223, 245), rect_2_points, 0)
        pygame.draw.polygon(screen, (187, 108, 230), rect_3_points, 0)
        pygame.draw.polygon(screen, (255, 92, 211), rect_4_points, 0)
        pygame.draw.polygon(screen, (252, 186, 3), rect_5_points, 0)

        offset *= 1.1

        # update the screen
        pygame.display.flip()
        clock.tick(120)


def main_window(width, height):
    triangles = Triangle.create_triangles(25, width, height)
    y_offset = 0.2

    # creating title variables
    title_text = osu_font.render("osu! Beatmap Generator v3", True, (255, 255, 255))
    header_text = osu_font_small.render("Made by: accent (thomas)", True, (255, 255, 255))
    title_rect = title_text.get_rect()
    header_rect = header_text.get_rect()
    title_rect.center = (width // 2, 50)
    header_rect.center = (width // 2, 90)

    # no access token message
    msg = no_access_token_message()

    # arrow button values
    arrow_button = Button((450, 400), (80, 32), (51, 57, 84), osu_font)
    arrow_button.text = ">>>"
    button_rect, button_font, button_font_rect = arrow_button.create_button_elements()

    # successfully authorized message
    success_text = osu_font.render("Successfully authorized! Click to get started.", True, (255, 255, 255))
    success_rect = success_text.get_rect()
    success_rect.center = (450, 300)

    # successfully authorized button
    success_button = Button((450, 370), (80, 32), (51, 57, 84), osu_font)
    success_button.text = ">>>"
    success_button_rect, success_button_font, success_button_font_rect = success_button.create_button_elements()

    # token expired message
    expired_text = osu_font_small.render("If there is a token in access_token.txt, it is expired. Clear the text file and relaunch.", True, (255, 255, 255))
    expired_text_rect = expired_text.get_rect()
    expired_text_rect.center = (450,500)

    access_token_exists = has_access_token()

    # main program loop
    running = True
    while running:
        # code to reset aspects of program at start of each loop
        screen.blit(bg, (0, 0))
        mouse_clicked = False

        # event listener loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True

        # for floating triangles in background
        for triangle, location in triangles:
            screen.blit(triangle, location)
            location[1] -= y_offset
            if location[1] + triangle.get_height() < 0:
                location[1] = height + 20  # set triangle below screen if past above
                location[0] = random.randint(50, width - 50)  # set triangle to random x value

        # to display mouse coordinates
        mx, my = pygame.mouse.get_pos()
        text = osu_font.render(str(mx) + ", " + str(my), True, (255,255,255))
        text_rect = text.get_rect()
        text_rect.center = (100,100)
        screen.blit(text,text_rect)

        # display title
        screen.blit(title_text, title_rect)
        screen.blit(header_text, header_rect)

        # tell user if they have an access token
        if not access_token_exists:
            screen.blit(msg, (150, 175))
            pygame.draw.rect(screen, (255, 255, 255), button_rect)
            screen.blit(button_font, button_font_rect)
            screen.blit(expired_text,expired_text_rect)

            # check if button pressed
            if button_rect.collidepoint(mx, my) and mouse_clicked:
                if auth_window(width, height):
                    access_token_exists = True
        else:
            screen.blit(success_text, success_rect)
            pygame.draw.rect(screen, (255, 255, 255), success_button_rect)
            screen.blit(success_button_font, success_button_font_rect)

            # check if button pressed
            if success_button_rect.collidepoint(mx, my) and mouse_clicked:
                transition(width, height, screen.copy())
                map_window(width, height)

        # update screen
        pygame.display.flip()
        clock.tick(120)


def auth_window(width, height):
    # variables whose values are declared once OR at the start only
    running = True
    triangles = Triangle.create_triangles(25, width, height)
    y_offset = 0.2

    # variables for text instructions on how to authorize
    fetched_user_auth_link = fetch_access_token(fetch_auth_link=True)
    auth_message = osu_font_small.render("Locate user_files/auth_link.txt where this app is stored.", True,
                                         (255, 255, 255))
    auth_message2 = osu_font_small.render(
        "Visit the link, authorize the program, and copy the entire URL once you get redirected.", True,
        (255, 255, 255))
    auth_message3 = osu_font_small.render(
        "Place the authorization link in redirect_link.txt. Make sure it is the only line in that file.", True,
        (255, 255, 255))
    a_rect = auth_message.get_rect()
    a_rect2 = auth_message2.get_rect()
    a_rect3 = auth_message3.get_rect()
    a_rect.center = (450, 175)
    a_rect2.center = (450, 225)
    a_rect3.center = (450, 275)

    # button for user to press when they have finished authorizing
    finished_button = Button((450, 325), (80, 32), (51, 57, 84), osu_font_small)
    finished_button.text = "Done!"
    finished_button_rect, finished_button_font, finished_button_font_rect = finished_button.create_button_elements()

    while running:
        screen.blit(bg, (0, 0))
        mx, my = pygame.mouse.get_pos()

        # event listener loop
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # triangle background
        for triangle, location in triangles:
            screen.blit(triangle, location)
            location[1] -= y_offset
            if location[1] + triangle.get_height() < 0:
                location[1] = height + 20  # set triangle below screen if past above
                location[0] = random.randint(50, width - 50)  # set triangle to random x value

        # code for text input
        # screen.blit(text_input.get_surface(), (450, 300)) // not used for now (text input obj)

        if fetched_user_auth_link:
            screen.blit(auth_message, a_rect)
            screen.blit(auth_message2, a_rect2)
            screen.blit(auth_message3, a_rect3)
            pygame.draw.rect(screen, (255, 255, 255), finished_button_rect)
            screen.blit(finished_button_font, finished_button_font_rect)

            if finished_button_rect.collidepoint(mx, my) and mouse_clicked:  # return to main menu
                if fetch_access_token(code_passed=True):
                    running = False
                    return True

        pygame.display.flip()
        clock.tick(120)


def map_window(width, height):
    # variables whose values are declared once OR at the start only
    running = True
    triangles = Triangle.create_triangles(25, width, height)
    y_offset = 0.2

    # Filter variables
    length_filter = Filter("Length", (1, 10), 20, 30, 1)
    length_filter_box = length_filter.create_filter_box()
    length_filter.slider_box_center = [235, 180]

    stars_filter = Filter("Stars", (1, 10), 20, 10, 2)
    stars_filter_box = stars_filter.create_filter_box()
    stars_filter.slider_box_center = [235, 345]

    ar_filter = Filter("AR", (1, 10), 20, 10, 1)
    ar_filter_box = ar_filter.create_filter_box()
    ar_filter.slider_box_center = [235, 510]

    bpm_filter = Filter("BPM", (1, 10), 20, 300, 0)
    bpm_filter_box = bpm_filter.create_filter_box()
    bpm_filter.slider_box_center = [660, 180]

    cs_filter = Filter("CS", (1, 10), 20, 7, 1)
    cs_filter_box = cs_filter.create_filter_box()
    cs_filter.slider_box_center = [660, 345]

    status_filter = Filter("Status", (1, 10), 20, 10, 1)
    status_filter_box = status_filter.create_filter_box()
    status_filter.slider_box_center = [660, 510]

    y_padding = 40  # determine spacing between Filters
    y_offset_2 = -40  # move all filters up/down

    # text variables
    title_text = osu_font.render("Filters", True, (255, 255, 255))
    title_rect = title_text.get_rect()
    title_rect.center = (90, 45)

    while running:
        screen.blit(bg, (0, 0))

        # event listener
        mouse_clicked = False
        mouse_one_pressed = pygame.mouse.get_pressed(num_buttons=3)[0]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    main_window(width, height)
                if event.key == pygame.K_RETURN and 'status_slider_info' in locals():
                    running = False
                    values = {
                        "len": length_slider_info[2],
                        "stars": stars_slider_info[2],
                        "ar": ar_slider_info[2],
                        "bpm": bpm_slider_info[2],
                        "cs": cs_slider_info[2],
                        "status": status_slider_info[2]
                    }
                    download_window(width, height, values)

        # # to display mouse coordinates
        mx, my = pygame.mouse.get_pos()
        # text = osu_font.render(str(mx) + ", " + str(my), True, (255, 255, 255))
        # text_rect = text.get_rect()
        # text_rect.center = (700, 50)
        # screen.blit(text, text_rect)

        # triangle background
        for triangle, location in triangles:
            screen.blit(triangle, location)
            location[1] -= y_offset
            if location[1] + triangle.get_height() < 0:
                location[1] = height + 20  # set triangle below screen if past above
                location[0] = random.randint(50, width - 50)  # set triangle to random x value

        # display title
        screen.blit(title_text, title_rect)

        # left filters
        screen.blit(length_filter_box, (50, 150 + y_offset_2))
        length_slider_info = length_filter.create_slider_box((mx, my), mouse_one_pressed, 135, 335)
        length_slider_obj, length_val = length_slider_info[0], length_slider_info[1]
        pygame.draw.rect(screen, (255, 255, 255), length_slider_obj)
        screen.blit(length_val, (235 - length_val.get_width() // 2, 212 - length_val.get_height() // 2))

        screen.blit(stars_filter_box, (50, 275 + y_padding + y_offset_2))
        stars_slider_info = stars_filter.create_slider_box((mx, my), mouse_one_pressed, 135, 335)
        stars_slider_obj, stars_val = stars_slider_info[0], stars_slider_info[1]
        pygame.draw.rect(screen, (255, 255, 255), stars_slider_obj)
        screen.blit(stars_val, (235 - stars_val.get_width() // 2, 377 - stars_val.get_height() // 2))

        screen.blit(ar_filter_box, (50, 400 + 2 * y_padding + y_offset_2))
        ar_slider_info = ar_filter.create_slider_box((mx, my), mouse_one_pressed, 135, 335)
        ar_slider_obj, ar_val = ar_slider_info[0], ar_slider_info[1]
        pygame.draw.rect(screen, (255, 255, 255), ar_slider_obj)
        screen.blit(ar_val, (235 - ar_val.get_width() // 2, 542 - ar_val.get_height() // 2))

        # right filters
        screen.blit(bpm_filter_box, (50 + 425, 150 + y_offset_2))
        bpm_slider_info = bpm_filter.create_slider_box((mx, my), mouse_one_pressed, 560, 760)
        bpm_slider_obj, bpm_val = bpm_slider_info[0], bpm_slider_info[1]
        pygame.draw.rect(screen, (255, 255, 255), bpm_slider_obj)
        screen.blit(bpm_val, (660 - bpm_val.get_width() // 2, 212 - bpm_val.get_height() // 2))

        screen.blit(cs_filter_box, (50 + 425, 275 + y_padding + y_offset_2))
        cs_slider_info = cs_filter.create_slider_box((mx, my), mouse_one_pressed, 560, 760)
        cs_slider_obj, cs_val = cs_slider_info[0], cs_slider_info[1]
        pygame.draw.rect(screen, (255, 255, 255), cs_slider_obj)
        screen.blit(cs_val, (660 - bpm_val.get_width() // 2, 377 - cs_val.get_height() // 2))

        screen.blit(status_filter_box, (50 + 425, 400 + 2 * y_padding + y_offset_2))
        status_slider_info = status_filter.create_slider_box((mx, my), mouse_one_pressed, 560, 760,
                                                             items=['ranked', 'qualified', 'loved', 'pending', 'wip',
                                                                    'graveyard', 'any'])
        status_slider_obj, status_val = status_slider_info[0], status_slider_info[1]
        pygame.draw.rect(screen, (255, 255, 255), status_slider_obj)
        screen.blit(status_val, (660 - status_val.get_width() // 2, 542 - status_val.get_height() // 2))

        pygame.display.flip()
        clock.tick(FPS)


def download_window(width, height, filter_values):
    running = True
    triangles = Triangle.create_triangles(25, width, height)
    y_offset = 0.2

    # load warning sign
    warning_surface = pygame.image.load('resources/Images/warning.png')
    warning_surface = pygame.transform.scale(warning_surface, (80, 75))
    warning_surface.set_colorkey((0, 0, 0))

    # create text for filter box
    info_text = osu_font_small.render("These are your filters. If you want to go back and change them, hit ESCAPE.",
                                      True,
                                      (255, 255, 255))
    info_text_rect = info_text.get_rect()
    info_text_rect.center = (450, 60)

    # to display filter values box
    filters_surface = pygame.Surface((540, 44))
    filters_str = ", ".join('='.join((key, str(val))) for (key, val) in filter_values.items())
    filters_text = osu_font_small.render(filters_str, True, (255, 255, 255))
    filters_text_rect = filters_text.get_rect()
    filters_text_rect.center = (540 // 2, 44 // 2)
    filters_surface.blit(filters_text, filters_text_rect)
    filters_surface.set_alpha(100)

    # create text for instructions
    instruc_str = "This program uses ChromeDriver. Visit the official page and download the appropriate version (according to your Chrome version.)"
    instruc_text_rect = pygame.Rect(0, 0, 400, 100)
    instruc_text_rect.center = (515, 250)

    instruc_text_2 = osu_font_small.render("Once installed, place chromedriver.exe into the user_files folder.", True,
                                           (255, 255, 255))
    instruc_text_2_rect = instruc_text_2.get_rect()
    instruc_text_2_rect.center = (450, 350)

    # proceed button
    proceed_button = Button((450, 485), (80, 32), (51, 57, 84), osu_font)
    proceed_button.text = ">>>"
    proceed_rect, proceed_font, proceed_font_rect = proceed_button.create_button_elements()

    while running:
        screen.blit(bg, (0, 0))
        chromedriver_found = os.path.exists('user_files\chromedriver.exe')
        mx, my = pygame.mouse.get_pos()

        # event listener
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN and chromedriver_found and proceed_rect.collidepoint(mx, my):
                running = False
                progress_window(width, height,filter_values)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    map_window(width, height)
                if event.key == pygame.K_RETURN:
                    pass

        # # to display mouse coordinates
        # text = osu_font.render(str(mx) + ", " + str(my), True, (255, 255, 255))
        # text_rect = text.get_rect()
        # text_rect.center = (700, 50)
        # screen.blit(text, text_rect)

        # triangle background
        for triangle, location in triangles:
            screen.blit(triangle, location)
            location[1] -= y_offset
            if location[1] + triangle.get_height() < 0:
                location[1] = height + 20  # set triangle below screen if past above
                location[0] = random.randint(50, width - 50)  # set triangle to random x value

        # text variables
        screen.blit(filters_surface, (450 - 540 // 2, 115 - 44 // 2))
        screen.blit(info_text, info_text_rect)
        screen.blit(warning_surface, (250 - warning_surface.get_width() // 2, 225 - warning_surface.get_height() // 2))
        draw_text(screen, instruc_str, (255, 255, 255), instruc_text_rect, osu_font_small, aa=True)
        screen.blit(instruc_text_2, instruc_text_2_rect)

        # chromedriver status
        status_colour = pygame.Surface((110, 44))

        if chromedriver_found:
            status_colour.fill((20, 201, 75))  # green colour
            found_text = osu_font_small.render("Found!", True, (255, 255, 255))
            pygame.draw.rect(screen, (255, 255, 255), proceed_rect)
            screen.blit(proceed_font, proceed_font_rect)
        else:
            status_colour.fill((196, 20, 67))
            found_text = osu_font_small.render("Not found.", True, (255, 255, 255))

        found_text_rect = found_text.get_rect()
        found_text_rect.center = (55, 22)
        status_colour.blit(found_text, found_text_rect)
        status_colour.set_alpha(150)
        screen.blit(status_colour, (450 - 110 // 2, 410 - 44 // 2))

        pygame.display.flip()
        clock.tick(FPS)


def progress_window(width,height,dct):
    # variables whose values are declared once OR at the start only
    running = True
    filter_vals = dct
    triangles = Triangle.create_triangles(25, width, height)
    y_offset = 0.2

    # map count slider bar
    count_filter = Filter("Number of Maps", (1, 10), 20, 1000, 0)
    count_filter_box = count_filter.create_filter_box()
    count_filter.slider_box_center = [450, 140]

    # directory instructions and note
    directory_str = "Paste the directory of your osu! Songs folder into songs_directory.txt in user_files."
    directory_text = osu_font_small.render(directory_str,True,(255,255,255))
    directory_text_rect = directory_text.get_rect()
    directory_text_rect.center = (450,245)
    example_str = "Example: C:\\Users\\accent\\AppData\\Local\\osu!\\Songs"
    example_text = osu_font_small.render("Make sure there is no slash at the end. " + example_str,True,(255,255,255))
    example_text_rect = example_text.get_rect()
    example_text_rect.center = (450,285)
    note_text = osu_font.render("NOTE: The download will start once you press the button!",True,(140, 139, 137))
    note_text_rect = note_text.get_rect()
    note_text_rect.center = (450,515)

    # proceed button
    proceed_button = Button((450, 415), (80, 32), (51, 57, 84), osu_font)
    proceed_button.text = ">>>"
    proceed_rect, proceed_font, proceed_font_rect = proceed_button.create_button_elements()

    while running:
        screen.blit(bg,(0,0))
        mx, my = pygame.mouse.get_pos()

        # event listener loop
        mouse_clicked = False
        mouse_one_pressed = pygame.mouse.get_pressed(num_buttons=3)[0]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    download_window(width,height,filter_vals)

        # display mouse pos
        mx, my = pygame.mouse.get_pos()
        text = osu_font.render(str(mx) + ", " + str(my), True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.center = (100, 100)
        screen.blit(text, text_rect)

        # code to read songs_directory.txt
        with open('user_files/songs_directory.txt','r') as f:
            directory = f.readline().rstrip("\n")
            directory_found = False if directory == "" else True

        # triangle background
        for triangle, location in triangles:
            screen.blit(triangle, location)
            location[1] -= y_offset
            if location[1] + triangle.get_height() < 0:
                location[1] = height + 20  # set triangle below screen if past above
                location[0] = random.randint(50, width - 50)  # set triangle to random x value

        # map count slider bar
        screen.blit(count_filter_box, (450 - count_filter_box.get_width() // 2, 130 - count_filter_box.get_height() // 2))
        count_slider_info = count_filter.create_slider_box((mx, my), mouse_one_pressed, 350, 550)
        count_slider_obj, count_val = count_slider_info[0], count_slider_info[1]
        pygame.draw.rect(screen, (255, 255, 255), count_slider_obj)
        screen.blit(count_val, (450 - count_val.get_width() // 2, 170 - count_val.get_height() // 2))

        # text for instructions
        screen.blit(directory_text,directory_text_rect)
        screen.blit(example_text,example_text_rect)
        screen.blit(note_text,note_text_rect)

        # detect if directory has been pasted
        status_colour = pygame.Surface((110, 44))

        if directory_found:
            with open('user_files/songs_directory.txt') as f:
                directory = f.readline().rstrip("\n")

            status_colour.fill((20, 201, 75))  # green colour
            found_text = osu_font_small.render("Found!", True, (255, 255, 255))
            pygame.draw.rect(screen, (255, 255, 255), proceed_rect)
            screen.blit(proceed_font, proceed_font_rect)
        else:
            status_colour.fill((196, 20, 67))
            found_text = osu_font_small.render("Not found.", True, (255, 255, 255))

        found_text_rect = found_text.get_rect()
        found_text_rect.center = (55, 22)
        status_colour.blit(found_text, found_text_rect)
        status_colour.set_alpha(150)
        screen.blit(status_colour, (450 - 110 // 2, 350 - 44 // 2))

        if proceed_rect.collidepoint(mx,my) and mouse_clicked:
            running = False
            downloading_window(width,height,filter_vals,count_slider_info[2],directory)

        pygame.display.flip()
        clock.tick(120)


def downloading_window(width,height,filters,num,direc):
    thread = Backend(filters,direc,num)
    thread.start()  # start the 'backend'
    triangles = Triangle.create_triangles(25, width, height)
    y_offset = 0.2

    running = True
    while running:
        screen.fill((255,255,255))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        for triangle, location in triangles:
            screen.blit(triangle, location)
            location[1] -= y_offset
            if location[1] + triangle.get_height() < 0:
                location[1] = height + 20  # set triangle below screen if past above
                location[0] = random.randint(50, width - 50)  # set triangle to random x value

        # tell user their maps are being searched
        if thread.searching:
            searching_text = osu_font.render("Your maps are currently being searched!",True,(78, 87, 130))
            searching_text_rect = searching_text.get_rect()
            searching_text_rect.center = (450,300)
            screen.blit(searching_text,searching_text_rect)

        # tell user the their maps are being filtered
        if thread.filtering:
            filtering_text = osu_font.render("The maps found are currently being filtered!",True,(78, 87, 130))
            filtering_text_rect = filtering_text.get_rect()
            filtering_text_rect.center = (450,300)
            screen.blit(filtering_text,filtering_text_rect)

        # display all the maps being downloaded, including 2 which have already been installed
        if len(thread.maps_downloaded) != 0 and not thread.finished:
            map_name = thread.maps_downloaded[-1][0]  # map name to be displayed
            map_path = thread.maps_downloaded[-1][1]
            map_size = int(thread.maps_downloaded[-1][2])

            try:
                map_current_size = os.path.getsize(map_path)
                percentage = str(round(map_current_size / map_size * 100, 0)) + "%"
            except FileNotFoundError:  # file not yet in Songs! directory
                percentage = "-%"

            map_name += "   " + percentage

            map_name_text = osu_font.render(map_name,True,(51, 57, 84))
            map_name_rect = map_name_text.get_rect()
            map_name_rect.center = (450,300)
            screen.blit(map_name_text,map_name_rect)

            if len(thread.maps_downloaded) > 1:
                map_name_text_2 = osu_font.render(thread.maps_downloaded[-2][0], True, (78, 87, 130))
                map_name_rect_2 = map_name_text.get_rect()
                map_name_rect_2.center = (450, 250)
                screen.blit(map_name_text_2, map_name_rect_2)

            if len(thread.maps_downloaded) > 2:
                map_name_text_3 = osu_font.render(thread.maps_downloaded[-3][0], True, (121, 135, 201))
                map_name_rect_3 = map_name_text.get_rect()
                map_name_rect_3.center = (450, 200)
                screen.blit(map_name_text_3, map_name_rect_3)

        if thread.finished:  # when the backend has finished downloading all the maps
            finished_text = osu_font.render("Finished downloading! Your songs are now on osu!.",True,(78, 87, 130))
            finished_text_rect = finished_text.get_rect()
            finished_text_rect.center = (450,300)
            screen.blit(finished_text,finished_text_rect)

        pygame.display.flip()
        clock.tick(120)


# ----------------MAIN PROGRAM-----------------------------------------------------------------------------------------
main_window(W, H)
