import requests
from  urllib.parse import urlencode
from bs4 import BeautifulSoup
from os import path, makedirs, remove
from sys import exit


HOST = "https://mcm.lifeway.com"
LOGIN_PAGE = "/login.html"
CURRICULUM_PAGE = "/curriculum/curriculumlist.html"

EMAIL = "EMAIL_HERE"
PASSWORD = "PASSWORD_HERE"

def download_file(url, p):
    local_filename = p + "/" + url.split('/')[-1].split('?')[0]
    try:
        makedirs(p)
    except FileExistsError:
        pass
    # NOTE the stream=True parameter below
    try:
        if not path.exists(local_filename):
            with requests.get(url, stream=True, timeout=5) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            # f.flush()
    except Exception as e:
        print("{}/{} did not download".format(p, url))
        if path.exists(local_filename):
            remove(local_filename)
    except KeyboardInterrupt:
        print("{}/{} did not download due to interrupt".format(p, url))
        if path.exists(local_filename):
            remove(local_filename)
        exit()

    return local_filename

def get_unit_name(unit):
    return unit.split("=")[-1]

curriculums = set()

def does_file_exist(link, p):
    local_filename = p + "/" + link.split('/')[-1].split('?')[0]
    return path.exists(local_filename)

s = requests.Session() 
# all cookies received will be stored in the session object
s.get(HOST+LOGIN_PAGE)

data = {"emailAddress": EMAIL,
        "password": PASSWORD}
# data = urlencode(data)
# data = "emailAddress={}&password={}".format(EMAIL, PASSWORD)
s.post(HOST + LOGIN_PAGE, data=data)
r = s.get(HOST + CURRICULUM_PAGE)

soup = BeautifulSoup(r.text, 'html.parser')

other_pages = set()

for page_link in soup.select(".pages a"):
    if '/curriculumlist.html' in page_link.attrs['href']:
        other_pages.add(page_link.attrs['href'])


for curr in soup.select(".curriculumList a"):
    curriculums.add(curr.attrs['href'])

for page in other_pages:
    r = s.get(HOST + page)
    page_soup = BeautifulSoup(r.text, 'html.parser')
    for curr in page_soup.select(".curriculumList a"):
    curriculums.add(curr.attrs['href'])

for curr in curriculums:
    downloaded_items = 0
    units = set()
    r = s.get(HOST + curr)
    curr_soup = BeautifulSoup(r.text, 'html.parser')
    # get units
    for menu in curr_soup.select('.menu a'):
        if "selectedUnit" in menu.attrs['href']:
            units.add(menu.attrs['href'])

    for unit in units:
        print("downloading {}".format(get_unit_name(unit)))
        dl_list = set()
        # logging in again in case there was a time out.
        s.post(HOST + LOGIN_PAGE, data=data)
        r = s.get(HOST + unit)
        curr_soup = BeautifulSoup(r.text, 'html.parser')

        title = curr_soup.select('.title h1')[0].text
        p = path.join(title, get_unit_name(unit))

        for link in curr_soup.select('.wrap a'):
            l = link.attrs['href']
            if not l:
                continue
            if l.startswith('http://lifeway.s3.amazonaws.com') and not does_file_exist(l, p):
                dl_list.add(l)

        downloaded_items = downloaded_items + len(dl_list)

        if not dl_list:
            print("nothing to download from {}".format(unit))
        else:
            print("downloading {} files from {}".format(len(dl_list), unit))

        for link in dl_list:
            download_file(link, p)

    print("downloaded {} files from {}".format(downloaded_items, curr))


