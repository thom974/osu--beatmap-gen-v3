from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

driver = webdriver.Chrome('C:\Program Files (x86)\chromedriver.exe')
driver.get('https://bloodcat.com/osu/')

generated_maps = []  # store all maps, format type unknown for now
desired_map_count = 15  # e.g after 15 maps, driver will stop scraping page
t_end = time.time() + 3

# while time.time() < t_end:
#     driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
#     page_sc = driver.page_source
#     print(page_sc)

map_str = driver.find_elements_by_tag_name("a")
for beatmap in map_str:
    print("line:", beatmap.text)

driver.quit()