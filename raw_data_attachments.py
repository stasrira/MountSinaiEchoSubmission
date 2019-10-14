from raw_data_request import RawDataRequest
from pathlib import Path
import os

class RawDataAttachment(RawDataRequest):

    def __init__(self, request):
        # self.rawdata_attachments = {}
        RawDataRequest.__init__(self, request)

    def init_specific_settings(self):
        last_part_path = self.conf_assay['attachement_folder']
        self.data_loc = Path(self.convert_aliquot_properties_to_path(last_part_path))
        # print (self.data_loc)
        search_by = self.conf_assay['search_attachment']['search_by']
        if search_by == 'folder_name':
            search_deep_level = self.conf_assay['search_attachment']['search_deep_level_max']
            exclude_dirs = self.conf_assay['search_attachment']['exclude_folders']
            self.get_data_by_folder_name(search_deep_level, exclude_dirs)
        elif search_by == 'file_name':
            self.get_data_by_file_name()

    def get_data_for_aliquot(self, sa, attach_dir):
        # this will record path of the found directory as one of the rawdata_attachments for the request
        self.add_attachment(sa, attach_dir)

    def add_attachment(self, sa, attach_path):
        if not sa in self.aliquots_data_dict:
            self.aliquots_data_dict[sa] = []
        self.aliquots_data_dict[sa].append(attach_path)

    def get_data_by_file_name(self):
        # it retrieves all files potentially qualifying to be an attachment and searches through each to match
        # the sub-aliquot name in the name of the file
        search_deep_level = self.conf_assay['search_attachment']['search_deep_level_max']
        exclude_dirs = self.conf_assay['search_attachment']['exclude_folders']
        ext_match = self.conf_assay['attachment_file_ext']
        files = self.get_file_system_items(self.data_loc, search_deep_level, exclude_dirs, 'file', ext_match)
        for fl in files:
            fn = os.path.basename(fl)
            # print('File name = {}'.format(fn))
            for sa in self.req_obj.sub_aliquots:
                # print ('Aliquot = {}'.format(sa))
                if sa in fn:
                    self.add_attachment(sa, fl)
