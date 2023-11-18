from AlzaScraper import AlzaProductParametersExtractor


if __name__ == "__main__":
    category_url = "https://www.alza.cz/lcd-monitory/18842948"
    extractor = AlzaProductParametersExtractor()
    extractor.extract_and_save_products(category_url, 74)
    extractor.process_products()
    extractor.convert_json_to_csv()
