
class AttachmentAliquot:

    def __init__(self, sub_aliquot, request_obl):
        self.sub_aliquot = sub_aliquot
        self.req_obj = request_obl
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = self.req_obj.conf_assay
        self.attachment_path = ''
        self.loaded = False  # default value
        self.attachments = {}  # dictionary to hold final rawdata summary data
