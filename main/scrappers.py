import urllib.request
from bs4 import BeautifulSoup
import pandas as pd

class Scrapper:
    def __init__(self, url: str):
        self.url = url

    def gets_html(self, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}):
        """Reads a URL and returns the HTML code."""
        req = urllib.request.Request(self.url, headers=headers)
        return urllib.request.urlopen(req).read().decode("utf-8")

class FreeAgentScrapper(Scrapper):
    def __init__(self, url: str, year: int):
        super().__init__(url)
        self.year = year
        f"https://web.archive.org/web/{self.year}0101000000/http://www.basketball-reference.com/contracts/players.html"

class ContractScrapper(Scrapper):
    def __init__(self, url: str, year: int):
        super().__init__(url)
        self.year = year

    def scrap_table(soup, table_class: str):
        # This function should scrape the table data from the soup object
        # and return it as a list of records. Here's a simple mock-up:
        table = soup.find('table', class_=table_class)
        records = []
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                records.append([col.get_text(strip=True) for col in cols])
        return records

    def scrap_contracts(self):
        # Get the HTML content from the specified year using the Wayback Machine URL format
        html = self.gets_html()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract the table headers
        columns = soup.find_all('th', class_=['tooltip', 'poptip'])
        columns = [c.get_text() for c in columns]
        print(f"Columns: {columns}")
        
        # Scrape the table data
        records_list = scrap_table(soup, table_class='table_container')
        
        # Create a DataFrame from the records
        contracts_df = pd.DataFrame.from_records(records_list, columns=columns[1:])
        return contracts_df.dropna(how='all')




def scrap_table(soup, table_class):
    table = soup.find(class_=table_class)
    table_body = table.find('tbody')
    table_rows = table.find_all('tr') if table_body is None else table_body.find_all('tr')
    table_list = []
    for row in table_rows:
        row_list = []
        for cell in row.find_all('td'):
            # Get case value
            row_list.append(cell.get_text())
        table_list.append(row_list)
    return table_list