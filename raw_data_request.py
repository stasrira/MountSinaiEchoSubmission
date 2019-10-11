from pathlib import Path
import os
import glob
from raw_data_aliquot import RawDataAliquot
from file_load.rawdata_excel import RawData_Excel
# TODO: figure out why import statement does not read __init__.py file and require full path to the module


class RawDataRequest():

    def __init__(self, request):
        self.aliquots_rawdata_dict = {}
        # self.path_sub_aliqs = {}
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay
        self.rawdata_loc = Path(self.convert_aliquot_properties_to_path())
        # print (self.rawdata_loc)
        search_by = self.conf_assay['search_rawdata_summary']['search_by']
        if search_by == 'folder_name':
            self.get_rawdata_summary_by_folder_name()
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
        file_index = self.index_rawdata_files(files)
        for sa  in file_index:
            if sa in self.req_obj.sub_aliquots:
                rda = RawDataAliquot(sa, self)
                rda.get_rawdata_by_rownum(file_index[sa][1], file_index[sa][0])
                if rda.loaded:
                    _str = 'Summary Raw Data for aliquot "{}" was successfully loaded from file "{}".'.format(sa, file_index[sa][1])
                    self.aliquots_rawdata_dict[sa] = rda
                    # self.path_sub_aliqs[dbn] = sa
                    self.logger.info(_str)
                else:
                    _str = 'Summary Raw Data for aliquot "{}" failed to load from file "{}"; ' \
                           'see earlier error(s) in this log.'.format(sa, file_index[sa][1])
                    self.logger.warning(_str)
        print('')

    def index_rawdata_files(self, files):
        # combine content of selected files and create dictionary pr_key/file path
        worksheet = self.conf_assay['rawdata_summary']['sheet_name']
        header_row_num = self.conf_assay['rawdata_summary']['header_row_number'] # 1
        header_row_num = header_row_num - 1  # accommodate for 0-based numbering
        col_num = self.conf_assay['rawdata_summary']['pk_column_number']  # 6
        col_num = col_num - 1  # accommodate for 0-based numbering
        # col_num = 6 #TODO: remove hardcodded value with a proper implementation
        exlude_header = True

        index_dict = {}
        for file in files:
            f = RawData_Excel(file, self.error, self.logger, worksheet)
            col_vals = f.get_column_values(col_num, header_row_num, exlude_header)
            if col_vals:
                # if list of values returned, loop to create a dictionary with key = aliquot_id and
                # value a tuple containing row_number (using 0-base array) adjusted to accommodate excluded header
                # and path to the file containing it
                for i in range(len(col_vals)):
                    if len(str(col_vals[i]).strip()) > 0:
                        if exlude_header:
                            rn = i + 1
                        else:
                            rn = 1
                        index_dict[col_vals[i]] = (rn+1, file)  # row number (rn) is increased by
                                                                # 1 to convert to 1-base numbering
                # print(index_dict)
            f = None
        return index_dict


    def get_rawdata_summary_by_folder_name(self):
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
                    rda = RawDataAliquot(sa, self.req_obj)
                    rda.get_rawdata_predefined_file_text(d)
                    if rda.loaded:
                        _str = 'Summary Raw Data for aliquot "{}" was successfully loaded from sub-aliquot ' \
                               'raw data location "{}".'\
                            .format(sa, d)
                        self.aliquots_rawdata_dict[sa] = rda
                        # self.path_sub_aliqs[dbn] = sa
                        self.logger.info(_str)
                    else:
                        _str = 'Summary Raw Data for aliquot "{}" failed to load from sub-aliquot ' \
                               'raw data location "{}"; see earlier error(s) in this log.'\
                            .format(sa, d)
                        self.logger.warning(_str)

        # print(self.aliquots_rawdata_dict)
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