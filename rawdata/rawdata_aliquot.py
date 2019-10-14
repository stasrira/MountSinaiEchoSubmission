from file_load import RawData_Text
from file_load import RawData_Excel
from pathlib import Path

class RawDataAliquot():
    def __init__(self, sub_aliquot, request_obl):  # sub_aliquot, rawdata_folder, request_obl, rawdata_row_num =''
        self.sub_aliquot = sub_aliquot
        self.req_obj = request_obl
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = self.req_obj.conf_assay
        self.rawdata_summary_path = ''
        self.loaded = False  # default value
        self.rawdata_summary = {}  # dictionary to hold final rawdata summary data

    def get_rawdata_by_rownum(self, filepath, rawdata_row_num, isexcel = True):
        self.rawdata_summary_path = filepath
        self.rawdata_summary_file = RawData_Excel(self.rawdata_summary_path, self.error, self.logger)
        self.rawdata_summary_file.get_file_content()
        if not self.rawdata_summary_file.loaded:
            # summary file was not loaded property; return with loaded = False
            return
        self.rawdata_summary = self.rawdata_summary_file.get_row_by_number_with_headers(rawdata_row_num)
        self.loaded = True

    # this function is used by csRNAseq and scATACseq assays that have rawdata summary file located in
    # a predefined location and the predefined file name. This info is picked up from a config file
    # All summary files are csv files
    def get_rawdata_predefined_file_text(self, rawdata_folder, rawdata_row_num =''):
        self.rawdata_folder = rawdata_folder

        read_data_method = self.conf_assay['read_rawdata_summary_method']
        rawdata_summary_path = self.conf_assay['rawdata_summary_file']['file_path']  # path to the summary file
        get_data_by = self.conf_assay['rawdata_summary_file']['get_data_by']
        if len(rawdata_row_num) == 0:
            rawdata_row_num = self.conf_assay['rawdata_summary_file']['row_num']

        if read_data_method == 'file_content':
            if len(rawdata_summary_path) > 0:
                # particular file name hast to be found
                self.rawdata_summary_path = str(Path('/'.join([self.rawdata_folder, rawdata_summary_path])))
            else:
                pass

        if len(self.rawdata_summary_path) == 0:
            _str = 'Was not able to identify raw data summary file for sub-aliquot: "{}"'.format(self.sub_aliquot)
            self.logger.error(_str)
            self.error.add_error(_str)
            return

        self.rawdata_summary_file = RawData_Text(self.rawdata_summary_path, self.error, self.logger)
        self.rawdata_summary_file.get_file_content()
        if not self.rawdata_summary_file.loaded:
            # summary file was not loaded property; return with loaded = False
            return

        if get_data_by == 'row_num':
            self.rawdata_summary = self.rawdata_summary_file.get_row_by_number_with_headers(rawdata_row_num)

        self.loaded = True
