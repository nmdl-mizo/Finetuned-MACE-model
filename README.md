latex_paper_template
====

Template for writing a academic paper, cover letters, and response with $\LaTeX$ and Markdown using Git

## Note

***The author of this template accepts NO RESPONSIBILITY for any damage or disadvantage caused by the use of this template.***
***Please use this template at your own risk after confirming that there will be no problems using it at your research institution or group.***

If you use this template to create a repository for writing papers on GitHub, please make sure that its Owner is your account and its visibility is private.
Although this template also includes a GitHub Action files for compilation checks and making releases, it is recommended that those concerned about security use this template only in on-premise or local environments.

## Usage
### Prepare repository

- For GitHub: Click [Use this template](https://github.com/kiyou/latex_paper_template/generate) and set Owner, Repository Name and Visibility, correctly (in most cases it should be Private).

- For on-premise or local: Fork or clone this repository and set remote url.
    ```bash
    git clone git@github.com:kiyou/latex_paper_template.git
    cd latex_paper_template
    git remote set-url origin {URL_TO_YOUR_REPOSITORY}
    ```

### Compile
To compile single-column plain pdf, just run
```bash
make
```

Other Make recipes:

```bash
make tc # two-column plain pdf
make hash # single-column pdf with line numbers for review
make hash_tc # two-column pdf with line numbers for review
make diff # diff pdf compared with HEAD
make diff DIFF_REV=[revision] # diff pdf compared with [revision]
make clean # clean up intermediate files
make distclean # clean up intermediate files and document pdfs
make count # count words
make fig # convert svg figures in ./figures to pdf
make correspondence # make pdfs of cover letters and response letters from markdown files
```

### GitHub Actions
This template includes two .yml files for GitHub Actions:

- compile.yml

    Pushing a branch to GitHub triggers compiling check of the manuscript and correspondence files.

- release.yml

    Pushing a tag to GitHub triggers making a release and attach the manuscript pdf.

### Dev Container in Visual Studio Code
This template includes `.devcontainer/devcontainer.json` for Dev Container.

#### Usage
1. Prepare a repository by cloning to local machine.
1. Start a new window in Visual Studio Code.
1. Open the repository folder by `Remote-WSL: Open folder in WSL...`
1. Open the repository folder by `Remote-Containers: Open folder in Container...`
1. It is recommended to add `make` as a latex build recipe in your `settings.json` for automatic build:
    ``` json
    "latex-workshop.latex.recipes": [
        // Add below
        {
            "name": "make 🔃",
            "tools": [
                "make"
            ]
        },
        // Add above
        {
            "name": "latexmk 🔃",
            "tools": [
                "latexmk"
            ]
        },
    ]
    ```

#### Tips
- synctex
    1. Open tex editor and corresponding pdf by split tabs in Visual Studio Code
    1. `Ctrl + Alt + j` on the editor to jump to the corresponding part in the pdf viewer
    1. `Ctrl + LeftClick` on the pdf viewer to jump to the corresponding part in the editor

## Requirements

### Packages
- bash
- git
- make
- texlive (pdflatex, bibtex)
- texlive-extra-utils (texcount)
- texlive-latex-recommended (lineno.sty)
- latexmk
- latexdiff
- inkscape
- pandoc
- pandoc-citeproc
- gs

### Docker

The Dockerfiles and Docker Images for building pdf are available at [GitHub](https://github.com/kiyou/latex-docker) and [GitHub Container Registry](https://github.com/kiyou/latex-docker/pkgs/container/latex)/[DockerHub](https://hub.docker.com/repository/docker/kiyou/latex).

A shell script `docker_make.sh` can run `make` on a container from CLI with docker.

## Licence

[MIT](https://opensource.org/licenses/mit-license.php)

## Author

[kiyou](https://github.com/kiyou)
