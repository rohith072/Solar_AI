"""
SolarIQ Agentic AI Recommendation Engine
Provides intelligent autonomous load management, generation balancing,
battery dispatch optimization, and weather-driven advisory.
"""

# Standard 5 Connected Loads Definition
DEFAULT_LOADS = [
    {
        "id": "load_1",
        "name": "HVAC / Air Conditioning",
        "rating_watts": 2000,
        "priority": 4, # 1=Highest/Critical, 5=Lowest/Deferrable
        "category": "Climate",
        "status": True, # Currently ON
        "icon": "fa-snowflake"
    },
    {
        "id": "load_2",
        "name": "EV Fast Charger",
        "rating_watts": 3300,
        "priority": 5,
        "category": "Mobility",
        "status": True,
        "icon": "fa-car-battery"
    },
    {
        "id": "load_3",
        "name": "Smart Water Heater",
        "rating_watts": 1500,
        "priority": 3,
        "category": "Thermal",
        "status": True,
        "icon": "fa-hot-tub-person"
    },
    {
        "id": "load_4",
        "name": "Refrigeration & Food Storage",
        "rating_watts": 450,
        "priority": 1,
        "category": "Critical",
        "status": True,
        "icon": "fa-refrigerator"
    },
    {
        "id": "load_5",
        "name": "Essential Lighting & Electronics",
        "rating_watts": 250,
        "priority": 2,
        "category": "Essential",
        "status": True,
        "icon": "fa-lightbulb"
    }
]

