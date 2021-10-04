import email
from email.header import decode_header
import webbrowser
import os
from helper import filehelper
import datetime
import logging
import sys

log = logging.getLogger(__name__)


def authenticate(imap, username, password, mail_folder_name, readonly_mode):
    log.info('********* AUTHENTICATING ***********')
    # authenticate
    imap.login(username, password)
    # mail folder
    status, messages = imap.select(mail_folder_name, readonly_mode)
    # total number of emails
    messages = int(messages[0])
    return messages


def search_email(imap):
    date = (datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y")
    (_, data) = imap.search(None, ('UNSEEN'), '(SENTSINCE {0})'.format(
        date)), '(FROM {0})'.format("someone@yahoo.com".strip())
    ids = data[0].split()
    return ids


def filter_mails(imap, mail_cfg):
    log.info('********* FILTERING PROCESS STARTED ***********')
    switcher = {
        'date': filter_by_date(imap, str(mail_cfg.start_date), str(mail_cfg.end_date)),
        'keyword': filter_by_keyword(imap, mail_cfg.filter_keyword),
    }
    return switcher.get(mail_cfg.filter_type, "nothing")


def filter_by_date(imap, start_date, end_date):
    log.info('********* FILTERING BY DATE ***********')
    # define since/before dates
    #date_format = "%d-%b-%Y" # DD-Mon-YYYY e.g., 3-Mar-2014
    #since_date = datetime.strptime(start_date, date_format)
    #before_date = datetime.strptime(end_date, date_format)

    # get all messages since since_date and before before_date
    (_, data) = imap.search(None,
        '(since "%s" before "%s")' % (format_date(start_date),
                                      format_date(end_date)))
    #(_, data) = imap.search(None, '(SINCE {0} BEFORE {1})'.format(
    #    format_date(end_date), format_date(start_date)))
    log.info('data: {0}'.format(data))
    ids = data[0].split()
    return ids


def filter_by_keyword(imap, keyword):
    log.info('********* FILTERING BY KEYWORD ***********')
    (_, data) = imap.search(None, '(TEXT {0})'.format(keyword))
    ids = data[0].split()
    return ids


def format_date(ipdate):
    fmt_date = datetime.date(int(ipdate[-4:]), int(ipdate[2:4]), int(ipdate[:2])).strftime("%d-%b-%Y")
    log.info('fmt_date: {0}'.format(fmt_date))
    return fmt_date


def fetch_mail(imap, ids):
    # for i in range(messages, messages-count, -1):
    mail_detail_list = []
    for emailid in ids[::-1]:
        res, msg = imap.fetch(emailid, "(RFC822)")
        log.info('res: {0}'.format(res))
        mail_detail = {}
        for response in msg:
            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                pbody = ''
                subject = fetch_subject(msg)
                sender = fetch_sender(msg)
                log.info('Subject: {0}'.format(subject))
                log.info('Sender: {0}'.format(sender))
                mail_detail['subject'] = subject
                mail_detail['sender'] = sender
                folder_name = filehelper.clean(subject)
                # make a folder for this email (named after the subject)
                os.mkdir(folder_name)
                # if the email message is multipart
                if msg.is_multipart():
                # iterate over email parts
                    for part in msg.walk():
                        # extract content type of email
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            # get the email body
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            # print text/plain emails and skip attachments
                            log.info('content_type: {0}'.format(content_type))
                            pbody = body
                        elif "attachment" in content_disposition:
                            # download attachment
                            filename = part.get_filename()
                            if filename:
                                folder_name = filehelper.clean(subject)
                                if not os.path.isdir(folder_name):
                                    # make a folder for this email (named after the subject)
                                    os.mkdir(folder_name)
                                filepath = os.path.join(folder_name, filename)
                                # download attachment and save it
                                open(filepath, "wb").write(part.get_payload(decode=True))
                else:
                    # extract content type of email
                    content_type = msg.get_content_type()
                    # get the email body
                    body = msg.get_payload(decode=True).decode()
                    if content_type == "text/plain":
                        # print only text email parts
                        log.info('content_type: {}'.format(content_type))
                        pbody = body
                if content_type == "text/html":
                    # if it's HTML, create a new HTML file and open it in browser
                    folder_name = filehelper.clean(subject)
                    if not os.path.isdir(folder_name):
                        # make a folder for this email (named after the subject)
                        os.mkdir(folder_name)
                    filename = "index.html"
                    filepath = os.path.join(folder_name, filename)
                    # write the file
                    open(filepath, "w").write(body)
                    # open in the default browser
                    webbrowser.open(filepath)
                log.info('body: {0}'.format(body))
                log.info("="*100)
                mail_detail['folder_name'] = folder_name
                mail_detail['body'] = pbody
                mail_detail_list.append(mail_detail)
    return mail_detail_list


def fetch_subject(msg):
    # decode the email subject
    subject, encoding = decode_header(msg["Subject"])[0]
    log.info('enc: {}'.format(encoding))
    if isinstance(subject, bytes):
        try:
            # if it's a bytes, decode to str
            subject = subject.decode(encoding)
        except TypeError:
            subject = subject.decode('utf-8')
    return subject


def fetch_sender(msg):
    # decode email sender
    sender, encoding = decode_header(msg.get("From"))[0]
    if isinstance(sender, bytes):
        # if it's a bytes, decode to str
        sender = sender.decode(encoding)
    return sender


def process_multipart_mail(msg, folder_name):
    body = ''
    # iterate over email parts
    for part in msg.walk():
        # extract content type of email
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition"))
        try:
            # get the email body
            body = part.get_payload(decode=True).decode()
        except:
            pass
        if content_type == "text/plain" and "attachment" not in content_disposition:
            # print text/plain emails and skip attachments
            continue
        elif "attachment" in content_disposition:
            log.info('attachment present')
            # download attachment
            filename = part.get_filename()
            log.info('att_name: {0}'.format(filename))
            if filename:
                #folder_name = filehelper.clean(subject)
                # if not os.path.isdir(folder_name):
                # make a folder for this email (named after the subject)
                # os.mkdir(folder_name)
                filepath = os.path.join(folder_name, filename)
                # download attachment and save it
                #open(filepath, "wb").write(part.get_payload(decode=True))
                fp = open(filepath, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()
    return body


def process_web_content(body, folder_name):
    log.info('html content present')
    # if it's HTML, create a new HTML file and open it in browser
    #folder_name = filehelper.clean(subject)
    # if not os.path.isdir(folder_name):
    # make a folder for this email (named after the subject)
    # os.mkdir(folder_name)
    filename = "index.html"
    filepath = os.path.join(folder_name, filename)
    # write the file
    open(filepath, "w").write(body)
    fp = open(filepath, 'w')
    fp.write(body)
    fp.close()
    # open in the default browser
    # webbrowser.open(filepath)
