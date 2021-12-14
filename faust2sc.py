# Compile a faust file as a SuperCollider help file
import os
import sys
import os.path
from os import path
import json
from collections import ChainMap
import subprocess
import platform

###########################################
# Utils
###########################################

# TODO Is this cross platform? Does it work on Windows?
def convert_files(dsp_file, out_dir):
    # out_dir = os.path.dirname(dsp_file)
    cpp_file = path.basename(path.splitext(dsp_file)[0] + ".cpp")
    cmd = "faust -i -a supercollider.cpp -json %s -O %s -o %s" % (dsp_file, out_dir, cpp_file)

    result = {"dsp_file": dsp_file, "out_dir": out_dir, "cpp_file": path.abspath(cpp_file), "json_file": path.abspath(dsp_file) + ".json" }

    try:
        subprocess.run(cmd.split(), check = True, capture_output=False)
    except subprocess.CalledProcessError:
        # print(cmd)
        sys.exit('faust failed to compile json file')

    return result

def read_json(json_file):
    f = open(json_file)
    data = json.load(f)
    f.close()
    return data

# Some parts of the generated json file are parsed as lists of dicts -
# This flattens one of those into one dictionary
def flatten_list_of_dicts(list_of_dicts):
    return ChainMap(*list_of_dicts)

def write_file(file, contents):
    f = open(file, "w")
    f.write(contents)
    f.close()

def make_dir(dir_path):
    if not path.exists(dir_path):
        os.mkdir(dir_path)

###########################################
# Compilation
###########################################

# TODO flags/env vars not included yet:
# - DNDEBUG
# - OMP
# - FAUSTTOOLSFLAGS

# This is a slightly hackey way of including all of the environment variables found in the `faustoptflags` script, mostly because I could not find a python native way to set and access those variables otherwise
def faustoptflags():
    systemType = platform.system()
    machine = platform.machine()
    envDict = {}

    # Compilation flags for gcc and icc
    if machine == 'arm6vl':
        # Raspberry Pi
        envDict["MYGCCFLAGS"] = "-std=c++11 -O3 -march=armv6zk -mcpu=arm1176jzf-s -mtune=arm1176jzf-s -mfpu=vfp -mfloat-abi=hard -ffast-math -ftree-vectorize"

    # MacOS
    elif systemType == 'Darwin':
        envDict["EXT"] = "scx"

        # TODO: DNDEBUG
        envDict["SCFLAGS"] = "-DNO_LIBSNDFILE -DSC_DARWIN -bundle"

        if machine == 'arm64':
            # Silicon MX
            envDict["MYGCCFLAGS"] = "-std=c++11 -Ofast"
        else:
            envDict["MYGCCFLAGS"] = "-std=c++11 -Ofast -march=native"

        envDict["MYGCCFLAGSGENERIC"]="-std=c++11 -Ofast"
    else:
        envDict["MYGCCFLAGS"] = "-std=c++11 -Ofast -march=native"
        envDict["MYGCCFLAGSGENERIC"] = "-std=c++11 -Ofast"

    envDict["MYICCFLAGS"]="-std=c++11 -O3 -xHost -ftz -fno-alias -fp-model fast=2"

    if systemType != 'DARWIN':
        envDict["EXT"]="so"
        # TODO DNDEBUG
        envDict["SCFLAGS"]="-DNO_LIBSNDFILE -DSC_LINUX -shared -fPIC"

    if 'CXXFLAGS' in os.environ:
        envDict["MYGCCFLAGS"] = envDict["MYGCCFLAGS"] + " " + os.environ["CXXFLAGS"]

    # Set default values for CXX and CC
    if 'CXX' not in os.environ:
        os.environ['CXX'] = "c++"

    if 'CC' not in os.environ:
        os.environ['CC'] = "cc"

    os.environ['LIPO'] = "lipo"

    return envDict

# Check if header path contains the right folders
def check_header_path(headerpath):
    headerpath = path.join(headerpath, "include")
    plugin_interface = path.join(headerpath, "plugin_interface")
    server = path.join(headerpath, "server")
    common = path.join(headerpath, "common")

    if path.exists(headerpath) and path.exists(plugin_interface) and path.exists(server) and path.exists(common):
        return True
    else:
        return False

# Try and find SuperCollider headers on system
def find_headers():
    # Possible locations of SuperCollider headers
    header_directories = [
        "/usr/local/include/SuperCollider/include",
        "/usr/local/include/supercollider",
        "/usr/include/SuperCollider",
        "/usr/include/supercollider",
        "/usr/local/include/SuperCollider/",
        "/usr/share/supercollider-headers",
        path.join(os.getcwd(), "supercollider")
        ]

    if os.environ['HOME']:
        header_directories.append(path.join(os.environ['HOME'], "supercollider"))

    for headerpath in header_directories:
        if check_header_path(headerpath):
            print("Found SuperCollider headers: %s" % headerpath)
            return headerpath

