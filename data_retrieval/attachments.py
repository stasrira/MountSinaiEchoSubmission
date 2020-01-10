from data_retrieval import DataRetrieval
from pathlib import Path
import os
import tarfile
import hashlib
import subprocess
import shlex
from utils import global_const as gc


class Attachment(DataRetrieval):

    def __init__(self, request):
        self.tar_folder = None
        self.tar_include_parent_dir = None
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
            # set default values
            self.tar_folder = None
            self.tar_include_parent_dir = None

            # check if key received from config file is a dictionary
            if isinstance(last_part_path_item, dict):
                # if it is a dictionary, get values from it to a local variables
                if 'folder' in last_part_path_item:
                    last_part_path = last_part_path_item['folder']
                if 'tar_dir' in last_part_path_item:
                    self.tar_folder = last_part_path_item['tar_dir']
                if 'tar_include_parent_dir' in last_part_path_item:
                    self.tar_include_parent_dir = last_part_path_item['tar_include_parent_dir']
            else:
                last_part_path = last_part_path_item

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
        attach_details = {'path': attach_path, 'tar_dir': self.tar_folder, 'incl_prnt_dir': self.tar_include_parent_dir}
        self.aliquots_data_dict[sa].append(attach_details)

        _str = 'Aliquot "{}" was successfully assigned with an attachment object "{}".'.format(sa, attach_details)
        self.logger.info(_str)

    def add_tarball(self, sa, tarball_path):
        # create a tarball based on the approach selected in the main config file
        if gc.TARBALL_APPROACH == 'tarfile':
            self.add_tarball_tarfile(sa, tarball_path)
        elif gc.TARBALL_APPROACH == 'commandline':
            self.add_tarball_commandline(sa, tarball_path)
        else:
            _str = 'No tarball file for aliquot "{}" was created. Provided tar ball approach parameter ' \
                   '(from main config) "{}" was not recognized.'.format(sa, gc.TARBALL_APPROACH)
            self.logger.error(_str)
            self.error.add_error(_str)
            return
        if not self.error.exist():
            # calculate an md5sum for the created tarball
            self.calculate_md5sum(sa, tarball_path)
            if gc.TARBALL_SAVE_MD5SUM_FILE:
                # save md5sum file next to the created tar file
                self.save_md5sum_file(tarball_path + ".md5", self.aliquots_tarball_dict[sa]["md5"])

    def add_tarball_commandline(self, sa, tarball_path):
        self.logger.info('Start preparing a tarball file for aliquot "{}"; command line approach is used.'.format(sa, tarball_path))
        cnt = 0
        for item in self.aliquots_data_dict[sa]:
            # add holder to the end of path
            if Path(item['path']).is_dir():
                item_dir_path = str(Path(item['path']).parent)  # str(Path(item['path']) / '..') # .parent
            else:
                item_dir_path = str(os.path.dirname(Path(item['path'])))
            # print(item_dir_path)
            item_to_tar = os.path.basename(item['path'])  # target file to tar

            incl_prnt_dir = item['incl_prnt_dir']  # TODO: this parameter should come from a config file
            if incl_prnt_dir:
                parent = os.path.basename(item_dir_path)
                item_dir_path = str(Path(item_dir_path).parent)
                item_to_tar = str(Path(parent + '/' + item_to_tar))

            in_tar_path = ''
            if item['tar_dir'] and len(item['tar_dir'].strip()) > 0:
                in_tar_path = item['tar_dir']
            self.logger.info('Start adding item "{}" to a tarball file "{}".'.format(item['path'], tarball_path))
            cmd_tmpl = "tar -C {} --transform=s,^,/{}/, {} {} {}"
            cmd_tmpl_1 = "tar -C {} {} {} {}"
            if cnt == 0:
                tar_cmd = '-cvf'
            else:
                tar_cmd = '-rvf'
            if in_tar_path != '':
                cmd = cmd_tmpl.format(Path(item_dir_path), Path(in_tar_path), tar_cmd, Path(tarball_path), item_to_tar)
            else:
                cmd = cmd_tmpl_1.format(Path(item_dir_path), tar_cmd, Path(tarball_path), item_to_tar)
             # print(cmd)
            self.logger.info('Command to append items to a tar file: "{}".'.format(cmd))
            arg_list = shlex.split (cmd, posix=False)
            # print (arg_list)
            process = subprocess.run(arg_list,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True)
            if process.returncode == 0:
                self.logger.info('Item "{}" was added to a tarball file "{}".'.format(item['path'], tarball_path))
                self.logger.info('Here is the stdout: \n"{}".'.format(process.stdout))
            else:
                _str = 'Error "{}" was reported while adding item "{}" to a tarball file "{}"'\
                    .format(process.stderr, item['path'], tarball_path)
                self.logger.error(_str)
                self.error.add_error(_str)
                return
            cnt = cnt + 1
        self.logger.info('Tarball file "{}" was successfully created for aliquot "{}".'.format(tarball_path, sa))

    def add_tarball_tarfile(self, sa, tarball_path):
        self.logger.info('Start preparing a tarball file for aliquot "{}"; tarfile library is used.'.format(sa, tarball_path))
        with tarfile.open(Path(tarball_path), "w:") as tar:
            for item in self.aliquots_data_dict[sa]:
                if item['tar_dir'] and len(item['tar_dir'].strip()) > 0:
                    _str = '{}/{}'.format(item['tar_dir'], os.path.basename(item['path']))
                else:
                    _str = '{}'.format(os.path.basename(item['path']))
                self.logger.info('Start adding item "{}" to a tarball file "{}".'.format(item['path'], tarball_path))
                tar.add(str(Path(item['path'])), arcname=_str)
                self.logger.info('Item "{}" was added to a tarball file "{}".'.format(item['path'], tarball_path))
            tar.close()
        self.logger.info('Tarball file "{}" was successfully created for aliquot "{}".'.format(tarball_path, sa))

    def calculate_md5sum(self, sa, tarball_path):
        self.logger.info('Start calculating MD5sum for tarball file "{}".'.format(tarball_path))
        md5 = self.get_file_md5(tarball_path)
        tar_details = {'path': tarball_path, 'md5': md5}
        self.aliquots_tarball_dict[sa] = tar_details

        _str = 'Aliquot "{}" was successfully assigned with a tarball file "{}"; MD5sum = "{}".' \
            .format(sa, tarball_path, md5)
        self.logger.info(_str)

    def save_md5sum_file(self, md5_path, md5_value):
        f = open(md5_path, "w+")
        f.write(md5_value)
        f.close()


    @staticmethod
    # solution used below is based on https://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
    def get_file_md5(file_path, block_size=256*128):
        with open(file_path, 'rb') as file:
            md5 = hashlib.md5()
            for chunk in iter(lambda: file.read(block_size), b''):
                md5.update(chunk)
            '''
            while True:
                data = file.read(block_size)
                if not data:
                    break
                md5.update(data)
            '''
            return md5.hexdigest()

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
