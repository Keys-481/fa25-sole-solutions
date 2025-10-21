"""
Calculation functions for the main UI.
"""

'''Basic Plantar Loading'''
# Peak Pressure (kPa/N/cm²) – maximum force under each sensor or region. 
def peak_pressure(data_storage): # TODO: Takes in the data to find the max pressure value for each sensor in the csv file    # peak_values = {}
    peak_values = {}
    for sensor, pressures in data_storage.items():
        peak_values[sensor] = max(pressures)
    return peak_values
# Pressure–Time Integral (PTI) – cumulative loading over stance.
def pressure_time_integral(pressure_data, time_data):
    pti_values = {}
    for sensor, pressures in pressure_data.items():
        pti = 0
        for i in range(1, len(pressures)):
            dt = time_data[i] - time_data[i-1]
            avg_pressure = (pressures[i] + pressures[i-1]) / 2
            pti += avg_pressure * dt
        pti_values[sensor] = pti
    return pti_values
# Contact Area – surface area of the foot in contact with the insole.
def contact_area(pressure_data, threshold=20):
    contact_areas = {}
    for sensor, pressures in pressure_data.items():
        contact_time = sum(1 for p in pressures if p >= threshold)
        contact_areas[sensor] = contact_time  # Assuming each time unit corresponds to a fixed area
    return contact_areas
# Center of Pressure (CoP) Path – trajectory of pressure centroid across stance.
def center_of_pressure(pressure_data, sensor_positions):
    cop_path = []
    for i in range(len(next(iter(pressure_data.values())))):
        total_pressure = sum(pressure_data[sensor][i] for sensor in pressure_data)
        if total_pressure == 0:
            cop_path.append((0, 0))
            continue
        cop_x = sum(sensor_positions[sensor][0] * pressure_data[sensor][i] for sensor in pressure_data) / total_pressure
        cop_y = sum(sensor_positions[sensor][1] * pressure_data[sensor][i] for sensor in pressure_data) / total_pressure
        cop_path.append((cop_x, cop_y))
    return cop_path

    '''Temporal-Spatial Parameters'''
# Stance time / swing time
def stance_swing_time(time_data):
    stance_time = time_data[-1] - time_data[0]
    # Assuming swing time is total time minus stance time
    total_time = time_data[-1] - time_data[0]
    swing_time = total_time - stance_time
    return stance_time, swing_time
# Step time, stride time, cadence
def step_stride_cadence(time_data):
    step_time = time_data[1] - time_data[0]  # Assuming time_data has timestamps for each step
    stride_time = time_data[2] - time_data[0]  # Assuming time_data has timestamps for each stride
    cadence = 60 / step_time  # Steps per minute
    return step_time, stride_time, cadence
