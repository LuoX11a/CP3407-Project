"""
Carpark rate information and EV charging station lookup.

Rate data is derived from HDB/URA published schedules:
- CBD / central area: higher rates (short-term parking)
- Suburban / HDB estates: lower rates

EV charging data: sourced from LTA open dataset of charging stations.
Currently a curated list of known EV-equipped carparks; future integration
with LTA Dynamic Datamall API will provide live data.

Sources:
- HDB parking rates: https://www.hdb.gov.sg/car-parks/short-term-parking
- URA parking rates: https://www.ura.gov.sg/parking
- LTA EV charging: https://www.lta.gov.sg/ev charging
"""

# Known EV-equipped carparks (HDB carparks with charging stations)
# Sourced from LTA EV charging point locations dataset
EV_CARPARKS: set[str] = {
    # Ang Mo Kio
    "A11", "A20", "A35",
    # Bedok
    "B28", "BE10",
    # Bishan
    "B12", "B15",
    # Bukit Batok
    "BBM2",
    # Bukit Panjang
    "BP5",
    # Choa Chu Kang
    "CK15",
    # Clementi
    "CL1", "CL5",
    # Geylang
    "GL3",
    # Hougang
    "HG55",
    # Jurong East
    "J66M", "GTRM",
    # Jurong West
    "JW5",
    # Kallang
    "KL1",
    # Marine Parade
    "MP1M",
    # Pasir Ris
    "PR2",
    # Punggol
    "PG1",
    # Queenstown
    "QT2",
    # Sembawang
    "SB42",
    # Sengkang
    "SK35", "SK74",
    # Tampines
    "TM11", "TP3",
    # Toa Payoh
    "TPY5",
    # Woodlands
    "W44", "W101", "W187", "W56L",
    # Yishun
    "Y25M", "NHC",
    # Central / CBD area carparks
    "L7", "L8",
    # Bukit Timah
    "TH34", "TH35",
    # Commercial
    "ACE",
}


def get_hourly_rate(carpark_id: str, lat: float = 0, lng: float = 0) -> str:
    """Return a human-readable hourly rate string for a carpark.

    Rate tiers are approximate, based on HDB published schedules (2025):
    - CBD / central: $1.20–$2.40/hr (short-term)
    - Non-CBD HDB: $0.60–$1.20/hr
    - Shopping mall: $1.00–$2.00/hr (private, not HDB)

    A future API integration with URA/HDB rate endpoints would replace
    this lookup with actual per-carpark rate data.
    """
    # Central area (high-rate zone)
    central_area = lat > 1.275 and lat < 1.320 and lng > 103.82 and lng < 103.87

    if central_area:
        return "$2.00/hr"
    elif carpark_id in EV_CARPARKS:
        return "$1.20/hr"
    else:
        return "$0.80/hr"


def has_ev_charging(carpark_id: str) -> bool:
    """Check if a carpark has EV charging stations."""
    return carpark_id in EV_CARPARKS
