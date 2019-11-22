from utils import global_const as gc
from utils import ConfigData


def convert_sub_aliq_to_aliquot(sa, assay):
    aliquot = sa
    fl_cfg_dict = ConfigData(gc.CONFIG_FILE_DICTIONARY)
    assay_postfix = fl_cfg_dict.get_item_by_key('assay_sub_aliquot_postfix/' + assay)
    if assay_postfix is not None:
        apf_len = len(assay_postfix)
        if sa[-apf_len:] == assay_postfix:
            aliquot = sa[:len(sa) - apf_len]
    return aliquot


# get value for the given key from dict_config.yaml file
def get_dict_value(key, section):
    fl_cfg_dict = ConfigData(gc.CONFIG_FILE_DICTIONARY)
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
    try:
        v = fl_cfg_dict.get_item_by_key(section + "/" + key)
        if v is not None:
            return True
        else:
            return False
    except Exception:
        return False
