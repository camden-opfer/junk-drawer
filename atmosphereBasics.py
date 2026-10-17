"""
Created: Camden Opfer November 2024

A pool of miscellaneous constants and functions useful for basic atmospheric science. Handy if you forget what a Clausius Claperyon is and, for some reason, want to remember in Python form.
"""

import numpy as np

## Reused Constants
Rd = 287 # J/(kg K) Dry air gas constant
Rv = 461 # J/(kg K) Water vapor gas constant
Cp_dry = 1004 #J/(kg K) Specific heat capacity of dry air
Cp_v = 4184 # J/(kg K) Specific heat capacity of water
Lv = 2.50 * 10**6 # J/kg Latent heat of vaporization of water
Ld = 2.83 * 10**6 # J/kg Latent heat of deposition of water
epsilon = Rd/Rv # Dimensionless ratio between Rd and Rv
Omega = 7.292 * 10**(-5) # Hz Rotation rate of Earth
a = 6.37 * 10**6 # m Radius of Earth
g = 9.81 # m/(s^2) Gravity

## Utilities
def gradient(y2, y1, x2, x1=0):
    """
    Input:
    Two pairs of coordinates (x1,y1) and (x2,y2)

    Output:
    Approximate slope dy/dx
    """
    return (y2 - y1)/(x2 - x1)

## Conversions
def FahrenheitToCelsius(F):
    """
    Input:
    Temperature, degrees F

    Output:
    Temperature, degrees C
    """
    return 5 / 9 * (F - 32)

def FahrenheitToKelvin(F):
    """
    Input:
    Temperature, degrees F

    Output:
    Temperature, K
    """
    return 5 / 9 * (F - 32) + 273.15

def CelsiusToKelvin(C):
    """
    Input:
    Temperature, degrees C

    Output:
    Temperature, K
    """
    return C + 273.15

def CelsiusToFahrenheit(C):
    """
    Input:
    Temperature, degrees C

    Output:
    Temperature, degrees F
    """
    return C * 9/5 + 32

def KelvinToCelsius(K):
    """
    Input:
    Temperature, K

    Output:
    Temperature, degrees C
    """
    return K - 273.15

def KelvinToFahrenheit(K):
    """
    Input:
    Temperature, K

    Output:
    Temperature, degrees F
    """
    return (K - 273.15) * 9 / 5 + 32

def KnotToMeterpersec(kt):
    """
    Input:
    Wind speed, kt

    Output:
    Windspeed, m/s
    """
    return kt * 0.514444

def MeterpersecToKnot(ms):
    """
    Input:
    Wind speed, m/s

    Output:
    Windspeed, kt
    """
    return ms * 1.94384

def pressureFromMap(p):
    """
    Input:
    The pressure reading from a weather map

    Output:
    The actual pressure value, Pa
    May not be accurate in extreme low and high pressure
    """
    if 500 < p:
        return 900 + p/10
    else:
        return 1000 + p/10

def mapFromPressure(p):
    """
    Input:
    Pressure, Pa

    Output:
    Corresponding weather map reading
    May not be accurate in extreme low and high pressure
    """
    if p < 1000:
        return (p - 900) * 10
    else:
        return (p - 1000) * 10

## General Atmospheric State
def idealGasLaw(p, T, R=Rd):
    """
    Inout:
    p is pressure, Pa
    T is temperature, K
    R is the gas constant (typically Rd or Rv), J/(kgK)
    
    Output:
    Denstiy (rho), kg/(m^3)
    """
    return p/(R * T)

# A dictionary to go from direction names to corresponding angles (degrees)
directionsToDegrees = {'N':0, 'NNE':22.5, 'NE':45, 'ENE':67.5, 'E':90, 'ESE':112.5,
                     'SE':135, 'SSE':157.5, 'S':180, 'SSW':202.5, 'SW':225,
                     'WSW':247.5, 'W':270, 'WNW':292.5, 'NW':315, 'NNW':337.5}

# A dictionary to go from angles (degrees) to corresponding direction names
degreesToDirections = {v:k for k, v in directionsToDegrees.items()}

