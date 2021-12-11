# Compile a faust file as a SuperCollider help file
# faust -json $INFILE -O . > /dev/null && echo "Done."
import os
import json
from collections import ChainMap

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

# Iterate over all UI elements to get the parameter names, values and ranges
def get_arguments(json_data):
    out_string = ""
    # The zero index is needed because it's all in the first index, or is it? @FIXME
    for ui_element in json_data["ui"][0]["items"]:
        param_name = ui_element["label"]
        param_default = ui_element["init"]
        param_min = ui_element["min"]
        param_max = ui_element["max"]
        # param_tooltip_info = ui_element["meta"]
        # print("Param name: %s\nDefault Value:%s\nMinimum:%s\nMaximum:%s\n" % (param_name, param_default, param_min, param_max))

        # Param name
        this_argument = "ARGUMENT::%s\n" % (param_name.lower())

        # Add tool tip info if present
        # TODO

        # Add min and max values if present
        if param_min and param_max:
            this_argument = this_argument + "Minimum value: %s\nMaximum value: %s\n" % (param_min, param_max)

        out_string = out_string + "\n" + this_argument

    return out_string

def class_help(json_data):

    # TODO Are the fields used from this guaranteed and what happens if they are not used?
    meta = flatten_list_of_dicts(json_data["meta"])

    out_string = """
CLASS:: %s
SUMMARY:: A Faust plugin
RELATED::Classes/SinOsc
CATEGORIES::Categories>Faust
DESCRIPTION::
A Faust plugin written by %s.
This plugin has %s inputs and %s outputs.
%s

CLASSMETHODS::
METHOD::ar
%s
EXAMPLES::
code::
// TODO
::
    """ % (
            json_data["name"],
            meta["author"],
            json_data["inputs"],
            json_data["outputs"],
            # get_value_from_dict_list(json_data["meta"], "description"),
            meta["description"],
            # json_data["meta"]["description"],
            get_arguments(json_data)
        )

    return out_string

if __name__ == "__main__":
    jsonfile = generate_json("test/testfile.dsp")
    data = read_json(jsonfile)
    help_file_contents = class_help(data)
    print(help_file_contents)
    # print(type(data["meta"]))
