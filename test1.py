from file_load import File_Json
import os
import tarfile
from pathlib import Path
import jsonschema
from jsonschema import validate

# filepath = 'forms/experiment_metadata.forms'
# filepath = 'forms\experiment_metadata\experiment_metadata.json'
filepath = 'E:\MounSinai\Darpa\Programming\submission\Temp\sequence_item_v3.json'
# filepath = 'forms/aliquot_metadata.forms'
cur_assay = 'scrnaseq'

def get_json_keys(json_node, parent_keys = ''):
    if isinstance(json_node, list):
        get_json_keys_list(json_node, parent_keys)
    else:
        for key, val in json_node.items():
            if parent_keys:
                cur_parents = '/'.join([parent_keys, key])
            else:
                cur_parents = key
            if isinstance(val, list):
                list_val = get_json_keys_list(val, cur_parents)
                json_node[key] = list_val
                print ('Key = {}, Value: {}'.format(cur_parents, json_node[key]))
            else:
                if isinstance(val, dict):
                    get_json_keys(val, cur_parents)
                else:
                    full_key_name = cur_parents

                    # eval_val = eval('update_function("{}", "{}", "{}")'.format(full_key_name, cur_assay, os.path.basename(filepath)))
                    eval_val = 'Evaled key for key = {}'.format(full_key_name)
                    json_node[key] = eval_val
                    print('Key = {}, Value: {}'.format(full_key_name, json_node[key])) # val

def get_json_keys_list(json_node_list, parent_keys =''):

    return

    list_out = []
    if isinstance(json_node_list, list):
        for item in json_node_list:
            # get_json_keys(item, parent_keys)
            print('Node: "{}". Member of list item = {}'.format(parent_keys, item))
            list_out.append(item)
        return list_out

def get_spike_ins():
    out_list = []
    spikes = [1,2,3]
    for spike in spikes:
        spike_dict = {'name': 'spike #' + spike}
        out_list.append(spike_dict)
    return out_list


def get_json_keys_bkp1(json_node, parent_keys = '', islist = False):
    if islist:
        for item in json_node:
            get_json_keys(item, parent_keys)
        return
    for key, val in json_node.items():
        if parent_keys:
            cur_parents = '/'.join([parent_keys, key])
        else:
            cur_parents = key
        if isinstance(val, list):
            get_json_keys(val, cur_parents, True)
        if isinstance(val, dict):
            get_json_keys(val, cur_parents)
        else:
            full_key_name = cur_parents

            json_node[key] = 'update_function("{}", "{}", "{}")'.format(full_key_name, cur_assay, os.path.basename(filepath))
            json_node[key] = eval(json_node[key])
            print("{} : {}".format(key, json_node[key])) # val

def get_json_schema_keys_names_printed(json_node, parent_keys ='', islist = False):
    child_printed = False
    if islist:
        for item in json_node:
            ch_prt = get_json_schema_keys_names_printed(item, parent_keys)
            if ch_prt:
                child_printed = True
        return child_printed
    for key, val in json_node.items():
        if key not in ['type', 'examples', 'comment', 'enum', 'minItems']:
            if parent_keys:
                cur_parents = '/'.join([parent_keys, key])
            else:
                cur_parents = key
            if isinstance(val, list):
                if key not in ['examples', 'enum', 'required']:
                    # print("{} \t {}".format(key, val))
                    ch_prt = get_json_schema_keys_names_printed(val, cur_parents, True)
                    if ch_prt:
                        child_printed = True
                    if not ch_prt:
                        print("{} \t {}".format(key, val))
            if isinstance(val, dict):
                #if key != 'properties':
                #    print("{}: {}".format(key, val))
                # print ('{} -------------'.format(key))
                ch_prt = get_json_schema_keys_names_printed(val, cur_parents)
                if ch_prt:
                    child_printed = True
                if not ch_prt and key != 'properties':
                    print("{} \t {}".format(key, val))
            else:
                full_key_name = cur_parents

                #json_node[key] = 'update_function("{}", "{}", "{}")'.format(full_key_name, cur_assay, os.path.basename(filepath))
                #json_node[key] = eval(json_node[key])
                print("{} \t {}".format(key, val)) # val
                child_printed = True

    return child_printed


def update_function(key, assay, filename):
    return 'Assay: {}; Json Key: {}; Requested for filling out file: "{}"'.format(assay, key, filename)

def process_json():
    err = None
    log = None

    fl = File_Json(filepath, err, log)

    # for key, item in fl.json_data.items():
    #    print ('key="{}"; key={}'.format(key, item))
    if fl.json_data:
        # get_json_keys(fl.json_data)
        get_json_schema_keys_names_printed(fl.json_data)



def process_tar():
    output_filename = "packages\sample.tar.gz"
    arch_list = [
        ("processed","E:\MounSinai\Darpa\Programming\submission\data_examples\Bulk_Drive\ECHO\HIV\HI\PBMC\scrna-seq\\690_3GEX_AS17-00144_1"),
        ("fastq", "E:\MounSinai\Darpa\Programming\submission\data_examples\Bulk_Drive\ECHO\HIV\HI\PBMC\scrna-seq\FASTQs\\690_3GEX_AS17-00144_1"),
        ("","E:\MounSinai\Darpa\Programming\submission\forms\\aliquot_metadata.forms"),
        ("", "E:\MounSinai\Darpa\Programming\submission\forms\experiment_metadata.forms"),
        ("", "E:\MounSinai\Darpa\Programming\submission\forms\sequence_item_metadata.forms")
    ]

    with tarfile.open(output_filename, "w:") as tar:

        for item in arch_list:
            if len(item[0].strip()) > 0:
                _str = '{}/{}'.format(item[0],os.path.basename(item[1]))
            else:
                _str = '{}'.format(os.path.basename(item[1]))
            tar.add(str(Path(item[1])), arcname=_str)
        tar.close()

def validate_schema ():
    # schema_path = 'E:\MounSinai\Darpa\Programming\submission\\forms\experiment_metadata\experiment_metadata_schema.json'
    schema_path = 'E:\MounSinai\Darpa\Programming\submission\submission_packages\sequence_item_metadata_schema.json'
    schema = File_Json(schema_path, None, None)
    # json_path = 'E:\MounSinai\Darpa\Programming\submission\submission_packages\experiment_metadata_v1.json'
    json_path = 'E:\MounSinai\Darpa\Programming\submission\submission_packages\\test_sequence_item_metadata.json'
    json = File_Json(json_path, None, None)
    try:
        validate(json.json_data, schema.json_data)
        print('Validation was successful')
        pass
    except jsonschema.exceptions.ValidationError as ve:
        print('Validation failed with this error: {}'.format(ve))
        pass

# process_json()

# process_tar()

# validate_schema()
