#!/bin/python2.7

script_description = """
    This script can be used to download manga chapters on manga readers websites.

    Juste enter the name of the manga. If we don't have any sources on our databases,
    you can manually enter the name of the mange and the url with two vars: {page}, {chapter}
    who replace the page and chapter number on the url.
    For example:
    example.com/manga-chapter1-page34.html become example.com/manga-chapter{chapter}-page{page}.html
"""

import urllib2
import ctypes
import os, errno, sys, re, signal
from HTMLParser import HTMLParser
import requests
from xml.etree import cElementTree as ET
import argparse
import subprocess

"""
  TODO
  - json to save mangasListing, last chapter dl, and mangas infos
  - option update-all who download all new chapters
"""

config = {
  "animelist_username": "rageberry",
  "animelist_password": "123456"
}

SOFT_NAME="dl_manga"

DEST_DIR="downloads/"
NAME_FORMAT="{manga}_{chapter}_{page}"

mangasListing = [
  {
    "title": "Mahou Sensei Negima",
    "url": "http://www.mangareader.net/mahou-sensei-negima/{chapter}/{page}",
  },
]

def sendmessage(message):
    print(message);
    #subprocess.Popen(['notify-send', message])
    return

def signal_handler(signal, frame):
        print('Exiting...!')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

class MyAnimeList():
    username = ''
    password = ''
    base_url = 'http://myanimelist.net/api'
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36'


    def __init__(self):
      self.username = config['animelist_username']
      self.password = config['animelist_password']
      self.testCredentials()

    def testCredentials(self):

      r = requests.get(
          self.base_url + '/account/verify_credentials.xml',
          auth = (self.username, self.password),
          #headers = {'User-Agent': self.user_agent}
      )

    def search(self, query):
        params = { 'q': query }

        r = requests.get(
            self.base_url + '/anime/search.xml',
            params= params,
            auth = (self.username, self.password),
            headers = {'User-Agent': self.user_agent}
        )

        if (r.status_code == 204):
            return []

        elements = ET.fromstring(r.text)
        return [dict((attr.tag, attr.text) for attr in el) for el in elements]


website_source = MyAnimeList()


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def hr():
  print("========================================")

def progress_bar(percent):
  sys.stdout.write("\r%d%%" % percent)
  sys.stdout.flush()

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

class MangaCrawler():

  def __init__(self, mangaName, mangaUrl):
    self.minit(mangaName, mangaUrl)

  def __init__(self, mangaName):
    for manga in mangasListing:
      if mangaName.lower() in manga["title"].lower():
        self.url = manga["url"]
        self.mangaName = mangaName
        self.dir_path = DEST_DIR + self.mangaName + "/"
        print(mangaName)
        return
    mangareader_url = "http://www.mangareader.net/"
    print("Search on %s" % (mangareader_url))

    manga_url_name = mangaName.lower()
    manga_url_name = re.sub('[^0-9a-zA-Z]+', '-', manga_url_name)

    mangaUrl = mangareader_url + manga_url_name + "/1/1"
    res = self.getPagePic(mangaUrl)
    if None != res:
      mangaUrl = "http://www.mangareader.net/" + manga_url_name + "/{chapter}/{page}"
      self.minit(manga_url_name, mangaUrl)
    else:
      raise RuntimeError("%s not found" % (mangaName))

  def minit(self, mangaName, mangaUrl):
    self.url = mangaUrl
    self.mangaName = mangaName
    self.dir_path = DEST_DIR + self.mangaName + "/"

  def getFilename(self, chapter, page):
    name = NAME_FORMAT
    name = name.replace("{manga}", self.mangaName)
    name = name.replace("{chapter}", str(chapter))
    name = name.replace("{page}", str(page))
    return name + ".jpg"

  def getPagePic(self, url):
    try:
      response = urllib2.urlopen(url)
      html = response.read()
      parser = MyHTMLParser()
      parser.feed(html)
    except urllib2.URLError:
      return None
    except RuntimeError as e:
      print(e)
      return -1

    if parser.has404 == True:
      return -1

    if len(parser.imgs) == 0:
      return None

    res = parser.imgs[len(parser.imgs) - 1]

    return res

  def savePicture(self, imgName, url):
    try:
      img = urllib2.urlopen(url)
      localFile = open(self.dir_path + imgName, 'w+')
      localFile.write(img.read())
      localFile.close()
    except urllib2.HTTPError as e:
      print("Error: %s at %s: %s" % (imgName, url, e.msg))

  def getChapter(self, num):
    chapterUrl = self.url.replace("{chapter}", str(num))
    hr()
    print("Get %s chapter %d" % (self.mangaName, num))
    hr()

    i = 1
    nb_pass = 0
    pics_list = []
    try:
      while i != 1000:
        url = chapterUrl.replace("{page}", str(i))
        sys.stdout.write("\rIndexing" + "." * i)
        sys.stdout.flush()
        try:
          if nb_pass >= 10:
            print("\nThis manga seems to don't have chapter %d" % (num))
            return False
          page_pic = self.getPagePic(url)
          if -1 == page_pic: # 404 found
            nb_pass += 1
          elif  None == page_pic:
            break
          else:
            infos = {
              'url': page_pic,
              'chapter': num,
              'page': i,
            }
            pics_list.append(infos)
        except RuntimeError:
          print("No image for that url")
        i += 1
    except urllib2.HTTPError:
        if i == 1:
          print("Invalid url")
          return False
        elif i <= 5:
          hr()
          print("Indexing finished. They may be an error, please verify that there is %d pages for chapter %d (%s)." % (i, num, self.mangaName))
          hr()
          res = query_yes_no("The chapter is it valid ? Yes: continue, No: Cancel")
          if res == False:
            print("Exit the chapter %d (%s)" % (num, self.mangaName))
            return False
          print("Retriying...")
          self.getChapter(num)
        else:
          print("\nDownloading.")

    if False == options.force_download:
      res = query_yes_no("Download %s - chapter %d ?" % (self.mangaName, num))
      if (res == False):
        return

    mkdir_p(self.dir_path)
    nb_pics = len(pics_list)
    for i, pic in enumerate(pics_list):
      percent = (float(float(i) / float(nb_pics)) * 100)
      sys.stdout.write("\r[%d%%] Download %s" % (percent, self.getFilename(pic["chapter"], pic["page"])))
      sys.stdout.flush()
      self.savePicture(self.getFilename(pic["chapter"], pic["page"]), pic["url"])
    print("\r\nChapter %d finished with %d pages\n" % (num, nb_pics))
    return True

  def getRangeChapters(self, begin, end):
    while (begin <= end):
      if False == self.getChapter(begin): # no more chapters or big error
        return True
      begin += 1
    return False

  def getAllChapters(self):
    return self.getRangeChapters(1, 1000);

