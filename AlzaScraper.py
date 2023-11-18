import json
import pandas as pd
import requests
from datetime import datetime
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from tutorial.tutorial.spiders.alza_spider import AlzaProductSpider


class AlzaProductParametersExtractor:
    """ Class for extracting product parameters from the Alza.cz website."""

    def __init__(self):
        """ Initializes the class with file names for storing product links and data. """
        self.product_file = 'products.txt'
        self.data_file = 'data.json'

    def extract_and_save_products(self, category_url: str, number_of_pages: int):
        """ Extracts product links from a given category and saves them to a file. """
        process = CrawlerProcess(get_project_settings())
        process.crawl(AlzaProductSpider,
                      target=category_url,
                      number_of_pages=number_of_pages,
                      file_name=self.product_file)
        process.start()
        # product_links = self.get_products(category_url, number_of_pages)
        # with open(self.product_file, 'w') as file:
        #     for link in product_links:
        #         file.write(link + '\n')

    def process_products(self):
        """ Processes each product, extracts parameters, and saves them to a data file. """
        with open(self.data_file, 'a') as data_file, open(self.product_file, 'r') as file:
            lines = file.readlines()
            for idx, line in enumerate(lines, 1):
                product_url = line.strip()
                print(f"Processing product {idx}/{len(lines)}: {product_url}")
                parameters = self.get_parameters(product_url)
                json.dump(parameters, data_file)
                data_file.write('\n')

    def convert_json_to_csv(self):
        """ Converts the JSON data file to a CSV format. """
        df = pd.read_json(self.data_file, lines=True)
        df_filtered = df.drop_duplicates(subset=[col for col in df.columns if col != 'Scraping time'])
        df_filtered.to_csv('data.csv', index=False, sep=';')

    # def get_products(self, category_url: str, number_of_pages: int) -> list:
    #     """ Retrieves product links from specified pages of a category. """
    #     all_links = []
    #     links = [category_url + f"#pg={x}" for x in range(1, number_of_pages + 1)]
    #     for link in links:
    #         try:
    #             product_urls = self.get_product_url_list(link)
    #             all_links.extend(product_urls)
    #         except Exception as e:
    #             print(f"Error fetching page {link}: {e}")
    #     return all_links

    def get_parameters(self, product_url: str) -> dict:
        """ Extracts product parameters from a given product URL. """
        row_elements, price, availability = self._extract_rows_and_price(product_url)
        parameters = {
            "Scraping time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Link": product_url,
            "Price": price,
            "Availability": availability
        }

        for row in row_elements:
            name, value = self._extract_name_and_value(row)
            if name and value:
                parameters[name] = value

        return parameters

    # @staticmethod
    # def get_product_url_list(target_url: str) -> list:
    #     """ Extracts and returns a list of product URLs from the target page. """
    #     base_url = 'https://www.alza.cz'
    #     response = requests.get(target_url)
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     links = soup.find_all('a', class_='name browsinglink')
    #     return [base_url + link['href'] + "#parametry" for link in links]

    @staticmethod
    def _extract_rows_and_price(product_url: str) -> (list, str, str):
        """ Extracts detailed rows, price, and availability info from a product page. """
        response = requests.get(product_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('div', class_='row')
        price, availability = AlzaProductParametersExtractor._parse_price_and_availability(soup)
        return rows, price, availability

    @staticmethod
    def _parse_price_and_availability(soup):
        """ Parses and returns price and availability information from the soup object. """
        price_detail_block = soup.find('div', class_='price-detail')
        price = None
        if price_detail_block:
            price_span = price_detail_block.find('span', class_='price-box__price')
            if price_span:
                price = price_span.get_text(strip=True).replace('\xa0', ' ').replace(',', '').replace('-', '').strip()

        availability_span = soup.find('span', class_=lambda x: x and x.startswith('stcStock avlVal '))
        availability = availability_span.get_text(strip=True) if availability_span else "Unknown"
        return price, availability

    def _extract_name_and_value(self, row):
        filtered_elements = self._filtered_elements(row)
        name, value = "", ""
        for elem in filtered_elements:
            if "value" in elem["class"]:
                value = elem.get_text(strip=True)
            else:
                name = elem.get_text(strip=True)
        return name, value

    @staticmethod
    def _filtered_elements(row) -> list:
        result = []
        for class_name in ["name typeName first hasPopupInfo", "value", "name typeName first"]:
            elements = row.find_all(class_=class_name)
            for elem in elements:
                for unwanted in elem.find_all(class_="infoPopup infoDialog"):
                    unwanted.decompose()
                result.append(elem)
        return result