# Generate string of include flags for the compiler command
def includeflags(header_path):
    # dspresult = subprocess.run(["faust", "-dspdir"], stdout=subprocess.PIPE)
    # dspdir = dspresult.stdout.decode('utf-8')

    # libresult = subprocess.run(["faust", "-libdir"], stdout=subprocess.PIPE)
    # libdir = libresult.stdout.decode('utf-8')

    incresult = subprocess.run(["faust", "-includedir"], stdout=subprocess.PIPE)
    includedir = incresult.stdout.decode('utf-8')

    if header_path:
        sc = header_path
    else:
        possible_header_path = find_headers()
        if possible_header_path:
            if check_header_path(possible_header_path):
                sc = possible_header_path
            else:
                sys.exit("Could not find SuperCollider headers")
        else:
            sys.exit("Could not find SuperCollider headers")

    sc = path.join(sc, "include")

    plugin_interface = path.join(sc, "plugin_interface")
    if not path.exists(plugin_interface):
        sys.exit("Could not find supercollider headers")

    server = path.join(sc, "server")
    if not path.exists(server):
        sys.exit("Could not find supercollider headers")

    common = path.join(sc, "common")
    if not path.exists(common):
        sys.exit("Could not find supercollider headers")

    return "-I%s -I%s -I%s -I%s -I%s" % (plugin_interface, common, server, includedir, os.getcwd())

# Generate a string of build flags for the compiler command. This includes the include flags.
def buildflags(headerpath):
    env = faustoptflags()
    return "-O3 %s %s %s" % (env["SCFLAGS"], includeflags(headerpath), env["MYGCCFLAGS"])

# Compile a .cpp file generated using faust to SuperCollider plugins.
# TODO: Allow additional CXX flags
def compile(out_dir, cpp_file, class_name, compile_supernova, headerpath):
    print("Compiling %s" % class_name)

    flags = buildflags(headerpath)
    env = faustoptflags()

    if path.exists(cpp_file):
        scsynth_obj = path.join(out_dir, class_name + "." + env["EXT"])
        scsynth_compile_command = "%s %s -Dmydsp=\"%s\" -o %s %s" % (os.environ["CXX"], flags, class_name, scsynth_obj, cpp_file)

        # Compile scsynth
        print("Compiling scsynth object using command:\n%s" % scsynth_compile_command)
        os.system(scsynth_compile_command.replace("\n", ""))

        if compile_supernova:
            supernova_obj = path.join(out_dir, class_name + "_supernova." + env["EXT"])
            supernova_compile_command = "%s %s -Dmydsp=\"%s\" -o %s %s" % (os.environ["CXX"], flags, class_name, supernova_obj, cpp_file)

            print("Compiling supernova object using command:\n%s" % supernova_compile_command)
            os.system(supernova_compile_command.replace("\n", ""))
    else:
        sys.exit("Could not find cpp_file")

###########################################
# Help file
###########################################

# Iterate over all UI elements to get the parameter names, values and ranges
def get_help_file_arguments(json_data):
    out_string = ""
    # The zero index is needed because it's all in the first index, or is it? @FIXME
    for ui_element in flatten_list_of_dicts(json_data["ui"])["items"]:
        param_name = ui_element["label"]
        # param_default = ui_element["init"]
        param_min = ui_element["min"]
        param_max = ui_element["max"]

        # Param name
        this_argument = "ARGUMENT::%s\n" % (param_name.lower())
        meta = flatten_list_of_dicts(ui_element["meta"])

        # Add tooltip as a description
        if meta["tooltip"]:
            this_argument = this_argument + meta["tooltip"] + "\n"

        # Add min and max values if present
        if param_min and param_max:
            this_argument = this_argument + "Minimum value: %s\nMaximum value: %s\n" % (param_min, param_max)

        out_string = out_string + "\n" + this_argument

    return out_string

# Generate the contents of a SuperCollider help file
def class_help(json_data, noprefix):

    # TODO Are the fields used from this guaranteed and what happens if they are not used?
    meta = flatten_list_of_dicts(json_data["meta"])
    class_name = get_class_name(json_data, noprefix)

    out_string = """
CLASS::%s
SUMMARY::A Faust plugin
RELATED::Classes/UGen
CATEGORIES::Categories>Faust
DESCRIPTION::
A Faust plugin written by %s.
This plugin has %s inputs and %s outputs.
%s

CLASSMETHODS::
METHOD::ar,kr
%s
EXAMPLES::

code::
// TODO
::

KEYWORD::faust,plugin
    """ % (
            class_name,
            meta["author"],
            json_data["inputs"],
            json_data["outputs"],
            # get_value_from_dict_list(json_data["meta"], "description"),
            meta["description"],
            # json_data["meta"]["description"],
            get_help_file_arguments(json_data)
        )

    return out_string

# Create a help file in target_dir
def make_help_file(target_dir, json_data, noprefix):

    # Create directory if necessary
    out_dir = path.join(target_dir, "HelpSource")
    make_dir(out_dir)
    out_dir = path.join(out_dir, "Classes")
    make_dir(out_dir)

    # help file
    file_name = get_class_name(json_data, noprefix) + ".schelp"
    file_name = path.join(out_dir, file_name)
    write_file(file_name, class_help(json_data, noprefix))

