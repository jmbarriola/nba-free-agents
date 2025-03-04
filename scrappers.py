from bs4 import BeautifulSoup
import pandas as pd
import requests
import csv
import os
from io import StringIO
import tqdm

class FreeAgentTransactionScraper:
    def __init__(self, start_year:int):
        self.start_year = start_year
        self.end_year = start_year + 1
        self.base_url = "https://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=&Team=&BeginDate={}-05-01&EndDate={}-04-30&PlayerMovementChkBx=yes&Submit=Search&start={}"
        self.pages_list = []

    def get_max_page(self, soup):
        links = soup.find_all('a', href=True)
        links = [link.text for link in links]
        max_page = max([int(link) for link in links if link.isdigit()]) - 1
        return max_page

    def scrape_data(self):
        n = 0
        url = self.base_url.format(self.start_year, self.end_year, n)
        response = requests.get(url)
        html = response.content
        soup = BeautifulSoup(html, 'lxml')
        max_page = self.get_max_page(soup)
        print(f"Max page: {max_page}")

        for n in tqdm.tqdm(range(0, max_page * 25, 25)):
            url = self.base_url.format(self.start_year, self.end_year, n)
            response = requests.get(url)
            html = response.content
            soup = BeautifulSoup(html, 'lxml')
            table = soup.find('table', attrs={'class': 'datatable center'})
            table_str = str(table)

            # Use StringIO to read the string as if it were a file
            df = pd.read_html(StringIO(table_str), header=0)[0]
            free_agents = df[df['Notes'].str.contains('agen', na=False, case=False)]
            self.pages_list.append(free_agents)

    def get_free_agents(self):
        return pd.concat(self.pages_list).reset_index(drop=True)
    
    def save_to_csv(self, df:pd.DataFrame):
        filename = f'data/raw/free_agents/transactions/{self.start_year}_free_agents_transactions.csv'
        # if directory does not exist, create it
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False)


class FreeAgentScrapper:
    def __init__(self, year: int):
        self.year = year
        self.url = f"https://www.spotrac.com/nba/free-agents/_/year/{year}/"
    
    def scrape_data(self) -> dict:
        """
        Scrapes data from the specified URL and parses the HTML to extract player statistics.

        This method sends a GET request to the URL defined in the instance, parses the HTML content
        using BeautifulSoup, and extracts player statistics from the table based on the stats type
        ('per_game' or 'advanced'). The extracted data is stored in the instance variable `self.data`.

        Attributes:
            self.url (str): The URL to scrape data from.
            self.year (int): The year for which data is being scraped.
        """
        response = requests.get(self.url)
        # Use utf-8 encoding to handle special characters
        print(f"Scraping data for year {self.year} free agents", )
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        data_dict = {'signed': [], 'unsigned': []}

        for i, table in enumerate(tables):
            headers = table.find('thead').find_all('th')
            headers = [header.text.strip() for header in headers]
            rows = table.find('tbody').find_all('tr')
            rows = [row.find_all('td') for row in rows]
            data = []
            data.append(headers)
            for row in rows:
                player = [data.text.strip() for data in row]
                data.append(player)
            if i == 0:
                data_dict['signed'] = data
            else:
                data_dict['unsigned'] = data
            
        return data_dict   
        
    def save_to_csv(self, data_dict: dict):
        for key, value in data_dict.items():
            filename = f'data/raw/free_agents/{key}/{self.year}_{key}_free_agents.csv'
            # if directory does not exist, create it
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerows(value)  

class ContractScrapper:
    def __init__(self, site: str, year: int):
        self.site = site
        self.year = year
        SITE_DICT = {'sportrac': 'https://www.spotrac.com/nba/contracts/',
                     'basketball-reference': 'https://www.basketball-reference.com/contracts/players.html'}
        self.url = f"https://web.archive.org/web/{self.year}0401000000/{SITE_DICT[self.site]}"
    
    def scrape_data(self):
        """
        Scrapes data from the specified URL and parses the HTML to extract player statistics.

        This method sends a GET request to the URL defined in the instance, parses the HTML content
        using BeautifulSoup, and extracts player statistics from the table based on the stats type
        ('per_game' or 'advanced'). The extracted data is stored in the instance variable `self.data`.

        Attributes:
            self.url (str): The URL to scrape data from.
            self.year (int): The year for which data is being scraped.
            self.stats_type (str): The type of statistics to scrape ('per_game' or 'advanced').
            self.headers (list): The headers of the statistics table.
            self.data (list): The extracted player statistics.
        """

        response = requests.get(self.url)
        # Use utf-8 encoding to handle special characters
        print(f"Scraping data for year {self.year}", )
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        self.headers = table.find('thead').find_all('th')
        self.headers = [header.text for header in self.headers]
        rows = table.find('tbody').find_all('tr')
        rows = [row.find_all('td') for row in rows]
        self.data = []
        for row in rows:
            player = [data.text.strip() for data in row]
            self.data.append(player)


    def save_to_csv(self):
        filename = f'data/contracts/{self.site}/{self.year}_contracts.csv'
        # if directory does not exist, create it
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(self.headers)
            csvwriter.writerows(self.data)


class NBAStatsScraper:
    """
    A class to scrape NBA data from Basketball Reference and save it to a CSV file.
    Attributes:
    -----------
    year : int
        The year for which the data is to be scraped.
    stats_type : str
        The type of stats to scrape (e.g., 'per_game', 'advanced').
    headers : list
        The headers of the table containing the stats.
    data : list
        The data scraped from the table.
    url : str
        The URL of the page to scrape data from.
    Methods:
    --------
    scrape_data():
        Scrapes the data from the specified URL and stores it in the `data` attribute.
    save_to_csv():
        Saves the scraped data to a CSV file.
    """

    def __init__(self, year, stats_type):
        self.stats_type = stats_type
        self.year = year
        self.headers = []
        self.data = []
        self.url = f"https://www.basketball-reference.com/leagues/NBA_{year}_{stats_type}.html"

        
    def scrape_data(self):
        """
        Scrapes data from the specified URL and parses the HTML to extract player statistics.

        This method sends a GET request to the URL defined in the instance, parses the HTML content
        using BeautifulSoup, and extracts player statistics from the table based on the stats type
        ('per_game' or 'advanced'). The extracted data is stored in the instance variable `self.data`.

        Attributes:
            self.url (str): The URL to scrape data from.
            self.year (int): The year for which data is being scraped.
            self.stats_type (str): The type of statistics to scrape ('per_game' or 'advanced').
            self.headers (list): The headers of the statistics table.
            self.data (list): The extracted player statistics.
        """

        response = requests.get(self.url)
        # Use utf-8 encoding to handle special characters
        print(f"Scraping data for year {self.year} {self.stats_type} stats", )
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        d = {'per_game': 'per_game_stats', 'advanced': 'advanced'}
        table = soup.find('table', {'id': d[self.stats_type]})
        self.headers = table.find('thead').find_all('th')
        self.headers = [header.text for header in self.headers]
        rows = table.find('tbody').find_all('tr')
        rows = [row.find_all('td') for row in rows]
        self.data = []
        for row in rows:
            player = [data.text for data in row]
            self.data.append(player)

    def save_to_csv(self):
        filename = f'data/{self.stats_type}/{self.year}_stats.csv'
        # if directory does not exist, create it
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(self.headers[1::])
            csvwriter.writerows(self.data)
