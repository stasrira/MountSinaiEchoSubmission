from data_retrieval import DataRetrievalDB
from utils import global_const as gc


class DataSourceDB(DataRetrievalDB):

    def __init__(self, request_obj, data_source_id, data_source_name):
        self.data_source_id = data_source_id
        self.data_source_name = data_source_name
        self.cnf_data_source = None
        self.mdb_study_id = None
        self.db_config_section_name = None
        self.db_config = None
        self.metadata = None
        self.manifest = None
        self.subject = None
        DataRetrievalDB.__init__(self, request_obj)

    def init_specific_settings(self):
        # this function is called by the base class to perform actions specific to the current class' needs

        # get configuration info for the current data source id (of the current center, i.e. HI)
        self.cnf_data_source = self.conf_process_entity[self.data_source_id]

        # get study_id (of the MDB database) assigned to for the current data source
        self.mdb_study_id = self.cnf_data_source['mdb_study_id']

        # get name of the main_config's section holding database information for the current data_source_id
        self.db_config_section_name = self.cnf_data_source['db_config_section_name']
        # get database related config information from the main_config file
        self.db_config = self.conf_main.get_value(self.db_config_section_name)

        self.s_conn = self.db_config[gc.CFG_DB_CONN].strip()

        pass

    def get_db_data(self):
        # get configuration data for all required db calls
        sql_proc_metadata = self.db_config[gc.CFG_DB_PROC_METADATA].strip()
        sql_proc_manifest = self.db_config[gc.CFG_DB_PROC_MANIFEST].strip()
        sql_proc_subject = self.db_config[gc.CFG_DB_PROC_SUBJECT].strip()

        # get sample metadata from DB
        metadata = self.get_dataset(sql_proc_metadata)
        self.metadata = self.convert_dataset_to_db_object(metadata, 'sample_id', 'subject_id')
        # get manifest from DB
        manifest = self.get_dataset(sql_proc_manifest)
        self.manifest = self.convert_dataset_to_db_object(manifest, 'aliquot_id', 'sample_id')
        # get subject metadata from DB
        subject = self.get_dataset(sql_proc_subject)
        self.subject = self.convert_dataset_to_db_object(subject, 'subject_id')


        #TODO: implement validation of datasets received from DB. If any of those is None, disqualify the current request

        self.conn.close()
        pass


    def get_dataset(self, str_proc):
        rs_out = None

        # prepare stored proc string to be executed
        str_proc = str_proc.replace(self.db_config[gc.CFG_FLD_TMPL_STUDY_ID],
                                    str(self.mdb_study_id))  # '{study_id}'
        str_proc = str_proc.replace(self.db_config[gc.CFG_FLD_TMPL_SAMPLE_IDS],
                                    ','.join(self.req_obj.samples))  # '{sample_ids}'
        str_proc = str_proc.replace(self.db_config[gc.CFG_FLD_TMPL_ALIQUOT_IDS],
                                    ','.join(self.req_obj.aliquots))  # '{aliquot_ids}'

        rs_out, str_error = self.exec_sql_procedure_with_output (str_proc)

        if len(str_error) > 0:
            # error was returned from DB
            return None

        return rs_out

    def convert_dataset_to_db_object(self, dataset, id_main_name, id_2_name = None):
        obj_out = {}
        if dataset:
            for row in dataset:
                id_main = ''
                id_2 = ''
                if row:
                    if id_main_name in row.keys():
                        id_main = row[id_main_name]
                    if id_2_name:
                        if id_2_name in row.keys():
                            id_2 = row[id_2_name]
                    obj_out[id_main] = {'id_2': id_2, 'data': row}
        return obj_out


