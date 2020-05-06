from forms import SubmissionForm
import traceback


class SubmissionForms:
    def __init__(self, request):
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        # self.conf_assay = request.conf_assay
        self.conf_main = request.conf_main

        self.forms_dict = {}

        self.prepare_submission_forms()

    def prepare_submission_forms(self):
        if self.req_obj.type == 'sequence':
            forms = self.conf_main.get_value('submission_forms/sequence')
        elif self.req_obj.type == 'metadata':
            forms = self.conf_main.get_value('submission_forms/metadata')
        self.logger.info('Start processing the following submission forms for the current request: {}'.format(forms))
        for form in forms:
            self.logger.info('Processing submission form "{}".'.format(form))
            try:
                # submission_form = None  # reset the submission form reference
                if form['assignment'] == 'aliquot':
                    # prepare an instance of the current form for each aliquot
                    if self.req_obj.type == 'sequence':
                        # proceed here for sequence type submissions
                        for sa, a, smpl in zip(self.req_obj.sub_aliquots, self.req_obj.aliquots, self.req_obj.samples):
                            if not sa in self.req_obj.disqualified_sub_aliquots.keys():
                                self.logger.info('Prepare submission form "{}" for sub_aliquot "{}".'
                                                 .format(form['name'], sa))
                                submission_form = SubmissionForm(form['name'], self.req_obj, sa, a, smpl)
                                self.add_submission_form(sa, form['assignment'], submission_form)  # .json_form.json_data
                    elif self.req_obj.type == 'metadata':
                        # proceed here for metadata type submissions
                        for sa, a, smpl in zip(self.req_obj.sub_aliquots, self.req_obj.aliquots, self.req_obj.samples):
                            # if not sa in self.req_obj.disqualified_sub_aliquots.keys(): # TODO: verify that disqualification check is not needed
                            self.logger.info('Prepare submission form "{}" for aliquot "{}".'
                                             .format(form['name'], a))
                            submission_form = SubmissionForm(form['name'], self.req_obj, sa, a, smpl)
                            self.add_submission_form(sa, form['assignment'], submission_form)  # .json_form.json_data
                    else:
                        _str = 'Unexpected value of request type "{}" was received in the SubmissionForms class ' \
                               'during processing the submission form "{}" with the "{}" configuration assignment; ' \
                               'the form was not created. '\
                            .format(self.req_obj.type, form['name'], form['assignment'])
                        self.logger.error(_str)
                        self.error.add_error(_str)
                elif form['assignment'] == 'sample':
                    if self.req_obj.type == 'metadata':
                        # proceed here for metadata type submissions
                        db_samples = self.req_obj.metadata_db.metadata  # dataset of samples received from DB
                        for smpl in db_samples:
                            self.logger.info('Prepare submission form "{}" for sample "{}".'
                                             .format(form['name'], smpl))
                            submission_form = SubmissionForm(form['name'], self.req_obj, None, None, smpl)
                            self.add_submission_form(smpl, form['assignment'],
                                                     submission_form)  # .json_form.json_data
                    else:
                        _str = 'Unexpected value of request type "{}" was received in the SubmissionForms class ' \
                               'during processing the submission form "{}" with the "{}" configuration assignment; ' \
                               'the form was not created. ' \
                            .format(self.req_obj.type, form['name'], form['assignment'])
                        self.logger.error(_str)
                        self.error.add_error(_str)
                elif form['assignment'] == 'subject':
                    pass
                elif form['assignment'] == 'request':
                    #populate list of qualifed aliquots (removing all disqualified ones during attachment preps, etc.)
                    self.req_obj.populate_qualified_aliquots()

                    self.logger.info('Prepare submission form "{}" of the request level.'.format(form['name']))
                    submission_form = SubmissionForm(form['name'], self.req_obj, None, None, None)
                    self.add_submission_form(form['assignment'], form['assignment'], submission_form)
                else:
                    _str = 'Submission form "{}" had an unexpected configuration "assignment" key "{}" ' \
                           'and was not created.'.format(form['name'], form['assignment'])
                    self.logger.error(_str)
                    self.error.add_error(_str)
            except Exception as ex:
                _str = 'Unexpected error "{}" occurred during processing submission form "{}". \n{} ' \
                    .format(ex, form, traceback.format_exc())
                self.logger.error(_str)
                self.error.add_error(_str)

    def add_submission_form(self, assingment_id, assignment_name, submission_form):
        if assingment_id not in self.forms_dict:
            self.forms_dict[assingment_id] = []
        # attach_details = submission_form
        self.forms_dict[assingment_id].append(submission_form)

        if self.error.exist():
            _str = 'The following errors were reported during preparing a submission form "{}" for current {} ' \
                   '(referred as "{}"):\n{}' \
                .format(submission_form.form_name, assignment_name, assingment_id, self.error.get_errors_to_str())
            self.logger.warning(_str)
        else:
            _str = 'Current {} (referred as "{}") was successfully assigned with a submission form "{}".' \
                .format(assignment_name, assingment_id, submission_form.form_name)
            self.logger.info(_str)
