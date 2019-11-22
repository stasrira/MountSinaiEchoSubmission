from file_load import Data_Retrieval_Text
from file_load import Data_Retrieval_Excel
from pathlib import Path


class DataRetrievalAliquot():
    def __init__(self, sub_aliquot, request_obl):  # sub_aliquot, data_folder, request_obj, file_row_num =''
        self.sub_aliquot = sub_aliquot
        self.req_obj = request_obl
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = self.req_obj.conf_assay
        self.data_loc_path = ''
        self.data_file = None
        self.data_folder = None
        self.loaded = False  # default key
        self.data_retrieved = {}  # dictionary to hold final data_retrieval summary data

    def get_data_by_rownum(self, filepath, data_row_num, header_row_num=1, isexcel=True):
        self.data_loc_path = filepath
        if isexcel:
            self.data_file = Data_Retrieval_Excel(self.data_loc_path, self.error, self.logger)
        else:
            self.data_file = Data_Retrieval_Text(self.data_loc_path, self.error, self.logger)
        self.data_file.header_row_num = header_row_num
        final_row_num = data_row_num + header_row_num - 1  # add given row number to the header row num to get actual
        # row number needed in the file
        # (deduct 1 to accommodate header row)
        self.data_file.get_file_content()
        if not self.data_file.loaded:
            # summary file was not loaded property_val; return with loaded = False
            self.loaded = False
        else:
            self.data_retrieved = self.data_file.get_row_by_number_with_headers(final_row_num)  # data_row_num
            self.loaded = True

    # this function is used by csRNAseq and scATACseq assays that have data_retrieval summary file located in
    # a predefined location with a predefined file name. This info is picked up from a config file
    # All summary files are csv files
    def get_data_from_predefined_file_text(self, config_source, data_folder, file_row_num=''):
        self.data_folder = data_folder

        data_file_path = config_source['search_method']['single_file_path']  # path to the summary file
        get_data_by = config_source['file_content_details']['get_data_by']
        if len(file_row_num) == 0:
            file_row_num = config_source['file_content_details']['get_by_row_num']['row_num']

        if len(data_file_path) > 0:
            # particular file name hast to be found
            self.data_loc_path = str(Path('/'.join([self.data_folder, data_file_path])))
        else:
            pass

        if len(self.data_loc_path) == 0:
            _str = 'Was not able to identify raw data summary file for sub-aliquot: "{}"'.format(self.sub_aliquot)
            self.logger.error(_str)
            self.error.add_error(_str)
            return

        self.data_file = Data_Retrieval_Text(self.data_loc_path, self.error, self.logger)
        self.data_file.get_file_content()
        if not self.data_file.loaded:
            # summary file was not loaded property_val; return with loaded = False
            return

        if get_data_by == 'row_num':
            self.data_retrieved = self.data_file.get_row_by_number_with_headers(file_row_num)
            self.loaded = True
        else:
            _str = "Unexpected key of 'file_content_details/get_data_by' ({}) was provided. " \
                   "No data retrieval was completed.".format(get_data_by)
            self.logger.warning(_str)
            self.loaded = False

    '''
    # this function is used by csRNAseq and scATACseq assays that have data_retrieval summary file located in
    # a predefined location with a predefined file name. This info is picked up from a config file
    # All summary files are csv files
    def get_processed_data_predefined_file_text_original (self, rawdata_folder, rawdata_row_num=''):
        self.data_folder = rawdata_folder

        read_data_method = self.conf_assay['read_rawdata_summary_method']
        rawdata_summary_path = self.conf_assay['data_file']['file_path']  # path to the summary file
        get_data_by = self.conf_assay['data_file']['get_data_by']
        if len(rawdata_row_num) == 0:
            rawdata_row_num = self.conf_assay['data_file']['row_num']

        if read_data_method == 'file_content':
            if len(rawdata_summary_path) > 0:
                # particular file name hast to be found
                self.data_loc_path = str(Path('/'.join([self.data_folder, rawdata_summary_path])))
            else:
                pass

        if len(self.data_loc_path) == 0:
            _str = 'Was not able to identify raw data summary file for sub-aliquot: "{}"'.format(self.sub_aliquot)
            self.logger.error(_str)
            self.error.add_error(_str)
            return

        self.data_file = Data_Retrieval_Text(self.data_loc_path, self.error, self.logger)
        self.data_file.get_file_content()
        if not self.data_file.loaded:
            # summary file was not loaded property_val; return with loaded = False
            return

        if get_data_by == 'row_num':
            self.data_retrieved = self.data_file.get_row_by_number_with_headers(rawdata_row_num)

        self.loaded = True
    '''
