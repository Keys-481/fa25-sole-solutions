"""
Calculation functions for the main UI.
"""

'''Basic Plantar Loading'''
# Peak Pressure (kPa/N/cm²) – maximum force under each sensor or region. 
def peak_pressure(pressure_data):
# Pressure–Time Integral (PTI) – cumulative loading over stance.
def pressure_time_integral(pressure_data, time_data):
# Contact Area – surface area of the foot in contact with the insole.
def contact_area(pressure_data, threshold=20):
# Center of Pressure (CoP) Path – trajectory of pressure centroid across stance.
def center_of_pressure(pressure_data, sensor_positions):

    '''Temporal-Spatial Parameters'''
# Stance time / swing time
def stance_swing_time(time_data):
# Step time, stride time, cadence
def step_stride_cadence(time_data):
# Gait cycle phases (initial contact, loading response, mid-stance, push-off)
def gait_cycle_phases(time_data, pressure_data):
# Symmetry indices (right vs. left stance, timing, or loading).
def symmetry_indices(param_right, param_left):

    '''Force & Work Estimates'''
# Vertical Ground Reaction Force (vGRF) estimates (from summing insole pressures).
def vertical_ground_reaction_force(pressure_data, sensor_areas):
# Impulse (Force × Time) – integral of vGRF curve.
def impulse(vgrf_data, time_data):
# Load rates – how quickly force is applied (important for injury risk).
def load_rate(vgrf_data, time_data):

    '''Footstrike & Running Metrics'''
# Footstrike angle (heel strike, midfoot, forefoot classification).
def footstrike_angle(pressure_data, sensor_positions):
# Step length & stride length (estimated via CoP movement + timing).
def step_stride_length(cop_data, time_data):
# Running symmetry and variability.
def running_symmetry_variability(param_right, param_left):
# Jump/landing forces (peak and impulse).
def jump_landing_forces(pressure_data, time_data):

    '''Clinical & Performance Indicators'''
# Balance measures – CoP sway area, velocity (for quiet standing tasks).
def balance_measures(cop_data, time_data):
# Pressure distribution by foot region (heel, midfoot, forefoot, hallux, lateral toes).
def regional_pressure_distribution(pressure_data, sensor_regions):
# Asymmetries in gait or running (useful for rehab, e.g., post-ACL reconstruction).
def gait_asymmetries(param_right, param_left):
# Load monitoring – total steps, cumulative load exposure.
def load_monitoring(step_count, pressure_data, time_data):