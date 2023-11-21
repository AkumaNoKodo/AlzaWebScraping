import json
import os

import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from tutorial.tutorial.spiders.alza_spider import AlzaProductSpider


class AlzaProductParametersExtractor:
    """ Class for extracting product parameters from the Alza.cz website."""

    def __init__(self):
        """
        Initializes the AlzaProductParametersExtractor class.

        Sets up the filenames for storing product links and extracted data. The product
        links are stored in 'products.txt', and the extracted data is stored in 'data.json'.
        """
        self.product_file = 'products.txt'
        self.data_file = 'data.json'

    def extract_and_save_products(self, category_url: str, number_of_pages: int) -> None:
        """
        Extracts product links from a specified category URL and saves them into a file.

        This method uses a Scrapy CrawlerProcess to crawl a given category URL for a specified
        number of pages. It saves the extracted product links to a text file.

        Args:
            category_url (str): The URL of the category to scrape.
            number_of_pages (int): The number of pages to crawl in the category.
        """
        process = CrawlerProcess(get_project_settings())
        process.crawl(AlzaProductSpider,
                      target=category_url,
                      number_of_pages=number_of_pages,
                      out_product_file_name=self.product_file)
        process.start()

    def process_products(self) -> None:
        """
        Processes each product URL, extracts parameters, and saves them to a JSON file.

        Reads product URLs from a file, extracts parameters for each product, and appends
        them to a JSON file. Each product's parameters are extracted using the 'get_parameters'
        method and stored in a dictionary format.
        """
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w'):
                pass

        if not os.path.exists(self.product_file):
            with open(self.product_file, 'w'):
                pass

        with open(self.data_file, 'a') as data_file, open(self.product_file, 'r') as file:
            lines = file.readlines()
            for idx, line in enumerate(lines, 1):
                product_url = line.strip()
                print(f"Processing product {idx}/{len(lines)}: {product_url}")
                parameters = self._get_parameters(product_url)
                json.dump(parameters, data_file)
                data_file.write('\n')

    def convert_json_to_csv(self) -> None:
        """
        Converts the JSON data file into a CSV format.

        Reads the JSON file containing product data, filters out duplicate entries based on all
        columns except 'Scraping time', and saves the result into a CSV file named 'data.csv'.
        """
        df = pd.read_json(self.data_file, lines=True)
        df_filtered = df.drop_duplicates(subset=[col for col in df.columns if col != 'Scraping time'])
        df_filtered.to_csv('data.csv', index=False, sep=';')

    def _get_parameters(self, product_url: str) -> dict:
        """
        Extracts product parameters from a given product URL.

        Visits the product page and extracts various parameters like price, availability,
        and other product-specific attributes. The method organizes these parameters into
        a dictionary.

        Args:
            product_url (str): The URL of the product page to extract data from.

        Returns:
            dict: A dictionary containing extracted product parameters.
        """
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

    @staticmethod
    def _extract_rows_and_price(product_url: str) -> tuple[list[Tag], str, str]:
        """
        Extracts detailed rows, price, and availability information from a product page.

        This method sends a request to the product URL and parses the HTML response to
        extract product details, price, and availability information.

        Args:
            product_url (str): The URL of the product page.

        Returns:
            tuple: A tuple containing a list of detail rows, the price, and the availability
                   information of the product.
        """
        response = requests.get(product_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('div', class_='row')
        price, availability = AlzaProductParametersExtractor._parse_price_and_availability(soup)
        return rows, price, availability

    @staticmethod
    def _parse_price_and_availability(soup: BeautifulSoup) -> tuple[str, str]:
        """
        Parses and returns price and availability information from a BeautifulSoup object.

        Extracts the price and availability details from the parsed HTML content of the product
        page.

        Args:
            soup (bs4.BeautifulSoup): A BeautifulSoup object of the product page.

        Returns:
            tuple: A tuple containing the extracted price and availability information.
        """
        price_detail_block = soup.find('div', class_='price-detail')
        price = None
        if price_detail_block:
            price_span = price_detail_block.find('span', class_='price-box__price')
            if price_span:
                price = price_span.get_text(strip=True).replace('\xa0', ' ').replace(',', '').replace('-', '').strip()

        availability_span = soup.find('span', class_=lambda x: x and x.startswith('stcStock avlVal '))
        availability = availability_span.get_text(strip=True) if availability_span else "Unknown"
        return price, availability

    def _extract_name_and_value(self, row: Tag) -> tuple[str, str]:
        """
        Filters and returns elements of interest from a given row.

        Iterates through specified CSS classes to find elements within the row and removes
        any unwanted elements like popups or dialogs before returning them.

        Args:
            row (bs4.element.Tag): A BeautifulSoup element representing a row in the HTML structure.

        Returns:
            list: A list of BeautifulSoup elements after filtering out unwanted parts.
        """
        filtered_elements = self._filtered_elements(row)
        name, value = "", ""
        for elem in filtered_elements:
            if "value" in elem["class"]:
                value = elem.get_text(strip=True)
            else:
                name = elem.get_text(strip=True)
        return name, value

    @staticmethod
    def _filtered_elements(row: Tag) -> list[Tag]:
        """
        Filters and returns elements of interest from a given row.

        Iterates through specified CSS classes to find elements within the row and removes
        any unwanted elements like popups or dialogs before returning them.

        Args:
            row (bs4.element.Tag): A BeautifulSoup element representing a row in the HTML structure.

        Returns:
            list: A list of BeautifulSoup elements after filtering out unwanted parts.
        """
        filtered_elements = []
        for class_name in ["name typeName first hasPopupInfo", "value", "name typeName first"]:
            elements = row.find_all(class_=class_name)
            for elem in elements:
                for unwanted in elem.find_all(class_="infoPopup infoDialog"):
                    unwanted.decompose()
                filtered_elements.append(elem)
        return filtered_elements