def windCartesian(speed, direction):
    """
    Input:
    speed is wind speed, m/s
    direction is wind direction, degrees (N is 0, increases to right)
    
    Output: u, v
    u is zonal wind speed, m/s
    v is meridional wind speed, m/s
    """
    direction = np.pi/180 * direction
    return speed * np.sin(direction), speed * np.cos(direction)

def windPolar(u, v):
    """
    Input:
    u is zonal wind speed, m/s
    v is meridional wind speed, m/s

    Output: speed,direction
    speed is wind speed, m/s
    direction is wind direction, degrees (N is 0, increases to right)
    """
    if u > 0:
        return (u**2 + v**2)**(1/2), 270 - 180/np.pi * np.arctan(v/u)
    elif u < 0:
        return (u**2 + v**2)**(1/2), 90 - 180/np.pi * np.arctan(v/u)
    else:
        return (u**2 + v**2)**(1/2), [np.nan, 180, 0][np.sign(v)]

def virtualTemperature(q, T, _epsilon=epsilon):
    """
    Input:
    q is (saturated) specific humidity, kg/kg
    T is temperature, K
    epsilon is Rd/Rv, dimensionless

    Output:
    Virtual temperature, K
    """
    return (1 + _epsilon * q) * T

def potentialTemperature(T, p, p0=100000, _Rd=Rd, Cp=Cp_dry):
    """
    Input:
    T is temperature, K
    p is pressure, Pa
    p0 is basiline pressure (assumed to be ~SLP), Pa
    R is the gas constant (assumed to be dry), J/(kgK)
    Cp is heat capacity (assumed to be dry), J/(kgK)

    Output:
    Potential temperature, K
    """
    return T(p0/p)**(_Rd/Cp)

def rossby(V, f, R):
    """
    Input:
    V is wind velocity, m/s
    f is coriolis parameter, Hz
    R is radius of wind motion, m

    Output:
    Rossby number, dimensionless
    
    Ro = 1 is inertial, > 10 is cyclostrophic, < 0.1 is geostrophic, all are gradient
    """
    return V/(f * R)

def bruntVaisala(theta, dthetadz, _g=g):
    """
    Input:
    theta is potential temperature, K
    dthetadz is change in potential temperature with height, K/m
    g is gravity, m/s^2

    Ouptut:
    The Brun Vaisala frequency, Hz^2
    """
    return _g * dthetadz/theta

def beta(phi, _Omega=Omega, _a=a):
    """
    Input:
    phi is latitude, degrees
    Omega is planetary rotation rate, Hz
    a is planetary radius, m

    Output:
    Turbulence parameter beta, 1/(ms)
    """
    return 2 * _Omega * np.cos(phi)/_a

## Moisture
def ClausiusClapeyron(T_K, L, e0=6.113, T0=273.15, _Rv=Rv):
    """
    Input:
    T_K is temperature in Kelvin
    L is latent heat, Lv if over liquid water and Ld if over ice
    e0 and T0 are constants that should only be changed for precision
    
    
    Output:
    Vapor pressure (e or e_s), hPa
    """
    return e0 * np.exp(L / _Rv * (1 / T0 - 1 / T_K))

def Tetens(T_K, e0=6.113, b=17.2694, T1=273.15, _T2=35.86):
    """
    Input: 
    T_K is (dew point) temperature in Kelvin
    e0, b, T1, and T2 are constants that should only be changed for precision

    Output:
    (Saturation) vapor pressure (e or e_s), hPa
    """
    return e0 * np.exp(b * (T_K - T1) / (T_K - _T2))

def mixingRatio1(e, p, _epsilon=epsilon):
    """
    Input 
    e is vapor pressure, hPa or Pa or other
    p is pressure, units must match e
    epsilon is a constant and should only be changed for precision

    Output:
    Mixing ratio (r or w), kg/kg or dimensionless
    """
    return _epsilon * e / (p - e)

def mixingRatio2(q):
    """
    Input:
    q is specific humidity, kg/kg or dimensionless
    
    Output:
    Mixing ratio (r or w), kg/kg or dimensionless
    """
    return q / (1 - q)

