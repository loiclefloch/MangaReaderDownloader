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


