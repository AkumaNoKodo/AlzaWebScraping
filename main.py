from AlzaScraper import AlzaProductParametersExtractor


if __name__ == "__main__":
    category_url = "https://www.alza.cz/lednicky/18852759"
    extractor = AlzaProductParametersExtractor()
    extractor.extract_and_save_products(category_url, 48)
    extractor.process_products()
    extractor.convert_json_to_csv()