# Gait cycle phases (initial contact, loading response, mid-stance, push-off)
def gait_cycle_phases(time_data, pressure_data):
    phases = {}
    # Placeholder logic for phase detection
    phases['initial_contact'] = time_data[0]
    phases['loading_response'] = time_data[len(time_data)//4]
    phases['mid_stance'] = time_data[len(time_data)//2]
    phases['push_off'] = time_data[-1]
    return phases
# Symmetry indices (right vs. left stance, timing, or loading).
def symmetry_indices(param_right, param_left):
    if param_right + param_left == 0:
        return 0

    '''Force & Work Estimates'''
# Vertical Ground Reaction Force (vGRF) estimates (from summing insole pressures).
def vertical_ground_reaction_force(pressure_data, sensor_areas):
    vgrf = []
    for i in range(len(next(iter(pressure_data.values())))):
        total_force = sum(pressure_data[sensor][i] * sensor_areas[sensor] for sensor in pressure_data)
        vgrf.append(total_force)
    return vgrf
# Impulse (Force × Time) – integral of vGRF curve.
def impulse(vgrf_data, time_data):
    impulse_value = 0
    for i in range(1, len(vgrf_data)):
        dt = time_data[i] - time_data[i-1]
        avg_force = (vgrf_data[i] + vgrf_data[i-1]) / 2
        impulse_value += avg_force * dt
    return impulse_value
# Load rates – how quickly force is applied (important for injury risk).
def load_rate(vgrf_data, time_data):
    load_rates = []
    for i in range(1, len(vgrf_data)):
        dt = time_data[i] - time_data[i-1]
        if dt == 0:
            load_rates.append(0)
            continue
        rate = (vgrf_data[i] - vgrf_data[i-1]) / dt
        load_rates.append(rate)
    return load_rates

    '''Footstrike & Running Metrics'''
# Footstrike angle (heel strike, midfoot, forefoot classification).
def footstrike_angle(pressure_data, sensor_positions):
    # Placeholder logic for footstrike angle calculation
    heel_pressure = pressure_data.get('heel', [0]*len(next(iter(pressure_data.values()))))
    forefoot_pressure = pressure_data.get('forefoot', [0]*len(next(iter(pressure_data.values()))))
    if max(heel_pressure) > max(forefoot_pressure):
        return 'heel strike'
    elif max(forefoot_pressure) > max(heel_pressure):
        return 'forefoot strike'
    else:
        return 'midfoot strike'
# Step length & stride length (estimated via CoP movement + timing).
def step_stride_length(cop_data, time_data):
    step_length = 0
    stride_length = 0
    # Placeholder logic for length calculation
    if len(cop_data) >= 2:
        step_length = ((cop_data[1][0] - cop_data[0][0])**2 + (cop_data[1][1] - cop_data[0][1])**2)**0.5
    if len(cop_data) >= 3:
        stride_length = ((cop_data[2][0] - cop_data[0][0])**2 + (cop_data[2][1] - cop_data[0][1])**2)**0.5
    return step_length, stride_length
# Running symmetry and variability.
def running_symmetry_variability(param_right, param_left):
    if param_right + param_left == 0:
        return 0
    symmetry_index = abs(param_right - param_left) / ((param_right + param_left) / 2)
    return symmetry_index
# Jump/landing forces (peak and impulse).
def jump_landing_forces(pressure_data, time_data):
    peak_force = 0
    impulse_value = 0
    for i in range(len(next(iter(pressure_data.values())))):
        total_force = sum(pressure_data[sensor][i] for sensor in pressure_data)
        if total_force > peak_force:
            peak_force = total_force
        if i > 0:
            dt = time_data[i] - time_data[i-1]
            avg_force = (total_force + sum(pressure_data[sensor][i-1] for sensor in pressure_data)) / 2
            impulse_value += avg_force * dt
    return peak_force, impulse_value

    '''Clinical & Performance Indicators'''
# Balance measures – CoP sway area, velocity (for quiet standing tasks).
def balance_measures(cop_data, time_data):
    sway_area = 0
    sway_velocity = 0
    # Placeholder logic for balance measures
    if len(cop_data) >= 2:
        for i in range(1, len(cop_data)):
            distance = ((cop_data[i][0] - cop_data[i-1][0])**2 + (cop_data[i][1] - cop_data[i-1][1])**2)**0.5
            dt = time_data[i] - time_data[i-1]
            if dt > 0:
                sway_velocity += distance / dt
        sway_velocity /= (len(cop_data) - 1)
    return sway_area, sway_velocity
# Pressure distribution by foot region (heel, midfoot, forefoot, hallux, lateral toes).
def regional_pressure_distribution(pressure_data, sensor_regions):
    region_pressures = {}
    for sensor, pressures in pressure_data.items():
        region = sensor_regions.get(sensor, 'unknown')
        if region not in region_pressures:
            region_pressures[region] = []
        region_pressures[region].extend(pressures)
    avg_region_pressures = {region: sum(pressures)/len(pressures) for region, pressures in region_pressures.items() if pressures}
    return avg_region_pressures
# Asymmetries in gait or running (useful for rehab, e.g., post-ACL reconstruction).
def gait_asymmetries(param_right, param_left):
    if param_right + param_left == 0:
        return 0
    asymmetry_index = abs(param_right - param_left) / ((param_right + param_left) / 2)
    return asymmetry_index
# Load monitoring – total steps, cumulative load exposure.
def load_monitoring(step_count, pressure_data, time_data):
    cumulative_load = 0
    for i in range(len(next(iter(pressure_data.values())))):
        total_pressure = sum(pressure_data[sensor][i] for sensor in pressure_data)
        cumulative_load += total_pressure * (time_data[1] - time_data[0])  # Assuming uniform time intervals
    return step_count, cumulative_load