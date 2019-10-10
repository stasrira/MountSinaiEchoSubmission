import os
from pathlib import Path
import glob

def get_file_system_items(dir_cur, search_deep_level, exclude_dirs=[], item_type='dir', ext_match = []):
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
            items_clean = [fn for fn in items_cur if not Path.is_dir(Path(fn)) and (len(ext_match) == 0 or os.path.splitext(fn)[1] in ext_match)]

        items.extend(items_clean)
        deep_cnt += 1
    return items

path = 'E:\MounSinai\Darpa\Programming\submission\data_examples\Bulk_Drive\ECHO\HIV\HI\PBMC\cytoff'
path2 = 'E:\MounSinai\Darpa\Programming\submission\data_examples\Bulk_Drive\ECHO\HIV\HI\PBMC\scatac-seq'
exclude_dirs = []
ext_match = ['.xlsx', '.xls']

files = get_file_system_items(path, 2, [], 'file', ext_match)
print (files)

dirs =  get_file_system_items(path2, 2, ['fastqs', 'FASTQs'], 'dir')
print (dirs)