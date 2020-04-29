from pathlib import Path
import os
import stat
import traceback
import time
import xlrd
from utils import global_const as gc
from utils import common as cm
from utils import common2 as cm2
from utils import setup_logger_common
from utils import ConfigData
from file_load import File  # , MetaFileExcel
from file_load.file_error import RequestError
# from data_retrieval import RawData # DataRetrieval
from data_retrieval import DataSource, Attachment, DataSourceDB
# from data_retrieval import Attachment
from forms import SubmissionPackage
import xlwt


class Request(File):

    def __init__(self, filepath, cfg_path='', file_type=2, sheet_name=''):

        # load_configuration (main_cfg_obj) # load global and local configureations

        File.__init__(self, filepath, file_type)

        if cfg_path=='':
            self.conf_main = ConfigData(gc.CONFIG_FILE_MAIN)
        else:
            self.conf_main = ConfigData(cfg_path)

        self.error = RequestError(self)

        self.log_handler = None
        self.logger = self.setup_logger(self.wrkdir, self.filename)
        self.logger.info('Start working with Submission request file {}'.format(filepath))

        # self.file_dict = OrderedDict()
        # self.rows = OrderedDict()

        self.columnlist = []
        self.samples = []
        self.sub_aliquots = []
        self.disqualified_sub_aliquots = {}
        self.disqualified_request_path = ''  # will store path to a request file with disqualified sub-aliquots
        self.project = ''
        self.exposure = ''
        self.center = ''
        self.source_spec_type = ''
        self.assay = ''
        self.experiment_id = ''

        self.aliquots = None
        self.qualified_aliquots = None
        self.raw_data = None
        self.assay_data = None
        self.attachments = None
        self.submission_forms = None
        self.submission_package = None
        self.data_sources = None
        self.type = None
        self.metadata_db = None

        # self.sheet_name = ''
        self.sheet_name = sheet_name.strip()
        if not self.sheet_name or len(self.sheet_name) == 0:
            # if sheet name was not passed as a parameter, try to get it from config file
            self.sheet_name = gc.REQUEST_EXCEL_WK_SHEET_NAME  # 'wk_sheet_name'
        # print (self.sheet_name)
        self.logger.info('Data will be loaded from worksheet: "{}"'.format(self.sheet_name))

        self.conf_process_entity = None

        self.get_file_content()

    def get_file_content(self):
        if not self.columnlist:
            if cm.file_exists(self.filepath):
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

                lines = []  # will hold content of the request file as an array of arrays (rows)
                for i in range(sheet.ncols):
                    column = []
                    for j in range(sheet.nrows):
                        if i == 0:
                            lines.append([])  # adds an array for each new row in the request file

                        # print(sheet.cell_value(i, j))
                        cell = sheet.cell(j, i)
                        cell_value = cell.value
                        # take care of number and dates received from Excel and converted to float by default
                        if cell.ctype == 2 and int(cell_value) == cell_value:
                            # the key is integer
                            cell_value = str(int(cell_value))
                        elif cell.ctype == 2:
                            # the key is float
                            cell_value = str(cell_value)
                        # convert date back to human readable date format
                        # print ('cell_value = {}'.format(cell_value))
                        if cell.ctype == 3:
                            cell_value_date = xlrd.xldate_as_datetime(cell_value, wb.datemode)
                            cell_value = cell_value_date.strftime("%Y-%m-%directory")
                        column.append(cell_value)  # adds value to the current column array
                        lines[j].append('"' + str(cell_value) + '"')  # adds value in "csv" format for a current row

                    # self.columnlist.append(','.join(column))
                    self.columnlist.append (column)  # adds a column to a list of columns

                # populate lineList property
                self.lineList = []
                for ln in lines:
                    self.lineList.append(','.join(ln))

                wb.unload_sheet(sheet.name)

                # load passed request parameters (by columns)
                self.get_request_parameters()
                # Log type of the request being processed
                self.logger.info('Current request Type was identified as "{}"'.format(self.type))

                # to support decision of not supplying Project Name from Request file,
                # it will be retrieved from gc module
                self.project = gc.PROJECT_NAME

                # validate provided information
                self.logger.info('Validating provided request parameters. Exposure: "{}", '
                                 'Center: "{}", Source specimen type: "{}", Experiment: {}, '
                                 'Sub-Aliquots: "{}", Aliquots: "{}"'
                                 .format(self.exposure, self.center, self.source_spec_type,
                                         self.experiment_id, self.sub_aliquots, self.samples))
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

                # calculate Experiment_id out of request paramaters
                self.experiment_id = "_".join([self.exposure, self.center, self.source_spec_type, self.assay])

            else:
                _str = 'Loading content of the file "{}" failed since the file does not appear to exist".'.format(
                    self.filepath)
                self.error.add_error(_str)
                self.logger.error(_str)

                self.columnlist = None
                self.lineList = None
                self.loaded = False
        return self.lineList

    # get all values provided in the request file
    def get_request_parameters(self):
        col_count = len(self.columnlist)
        if col_count < 7:
            # if 7th column is not provided, assume that it is a Sequence request and set request's type appropriately
            # otherwise the type value will be received from the file
            self.type = gc.DEFAULT_REQUEST_TYPE.lower()

        for i in range(col_count):
            if len(self.columnlist[i]) > 1:
                first_val = self.columnlist[i][1]
            else:
                first_val = ''

            if i == 0:
                self.exposure = first_val
            elif i == 1:
                self.center = first_val
            elif i == 2:
                self.source_spec_type = first_val
            elif i == 3:
                self.assay = first_val.lower()
            elif i == 4:
                self.sub_aliquots = self.columnlist[i]
                if self.sub_aliquots and len(self.sub_aliquots) > 0:
                    self.sub_aliquots.pop(0)  # get rid of the column header
            elif i == 5:
                self.samples = self.columnlist[i]
                if self.samples and len(self.samples) > 0:
                    self.samples.pop(0)  # get rid of the column header
            elif i == 6:
                self.type = first_val.lower()
                if len(self.type.strip()) == 0:
                    # if request type was not provided, assume it is a default type
                    self.type = gc.DEFAULT_REQUEST_TYPE.lower()
            else:
                break

    # validates provided parameters (loaded from the submission request file)
    def validate_request_params(self):
        if self.type == 'sequence':
            self.validate_request_params_sequence()
        elif self.type == 'metadata':
            self.validate_request_params_metadata()
        else:
            _str_err = 'Supplied request type value "{}" is not expected! Aborting processing of the ' \
                       'submission request.'.format(self.type)
            self.error.add_error(_str_err)
            self.logger.error(_str_err)

    def validate_request_params_sequence(self):
        _str_err = ''
        _str_warn = ''
        if len(self.sub_aliquots) == 0:
            _str_err = '\n'.join([_str_err, 'List of provided sub-samples is empty. '
                                            'Aborting processing of the submission request.'])
        # Check if empty sub-aliquots were provided
        if self.sub_aliquots and '' in self.sub_aliquots:
            i = 0
            cleaned_cnt = 0
            for s, a in zip(self.sub_aliquots, self.samples):
                # check for any empty sub-aliquot values and remove them. Also remove corresponded Aliquot values
                if len(s.strip()) == 0:
                    self.sub_aliquots.pop(i)
                    self.samples.pop(i)
                    cleaned_cnt += 1
                else:
                    i += 1
            if cleaned_cnt > 0:
                _str_warn = '\n'.join([_str_warn, 'Empty sub-aliqouts (count = {}) were removed from the list. '
                                                  'Here is the list of sub-aliqouts after cleaning (count = {}): "{}" '
                                      .format(cleaned_cnt, len(self.sub_aliquots), self.sub_aliquots)])
        # if len(self.project) == 0:
        #    _str_err = '\n'.join(
        #        [_str_err, 'No Project name was provided. Aborting processing of the submission request.'])
        if len(self.exposure) == 0:
            _str_err = '\n'.join([_str_err, 'No Exposure was provided. Aborting processing of the submission request.'])
        if len(self.center) == 0:
            _str_err = '\n'.join([_str_err, 'No Center was provided. Aborting processing of the submission request.'])
        if len(self.source_spec_type) == 0:
            _str_err = '\n'.join(
                [_str_err, 'No Specimen type was provided. Aborting processing of the submission request.'])
        if len(self.assay) == 0:
            _str_err = '\n'.join([_str_err, 'No Assay was provided. Aborting processing of the submission request.'])
        if not cm2.key_exists_in_dict(self.assay, 'assay'):
            _str_err = '\n'.join([_str_err, 'Provided Assay name "{}" is not matching a list of expected assay names '
                                            '(as stored in "{}" dictionary file). '
                                            'Aborting processing of the submission request.'
                                 .format(self.assay, gc.CONFIG_FILE_DICTIONARY)])
        else:
            # if provided assay name is expected, convert it to the name expected by the Submission logic
            self.assay = cm2.get_dict_value(self.assay, 'assay')
            # get list of aliquots from list of sub-aliquots
            self.aliquots = [cm2.convert_sub_aliq_to_aliquot(al, self.assay) for al in self.sub_aliquots]

        # report any collected errors
        if len(_str_err) > 0:
            _str_err = 'Validation of request parameters:' + _str_err
            self.error.add_error(_str_err)
            self.logger.error(_str_err)
        # report any collected warnings
        if len(_str_warn) > 0:
            _str_warn = 'Validation of request parameters:' + _str_warn
            self.logger.warning(_str_warn)

    def validate_request_params_metadata(self):
        _str_err = ''
        _str_warn = ''
        # Check if empty sub-aliquots were provided
        if self.samples and '' in self.samples:
            i = 0
            cleaned_cnt = 0
            for sa, s in zip(self.sub_aliquots, self.samples):
                # check for any empty sub-aliquot values and remove them. Also remove corresponded Aliquot values
                if len(s.strip()) == 0:
                    self.sub_aliquots.pop(i)
                    self.samples.pop(i)
                    cleaned_cnt += 1
                else:
                    i += 1
            if cleaned_cnt > 0:
                _str_warn = '\n'.join([_str_warn, 'Empty Samples (count = {}) were removed from the list. '
                                                  'Here is the list of samples after cleaning (count = {}): "{}" '
                                      .format(cleaned_cnt, len(self.samples), self.samples)])
        if len(self.center) == 0:
            _str_err = '\n'.join([_str_err, 'No Center was provided. Aborting processing of the submission request.'])

        # TODO: Identify the following fact in requirements for requests
        # for metadata requests column of Sub-aliquots is expected to hold list of aliquots
        self.aliquots = self.sub_aliquots

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

        # m_cfg = ConfigData(gc.CONFIG_FILE_MAIN)

        log_folder_name = gc.REQ_LOG_DIR  # gc.LOG_FOLDER_NAME

        # m_logger_name = gc.MAIN_LOG_NAME
        # m_logger = logging.getLogger(m_logger_name)

        logger_name = gc.REQUEST_LOG_NAME
        logging_level = self.conf_main.get_value('Logging/request_log_level')

        # if a relative path provided, convert it to the absolute address based on the application working dir
        if not os.path.isabs(log_folder_name):
            log_folder_path = Path(wrkdir) / log_folder_name
        else:
            log_folder_path = Path(log_folder_name)

        lg = setup_logger_common(logger_name, logging_level,
                                 log_folder_path,  # Path(wrkdir) / log_folder_name,
                                 str(filename) + '_' + time.strftime("%Y%m%d_%H%M%S", time.localtime()) + '.log')

        self.log_handler = lg['handler']
        return lg['logger']

    def process_request(self):
        if self.type == 'sequence':
            self.conf_process_entity = self.load_assay_conf(self.assay)
        elif self.type == 'metadata':
            self.conf_process_entity = self.load_center_conf(self.center)

        self.data_sources = self.conf_process_entity['data_sources']

        if self.data_sources and 'rawdata' in self.data_sources:
            self.raw_data = DataSource(self, 'rawdata', 'Raw Data')  # RawData(self)
        if self.data_sources and 'assaydata' in self.data_sources:
            self.assay_data = DataSource(self, 'assaydata', 'Assay Data')  # RawData(self)
        if self.data_sources and 'metadata_db' in self.data_sources:
            self.metadata_db = DataSourceDB(self, 'metadata_db', 'Metadata DB')
            self.metadata_db.get_db_data()
        if self.data_sources and 'attachment' in self.data_sources:
            self.attachments = Attachment(self)

        self.submission_package = SubmissionPackage(self)

        self.create_request_for_disqualified_sub_aliquots()

        self.create_trasfer_script_file()

        # check for errors and put final log entry for the request.
        if self.error.exist():
            _str = 'Processing of the current request was finished with the following errors: {}\n'.format(
                self.error.get_errors_to_str())
            self.logger.error(_str)
        else:
            _str = 'Processing of the current request was finished successfully.\n'
            self.logger.info(_str)

    def load_assay_conf(self, assay):
        cfg_assay = ConfigData(gc.CONFIG_FILE_ASSAY)
        return cfg_assay.get_value(assay.upper())

    def load_center_conf(self, center):
        cfg_assay = ConfigData(gc.CONFIG_FILE_CENTER)
        return cfg_assay.get_value(center.upper())

    def create_trasfer_script_file(self):
        self.logger.info("Start preparing transfer_script.sh file.")
        # path for the script file being created
        sf_path = Path(self.submission_package.submission_dir + "/transfer_script.sh")

        #get script file template
        with open('scripts/transfer_script.sh', 'r') as ft:
            scr_tmpl = ft.read()

        #update placeholders in the script with the actual values
        scr_tmpl = scr_tmpl.replace("{!smtp!}", self.conf_main.get_value("Email/smtp_server") + ":"
                                    + str(self.conf_main.get_value("Email/smtp_server_port")))
        scr_tmpl = scr_tmpl.replace("{!to_email!}", self.conf_main.get_value("Email/sent_to_emails"))
        scr_tmpl = scr_tmpl.replace("{!from_email!}", self.conf_main.get_value("Email/default_from_email"))
        scr_tmpl = scr_tmpl.replace("{!send_email_flag!}", str(self.conf_main.get_value("Email/send_emails")))
        scr_tmpl = scr_tmpl.replace("{!source_dir!}", self.submission_package.submission_dir)
        scr_tmpl = scr_tmpl.replace("{!target_dir!}", self.conf_main.get_value("DataTransfer/remote_target_dir"))
        scr_tmpl = scr_tmpl.replace("{!ssh_user!}", self.conf_main.get_value("DataTransfer/ssh_user"))

        set_permissions = False
        set_perm_value = self.conf_main.get_value("DataTransfer/exec_permis")
        if set_perm_value:
            try:
                exec_permission = eval(set_perm_value.strip())
                set_permissions = True
            except Exception as ex:
                _str = 'Unexpected error Error "{}" occurred during evaluating of "DataTransfer/exec_permis" value ' \
                       '"{}" retrieved from the main config file. Permission setup operation will be skipped. \n{} '\
                    .format(ex, set_perm_value, traceback.format_exc())
                self.logger.warning(_str)
                # self.error.add_error(_str)
                set_permissions = False

        with open(sf_path, "w") as sf:
            sf.write(scr_tmpl)

        if set_permissions:
            try:
                # if permissions to be set were retrieved from config file, set them here
                st = os.stat(sf_path)
                os.chmod(sf_path, st.st_mode | exec_permission) #stat.S_IXUSR
            except Exception as ex:
                _str = 'Unexpected error Error "{}" occurred during setting up permissions "{}" for the script file ' \
                       '"{}". \n{} '\
                    .format(ex, set_perm_value, sf_path, traceback.format_exc())
                self.logger.warning(_str)
                self.error.add_error(_str)
        else:
            _str = 'Permission setup was skipped for the transfer script file. ' \
                   'Note: value of "DataTransfer/exec_permis" from main config was set to "{}".'\
                                    .format(set_perm_value)
            self.logger.warning(_str)

        self.logger.info("Finish preparing '{}' file.".format(sf_path))

    def disqualify_sub_aliquot(self, sa, details):
        # adds a sub aliquots to the disctionary of disqualified sub_aliquots
        # key = sub-aliquot, value = array of details for disqualification; 1 entry can have multiple detail reasons
        if sa in self.disqualified_sub_aliquots.keys():
            self.disqualified_sub_aliquots[sa].append(details)
        else:
            arr_details = [details]
            self.disqualified_sub_aliquots[sa]= arr_details
        self.logger.warning('Sub-aliquot "{}" was disqualified with the following details: "{}"'.format(sa, details))

    def populate_qualified_aliquots(self):
        # reset self.qualified_aliquots array
        self.qualified_aliquots = []
        #select only aliquots that were not disqualified
        for sa, a in zip(self.sub_aliquots, self.aliquots):
            if not sa in self.disqualified_sub_aliquots.keys():
                self.qualified_aliquots.append(a)

    def create_request_for_disqualified_sub_aliquots(self):

        # proceed only if some disqualified sub-aliquots are present
        if self.disqualified_sub_aliquots:

            self.logger.info("Start preparing a request file for disqualified sub-aliquots '{}'."
                             .format([val for val in self.disqualified_sub_aliquots.keys()]))

            wb = xlwt.Workbook()  # create empty workbook object
            sh = wb.add_sheet('Submission_Request')  # sheet name can not be longer than 32 characters

            cur_row = 0 # first row for 0-based array
            cur_col = 0 # first col for 0-based array
            #write headers to the file
            headers = self.get_headers()
            for val in headers:
                sh.write (cur_row, cur_col, val)
                cur_col += 1

            cur_row += 1

            for sa, s in zip (self.sub_aliquots, self.samples):
                if sa in self.disqualified_sub_aliquots.keys():
                    sh.write(cur_row, 0, self.exposure)
                    sh.write(cur_row, 1, self.center)
                    sh.write(cur_row, 2, self.source_spec_type)
                    sh.write(cur_row, 3, self.assay)
                    sh.write(cur_row, 4, sa)
                    sh.write(cur_row, 5, s)
                    cur_row += 1

            self.disqualified_request_path = Path(gc.DISQUALIFIED_REQUESTS + '/' +
                            time.strftime("%Y%m%d_%H%M%S", time.localtime()) + '_reprocess_disqualified _' +
                            Path(self.filename).stem + '.xls')

            # if DISQUALIFIED_REQUESTS folder does not exist, it will be created
            os.makedirs(gc.DISQUALIFIED_REQUESTS, exist_ok=True)

            wb.save(str(self.disqualified_request_path))

            self.logger.info("Successfully prepared the request file for disqualified sub-aliquots and saved in '{}'."
                             .format(str(self.disqualified_request_path)))