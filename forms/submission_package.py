import traceback
import os
# from os import walk
from pathlib import Path
import time
import json
import tarfile
from utils import global_const as gc

class SubmissionPackage():
    def __init__(self, request):
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay
        self.attachments = request.attachments
        self.submission_forms = request.submission_forms
        self.submission_dir = gc.SUBMISSION_PACKAGES_DIR + "/" \
                              + time.strftime("%Y%m%d_%H%M%S", time.localtime()) \
                              + "_" + self.req_obj.experiment_id

        self.prepare_submission_package()

        print ()

    def prepare_submission_package(self):
        # create a package dir for this submission
        os.makedirs(self.submission_dir, exist_ok=True)
        """
        # clean package dir
        (_, dirs, files) = next(walk(self.submission_dir))
        for file in files:
            os.remove(file)
        for dir in dirs:
            os.remove(dir)
        """

        self.prepare_submission_package_jsons()
        self.prepare_submission_package_attachments()

    def prepare_submission_package_jsons(self):
        # save json files to package dir
        dict_forms = self.req_obj.submission_forms.forms_dict
        # print(dict_forms)
        for form_grp in dict_forms:
            for form in dict_forms[form_grp]:
                js_data = form.fl_json.json_data
                # print (js_data)
                if form_grp == 'request':
                    json_file_name = Path(self.submission_dir + "/" + form.form_name + ".json")
                else:
                    json_file_name = Path(self.submission_dir + "/" + form_grp + "_" + form.form_name + ".json")

                with open(json_file_name, 'w') as fp:
                    json.dump(js_data, fp)

    def prepare_submission_package_attachments(self):
        attachments = self.req_obj.attachments.aliquots_data_dict
        for attch in attachments:
            with tarfile.open(self.submission_dir + "/" + attch + ".tar.gz", "w:") as tar:
                for item in attachments[attch]:
                    if len(item['tar_dir'].strip()) > 0:
                        _str = '{}/{}'.format(item['tar_dir'], os.path.basename(item['path']))
                    else:
                        _str = '{}'.format(os.path.basename(item['path']))
                    tar.add(str(Path(item['path'])), arcname=_str)
                tar.close()
