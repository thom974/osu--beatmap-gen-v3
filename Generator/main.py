import requests
import re
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
import time


starting_time = time.time()


def return_sc(driver):
    return driver.page_source


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


def fetch_access_token():
    with open('access_token.txt','r') as f:
        file_contents = [line for line in f]

    if len(file_contents) == 0:  # if there is no access token
        # parameters used to construct initial authorization url for the client
        req_user_perm = {'client_id':'1659',
                         'redirect_uri': 'https://osu.ppy.sh/beatmapsets',
                         'response_type': 'code',
                         'scope': 'public'
                         }
        # from the response object, grab url
        constructed_url = requests.get('https://osu.ppy.sh/oauth/authorize', params=req_user_perm).url

        # send user to auth. page // this was using selenium
        # driver = webdriver.Chrome('C:\Program Files (x86)\chromedriver.exe')
        # driver.get(constructed_url)
        # print(constructed_url)

        print("Please visit this link to authorize the client:", constructed_url)
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

        with open('access_token.txt','w') as f:
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

    with open('access_token.txt','r') as f:
        access_token = f.readline().rstrip("\n")
    global token_header
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
    for index, beatmap in enumerate(lst):
        url = "https://bloodcat.com/osu/s/" + str(beatmap)
        req = urllib.request.Request(url, method='HEAD')
        r = urllib.request.urlopen(req)
        filename = r.info().get_filename().replace("%20", " ")
        urllib.request.urlretrieve(url,'C:/Users/Acer/AppData/Local/osu!/Songs/' + filename)
        print("finished downloading", str(index+1), "map(s)! (" + filename + ")")

fetch_access_token()
# users_maps = fetch_maps(1000)
filters = {'len':60,
           'stars':6,
           'ar':9,
           'bpm':130,
           'cs':4.2,
           'status': 'any'
           }
maps = fetch_new_maps([905674,1238488],filters)
download_maps(maps)
print(time.time() - starting_time, "seconds")

