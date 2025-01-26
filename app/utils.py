import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


world = gpd.read_file('app/europe.geojson')
data = pd.read_csv('app/full_data.csv')

def plot_map(years, commodity, var='consumption pP'):
    data_ = data[(data['Variable'] == var) & (data['Year'] == years[1])]
    data_ = data_[(data_['Commodity'] == commodity)]

    merged = world.merge(data_, left_on='NAME', right_on='Country')

    # Define bins and labels
    m = merged['Value'].max()
    bins = [0, 0.2*m, 0.4*m, 0.6*m, 0.8*m, m]
    labels = [f"< {round(0.2*m, 1)}", f"{round(0.2*m, 1)} - {round(0.4*m, 1)}", 
              f"{round(0.4*m, 1)} - {round(0.6*m, 1)}", f"{round(0.6*m, 1)} - {round(0.8*m, 1)}", 
              f"> {round(0.8*m, 1)}"]
    merged['ValueClass'] = pd.cut(merged['Value'], bins=bins, labels=labels)

    fig = px.choropleth(
        merged,
        geojson=world,
        locations='NAME',
        featureidkey='properties.NAME',
        color='ValueClass',
        color_discrete_sequence=['#59A1E3', '#A8CFEA', '#D4C6BA', '#D5B08D', '#DC9554'],
        labels={'ValueClass': var},
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Reduced top margin
        plot_bgcolor='#fefae0',
        height=350,
        legend=dict(
            title=dict(text=var, font=dict(color='black')),
            orientation="v",
            yanchor="top",
            y=0.8,
            xanchor="left",
            x=0.05,
            bgcolor="rgba(255, 255, 255, 0.7)",
            font=dict(color='black')
        )
    )
    return fig



def ec_con_lines(region, years, commodity, var1='GDP pP', var2='consumption pP'):
    data1 = data[(data['Variable'] == var1) & (data['Region'] == region) & 
                 (data['Year'] >= years[0]) & (data['Year'] <= years[1])]
    data1 = data1.pivot_table(index='Year', columns='Country', values='Value', aggfunc='mean')
    
    data2 = data[(data['Variable'] == var2) & (data['Region'] == region) & 
                 (data['Year'] >= years[0]) & (data['Year'] <= years[1])]
    data2 = data2[(data2['Commodity'] == commodity)]
    data2 = data2.pivot_table(index='Year', columns='Country', values='Value', aggfunc='mean')
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    
    # Create a color map for countries
    color_map = {country: color for country, color in zip(data1.columns, px.colors.qualitative.Plotly)}
    
    for country in data1.columns:
        fig.add_trace(go.Scatter(x=data1.index, y=data1[country], mode='lines+markers', 
                                 name=country, line=dict(color=color_map[country]), legendgroup=country), row=1, col=1)
    
    for country in data2.columns:
        fig.add_trace(go.Scatter(x=data2.index, y=data2[country], mode='lines+markers', 
                                 name=country, line=dict(color=color_map[country]), 
                                 showlegend=False, legendgroup=country), row=2, col=1)
    
    fig.update_layout(
        plot_bgcolor='#fefae0', 
        height=700, 
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    fig.update_xaxes(title_text='Year', row=2, col=1)
    fig.update_yaxes(title_text=var1, row=1, col=1)
    fig.update_yaxes(title_text=var2, row=2, col=1)
    
    return fig


def train_test_split(commodity, years):
    data_ = data[data['Variable'].isin(['consumption', 'GDP', 'FCE', 'salary earners'])]
    data_['Variable'] = np.where(data_['Variable'] == 'consumption', data_['Variable'] + "/" + data_['Commodity'], data_['Variable'])
    data_ = data_.pivot_table(index=['Country', 'Year'], columns='Variable', values='Value').reset_index()
    
    data_ = data_[['Country', 'Year', 'GDP', 'FCE', 'salary earners', f'consumption/{commodity}']]
    data_ = data_.dropna()

    train = data_[data_['Year'] < years[1]]
    test = data_[data_['Year'] == years[1]]

    X_train = train[['GDP', 'FCE', 'salary earners']]
    y_train = train[f'consumption/{commodity}']
    X_test = test[['GDP', 'FCE', 'salary earners']]
    y_test = test[f'consumption/{commodity}']
    
    return X_train, y_train, X_test, y_test

class ConsumptionModel:
    def __init__(self, commodity, years):
        self.commodity = commodity
        self.model = LinearRegression()
        self.X_train, self.y_train, self.X_test, self.y_test = train_test_split(commodity, years)
        self.y_train_p = None
        self.y_test_p = None
        self.rmse = None
        self.rmse_rel = None
        self.r2 = None
        self.coeff_impact = None
        
        self.fit()
        self.predict()
        self.metrics()
    
    def fit(self):
        self.model.fit(self.X_train, self.y_train)
        sum = np.sum(np.abs(self.model.coef_))
        self.coeff_impact = self.model.coef_ / sum
    
    def predict(self):
        self.y_train_p = self.model.predict(self.X_train)
        self.y_test_p = self.model.predict(self.X_test)
    
    def metrics(self):
        if self.y_test_p is None:
            self.predict()
        mean = self.y_test.mean()
        self.rmse = np.sqrt(mean_squared_error(self.y_test, self.y_test_p))
        self.rmse_rel = self.rmse / mean
        self.r2 = self.model.score(self.X_test, self.y_test)
        
        return self.rmse, self.rmse_rel, self.r2
    
    def plot_scatter(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.y_train, y=self.y_train_p, mode='markers', name='Training Data',
                                marker=dict(color='#606c38', opacity=0.6)))

        fig.add_trace(go.Scatter(x=self.y_test, y=self.y_test_p, mode='markers', name='Validation Data',
                                marker=dict(color='#bc6c25', opacity=0.8)))

        fig.add_trace(go.Scatter(x=[self.y_train.min(), self.y_train.max()], y=[self.y_train.min(), self.y_train.max()],
                                mode='lines', name='Ideal', line=dict(color='#283618', dash='dash')))

        fig.update_layout(xaxis_title='Actual',
              yaxis_title='Predicted',
              legend_title=dict(text='Data Type', font=dict(color='black')),
              legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=0, bgcolor='rgba(255, 255, 255, 0.5)', font=dict(color='black')),
              plot_bgcolor='#fefae0',
              margin={"r":0,"t":0,"l":0,"b":0})
        
        return fig
        
    def plot_coefficients(self):
        palette = ['#606c38', '#bc6c25', '#283618']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=self.coeff_impact, y=self.X_train.columns, orientation='h',
                            marker=dict(color=palette), text=[round(coef, 2) for coef in self.coeff_impact],
                            textposition='outside'))

        fig.update_layout(xaxis_title='Coefficient Impact',
                          yaxis_title='Features',
                          plot_bgcolor='#fefae0',
                          height=200,
                          margin={"r":0,"t":0,"l":0,"b":0})        
        return fig