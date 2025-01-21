# target and root file name
MANUSCRIPT_DIR = ./
MANUSCRIPT = $(MANUSCRIPT_DIR)manuscript
SUPPLEMENT_DIR = supplement/
SUPPLEMENT = $(SUPPLEMENT_DIR)supplement
CORRESPONDENCE_DIR = correspondence/
CORRESPONDENCE_TEX:=$(wildcard $(CORRESPONDENCE_DIR)*/*/*.tex)
CORRESPONDENCE_MD:=$(wildcard $(CORRESPONDENCE_DIR)*/*/*.md)
MERGED = merged
DIFF_REV := HEAD
#DIFF_REV := $(shell git describe --tags --abbrev=0) # diff with latest tag as default

# Tex commands
PDFLATEX = pdflatex -halt-on-error --synctex=1
LATEXMK = latexmk -cd
LATEXDIFF-GIT = latexdiff-vc --git --force -r ${DIFF_REV} -e utf8
TWOCOLUMNCMD = \\newcommand{\\TWOCOLUMN}{TRUE}
LINENOCMD = \\newcommand{\\LINENO}{TRUE}
GIT_MOD = `if [ -z "\`git status --porcelain\`" ];then echo "";else echo "*";fi`
HASHCMD = \\newcommand{\\GITHASH}{`git log -1 --format=%h`$(GIT_MOD)} \\newcommand{\\GITDATE}{`git log -1 --format=%ad --date=short`} \\newcommand{\\GITBRANCH}{`git symbolic-ref --short HEAD`$(GIT_MOD)} \\newcommand{\\GITTAG}{`git describe --tags`}
HASHOPT = -pdflatex='$(PDFLATEX) $(LINENOCMD) $(HASHCMD) \\input{%S}'
HASHOPT_TC = -pdflatex='$(PDFLATEX) $(LINENOCMD) $(TWOCOLUMNCMD) $(HASHCMD) \\input{%S}'
OPT_TC = -pdflatex='$(PDFLATEX) $(TWOCOLUMNCMD) \\input{%S}'
DIFF_HASHCMD = \\newcommand{\\GITHASH}{`git log -1 --format=%h` \\Leftarrow\\ ${DIFF_REV}} \\newcommand{\\GITDATE}{`git show --quiet --pretty=format:"%ad" --date=short HEAD` \\Leftarrow\\ `git show --quiet --pretty=format:"%ad" --date=short ${DIFF_REV} | tail -n 1`} \\newcommand{\\GITBRANCH}{`git symbolic-ref --short HEAD`} \\newcommand{\\GITTAG}{`git describe --tags`}
DIFF_HASHOPT = -pdflatex='$(PDFLATEX) $(DIFF_HASHCMD) \\input{%S}'
PVCOPT = -pvc -view=none

# Inkscape commands
INKSCAPE = inkscape
FIG_SVG:=$(wildcard $(MANUSCRIPT_DIR)/figures/*.svg) $(wildcard $(SUPPLEMENT_DIR)figures/*.svg)
FIG_PDF = $(FIG_SVG:.svg=.pdf)

# Ghost script commands
GS = gs
GSMERGE = $(GS) -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=$(MERGED).pdf

# make rules
.PHONY: all fig pdf tc hash hash_tc pvc supplement_pdf diff merge count bib_include docx correspondence clean distclean
all: pdf supplement_pdf correspondence

fig: $(FIG_PDF)

# suffix rules
%.pdf: fig %.tex
	$(LATEXMK) $*

%.aux %Notes.bib: %.tex
	$(PDFLATEX) --output-directory=$(dir $<) $*

%.bbl: %.aux
	bibtex $*

%.pdf: %.svg
	$(INKSCAPE) $(FLAGS_INK) -z --export-filename=$@ --export-area-drawing $^

%_with_bib.tex: %.tex %.bbl %Notes.bib
	sed -e '/^\\bibliography{/e cat $*.bbl' -e 's/^\\bibliography{/\%\\bibligraphy{/' $< > $@

%_lineno.tex: %.tex
	sed -e 's/\\ifdefined\\LINENO/\\iftrue/' $< > $@

%.pdf: %.md %.template
	pandoc -N $< -f markdown --pdf-engine=pdflatex --template=$*.template -o $@

%.pdf: %.md
	pandoc -N $< -f markdown --pdf-engine=pdflatex -H templates/markdown_preamble.tex -V pagesize:a4 -o $@

%.docx: %.tex
	pandoc -s $^ -o $@

# build rules
pdf: $(MANUSCRIPT).pdf

tc: distclean fig $(MANUSCRIPT).tex $(wildcard $(SUPPLEMENT).tex)
	$(LATEXMK) $(OPT_TC) $(MANUSCRIPT)
ifneq ($(wildcard $(SUPPLEMENT).tex),)
	$(LATEXMK) $(OPT_TC) $(SUPPLEMENT)
endif

hash: distclean fig $(MANUSCRIPT).tex $(wildcard $(SUPPLEMENT).tex)
	$(LATEXMK) $(HASHOPT) $(MANUSCRIPT)
ifneq ($(wildcard $(SUPPLEMENT).tex),)
	$(LATEXMK) $(HASHOPT) $(SUPPLEMENT)
endif

hash_tc: distclean fig $(MANUSCRIPT).tex $(wildcard $(SUPPLEMENT).tex)
	$(LATEXMK) $(HASHOPT_TC) $(MANUSCRIPT)
ifneq ($(wildcard $(SUPPLEMENT).tex),)
	$(LATEXMK) $(HASHOPT_TC) $(SUPPLEMENT)
endif

#pvc:
#	$(LATEXMK) $(PVCOPT) $(HASHOPT) $(MANUSCRIPT)
#ifneq ($(wildcard $(SUPPLEMENT).tex),)
#	$(LATEXMK) $(PVCOPT) $(HASHOPT) $(SUPPLEMENT)
#endif

supplement_pdf: $(wildcard $(SUPPLEMENT).tex)
ifneq ($(wildcard $(SUPPLEMENT).tex),)
	make $(SUPPLEMENT).pdf
endif

merge: all
	$(GSMERGE) $(MANUSCRIPT).pdf $(SUPPLEMENT).pdf

diff:
	$(LATEXDIFF-GIT) $(MANUSCRIPT).tex
	$(LATEXMK) $(DIFF_HASHOPT) $(MANUSCRIPT)-diff$(DIFF_REV)
	rm -f $(addprefix $(MANUSCRIPT)-diff$(DIFF_REV).,tex blg bbl log out tbx vdx fgx aux fls fdb_latexmk)
ifneq ($(wildcard $(SUPPLEMENT).tex),)
	$(LATEXDIFF-GIT) $(SUPPLEMENT).tex
	$(LATEXMK) $(DIFF_HASHOPT) $(SUPPLEMENT)-diff$(DIFF_REV)
	rm -f $(addprefix $(SUPPLEMENT)-diff$(DIFF_REV).,tex blg bbl log out tbx vdx fgx aux fls fdb_latexmk)
endif

diff_no_hash:
	$(LATEXDIFF-GIT) $(MANUSCRIPT).tex
	$(LATEXMK) $(MANUSCRIPT)-diff$(DIFF_REV)
	rm -f $(addprefix $(MANUSCRIPT)-diff$(DIFF_REV).,tex blg bbl log out tbx vdx fgx aux fls fdb_latexmk)
ifneq ($(wildcard $(SUPPLEMENT).tex),)
	$(LATEXDIFF-GIT) $(SUPPLEMENT).tex
	$(LATEXMK) $(SUPPLEMENT)-diff$(DIFF_REV)
	rm -f $(addprefix $(SUPPLEMENT)-diff$(DIFF_REV).,tex blg bbl log out tbx vdx fgx aux fls fdb_latexmk)
endif

count: $(MANUSCRIPT).tex
	texcount -v -html $(MANUSCRIPT).tex > $(MANUSCRIPT)_count.html
	texcount $(MANUSCRIPT).tex

bib_include: $(MANUSCRIPT).tex $(MANUSCRIPT).bbl
	make $(MANUSCRIPT)_with_bib.pdf

docx: $(MANUSCRIPT).tex $(wildcard $(SUPPLEMENT).tex)
	make $(MANUSCRIPT).docx
ifneq ($(wildcard $(SUPPLEMENT).tex),)
	make $(SUPPLEMENT).docx
endif

correspondence: $(CORRESPONDENCE_MD)
	make $(CORRESPONDENCE_MD:.md=.pdf)

# clean rules
clean:
	$(LATEXMK) -c
	rm -f $(addprefix $(MANUSCRIPT).,aux bbl fgx tbx vdx blg fgx aux fls fdb_latexmk synctex.gz out log) $(MANUSCRIPT)Notes.bib $(MANUSCRIPT)_count.html
ifneq ($(wildcard $(SUPPLEMENT).tex),)
	rm -f $(addprefix $(SUPPLEMENT).,aux bbl fgx tbx vdx blg fgx aux fls fdb_latexmk synctex.gz out log) $(SUPPLEMENT)Notes.bib
endif

distclean: clean
	rm -f $(MANUSCRIPT).pdf $(SUPPLEMENT).pdf $(CORRESPONDENCE_MD:.md=.pdf)
