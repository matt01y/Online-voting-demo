# Report

LaTeX source code and schematics for the report.

## Building PDF

You can build to source files into a PDF by running `make` in this directory. The Makefile has the following dependencies:

- `texlive` (You'll want the full scheme)
- `biber` to handle references and citations

For Nix users, please check out [this LaTeX flake](https://git.depeuter.dev/tdpeuter/flakes/src/commit/34e40f73b3be4e1a819f66a5b1766b94817fbcbd/latex/flake.nix).

