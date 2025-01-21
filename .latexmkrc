#!/usr/bin/env perl
@default_files = ('manuscript.tex');
$max_repeat       = 5;
$pdf_mode         = 1;
$pdflatex = 'pdflatex -synctex=1 -halt-on-error';
$latex = 'pdflatex -synctex=1 -halt-on-error';
$latex_silent = 'pdflatex -synctex=1 -file-line-error -halt-on-error -interaction=nonstopmode';
$bibtex = 'bibtex';
