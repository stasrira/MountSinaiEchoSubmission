from submission_forms import SubmissionForm
import traceback

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
        forms = self.conf_assay['submission_forms']
        for form in forms:
            try:
                submission_form = None  # reset the submission form reference
                if form['assignment'] == 'aliquot': # TODO store strings "aliquot" and "assignments" in global const module
                    # prepare an instance of the current form for each aliquot
                    for sa in self.req_obj.sub_aliquots:
                        submission_form = SubmissionForm(form['name'], self.req_obj, sa) # TODO: store "name" in global const
                        self.add_submission_form(sa, form['assignment'], submission_form) # .json_form.json_data
                elif form['assignment'] == 'request':  # TODO: store "request" in global const
                    submission_form = SubmissionForm(form['name'], self.req_obj, None)  # TODO: store "name" and "assignments" in global const
                    self.add_submission_form(form['assignment'], form['assignment'], submission_form)  # .json_form.json_data
                else:
                    _str = 'Submission form "{}" had an unexpected configuration "assignment" value "{}" ' \
                           'and was not created.'.format(form['name'], form['assignment'])
                    self.logger.error(_str)
                    self.error.add_error(_str)
            except Exception as ex:
                _str = 'Unexpected error "{}" occurred during processing submission form "{}". \n{} ' \
                    .format(ex, form, traceback.format_exc())
                self.logger.error(_str)
                self.error.add_error(_str)

        print()

    def add_submission_form(self, assingment_id, assignment_name, submission_form):
        if not assingment_id in self.forms_dict:
            self.forms_dict[assingment_id] = []
        # attach_details = submission_form
        self.forms_dict[assingment_id].append(submission_form)

        if self.error.exist:
            _str = 'The following errors were reported during preparing a submission form "{}" for current {} (referred as "{}"):\n{}'\
                .format(submission_form.form_name, assignment_name, assingment_id, self.error.get_errors_to_str())
            self.logger.warning(_str)
        else:
            _str = 'Current {} (referred as "{}") was successfully assigned with a submission form "{}".'\
                .format(assignment_name, assingment_id, submission_form.form_name)
            self.logger.info(_str)