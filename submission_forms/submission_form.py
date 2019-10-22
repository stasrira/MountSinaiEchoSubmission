from file_load import File_Json
import os
from pathlib import Path
from utils import global_const as gc
from utils import ConfigData

class SubmissionForm():
    def __init__(self, form_name, request, sub_aliquot):
        self.forma_name = form_name
        self.req_obj = request  # reference to the current request object
        self.sub_aliquot = sub_aliquot
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay
        self.prepare_form(form_name)

    def prepare_form(self, form_name):
        # identify paths for json and config (yaml) files
        fl_path_json = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '.json')
        fl_path_cfg_common = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '.yaml')
        fl_path_cfg_assay = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '_' + str(self.req_obj.assay).lower() + '.yaml')

        # load json and config files
        fl_json = File_Json(fl_path_json, self.req_obj.error, self.req_obj.logger)
        self.json_form = fl_json
        fl_cfg_common = ConfigData(fl_path_cfg_common)
        self.fl_cfg_common = fl_cfg_common
        fl_cfg_assay = ConfigData(fl_path_cfg_assay)
        self.fl_cfg_assay = fl_cfg_assay

        print(fl_json.json_data)
        self.get_json_keys(fl_json.json_data)
        print(fl_json.json_data)
        print ()

    def get_json_keys(self, json_node, parent_keys=''):
        for key, val in json_node.items():
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

                json_node[key] = self.eval_cfg_value(key, self.fl_cfg_assay.get_value(key), self.fl_cfg_common.get_value(key))

                print(key, json_node[key])

    def eval_cfg_value(self, key, assay_cfg_val, common_cfg_val):
        # if assay config value is not provided, use common assay val
        if assay_cfg_val:
            cfg_val = assay_cfg_val
        else:
            cfg_val = common_cfg_val

        #TODO: move values for the following 2 constants to Global Config file
        eval_flag = 'eval!'
        yaml_path_flag = '!yaml_path!'
        #make sure that cfg_val is defined
        if cfg_val:
            if eval_flag in cfg_val:
                cfg_val = cfg_val.replace(eval_flag, '', 1) #replace 'eval!' flag value
                cfg_val = cfg_val.replace(yaml_path_flag, "'" + key + "'", 1)  # replace 'eval!' flag value
                if not cfg_val[0:5] == 'self.':
                    cfg_val = 'self.'+ cfg_val
                out_val = eval(cfg_val)
            else:
                out_val = cfg_val
        return out_val

    def get_value(self, key):
        # str = 'GET VALUE CALL, parameter: {}'.format(key)
        out = ''
        if key == 'assay':
            out = 'ASSAY WAS NOT DEFINED' # self.req_obj.assay
        elif key == 'experiment_id':
            out = 'TODO: Define Experiment ID'
        return out