import os
from pathlib import Path
import time
import json
from utils import global_const as gc
from forms import SubmissionForms


class SubmissionPackage:
    def __init__(self, request):
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay
        self.attachments = request.attachments
        self.submission_forms = None
        self.submission_dir = gc.OUTPUT_PACKAGES_DIR + "/" + time.strftime("%Y%m%d_%H%M%S", time.localtime()) \
                              + "_" + self.req_obj.experiment_id

        self.prepare_submission_package()

    def prepare_submission_package(self):
        # create a package dir for this submission
        os.makedirs(self.submission_dir, exist_ok=True)

        self.prepare_submission_package_attachments()

        self.submission_forms = SubmissionForms(self.req_obj)
        self.req_obj.submission_forms = self.submission_forms
        self.prepare_submission_package_jsons()

    # this function will create all required json files
    # depends on a form group key assigned to a form,
    # one json file per request or one json file per aliquot entry will be created
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

    # this function will loop through all attachments,
    # create tarball files for each aliquot (grouping all attachments)
    # save name of the tarbal and its MD5sum to the attachment's object property_val
    def prepare_submission_package_attachments(self):
        if self.req_obj.attachments:
            attachments = self.req_obj.attachments.aliquots_data_dict
            for attch in attachments:
                tar_path = self.submission_dir + "/" + attch + ".tar.gz"
                self.req_obj.attachments.add_tarball(attch, tar_path)
