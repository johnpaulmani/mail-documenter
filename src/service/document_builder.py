import time
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

# =============================== The content =======================

md_template = """

/Users/johnpaulmani/Work Assignments/MailDocumenter/src/images/confid.jpeg

****************************** AUTO GENERATED - START ******************************
AGTS: time.ctime()
 
sdheader: 
    mdsender
sbheader: 
    mdsubject
 
byheader:
    mdbody

****************************** AUTO GENERATED - END ******************************
"""
# ===========================================================


def initiate_build(cfg_document, mail_detail_list):
    if cfg_document.type == 'pdf':
        for mail_detail in mail_detail_list:
            construct_pdf(mail_detail)


def add_image(img, page):
    im = Image(img, 2*inch, 2*inch)
    page.append(im)


def add_space(page):
    page.append(Spacer(1, 12))


def add_text(text, page, space=0):
    if type(text) == list:
        for f in text:
            add_text(f)
    else:
        ptext = f'<font size="12">{text}</font>'
        page.append(Paragraph(ptext, styles["Normal"]))
        if space == 1:
            add_space(page)
        add_space(page)


def add_bold_text(text, page):
    ptext = f'<font name="Times-Bold" size="13">{text}</font>'
    page.append(Paragraph(ptext, styles["Normal"]))


def construct_pdf(mail_detail):
    dir_name = mail_detail.get('folder_name') + '/md_ag.pdf'
    doc = SimpleDocTemplate(dir_name, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    page = []
    "Prints all the lines in the text multiline string"
    text = md_template.splitlines()
    for line in text:
        if "confid" in line:
            add_image(line, page)
        elif "ctime()" in line:
            add_text(time.ctime(), page)
        elif "sdheader" in line:
            add_bold_text('Sender:', page)
        elif "mdsender" in line:
            add_text(mail_detail.get('sender'), page)
        elif "sbheader" in line:
            add_bold_text('Subject:', page)
        elif "mdsubject" in line:
            add_text(mail_detail.get('subject'), page)
        elif "byheader" in line:
            add_bold_text('Body:', page)
        elif "mdbody" in line:
            add_text(mail_detail.get('body'), page)
        else:
            add_text(line, page)
    doc.build(page)