def specificHumidity1(e, p, _epsilon=epsilon):
    """
    Input:
    e is vapor pressure, hPa or Pa or other
    p is pressure, units must match e
    epsilon is a constant and should only be changed for precision

    Output:
    Specific humidity (q), kg/kg or dimensionless
    """
    return _epsilon * e / p

def specificHumidity2(r):
    """
    Input:
    p is mixing ratio, kg/kg
    
    Output:
    Specific humidity, kg/kg or dimensionless
    """
    return r / (1 + r)

def relativeHumidity(regular, saturation):
    """
    Input:
    Regular and saturation of the same variable
    AMS says to use vapor pressure and saturation vapor pressure
    WMO says to use mixing ratio and saturation mixing ratio

    Output:
    Relvative humidity (RH), decimal value NOT percent
    """
    return regular/saturation

## Dynamics
def hypsometric1(T00, p, z1, z2=0, _Rd=Rd, _g=g):
    """
    Input:
    T00 is average column temperature, K
    p is the known pressure, hPa or Pa or other (output will match units)
    z1 is the height at which the pressure is p, m
    z2 is height at which output pressure applies (default sea level), m
    Rd is dry air gas constant, J/(K kg)
    g is gravity, m/s^2

    Output:
    Pressure (same units as p) at height z2
    """
    return p * np.exp(-_g * (z2 - z1)/(_Rd * T00))

def hypsometric2(T00, z, p1, p2, _Rd=Rd, _g=g):
    """
    Input:
    T00 is average column temperature, K
    z is the known height, m or ft or other (output will match units)
    p1 is the pressure at which the height is z, hPa or Pa or other
    p2 is pressure at which output height applies, units must match p1
    Rd is dry air gas constant, J/(K kg)
    g is gravity, m/s^2

    Output:
    Height (same units as z) at pressure level p2
    """
    return z + _Rd * T00/_g * np.log(p2/p1)

def coriolis(phi, _Omega=Omega):
    """
    Input:
    phi is latitude, degrees
    Omega is planetary rotation rate, Hz
    
    Output:
    Coriolis parameter (f), which is also planetary vorticity, Hz
    """
    return 2 * _Omega * np.sin(phi * np.pi / 180)

def geostrophic1(f, dpdn, rho=1):
    """ 
    dpdn is the partial change in pressure per distance perpendicular to wind, Pa/m
    Note: Positive dpdn points left of wind direction
    rho is air density, kg/(m^3)
    
    Output:
    Geostrophic wind speed (V), m/s
    """
    return -dpdn / (rho* f)

def geostrophic2(f, dzdn, _g=g):
    """ 
    dzdn is the partial change in geopotential height per distance perpendicular to wind, Pa/m
    Note: Positive dzdn points left of wind direction
    g is gravity, m/s^2
    
    Output:
    Geostrophic wind speed (V), m/s
    """
    return -dzdn * _g / f

def gradient1(f, dpdn, R, rho=1):
    """
    dpdn is the partial change in pressure per distance perpendicular to wind, Pa/m
    R is radius of wind curvature, m
    Note: Positive dpdn and R point left of wind direction
    rho is air density, kg/(m^3)
    
    Output:
    Gradient wind speed (V), m/s
    """
    temp1 = -f * R/2
    temp2 = (f**2 * R**2 / 4 - R * dpdn / rho)**(1/2)
    return temp1 + np.sign(R) * np.sign(dpdn) * temp2

def gradient2(f, dzdn, R, _g=g):
    """
    dzdn is the partial change in geopotential height per distance perpendicular to wind, Pa/m
    R is radius of wind curvature, m
    Note: Positive dzdn and R point left of wind direction
    g is gravity, m/s^2
    
    Output:
    Gradient wind speed (V), m/s
    """
    temp1 = -f * R/2
    temp2 = (f**2 * R**2 / 4 - _g * R * dzdn)**(1/2)
    return temp1 + np.sign(R) * np.sign(dzdn) * temp2
