from data_retrieval import DataRetrieval
from pathlib import Path
from data_retrieval import DataRetrievalAliquot


class DataSource(DataRetrieval):
    def __init__(self, request_obj, data_source_id, data_source_name):
        self.data_source_id = data_source_id
        self.data_source_name = data_source_name
        DataRetrieval.__init__(self, request_obj)
        self.cnf_data_source = None

    def init_specific_settings(self):
        # this function is called by the base class to perform actions specific to the current class' needs
        self.cnf_data_source = self.conf_assay[self.data_source_id]
        cnf_data_source = self.cnf_data_source
        last_part_path = cnf_data_source['sub_folder']
        data_source_loc = cnf_data_source['location']
        self.data_loc = Path(self.convert_aliquot_properties_to_path(data_source_loc, last_part_path))
        self.logger.info('Data location for the current data source "{}" is "{}"'
                          .format(self.data_source_name, self.data_loc))
        # print (self.data_loc)
        search_by = cnf_data_source['search_method']['search_by']
        search_deep_level = cnf_data_source['search_method']['search_deep_level_max']
        exclude_dirs = cnf_data_source['search_method']['exclude_folders']

        # check if exact_aliquot_match value was provided for current data source
        if 'exact_aliquot_match' in cnf_data_source['search_method']:
            # if it was provided, save to a object level variable
            self.exact_aliquot_match = cnf_data_source['search_method']['exact_aliquot_match']

        if search_by == 'folder_name':
            # search_deep_level = cnf_data_source['search_method']['search_deep_level_max']
            # exclude_dirs = cnf_data_source['search_method']['exclude_folders']
            self.get_data_by_folder_name(search_deep_level, exclude_dirs, self.data_loc)
        elif search_by == 'file_content':
            # search_deep_level = cnf_data_source['search_method']['search_deep_level_max']
            # exclude_dirs = cnf_data_source['search_method']['exclude_folders']
            file_ext = cnf_data_source['search_method']['file_ext']  # self.conf_assay['rawdata_summary_file_ext']
            data_file_struct = {
                'worksheet': cnf_data_source['file_content_details']['excel']['sheet_name'],
                'header_row_num': cnf_data_source['file_content_details']['get_by_primary_key']['header_row_number'],
                'col_num': cnf_data_source['file_content_details']['get_by_primary_key']['pk_column_number'],
                'exlude_header': True
                }
            self.get_data_by_file_content(search_deep_level, exclude_dirs, file_ext, data_file_struct)

        # check if some data_retrieval was assigned to an aliquot and warn if none were assigned
        for sa in self.req_obj.sub_aliquots:
            if sa not in self.aliquots_data_dict:
                # no data was assigned to aliquot
                _str = 'Aliquot "{}" was not assigned with any {}.'.format(sa, self.data_source_name)
                self.logger.warning(_str)
                self.req_obj.disqualify_sub_aliquot(sa, _str)
                # self.error.add_error(_str)

    def get_data_for_aliquot(self, sa, directory):
        # this function is called from the based class to get data for a particular aliquot found in the give dir
        rda = DataRetrievalAliquot(sa, self.req_obj)
        rda.get_data_from_predefined_file_text(self.cnf_data_source, directory)
        if rda.loaded:
            _str = '{} for sub-aliquot "{}" was successfully loaded from sub-aliquot ' \
                   'data location "{}".' \
                .format(self.data_source_name, sa, directory)
            self.aliquots_data_dict[sa] = rda.data_retrieved
            self.logger.info(_str)
        else:
            _str = '{} for aliquot "{}" failed to load from sub-aliquot ' \
                   'data location "{}"; see earlier error(s) in this log.' \
                .format(self.data_source_name, sa, directory)
            self.logger.warning(_str)
