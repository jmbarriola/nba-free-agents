import pandas as pd
from argparse import ArgumentParser
import os

### FUNCTIONS

def clean_multiple_contracts_salaries(salaries, free_agents):
    multiple_contracts_players_list = salaries.groupby('Player').agg(n = ('Tm','count')).reset_index().query('n > 1').Player.to_list()
    multiple_contracts_free_agents = free_agents[free_agents.player.isin(multiple_contracts_players_list)][['player', 'new_team']]
    multiple_contracts_players = salaries[salaries.Player.isin(multiple_contracts_players_list)]
    multiple_contract_players = pd.merge(multiple_contracts_players, multiple_contracts_free_agents,
                                     left_on = ['Player', 'Tm'], right_on=['player', 'new_team'])\
                                .drop_duplicates(['Player', 'Tm'], keep='first').drop(columns=['player', 'new_team'])
    salaries = salaries[~salaries.Player.isin(multiple_contracts_players_list)]
    salaries = pd.concat([salaries, multiple_contract_players], axis=0)
    return salaries


### PARSER

parser = ArgumentParser()
parser.add_argument('--year', type=int)
args = parser.parse_args()

YEAR = args.year


### ARGUMENTS

INPUT_DIRECTORY = f'datasets/{YEAR}/'


def create_salaries_summary_df(salaries):
    melted_salaries = pd.melt(salaries,id_vars=['Player', 'Tm'],
                             value_vars=[c for c in salaries.columns if c.startswith('20')],
                             value_name='salary').dropna()
    salaries_summary = melted_salaries.groupby(['Player', 'Tm']).agg(mean_salary=('salary', 'mean'),
                                                              full_contract=('salary', 'sum'),
                                                              first_year_salary=('salary', 'first')).reset_index()
    return salaries_summary

def main():
    free_agents = pd.read_csv(INPUT_DIRECTORY + 'free_agents.csv')
    salaries = pd.read_csv(f'datasets/{YEAR+1}/' + 'salaries.csv')
    if YEAR <= 2015:
        free_agents.columns = [c.lower() for c in free_agents.columns]
        free_agents.rename(columns={'ntm':'new_team'}, inplace=True)

    free_agents = free_agents[['player', 'terms', 'new_team']] 
    print(f"There are {free_agents.shape[0]} free agents")

    salaries = clean_multiple_contracts_salaries(salaries, free_agents)
    salaries_summary = create_salaries_summary_df(salaries)
    free_agents_salary = pd.merge(free_agents, salaries_summary, how='left', left_on='player', right_on='Player')
    free_agents_salary = free_agents_salary[~free_agents_salary.mean_salary.isna()][['player','mean_salary', 'full_contract', 'first_year_salary']]
    free_agents_salary['free_agency_year'] = YEAR 

    print(f"There are {free_agents_salary.shape[0]} free agents with contract information")
    
    if not os.path.exists(INPUT_DIRECTORY):
        os.makedirs(INPUT_DIRECTORY)
    
    free_agents_salary.to_csv(INPUT_DIRECTORY + f'free_agents_salaries_{YEAR}.csv', index=False)
    
if __name__ == "__main__":
    main()