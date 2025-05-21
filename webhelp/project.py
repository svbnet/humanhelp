import xml.etree.ElementTree
import pathlib

from webhelp.table_of_contents import TableOfContents


class Project:
  def __init__(self, project_dir):
    self.project_dir = pathlib.Path(project_dir)
    self.data_dir = None
    self.toc_path = None
    self.index_path = None
    self.fts_path = None
    self.glossary_path = None
    self.toc = None
    self._load_whproj()
  
  def _load_whproj(self):
    # whproj.xml:
    # <project langid="1033" datapath="whxdata" toc="whtoc.xml" index="whidx.xml" fts="whfts.xml" glossary="whglo.xml" />
    full_path = str(self.project_dir.joinpath('whproj.xml'))
    tree = xml.etree.ElementTree.parse(full_path)
    root = tree.getroot()
    
    self.data_dir = self.project_dir.joinpath(root.attrib['datapath'])

    self.toc_path = self.data_dir.joinpath(root.attrib['toc'])
    self.index_path = self.data_dir.joinpath(root.attrib['index'])
    self.fts_path = self.data_dir.joinpath(root.attrib['fts'])
    self.glossary_path = self.data_dir.joinpath(root.attrib['glossary'])
  
  def load_toc(self):
    # TODO confirm if <toc> has any child elements...
    if self.toc: return self.toc

    self.toc = TableOfContents(self)
    return self.toc
