import pandas as pd
import numpy as np

def preprocess_economic_data():
    data = pd.read_excel("data/eu27_economic_data.xlsx")
    
    # remove unnecessary data
    data = data[data['Unit'].isin(['(1000 EUR)', 'Mrd ECU/EUR', '1000 persons'])]
    data = data[~data['Country'].str.contains('Euro')]
    
    # drop unnecessary columns
    data.drop(columns=['Unit/Description', 'Unit', 'Year'], inplace=True)
    
    # tidy data to get 'index' - 'variable' - 'value' format
    data = pd.melt(data, id_vars=['Variable', 'Country'], var_name='Year', value_name='Value')

    return data

def preprocess_consumption_data():
    data = pd.read_csv('data\eu27_food_consumption.csv')
    
    # summarize apparent use and yield data
    data['Apparent use'] = np.where(data['Apparent use (THOUSAND TONNES)'] > 0, data['Apparent use (THOUSAND TONNES)'], data['Apparent use (THOUSAND HECTOLITRES)'])
    data['Apparent use per capita'] = np.where(data['Apparent per capita use (KG/PERSON)'] > 0, data['Apparent per capita use (KG/PERSON)'], data['Apparent per capita use (LITRES/PERSON)'])
    data['Yield'] = np.where(data['Yield (crops) (TONNE/HA)'] > 0, data['Yield (crops) (TONNE/HA)'], data['Yield (HECTOLITRES PER HECTARE)'])
    
    # drop 'old' columns
    data.drop(columns=['Apparent use (THOUSAND TONNES)', 'Apparent use (THOUSAND HECTOLITRES)',
                       'Apparent per capita use (KG/PERSON)', 'Apparent per capita use (LITRES/PERSON)',
                       'Yield (crops) (TONNE/HA)', 'Yield (HECTOLITRES PER HECTARE)'], inplace=True)
    
    data.rename(columns={'Harvested area (THOUSAND HECTARES)': 'Harvested area', 'Self sufficiency (RATIO)': 'Self sufficiency'}, inplace=True)

    # tidy data to get 'index' - 'variable' - 'value' format
    data = pd.melt(data, id_vars=['Country', 'Commodity', 'Year'], var_name='Variable', value_name='Value')
    
    # drop rows with missing values
    data = data[data.groupby(by=['Variable','Commodity'])['Value'].transform('count') > 0]
    
    return data

def preprocess_full_data(data):
    data['Variable'] = data['Variable'].replace({'Apparent use': 'consumption', 
                                             'Apparent use per capita': 'consumption pP', 
                                             'GDP per head, at current prices (HVGDP)': 'GDP pP', 
                                             'GDP, at current prices (UVGD)': 'GDP', 
                                             'Private FCE, at current prices (UCPH)': 'FCE', 
                                             'Wage and salary earners (Persons),Total economy, domestic (NWTD)': 'salary earners'
                                             })

    data['Commodity'] = data['Commodity'].replace({'APPLES': 'apples',
                                               'BARLEY': 'barley',
                                               'OATS': 'oats',
                                               'SOYA BEAN': 'soy',
                                               'SUNFLOWER': 'sunflower',
                                               'WINE': 'wine',
                                               'BUTTER (80-90% FAT)': 'butter',
                                               'DRINKING MILK': 'milk'
                                               })
    
    data['Country'] = data['Country'].replace({'Czechia': 'Czech Republic'})
    
    region = {'Austria': 'Central Europe', 'Belgium': 'Western Europe', 'Bulgaria': 'South Eastern Europe', 'Croatia': 'South Eastern Europe',
            'Cyprus': 'Southern Europe', 'Czech Republic': 'Central Europe', 'Denmark': 'Northern Europe', 'Estonia': 'Northern Europe',
            'Finland': 'Northern Europe', 'France': 'Western Europe', 'Germany': 'Central Europe', 'Greece': 'Southern Europe',
            'Hungary': 'Central Europe', 'Ireland': 'Western Europe', 'Italy': 'Southern Europe', 'Latvia': 'Northern Europe',
            'Lithuania': 'Northern Europe', 'Luxembourg': 'Western Europe', 'Malta': 'Southern Europe', 'Netherlands': 'Western Europe',
            'Poland': 'Central Europe', 'Portugal': 'Southern Europe', 'Romania': 'South Eastern Europe', 'Slovakia': 'Central Europe',
            'Slovenia': 'Central Europe', 'Spain': 'Southern Europe', 'Sweden': 'Northern Europe'
        }
    data['Region'] = data['Country'].map(region)
    
    return data

 
if __name__ == '__main__':
    consumption_data = preprocess_consumption_data()
    economic_data = preprocess_economic_data()
    
    full_data = pd.concat([consumption_data, economic_data])
    full_data = preprocess_full_data(full_data)
    full_data.to_csv('app/full_data.csv', index=False)