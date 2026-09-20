def simulate_mission_margin(current_health, target_throttle, target_altitude, current_anomaly):
    """
    Core USP logic: Calculates Mission Survival Margin based on counterfactual inputs.
    If engine is anomalous, high throttle/altitude aggressively drops the margin.
    Dropping altitude or throttle allows a degraded engine to recover mission margin.
    """
    # Base margin derived from current health
    base_margin = current_health - 50.0  
    
    # Penalties for aggressive counterfactuals while anomalous
    throttle_penalty = max(0, (target_throttle - 40)) * 0.8 * current_anomaly
    altitude_penalty = (target_altitude / 1000) * 1.5 * current_anomaly
    
    margin = base_margin - throttle_penalty - altitude_penalty
    
    # Clamp between -100% and 100%
    return round(max(-100.0, min(100.0, margin)), 2)
