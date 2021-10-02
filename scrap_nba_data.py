import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
from argparse import ArgumentParser
import os


### FUNCTIONS

def gets_html(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}):
    """ Lee un url y devuelve el código html """
    req = urllib.request.Request(url,headers=headers)
    return(urllib.request.urlopen(req).read().decode("utf-8"))

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

def create_basketball_reference_df(link, columns):
    # Scrap info
    html = gets_html(link)
    soup = BeautifulSoup(html)
    # Create free agents list 
    records_list = scrap_table(soup, table_class='table_container')
    # Create dataframe
    df = pd.DataFrame.from_records(records_list, columns=columns)
    return df

def create_salaries_df(year):
    html = gets_html(f"https://web.archive.org/web/{year}0101000000/http://www.basketball-reference.com/contracts/players.html")
    soup = BeautifulSoup(html)
    columns = soup.find_all('th', class_=['tooltip','poptip'])
    columns = [c.get_text() for c in columns]
    records_list = scrap_table(soup, table_class='table_container')
    salaries_df = pd.DataFrame.from_records(records_list, columns=columns[1:])
    if '' in salaries_df.columns:
        salaries_df.drop(columns='', inplace=True)
    return salaries_df

### PARSER

parser = ArgumentParser()
parser.add_argument('--year', type=int)
args = parser.parse_args()

YEAR = args.year


### ARGUMENTS

DIRECTORY = f'datasets/{YEAR}/'

FREE_AGENTS_LINK = f"https://www.basketball-reference.com/friv/free_agents.fcgi?year={YEAR}"
FREE_AGENTS_COLUMNS = ["player", "position", "age", "type", "old_team",
                       "stats", "ws", "new_team", "terms", "notes"]

STATS_LINK = f"https://www.basketball-reference.com/leagues/NBA_{YEAR}_per_game.html"
STATS_COLUMNS = ["player", "position", "age","team_id","g","gs","mp_per_g","fg_per_g",
"fga_per_g","fg_pct","fg3_per_g","fg3a_per_g","fg3_pct","fg2_per_g","fg2a_per_g",
"fg2_pct","efg_pct","ft_per_g","fta_per_g","ft_pct","orb_per_g","drb_per_g","trb_per_g",
"ast_per_g","stl_per_g","blk_per_g","tov_per_g","pf_per_g","pts_per_g"]
NUM_STATS_COLUMNS = [col for col in STATS_COLUMNS if col not in ('"player", "position","team_id"')]


ADVANCED_STATS_LINK = f"https://www.basketball-reference.com/leagues/NBA_{YEAR}_advanced.html"
ADVANCED_STATS_COLUMNS =["player","position","age","team_id","g","mp","per","ts_pct","fg3a_per_fga_pct",
"fta_per_fga_pct","orb_pct","drb_pct","trb_pct","ast_pct","stl_pct","blk_pct","tov_pct","usg_pct",
"ws-dum","ows","dws","ws","ws_per_48","bpm-dum","obpm","dbpm","bpm","vorp"] 
NUM_ADVANCED_STATS_COLUMNS = [col for col in ADVANCED_STATS_COLUMNS if col not in ('"player", "position","team_id"')]

def main():
    # Free agents
    
    free_agents = create_basketball_reference_df(FREE_AGENTS_LINK, FREE_AGENTS_COLUMNS)
    free_agents = free_agents[free_agents.player.notnull()]
    # Stats per game
    stats = create_basketball_reference_df(STATS_LINK, STATS_COLUMNS)
    stats = stats[stats.player.notnull()]
    stats[NUM_STATS_COLUMNS] = stats[NUM_STATS_COLUMNS].apply(pd.to_numeric)

    # Advanced stats
    advanced_stats = create_basketball_reference_df(ADVANCED_STATS_LINK, ADVANCED_STATS_COLUMNS)
    advanced_stats = advanced_stats[advanced_stats.player.notnull()]
    advanced_stats[NUM_ADVANCED_STATS_COLUMNS] = advanced_stats[NUM_ADVANCED_STATS_COLUMNS].apply(pd.to_numeric)
    
    # Salaries
    salaries = create_salaries_df(YEAR)
    salaries = salaries[salaries.Player.notnull()]
    NUM_SALARIES_COLUMNS = [c for c in salaries.columns if c not in ('Player', 'Tm', 'Signed Using')]
    salaries[NUM_SALARIES_COLUMNS] = salaries[NUM_SALARIES_COLUMNS]\
                                        .apply(lambda x: x.str.replace('\$|,','')).apply(pd.to_numeric)
    
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)
    
    free_agents.to_csv(DIRECTORY + 'free_agents.csv', index=False)
    stats.to_csv(DIRECTORY + 'stats.csv', index=False)
    advanced_stats.to_csv(DIRECTORY + 'advanced_stats.csv', index=False)
    salaries.to_csv(DIRECTORY + 'salaries.csv', index=False)
    
    
if __name__ == "__main__":
    main()
    
    