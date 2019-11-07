import traceback

class SubmissionForms():
    def __init__(self, request):
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay
        self.attachments = request.attachments
        self.submission_forms = request.submission_forms

        self.prepare_submission_package()

        print ()