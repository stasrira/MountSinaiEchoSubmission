import os
from pathlib import Path
import time
import logging
from utils import global_const as gc
from utils.log_utils import setup_logger_common
from file_load.file_error import RequestError
from file_load.file_utils import StudyConfig
from utils import ConfigData

class Request:

    def __init__(self, sample_type, assay_type, samples, aliqouts, file_path):
        self.sample_type = sample_type
        self.assay_type = assay_type
        self.samples = []
        if samples:
            self.samples = samples
        self.aliquots = []
        if aliqouts:
            self.aliquots = aliqouts
        self.file_path = file_path
        self.wrkdir = os.path.dirname(os.path.abspath(file_path))
        self.filename = Path(os.path.abspath(file_path)).name
        self.project = ''
        self.exposure = ''
        self.center = ''
        self.tissue_type = ''
        self.error = RequestError(self)

        # setup logger
        self.logger = self.setup_logger(self.wrkdir, self.filename)

        self.logger.info('Request "{}" was loaded, processing starts. Request path: {}.'.format(self.filename, self.file_path))

        # validate provided information
        self.logger.info('Validating provided sample type value: "{}".'.format(self.sample_type))
        self.decode_sample_type(self.sample_type)
        self.logger.info('Validating provided Sample IDs ({}) vs. Aliquot IDs ({}).'.format(self.samples, self.aliquots))
        self.verify_samples_vs_aliquots()

        if self.error.exist():
            # report that errors exist
            self.loaded = False
            # print(self.error.count)
            # print(self.error.get_errors_to_str())
            _str = 'Errors ({}) were identified during validating of the request. \nError(s): {}'.format(self.error.count, self.error.get_errors_to_str())
        else:
            self.loaded = True
            _str = 'Request parameters were successfully validated - no errors found.'
        self.logger.info(_str)

    def decode_sample_type(self, sample_type):

        def_delim = gc.DEFAULT_REQUEST_SAMPLE_TYPE_SEPARATOR
        # make sure the correct delimiter was provided
        _sample_type = sample_type.replace('\\', def_delim)
        # _sample_type = sample_type.replace('-', def_delim)
        items = _sample_type.split("/")

        if len(items) > 3:
            self.project = items[0]
            self.exposure = items[1]
            self.center = items[2]
            self.tissue_type = items[3]
        else:
            _str = "Provided Sample Type '{}' did not have 4 components present".format(self.sample_type)
            self.error.add_error(_str)
            self.logger.error(_str)

    def verify_samples_vs_aliquots(self):
        s_cnt = len(self.samples)
        a_cnt = len(self.aliquots)
        if s_cnt != a_cnt:
            _str = 'Number of samples ({}) does not match number of aliquots ({}) provided in the Request file "{}".'\
                .format(s_cnt, a_cnt, self.file_path)
            self.error.add_error(_str)
            self.logger.error(_str)

    def setup_logger(self, wrkdir, filename):

        m_cfg = ConfigData(gc.MAIN_CONFIG_FILE)

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
