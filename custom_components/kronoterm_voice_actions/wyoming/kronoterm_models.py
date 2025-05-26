from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


@dataclass
class KronotermAction:
    """Data model that defines the structure of a request for an action to execute on the Kronoterm heat pump."""
    action: str
    parameters: Dict[str, Any]


class RegisterAddress(Enum):
    """Modbus register addresses"""

    def to_int(self) -> int:
        return self.value

    SYSTEM_STATUS                        = 2000  # Delovanje sistema
    OPERATING_MODE                       = 2001  # Funkcija delovanja
    ADDITIONAL_ENGAGERS                  = 2002  # Dodatni vklopi
    RESERVE_SOURCE                       = 2003  # Rezervni vir
    ALTERNATIVE_SOURCE                   = 2004  # Alternativni vir

    OPERATING_REGIME                     = 2007  # Režim delovanja
    PROGRAM_MODE                         = 2008  # Program delovanja

    DHW_QUICK_HEAT                       = 2010  # Hitro segrevanje sanitarne vode
    DEFROST_MODE                         = 2011  # Odtaljevanje
    SYSTEM_ON                            = 2012  # Vklop sistema
    PROGRAM_SELECT                       = 2013  # Izbira programa delovanja
    SYSTEM_TEMP_CORRECTION               = 2014  # Korekcija temperature sistema
    DHW_QUICK_HEAT_ENABLE                = 2015  # Vklop hitrega segrevanja sanitarne vode
    ADDITIONAL_SOURCE_ENABLE             = 2016  # Vklop dodatnega vira
    MODE_SWITCH                          = 2017  # Preklop režima
    RESERVE_SOURCE_ENABLE                = 2018  # Vklop rezervnega vira

    DHW_TARGET_TEMP                      = 2023  # Želena temperatura sanitarne vode
    DHW_CURRENT_TARGET_TEMP              = 2024  # Trenutna želena temperatura sanitarne vode
    DHW_MODE_SELECT                      = 2026  # Izbira delovanja sanitarne vode
    DHW_SCHEDULE_STATUS                  = 2027  # Status delovanja sanitarne vode po urniku

    LOOP_1_MODE_SELECT                   = 2042  # Izbira delovanja krog 1
    LOOP_1_SCHEDULE_STATUS               = 2044  # Status delovanja kroga 1 po urniku
    LOOP_2_TARGET_ROOM_TEMP              = 2049  # Želena temperatura prostora ogrevalnega kroga 2

    LOOP_2_CURRENT_TARGET_ROOM_TEMP      = 2051  # Trenutna želena temperatura prostora 2. kroga
    LOOP_2_MODE_SELECT                   = 2052  # Izbira delovanja ogrevalni krog 2
    LOOP_2_SCHEDULE_STATUS               = 2054  # Status delovanja kroga 2 po urniku
    LOOP_3_ROOM_TARGET_TEMP              = 2059  # Želena temperatura prostora ogrevalnega kroga 3

    LOOP_3_TARGET_ROOM_TEMP              = 2061  # Trenutna želena temperatura ogrev. kroga 3
    LOOP_3_MODE_SELECT                   = 2062  # Izbira delovanja ogrevalni krog 3
    LOOP_3_SCHEDULE_STATUS               = 2064  # Status delovanja krog 3 po urniku
    LOOP_3_PUMP_STATUS                   = 2065  # Status obtočne črpalke krog 3
    LOOP_3_THERMOSTAT_STATUS             = 2066  # Status termostata krog 3
    LOOP_3_ECO_OFFSET                    = 2067  # Odmik v eco načinu krog 3
    LOOP_3_COMFORT_OFFSET                = 2068  # Odmik v comfort načinu krog 3
    LOOP_4_ROOM_TARGET_TEMP              = 2069  # Želena temperatura prostora ogrevalnega kroga 4

    LOOP_4_TARGET_ROOM_TEMP              = 2071  # Trenutna želena temperatura prostora ogrev. kroga 4
    LOOP_4_MODE_SELECT                   = 2072  # Izbira delovanja ogrevalni krog 4
    LOOP_4_SCHEDULE_STATUS               = 2074  # Status delovanja krog 4 po urniku
    LOOP_4_PUMP_STATUS                   = 2075  # Status obtočne črpalke krog 4
    LOOP_4_THERMOSTAT_STATUS             = 2076  # Status termostata krog 4
    LOOP_4_ECO_OFFSET                    = 2077  # Odmik v eco načinu krog 4
    LOOP_4_COMFORT_OFFSET                = 2078  # Odmik v comfort načinu krog 4
    LOOP_4_TARGET_TEMP2                  = 2079  # Želena temperatura ogrevalnega kroga 4

    HP_INLET_TEMP                        = 2101  # Temperatura povratnega voda
    DHW_TEMP                             = 2102  # Temperatura sanitarne vode
    OUTSIDE_TEMP                         = 2103  # Zunanja temperatura
    HP_OUTLET_TEMP                       = 2104  # Temperatura dviznega voda
    EVAPORATING_TEMP                     = 2105  # Temperatura uparjanja
    COMPRESSOR_TEMP                      = 2106  # Temperatura kompresorja
    ALT_SOURCE_TEMP                      = 2107  # Temperatura altern. vira

    POOL_TEMP_SENSOR                     = 2109  # Temperatura bazena
    LOOP_2_TEMP_SENSOR                   = 2110  # Temperatura 2. kroga
    LOOP_3_TEMP_SENSOR                   = 2111  # Temperatura 3. kroga
    LOOP_4_TEMP_SENSOR                   = 2112  # Temperatura 4. kroga
    FAULT_ACTIVE_SENSOR                  = 2113  # Napaka aktivna
    FAULT_1_SENSOR                       = 2114  # Napake 1
    FAULT_2_SENSOR                       = 2115  # Napake 2

    LOOP_1_CURRENT_TARGET_TEMP           = 2128  # Trenutna zelena temperatura 1. kroga
    CURRENT_ELECTRIC_POWER               = 2129  # Trenutna električna poraba
    LOOP_1_TEMP_SENSOR                   = 2130  # Temperatura 1. kroga

    LOOP_1_THERMOSTAT_SETPOINT           = 2160  # Temperatura termostata 1. ogrevalnega kroga
    LOOP_2_THERMOSTAT_SETPOINT           = 2161  # Temperatura termostata 2. ogrevalnega kroga
    LOOP_3_THERMOSTAT_SETPOINT           = 2162  # Temperatura termostata 3. ogrevalnega kroga
    LOOP_4_THERMOSTAT_SETPOINT           = 2163  # Temperatura termostata 4. ogrevalnega kroga

    LOOP_1_TARGET_ROOM_TEMP              = 2187  # Želena temperatura prostora 1. kroga
    LOOP_1_TARGET_TEMP                   = 2188  # Trenutna zelena temperatura ogrev. krog 2
    ROOM_2_CURRENT_TEMP                  = 2189  # Trenutna zelena temperatura ogrev. krog 3
    ROOM_3_CURRENT_TEMP                  = 2190  # Trenutna zelena temperatura ogrev. krog 4
    LOOP_1_CURRENT_TARGET_ROOM_TEMP      = 2191  # Trenutna zelena temperatura prostor 1
    REMOTE_ENABLE                        = 2197  # Oddaljen vklop funkcij [0=izklop,1=vklop]

    THERMAL_DISINF_MODE                  = 2301  # Termična dezinfekcija [0=off,1=on]
    THERMAL_DISINF_TEMP_SET              = 2302  # Termična dezinfekcija: Želena temperatura
    THERMAL_DISINF_PERIOD                = 2303  # Termična dezinfekcija: Perioda dezinfekcije [day]
    THERMAL_DISINF_START_MIN             = 2304  # Termična dezinfekcija: Začetek [minute]
    SOLAR_BUFFER_TARGET_TEMP             = 2305  # Solar / biomasa: Želena temperatura zalogovnika
    SOLAR_BOILER_TARGET_TEMP             = 2306  # Solar / biomasa: Želena temperatura bojlerja
    SCREED_DRYING_MODE                   = 2307  # Sušenje estrihov [0=izklop,1=vklop]

    BUFFER_CURVE_POINT1                  = 2308  # Krivulja zalogovnika pri prvi točki
    LOOP_1_CURVE_POINT1                  = 2309  # Krivulja krog 1 pri prvi točki
    LOOP_2_CURVE_POINT1                  = 2310  # Krivulja krog 2 pri prvi točki
    LOOP_3_CURVE_POINT1                  = 2311  # Krivulja krog 3 pri prvi točki
    LOOP_4_CURVE_POINT1                  = 2312  # Krivulja krog 4 pri prvi točki
    BUFFER_CURVE_POINT2                  = 2313  # Krivulja zalogovnika pri drugi točki
    LOOP_1_CURVE_POINT2                  = 2314  # Krivulja krog 1 pri drugi točki
    LOOP_2_CURVE_POINT2                  = 2315  # Krivulja krog 2 pri drugi točki
    LOOP_3_CURVE_POINT2                  = 2316  # Krivulja krog 3 pri drugi točki
    LOOP_4_CURVE_POINT2                  = 2317  # Krivulja krog 4 pri drugi točki

    COMPRESSOR_STATUS                    = 2318  # Status kompresorjev [bit-mask]
    COMPRESSOR_PROTECTION_STATUS         = 2319  # Status kompresorja [varovanje/zagon]
    LOOP_1_ADAPTIVE_CURVE_ENABLE         = 2320  # Adaptivna krivulja krog 1 [0/1]
    LOOP_2_ADAPTIVE_CURVE_ENABLE         = 2321  # Adaptivna krivulja krog 2 [0/1]
    LOOP_3_ADAPTIVE_CURVE_ENABLE         = 2322  # Adaptivna krivulja krog 3 [0/1]
    LOOP_4_ADAPTIVE_CURVE_ENABLE         = 2323  # Adaptivna krivulja krog 4 [0/1]
    HEAT_SYSTEM_FILLING                  = 2324  # Polnjenje ogrevalnega sistema [0/1]

    HEAT_SYSTEM_PRESSURE_SETPOINT        = 2325  # Nastavitev tlaka ogrevalnega sistema
    HEAT_SYSTEM_PRESSURE                 = 2326  # Tlak ogrevalnega sistema
    CURRENT_HP_LOAD                      = 2327  # Trenutna obremenitev TČ [%]
    CURRENT_BUFFER_LOAD                  = 2328  # (reserved)
    CURRENT_POWER_CONSUMPTION            = 2329  # Trenutna grelna/hladilna moč [W]

    SEC_MONO_SW_ALARM_1                  = 2330
    SEC_MONO_SW_ALARM_2                  = 2331
    SEC_MONO_HW_ALARM_1                  = 2332
    SEC_MONO_HW_ALARM_2                  = 2333
    SEC_MONO_VSS_ALARM_1                 = 2334
    SEC_MONO_VSS_ALARM_2                 = 2335
    SEC_MONO_VSS_ALARM_3                 = 2336
    SEC_MONO_VSS_ALARM_4                 = 2337
    SEC_MONO_VSS_ALARM_5                 = 2338
    ALARM_ADDITIONAL_1                   = 2339
    ALARM_ADDITIONAL_2                   = 2340
    WARNING_ADDITIONAL                   = 2341

    PUMPED_WATER_VOLUME_HIGH             = 2349  # Prečrpana podtalnica (high) [m³]
    PUMPED_WATER_VOLUME_LOW              = 2350  # Prečrpana podtalnica (low) [m³]
    CASCADE_STATUS                       = 2360  # Status delovanja kaskad [bit-mask]
    ENERGY_ELECTRIC_HIGH                 = 2361  # El. energija ogrevanje+san. voda (high)[kWh]
    ENERGY_ELECTRIC_LOW                  = 2362  # El. energija ogrevanje+san. voda (low) [kWh]
    ENERGY_HEAT_HIGH                     = 2363  # Toplotna energija ogrevanje+san. voda (high) [kWh]
    ENERGY_HEAT_LOW                      = 2364  # Toplotna energija ogrevanje+san. voda (low) [kWh]

    COP                                  = 2371  # COP [×0.01]
    SCOP                                 = 2372  # SCOP [×0.01]
