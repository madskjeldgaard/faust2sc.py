# This is now part of faust

See https://github.com/grame-cncm/faust/pull/689

For more info. Any contributions and issues on this should be addressed in the faust repo. 

# faust2sc.py

This repo contains a script - `faust2sc.py` - for compiling [https://github.com/grame-cncm/faust](faust) files to SuperCollider plugins. 

It is a rewrite and replacement of the original `faust2sc` (for converting faust files to SuperCollider-class files) and `faust2supercollider` (for compiling scsynth and supernova object files). The main goals have been to make the script easier to use and to maintain by rewriting it in Python (as opposed to Ruby+Bash) using standard Python modules. Additionally, this script combines what was formerly split into two scripts into one script that does both things and tries to be smarter about the converted plugins' names, supercollider header paths etc. 

This will eventually end up as a pull request to be included with faust

## Requirements

The script uses only built in Python modules, but *python version =>3.8 is needed*.

## Usage

Download this repo. 

Change permissions of the script:
```bash
chmod +x faust2sc.py
```
Here's an example where the faust file `testfile.dsp` is compiled as a scsynth and supernova plugin and placed in the userExtension directory of a linux machine:

```bash
./faust2sc.py testfile.dsp -s -t $HOME/.local/share/SuperCollider/Extensions/Faust/
```
See the help screen for more info:

```bash
./faust2sc.py -h
```


