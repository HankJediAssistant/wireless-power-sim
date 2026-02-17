"""
Wireless Power Transfer Simulator
Coil-to-coil inductive power transfer for rotating robot joints
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import numpy as np
import math

app = FastAPI(title="Wireless Power Transfer Simulator")

class SimulationParams(BaseModel):
    # Coil parameters
    primary_turns: int = 20          # Number of turns in primary coil
    secondary_turns: int = 20        # Number of turns in secondary coil
    coil_radius: float = 0.025       # Coil radius in meters (25mm default)
    wire_diameter: float = 0.001     # Wire diameter in meters (1mm)
    
    # Operating parameters
    air_gap: float = 0.005           # Air gap in meters (5mm default)
    frequency: float = 200000        # Operating frequency in Hz (200kHz default)
    input_power: float = 10          # Input power in Watts (fixed supply)
    input_voltage: float = 24        # Input voltage
    
    # Load
    load_resistance: float = 10      # Load resistance in ohms


def calculate_self_inductance(turns: int, radius: float, wire_diameter: float = 0.001) -> float:
    """
    Calculate self-inductance of a single-layer solenoid coil.
    Uses Wheeler's empirical formula: L = μ₀ * π * N² * r² / (l + 0.9 * r)
    Accurate to within ~2-3% for typical coil geometries (l/r from 0.2 to 5).
    """
    mu_0 = 4 * math.pi * 1e-7  # Permeability of free space
    area = math.pi * radius ** 2
    # Coil length based on turns and wire diameter
    coil_length = turns * wire_diameter

    # Wheeler's correction factor for finite-length solenoids
    # Equivalent to Wheeler's formula: L = μ₀ * π * N² * r² / (l + 0.9 * r)
    k_factor = 1 / (1 + 0.9 * radius / coil_length)

    inductance = mu_0 * (turns ** 2) * area * k_factor / coil_length
    return inductance


def calculate_mutual_inductance(n1: int, n2: int, r1: float, r2: float, distance: float) -> float:
    """
    Calculate mutual inductance between two coaxial coils.
    
    For two coaxial circular coils of radii r1, r2 separated by distance d:
    M = μ₀ * π * N1 * N2 * r1² * r2² / (2 * ((r1² + r2²)/2 + d²)^1.5)
    
    For identical coils (r1 = r2 = r):
    M = μ₀ * π * N1 * N2 * r⁴ / (2 * (r² + d²)^1.5)
    
    This approximation works well when r and d are comparable in magnitude.
    """
    mu_0 = 4 * math.pi * 1e-7
    
    # For coils of potentially different radii
    r_eff_sq = r1 * r1 * r2 * r2  # r1² * r2² = r⁴ for identical coils
    
    # Average of squared radii for denominator (reduces to r² for identical coils)
    avg_r_sq = (r1 ** 2 + r2 ** 2) / 2
    
    # Mutual inductance using Neumann formula approximation
    # Units: (H/m) * m⁴ / m³ = H ✓
    M = mu_0 * math.pi * n1 * n2 * r_eff_sq / (2 * (avg_r_sq + distance ** 2) ** 1.5)
    
    return M


def calculate_coupling_coefficient(L1: float, L2: float, M: float) -> float:
    """Calculate coupling coefficient k = M / sqrt(L1 * L2)"""
    return M / math.sqrt(L1 * L2) if L1 > 0 and L2 > 0 else 0


def calculate_resonant_capacitance(inductance: float, frequency: float) -> float:
    """Calculate capacitance needed for resonance: C = 1 / (4π²f²L)"""
    omega = 2 * math.pi * frequency
    return 1 / (omega ** 2 * inductance)


def calculate_ac_resistance(dc_resistance: float, wire_diameter: float, frequency: float) -> tuple:
    """
    Calculate AC resistance accounting for skin effect.
    Returns (ac_resistance, skin_depth_meters).

    At high frequencies, current crowds to the conductor surface.
    Skin depth: δ = √(ρ / (π * f * μ₀))
    For wire_radius >> δ: R_ac = R_dc * (r_wire / (2δ))
    For wire_radius ~ δ: smooth transition via Bessel series expansion
    """
    mu_0 = 4 * math.pi * 1e-7
    resistivity_copper = 1.68e-8

    skin_depth = math.sqrt(resistivity_copper / (math.pi * frequency * mu_0))
    wire_radius = wire_diameter / 2
    ratio = wire_radius / skin_depth

    if ratio > 2.0:
        # Thick wire regime: current flows in annular ring of thickness δ
        ac_resistance = dc_resistance * (wire_radius / (2 * skin_depth))
    else:
        # Thin wire / transition regime: Bessel function series approximation
        # R_ac/R_dc ≈ 1 + (1/48)*(r/δ)⁴, accurate to <1% for ratio < 2
        ac_resistance = dc_resistance * (1 + (ratio ** 4) / 48)

    return ac_resistance, skin_depth


def calculate_power_transfer(params: SimulationParams) -> dict:
    """
    Calculate power transfer efficiency and characteristics.
    Uses skin-effect-corrected AC resistance and reflected impedance
    analysis for load-dependent efficiency (series-series topology).
    """
    # Calculate inductances
    L1 = calculate_self_inductance(params.primary_turns, params.coil_radius, params.wire_diameter)
    L2 = calculate_self_inductance(params.secondary_turns, params.coil_radius, params.wire_diameter)
    M = calculate_mutual_inductance(
        params.primary_turns, params.secondary_turns,
        params.coil_radius, params.coil_radius,
        params.air_gap
    )
    
    # Coupling coefficient
    k = calculate_coupling_coefficient(L1, L2, M)
    
    # Angular frequency
    omega = 2 * math.pi * params.frequency
    
    # Resonant capacitances
    C1 = calculate_resonant_capacitance(L1, params.frequency)
    C2 = calculate_resonant_capacitance(L2, params.frequency)
    
    # Reactances at operating frequency
    X_L1 = omega * L1
    X_L2 = omega * L2
    X_M = omega * M
    
    # Wire resistance (DC)
    wire_length_1 = 2 * math.pi * params.coil_radius * params.primary_turns
    wire_length_2 = 2 * math.pi * params.coil_radius * params.secondary_turns
    resistivity_copper = 1.68e-8  # Ohm-meters
    wire_area = math.pi * (params.wire_diameter / 2) ** 2
    R1_dc = resistivity_copper * wire_length_1 / wire_area
    R2_dc = resistivity_copper * wire_length_2 / wire_area

    # AC resistance with skin effect correction
    R1_ac, skin_depth = calculate_ac_resistance(R1_dc, params.wire_diameter, params.frequency)
    R2_ac, _ = calculate_ac_resistance(R2_dc, params.wire_diameter, params.frequency)

    # Quality factors (using AC resistance)
    Q1 = X_L1 / R1_ac if R1_ac > 0 else 0
    Q2 = X_L2 / R2_ac if R2_ac > 0 else 0

    # Maximum theoretical efficiency at resonance (optimal load matching)
    # η_max = k² * Q1 * Q2 / (1 + sqrt(1 + k² * Q1 * Q2))²
    kQ_product = k ** 2 * Q1 * Q2
    if kQ_product > 0:
        efficiency_max = kQ_product / (1 + math.sqrt(1 + kQ_product)) ** 2
    else:
        efficiency_max = 0

    # Actual efficiency with specified load resistance (reflected impedance analysis)
    # Series-series compensation topology at resonance
    omega_M_sq = (omega * M) ** 2
    R2_total = R2_ac + params.load_resistance

    if omega_M_sq > 0 and R2_total > 0:
        Z_reflected = omega_M_sq / R2_total
        eta_primary = Z_reflected / (R1_ac + Z_reflected)
        eta_secondary = params.load_resistance / R2_total
        efficiency = eta_primary * eta_secondary
    else:
        efficiency = 0

    # Optimal load resistance for maximum efficiency
    optimal_load = R2_ac * math.sqrt(1 + kQ_product) if kQ_product > 0 else 0

    # Power calculations (fixed input power, output degrades with efficiency)
    power_input = params.input_power
    power_output = power_input * efficiency
    power_loss = power_input - power_output

    # Current calculations
    I_primary = power_input / params.input_voltage if params.input_voltage > 0 else 0
    I_secondary = math.sqrt(power_output / params.load_resistance) if params.load_resistance > 0 and power_output > 0 else 0

    # Critical coupling
    k_critical = 1 / math.sqrt(Q1 * Q2) if Q1 > 0 and Q2 > 0 else 0
    coupling_status = "over-coupled" if k > k_critical else ("critically-coupled" if abs(k - k_critical) < 0.01 else "under-coupled")

    return {
        "inductances": {
            "primary_uH": L1 * 1e6,
            "secondary_uH": L2 * 1e6,
            "mutual_uH": M * 1e6
        },
        "coupling": {
            "coefficient": k,
            "critical_k": k_critical,
            "status": coupling_status
        },
        "resonance": {
            "capacitor_primary_nF": C1 * 1e9,
            "capacitor_secondary_nF": C2 * 1e9
        },
        "quality_factors": {
            "Q1": Q1,
            "Q2": Q2
        },
        "efficiency": {
            "percent": efficiency * 100,
            "max_percent": efficiency_max * 100,
            "optimal_load_ohm": optimal_load,
            "power_input_W": power_input,
            "power_output_W": power_output,
            "power_loss_W": power_loss
        },
        "currents": {
            "primary_A": I_primary,
            "secondary_A": I_secondary
        },
        "coil_resistance": {
            "primary_dc_mOhm": R1_dc * 1000,
            "secondary_dc_mOhm": R2_dc * 1000,
            "primary_ac_mOhm": R1_ac * 1000,
            "secondary_ac_mOhm": R2_ac * 1000
        },
        "skin_effect": {
            "skin_depth_mm": skin_depth * 1000,
            "resistance_ratio": R1_ac / R1_dc if R1_dc > 0 else 1
        }
    }


@app.post("/api/simulate")
async def simulate(params: SimulationParams):
    """Run power transfer simulation with given parameters"""
    results = calculate_power_transfer(params)
    return {"params": params.dict(), "results": results}


@app.get("/api/sweep/airgap")
async def sweep_airgap(
    min_gap: float = 0.001,
    max_gap: float = 0.05,
    steps: int = 50,
    frequency: float = 200000,
    power: float = 10,
    coil_radius: float = 0.025,
    primary_turns: int = 20,
    secondary_turns: int = 20,
    load_resistance: float = 10,
    input_voltage: float = 24,
    wire_diameter: float = 0.001
):
    """Sweep air gap and return efficiency and power curves"""
    gaps = np.linspace(min_gap, max_gap, steps)
    efficiencies = []
    couplings = []
    power_outputs = []
    power_inputs = []
    power_losses = []

    for gap in gaps:
        params = SimulationParams(
            air_gap=gap, frequency=frequency, input_power=power,
            coil_radius=coil_radius, primary_turns=primary_turns,
            secondary_turns=secondary_turns, load_resistance=load_resistance,
            input_voltage=input_voltage, wire_diameter=wire_diameter
        )
        result = calculate_power_transfer(params)
        efficiencies.append(result["efficiency"]["percent"])
        couplings.append(result["coupling"]["coefficient"])
        power_outputs.append(result["efficiency"]["power_output_W"])
        power_inputs.append(result["efficiency"]["power_input_W"])
        power_losses.append(result["efficiency"]["power_loss_W"])

    return {
        "gaps_mm": (gaps * 1000).tolist(),
        "efficiencies": efficiencies,
        "couplings": couplings,
        "power_outputs": power_outputs,
        "power_inputs": power_inputs,
        "power_losses": power_losses
    }


@app.get("/api/sweep/frequency")
async def sweep_frequency(
    min_freq: float = 10000,
    max_freq: float = 1000000,
    steps: int = 50,
    air_gap: float = 0.005,
    power: float = 10,
    coil_radius: float = 0.025,
    primary_turns: int = 20,
    secondary_turns: int = 20,
    load_resistance: float = 10,
    input_voltage: float = 24,
    wire_diameter: float = 0.001
):
    """Sweep frequency and return efficiency curve"""
    freqs = np.logspace(np.log10(min_freq), np.log10(max_freq), steps)
    efficiencies = []

    for freq in freqs:
        params = SimulationParams(
            frequency=freq, air_gap=air_gap, input_power=power,
            coil_radius=coil_radius, primary_turns=primary_turns,
            secondary_turns=secondary_turns, load_resistance=load_resistance,
            input_voltage=input_voltage, wire_diameter=wire_diameter
        )
        result = calculate_power_transfer(params)
        efficiencies.append(result["efficiency"]["percent"])

    return {
        "frequencies_kHz": (freqs / 1000).tolist(),
        "efficiencies": efficiencies
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI"""
    return open("static/index.html").read()


# Mount static files
import os
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