###########################################
# Class file
###########################################

# Iterate over all UI elements to get the parameter names, values and ranges
def get_parameter_list(json_data, with_initialization):
    out_string = ""
    # The zero index is needed because it's all in the first index, or is it? @FIXME
    counter=0
    for ui_element in json_data["ui"][0]["items"]:
        param_name = ui_element["label"].lower()
        param_default = ui_element["init"]

        # Param name
        if with_initialization:
            this_argument =  "%s(%s)" % (param_name, param_default)
        else:
            this_argument = param_name

        if counter != 0:
            out_string = out_string + ", " + this_argument
        else:
            out_string = this_argument

        counter = counter + 1

    return out_string

# This sanitizes the "name" field from the faust file, makes it capitalized, removes dashes and spaces
def get_class_name(json_data, noprefix):
    # Capitalize all words in string
    name = json_data["name"].title()

    # Remove whitespace
    name = name.strip()
    name = name.replace(" ", "")

    # Remove dashes and underscores
    name = name.replace("-", "")
    name = name.replace("_", "")

    if noprefix == 1:
        return name
    else:
        name = "Faust" + name
        return name

# Generate supercollider class file contents
def get_sc_class(json_data, noprefix):
    # TODO Are the fields used from this guaranteed and what happens if they are not used?
    # meta = flatten_list_of_dicts(json_data["meta"])

    class_name = get_class_name(json_data, noprefix)

    # Specifics for multi channel output ugens: Needs to inherit from different class and the init function needs to be overridden
    if json_data["outputs"] > 1:
        parent_class = "MultiOutUGen"
        init = """

init { | ... theInputs |
      inputs = theInputs
      ^this.initOutputs(%s, rate)
  }

    """ % json_data["outputs"]
    else:
        parent_class = "UGen"
        init = ""

    # Input checking
    if json_data["inputs"] > 0:
        input_check = """

checkInputs {
    if (rate == 'audio', {
      %s.do({|i|
        if (inputs.at(i).rate != 'audio', {
          ^(" input at index " + i + "(" + inputs.at(i) +
            ") is not audio rate");
        });
      });
    });
    ^this.checkValidInputs
  }

""" % json_data["inputs"]

    else:
        input_check = ""

    # The final class
    return """
%s : %s {

    *ar{|%s|
      ^this.multiNew('audio', %s)
    }

    *kr{|%s|
      ^this.multiNew('control', %s)
    }

    name { ^"%s" }

    info { ^"Generated with Faust" }
    %s
    %s
}
""" % (
            class_name, parent_class,
            # *ar
            get_parameter_list(json_data, True),
            get_parameter_list(json_data, False),

            # *kr
            get_parameter_list(json_data, True),
            get_parameter_list(json_data, False),

            # FIXME: This is pretty ugly but it matches what the normalizeClassName function does in faust's supercollider.cpp
            # Ideally, this should be fixed in the supercollider.cpp
            # Because, not doing this will lead to "plugin not installed" type errors in SuperCollider
            json_data["name"][0].upper() + json_data["name"][1:].replace("-", "").replace("_", "").replace(" ", ""),
            input_check,
            init
        )

# Make Supercollider class file
def make_class_file(target_dir, json_data, noprefix):

    # Create directory if necessary
    out_dir = path.join(target_dir, "Classes")
    make_dir(out_dir)

    # help file
    file_name = get_class_name(json_data, noprefix) + ".sc"
    file_name = path.join(out_dir, file_name)
    write_file(file_name, get_sc_class(json_data, noprefix))

###########################################
# faust2sc
###########################################

# Generate SuperCollider class and help files and return a dictionary of paths to the generated files including the .cpp and .json files produced by the faust command.
def faust2sc(faustfile, target_folder, noprefix):
    print("Converting faust file to SuperCollider class and help files.\nTarget dir: %s" % target_folder)
    result = convert_files(faustfile, target_folder)

    data = read_json(result["json_file"])
    make_class_file(target_folder, data, noprefix)
    make_help_file(target_folder, data, noprefix)

    result["class"] = get_class_name(data, noprefix)

    return result

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Compile faust .dsp files to SuperCollider plugins including class and help files and supernova objects'
    )

    parser.add_argument("inputfile", help="A Faust .dsp file to be converted")
    parser.add_argument("-t", "--targetfolder", help="Put the generated files in this folder")
    parser.add_argument("-n", "--noprefix", help="Do not prefix the SuperCollider class and object with Faust", type=int, choices=[0,1])
    parser.add_argument("-s", "--supernova", help="Compile supernova plugin", action="store_true")
    parser.add_argument("-p", "--headerpath", help="Path to SuperCollider headers")

    args = parser.parse_args()

    targetfolder = args.targetfolder or os.getcwd()
    noprefix = args.noprefix or 0
    scresult = faust2sc(args.inputfile, targetfolder, noprefix)
    compile_supernova = args.supernova
    header_path = args.headerpath
    compile(scresult["out_dir"], scresult["cpp_file"], scresult["class"], compile_supernova, header_path)
