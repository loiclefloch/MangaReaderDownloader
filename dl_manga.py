#!/bin/python2.7

script_description = """
    This script can be used to download manga chapters on manga readers websites.

    Juste enter the name of the manga. If we don't have any sources on our databases,
    you can manually enter the name of the mange and the url with two vars: {page}, {chapter}
    who replace the page and chapter number on the url.
    For example:
    example.com/manga-chapter1-page34.html become example.com/manga-chapter{chapter}-page{page}.html
"""

import ctypes
import requests
from xml.etree import cElementTree as ET
import argparse
import subprocess
import sys

from manga import Manga
from mangaCrawler import MangaCrawler
from tools import sendmessage
from globals import *

"""
  TODO
  - json to save mangasListing, last chapter dl, and mangas infos
  - option update-all who download all new chapters
"""

config = {
  "animelist_username": "rageberry",
  "animelist_password": "123456"
}

mangasListing = [
  {
    "title": "Mahou Sensei Negima",
    "url": "http://www.mangareader.net/mahou-sensei-negima/{chapter}/{page}",
  },
]

def main():
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
            MangaReader = MangaCrawler(options)
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
    except Exception as e:
        sendmessage("\n%s: An error occured: %s" % (SOFT_NAME, e))

if __name__ == '__main__':
    main()
