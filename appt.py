from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)

# Load and preprocess data
def load_data():
    df = pd.read_csv('SeoulBikeData.csv', encoding='unicode_escape')
    
    # Data cleaning
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    df['Month'] = df['Date'].dt.month
    df['Weekday'] = df['Date'].dt.weekday  # Monday=0, Sunday=6
    df['DayType'] = df['Weekday'].apply(lambda x: 'Weekend' if x >= 5 else 'Weekday')
    df['Year'] = df['Date'].dt.year
    
    return df

# Process data with filters
def process_data(df, date_range=None, temp_range=None):
    # Apply filters
    if date_range:
        df = df[(df['Date'] >= pd.to_datetime(date_range['start'])) & 
                (df['Date'] <= pd.to_datetime(date_range['end']))]
    
    if temp_range:
        df = df[(df['Temperature(°C)'] >= temp_range['min']) & 
                (df['Temperature(°C)'] <= temp_range['max'])]
    
    # Hourly averages
    hourly = df.groupby('Hour')['Rented Bike Count'].mean().reset_index()
    
    # Seasonal averages
    seasonal = df.groupby('Seasons')['Rented Bike Count'].mean().reset_index()
    
    # Temperature ranges
    temp_bins = [-20, 0, 10, 20, 30, 40]
    temp_labels = ['<0°C', '0-10°C', '10-20°C', '20-30°C', '>30°C']
    df['TempRange'] = pd.cut(df['Temperature(°C)'], bins=temp_bins, labels=temp_labels)
    temp_data = df.groupby('TempRange')['Rented Bike Count'].mean().reset_index()
    
    # Weekday vs weekend
    weekday_data = df.groupby('DayType')['Rented Bike Count'].mean().reset_index()
    
    # Daily trends
    daily = df.groupby('Date')['Rented Bike Count'].sum().reset_index()
    
    # Weather correlation
    weather_corr = df[['Rented Bike Count', 'Temperature(°C)', 'Humidity(%)', 
                      'Wind speed (m/s)', 'Visibility (10m)']].corr()
    
    return {
        'hourly': hourly.to_dict(orient='records'),
        'seasonal': seasonal.to_dict(orient='records'),
        'temperature': temp_data.to_dict(orient='records'),
        'weekday': weekday_data.to_dict(orient='records'),
        'daily': daily.to_dict(orient='records'),
        'weather_corr': weather_corr.to_dict(),
        'summary': {
            'total_records': len(df),
            'date_range': {
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d')
            },
            'temp_range': {
                'min': df['Temperature(°C)'].min(),
                'max': df['Temperature(°C)'].max()
            },
            'avg_rentals': df['Rented Bike Count'].mean(),
            'avg_temp': df['Temperature(°C)'].mean()
        }
    }

# Load data once when app starts
df = load_data()
min_date = df['Date'].min().strftime('%Y-%m-%d')
max_date = df['Date'].max().strftime('%Y-%m-%d')
min_temp = df['Temperature(°C)'].min()
max_temp = df['Temperature(°C)'].max()

@app.route('/')
def dashboard():
    initial_data = process_data(df)
    return render_template('dashboard.html', 
                         data=initial_data,
                         min_date=min_date,
                         max_date=max_date,
                         min_temp=min_temp,
                         max_temp=max_temp)

@app.route('/api/filter', methods=['POST'])
def filter_data():
    filters = request.json
    filtered_data = process_data(df, 
                               date_range=filters.get('date_range'),
                               temp_range=filters.get('temp_range'))
    return jsonify(filtered_data)

@app.route('/api/initial_data')
def initial_data():
    initial_data = process_data(df)
    return jsonify(initial_data)

if __name__ == '__main__':
    app.run(debug=True)