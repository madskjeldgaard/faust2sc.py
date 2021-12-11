# Compile a faust file as a SuperCollider help file
# faust -json $INFILE -O . > /dev/null && echo "Done."
import os
import os.path
from os import path
import json
from collections import ChainMap

###########################################
# Utils
###########################################

def generate_json(dsp_file):
    # TODO Is this cross platform? Does it work on Windows?
    cmd = "faust -json %s -O %s" % (dsp_file, os.path.dirname(dsp_file))
    os.system(cmd)
    return dsp_file + ".json"

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
    if path.exists(dir_path):
        print("Warning: %s already exists. Not creating again" % dir_path)
    else:
        os.mkdir(dir_path)

###########################################
# Help file
###########################################

# Iterate over all UI elements to get the parameter names, values and ranges
def get_help_file_arguments(json_data):
    out_string = ""
    # The zero index is needed because it's all in the first index, or is it? @FIXME
    for ui_element in json_data["ui"][0]["items"]:
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

def class_help(json_data):

    # TODO Are the fields used from this guaranteed and what happens if they are not used?
    meta = flatten_list_of_dicts(json_data["meta"])
    class_name = get_class_name(json_data)

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

def make_help_file(target_dir, json_data):

    # Create directory if necessary
    out_dir = path.join(target_dir, "HelpSource")
    make_dir(out_dir)
    out_dir = path.join(out_dir, "Classes")
    make_dir(out_dir)

    # help file
    file_name = get_class_name(json_data) + ".schelp"
    file_name = path.join(out_dir, file_name)
    write_file(file_name, class_help(json_data))

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

def get_class_name(json_data):
    # TODO: Make this more consistent with the logic of the generator - what happens to spaces in names for example?
    return json_data["name"].capitalize()

def get_sc_class(json_data):
    # TODO Are the fields used from this guaranteed and what happens if they are not used?
    # meta = flatten_list_of_dicts(json_data["meta"])

    class_name = get_class_name(json_data)

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

            json_data["name"],
            input_check,
            init
        )

def make_class_file(target_dir, json_data):

    # Create directory if necessary
    out_dir = path.join(target_dir, "Classes")
    make_dir(out_dir)

    # help file
    file_name = get_class_name(json_data) + ".sc"
    file_name = path.join(out_dir, file_name)
    write_file(file_name, get_sc_class(json_data))

if __name__ == "__main__":
    jsonfile = generate_json("test/testfile.dsp")
    data = read_json(jsonfile)
    # print(help_file_contents)
    # print(get_sc_class(data))
    # print(type(data["meta"]))
    make_class_file("test", data)
    make_help_file("test", data)
