# ========== config file names
# main config file name
CONFIG_FILE_MAIN = 'configs/main_config.yaml'
CONFIG_FILE_ASSAY = 'configs/assay_config.yaml'
CONFIG_FILE_CENTER = 'configs/center_config.yaml'
CONFIG_FILE_DICTIONARY = 'configs/dict_config.yaml'

PROJECT_NAME = 'ECHO'  # this key is stored in here instead of being passed from a request.
DEFAULT_REQUEST_TYPE = 'sequence'

# study level default name for the config file
# DEFAULT_STUDY_CONFIG_FILE = 'study.cfg.yaml'

# name for the each type of log
MAIN_LOG_NAME = 'main_log'
REQUEST_LOG_NAME = 'request_processing_log'

# default folder names for logs and processed files

# following variables will be defined at the start of execution based on the config values from main_config.yaml
APP_LOG_DIR = ''  # path to the folder where all application level log files will be stored (one file per run)
REQ_LOG_DIR = ''  # path to the folder where all log files for processing request files will be stored
                          # (one file per request)
REQ_PROCESSED_DIR = ''  # path to the folder where all processed (and renamed) requests will be stored
DISQUALIFIED_REQUESTS = '' # path to dir where will be saved dynamically created request files for disqualified aliquots
OUTPUT_PACKAGES_DIR = ''  # path to the folder where all processed (and renamed) requests will be stored
SUBMISSION_FORMS_DIR = 'forms'
TARBALL_APPROACH = 'tarfile'  # "tarfile" (default) and "commandline" are expected values
TARBALL_SAVE_MD5SUM_FILE = True # set default functionality to create physical MD5sum files

# the following 3 lines are to be removed
# SUBMISSION_PACKAGES_DIR = "submission_packages"
# LOG_FOLDER_NAME = 'logs'
# PROCESSED_FOLDER_NAME = 'processed'

# name of the sheet name in the request file (excel file) where from data should be retrieved.
# If omitted, the first sheet in array of sheets will be used
REQUEST_EXCEL_WK_SHEET_NAME = ''  # 'Submission_Request'

# default values for Study config file properties
# DEFAULT_CONFIG_VALUE_LIST_SEPARATOR = ','
# DEFAULT_REQUEST_SAMPLE_TYPE_SEPARATOR = '/'

SUBMISSION_YAML_EVAL_FLAG = 'eval!'

ASSAY_CHARS_TO_REPLACE = [' ', '/', '\\']

# default study config file extension
# DEFAULT_STUDY_CONFIG_FILE_EXT = '.cfg.yaml'

# database related constants
# predefined paths in the main config file for database related parameters
# CFG_DB_CONN = 'DB/mdb_conn_str'  # name of the config parameter storing DB connection string
# CFG_DB_SQL_PROC = 'DB/mdb_sql_proc_load_sample'  # name of the config parameter storing DB name of the stored proc
# predefined names for stored procedure parameters that being passed to procedure specified in "CFG_DB_SQL_PROC"
# CFG_FLD_TMPL_STUDY_ID = 'DB/fld_tmpl_study_id'
# CFG_FLD_TMPL_SAMPLE_ID = 'DB/fld_tmpl_sample_id'
# CFG_FLD_TMPL_ROW_JSON = 'DB/fld_tmpl_row_json'
# CFG_FLD_TMPL_DICT_JSON = 'DB/fld_tmpl_dict_json'
# CFG_FLD_TMPL_DICT_PATH = 'DB/fld_tmpl_dict_path'
# CFG_FLD_TMPL_FILEPATH = 'DB/fld_tmpl_filepath'
# CFG_FLD_TMPL_DICT_UPD = 'DB/fld_tmpl_dict_update'
# CFG_FLD_TMPL_SAMPLE_UPD = 'DB/fld_tmpl_samlpe_update'

# predefined paths in the study config file for database related parameters
# CFG_DB_STUDY_ID = 'mdb_study_id'  # name of the config parameter storing key of the MDB study id
# CFG_DICT_PATH = 'dict_tmpl_fields_node'  # name of config parameter storing key of dictionary path to list of fields
# CFG_DB_ALLOW_DICT_UPDATE = 'mdb_allow_dict_update'  # name of config parameter storing values for "allow dict updates"
# CFG_DB_ALLOW_SAMPLE_UPDATE = 'mdb_allow_sample_update'# name of config param storing values for "allow sample updates"

# Excel processing related
# STUDY_EXCEL_WK_SHEET_NAME = 'wk_sheet_name'  # name of the worksheet name to be used for loading data from
