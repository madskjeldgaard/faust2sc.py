# Compile a faust file as a SuperCollider help file
# faust -json $INFILE -O . > /dev/null && echo "Done."
import os
import json

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

# Iterate over all UI elements to get the parameter names, values and ranges
def get_parameters(json_data):
    # The zero index is needed because it's all in the first index, or is it? @FIXME
    for ui_element in json_data["ui"][0]["items"]:
        param_name = ui_element["label"]
        param_default = ui_element["init"]
        param_min = ui_element["min"]
        param_max = ui_element["max"]

        print("Param name: %s\nDefault Value:%s\nMinimum:%s\nMaximum:%s\n" % (param_name, param_default, param_min, param_max))

if __name__ == "__main__":
    jsonfile = generate_json("test/testfile.dsp")
    data = read_json(jsonfile)
    get_parameters(data)

    data["name"]
    data["inputs"]
    data["outputs"]
    data["meta"]["author"]
    data["meta"]["description"]
