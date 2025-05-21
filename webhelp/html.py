import bs4
import pathlib
import re
import codecs
import os.path

bad_char_regexp = re.compile(r'[^a-zA-Z_-]')
css_html_comment_regexp = re.compile(r'(<!--|-->)')

unpermitted_selector = 'h1, h2, h3, h4, h5, h6, script, .Keyword'


def prepend_css_id(css_rules, id_selector):
  # Ensure the ID selector doesn't start with #
  id_selector = id_selector.lstrip('#')
  
  # Add the # prefix
  id_selector = f"#{id_selector}"
  
  # Process the CSS rules
  result = []
  in_rule = False
  current_selector = ""
  current_declaration = ""
  
  i = 0
  while i < len(css_rules):
    char = css_rules[i]
    
    # Skip whitespace outside of rules
    if not in_rule and char.isspace():
      i += 1
      continue
    
    # Capture selector
    if not in_rule:
      # Find the opening brace
      selector_start = i
      while i < len(css_rules) and css_rules[i] != '{':
        i += 1
      
      if i < len(css_rules):
        # Extract the selector
        current_selector = css_rules[selector_start:i].strip()
        
        # Handle comma-separated selectors
        if ',' in current_selector:
          selectors = [s.strip() for s in current_selector.split(',')]
          current_selector = ', '.join([f"{id_selector} {s}" for s in selectors])
        else:
          current_selector = f"{id_selector} {current_selector}"
        
        in_rule = True
        i += 1  # Skip the opening brace
      else:
        # No opening brace found, break
        break
    else:
      # Capture everything until the closing brace
      declaration_start = i
      brace_count = 1
      
      while i < len(css_rules) and brace_count > 0:
        if css_rules[i] == '{':
          brace_count += 1
        elif css_rules[i] == '}':
          brace_count -= 1
        i += 1
      
      if brace_count == 0:
        # Extract the declaration (excluding the closing brace)
        current_declaration = css_rules[declaration_start:i-1]
        
        # Add the modified rule to the result
        result.append(f"{current_selector} {{{current_declaration}}}")
        
        in_rule = False
      else:
        # No closing brace found, break
        break
  
  return " ".join(result)


def id_for(rel_path):
  """Generates an ID that can be used as an HTML/CSS ID or class name"""
  return 'hh-' + bad_char_regexp.sub('--', rel_path)


class ExternalDependency:
  def __init__(self, location, element_type, absolute_path):
     self.location = location
     self.element_type = element_type
     self.absolute_path = absolute_path


class HtmlHelpPage:
  def __init__(self, fragment, inline_css, ext_dependencies):
    self.fragment = fragment
    self.inline_css = inline_css
    self.ext_dependencies = ext_dependencies
  
  def inject_title(self, level, title):
    if level < 1 or level > 6:
      raise ValueError('level must be from 1 to 6')
    elem = self.fragment.new_tag(f'h{level}')
    elem.string = title
    self.fragment.div.insert(0, elem)


class HtmlSmoother:
  def __init__(self, project, relative_document_path, encoding='windows-1252'):
    self.project = project
    self.document_path = project.project_dir.joinpath(relative_document_path)
    self.document_id = id_for(relative_document_path)
    
    with codecs.open(self.document_path, encoding=encoding) as fp:
      self.document = bs4.BeautifulSoup(fp, features='html.parser')
  
  def actual_href_path(self, href):
    """Absolute (but not normalized) path of an element href"""
    return pathlib.Path(self.document_path.parent, href)
  
  def relativized_path(self, href):
    """
    Returns a relative path relative to the project root directory.
    Useful for resolving <a href> links to element IDs.
    """
    abs_path = os.path.normpath(self.actual_href_path(href))
    return os.path.relpath(abs_path, self.project.project_dir)
  
  def collect_stylesheet_dependencies(self):
    for elem in self.document.css.select('link[rel="stylesheet"]'):
      yield ExternalDependency('head', 'stylesheet', self.actual_href_path(elem.attrs['href']))
  
  def collect_inline_styles(self):
    for elem in self.document.find_all('style'):
      # Sometimes the <style> contents are wrapped in HTML comments...
      yield prepend_css_id(css_html_comment_regexp.sub('', elem.string).strip(), self.document_id)
  
  def convert_a_hrefs_to_anchors(self):
    """
    Converts the relative hrefs of <a>s to document IDs so that navigation works.
    """
    for elem in self.document.find_all('a'):
      if 'href' not in elem.attrs: continue
      href = elem.attrs['href']
      # External link, don't touch it
      if href.startswith('http://') or href.startswith('https://'): continue
      # Don't deal with file:// or absolute links, these shouldn't exist as there's no real way to base
      # them off of anything
      if href.startswith('/') or href.startswith('file://'):
        print(f"warn: don't know how to deal with link '{href}'")
        continue

      target_id = id_for(self.relativized_path(href))
      elem.attrs['href'] = f'#{target_id}'
  
  def smooth_body(self):
    body = self.document.find('body')

    # Lump all of the <style>s together
    inline_css = '\n'.join(self.collect_inline_styles())
    
    # Find all referenced stylesheets through <link> (not worrying about @import yet)
    deps = list(self.collect_stylesheet_dependencies())
    
    # Don't include headings or scripts
    for elem in body.css.select(unpermitted_selector):
      elem.decompose()

    for elem in body.find_all('img'):
      full_path = self.actual_href_path(elem.attrs['src'])
      deps.append(ExternalDependency('body', 'image', full_path))
      elem.attrs['src'] = full_path.as_uri()
    
    # Make relative <a>s work
    self.convert_a_hrefs_to_anchors()
    
    body.name = 'div'
    body.attrs['id'] = self.document_id
    body.attrs['class'] = 'humanhelp-item'
    
    return HtmlHelpPage(bs4.BeautifulSoup(str(body), features='html.parser'), inline_css, deps)


class HtmlDocument:
  def __init__(self, project, external_css=[], include_inline_styles=True):
    self.project = project
    self.stylesheets = set(external_css)
    self.inline_styles = []
    self.include_inline_styles = include_inline_styles
    self.document = bs4.BeautifulSoup('''
                                      <html>
                                        <head></head>
                                        <body></body>
                                      </html>
                                      ''', features='html.parser')
  
  def append_help_page(self, page):
    doc_body = self.document.find('body')
    
    if self.include_inline_styles:
      self.inline_styles.extend(page.inline_css)

    for ref in page.ext_dependencies:
      if ref.element_type == 'stylesheet':
        normed_path = os.path.normpath(ref.absolute_path)
        self.stylesheets.add(pathlib.Path(normed_path).as_uri())
    
    doc_body.append(page.fragment)
  
  def finalize(self):
    doc_head = self.document.find('head')

    for sheet_url in self.stylesheets:
      link_elem = self.document.new_tag('link')
      link_elem.attrs['rel'] = 'stylesheet'
      link_elem.attrs['href'] = sheet_url
      doc_head.append(link_elem)
    
    inline_css = ''.join(self.inline_styles)
    style_elem = self.document.new_tag('style')
    style_elem.string = inline_css
    
    doc_head.append(style_elem)
  
  def write(self, path):
    with open(path, 'w+') as fp:
      fp.write(str(self.document))
