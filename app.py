import os
import time
import math
import random
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
import joblib
from agentic_ai import agentic_ai, DEFAULT_LOADS

app = Flask(__name__, static_folder='static', static_url_path='')

# Load Machine Learning Models
MODELS_DIR = 'models'
rf_model = None
gb_model = None
metadata = None

def load_ai_models():
    global rf_model, gb_model, metadata
    rf_path = os.path.join(MODELS_DIR, 'solar_rf_model.pkl')
    gb_path = os.path.join(MODELS_DIR, 'solar_gb_model.pkl')
    meta_path = os.path.join(MODELS_DIR, 'model_metadata.pkl')
    
    if os.path.exists(rf_path) and os.path.exists(gb_path) and os.path.exists(meta_path):
        rf_model = joblib.load(rf_path)
        gb_model = joblib.load(gb_path)
        metadata = joblib.load(meta_path)
        print("[SUCCESS] Loaded Random Forest & Gradient Boosting models into memory.")
    else:
        print("[WARNING] Trained models not found! Run train_model.py first.")

load_ai_models()

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'online',
        'system_name': 'SolarIQ AI Renewable Intelligence',
        'models_loaded': rf_model is not None and gb_model is not None,
        'metadata': metadata
    })

@app.route('/api/predict', methods=['POST'])
def predict_power():
    try:
        data = request.json or {}
        
        # Weather inputs
        temp = float(data.get('temperature', 28.0))
        irradiance = float(data.get('solar_irradiance', 650.0))
        cloud = float(data.get('cloud_cover', 25.0))
        humidity = float(data.get('humidity', 55.0))
        wind = float(data.get('wind_speed', 4.5))
        rain = float(data.get('rainfall', 0.0))
        dust = float(data.get('dust_level', 2.0))
        hour = int(data.get('hour', 14))
        month = int(data.get('month', 8))
        model_choice = data.get('model_type', 'random_forest') # 'random_forest' or 'gradient_boosting'
        
        # Construct feature vector
        features = np.array([[temp, irradiance, cloud, humidity, wind, rain, dust, hour, month]])
        feature_cols = ['temperature', 'solar_irradiance', 'cloud_cover', 'humidity', 'wind_speed', 'rainfall', 'dust_level', 'hour', 'month']
        features_df = pd.DataFrame(features, columns=feature_cols)
        
        # Predict using selected model
        if model_choice == 'gradient_boosting' and gb_model:
            predicted_total = float(gb_model.predict(features_df)[0])
            active_model_name = "Gradient Boosting (GBDT)"
            metrics = metadata['gb_metrics'] if metadata else {}
        else:
            predicted_total = float(rf_model.predict(features_df)[0]) if rf_model else 0.0
            active_model_name = "Random Forest Regressor"
            metrics = metadata['rf_metrics'] if metadata else {}
            
        predicted_total = max(0.0, float(predicted_total))
        
        # Compute solar vs wind component estimation
        # Solar component logic
        if hour < 6 or hour > 18 or irradiance < 10:
            solar_comp = 0.0
        else:
            temp_loss = 1.0 - 0.004 * max(0.0, temp - 25.0)
            dust_loss = 1.0 - 0.015 * dust
            solar_comp = (irradiance / 1000.0) * 3000.0 * temp_loss * dust_loss
            solar_comp = max(0.0, min(solar_comp, predicted_total))
            
        wind_comp = max(0.0, predicted_total - solar_comp)
        
        return jsonify({
            'success': True,
            'model_used': active_model_name,
            'metrics': metrics,
            'predicted_total_watts': round(predicted_total, 2),
            'predicted_solar_watts': round(solar_comp, 2),
            'predicted_wind_watts': round(wind_comp, 2),
            'inputs': {
                'temperature': temp,
                'solar_irradiance': irradiance,
                'cloud_cover': cloud,
                'humidity': humidity,
                'wind_speed': wind,
                'rainfall': rain,
                'dust_level': dust,
                'hour': hour,
                'month': month
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/recommend', methods=['POST'])
def recommend_load_management():
    try:
        data = request.json or {}
        solar_w = float(data.get('predicted_solar_watts', 1800.0))
        wind_w = float(data.get('predicted_wind_watts', 400.0))
        weather_data = data.get('weather_data', {})
        loads_state = data.get('loads', DEFAULT_LOADS)
        battery_soc = float(data.get('battery_soc', 65.0))
        
        result = agentic_ai.evaluate_system(solar_w, wind_w, weather_data, loads_state, battery_soc)
        return jsonify({
            'success': True,
            'evaluation': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/weather/live', methods=['GET'])
def get_live_weather():
    lat = float(request.args.get('lat', 11.0168)) # Default Coimbatore, India
    lon = float(request.args.get('lon', 76.9558))
    
    # Simulate high-fidelity realistic weather based on coordinates and current hour
    current_hour = time.localtime().tm_hour
    current_month = time.localtime().tm_mon
    
    # Base diurnal calculation
    sun_factor = max(0.0, math.sin(math.pi * (current_hour - 6) / 12)) if 6 <= current_hour <= 18 else 0.0
    
    # Location hash seed for repeatability per location
    seed = int(abs(lat * 100 + lon * 10)) % 100
    random.seed(seed + current_hour)
    
    temp = round(26.0 + 6.0 * sun_factor + random.uniform(-2, 2), 1)
    irradiance = round(sun_factor * 950.0 * random.uniform(0.85, 1.05), 1)
    cloud = round(random.uniform(10, 45), 1)
    humidity = round(60.0 - 15.0 * sun_factor + random.uniform(-5, 5), 1)
    wind = round(random.uniform(2.5, 7.5), 1)
    rain = round(random.uniform(0, 2) if cloud > 70 else 0.0, 1)
    dust = round(random.uniform(1.0, 4.0), 1)
    
    location_name = f"Location ({lat:.2f}°, {lon:.2f}°)"
    if abs(lat - 11.01) < 0.5 and abs(lon - 76.95) < 0.5:
        location_name = "Coimbatore, TN, India"
    elif abs(lat - 13.08) < 0.5 and abs(lon - 80.27) < 0.5:
        location_name = "Chennai, TN, India"
    elif abs(lat - 12.97) < 0.5 and abs(lon - 77.59) < 0.5:
        location_name = "Bengaluru, KA, India"
    elif abs(lat - 28.61) < 0.5 and abs(lon - 77.20) < 0.5:
        location_name = "New Delhi, India"
        
    return jsonify({
        'success': True,
        'location_name': location_name,
        'latitude': lat,
        'longitude': lon,
        'temperature': temp,
        'solar_irradiance': irradiance,
        'cloud_cover': cloud,
        'humidity': humidity,
        'wind_speed': wind,
        'rainfall': rain,
        'dust_level': dust,
        'hour': current_hour,
        'month': current_month
    })

@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    lat = float(request.args.get('lat', 11.0168))
    lon = float(request.args.get('lon', 76.9558))
    
    # 24-Hour Hourly Forecast
    hourly_forecast = []
    feature_cols = ['temperature', 'solar_irradiance', 'cloud_cover', 'humidity', 'wind_speed', 'rainfall', 'dust_level', 'hour', 'month']
    
    for h in range(24):
        sun_factor = max(0.0, math.sin(math.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0.0
        h_temp = round(24.0 + 7.0 * sun_factor, 1)
        h_irr = round(sun_factor * 900.0, 1)
        h_cloud = round(20.0 + 15.0 * math.sin(h / 3), 1)
        h_hum = round(65.0 - 20.0 * sun_factor, 1)
        h_wind = round(3.5 + 2.0 * math.cos(h / 4), 1)
        h_rain = 0.0
        h_dust = 2.5
        
        feats = pd.DataFrame([[h_temp, h_irr, h_cloud, h_hum, h_wind, h_rain, h_dust, h, 8]], columns=feature_cols)
        pred_w = float(rf_model.predict(feats)[0]) if rf_model else 0.0
        
        hourly_forecast.append({
            'hour': f"{h:02d}:00",
            'temperature': h_temp,
            'solar_irradiance': h_irr,
            'cloud_cover': h_cloud,
            'wind_speed': h_wind,
            'predicted_watts': round(max(0, pred_w), 1)
        })
        
    # 7-Day Daily Forecast
    days_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    daily_forecast = []
    for d in range(7):
        day_temp = round(27.0 + random.uniform(-2, 3), 1)
        day_irr = round(650.0 + random.uniform(-100, 150), 1)
        day_cloud = round(25.0 + random.uniform(-15, 30), 1)
        day_wind = round(4.5 + random.uniform(-1, 2), 1)
        
        # Peak noon prediction
        feats = pd.DataFrame([[day_temp, day_irr, day_cloud, 50.0, day_wind, 0.0, 2.0, 13, 8]], columns=feature_cols)
        peak_pred_w = float(rf_model.predict(feats)[0]) if rf_model else 0.0
        
        daily_forecast.append({
            'day': f"Day {d+1} ({days_map[d % 7]})",
            'avg_temp': day_temp,
            'avg_irradiance': day_irr,
            'avg_cloud': day_cloud,
            'avg_wind': day_wind,
            'peak_predicted_watts': round(max(0, peak_pred_w), 1)
        })
        
    return jsonify({
        'success': True,
        'hourly': hourly_forecast,
        'daily': daily_forecast
    })

if __name__ == '__main__':
    print("[+] Launching SolarIQ Web Server at http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
