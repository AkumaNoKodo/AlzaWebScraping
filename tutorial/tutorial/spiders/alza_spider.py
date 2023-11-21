import os

import scrapy


class AlzaProductSpider(scrapy.Spider):
    """
    Spider for crawling the Alza.cz website to extract product URLs.

    Attributes:
        name (str): Name of the spider.
        base_url (str): Base URL of the Alza.cz website.
        product_file (str): File path where product URLs will be saved.
    """

    name = "alza_products"
    base_url = 'https://www.alza.cz'

    def __init__(self, target: str, number_of_pages: int, out_product_file_name: str, *args, **kwargs):
        """
        Initializes the spider with the target URL, number of pages, and output file name.

        Args:
            target (str): The target category URL.
            number_of_pages (int): Number of pages to scrape in the category.
            out_product_file_name (str): File path to save the extracted product URLs.
        """
        super(AlzaProductSpider, self).__init__(*args, **kwargs)
        self.product_file = out_product_file_name
        self.start_urls = [f"{target}-p{page}.htm" for page in range(1, number_of_pages + 1)]

    def parse(self, response) -> None:
        """
        Parses the product page and extracts product URLs.

        Args:
            response (scrapy.http.Response): Response object from Scrapy.

        Writes each extracted product URL to the specified file.
        """
        links = response.css('a.name.browsinglink::attr(href)').getall()
        if not os.path.exists(self.product_file):
            with open(self.product_file, 'w'):
                pass

        with open(self.product_file, 'a') as file:
            for link in links:
                product_url = self.base_url + link + "#parametry"
                file.write(product_url + '\n')