class AgenticAIEngine:
    def __init__(self):
        pass

    def evaluate_system(self, predicted_solar_w, predicted_wind_w, weather_data, loads_state, battery_soc=65.0):
        """
        Evaluates current generated power against active loads state and generates 
        actionable Agentic AI recommendations.
        """
        total_generation = max(0.0, float(predicted_solar_w) + float(predicted_wind_w))
        
        active_loads = [l for l in loads_state if l.get('status', False)]
        inactive_loads = [l for l in loads_state if not l.get('status', False)]
        
        total_demand = sum(l['rating_watts'] for l in active_loads)
        power_balance = total_generation - total_demand
        
        recommendations = []
        alerts = []
        action_plan = []
        recommended_turn_off_ids = []
        
        # -------------------------------------------------------------
        # 1. CRITICAL LOAD DEFICIT ANALYSIS & LIMITATION RECOMMENDATIONS
        # -------------------------------------------------------------
        if total_demand > total_generation:
            deficit = total_demand - total_generation
            
            # Sort active loads by priority descending (least critical first: priority 5 -> 4 -> 3 -> 2 -> 1)
            candidates_for_shedding = sorted(active_loads, key=lambda x: x['priority'], reverse=True)
            
            accumulated_shed_power = 0
            loads_to_shed = []
            
            for load in candidates_for_shedding:
                if accumulated_shed_power < deficit and load['priority'] > 1: # Protect priority 1 critical load
                    loads_to_shed.append(load)
                    recommended_turn_off_ids.append(load['id'])
                    accumulated_shed_power += load['rating_watts']
            
            # Format high urgency alert
            alerts.append({
                "type": "danger",
                "title": "🚨 POWER DEFICIT DETECTED",
                "message": f"Generating output ({total_generation:.0f} W) is insufficient for active load demand ({total_demand:.0f} W). Deficit: -{deficit:.0f} W."
            })
            
            shed_names = ", ".join([f"'{l['name']}' ({l['rating_watts']}W)" for l in loads_to_shed])
            
            recommendations.append({
                "category": "Load Shedding & Usage Limitation",
                "title": "⚡ Limit Connected Load Usage Immediately",
                "urgency": "HIGH",
                "reasoning": f"To prevent microgrid trip and battery exhaustion, switch OFF lower-priority loads: {shed_names}.",
                "expected_saving": f"{accumulated_shed_power} W saved",
                "actionable": True,
                "action_type": "auto_shed",
                "target_load_ids": recommended_turn_off_ids
            })
            
            # Battery support calculation
            if battery_soc > 20.0:
                available_battery_w = 1500 # max battery discharge rate
                battery_cover_hours = (battery_soc - 20.0) * 50.0 / max(1.0, deficit)
                recommendations.append({
                    "category": "Battery Storage Dispatch",
                    "title": "🔋 Discharge Battery Reserve",
                    "urgency": "MEDIUM",
                    "reasoning": f"Battery SOC is at {battery_soc:.0f}%. Discharging at up to {min(deficit, available_battery_w):.0f} W to cushion power deficit for ~{battery_cover_hours:.1f} hours.",
                    "expected_saving": f"{min(deficit, available_battery_w):.0f} W supplemented",
                    "actionable": False
                })
        else:
            surplus = total_generation - total_demand
            if surplus > 300:
                recommendations.append({
                    "category": "Surplus Optimization",
                    "title": "☀️ Generation Surplus Available",
                    "urgency": "LOW",
                    "reasoning": f"Power generation exceeds current demand by +{surplus:.0f} W. You can safely activate scheduled loads (EV Charger / Water Heater) or route surplus into battery storage.",
                    "expected_saving": "Zero grid dependency",
                    "actionable": False
                })
                
                if battery_soc < 95.0:
                    recommendations.append({
                        "category": "Battery Charging",
                        "title": "🔋 Direct Excess Generation to Battery Storage",
                        "urgency": "LOW",
                        "reasoning": f"Store surplus {surplus:.0f} W into battery bank (Current SOC: {battery_soc:.0f}%).",
                        "expected_saving": f"+{surplus:.0f} W battery charge rate",
                        "actionable": False
                    })
        
        # -------------------------------------------------------------
        # 2. TIME-OF-USE & SHIFTABLE LOAD ADVISORY
        # -------------------------------------------------------------
        hour = weather_data.get('hour', 12)
        if 6 <= hour <= 10:
            recommendations.append({
                "category": "Smart Scheduling",
                "title": "⏰ Pre-Peak Solar Ramp Advisory",
                "urgency": "INFO",
                "reasoning": "Solar irradiance is ramping up. Defer high-capacity EV charging and thermal heating until peak solar window (11:00 AM - 3:00 PM).",
                "expected_saving": "Optimizes renewable fraction to 92%",
                "actionable": False
            })
        elif 16 <= hour <= 20:
            recommendations.append({
                "category": "Peak Hour Demand Management",
                "title": "🌙 Evening Peak Grid Saver",
                "urgency": "MEDIUM",
                "reasoning": "Solar generation is declining. Switch non-essential appliances to eco mode or battery storage to avoid high peak-tariff grid rates.",
                "expected_saving": "Reduces peak tariff costs by 35%",
                "actionable": False
            })

        # -------------------------------------------------------------
        # 3. WEATHER IMPACT ADVISORY (CLOUD COVER & DUST)
        # -------------------------------------------------------------
        cloud_cover = weather_data.get('cloud_cover', 0)
        dust_level = weather_data.get('dust_level', 0)
        temp = weather_data.get('temperature', 25)
        
        if cloud_cover > 60:
            alerts.append({
                "type": "warning",
                "title": "☁️ High Cloud Cover Forecast",
                "message": f"Cloud cover is at {cloud_cover:.0f}%. Solar irradiance reduced. Standby load limiting enabled."
            })
            recommendations.append({
                "category": "Weather Alert",
                "title": "☁️ Cloud Attenuation Compensation",
                "urgency": "MEDIUM",
                "reasoning": f"Heavy cloud cover ({cloud_cover:.0f}%) is reducing solar panel yield. Prepare to shift flex loads to wind generation or battery backup.",
                "expected_saving": "Prevents unexpected brownout",
                "actionable": False
            })

        if dust_level >= 6.0:
            recommendations.append({
                "category": "Maintenance & Yield Optimization",
                "title": "🧹 Solar Panel Dust Cleaning Alert",
                "urgency": "LOW",
                "reasoning": f"Accumulated dust index is high ({dust_level:.1f}/10). Dust soiling is causing ~{(dust_level*1.5):.1f}% reduction in PV yield. Schedule panel cleaning.",
                "expected_saving": f"+{dust_level*1.5:.1f}% efficiency recovery",
                "actionable": False
            })
            
        if temp > 35:
            recommendations.append({
                "category": "Thermal Derating",
                "title": "🌡️ High Temperature Loss Warning",
                "urgency": "LOW",
                "reasoning": f"Ambient temperature ({temp:.1f}°C) exceeds standard test conditions (25°C). Silicon panel thermal derating causing -{((temp-25)*0.4):.1f}% power reduction.",
                "expected_saving": "Consider panel water mist cooling",
                "actionable": False
            })

        return {
            "total_generation_watts": round(total_generation, 2),
            "total_demand_watts": round(total_demand, 2),
            "power_balance_watts": round(power_balance, 2),
            "is_deficit": total_demand > total_generation,
            "deficit_watts": round(max(0, total_demand - total_generation), 2),
            "alerts": alerts,
            "recommendations": recommendations,
            "recommended_turn_off_ids": recommended_turn_off_ids
        }

agentic_ai = AgenticAIEngine()
