from file_load import File
import json

class File_Json(File):

    def __init__(self, filepath, req_error, req_logger, file_type=1):

        # req_error parameter is a pointer to the current request error object

        File.__init__(self, filepath, file_type)
        self.error = req_error
        self.logger = req_logger
        self.load_file()

    def load_file(self, filepath = ''):
        if len(str(filepath).strip()) == 0:
            filepath = self.filepath

        if self.file_exists(filepath):
            with open(filepath) as json_file:
                self.json_data = json.load(json_file)

