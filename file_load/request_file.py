# import os
from pathlib import Path
import time
import xlrd
# import logging
from utils import global_const as gc
from utils.log_utils import setup_logger_common
# from file_load.file_utils import StudyConfig
# from collections import OrderedDict
from utils import ConfigData
from file_load import File # , MetaFileExcel
from file_load.file_error import RequestError
from raw_data_request import RawDataRequest
from raw_data_attachments import RawDataAttachment

class Request(File):

    def __init__(self, filepath, cfg_path='', file_type=2, sheet_name=''):

        # load_configuration (main_cfg_obj) # load global and local configureations

        File.__init__(self, filepath, file_type)
        self.error = RequestError(self)

        self.logger = self.setup_logger(self.wrkdir, self.filename)
        self.logger.info('Start working with Submission request file {}'.format(filepath))

        # self.file_dict = OrderedDict()
        # self.rows = OrderedDict()

        self.columnlist = []
        self.aliquots = []
        self.sub_aliquots = []
        self.project = ''
        self.exposure = ''
        self.center = ''
        self.source_spec_type = ''
        self.assay = ''

        # self.sheet_name = ''
        self.sheet_name = sheet_name.strip()
        if not self.sheet_name or len(self.sheet_name) == 0:
            # if sheet name was not passed as a parameter, try to get it from config file
            self.sheet_name = gc.REQUEST_EXCEL_WK_SHEET_NAME  # 'wk_sheet_name'
        # print (self.sheet_name)
        self.logger.info('Data will be loaded from worksheet: "{}"'.format(self.sheet_name))

        self.get_file_content()

        self.conf_assay = None

    def get_file_content(self):
        if not self.columnlist:
            if self.file_exists(self.filepath):
                self.logger.debug('Loading file content of "{}"'.format(self.filepath))

                with xlrd.open_workbook(self.filepath) as wb:
                    if not self.sheet_name or len(self.sheet_name) == 0:
                        # by default retrieve the first sheet in the excel file
                        sheet = wb.sheet_by_index(0)
                    else:
                        # if sheet name was provided
                        sheets = wb.sheet_names()  # get list of all sheets
                        if self.sheet_name in sheets:
                            # if given sheet name in the list of available sheets, load the sheet
                            sheet = wb.sheet_by_name(self.sheet_name)
                        else:
                            # report an error if given sheet name not in the list of available sheets
                            _str = ('Given worksheet name "{}" was not found in the file "{}". '
                                    'Verify that the worksheet name exists in the file.').format(
                                self.sheet_name, self.filepath)
                            self.error.add_error(_str)
                            self.logger.error(_str)

                            self.lineList = None
                            self.loaded = False
                            return self.lineList

                sheet.cell_value(0, 0)

                for i in range(sheet.ncols):
                    column = []
                    for j in range(sheet.nrows):
                        # print(sheet.cell_value(i, j))
                        # column.append('"' + sheet.cell_value(i,j) + '"')
                        cell = sheet.cell(j, i)
                        cell_value = cell.value
                        # take care of number and dates received from Excel and converted to float by default
                        if cell.ctype == 2 and int(cell_value) == cell_value:
                            # the value is integer
                            cell_value = str(int(cell_value))
                        elif cell.ctype == 2:
                            # the value is float
                            cell_value = str(cell_value)
                        # convert date back to human readable date format
                        # print ('cell_value = {}'.format(cell_value))
                        if cell.ctype == 3:
                            cell_value_date = xlrd.xldate_as_datetime(cell_value, wb.datemode)
                            cell_value = cell_value_date.strftime("%Y-%m-%d")
                        column.append(cell_value)

                    self.columnlist.append(','.join(column))

                wb.unload_sheet(sheet.name)

                #load passed request parameters (by columns)
                self.get_request_parameters ()

                # validate provided information
                self.logger.info('Validating provided request parameters. Project: "{}", Exposure: "{}", '
                                 'Center: "{}", Source specimen type: "{}", Sub-Aliquots: "{}", Aliquots: "{}"'
                                 .format(self.project, self.exposure, self.center, self.source_spec_type,
                                         self.sub_aliquots, self.aliquots))
                self.validate_request_params()

                if self.error.exist():
                    # report that errors exist
                    self.loaded = False
                    # print(self.error.count)
                    # print(self.error.get_errors_to_str())
                    _str = 'Errors ({}) were identified during validating of the request. \nError(s): {}'.format(
                        self.error.count, self.error.get_errors_to_str())
                else:
                    self.loaded = True
                    _str = 'Request parameters were successfully validated - no errors found.'
                self.logger.info(_str)

            else:
                _str = 'Loading content of the file "{}" failed since the file does not appear to exist".'.format(
                    self.filepath)
                self.error.add_error(_str)
                self.logger.error(_str)

                self.columnlist = None
                self.loaded = False
        return self.lineList

    def get_request_parameters(self):
        self.project = self.columnlist[0].split(',')[1]
        self.exposure = self.columnlist[1].split(',')[1]
        self.center = self.columnlist[2].split(',')[1]
        self.source_spec_type = self.columnlist[3].split(',')[1]
        self.assay = self.columnlist[4].split(',')[1]
        self.sub_aliquots = self.columnlist[5].split(',')
        if self.sub_aliquots and len(self.sub_aliquots) > 0:
            self.sub_aliquots.pop(0)
        self.aliquots =  self.columnlist[6].split(',')
        if self.aliquots and len(self.aliquots) > 0:
            self.aliquots.pop(0)

    # validates provided parameters (loaded from the submission request file)
    def validate_request_params(self):
        # TODO: Add validation of provided values against a dictionary (located on another tab) from the request file
        _str_err = ''
        _str_warn = ''
        if len(self.sub_aliquots) == 0:
            _str_err = '\n'.join ([_str_err, 'List of provided sub-aliquots is empty. ' \
                                    'Aborting processing of the submission request.'])
        # Check if empty sub-aliquots were provided
        if '' in self.sub_aliquots:
            i = 0
            cleaned_cnt = 0
            for s, a in zip(self.sub_aliquots, self.aliquots):
                # check for any empty sub-aliquot values and remove them. Also remove corresponded Aliquot values
                if len(s.strip()) == 0:
                    self.sub_aliquots.pop(i)
                    self.aliquots.pop(i)
                    cleaned_cnt += 1
                else:
                    i += 1
            if cleaned_cnt > 0:
                _str_warn = '\n'.join ([_str_warn, 'Empty sub-aliqouts (count = {}) were removed from the list. '
                                        'Here is the list of sub-aliqouts after cleaning (count = {}): "{}" '
                                       .format(cleaned_cnt, len(self.sub_aliquots), self.sub_aliquots)])
        if len(self.project) == 0:
            _str_err = '\n'.join ([_str_err, 'No Project name was provided. Aborting processing of the submission request.'])
        if len(self.exposure) == 0:
            _str_err = '\n'.join ([_str_err, 'No Exposure was provided. Aborting processing of the submission request.'])
        if len(self.center) == 0:
            _str_err = '\n'.join ([_str_err, 'No Center was provided. Aborting processing of the submission request.'])
        if len(self.source_spec_type) == 0:
            _str_err = '\n'.join ([_str_err, 'No Specimen type was provided. Aborting processing of the submission request.'])
        if len(self.assay) == 0:
            _str_err = '\n'.join ([_str_err, 'No Assay was provided. Aborting processing of the submission request.'])

        # report any collected errors
        if len(_str_err) > 0:
            _str_err = 'Validation of request parameters:' + _str_err
            self.error.add_error(_str_err)
            self.logger.error(_str_err)
        # report any collected warnings
        if len(_str_warn) > 0:
            _str_warn = 'Validation of request parameters:' + _str_warn
            self.logger.warning(_str_warn)

    def setup_logger(self, wrkdir, filename):

        m_cfg = ConfigData(gc.CONFIG_FILE_MAIN)

        log_folder_name = gc.LOG_FOLDER_NAME

        # m_logger_name = gc.MAIN_LOG_NAME
        # m_logger = logging.getLogger(m_logger_name)

        logger_name = gc.REQUEST_LOG_NAME
        logging_level = m_cfg.get_value('Logging/request_log_level')

        lg = setup_logger_common(logger_name, logging_level,
                                 Path(wrkdir) / log_folder_name,
                                 str(filename) + '_' + time.strftime("%Y%m%d_%H%M%S", time.localtime()) + '.log')

        self.log_handler = lg['handler']
        return lg['logger']

    def process_request(self):
        self.conf_assay =  self.load_assay_conf(self.assay)
        self.raw_data = RawDataRequest(self)
        self.attachments = RawDataAttachment(self)
        print()

    def load_assay_conf(self, assay):
        cfg_assay = ConfigData(gc.CONFIG_FILE_ASSAY)
        return cfg_assay.get_value(assay.upper())
