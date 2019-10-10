from file_load import MetaFileText, MetaFileExcel
from pathlib import Path
import sys
import os
from os import walk
import time
import traceback
from utils.log_utils import setup_logger_common, deactivate_logger_common
from utils import ConfigData
from utils import global_const as gc
from utils import send_email as email
from file_load import Request

# if executed by itself, do the following
if __name__ == '__main__':

    # load main config file and get required values
    m_cfg = ConfigData(gc.CONFIG_FILE_MAIN)

    # print ('m_cfg = {}'.format(m_cfg.cfg))
    # assign values
    common_logger_name = gc.MAIN_LOG_NAME # m_cfg.get_value('Logging/main_log_name')
    logging_level = m_cfg.get_value('Logging/main_log_level')
    requests_loc = m_cfg.get_value('Location/requests')
    log_folder_name = gc.LOG_FOLDER_NAME
    processed_folder_name = gc.PROCESSED_FOLDER_NAME

    # requests_loc = 'E:/MounSinai/MoTrPac_API/ProgrammaticConnectivity/MountSinai_metadata_file_loader/DataFiles'
    requests_path = Path(requests_loc)

    # get current location of the script and create Log folder
    logdir = Path(m_cfg.prj_wrkdir) / log_folder_name  # 'logs'
    lg_filename = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + '.log'

    lg = setup_logger_common(common_logger_name, logging_level, logdir, lg_filename)  # logging_level
    mlog = lg['logger']

    mlog.info('Start processing submission requests in "{}"'.format(requests_path))

    try:

        (_, _, requests) = next(walk(requests_path))
        # print('Study requests: {}'.format(requests))

        mlog.info('Submission requests to be processed (count = {}): {}'.format(len(requests), requests))

        req_proc_cnt = 0

        for req_file in requests:
            if req_file.endswith(('xlsx','xls')):
                req_path = Path(requests_path) / req_file

                # email_msgs_study = []
                # email_attchms_study = []

                try:
                    # print('--------->Process file {}'.format(req_path))
                    mlog.info('Request file {} was selected for processing.'.format(req_path))

                    # save timestamp of beginning of the file processing
                    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
                    """
                    #load request file
                    rf = ConfigData(req_path)
                    if rf.loaded:
                        try:
                            req_obj = Request ()
                        except Exception as ex:
                            _str = 'Attempt to read loaded request file failed with error: {}\n{} ' \
                                .format(ex, traceback.format_exc())
                            mlog.error(_str)
                            req_obj = None
                    else:
                        mlog.error('Loaded request file was empty. Request file: "{}".'.format(req_path))
                    """

                    req_obj = Request(req_path)

                    if req_obj and req_obj.loaded:
                        # proceed processing request
                        mlog.info('Submission request loading status: Success. Submission request file: "{}".'.format(req_path))

                        req_obj.process_request()
                        # process selected requestS
                        #req_obj.process_file()

                        mlog.info('Processing of Submission request was finished for {} request.'.format(req_path))
                        req_proc_cnt += 1

                    # identify if any errors were identified and set status variable accordingly
                    if not req_obj.error.exist():
                        fl_status = 'OK'
                        _str = 'Processing status: "{}". Submission Request: {}'.format(fl_status, req_path)
                    else:
                        fl_status = 'ERROR'
                        _str = 'Processing status: "{}". Check processing log file for this request: {}'\
                            .format(fl_status, req_obj.logger.handlers[0])

                    if fl_status == "OK":
                        mlog.info(_str)
                    else:
                        mlog.warning(_str)

                    # deactivate the current Request logger
                    deactivate_logger_common(req_obj.logger, req_obj.log_handler)

                    processed_dir = Path(requests_path) / processed_folder_name  # 'Processed'
                    # if Processed folder does not exist in the Requests folder, it will be created
                    os.makedirs(processed_dir, exist_ok=True)

                    req_processed_name = ts + '_' + fl_status + '_' + req_file
                    # print('New file name: {}'.format(ts + '_' + fl_status + '_' + fl))
                    # move processed files to Processed folder
                    os.rename(req_path, processed_dir / req_processed_name)
                    mlog.info('Processed Submission request "{}" was moved and renamed as: "{}"'
                              .format(req_path, processed_dir / req_processed_name))

                    """
                    # preps for email notification
                    email_msgs_study.append(
                                ('File <br/>"{}" <br/> was processed and moved/renamed to <br/> "{}".'
                                 '<br/> <b>Errors summary:</b> '
                                 '<br/> File level errors: {}'
                                 '<br/> Row level errors: {}'
                                 '<br/> <i>Log file location: <br/>"{}"</i>'
                                 ''.format(req_path,
                                           processed_dir / req_processed_name,
                                           '<font color="red">Check Errors in the log file (attached)</font>'
                                                if fl_ob.error.exist()
                                                else '<font color="green">No Errors</font> (the log file is attached)',
                                           '<font color="red">Check Errors in the log file (attached)</font>'
                                                if fl_ob.error.row_errors_count()
                                                else '<font color="green">No Errors</font> (the log file is attached)',
                                           fl_ob.log_handler.baseFilename)
                                 )
                    )
                    email_attchms_study.append(fl_ob.log_handler.baseFilename)
    
                    # print ('email_msgs_study = {}'.format(email_msgs_study))
                    """

                    req_obj = None

                except Exception as ex:
                    # report an error to log file and proceed to next file.
                    mlog.error('Error "{}" occurred during processing file: {}\n{} '
                               .format(ex, req_path, traceback.format_exc()))
                    raise

        mlog.info('Number of successfully processed Submission requests = {}'.format(req_proc_cnt))
        """
        if req_proc_cnt > 0:
            # collect final details and send email about this study results
            email_subject = 'Metadata files loading for study "{}"'.format(st_dir)
            email_body = ('Number of files processed for study "{}": {}.'.format(st_dir, req_proc_cnt)
                            + '<br/><br/>'
                            + '<br/><br/>'.join(email_msgs_study)
                            )

            # print ('email_subject = {}'.format(email_subject))
            # print('email_body = {}'.format(email_body))

            try:
                if m_cfg.get_value('Email/send_emails'):
                    email.send_yagmail(
                        emails_to = m_cfg.get_value('Email/sent_to_emails'),
                        subject = email_subject,
                        message = email_body,
                        attachment_path = email_attchms_study
                    )
            except Exception as ex:
                # report unexpected error during sending emails to a log file and continue
                _str = 'Unexpected Error "{}" occurred during an attempt to send email upon ' \
                       'finishing processing "{}" study: {}\n{} '\
                    .format(ex, st_dir, os.path.abspath(__file__), traceback.format_exc())
                mlog.critical(_str)
        """

    except Exception as ex:
        # report unexpected error to log file
        _str = 'Unexpected Error "{}" occurred during processing file: {}\n{} '\
            .format(ex, os.path.abspath(__file__), traceback.format_exc())
        mlog.critical(_str)
        raise

    sys.exit()

