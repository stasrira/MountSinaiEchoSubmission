from data_retrieval import DataRetrieval
from pathlib import Path
import os
import tarfile
import hashlib


class Attachment(DataRetrieval):

    def __init__(self, request):
        self.tar_folder = ''
        self.aliquots_tarball_dict = {}
        self.data_loc = None
        self.cnf_data_source = None
        DataRetrieval.__init__(self, request)

    def init_specific_settings(self):
        self.cnf_data_source = self.conf_assay['attachment']
        cnf_data_source = self.cnf_data_source
        last_part_path_list = cnf_data_source['attachment_folder']
        data_source_loc = cnf_data_source['location']
        for last_part_path_item in last_part_path_list:
            # check if key received from config file is a dictionary
            if isinstance(last_part_path_item, dict):
                # if it is a dictionary, get values from it to a local variables
                last_part_path = last_part_path_item['folder']
                self.tar_folder = last_part_path_item['tar_dir']
            else:
                last_part_path = last_part_path_item
                self.tar_folder = ''

            self.data_loc = Path(self.convert_aliquot_properties_to_path(data_source_loc, last_part_path))
            # print (self.data_loc)
            search_by = self.cnf_data_source['attachment_search_by']
            search_deep_level = self.cnf_data_source['search_deep_level_max']
            exclude_dirs = self.cnf_data_source['exclude_folders']
            ext_match = self.cnf_data_source['attachment_file_ext']

            if search_by == 'folder_name':
                self.get_data_by_folder_name(search_deep_level, exclude_dirs)
            elif search_by == 'file_name':
                self.get_data_by_file_name(search_deep_level, exclude_dirs, ext_match)

            # check if any attachments were assigned to an aliquot and warn if none were assigned
            for sa in self.req_obj.sub_aliquots:
                # print ('Aliquot = {}'.format(sa))
                if sa not in self.aliquots_data_dict:
                    # no attachments were assigned to an aliquot
                    _str = 'Aliquot "{}" was not assigned with any attachments.'.format(sa)
                    self.logger.error(_str)
                    self.error.add_error(_str)

    def get_data_for_aliquot(self, sa, attach_dir):
        # this will record path of the found directory as one of the attachments for the request
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
        md5 = self.get_file_md5(tarball_path)
        tar_details = {'path': tarball_path, 'md5': md5}
        self.aliquots_tarball_dict[sa] = tar_details

        _str = 'Aliquot "{}" was successfully assigned with an tarball file "{}; MD5sum = {}".' \
            .format(sa, tarball_path, md5)
        self.logger.info(_str)

    @staticmethod
    def get_file_md5(file_path):
        with open(file_path, 'rb') as file:
            # read contents of the file
            data = file.read()
            # pipe contents of the file through
            return hashlib.md5(data).hexdigest()

    def get_data_by_file_name(self, search_deep_level, exclude_dirs, ext_match):
        # it retrieves all files potentially qualifying to be an attachment and searches through each to match
        # the sub-aliquot name in the name of the file
        files = self.get_file_system_items(self.data_loc, search_deep_level, exclude_dirs, 'file', ext_match)
        for fl in files:
            fn = os.path.basename(fl)
            # print('File name = {}'.format(fn))
            for sa in self.req_obj.sub_aliquots:
                # print ('Aliquot = {}'.format(sa))
                if sa in fn:
                    self.add_attachment(sa, fl)
                    break
