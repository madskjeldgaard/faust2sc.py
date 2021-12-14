# faust2sc.py

This repo contains a script - `faust2sc.py` - for compiling [https://github.com/grame-cncm/faust](faust) files to SuperCollider plugins. 

It is a rewrite and replacement of the original `faust2sc` (for converting faust files to SuperCollider-class files) and `faust2supercollider` (for compiling scsynth and supernova object files). The main goals have been to make the script easier to use and to maintain by rewriting it in Python (as opposed to Ruby+Bash) using standard Python modules. Additionally, this script combines what was formerly split into two scripts into one script that does both things and tries to be smarter about the converted plugins' names, supercollider header paths etc. 

This will eventually end up as a pull request to be included with faust