class MyHTMLParser(HTMLParser):
    imgs = []
    has404 = False

    def handle_starttag(self, tag, attrs):
        if tag == "img":
           # Check the list of defined attributes.
           for name, value in attrs:
               # If href is defined, print it.
               if name == "src":
                  self.imgs.append(value)
    def handle_data(self, data):
        if data == "404 Not Found":
          self.has404 = True
          return

class Manga():

  def __init__(self, name):
    self.name = name
    self.getInfos()
    self.url = ""
    self.infos = ""

  # use myanimelist.net api
  def getInfos(self):
    self.infos = website_source.search(self.name)
    if len(self.infos) == 0:
      print("No information about this manga")
      return None
    return self.infos


parser = argparse.ArgumentParser(description=script_description)

# optionals
parser.add_argument('-f', '--force-download', action="store_true", default=False, help='Auto download chapter')
parser.add_argument('-r', '--report', action="store_true", default=False, help='Create a final report')
parser.add_argument('-a', '--append', action="store_true", default=False, help='The -l option append to the file')
parser.add_argument('-l', '--log', type=str, default='', help='Log all actions in the specified file. Create or trunc the file')
parser.add_argument('-i', '--generate-infos', action="store_true", default=False, help="Create a txt file with the manga informations.")
parser.add_argument('-c', '--chapters', type=str, default=None, help="The chapter(s) to download. Example: 3 3-5 all")

# required
parser.add_argument('name', type=str, help='The manga name')
options = parser.parse_args()

try:
  if options.chapters != None:
    MangaReader = MangaCrawler(options.name)
    if -1 != options.chapters.find('-'):
      split = options.chapters.split('-')
      rangeBegin = split[0]
      rangeEnd = split[1]
      if False == rangeBegin.isdigit() or False == rangeEnd.isdigit():
        print("Invalid range: " + options.chapters)
        sys.exit(0)
      MangaReader.getRangeChapters(int(rangeBegin), int(rangeEnd))
    elif options.chapters == "all":
      MangaReader.getAllChapters()
    elif True == options.chapters.isdigit():
      MangaReader.getChapter(int(options.chapters))
    else:
      print("Invalid chapters: " + options.chapters)
      sys.exit(0)
  if options.generate_infos == True:
    manga = Manga(options.name)
    print(manga.getInfos())

except:
  sendmessage("%s: An error occured" % SOFT_NAME)

