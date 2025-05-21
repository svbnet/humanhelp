import pathlib
import argparse

import weasyprint

import webhelp.project
import webhelp.html

INTERMEDIATE_HTML_FILENAME = 'hh-output.html'

def main():
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('project', help='Path to directory of the RoboHelp project to use. This should be a directory containing a whproj.xml file.')
  arg_parser.add_argument('output', help='Path to the output PDF.')
  arg_parser.add_argument('-s', '--stylesheet', action='append', help='Path to a custom stylesheet that will be included. Can be specified multiple times.')
  arg_parser.add_argument('-i', '--inline-styles', action='store_true', help='Include inline styles from help pages. Note that this may produce unexpected results.')
  args = arg_parser.parse_args()
  
  if args.stylesheet:
    extra_stylesheet_urls = [pathlib.Path(u).absolute().as_uri() for u in args.stylesheet]
  else:
    extra_stylesheet_urls = []

  print(f'Loading RoboHelp project at {args.project}...')

  proj = webhelp.project.Project(args.project)
  print('Loading table of contents...')
  proj.load_toc()

  out_file = proj.project_dir.joinpath(INTERMEDIATE_HTML_FILENAME)
  out_pdf_file = pathlib.Path(args.output)
  
  print('Preparing output document...')
  document = webhelp.html.HtmlDocument(
    proj,
    [pathlib.Path('ua_css/default.css').absolute().as_uri(), *extra_stylesheet_urls],
    include_inline_styles=args.inline_styles
  )
  
  previous_heading = None
  print('Table of contents:')
  for (level, item) in proj.toc.root.walk():
    tab = '\t' * (level - 1)
    print(f'{tab}<{level}> {item.name} -- {item.url if hasattr(item, 'url') else '(heading only)'}')
    
    if not hasattr(item, 'url'):
      previous_heading = item.name
      continue
    
    smoother = webhelp.html.HtmlSmoother(proj, item.url)
    page = smoother.smooth_body()
    page.inject_title(level, item.name)
    if previous_heading:
      page.inject_title(level - 1, previous_heading)
      previous_heading = None
    document.append_help_page(page)

  print('Finalizing HTML document...')
  document.finalize()

  print(f'Writing HTML to {out_file}...')
  document.write(out_file)

  print(f'Generating PDF to {out_pdf_file}...')
  html = weasyprint.HTML(filename=str(out_file))
  html.write_pdf(out_pdf_file)


if __name__ == '__main__':
  main()