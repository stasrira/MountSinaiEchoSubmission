from data_retrieval import DataRetrievalDB


class DataSourceDB(DataRetrievalDB):

    def __init__(self, request_obj, data_source_id, data_source_name):
        self.data_source_id = data_source_id
        self.data_source_name = data_source_name
        self.cnf_data_source = None
        self.mdb_study_id = None
        self.db_config_section_name = None
        self.db_config = None
        DataRetrievalDB.__init__(self, request_obj)

    def init_specific_settings(self):
        # this function is called by the base class to perform actions specific to the current class' needs
        self.cnf_data_source = self.conf_process_entity[self.data_source_id]
        self.mdb_study_id = self.cnf_data_source['mdb_study_id']
        self.db_config_section_name = self.cnf_data_source['db_config_section_name']
        self.db_config = self.conf_main.get_value(self.db_config_section_name)
        pass