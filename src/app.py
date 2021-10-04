import imaplib
import hydra
from omegaconf import DictConfig
import logging
from service import mail_ferry, document_builder

log = logging.getLogger(__name__)


@hydra.main(config_path="conf", config_name="config")
def app(cfg: DictConfig) -> None:
    log.info('********* STARTING MAIL DOCUMENTER SERVICE ***********')
    # create an IMAP4 class with SSL
    imap = imaplib.IMAP4_SSL(cfg.mail.server)
    messages = mail_ferry.authenticate(
        imap, cfg.mail.username, cfg.mail.password, cfg.mail.folder, cfg.mail.readonly_mode)
    log.info('********* AUTHENTICATION COMPLETE ***********')
    ids = ''
    if cfg.mail.filter_mode:
        log.info('********* FILTER MODE ENABLED ***********')
        ids = mail_ferry.filter_mails(imap, cfg.mail)
    else:
        log.info('********* FILTER NOT SET, GETTING ALL ***********')
        (_, data) = imap.search(None, "ALL")
        log.info('data: {0}'.format(data))
        ids = data[0].split()
    log.info('ids: {0}'.format(ids))
    if ids:
        log.info('********* FETCHING EMAIL DATA ***********')
        mail_detail_list = mail_ferry.fetch_mail(imap, ids)
        log.info('mail_detail_list: {0}'.format(mail_detail_list))
        document_builder.initiate_build(cfg.document, mail_detail_list)
    else:
        log.info('********* NO MAILS FOUND MATCHING CRITERIA ***********')
    # close the connection and logout
    imap.close()
    imap.logout()
    log.info('********* ENDING MAIL DOCUMENTER SERVICE ***********')
    return "Execution Complete"


if __name__ == '__main__':
    app()
