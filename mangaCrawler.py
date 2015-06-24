from HTMLParser import HTMLParser
from globals import *
from tools import hr, mkdir_p, progress_bar, query_yes_no
import re, urllib2, sys, errno

class MangaCrawler():

  def __init__(self, mangaName, mangaUrl):
    self.minit(mangaName, mangaUrl)

  def __init__(self, options):
    # TODO get manga on db

    self.options = options
    mangaName = options.name
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

  def getChapter(self, num, i = 1):
    chapterUrl = self.url.replace("{chapter}", str(num))
    hr()
    print("Get %s chapter %d" % (self.mangaName, num))
    hr()

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
          elif None == page_pic:
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

    if False == self.options.force_download:
      res = query_yes_no("Download %s - chapter %d ?" % (self.mangaName, num))
      if (res == False):
        return

    mkdir_p(self.dir_path)
    nb_pics = len(pics_list)
    error = 0
    for i, pic in enumerate(pics_list):
        if (error >= 15):
            print("To many errors. Please verify your internet connexion")
            return
        try:
            percent = (float(float(i) / float(nb_pics)) * 100)
            sys.stdout.write("\r[%d%%] Download %s" % (percent, self.getFilename(pic["chapter"], pic["page"])))
            sys.stdout.flush()
            self.savePicture(self.getFilename(pic["chapter"], pic["page"]), pic["url"])
        except urllib2.URLError:
            error += 1
            self.savePicture(self.getFilename(pic["chapter"], pic["page"]), pic["url"])
            return

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


