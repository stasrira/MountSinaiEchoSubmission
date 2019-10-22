from submission_forms import SubmissionForm

class SubmissionForms():
    def __init__(self, request):
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay

        self.forms_dict = {}

        self.prepare_submission_forms()

        print ()

    def prepare_submission_forms(self):
        for sa in self.req_obj.sub_aliquots:
            forms = self.conf_assay['submission_forms']
            for form in forms:
                submission_form = SubmissionForm(form, self.req_obj, sa)
                # self.forms.append({sa, submission_form.json_form.json_data})
                self.add_submission_form(sa, submission_form)
        print()

    def add_submission_form(self, sa, submission_form):
        if not sa in self.forms_dict:
            self.forms_dict[sa] = []
        attach_details = submission_form.json_form.json_data
        self.forms_dict[sa].append(attach_details)

        _str = 'Aliquot "{}" was successfully assigned with a submission form "{}".'.format(sa, submission_form.forma_name)
        self.logger.info(_str)