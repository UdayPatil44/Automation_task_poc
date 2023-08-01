import time
import os
import re
import urllib
import string
from urllib.parse import urlparse

import requests
from urllib.request import urlretrieve
import boto3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from TestCase.readProperties import readConfig

# Your AWS credentials and S3 bucket name
AWS_ACCESS_KEY_ID = readConfig.getAwsAccessKey()
AWS_SECRET_ACCESS_KEY = readConfig.getAwasSecretAccessKey()
S3_BUCKET_NAME = readConfig.getAwsBucketName()


def extract_urls_from_text(text):
    # Regular expression pattern to find URLs in the text
    pattern = r'(https?://\S+)|(www\.\S+)|(ftp://\S+)'
    return [match.group() for match in re.finditer(pattern, text)]


def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars)


def download_attachment(url, save_path):
    try:
        urllib.request.urlretrieve(url, save_path)
        print(f"Attachment downloaded from URL: {url}")

        url_filename = os.path.basename(urlparse(url).path)
        sanitized_filename = sanitize_filename(url_filename)

        # Upload the downloaded file to S3
        s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        s3_key = os.path.basename(save_path)
        s3_client.upload_file(save_path, S3_BUCKET_NAME, s3_key)

        print(f"Attachment uploaded to S3 bucket: {s3_key}")

    except Exception as e:
        print(f"Error occurred while downloading or uploading attachment: {e}")


def resolve_shortened_url(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.url
    except requests.exceptions.RequestException:
        return url


def open_all_urls_in_text(text, driver, headless_driver):
    # Extract all URLs from the text
    urls = extract_urls_from_text(text)

    try:
        for url in urls:
            # Check if the URL ends with punctuation marks and remove them
            url = re.sub(r'[.,!?;]$', '', url)

            print(f"URL found: {url}")

            # Get the final destination URL for shortened URLs
            final_url = resolve_shortened_url(url)

            # Check if the URL is for an attachment (assuming it starts with https:// and has a "download" attribute)
            if final_url is not None:
                # Get the filename from the URL
                filename = os.path.basename(final_url)

                # Download the attachment
                download_dir = os.path.join(os.path.abspath(os.getcwd()), "SMS downloads")
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)

                save_path = os.path.join(download_dir, sanitize_filename(filename))
                download_attachment(final_url, save_path)

            else:
                print(f"URL found, but has no attachment: {final_url}")

            # Open the URL in a new tab using the headless browser
            headless_driver.execute_script(f"window.open('{final_url}', '_blank');")

            # Wait for the new tab to load fully
            time.sleep(3)

    except Exception as e:
        print(f"Error occurred: {e}")


def read_first_03_messages():
    chrome_driver_path = "C:\\Drivers\\chromedriver_win32\\chromedriver.exe"

    # Set up the ChromeDriver service
    service = Service(chrome_driver_path)

    # Set options for the browser
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Maximize the window (not headless)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Set options for the headless browser
    headless_options = Options()
    headless_options.add_argument("--headless")  # Run in headless mode

    headless_driver = webdriver.Chrome(service=service, options=headless_options)

    # Open Google Messages
    driver.get("https://messages.google.com/web/authentication")

    # Wait for the user to log in and scan the QR code
    input("Press Enter after scanning the QR code...")
    time.sleep(3)
    # Dismiss the notification alert if present
    try:
        driver.find_element(By.XPATH, "//span[normalize-space()='No thanks']").click()
    except:
        pass

    # Find the conversation list and click on the first conversation
    try:
        conversation_list = driver.find_elements(By.XPATH, "//mws-conversation-list-item[@class='ng-star-inserted']")
        for i, conversation in enumerate(conversation_list[:5], start=1):
            conversation.click()
            time.sleep(3)
            # Wait for the message list to load

            # Read the first 10 messages and extract URLs from the text
            messages = driver.find_elements(By.XPATH,
                                            "//mws-message-wrapper[contains(@class,'ng-trigger ng-trigger-incomingMessage')]")
            for j, message in enumerate(messages[:3], start=1):
                print(f"Message {j}: {message.text}")

                # Open all URLs in the message text using the headless browser
                open_all_urls_in_text(message.text, driver, headless_driver)

    except TimeoutException:
        print("Timed out while waiting for elements to load.")
    finally:
        # Close both browser windows after all messages are processed
        driver.quit()
        headless_driver.quit()


if __name__ == "__main__":
    read_first_03_messages()
