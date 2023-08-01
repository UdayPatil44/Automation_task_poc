import imaplib
import email
from email.header import decode_header
import os
import re
import sys
import boto3
from TestCase.readProperties import readConfig

# Function to clean the filename from any invalid characters
def clean_filename(filename):
    return re.sub(r'[^\w\-_. ]', '', filename)

# Function to sanitize folder names
def clean_foldername(foldername):
    # Remove characters that are not allowed in Windows folder names
    restricted_chars = r'<>:"/\|?*'
    foldername = ''.join(c for c in foldername if c not in restricted_chars)

    # Remove leading and trailing spaces and truncate folder name
    foldername = foldername.strip()[:100]

    # Replace any remaining spaces with underscores
    foldername = foldername.replace(" ", "_")

    return foldername


# Function to get the absolute path of the script's directory
def get_script_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.realpath(__file__))

# Function to upload a file to AWS S3
def upload_to_s3(filepath, key):
    s3 = boto3.client("s3", aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    s3.upload_file(filepath, aws_bucket_name, key)

# account credentials
username = readConfig.getUserEmail()
password = readConfig.getPassword()

# use your email provider's IMAP server, you can look for your provider's IMAP server on Google
# or check this page: https://www.systoolsgroup.com/imap/
# for gmail, it's this:
imap_server = "imap.gmail.com"

# create an IMAP4 class with SSL
imap = imaplib.IMAP4_SSL(imap_server)
# authenticate
imap.login(username, password)

status, messages = imap.select("INBOX")
# number of top emails to fetch
N = 4
# total number of emails
messages = int(messages[0])

# AWS S3 configuration
aws_access_key = readConfig.getAwsAccessKey()
aws_secret_key = readConfig.getAwasSecretAccessKey()
aws_bucket_name = readConfig.getAwsBucketName()

# Get the absolute path of the script's directory
script_directory = get_script_directory()

for i in range(messages, messages - N, -1):
    # fetch the email message by ID
    res, msg = imap.fetch(str(i), "(RFC822)")
    for response in msg:
        if isinstance(response, tuple):
            # parse a bytes email into a message object
            msg = email.message_from_bytes(response[1])
            # decode the email subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                # if it's a bytes, decode to str
                subject = subject.decode(encoding)
            # decode email sender
            From, encoding = decode_header(msg.get("From"))[0]
            if isinstance(From, bytes):
                From = From.decode(encoding)
            print("Subject:", subject)
            print("From:", From)
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
                        print(body)
                    elif "attachment" in content_disposition:
                        # download attachment
                        filename, charset = decode_header(part.get_filename())[0]
                        if isinstance(filename, bytes):
                            filename = filename.decode(charset or 'utf-8', 'ignore')
                        filename = clean_filename(filename)
                        if filename:
                            folder_name = clean_foldername(subject)
                            folder_path = os.path.join(script_directory, folder_name)

                            if not os.path.isdir(folder_path):
                                # make a folder for this email (named after the subject)
                                os.makedirs(folder_path, exist_ok=True)

                            filepath = os.path.join(folder_path, filename)
                            # download attachment and save it
                            with open(filepath, "wb") as file:
                                file.write(part.get_payload(decode=True))

                            # Upload the attachment to AWS S3
                            with open(filepath, "rb") as file:
                                s3_key = f"{folder_name}/{filename}"
                                upload_to_s3(filepath, s3_key)
            else:
                # extract content type of email
                content_type = msg.get_content_type()
                # get the email body
                body = msg.get_payload(decode=True).decode()
                if content_type == "text/plain":
                    # print only text email parts
                    print(body)
            if content_type == "text/html":
                # if it's HTML, create a new HTML file and save it
                folder_name = clean_foldername(subject)
                folder_path = os.path.join(script_directory, folder_name)

                if not os.path.isdir(folder_path):
                    # make a folder for this email (named after the subject)
                    os.makedirs(folder_path, exist_ok=True)

                filename = "index.html"
                filepath = os.path.join(folder_path, filename)
                # write the file using UTF-8 encoding
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(body)

            print("=" * 100)

# close the connection and logout
imap.close()
imap.logout()
