"""
Psychrometric calculations for moist-air properties.

All formulas follow standard meteorological and ASHRAE conventions.

References
----------
* Magnus formula for saturation vapour pressure:
  Buck (1981), "New equations for computing vapor pressure and
  enhancement factor", J. Appl. Meteor. 20, 1527–1532.
* Wet-bulb approximation: Stull (2011), "Wet-Bulb Temperature from
  Relative Humidity and Air Temperature", J. Appl. Meteor. Climatol.
  50, 2267–2269.
* Air density: ideal-gas mixture law for moist air.
"""

from __future__ import annotations

import math

from app.models.schemas import PsychrometricProperties


# ---------------------------------------------------------------------------
# Magnus formula coefficients (valid for –40 to +60 °C)
# ---------------------------------------------------------------------------
_MAGNUS_A = 17.625
_MAGNUS_B = 243.04  # °C


def _saturation_vapour_pressure(temp_c: float) -> float:
    """
    Compute the saturation vapour pressure (hPa) using the Magnus formula.

    Parameters
    ----------
    temp_c:
        Air temperature in °C.

    Returns
    -------
    float
        Saturation vapour pressure in hPa.
    """
    return 6.1078 * math.exp(_MAGNUS_A * temp_c / (_MAGNUS_B + temp_c))


# ---------------------------------------------------------------------------
# Public calculation functions
# ---------------------------------------------------------------------------


def calculate_absolute_humidity(temp_c: float, rh_percent: float) -> float:
    """
    Calculate absolute humidity in g/m³.

    Uses the Magnus formula to obtain the partial pressure of water vapour
    and then applies the ideal-gas law for water vapour.

    Parameters
    ----------
    temp_c:
        Dry-bulb temperature in °C.
    rh_percent:
        Relative humidity in percent (0–100).

    Returns
    -------
    float
        Absolute humidity in g/m³.
    """
    rh_frac = max(0.0, min(100.0, rh_percent)) / 100.0
    e_s = _saturation_vapour_pressure(temp_c)       # hPa
    e_a = rh_frac * e_s                             # actual vapour pressure (hPa)

    # Ideal-gas law: ρ_v = (e_a × M_w) / (R × T_K)
    # M_w = 18.015 g/mol, R = 8.314 J/(mol·K), e_a in Pa = e_a_hPa × 100
    temp_k = temp_c + 273.15
    absolute_humidity = (e_a * 100.0 * 18.015) / (8.314 * temp_k)
    return round(absolute_humidity, 4)


def calculate_dew_point(temp_c: float, rh_percent: float) -> float:
    """
    Calculate the dew-point temperature in °C using the Magnus formula.

    Parameters
    ----------
    temp_c:
        Dry-bulb temperature in °C.
    rh_percent:
        Relative humidity in percent (0–100).

    Returns
    -------
    float
        Dew-point temperature in °C.
    """
    rh_frac = max(1e-6, min(100.0, rh_percent)) / 100.0
    ln_rh = math.log(rh_frac)
    gamma = ln_rh + (_MAGNUS_A * temp_c) / (_MAGNUS_B + temp_c)
    dew_point = (_MAGNUS_B * gamma) / (_MAGNUS_A - gamma)
    return round(dew_point, 2)


def calculate_wet_bulb_temperature(temp_c: float, rh_percent: float) -> float:
    """
    Estimate the wet-bulb temperature in °C (Stull 2011 approximation).

    Accurate to ±0.65 °C for the range 5–50 °C and 5–99 % RH.

    Parameters
    ----------
    temp_c:
        Dry-bulb temperature in °C.
    rh_percent:
        Relative humidity in percent (0–100).

    Returns
    -------
    float
        Wet-bulb temperature in °C.
    """
    rh = max(0.0, min(100.0, rh_percent))
    wet_bulb = (
        temp_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(temp_c + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
        - 4.686035
    )
    return round(wet_bulb, 2)


def calculate_specific_humidity(
    temp_c: float, rh_percent: float, pressure_hpa: float
) -> float:
    """
    Calculate specific humidity in g(vapour)/kg(moist air).

    Parameters
    ----------
    temp_c:
        Dry-bulb temperature in °C.
    rh_percent:
        Relative humidity in percent (0–100).
    pressure_hpa:
        Atmospheric (total) pressure in hPa.

    Returns
    -------
    float
        Specific humidity in g/kg.
    """
    rh_frac = max(0.0, min(100.0, rh_percent)) / 100.0
    e_s = _saturation_vapour_pressure(temp_c)
    e_a = rh_frac * e_s  # actual vapour pressure (hPa)

    # ε = M_w / M_d = 0.622
    # q = ε × e_a / (p - (1 - ε) × e_a)  [kg/kg] → ×1000 for g/kg
    epsilon = 0.622
    q_kg_kg = (epsilon * e_a) / (pressure_hpa - (1 - epsilon) * e_a)
    return round(q_kg_kg * 1000.0, 4)


def calculate_air_density(
    temp_c: float, pressure_hpa: float, rh_percent: float
) -> float:
    """
    Calculate the density of moist air in kg/m³.

    Uses the virtual temperature approach (accounts for water-vapour
    buoyancy effect on air density).

    Parameters
    ----------
    temp_c:
        Dry-bulb temperature in °C.
    pressure_hpa:
        Atmospheric pressure in hPa.
    rh_percent:
        Relative humidity in percent (0–100).

    Returns
    -------
    float
        Moist-air density in kg/m³.
    """
    rh_frac = max(0.0, min(100.0, rh_percent)) / 100.0
    e_s = _saturation_vapour_pressure(temp_c)
    e_a = rh_frac * e_s  # hPa

    pressure_pa = pressure_hpa * 100.0
    e_a_pa = e_a * 100.0

    # Moist-air density: ρ = (p_d / (R_d × T)) + (e_a / (R_v × T))
    # R_d = 287.058 J/(kg·K), R_v = 461.495 J/(kg·K)
    temp_k = temp_c + 273.15
    R_d = 287.058
    R_v = 461.495
    p_d_pa = pressure_pa - e_a_pa  # partial pressure of dry air

    density = (p_d_pa / (R_d * temp_k)) + (e_a_pa / (R_v * temp_k))
    return round(density, 4)


def get_all_psychrometric_properties(
    temp_c: float, rh_percent: float, pressure_hpa: float
) -> PsychrometricProperties:
    """
    Compute all relevant psychrometric properties at once.

    Parameters
    ----------
    temp_c:
        Dry-bulb temperature in °C.
    rh_percent:
        Relative humidity in percent (0–100).
    pressure_hpa:
        Atmospheric pressure in hPa.

    Returns
    -------
    PsychrometricProperties
        Validated Pydantic model containing all derived properties.
    """
    return PsychrometricProperties(
        absolute_humidity=calculate_absolute_humidity(temp_c, rh_percent),
        dew_point=calculate_dew_point(temp_c, rh_percent),
        wet_bulb_temp=calculate_wet_bulb_temperature(temp_c, rh_percent),
        specific_humidity=calculate_specific_humidity(temp_c, rh_percent, pressure_hpa),
        air_density=calculate_air_density(temp_c, pressure_hpa, rh_percent),
    )
