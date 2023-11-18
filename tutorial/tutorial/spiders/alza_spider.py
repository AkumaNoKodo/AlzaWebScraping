import json
from datetime import datetime
import scrapy
from scrapy.http import Response


class AlzaProductSpider(scrapy.Spider):
    name = "alza_products"
    base_url = 'https://www.alza.cz'

    def __init__(self, target: str, number_of_pages: int, file_name: str, *args, **kwargs):
        super(AlzaProductSpider, self).__init__(*args, **kwargs)
        self.product_file = file_name
        self.target = target
        self.number_of_pages = number_of_pages

    def start_requests(self):
        for page in range(1, self.number_of_pages + 1):
            yield scrapy.Request(url=f"{self.target}-p{page}.htm", callback=self.parse)

    def parse(self, response):
        links = response.css('a.name.browsinglink::attr(href)').getall()
        with open(self.product_file, 'a') as file:
            for link in links:
                product_url = self.base_url + link + "#parametry"
                file.write(product_url + '\n')
