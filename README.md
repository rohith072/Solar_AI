# SolarIQ - AI-Integrated Renewable Energy Intelligence & Load Management System

**Author**: Rohith K (727623BEE072)  
**Round**: Final Round Prototype Demo (Software Implementation)

---

## 🌟 Overview

**SolarIQ** is a pure software implementation of an AI-Integrated Weather Sensing, Renewable Power Prediction, and Autonomous Agentic Load Management System. 

It fulfills all presentation objectives:
1. **Real-Time Weather Sensing**: Software-simulated multi-parameter weather pipeline (Temperature, Solar Irradiance, Cloud Cover, Humidity, Wind Speed, Rainfall, Dust Index).
2. **AI Power Forecasting**: Machine Learning models using **Random Forest Regressor** ($R^2 = 0.9983$) and **Gradient Boosting Regressor (GBDT)** ($R^2 = 0.9987$) to project solar & wind generation.
3. **Agentic AI 5-Connected Load Recommendation Engine**:
   - Explicitly handles 5 connected loads (HVAC, EV Charger, Water Heater, Refrigeration, Essential Lighting).
   - Autonomous Deficit Detection: When active demand exceeds generated power, the Agentic AI engine recommends specific lower-priority loads to limit/switch OFF.
   - Provides 1-Click Auto-Balance, battery storage dispatch, peak tariff scheduling, and weather risk warnings.
4. **Live Interactive Web Dashboard**: Interactive Leaflet maps, Chart.js forecast curves, What-If simulator, and recommendation feeds.

---

## 💻 Step-by-Step Command Prompt (CMD) Setup Instructions

### Step 1: Open Command Prompt and Navigate to Project Directory
```cmd
cd C:\Users\ROHITH\.gemini\antigravity\scratch\solariq_ai_power_system
```

### Step 2: Install Python Dependencies
```cmd
pip install -r requirements.txt
```

### Step 3: Train Machine Learning Models (Random Forest & GBDT)
```cmd
python train_model.py
```
*Outputs: Synthetic 8,760-hour annual dataset (`data/weather_power_dataset.csv`) and trained models saved to `models/solar_rf_model.pkl` and `models/solar_gb_model.pkl`.*

### Step 4: Launch Web Dashboard & Server
```cmd
python app.py
```
*Starts the server at:* `http://127.0.0.1:5000`

---

## 🧪 Demonstration & Verification Guide

1. Open your web browser and navigate to `http://127.0.0.1:5000`.
2. **Location Selection**: Click anywhere on the interactive Leaflet map to update weather sensing for different geographical coordinates.
3. **Model Selection**: Switch between **Random Forest Regressor** and **Gradient Boosting (GBDT)** to compare real-time wattage predictions and performance metrics ($R^2$, MAE, RMSE).
4. **What-If Weather Simulator**: Drag the sliders for **Solar Radiation**, **Cloud Cover**, or **Temperature** to test weather events.
5. **5-Load Deficit & Agentic AI Demo**:
   - Turn **ON** all 5 loads in the **5 Connected Loads Manager** (Demand = ~7,500 W).
   - Reduce **Solar Radiation** slider to ~200 W/m² (Generation = ~900 W).
   - Observe the **🚨 POWER DEFICIT DETECTED** alert in red.
   - Read the Agentic AI recommendation: *Switch OFF EV Fast Charger (3300W) and HVAC (2000W)*.
   - Click **⚡ 1-Click Auto-Balance Loads** to automatically shed recommended loads and restore stability!

---

## 📦 Zip Codebase Generation

To build or refresh the zip archive:
```cmd
python create_zip.py
```
*Generates:* `solariq_ai_power_system.zip` inside the project folder and the parent scratch directory.
