# HumanHelp
A converter for legacy RoboHelp HTML help (WebHelp) documents to PDF. Tested with RoboHelp 5.50.

## Introduction
Legacy Adobe RoboHelp HTML help doesn't work well (or at all) in modern browsers due to the amount of weird JavaScript
hacks and cross-frame messaging. Fortunately, within the help directory are a bunch of XML files which lay out the
structure of the help document. This can be used to grab each help page and extract the body of the HTML, then convert
it to a PDF.

You will need to make sure the help file directory has a `whproj.xml` file, otherwise this won't work.

Currently only bookmarks from headings are generated - no table of contents page or page numbers yet.

## Requirements
* Python 3.13
* pipenv/virtualenv
* Requirements for [wheasyprint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)

Only tested on Ubuntu. YMMV on Windows.

## TODO
* Encoding bugs
* Generate table of contents page
* Page numbers
* Glossary
