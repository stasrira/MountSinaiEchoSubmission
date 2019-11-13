from rawdata import RawDataRequest
from pathlib import Path
import os
import tarfile
import hashlib


class RawDataAttachment(RawDataRequest):

    def __init__(self, request):
        # self.rawdata_attachments = {}
        self.tar_folder = ''
        self.aliquots_tarball_dict = {}
        self.data_loc = None
        RawDataRequest.__init__(self, request)

    def init_specific_settings(self):
        last_part_path_list = self.conf_assay['attachement_folder']
        for last_part_path_item in last_part_path_list:
            # check if value received from config file is a dictionary
            if isinstance(last_part_path_item, dict):
                # if it is a dictionary, get values from it to a local variables
                last_part_path = last_part_path_item['folder']
                self.tar_folder = last_part_path_item['tar_dir']
            else:
                last_part_path = last_part_path_item
                self.tar_folder = ''

            self.data_loc = Path(self.convert_aliquot_properties_to_path(last_part_path))
            # print (self.data_loc)
            search_by = self.conf_assay['search_attachment']['search_by']
            if search_by == 'folder_name':
                search_deep_level = self.conf_assay['search_attachment']['search_deep_level_max']
                exclude_dirs = self.conf_assay['search_attachment']['exclude_folders']
                self.get_data_by_folder_name(search_deep_level, exclude_dirs)
            elif search_by == 'file_name':
                self.get_data_by_file_name()

            # check if any attachments were assigned to an aliquot and warn if none were assigned
            for sa in self.req_obj.sub_aliquots:
                # print ('Aliquot = {}'.format(sa))
                if sa not in self.aliquots_data_dict:
                    # no attachments were assigned to an aliquot
                    _str = 'Aliquot "{}" was not assigned with any attachments.'.format(sa)
                    self.logger.error(_str)
                    self.error.add_error(_str)

    def get_data_for_aliquot(self, sa, attach_dir):
        # this will record path of the found directory as one of the rawdata_attachments for the request
        self.add_attachment(sa, attach_dir)

    def add_attachment(self, sa, attach_path):
        if sa not in self.aliquots_data_dict:
            self.aliquots_data_dict[sa] = []
        attach_details = {'path': attach_path, 'tar_dir': self.tar_folder}
        self.aliquots_data_dict[sa].append(attach_details)

        _str = 'Aliquot "{}" was successfully assigned with an attachment object "{}".'.format(sa, attach_details)
        self.logger.info(_str)

    def add_tarball(self, sa, tarball_path):
        with tarfile.open(tarball_path, "w:") as tar:
            for item in self.aliquots_data_dict[sa]:
                if len(item['tar_dir'].strip()) > 0:
                    _str = '{}/{}'.format(item['tar_dir'], os.path.basename(item['path']))
                else:
                    _str = '{}'.format(os.path.basename(item['path']))
                tar.add(str(Path(item['path'])), arcname=_str)
            tar.close()
        md5 = self.get_file_MD5(tarball_path)
        tar_details = {'path': tarball_path, 'md5': md5}
        self.aliquots_tarball_dict[sa] = tar_details

        _str = 'Aliquot "{}" was successfully assigned with an tarball file "{}; MD5sum = {}".' \
            .format(sa, tarball_path, md5)
        self.logger.info(_str)

    @staticmethod
    def get_file_MD5(file_path):
        with open(file_path, 'rb') as file:
            # read contents of the file
            data = file.read()
            # pipe contents of the file through
            return hashlib.md5(data).hexdigest()

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
                    break
