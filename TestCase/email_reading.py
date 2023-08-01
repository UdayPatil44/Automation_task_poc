import imaplib
import email
import traceback

ORG_EMAIL = "@gmail.com"
FROM_EMAIL = "udaypatil4495" + ORG_EMAIL
PASSWORD = input("Enter the Password: ")
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993


def read_email_from_gmail():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(FROM_EMAIL, PASSWORD)
        mail.select('inbox')
        _, data = mail.search(None, 'ALL')
        mail_ids = data[0].split()
        first_email_id = int(mail_ids[0])
        latest_email_id = int(mail_ids[-1])
        for (index, i) in enumerate(range(latest_email_id, first_email_id - 1, -1)):
            _, data = mail.fetch(str(i), '(RFC822)')
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    # Print (msg.keys())
                    email_subject = msg['subject']
                    email_from = msg['from']
                    date = msg['Date']
                    print("Date:", date, '\n')
                    print(index + 1, 'From:', email_from, '\n')
                    print('Subject:', email_subject, '\n')
                    print("-" * 100)
            if index == 15:
                break
    except Exception as e:
        traceback.print_exc()
        print(str(e))


read_email_from_gmail()
