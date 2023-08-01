import imaplib
import email
import os
import re
import urllib

from urllib.request import urlretrieve
import boto3
import logging
import requests
from TestCase.readProperties import readConfig

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(os.listdir())

# Your AWS credentials and S3 bucket name
AWS_ACCESS_KEY_ID = readConfig.getAwsAccessKey()
AWS_SECRET_ACCESS_KEY = readConfig.getAwasSecretAccessKey()
S3_BUCKET_NAME = readConfig.getAwsBucketName()


def is_valid_url(url):
    # Check if the URL starts with a valid scheme (http or https)
    return url.startswith(("http://", "https://"))


def extract_urls_from_text(text):
    # Regular expression pattern to find URLs in the text
    pattern = r'(https?://\S+)|(www\.\S+)|(ftp://\S+)'
    return [match.group() for match in re.finditer(pattern, text)]


def download_attachment(url, save_path):
    try:
        urllib.request.urlretrieve(url, save_path)
        logging.info(f"File downloaded from URL: {url}")

        # Upload the downloaded file to S3
        s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        s3_key = os.path.basename(save_path)
        s3_client.upload_file(save_path, S3_BUCKET_NAME, s3_key)

        logging.info(f"File uploaded to S3 bucket: {s3_key}")

    except Exception as e:
        logging.error(f"Error occurred while downloading or uploading file: {e}")


def resolve_shortened_url(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.url
    except requests.exceptions.RequestException:
        return url


def fetch_emails(server, username, password, max_emails=1):
    logging.info("Fetching emails from the server...")
    mail = imaplib.IMAP4_SSL(server)
    mail.login(username, password)
    mail.select("INBOX")

    status, messages = mail.search(None, "ALL")
    messages = messages[0].split()

    num_emails_to_process = min(len(messages), max_emails)

    email_list = []

    for msg_id in reversed(messages[-num_emails_to_process:]):
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        email_list.append(msg)

    mail.close()
    mail.logout()

    logging.info("Emails fetched successfully.")
    return email_list


def read_and_process_emails(server, username, password, max_emails=1):
    emails = fetch_emails(server, username, password, max_emails)

    for email_message in emails:
        # Extract URLs from the email content
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8")
                    break
        else:
            body = email_message.get_payload(decode=True).decode("utf-8")

        if body:
            urls = extract_urls_from_text(body)
            logging.info("Extracted URLs from the email:")
            for url in urls:
                logging.info(url)

            # Rest of the processing (downloading attachments, uploading to S3, etc.)
            for url in urls:
                final_url = resolve_shortened_url(url)

                # Check if the URL is for an attachment (assuming it starts with https:// and has a "download" attribute)
                if url is not None:
                    # Get the filename from the URL
                    filename = os.path.basename(final_url)

                    # Download the attachment
                    download_dir = os.path.join(os.path.abspath(os.getcwd()), "downloads")
                    if not os.path.exists(download_dir):
                        os.makedirs(download_dir)

                    save_path = os.path.join(download_dir, filename)

                    # logging.info("Download path is :", save_path)
                    download_attachment(final_url, save_path)

                else:
                    logging.warning(f"URL found, but has no attachment: {final_url}")

    logging.info("All emails have been processed.")


if __name__ == "__main__":
    email_server = "imap.gmail.com"
    email_username = readConfig.getUserEmail()
    email_password = readConfig.getPassword()

    num_emails_to_process = int(input("Enter the number of most recent emails to process: "))
    read_and_process_emails(email_server, email_username, email_password, num_emails_to_process)
