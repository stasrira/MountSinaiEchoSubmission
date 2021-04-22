from file_load import FileJson
from pathlib import Path
import os
from utils import global_const as gc
from utils import common as cm
from utils import common2 as cm2
from utils import ConfigData
import traceback
import jsonschema
from jsonschema import validate


class SubmissionForm:
    def __init__(self, form_name, request, sub_aliquot, aliquot, sample, form_file_name_id = None):
        self.form_name = form_name
        if not form_file_name_id:
            form_file_name_id = form_name
        self.form_file_name_id = form_file_name_id
        self.req_obj = request  # reference to the current request object
        self.sub_aliquot = sub_aliquot
        self.aliquot = aliquot
        self.sample = sample
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay

        self.fl_json = None
        self.fl_json_schema = None
        self.fl_cfg_common = None
        self.fl_cfg_assay = None
        # self.fl_cfg_dict = None

        self.prepare_form(form_name)

    def prepare_form(self, form_name):
        # identify paths for json and config (yaml) files
        fl_path_json_common = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '.json')
        fl_path_json_assay = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '_' + str(
            self.req_obj.assay).lower() + '.json')
        fl_path_json_schema = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '_schema.json')
        fl_path_cfg_common = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '.yaml')
        fl_path_cfg_assay = Path(gc.SUBMISSION_FORMS_DIR + '/' + form_name + '/' + form_name + '_' + str(
            self.req_obj.assay).lower() + '.yaml')

        # check if assay specific json exists; if yes - use it, if not - use common one
        if cm.file_exists(fl_path_json_assay):
            fl_path_json = fl_path_json_assay
        else:
            fl_path_json = fl_path_json_common

        # load json and config files
        self.fl_json = FileJson(fl_path_json, self.req_obj.error, self.req_obj.logger)
        self.fl_json_schema = FileJson(fl_path_json_schema, self.req_obj.error, self.req_obj.logger)
        self.fl_cfg_common = ConfigData(fl_path_cfg_common)
        self.fl_cfg_assay = ConfigData(fl_path_cfg_assay)
        # self.fl_cfg_dict = ConfigData(gc.CONFIG_FILE_DICTIONARY)

        # print(self.fl_json.json_data)
        # loop through all json keys and fill those with associated data
        self.get_json_keys(self.fl_json.json_data)
        # print(self.fl_json.json_data)

        # validate final json file against json schema (if present)
        self.validate_json(self.fl_json, self.fl_json_schema)

    def get_json_keys(self, json_node, parent_keys=''):
        for key, val in json_node.items():
            # TODO: add functionality to handle JSON arrays (if those are needed)
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

                val = self.eval_cfg_value(full_key_name,
                                          self.fl_cfg_assay.get_value(full_key_name),
                                          self.fl_cfg_common.get_value(full_key_name))
                # assign retrieved key back to associated json key
                json_node[key] = val
                '''
                if not str(val).strip() == '':
                    # if key is not empty, assing it as is
                    json_node[key] = val
                elif isinstance(val, list):
                    # if key is empty and a type of list, assign it as is
                    json_node[key] = val
                else:
                    # if key is blank and did not qualify for any previous conditions, assign Null (None)
                    json_node[key] = None
                '''
                # print(key, '==>', json_node[key])
                pass

    def eval_cfg_value(self, key, assay_cfg_val, common_cfg_val):
        # if assay config key is not provided, use common assay val
        if assay_cfg_val:
            cfg_val = assay_cfg_val
        else:
            cfg_val = common_cfg_val

        eval_flag = gc.SUBMISSION_YAML_EVAL_FLAG  # 'eval!'

        # check if some configuration instruction/key was retrieved for the given "key"
        if cfg_val:
            if eval_flag in str(cfg_val):
                cfg_val = cfg_val.replace(eval_flag, '')  # replace 'eval!' flag key
                try:
                    out_val = eval(cfg_val)
                except Exception as ex:
                    _str = 'Error "{}" occurred during preparing submission form "{}" for sub-aliquot "{}" ' \
                           'while attempting to interpret configuration key "{}" provided for the form\'s key ' \
                           '"{}". \n{} ' \
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

    def get_tarball_property(self, sa, val_type):

        value = ''
        if self.req_obj.attachments:
            tar_obj = self.req_obj.attachments.aliquots_tarball_dict[sa]
            if tar_obj:
                if val_type == 'name':
                    value = os.path.basename(tar_obj['path'])
                elif val_type == 'md5':
                    value = tar_obj['md5']
        return value

    # it will retrieve any existing property_val from the request object
    def get_request_value(self, property_name, check_dict=False):
        return self.get_property_value_from_object(self.req_obj, property_name, check_dict)

    # it will retrieve any existing property_val from the submission_form object
    def get_submission_form_value(self, property_name, check_dict=False):
        return self.get_property_value_from_object(self, property_name, check_dict)

    # it will retrieve any existing property_val from rawdata object
    def get_rawdata_value(self, property_name, check_dict=False):
        # return self.get_property_value_from_object(self.req_obj.raw_data.aliquots_data_dict[self.sub_aliquot],
        #                                            property_name, check_dict, 'dict')
        return self.get_sourcedata_value('rawdata', property_name, check_dict)

    # it will retrieve any existing property_val from assay data object
    def get_assaydata_value_by_col_number(self, col_num, check_dict=False):
        # obj = list(self.req_obj.assay_data.aliquots_data_dict[self.sub_aliquot].items())
        # val = self.get_property_value_from_object(obj, col_num - 1, check_dict, 'dict', 'number')
        # if isinstance(val, tuple):
        #     return val[1]
        # else:
        #     return val
        return self.get_sourcedata_value_by_col_number('assaydata', col_num, check_dict)

    # it will retrieve any existing property_val from assay data object
    def get_assaydata_value(self, property_name, check_dict=False):
        # return self.get_property_value_from_object(self.req_obj.assay_data.aliquots_data_dict[self.sub_aliquot],
        #                                            property_name, check_dict, 'dict')
        return self.get_sourcedata_value ('assaydata', property_name, check_dict)

    # it will retrieve any existing property_val (specified by the name) from the data source object
    # specified by the data_source_name
    def get_sourcedata_value(self, data_source_name, property_name, check_dict=False):
        if data_source_name in self.req_obj.data_source_names:
            return self.get_property_value_from_object(
                self.req_obj.data_source_objects[data_source_name].aliquots_data_dict[self.sub_aliquot],
                property_name, check_dict, 'dict')
        else:
            _str = 'Data source name ({}) requested during populating json submission form "{}" for aliquot id ' \
                   '"{}" does not exists for the current assay.'.format(data_source_name, self.form_name, self.aliquot)
            self.logger.error(_str)
            self.error.add_error(_str)
            return '#ERROR#'

    # it will retrieve any existing property_val (specified by the column number) from the data source object
    # specified by the data_source_name
    def get_sourcedata_value_by_col_number(self, data_source_name, col_num, check_dict=False):
        if data_source_name in self.req_obj.data_source_names:
            obj = list(self.req_obj.data_source_objects[data_source_name].aliquots_data_dict[self.sub_aliquot].items())
            val = self.get_property_value_from_object(obj, col_num - 1, check_dict, 'dict', 'number')
            if isinstance(val, tuple):
                return val[1]
            else:
                return val
        else:
            _str = 'Data source name ({}) requested during populating json submission form "{}" for aliquot id ' \
                   '"{}" does not exists for the current assay.'.format(data_source_name, self.form_name, self.aliquot)
            self.logger.error(_str)
            self.error.add_error(_str)
            return '#ERROR#'

    # it will retrieve a key of a property_val named in "property_val" parameter
    # from the object passed as a reference in "obj" parameter
    # obj_type possible values: "class" (type of "obj" is class),
    #                           "dict" (type of "obj" is dictionary)
    # property_type possible values: "name" ("property_val" is name of property_val),
    #                                "number" ("property_val" is number of items in dictionary)
    # noinspection PyUnusedLocal
    def get_property_value_from_object(self, obj, property_val, check_dict=False,
                                       obj_type='class', property_type='name'):
        property_val = str(property_val)
        if property_type == 'name':
            # if property_val name is given, proceed here
            if obj_type == 'class':
                get_item = 'obj.' + property_val
            elif obj_type == 'dict':
                get_item = 'obj["' + property_val + '"]'
            else:
                get_item = None
        else:
            # if column number is given, proceed here
            get_item = 'obj[' + property_val + ']'

        try:
            out = eval(get_item)

            if check_dict:
                out = cm2.get_dict_value(out, property_val)

        except Exception as ex:
            _str = 'Error "{}" occurred during preparing submission form "{}" for sub-aliquot "{}" ' \
                   'while attempting to evaluate property_val: "{}". \n{} ' \
                .format(ex, self.form_name, self.sub_aliquot, get_item, traceback.format_exc())
            self.logger.error(_str)
            self.error.add_error(_str)
            out = ''
        return out

    # converts an array of values (i.e. list of aliquots) in to list of dictionaries with a given key name
    # For example: [1, 2, 3] => [{name: 1}, {name: 2}, {name: 3}]
    @staticmethod
    def convert_simple_list_to_list_of_dict(sm_arr, key_name):
        out = []
        for a in sm_arr:
            dict_ob = {key_name: a}
            out.append(dict_ob)
        return out

    def validate_json(self, json_file, schema_file):
        try:
            validate(json_file.json_data, schema_file.json_data)
            _str = 'Validation of "{}" against "{}" was successful.'.format(json_file.filepath, schema_file.filepath)
            self.logger.info(_str)
        except jsonschema.exceptions.ValidationError as ve:
            _str = 'Validation of "{}" file against schema "{}" failed with the following error: \n{}' \
                .format(json_file.filepath, schema_file.filepath, ve)
            self.logger.error(_str)
            self.error.add_error(_str)
