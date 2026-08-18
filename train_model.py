import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

def generate_synthetic_weather_dataset(samples=8760, seed=42):
    """
    Generates a realistic 1-year hourly weather dataset (8760 hours)
    for Solar & Wind power prediction training.
    """
    np.random.seed(seed)
    
    hours = np.tile(np.arange(24), samples // 24)
    days = np.repeat(np.arange(365), 24)
    months = (days // 30.5).astype(int) + 1
    months = np.clip(months, 1, 12)
    
    # Temperature with daily & seasonal sinusoidal variations
    seasonal_temp = 25 + 7 * np.sin(2 * np.pi * (days - 80) / 365)
    daily_temp = 5 * np.sin(2 * np.pi * (hours - 9) / 24)
    temperature = seasonal_temp + daily_temp + np.random.normal(0, 1.5, samples)
    temperature = np.clip(temperature, 10, 45)
    
    # Solar Irradiance (W/m2) - strictly daytime solar zenith cycle
    solar_base = np.maximum(0, np.sin(np.pi * (hours - 6) / 12))
    solar_base[hours < 6] = 0
    solar_base[hours > 18] = 0
    
    # Cloud cover (%)
    cloud_cover = np.clip(np.random.beta(2, 5, samples) * 100, 0, 100)
    
    # Actual irradiance impacted by cloud cover & atmospheric attenuation
    irradiance = solar_base * (1000 * (1 - 0.75 * (cloud_cover / 100)**1.5))
    irradiance = np.clip(irradiance + np.random.normal(0, 20, samples), 0, 1100)
    irradiance[hours < 6] = 0
    irradiance[hours > 18] = 0
    
    # Humidity (%) inverse to temperature
    humidity = np.clip(75 - 1.2 * (temperature - 20) + np.random.normal(0, 8, samples), 20, 95)
    
    # Wind Speed (m/s)
    wind_speed = np.clip(np.random.weibull(2.0, samples) * 4.5, 0.5, 22.0)
    
    # Rainfall (mm) correlated with cloud cover
    rainfall = np.where(cloud_cover > 75, np.random.exponential(2.0, samples), 0)
    rainfall = np.clip(rainfall, 0, 40)
    
    # Dust Index (0 to 10) affecting panel efficiency
    dust_level = np.clip(3 + 2 * np.sin(days / 20) + np.random.normal(0, 1, samples), 0, 10)
    
    # Solar Power Calculation (Simulated Physics Ground Truth)
    # Solar capacity = 3000W peak at 1000 W/m2, temp coefficient -0.4%/C above 25C, dust loss
    temp_efficiency_factor = 1.0 - 0.004 * np.maximum(0, temperature - 25)
    dust_efficiency_factor = 1.0 - 0.015 * dust_level
    solar_power = (irradiance / 1000.0) * 3000.0 * temp_efficiency_factor * dust_efficiency_factor
    solar_power = np.clip(solar_power + np.random.normal(0, 25, samples), 0, 3200)
    
    # Wind Power Calculation (Simulated 2000W turbine)
    # Cut-in: 2.5 m/s, Rated: 12 m/s, Cut-out: 20 m/s
    wind_power = np.zeros(samples)
    mask_gen = (wind_speed >= 2.5) & (wind_speed <= 20.0)
    wind_power[mask_gen] = 2000.0 * np.minimum(1.0, ((wind_speed[mask_gen] - 2.5) / (12.0 - 2.5))**3)
    wind_power = np.clip(wind_power + np.random.normal(0, 15, samples), 0, 2200)
    
    # Total generated power (Watts)
    total_power = solar_power + wind_power
    
    df = pd.DataFrame({
        'temperature': np.round(temperature, 2),
        'solar_irradiance': np.round(irradiance, 2),
        'cloud_cover': np.round(cloud_cover, 2),
        'humidity': np.round(humidity, 2),
        'wind_speed': np.round(wind_speed, 2),
        'rainfall': np.round(rainfall, 2),
        'dust_level': np.round(dust_level, 2),
        'hour': hours,
        'month': months,
        'solar_power': np.round(solar_power, 2),
        'wind_power': np.round(wind_power, 2),
        'total_power': np.round(total_power, 2)
    })
    
    return df

def train_and_save_models():
    print("[+] Generating synthetic weather & renewable power dataset...")
    df = generate_synthetic_weather_dataset(samples=8760)
    
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    df.to_csv('data/weather_power_dataset.csv', index=False)
    print("[-] Dataset saved to data/weather_power_dataset.csv")
    
    feature_cols = ['temperature', 'solar_irradiance', 'cloud_cover', 'humidity', 'wind_speed', 'rainfall', 'dust_level', 'hour', 'month']
    X = df[feature_cols]
    y_total = df['total_power']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_total, test_size=0.2, random_state=42)
    
    print("\n[+] Training Random Forest Model...")
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    
    rf_mae = mean_absolute_error(y_test, rf_preds)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_preds))
    rf_r2 = r2_score(y_test, rf_preds)
    
    print(f"   Random Forest Metrics -> MAE: {rf_mae:.2f} W, RMSE: {rf_rmse:.2f} W, R2: {rf_r2:.4f}")
    
    print("\n[+] Training Gradient Boosting (GBDT) Model...")
    gb_model = GradientBoostingRegressor(n_estimators=120, learning_rate=0.1, max_depth=6, random_state=42)
    gb_model.fit(X_train, y_train)
    gb_preds = gb_model.predict(X_test)
    
    gb_mae = mean_absolute_error(y_test, gb_preds)
    gb_rmse = np.sqrt(mean_squared_error(y_test, gb_preds))
    gb_r2 = r2_score(y_test, gb_preds)
    
    print(f"   Gradient Boosting Metrics -> MAE: {gb_mae:.2f} W, RMSE: {gb_rmse:.2f} W, R2: {gb_r2:.4f}")
    
    # Save models and metadata
    joblib.dump(rf_model, 'models/solar_rf_model.pkl')
    joblib.dump(gb_model, 'models/solar_gb_model.pkl')
    
    metadata = {
        'feature_cols': feature_cols,
        'rf_metrics': {'mae': float(rf_mae), 'rmse': float(rf_rmse), 'r2': float(rf_r2)},
        'gb_metrics': {'mae': float(gb_mae), 'rmse': float(gb_rmse), 'r2': float(gb_r2)},
        'rf_feature_importances': dict(zip(feature_cols, [float(x) for x in rf_model.feature_importances_])),
        'gb_feature_importances': dict(zip(feature_cols, [float(x) for x in gb_model.feature_importances_]))
    }
    joblib.dump(metadata, 'models/model_metadata.pkl')
    
    print("\n[SUCCESS] All models trained & serialized to models/ directory successfully!")

if __name__ == '__main__':
    train_and_save_models()
