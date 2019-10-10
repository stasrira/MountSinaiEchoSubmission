from pathlib import Path
import os
import glob
from raw_data_aliquot import RawDataAliquot

class RawDataRequest():

    def __init__(self, request):
        self.sub_aliqs_rawdata_dict = {}
        # self.path_sub_aliqs = {}
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay
        self.rawdata_loc = Path(self.convert_aliquot_properties_to_path())
        # print (self.rawdata_loc)
        search_by = self.conf_assay['search_rawdata_summary']['search_by']
        if search_by == 'folder_name':
            self.get_rawdata_summary_by_folder()
        elif search_by == 'file_content':
            self.get_rawdata_summary_by_file_content()
        print ('')

    def convert_aliquot_properties_to_path(self):
        return '/'.join ([self.conf_assay['rawdata_location'],
                          self.req_obj.project,
                          self.req_obj.exposure,
                          self.req_obj.center,
                          self.req_obj.source_spec_type,
                          self.conf_assay['rawdata_folder']])

    def get_rawdata_summary_by_file_content(self):
        search_deep_level = self.conf_assay['search_rawdata_summary']['search_deep_level_max']
        exclude_dirs = self.conf_assay['search_rawdata_summary']['exclude_folders']
        ext_match = self.conf_assay['rawdata_summary_file_ext']
        files = self.get_file_system_items (self.rawdata_loc, search_deep_level, exclude_dirs, 'file', ext_match)
        print('')

    def get_rawdata_summary_by_folder(self):
        search_deep_level = self.conf_assay['search_rawdata_summary']['search_deep_level_max']
        exclude_dirs = self.conf_assay['search_rawdata_summary']['exclude_folders']

        dirs = self.find_locations_by_folder (self.rawdata_loc, search_deep_level, exclude_dirs)
        # check if any of the found folders contain sub_aliquot ids and assign such folders to sub_aliqout ids
        for d in dirs:
            dbn = os.path.basename(d)
            # print('File name = {}'.format(dbn))
            for sa in self.req_obj.sub_aliquots:
                # print ('Aliquot = {}'.format(sa))
                if sa in dbn:
                    rda = RawDataAliquot(sa, d, self.req_obj)
                    if rda.loaded:
                        _str = 'Summary Raw Data for aliquot "{}" was successfully loaded from sub-aliquot ' \
                               'raw data location "{}".'\
                            .format(sa, d)
                        self.sub_aliqs_rawdata_dict[sa] = rda
                        # self.path_sub_aliqs[dbn] = sa
                        self.logger.info(_str)
                    else:
                        _str = 'Summary Raw Data for aliquot "{}" failed to load from sub-aliquot ' \
                               'raw data location "{}"; see earlier error(s) in this log.'\
                            .format(sa, d)
                        self.logger.warning(_str)

        # print(self.sub_aliqs_rawdata_dict)
        # print(self.path_sub_aliqs)
        print('')

    def find_locations_by_folder(self, loc_path, search_deep_level, exclude_dirs):
        # get directories of the top level and filter out any directories to be excluded
        dirs_top = self.get_top_level_dirs(loc_path, exclude_dirs)
        dirs = []  # holds final list of directories
        dirs.extend(dirs_top)

        # if deeper than top level search is required, proceed here
        if search_deep_level > 0:
            for d in dirs_top:
                dirs.extend(self.get_file_system_items (d, search_deep_level, exclude_dirs, 'dir'))

        return dirs

    def get_top_level_dirs(self, path, exclude_dirs = []):
        itr = os.walk(path)
        _, dirs, _ = next(itr)
        dirs = list(set(dirs) - set(exclude_dirs))  # remove folders to be excluded from the list of directories
        dirs_path = [str(Path(path / fn)) for fn in dirs]
        return dirs_path

    #def get_sub_level_dirs(self, sub_dir, search_deep_level, exclude_dirs = []):
    #    return self.get_file_system_items (sub_dir, search_deep_level, exclude_dirs, 'dir')

    def get_file_system_items (self, dir_cur, search_deep_level, exclude_dirs = [], item_type ='dir', ext_match = []):
        # base_loc = self.rawdata_loc / dir_cur
        deep_cnt = 0
        cur_lev = ''
        items = []
        while deep_cnt < search_deep_level:
            temp_dir = []
            cur_lev = cur_lev + '/*'
            items_cur = glob.glob(str(Path(str(dir_cur) + cur_lev)))
            if item_type == 'dir':
                items_clean = [fn for fn in items_cur if
                             Path.is_dir(Path(fn)) and not os.path.basename(fn) in exclude_dirs]
            elif item_type == 'file':
                items_clean = [fn for fn in items_cur if not Path.is_dir(Path(fn))
                               and (len(ext_match) == 0 or os.path.splitext(fn)[1] in ext_match)]
            items.extend(items_clean)
            deep_cnt += 1
        return items