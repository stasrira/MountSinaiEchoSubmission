import os
from pathlib import Path
import glob
import sys

def get_file_system_items(dir_cur, search_deep_level, exclude_dirs=[], item_type='dir', ext_match = []):
    # base_loc = self.data_loc / dir_cur
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

l = ['1', '2', '3', '4', '3']
print(l.index('3'))

a = [[1, 2, 3, 4], [5, 6], [7, 8, 9]]
print (len(a))

[(['AS06-11984_6'], ['E:\\MounSinai\\Darpa\\Programming\\submission\\data_examples\\Bulk_Drive\\ECHO\\HIV\\HI\\PBMC\\cytoff\\20190801_experiment_31600_files\\072519_Frederique_HIMC Sample Drop Off Form 190417-1.xlsx']),
 (['AS10-16739_6'], ['E:\\MounSinai\\Darpa\\Programming\\submission\\data_examples\\Bulk_Drive\\ECHO\\HIV\\HI\\PBMC\\cytoff\\20190801_experiment_31600_files\\072519_Frederique_HIMC Sample Drop Off Form 190417-1.xlsx']),
 (['AS09-09992_6'], ['E:\\MounSinai\\Darpa\\Programming\\submission\\data_examples\\Bulk_Drive\\ECHO\\HIV\\HI\\PBMC\\cytoff\\20190801_experiment_31600_files\\072519_Frederique_HIMC Sample Drop Off Form 190417-1.xlsx']), (['AS08-13555_6'], ['E:\\MounSinai\\Darpa\\Programming\\submission\\data_examples\\Bulk_Drive\\ECHO\\HIV\\HI\\PBMC\\cytoff\\20190801_experiment_31600_files\\072519_Frederique_HIMC Sample Drop Off Form 190417-1.xlsx']), (['AS11-18755_6'], ['E:\\MounSinai\\Darpa\\Programming\\submission\\data_examples\\Bulk_Drive\\ECHO\\HIV\\HI\\PBMC\\cytoff\\20190801_experiment_31600_files\\072519_Frederique_HIMC Sample Drop Off Form 190417-1.xlsx']), (['AS17-00144_6'], ['E:\\MounSinai\\Darpa\\Programming\\submission\\data_examples\\Bulk_Drive\\ECHO\\HIV\\HI\\PBMC\\cytoff\\20190801_experiment_31600_files\\072519_Frederique_HIMC Sample Drop Off Form 190417-1.xlsx']), (['AS09-13278_6'], ['E:\\MounSinai\\Darpa\\Programming\\submission\\data_examples\\Bulk_Drive\\ECHO\\HIV\\HI\\PBMC\\cytoff\\20190801_experiment_31600_files\\072519_Frederique_HIMC Sample Drop Off Form 190417-1.xlsx']), (['AS14-03700_6'], ['E:\\MounSinai\\Darpa\\Programming\\submission\\data_examples\\Bulk_Drive\\ECHO\\HIV\\HI\\PBMC\\cytoff\\20190801_experiment_31600_files\\072519_Frederique_HIMC Sample Drop Off Form 190417-1.xlsx'])]

if 2 in a[0]:
    print('2 in 0 part of array')
if 6 in a[1]:
    print ('6 in part 1')
if 8 in a[2]:
    print ('8 in part 2')

for i in range(len(a)):
    for j in range(len(a[i])):
        print(a[i][j], end=' ')
    print()

sys.exit()

path = 'E:\MounSinai\Darpa\Programming\submission\data_examples\Bulk_Drive\ECHO\HIV\HI\PBMC\cytoff'
path2 = 'E:\MounSinai\Darpa\Programming\submission\data_examples\Bulk_Drive\ECHO\HIV\HI\PBMC\scatac-seq'
exclude_dirs = []
ext_match = ['.xlsx', '.xls']

files = get_file_system_items(path, 2, [], 'file', ext_match)
print (files)

dirs =  get_file_system_items(path2, 2, ['fastqs', 'FASTQs'], 'dir')
print (dirs)