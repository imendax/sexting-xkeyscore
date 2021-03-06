from ..lib.transformer import Transformer
from ..lib.instruction import Instruction
import csv, os
from LatLon import LatLon

# Tube station data from http://commons.wikimedia.org/wiki/London_Underground_geographic_maps/CSV
class Tube(Transformer):

    __punctuation_characters = ['.', ',', '?', '!', ';', ':', '-']

    def __init__(self):
        self.__import_stations()

    def can_handle_character(self, character):
        return character in Tube.__punctuation_characters

    def can_handle_contact(self, contact, clock):
        return contact.has('tubestation')

    def num_required_contacts(self):
        return 1

    def transform(self, character, contacts, clock):
        contact = contacts[0]
        station = contact.get('tubestation')
        if contact.has_state('lasttube'):
            station = contact.get_state('lasttube')

        stations = self.__nearest_stations(station, len(Tube.__punctuation_characters))
        index = Tube.__punctuation_characters.index(character)
        destination = stations[index]

        contact.set_state('lasttube', destination)
        contact.set_busy_func('tube', lambda clk: clock.jump_forward(12) > clk)

        return Instruction('tube', character, clock, contact, {'from_station': station, 'to_station': destination})

    def __nearest_stations(self, station, qty):
        point1 = self._stations[station]
        distances = {}

        for name in self._stations:
            if name == station:
                continue

            point2 = self._stations[name]
            distance = point1.distance(point2)
            distances[name] = distance

        nearest_stations = sorted(distances, lambda n1, n2: cmp(distances[n1], distances[n2]))
        return nearest_stations[:qty]

    def __import_stations(self):
        self._stations = {}

        with open(os.path.join('resources', 'tube.csv'), 'r') as csvfile:
            rows = csv.reader(csvfile)

            next(rows)
            for row in rows:
                name = row[3]
                lat = float(row[1])
                lng = float(row[2])

                self._stations[name] = LatLon(lat, lng)

