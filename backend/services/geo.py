import math
from typing import Optional, Tuple

def haversine_distance(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float]
) -> Optional[float]:
    """
    Calculate the great-circle distance between two points on the Earth 
    using the Haversine formula. Returns distance in kilometers (km).
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    try:
        # Convert decimal degrees to radians
        rad_lat1, rad_lon1, rad_lat2, rad_lon2 = map(
            math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)]
        )

        # Haversine formula
        dlat = rad_lat2 - rad_lat1
        dlon = rad_lon2 - rad_lon1

        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        r_km = 6371.0
        
        distance = r_km * c
        return round(distance, 2)
    except (ValueError, TypeError):
        return None
