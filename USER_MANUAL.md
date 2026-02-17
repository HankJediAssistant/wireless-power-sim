# ⚡ Wireless Power Transfer Simulator — User Manual

## Overview

This simulator models **coil-to-coil inductive power transfer** for applications like rotating robot joints, wireless chargers, and contactless power systems. It calculates efficiency, coupling, inductances, and resonant component values based on your coil geometry and operating parameters.

---

## Interface Layout

### 🎛️ Operating Parameters (Left Panel)

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Air Gap** | 1–50 mm | Distance between primary and secondary coils |
| **Frequency** | 10–1000 kHz | Operating frequency of the AC power source |
| **Required Power** | 1–100 W | Target power delivery to the load |
| **Input Voltage** | 5–48 V | DC input voltage to the inverter/driver |

### 🔧 Coil Design (Left Panel)

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Coil Radius** | 10–100 mm | Radius of both primary and secondary coils |
| **Primary Turns** | 5–50 | Number of wire turns on the primary (transmit) coil |
| **Secondary Turns** | 5–50 | Number of wire turns on the secondary (receive) coil |
| **Load Resistance** | 1–100 Ω | Resistance of the load being powered |

### 📊 Simulation Results (Right Panel)

**Main Metrics:**
- **Efficiency (%)** — Power delivered to load ÷ power input. Color-coded: green (>80%), yellow (50-80%), red (<50%)
- **Coupling (k)** — Coupling coefficient between coils (0 to 1). Higher = more magnetic flux links both coils
- **Primary Current (A)** — Current flowing through the primary coil
- **Secondary Current (A)** — Current delivered to the load
- **Power Input (W)** — Total power drawn from the source
- **Power Loss (W)** — Power dissipated as heat in coil resistance

**Coupling Status:**
- 🟢 **Critically Coupled** — Optimal energy transfer, maximum efficiency
- 🟡 **Under-Coupled** — Coils too far apart or weak magnetic coupling
- 🔴 **Over-Coupled** — Frequency splitting may occur; reduce coupling or adjust frequency

### 📈 Efficiency vs Air Gap Chart

Shows how efficiency and coupling coefficient change as air gap varies from 1–50 mm. Use this to:
- Find the maximum allowable air gap for your efficiency target
- Understand how mechanical tolerances affect performance

### 🔌 Component Values

| Value | Description |
|-------|-------------|
| **L₁, L₂** | Self-inductance of primary/secondary coils (μH) |
| **C₁, C₂** | Resonant capacitors needed for series resonance (nF) |
| **Q₁, Q₂** | Quality factors — higher Q = lower losses, sharper resonance |

---

## Physics & Formulas

### Self-Inductance (L)

For a single-layer solenoid coil:

```
L = μ₀ × N² × A × k_nagaoka / l
```

Where:
- **μ₀** = 4π × 10⁻⁷ H/m (permeability of free space)
- **N** = number of turns
- **A** = πr² (cross-sectional area)
- **l** = coil length (turns × wire diameter)
- **k_nagaoka** = correction factor for short coils ≈ 1/(1 + 0.9 × r/l)

### Mutual Inductance (M)

For two coaxial circular coils of identical radius:

```
M = μ₀ × π × N₁ × N₂ × r⁴ / (2 × (r² + d²)^1.5)
```

Where:
- **r** = coil radius (m)
- **d** = air gap / separation distance (m)
- **N₁, N₂** = turns on primary and secondary

This approximation works best when r and d are comparable (typical for wireless power).

### Coupling Coefficient (k)

```
k = M / √(L₁ × L₂)
```

- **k = 1**: Perfect coupling (all flux links both coils) — theoretical only
- **k = 0.5–0.9**: Tightly coupled, typical for close coils
- **k = 0.1–0.5**: Loosely coupled, common in wireless chargers
- **k < 0.1**: Very weakly coupled

### Resonant Capacitance

For series resonance at frequency f:

```
C = 1 / (4π²f²L)
```

Resonance maximizes power transfer by canceling inductive reactance.

### Quality Factor (Q)

```
Q = ωL / R = 2πfL / R
```

Where R is the coil's DC wire resistance. Higher Q means:
- Lower resistive losses
- Sharper frequency selectivity
- Higher efficiency

**Note:** At high frequencies (>100 kHz), skin effect increases effective resistance. This simulator uses DC resistance, so actual Q may be 30-50% lower.

### Maximum Efficiency

For resonant inductive coupling:

```
η_max = (k²Q₁Q₂) / (1 + √(1 + k²Q₁Q₂))²
```

This assumes optimal load matching and perfect resonance tuning.

### Wire Resistance

```
R = ρ × L_wire / A_wire
```

Where:
- **ρ** = 1.68 × 10⁻⁸ Ωm (copper resistivity at 20°C)
- **L_wire** = 2πr × N (total wire length)
- **A_wire** = π × (d_wire/2)² (wire cross-sectional area)

### Critical Coupling

```
k_critical = 1 / √(Q₁ × Q₂)
```

- **k > k_critical**: Over-coupled (frequency splitting occurs)
- **k = k_critical**: Critically coupled (maximum power transfer)
- **k < k_critical**: Under-coupled (limited by weak coupling)

---

## Design Guidelines

### Maximizing Efficiency

1. **Increase coil radius** — Larger coils have higher inductance and better coupling
2. **Increase turns** — More turns = higher L, higher Q, better coupling
3. **Reduce air gap** — Coupling falls rapidly with distance (~1/d³ for large gaps)
4. **Increase frequency** — Higher ω increases Q (up to a point where skin effect dominates)
5. **Use larger wire** — Lower resistance = higher Q

### Practical Considerations

- **Frequency choice**: 100–200 kHz is common (good Q, manageable skin effect, available components)
- **Typical efficiency**: 85–95% achievable at k > 0.5 with good coil design
- **Air gap tolerance**: Design for worst-case gap in your mechanical system
- **Thermal limits**: Power loss = heat; ensure coils can dissipate waste heat

---

## Limitations

1. **Simplified model** — Uses approximations valid for coaxial, identical coils
2. **No skin effect** — Wire resistance assumes uniform current distribution (DC)
3. **No proximity effect** — Adjacent turns don't affect resistance calculation
4. **No core materials** — Assumes air-core coils (no ferrite)
5. **No misalignment** — Assumes perfect axial alignment between coils
6. **No harmonic effects** — Assumes pure sinusoidal drive

---

## Running the Simulator

```bash
cd ~/Development/HankTesting/wireless-power-sim
source venv/bin/activate
python main.py
```

Then open **http://localhost:8080** in your browser.

---

*Wireless Power Transfer Simulator v1.0*
*Built for rotating robot joint power delivery*
