from utils import global_const as gc
from utils import ConfigData


def convert_sub_aliq_to_aliquot(sa, assay):
    fl_cfg_dict = ConfigData(gc.CONFIG_FILE_DICTIONARY)
    assay_postfix = fl_cfg_dict.get_item_by_key('assay_sub_aliquot_postfix/' + assay)
    apf_len = len(assay_postfix)
    if sa[-apf_len:] == assay_postfix:
        aliquot = sa[:len(sa) - apf_len]
    else:
        aliquot = sa
    return aliquot
