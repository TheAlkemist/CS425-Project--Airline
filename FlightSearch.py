from copy import deepcopy

class Flight:
    def __init__(self,flight_no,airline,frm,to,depart,arrive,price):
        self.flight_no = flight_no
        self.airline = airline
        self.frm = frm
        self.to = to
        self.depart = depart
        self.arrive = arrive
        self.price = price

    def duration(self):
        return self.arrive - self.depart

class Airport:
    def __init__(self, iata):
        self.iata = iata
        self._departing_flights = []

    def add_flight(self,flight):
        assert isinstance(flight,Flight)
        self._departing_flights.append(flight)

    def get_flights(self,after = None,max_price = None):
        if after is None and max_price is None:
            return self._departing_flights
        else:
            tmp = deepcopy(self._departing_flights)

            if after is not None and max_price is not None:
                for f in tmp:
                    if f.depart < after or f.price > max_price:
                        tmp.remove(f)
            elif after is not None:
                for f in tmp:
                    if f.depart < after:
                        tmp.remove(f)
            else:
                for f in tmp:
                    if f.price > max_price:
                        tmp.remove(f)
            return tmp

class Itinerary:
    def __init__(self,from_iata, to_iata):
        self.dept_time = None
        self.arrival_time = None
        self.from_iata = from_iata
        self.to_iata = to_iata
        self.duration = 0
        self.connections = 0
        self.total_price = 0
        self.been_to = set()
        self.complete = False
        self.last_time = None
        self.last_airport = None
        self.flights = []

    def add_flight(self,flight):
        assert not self.complete
        assert not flight.to in self.been_to
        if not self.last_time is None and self.last_time > flight.depart:
            raise Exception('Cannot board flight that left before arrival!')
        if self.last_airport is not None and self.last_airport != flight.frm:
            raise Exception('From airport does not match last airport in itinerary!')
        if self.dept_time is None:
            self.dept_time = flight.depart
            self.been_to.add(flight.frm)
        self.last_airport = flight.to
        if flight.to == self.to_iata:
            self.complete = True
        self.been_to.add(flight.to)
        self.arrival_time = flight.arrive
        self.duration += flight.duration()
        self.connections += 1
        self.total_price += flight.price
        self.flights.append(flight)

    def evaluate_flight(self,flight,max_price = None,max_connections = None,max_duration = None):
        if self.complete or flight.to in self.been_to or (not self.last_time is None and self.last_time > flight.depart):
            return False

        if max_price is not None and max_price > flight.price + self.total_price:
            return False

        if max_connections is not None and self.connections + 1 > max_connections:
            return False

        if max_duration is not None and flight.duration() + self.duration > max_duration:
            return False

        return True

    def copy(self):
        tmp = Itinerary(self.from_iata,self.to_iata)
        for flight in self.flights:
            tmp.add_flight(flight)



def search_flights(network,dept_date,from_iata,to_iata,max_price = None,max_connections=None,max_duration=None):
    itinerary_by_last_loc = {}
    locations = []
    start = network[from_iata]
    complete_itineraries = []

    #prepopulate itineraries
    for flight in start.get_flights(dept_date, max_price):
        itinerary = Itinerary(from_iata,to_iata)
        if from_iata not in itinerary_by_last_loc:
            itinerary_by_last_loc[from_iata] = []
        itinerary_by_last_loc[from_iata].append(itinerary)


    locations.append(start)

    while len(locations) > 0:
        curr_loc = locations.pop(-1)
        dept_flights = curr_loc.get_flights(dept_date,max_price)
        n_flights = len(dept_flights)
        itins = itinerary_by_last_loc[curr_loc.iata]
        for i,flight in enumerate( dept_flights):
            if i == n_flights - 1:
                while len(itins) > 0:
                    iten = itins.pop()
                    if iten.complete:
                        complete_itineraries.append(iten)
                    elif iten.evaluate_flight(flight,max_price = max_price,max_connections = max_connections,max_duration = max_duration):
                        iten.add_flight(flight)
                        if flight.to not in itinerary_by_last_loc:
                            itinerary_by_last_loc[flight.to] = []
                        itinerary_by_last_loc[flight.to].append(iten)
            else:
                for iten in itins:
                    if iten.evaluate_flight(flight,max_price = max_price,max_connections = max_connections,max_duration = max_duration):
                        new_iten = iten.copy()
                        new_iten.add_flight(flight)
                        if flight.to not in itinerary_by_last_loc:
                            itinerary_by_last_loc[flight.to] = []
                        itinerary_by_last_loc[flight.to].append(new_iten)
            if flight.to in itinerary_by_last_loc and len(itinerary_by_last_loc[flight.to]) > 0:
                locations.append(network[flight.to])

    return complete_itineraries

