import requests
import pygame
import re
import urllib.request
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
import time
import random
import pygame_textinput

starting_time = time.time()
#------------------------------------------------------CLASSES----------------------------------------------------------


class Triangle:
    def __init__(self, left_corner, side_length, colour):
        self.starting_location = [random.randint(0,W), random.randint(0,H)]
        self.x, self.y = left_corner
        self.side_length = side_length
        self.colour = colour

    def create_triangle(self):
        surface = pygame.Surface((self.side_length, self.side_length))
        point_1 = (0, self.side_length)
        point_2 = (self.side_length // 2, self.side_length - ((3**0.5)*self.side_length // 2))
        point_3 = (self.side_length,self.side_length)
        pygame.draw.polygon(surface,self.colour,(point_1,point_2,point_3),0)
        surface.set_colorkey((0,0,0))  # make black transparent
        surface.set_alpha(100)
        return surface

    @staticmethod
    def create_triangles(num, width, height):
        triangle_surfaces = []
        osu_colours = [(252, 186, 3), (115, 223, 245), (187, 108, 230), (255, 92, 211)]
        for _ in range(num):
            left_corner = (random.randint(0,width), random.randint(0,height))
            side_length = random.randrange(50,201,2)  # random even number from 50 - 200
            colour = random.choice(osu_colours)
            triangle = Triangle(left_corner,side_length,colour)
            triangle_surface = triangle.create_triangle()
            triangle_location = triangle.starting_location
            triangle_surfaces.append([triangle_surface, triangle_location])
        return triangle_surfaces


#--------------------------------------FUNCTIONALITY--------------------------------------------------------------------

def return_sc(driver):
    return driver.page_source


def has_access_token():
    with open('resources/access_token.txt', 'r') as f:
        file_contents = [line for line in f]
    if len(file_contents) == 0:
        return False
    return True


def fetch_maps(num):
    generated_maps = []  # store all maps, format type unknown for now
    xpath = "//main[@class]//a[@class='id']"
    desired_map_count = num

    driver = webdriver.Chrome('C:\Program Files (x86)\chromedriver.exe')
    driver.get('https://bloodcat.com/osu/?q=&c=b&m=0&s=&g=&l=')

    while len(generated_maps) < desired_map_count:
        WebDriverWait(driver, timeout=5).until(return_sc)
        map_str = driver.find_elements_by_xpath(xpath)

        for beatmap in map_str:
            map_id = beatmap.get_attribute('text')

            if map_id not in generated_maps:
                generated_maps.append(map_id)

            if len(generated_maps) >= desired_map_count:
                desired_map_count = len(generated_maps)
                break

        driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
    driver.quit()
    return generated_maps


def fetch_access_token(**kwargs):
    # parameters used to construct initial authorization url for the client
    req_user_perm = {'client_id':'1659',
                     'redirect_uri': 'https://osu.ppy.sh/beatmapsets',
                     'response_type': 'code',
                     'scope': 'public'
                     }
    # from the response object, grab url
    if kwargs['fetch_auth_link']:
        constructed_url = requests.get('https://osu.ppy.sh/oauth/authorize', params=req_user_perm).url
        with open('resources/auth_link.txt','w') as f:
            f.write(constructed_url)
        return True

    # fetch the auth_token from redirected URL
    code_for_auth = input("Copy and paste the URL of the redirected site after authorizing:").split("=")[1]

    # fetch authorization token
    auth_body_data = {'client_id':'1659',
                      'client_secret': 'kQYctkFBxE2vVWNlSzZdmPlLtBYdFE8a2m3cPrlE',
                      'code': code_for_auth,
                      'grant_type': 'authorization_code',
                      'redirect_uri': 'https://osu.ppy.sh/beatmapsets'
                      }
    code_response_text = requests.post('https://osu.ppy.sh/oauth/token', data=auth_body_data).text
    access_token = code_response_text.split(",")[2].split(":")[1][1:-1]

    with open('resources/access_token.txt', 'w') as f:
        f.write(access_token)


# how the maps are filtered
def map_filter(dct,map_filters):
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


def fetch_new_maps(lst,map_filters):
    maps_to_filter = lst
    new_maps = []

    with open('resources/access_token.txt', 'r') as f:
        access_token = f.readline().rstrip("\n")
    token_header = {'Authorization': 'Bearer ' + access_token}

    for map_id in maps_to_filter:
        beatmapset_info = requests.get("https://osu.ppy.sh/api/v2/beatmapsets/" + str(map_id), headers=token_header).json()
        beatmapset_diffs = beatmapset_info['beatmaps']  # holds all difficulties of the map set

        diff_star_ratings = [dct['difficulty_rating'] for dct in beatmapset_diffs]  # holds the star rating of each diff
        diff_star_ratings.sort()

        if map_filter(beatmapset_diffs,map_filters):
            new_maps.append(beatmapset_diffs[-1]['beatmapset_id'])

    return new_maps


def download_maps(lst):
    osu_path = input("Enter the path location to your Songs! folder:").replace("\\","/")
    for index, beatmap in enumerate(lst):
        url = "https://bloodcat.com/osu/s/" + str(beatmap)
        req = urllib.request.Request(url, method='HEAD')
        r = urllib.request.urlopen(req)
        filename = urllib.parse.unquote(r.info().get_filename())  # decode the encoded non ASCII chars (e.g !)
        urllib.request.urlretrieve(url, osu_path + '/' + filename)
        print("finished downloading", str(index+1), "map(s)! (" + filename + ")")

# fetch_access_token()
# users_maps = fetch_maps(100)
# filters = {'len':60,
#            'stars':6,
#            'ar':9,
#            'bpm':130,
#            'cs':4.2,
#            'status': 'any'
#            }
# maps = fetch_new_maps(users_maps,filters)
# download_maps(maps)
print(time.time() - starting_time, "seconds")

#----------------------------------------PYGAME GUI---------------------------------------------------------------------
# set up pygame
pygame.init()
pygame.display.set_caption("osu!")
W, H = 900,600
screen = pygame.display.set_mode((W,H))
bg = pygame.Surface((W, H))
bg.fill((51, 57, 84))
osu_font = pygame.font.Font('resources/Aller_Bd.ttf', 30)
osu_font_small = pygame.font.Font('resources/Aller_Bd.ttf', 16)


def no_access_token_message():
    # load in surface and fonts
    surface = pygame.Surface((600,300))
    osu_font_token = pygame.font.Font('resources/Aller_Bd.ttf', 20)
    osu_font_token_text = osu_font_token.render('You have not authorized this app with your osu! account yet!',True, (255,255,255))
    font_rect = osu_font_token_text.get_rect()
    font_rect.center = 600 // 2, 300 // 2
    surface.blit(osu_font_token_text,font_rect)
    surface.set_colorkey((0,0,0))
    return surface


def main_window(width, height):
    triangles = Triangle.create_triangles(25, width, height)
    y_offset = 0.2

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
            screen.blit(triangle,location)
            location[1] -= y_offset
            if location[1] + triangle.get_height() < 0:
                location[1] = height + 20  # set triangle below screen if past above
                location[0] = random.randint(50,width-50)  # set triangle to random x value

        # to display mouse coordinates
        mx, my = pygame.mouse.get_pos()
        text = osu_font.render(str(mx) + ", " + str(my), True, (255,255,255))
        text_rect = text.get_rect()
        text_rect.center = (100,100)
        screen.blit(text,text_rect)

        # display title
        title_text = osu_font.render("osu! Beatmap Generator v3", True, (255,255,255))
        header_text = osu_font_small.render("Made by: accent (thomas)", True, (255,255,255))
        title_rect = title_text.get_rect()
        header_rect = header_text.get_rect()
        title_rect.center = (width // 2, 50)
        header_rect.center = (width // 2, 90)
        screen.blit(title_text,title_rect)
        screen.blit(header_text,header_rect)

        # tell user if they have an access token
        if not has_access_token():
            msg = no_access_token_message()
            screen.blit(msg,(150,175))

            # create 'arrow' text
            osu_font_arrow_text = osu_font.render('>>>', True, (51, 57, 84))
            arrow_rect = osu_font_arrow_text.get_rect()
            arrow_rect.center = (450,400)

            # create and draw the button and 'arrow' text to send user to auth. window
            get_token_button = pygame.Rect(0, 0, 80, 32)
            get_token_button.center = (450, 400)
            pygame.draw.rect(screen, (255, 255, 255), get_token_button)
            screen.blit(osu_font_arrow_text,arrow_rect)

            # check if button pressed
            if get_token_button.collidepoint(mx, my) and mouse_clicked:
                auth_window(width,height)

        # update screen
        pygame.display.flip()


def auth_window(width,height):
    running = True
    triangles = Triangle.create_triangles(25, width, height)
    y_offset = 0.2
    # initial_text = fetch_access_token(fetch_auth_link=True)
    # text_input = pygame_textinput.TextInput()  # for text input
    fetched_user_auth_link = fetch_access_token(fetch_auth_link=True)

    while running:
        screen.blit(bg,(0,0))

        # event listener loop
        events = pygame.event.get()
        # text_input.update(events)  # pass events to text input every frame
        for event in events:
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # triangle background
        for triangle, location in triangles:
            screen.blit(triangle,location)
            location[1] -= y_offset
            if location[1] + triangle.get_height() < 0:
                location[1] = height + 20  # set triangle below screen if past above
                location[0] = random.randint(50,width-50)  # set triangle to random x value

        # code for text input
        # screen.blit(text_input.get_surface(), (450, 300)) // not used for now (text input obj)

        if fetched_user_auth_link:
            auth_message = osu_font_small.render("Locate resources/auth_link.txt where this app is stored.", True, (255,255,255))
            auth_message2 = osu_font_small.render("Visit the link, authorize the program, and copy the redirect url.", True, (255,255,255))
            a_rect = auth_message.get_rect()
            a_rect2 = auth_message2.get_rect()
            a_rect.center = (450,150)
            a_rect2.center = (450,200)
            screen.blit(auth_message, a_rect)
            screen.blit(auth_message2, a_rect2)

        pygame.display.flip()

main_window(W,H)
