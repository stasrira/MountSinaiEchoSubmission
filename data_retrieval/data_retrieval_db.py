class DataRetrievalDB():

    def __init__(self, request):
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger

        self.conf_process_entity = self.req_obj.conf_process_entity
        self.conf_main = self.req_obj.conf_main

        self.init_specific_settings()

