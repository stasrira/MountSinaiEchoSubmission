from pathlib import Path
import os
import glob
from data_retrieval import DataRetrievalAliquot
from file_load import DataRetrievalExcel, DataRetrievalText
from utils import common as cm


class DataRetrieval:

    def __init__(self, request):
        self.aliquots_data_dict = {}
        # self.path_sub_aliqs = {}
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger
        self.conf_assay = request.conf_assay
        self.data_loc = None
        self.init_specific_settings()
        # print ('')

    def init_specific_settings(self):
        # should be overwritten in classed that inherit this one
        pass
        '''# this is an old  version of code
        last_part_path = self.conf_assay['data_folder']
        self.data_loc = Path(self.convert_aliquot_properties_to_path(last_part_path))
        # print (self.data_loc)
        search_by = self.conf_assay['search_rawdata_summary']['search_by']
        if search_by == 'folder_name':
            search_deep_level = self.conf_assay['search_rawdata_summary']['search_deep_level_max']
            exclude_dirs = self.conf_assay['search_rawdata_summary']['exclude_folders']
            self.get_data_by_folder_name(search_deep_level, exclude_dirs)
        elif search_by == 'file_content':
            self.get_data_by_file_content()

        # check if some data_retrieval was assigned to an aliquot and warn if none were assigned
        for aliquot in self.req_obj.sub_aliquots:
            if aliquot not in self.aliquots_data_dict:
                # no attachments were assigned to an aliquot
                _str = 'Aliquot "{}" was not assigned with any Raw Data.'.format(aliquot)
                self.logger.error(_str)
                self.error.add_error(_str)
        '''

    def convert_aliquot_properties_to_path(self, data_location, last_part_path):
        return '/'.join([data_location,
                         # project name is removed since it will be part of data_location variable
                         #  self.req_obj.project,
                         self.req_obj.exposure,
                         self.req_obj.center,
                         self.req_obj.source_spec_type,
                         last_part_path])  # self.conf_assay['data_folder']])

    """
    # get_data_by_file_content function expects the following parameters:
    search_deep_level, 
    exclude_dirs, 
    file_ext_match  
    file_struct = {'worksheet': ,
                    'header_row_num': ,
                    'col_num': ,
                    'exlude_header':
                    }
    """

    def get_data_by_file_content(self, search_deep_level, exclude_dirs, file_ext_match, file_struct):
        # retrieves raw data summary info for each sub-aliquot (from the request file) based on
        # presence of aliquot id in the particular column of predefined files

        files = self.get_file_system_items(self.data_loc, search_deep_level, exclude_dirs, 'file', file_ext_match)

        file_index = self.index_data_files(files, file_struct)
        for id_val in file_index:
            sa_list = []
            sa_list  = [(sa, al) for sa, al in zip(self.req_obj.sub_aliquots, self.req_obj.aliquots)
                        if sa in id_val or al in id_val]

            #if id_val in self.req_obj.sub_aliquots:
            if sa_list:
                rda = DataRetrievalAliquot(id_val, self)
                rda.get_data_by_rownum(file_index[id_val][1], file_index[id_val][0], file_struct['header_row_num'])
                if rda.loaded:
                    _str = '{} for aliquot "{}" (matching file id value is "{}") was successfully loaded from file "{}".' \
                        .format(self.data_source_name, sa_list[0][0], id_val, file_index[id_val][1])
                    self.aliquots_data_dict[sa_list[0][0]] = rda.data_retrieved
                    self.logger.info(_str)
                else:
                    _str = '{} for aliquot "{}" failed to load from file "{}"; ' \
                           'see earlier error(s) in this log.'.format(self.data_source_name, sa_list[0], file_index[id_val][1])
                    self.logger.warning(_str)

    def index_data_files(self, files, file_struct):
        # combine content of selected files and create dictionary pr_key/file path
        worksheet = file_struct['worksheet']  # self.conf_assay['data_retrieved']['sheet_name']
        header_row_num = file_struct['header_row_num']  # self.conf_assay['data_retrieved']['header_row_number'] # 1
        if str(header_row_num).isnumeric():
            header_row_num = header_row_num - 1  # accommodate for 0-based numbering
        else:
            header_row_num = None
        col_num = file_struct['col_num']  # column number that will be checked for sub-aliquots
        if str(col_num).isnumeric():
            col_num = col_num - 1  # accommodate for 0-based numbering
        else:
            col_num = None
        exlude_header = file_struct['exlude_header']  # True

        index_dict = {}
        for file in files:
            # read files differently depending if that is excel or text file
            if cm.is_excel(file):  # 'xls' in ext:
                f = DataRetrievalExcel(file, self.error, self.logger, worksheet)
            else:
                f = DataRetrievalText(file, self.error, self.logger)
            col_vals = f.get_column_values(col_num, header_row_num, exlude_header)
            if col_vals:
                # if list of values returned, loop to create a dictionary with key = aliquot_id and
                # key a tuple containing row_number (using 0-base array) adjusted to accommodate excluded header
                # and path to the file containing it
                for i in range(len(col_vals)):
                    if len(str(col_vals[i]).strip()) > 0:
                        if exlude_header:
                            rn = i + 1  # header_row_num +
                        else:
                            rn = i  # header_row_num +
                        # row number (rn) is increased by 1 to convert to 1-base numbering
                        index_dict[col_vals[i]] = (rn + 1, file)
        return index_dict

    def get_data_by_folder_name(self, search_deep_level, exclude_dirs, data_loc=None):
        # retrieves data for each sub-aliquot listed in the request file based on presence
        # of aliquot id key in the name of the folder
        if not data_loc:
            data_loc = self.data_loc
        dirs = self.find_locations_by_folder(data_loc, search_deep_level, exclude_dirs)
        # check if any of the found folders contain sub_aliquot ids and assign such folders to sub_aliqout ids
        for d in dirs:
            dbn = os.path.basename(d)
            # print('dbn = |{}|'.format(dbn))
            for sa, al in zip(self.req_obj.sub_aliquots, self.req_obj.aliquots):
                # print ('Aliquot = |{}|'.format(sa))
                if sa in dbn or al in dbn:
                    self.get_data_for_aliquot(sa, d)

    def get_data_for_aliquot(self, sa, directory):
        # this retrieves data related to the purpose of the current class - raw data or attachment info.
        # should be overwritten in classes that inherit this one
        pass
        '''
        rda = DataRetrievalAliquot(sa, self.req_obj)
        rda.get_processed_data_predefined_file_text(directory)
        if rda.loaded:
            _str = 'Summary Raw Data for aliquot "{}" was successfully loaded from sub-aliquot ' \
                   'raw data location "{}".' \
                .format(sa, directory)
            self.aliquots_data_dict[sa] = rda.data_retrieved
            self.logger.info(_str)
        else:
            _str = 'Summary Raw Data for aliquot "{}" failed to load from sub-aliquot ' \
                   'raw data location "{}"; see earlier error(s) in this log.' \
                .format(sa, directory)
            self.logger.warning(_str)
        '''

    def find_locations_by_folder(self, loc_path, search_deep_level, exclude_dirs):
        # get directories of the top level and filter out any directories to be excluded
        dirs_top = self.get_top_level_dirs(loc_path, exclude_dirs)
        dirs = []  # holds final list of directories
        dirs.extend(dirs_top)

        # if deeper than top level search is required, proceed here
        if search_deep_level > 0:
            for d in dirs_top:
                dirs.extend(self.get_file_system_items(d, search_deep_level, exclude_dirs, 'dir'))

        return dirs

    def get_top_level_dirs(self, path, exclude_dirs=None):
        if exclude_dirs is None:
            exclude_dirs = []
        if Path(path).exists():
            itr = os.walk(Path(path))
            _, dirs, _ = next(itr)
            if not dirs:
                dirs = []
            dirs = list(set(dirs) - set(exclude_dirs))  # remove folders to be excluded from the list of directories
            dirs_path = [str(Path(path / fn)) for fn in dirs]
        else:
            self.logger.warning('Expected to exist directory "{}" is not present - reported from "DataRetrieval" '
                                'class, "get_top_level_dirs" function'.format (path))
            dirs_path = []
        return dirs_path

    @staticmethod
    def get_file_system_items(dir_cur, search_deep_level, exclude_dirs=None, item_type='dir', ext_match=None):
        # base_loc = self.data_loc / dir_cur
        if ext_match is None:
            ext_match = []
        if exclude_dirs is None:
            exclude_dirs = []
        deep_cnt = 0
        cur_lev = ''
        items = []
        while deep_cnt < search_deep_level:
            cur_lev = cur_lev + '/*'
            items_cur = glob.glob(str(Path(str(dir_cur) + cur_lev)))

            if item_type == 'dir':
                items_clean = [fn for fn in items_cur if
                               Path.is_dir(Path(fn)) and not os.path.basename(fn) in exclude_dirs]
            elif item_type == 'file':
                items_clean = [fn for fn in items_cur if not Path.is_dir(Path(fn))
                               and (len(ext_match) == 0 or os.path.splitext(fn)[1] in ext_match)]
            else:
                items_clean = None
            items.extend(items_clean)
            deep_cnt += 1
        return items
