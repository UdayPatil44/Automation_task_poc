import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd

def read_flipkart_sitemap(url):
    try:
        response = requests.get(url)

        print("Inside read Flipkart site map")

        if response.status_code == 200:
            sitemap_xml = response.text
            return sitemap_xml
        else:
            print(f"Failed to fetch the sitemap. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error occurred while fetching the sitemap: {e}")
    return None

def extract_urls_from_sitemap(sitemap_xml, limit=10):
    urls = []
    try:
        root = ET.fromstring(sitemap_xml)
        for i, url_element in enumerate(root.findall(
                ".//{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")):
            url = url_element.text
            urls.append(url)
            if i + 1 >= limit:
                break
    except ET.ParseError as e:
        print(f"Error occurred while parsing the sitemap: {e}")
    return urls

def extract_product_details(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            product_title_element = soup.find("a", class_="s1Q9rs")
            product_price_element = soup.find("div", class_="_30jeq3")
            product_rating_element = soup.find("div", class_="_3LWZlK")

            product_title = product_title_element.text.strip() if product_title_element else "N/A"
            product_price = product_price_element.text.strip() if product_price_element else "N/A"
            product_rating = product_rating_element.text.strip() if product_rating_element else "N/A"

            product_details = {
                "url": url,
                "title": product_title,
                "price": product_price,
                "rating": product_rating,
                # Add more details as needed
            }
            return product_details
        else:
            print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error occurred while fetching the URL {url}: {e}")
    return None

if __name__ == "__main__":
    flipkart_sitemap_url = "https://www.flipkart.com/sitemap_s_store-browse.xml"
    sitemap_xml_data = read_flipkart_sitemap(flipkart_sitemap_url)

    if sitemap_xml_data:
        urls = extract_urls_from_sitemap(sitemap_xml_data)
        print("URLs in the sitemap:")
        product_details_list = []
        for url in urls:
            print(url)
            product_details = extract_product_details(url)
            if product_details:
                print("Product Details:")
                print(product_details)
                product_details_list.append(product_details)
            print("------------")

        # Export data to Excel
        df = pd.DataFrame(product_details_list)
        output_file = "product_details.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Data exported to {output_file}")
