from utils import global_const as gc
from file_load import File
from utils import ConfigData

class RawData_Text(File):

    def __init__(self, filepath, req_error, req_logger, file_type=1):

        # req_error parameter is a pointer to the current request error object

        File.__init__(self, filepath, file_type)
        self.error = req_error
        self.logger = req_logger
        self.sheet_name = ''
        # self.config =

        self.get_file_content()