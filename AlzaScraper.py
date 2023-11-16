import json
import pandas as pd
import requests
from bs4 import BeautifulSoup, ResultSet
from datetime import datetime


class AlzaProductParametersExtractor:
    def __init__(self):
        self.product_file = 'products.txt'
        self.data_file = 'data.json'

    def extract_and_save_products(self, category_url: str, number_of_pages: int):
        product_links = self.get_products(category_url, number_of_pages)
        with open(self.product_file, 'w') as file:
            for link in product_links:
                file.write(link + '\n')

    def process_products(self):
        with open(self.data_file, 'a') as data_file, open(self.product_file, 'r') as file:
            lines = file.readlines()
            total = len(lines)
            for idx, line in enumerate(lines, 1):
                product_url = line.strip()
                print(f"Processing product {idx}/{total}: {product_url}")
                parameters = self.get_parameters(product_url)
                json.dump(parameters, data_file)
                data_file.write('\n')

    def process_existing_products(self):
        with open(self.data_file, 'a') as data_file, open(self.product_file, 'r+') as file:
            lines = file.readlines()
            file.seek(0)
            file.truncate()
            total = len(lines)
            for idx, line in enumerate(lines, 1):
                product_url = line.strip()
                print(f"Processing existing product {idx}/{total}: {product_url}")
                parameters = self.get_parameters(product_url)
                json.dump(parameters, data_file)
                data_file.write('\n')

    def convert_json_to_csv(self):
        df = pd.read_json(self.data_file, lines=True)
        df.to_csv('data.csv', index=False, sep=";")

    def get_products(self, category_url: str, number_of_pages: int) -> list:
        all_links = []
        for x in range(1, number_of_pages + 1):
            url = self.change_page(category_url, x)
            print(f"Fetching page {x}/{number_of_pages}: {url}")
            try:
                full_url = self.get_product_url_list(url)
                if not full_url:
                    continue
            except Exception as e:
                print(f"Error fetching page {x}: {e}")
                continue
            all_links.extend(full_url)
        return all_links

    def get_parameters(self, product_url: str) -> dict:
        row_elements, price, availability_text = self._extract_rows_and_price(product_url)
        parameters = {"Scraping time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      "Link": product_url,
                      "Price": price,
                      "Availability": availability_text}

        for row in row_elements:
            filtered_elements = self._filtered_elements(row)
            name, value = self._extract_name_and_value(filtered_elements)
            if name and value:
                parameters[name] = value

        return parameters

    @staticmethod
    def change_page(url: str, number: int) -> str:
        param = url.split("&")

        for i, cast in enumerate(param):
            if "pg=" in cast:
                param[i] = f"pg={number}"
                break
        new_url = "&".join(param)
        return new_url

    @staticmethod
    def get_product_url_list(target_url: str):
        base_url = 'https://www.alza.cz'
        response = requests.get(target_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', class_='name browsinglink')
        return [base_url + link['href'] + "#parametry" for link in links]

    @staticmethod
    def _extract_rows_and_price(product_url: str) -> (ResultSet, str, str):
        response = requests.get(product_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('div', class_='row')

        price_detail_block = soup.find('div', class_='price-detail')
        price = None
        if price_detail_block:
            price_span = price_detail_block.find('span', class_='price-box__price')
            if price_span:
                price_text = price_span.get_text(strip=True)
                price = price_text.replace('\xa0', ' ').replace(',', '').replace('-', '').strip()

        availability_span = soup.find('span', class_=lambda x: x and x.startswith('stcStock avlVal '))
        availability_text = availability_span.get_text(strip=True)
        return rows, price, availability_text

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

    @staticmethod
    def _extract_name_and_value(filtered_elements):
        name, value = "", ""
        for elem in filtered_elements:
            if "value" in elem["class"]:
                value = elem.get_text(strip=True)
            else:
                name = elem.get_text(strip=True)
        return name, value
