from file_load import File_Json
from pathlib import Path
from utils import global_const as gc
from utils import common as cm
from utils import common2 as cm2
from utils import ConfigData
import traceback

class SubmissionForm():
    def __init__(self, form_name, request, sub_aliquot, aliquot, sample):
        self.form_name = form_name
        self.req_obj = request  # reference to the current request object
        self.sub_aliquot = sub_aliquot
        self.aliquot = aliquot
        #if sub_aliquot:
        #    self.aliquot = cm2.convert_sub_aliq_to_aliquot(self.sub_aliquot, self.req_obj.assay)
        self.sample = sample
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay
        self.prepare_form(form_name)

    def prepare_form(self, form_name):
        # identify paths for json and config (yaml) files
        fl_path_json_common = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '.json')
        fl_path_json_assay = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '_' + str(self.req_obj.assay).lower() + '.json')
        fl_path_cfg_common = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '.yaml')
        fl_path_cfg_assay = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '_' + str(self.req_obj.assay).lower() + '.yaml')

        # check if assay specific json exists; if yes - use it, if not - use common one
        if cm.file_exists(fl_path_json_assay):
            fl_path_json = fl_path_json_assay
        else:
            fl_path_json = fl_path_json_common

        # load json and config files
        self.fl_json = File_Json(fl_path_json, self.req_obj.error, self.req_obj.logger)
        # self.json_form = fl_json
        self.fl_cfg_common = ConfigData(fl_path_cfg_common)
        # self.fl_cfg_common = fl_cfg_common
        self.fl_cfg_assay = ConfigData(fl_path_cfg_assay)
        # self.fl_cfg_assay = fl_cfg_assay
        self.fl_cfg_dict = ConfigData(gc.CONFIG_FILE_DICTIONARY)

        print(self.fl_json.json_data)
        # loop through all json keys and fill those with associated data
        self.get_json_keys(self.fl_json.json_data)
        print(self.fl_json.json_data)
        print ()

    def get_json_keys(self, json_node, parent_keys=''):
        for key, val in json_node.items():
            # TODO: add functionality to handle JSON arrays
            if isinstance(val, dict):
                if parent_keys:
                    cur_parents = '/'.join([parent_keys, key])
                else:
                    cur_parents = key
                self.get_json_keys(val, cur_parents)
            else:
                if parent_keys:
                    full_key_name = '/'.join([parent_keys, key])
                else:
                    full_key_name = key

                # json_node[key] = 'print("{}")'.format(full_key_name)
                # json_node[key] = eval(json_node[key])
                # print("JSON file - {} : {}".format(full_key_name, val))  # val # json_node[key]
                # print("Config Common - {} = {}".format(key, self.fl_cfg_common.get_value(key)))
                # print("Config Assay - {} = {}".format(key, self.fl_cfg_assay.get_value(key)))

                val = self.eval_cfg_value(full_key_name, self.fl_cfg_assay.get_value(full_key_name), self.fl_cfg_common.get_value(full_key_name))
                json_node[key] = val

                print(key, '==>', json_node[key])

    def eval_cfg_value(self, key, assay_cfg_val, common_cfg_val):
        # if assay config value is not provided, use common assay val
        if assay_cfg_val:
            cfg_val = assay_cfg_val
        else:
            cfg_val = common_cfg_val

        #TODO: move values for the following 2 constants to Global Config file
        eval_flag = 'eval!'
        # yaml_path_flag = '!yaml_path!'
        # check if some configuration instruction/value was retrieved for the given "key"
        if cfg_val:
            if eval_flag in cfg_val:
                cfg_val = cfg_val.replace(eval_flag, '', 1) #replace 'eval!' flag value
                # cfg_val = cfg_val.replace(yaml_path_flag, "'" + key + "'", 1)  # replace 'eval!' flag value
                #if not cfg_val[0:5] == 'self.':
                #    cfg_val = 'self.'+ cfg_val
                try:
                    out_val = eval(cfg_val)
                except Exception as ex:
                    _str = 'Error "{}" occurred during preparing submission form "{}" for sub-aliquot "{}" ' \
                           'while attempting to interpret configuration value "{}" provided for the form\'s key "{}". \n{} ' \
                            .format(ex, self.form_name, self.sub_aliquot, cfg_val, key, traceback.format_exc())
                    self.logger.error(_str)
                    self.error.add_error(_str)
                    out_val = ''
            else:
                out_val = cfg_val
        else:
            # requested "key" does not exist neither in assay or common config files
            _str = 'No value was assigned to "{}" key during preparing submission form "{}" for sub-aliquot "{}".' \
                .format(key, self.form_name, self.sub_aliquot)
            self.logger.warning(_str)
            out_val = ''
        return out_val

    # it will retrieve any existing property from the request object
    def get_request_value(self, property_name, check_dict = False):
        return self.get_property_value_from_object (self.req_obj, property_name, check_dict)

    # it will retrieve any existing property from the submission_form object
    def get_submission_form_value(self, property_name, check_dict = False):
        return self.get_property_value_from_object(self, property_name, check_dict)

    # it will retrieve any existing property from rawdata object
    def get_rawdata_value(self, property_name, check_dict = False):
        return self.get_property_value_from_object(self.req_obj.raw_data.aliquots_data_dict[self.sub_aliquot],
                                                   property_name, check_dict, 'dict')

    # it will retrieve a value of a property named in "property_name" parameter
    # from the object passed as a reference in "obj" parameter
    def get_property_value_from_object(self, obj, property_name, check_dict = False, obj_type = 'class'):
        if obj_type == 'class':
            get_item = 'obj.' + property_name
        elif obj_type == 'dict':
            get_item = 'obj["' + property_name +'"]'

        try:
            out = eval(get_item)

            if check_dict:
                out = self.get_dict_value (out, property_name)

        except Exception as ex:
            _str = 'Error "{}" occurred during preparing submission form "{}" for sub-aliquot "{}" ' \
                   'while attempting to evaluate property: "{}". \n{} ' \
                .format(ex, self.form_name, self.sub_aliquot, get_item, traceback.format_exc())
            self.logger.error(_str)
            self.error.add_error(_str)
            out = ''
        return out

    def get_dict_value(self, value, section):
        try:
            return self.fl_cfg_dict.get_item_by_key(section + "/" + value)
        except Exception as ex:
            return value

