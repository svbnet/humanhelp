import xml.etree.ElementTree


class _Branch:
  def __init__(self):
    self.children = None
  
  def _load_children(self):
    for child in self.element:
      match child.tag:
        case 'book':
          yield Book(self.root, self.parent, child)
        case 'item':
          yield Item(self.root, self.parent, child)
        case _:
          print(f"warn: don't know how to handle element type '{child.tag}'")
  
  def _recursive_walk(self, level):
    for child in self.children:
      yield (level, child)
      if isinstance(child, _Branch):
        yield from child._recursive_walk(level + 1)
  
  def walk(self):
    return self._recursive_walk(1)
  

class Item:
  def __init__(self, root, parent, element):
    self.root = root
    self.parent = parent
    self.element = element

    self.name = self.element.attrib['name']
    if 'url' in self.element.attrib:
      self.url = self.element.attrib['url']


class Book(Item, _Branch):
  def __init__(self, root, parent, element):
    super().__init__(root, parent, element)
    self.children = list(self._load_children())
  

class TableOfContentsRoot(_Branch):
  def __init__(self, toc):
    self.toc = toc
    self.root = toc
    self.parent = self
    self.element = None
    self.children = None
    self._load()
  
  def _load(self):
    doc = xml.etree.ElementTree.parse(str(self.toc.root_path))
    # <tocdata />
    self.element = doc.getroot()
    self.children = list(self._load_children())


class TableOfContents:
  def __init__(self, project):
    self.project = project
    self.root_path = None
    self.root = None
    self._load()
  
  def _load(self):
    # TODO: does <toc> have any children?
    # <toc root="whtdata0.xml" />
    doc = xml.etree.ElementTree.parse(str(self.project.toc_path))
    root = doc.getroot()

    self.root_path = self.project.data_dir.joinpath(root.attrib['root'])
    self.root = TableOfContentsRoot(self)
