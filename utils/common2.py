from utils import global_const as gc
from utils import ConfigData


def convert_sub_aliq_to_aliquot(sa, assay):
    aliquot = sa
    fl_cfg_dict = ConfigData(gc.CONFIG_FILE_DICTIONARY)
    assay_postfixes = fl_cfg_dict.get_value('assay_sub_aliquot_postfix/' + assay)  # get_item_by_key
    if assay_postfixes is not None:
        for assay_postfix in assay_postfixes:
            apf_len = len(assay_postfix)
            if sa[-apf_len:] == assay_postfix:
                aliquot = sa[:len(sa) - apf_len]
    return aliquot


# get value for the given key from dict_config.yaml file
def get_dict_value(key, section):
    fl_cfg_dict = ConfigData(gc.CONFIG_FILE_DICTIONARY)
    # replace spaces and slashes with "_"
    key = replace_unacceptable_chars(key, gc.ASSAY_CHARS_TO_REPLACE)
    try:
        v = fl_cfg_dict.get_item_by_key(section + "/" + key)
        if v is not None:
            return v
        else:
            return key
    except Exception:
        return key


# checks if provided key exists in dict_config.yaml file
def key_exists_in_dict(key, section):
    fl_cfg_dict = ConfigData(gc.CONFIG_FILE_DICTIONARY)
    key = replace_unacceptable_chars(key, gc.ASSAY_CHARS_TO_REPLACE)
    try:
        v = fl_cfg_dict.get_item_by_key(section + "/" + key)
        if v is not None:
            return True
        else:
            return False
    except Exception:
        return False

def replace_unacceptable_chars (val, bad_chars = ['/', ' ']):
    # replace not allowed characters with "_"
    for ch in bad_chars:
        val = val.replace(ch, '_')
    # remove repeating "_" symbols
    while '__' in val:
        val = val.replace('__', '_')
    return val