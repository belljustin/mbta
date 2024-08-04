import datetime
import logging
from typing import List, Mapping, Optional

import pymbta3

from mbta.config import config

logger = logging.getLogger(__name__)

class Arrival:
    headsign: str
    countdown: str

    def __init__(self, headsign: str, countdown: str):
        self.headsign = headsign
        self.countdown = countdown

class Board:
    route_name: str
    stop_name: str
    arrivals: List[Arrival]

    def __init__(self, route_name: str, stop_name: str, arrivals: List[Arrival]):
        self.route_name = route_name
        self.stop_name = stop_name
        self.arrivals = arrivals

def get_board(route_id: str, stop_id: str):
    route = get_route(route_id)
    stop = get_stop(stop_id)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    arrivals: List[Arrival] = []
    for prediction in get_predictions(route_id, stop_id):
        if prediction.is_valid(now):
            arrival = Arrival(prediction.headsign, prediction.countdown(now))
            arrivals.append(arrival)
    
    return Board(route.name, stop, arrivals)


class Vehicle:
    id: str
    current_status: str
    current_stop_sequence: int

    def __init__(self, current_status: str, current_stop_sequence: int):
        self.current_status = current_status
        self.current_stop_sequence = current_stop_sequence

    def is_stopped_at(self, current_stop_sequence: int) -> bool:
        return self.current_status == "STOPPED_AT" and self.current_stop_sequence == current_stop_sequence

class Prediction:
    _ERROR = "ERR"
    _BOARDING = "BRD"
    _ARRIVING = "ARR"
    _APPROACHING = "1 min"
    _FAR = "20+ min"

    stop_sequence: int
    status: str
    departure_time: datetime.datetime
    headsign: str
    vehicle: Optional[Vehicle]

    def __init__(self, stop_sequence: int, status: str, departure_time: datetime.datetime, headsign: str, vehicle: Optional[Vehicle]):
        self.stop_sequence = stop_sequence
        self.status = status
        self.departure_time = departure_time
        self.headsign = headsign
        self.vehicle = vehicle
    
    def is_valid(self, now: datetime.datetime) -> bool:
        if self.departure_time is None:
            return False
        
        dt = self.departure_time - now
        return dt.total_seconds() >= 0
        
    def countdown(self, now: datetime.datetime) -> str:
        if self.status:
            return self.status
        
        if not self.is_valid(now):
            return Prediction._ERROR
        seconds = (self.departure_time - now).total_seconds()
        
        if seconds <= 90 and self.vehicle is not None and self.vehicle.is_stopped_at(self.stop_sequence):
            return Prediction._BOARDING
        
        if seconds <= 30:
            return Prediction._ARRIVING
        
        if seconds <= 60:
            return Prediction._APPROACHING

        minutes = round(seconds / 60)
        if minutes > 20:
            return Prediction._FAR
        
        return f"{minutes} min"

def get_predictions(route_id: str, stop_id: str) -> List[Prediction]:
    pd = pymbta3.Predictions(key=config.apikey)

    res = pd.get(route=route_id, stop=stop_id, include=["vehicle", "trip"])
    logger.debug("get_predictions: %s", res)
    if 'errors' in res and len(res['errors']):
        raise RuntimeError(f"an error occured while getting predictions: {res['errors']}.")
    
    if len(res['data']) == 0:
        return []

    vehicles: Mapping[str, Vehicle] = {}
    for included in res['included']:
        if included['type'] != 'vehicle':
            continue

        attributes = included['attributes']
        vehicles[included['id']] = Vehicle(attributes['current_status'], attributes['current_stop_sequence'])

    trips: Mapping[str, str] = {}
    for included in res['included']:
        if included['type'] != 'trip':
            continue

        attributes = included['attributes']
        trips[included['id']] = attributes['headsign']
    

    predictions: List[Prediction] = []
    for data in res['data']:
        attrs = data['attributes']

        if _isInList(attrs['schedule_relationship'], ['CANCELLED', 'NO_DATA', 'SKIPPED']):
            continue

        departure_time_str = attrs['departure_time']
        if departure_time_str == None or departure_time_str == '':
            continue
        departure_time = datetime.datetime.strptime(departure_time_str, "%Y-%m-%dT%H:%M:%S%z")

        vehicle: Optional[Vehicle] = None
        vehicle_data = data['relationships']['vehicle']['data']
        if vehicle_data is not None:
            vehicle_id = vehicle_data['id']
            vehicle = vehicles[vehicle_id]

        trip_id = data['relationships']['trip']['data']['id']
        headsign = trips[trip_id]

        predictions.append(Prediction(attrs['stop_sequence'], attrs['status'], departure_time, headsign, vehicle))

    return predictions

class Route:
    _TYPE_BUS = 3

    id: str
    name: str
    direction_destinations: List[str]

    def __init__(self, id: str, name: str, direction_destinations: List[str]):
        self.id = id
        self.name = name
        self.direction_destinations = direction_destinations

def get_route(id: str) -> Route:
    rt = pymbta3.Routes(key=config.apikey)
    res = rt.get(id=id)
    logger.debug("get_route: %s", res)
    if 'errors' in res and len(res['errors']):
        raise RuntimeError(f"an error occured while getting predictions: {res['errors']}")
    
    if len(res['data']) != 1:
        raise RuntimeError(f"unexpected number of routes returned: expected 1 got %d", len(res['data']))


    attributes = res['data'][0]['attributes']

    # The bus route names are way too long, so just use the short names like '83'
    name_attribute_key = 'short_name' if attributes['type'] == Route._TYPE_BUS else 'long_name'

    return Route(id, attributes[name_attribute_key], attributes['direction_destinations'])

def get_stop(id: str) -> str:
    st = pymbta3.Stops(key=config.apikey)
    res = st.get(id=id)
    logger.debug("get_stop: %s", res)
    if 'errors' in res and len(res['errors']):
        raise RuntimeError(f"an error occured while getting predictions: {res['errors']}")
    
    if len(res['data']) != 1:
        raise RuntimeError(f"unexpected number of routes returned: expected 1 got %d", len(res['data']))

    attributes = res['data'][0]['attributes']
    return attributes['name']


def _isInList(val: str, lst: List[str]) -> bool:
    return any(val is x for x in lst)
