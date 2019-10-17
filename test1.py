from file_load import File_Json
import os
import tarfile
from pathlib import Path

# filepath = 'json/experiment_metadata.json'
filepath = 'json/sequence_item_metadata.json'
# filepath = 'json/aliquot_metadata.json'
cur_assay = 'scrnaseq'

def get_json_keys(json_node, parent_keys = ''):
    for key, val in json_node.items():
        if isinstance(val, dict):
            if parent_keys:
                cur_parents = '/'.join([parent_keys, key])
            else:
                cur_parents = key
            get_json_keys(val, cur_parents)
        else:
            if parent_keys:
                full_key_name = '/'.join([parent_keys, key])
            else:
                full_key_name = key

            json_node[key] = 'update_function("{}", "{}", "{}")'.format(full_key_name, cur_assay, os.path.basename(filepath))
            json_node[key] = eval(json_node[key])
            print("{} : {}".format(key, json_node[key])) # val

def update_function(key, assay, filename):
    return 'Assay: {}; Json Key: {}; Requested for filling out file: "{}"'.format(assay, key, filename)

def process_json():
    err = None
    log = None

    fl = File_Json(filepath, err, log)

    # for key, item in fl.json_data.items():
    #    print ('key="{}"; value={}'.format(key, item))

    get_json_keys(fl.json_data)

def process_tar():
    output_filename = "submission_out\sample.tar.gz"
    arch_list = [
        ("processed","E:\MounSinai\Darpa\Programming\submission\data_examples\Bulk_Drive\ECHO\HIV\HI\PBMC\scrna-seq\\690_3GEX_AS17-00144_1"),
        ("fastq", "E:\MounSinai\Darpa\Programming\submission\data_examples\Bulk_Drive\ECHO\HIV\HI\PBMC\scrna-seq\FASTQs\\690_3GEX_AS17-00144_1"),
        ("","E:\MounSinai\Darpa\Programming\submission\json\\aliquot_metadata.json"),
        ("", "E:\MounSinai\Darpa\Programming\submission\json\experiment_metadata.json"),
        ("", "E:\MounSinai\Darpa\Programming\submission\json\sequence_item_metadata.json")
    ]

    with tarfile.open(output_filename, "w:") as tar:

        for item in arch_list:
            if len(item[0].strip()) > 0:
                _str = '{}/{}'.format(item[0],os.path.basename(item[1]))
            else:
                _str = '{}'.format(os.path.basename(item[1]))
            tar.add(str(Path(item[1])), arcname=_str)
        tar.close()

# process_json()

process_tar()




