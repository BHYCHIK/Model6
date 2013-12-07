# -*- coding: utf-8 -*-
import random
import math


class QueueError(Exception): pass

class PetrolStation(object):
    class State(object):
        freed = 0
        filling = 1
        complete = 2

    def __init__(self, expected_value, halfrange, row_id, station_id, logger):
        self._state = PetrolStation.State.freed
        self._car = None
        self._expected_value = expected_value
        self._halfrange = halfrange
        self._time_in_complete = 0
        self._time_in_freed = 0
        self._time_in_filling = 0
        self._last_known_time = 0
        self._waiting_event = None
        self._row_id = row_id
        self._station_id = station_id
        self._logger = logger

    def get_state(self):
        return self._state

    def get_event(self):
        return self._waiting_event

    def next_step(self, model_time, car=None):
        if self.get_state() == PetrolStation.State.freed:
            self._state = PetrolStation.State.filling
            self._time_in_freed = self._time_in_freed + (model_time - self._last_known_time)
            self._waiting_event = self._generate_event(model_time)
            self._car = car
            self._car.set_start_filling(model_time)
        elif self.get_state() == PetrolStation.State.filling:
            self._waiting_event = None
            self._state = PetrolStation.State.complete
            self._time_in_filling = self._time_in_filling + (model_time - self._last_known_time)
            self._car.set_stop_filling(model_time)
        elif self.get_state() == PetrolStation.State.complete:
            self._waiting_event = None
            self._state = PetrolStation.State.freed
            self._car.set_left(model_time)
            self._car = None
            self._time_in_complete = self._time_in_complete + (model_time - self._last_known_time)

        self._last_known_time = model_time

    def _generate_time(self):
        return random.uniform(self._expected_value - self._halfrange, self._expected_value + self._halfrange)

    def _generate_event(self, model_time):
        return ProcessingEvent(self._generate_time() + model_time, self._row_id, self._station_id)


class PetrolStationsRow(object):
    def __init__(self, PetrolStationsNum, expected_value, halfrange, row_id, logger):
        self._stations = [PetrolStation(expected_value, halfrange, row_id, station_id, logger) for station_id in
                          range(0, PetrolStationsNum)]
        self._queue = []
        self._logger = logger

    def __getitem__(self, item):
        return self._stations[item]

    def find_nearest_event(self):
        first = True
        selected = None
        for station in self._stations:
            if station.get_state() == PetrolStation.State.filling:
                if first or selected.get_planned_time() > station.get_event().get_planned_time():
                    selected = station.get_event()
                first = False
        return selected

    def get_queue_size(self):
        return len(self._queue)

    def _add_to_filling(self, model_time, car):
        pos = -1
        for station in self._stations:
            if station.get_state() == PetrolStation.State.freed:
                pos = pos + 1
            else:
                break
        if pos == -1:
            return False
        self[pos].next_step(model_time, car)
        return True

    def _try_to_get_from_queue(self, model_time):
        rc = True
        while rc and len(self._queue) > 0:
            car_from_queue = self._queue.pop()
            rc = self._add_to_filling(model_time, car_from_queue)
            if not rc:
                self._queue.append(car_from_queue)

    def finish_filling(self, model_time, event, complete):
        station_id = event.get_station_id()
        self[station_id].next_step(model_time)
        for i in range(len(self._stations) - 1, -1, -1):
            if self[i].get_state() == PetrolStation.State.complete:
                complete = complete + 1
                self[i].next_step(model_time)
            elif self[i].get_state() == PetrolStation.State.freed:
                continue
            else:
                break
        self._try_to_get_from_queue(model_time)
        return complete

    def accept_to_queue(self, model_time, car):
        self._queue.insert(0, car)
        self._try_to_get_from_queue(model_time)

class ModelEvent(object):
    def __init__(self, time):
        self._time = time

    def get_planned_time(self):
        return self._time


class GenerationEvent(ModelEvent):
    def __init__(self, time, car_id):
        super(GenerationEvent, self).__init__(time)
        self._car_id = car_id
        self._car_made = False

    def make_car(self):
        if self._car_made:
            assert 0
        return Car(self._car_id, self.get_planned_time())

    def __repr__(self):
        return "Generate at %f" % self.get_planned_time()

class ProcessingEvent(ModelEvent):
    def __init__(self, time, row_id, station_id):
        super(ProcessingEvent, self).__init__(time)
        self._row_id = row_id
        self._station_id = station_id

    def get_row_id(self):
        return self._row_id

    def get_station_id(self):
        return self._station_id

    def __repr__(self):
        return "Process at %f" % self.get_planned_time()

class Car(object):
    def __init__(self, id, entered):
        self._id = id
        self._entered = entered
        self._start_filling = -1
        self._end_filling = -1
        self._left = -1

    def set_start_filling(self, t):
        self._start_filling = t

    def set_stop_filling(self, t):
        self._end_filling = t

    def set_left(self, t):
        self._left = t

    def __repr__(self):
        return "Машина %d приехала в %f, начала заправляться в %f, закончила заправляться в %f, уехала в %f" % \
            (self._id, self._entered, self._start_filling, self._end_filling, self._left)

    def __str__(self):
        return "Машина %d приехала в %f, начала заправляться в %f, закончила заправляться в %f, уехала в %f" % \
            (self._id, self._entered, self._start_filling, self._end_filling, self._left)

class Generator(object):
    def __init__(self, excepted_value):
        self._expected_value = excepted_value
        self._car_id = -1

    def generate_time(self):
        return (0 - self._expected_value) * math.log(1 - random.random())

    def generate_event(self, model_time):
        self._car_id = self._car_id + 1
        return GenerationEvent(self.generate_time() + model_time, self._car_id)


class Model(object):
    def __init__(self, gen_expected_value, process_expected_value, process_halfrange, petrol_stations_num, rows_num):
        self._logger = []
        self._generator = Generator(gen_expected_value)
        self._rows = [PetrolStationsRow(petrol_stations_num, process_expected_value, process_halfrange, row_id, self._logger) for row_id in range(0, rows_num)]
        self._model_time = 0
        self._planned_generation_event = self._generator.generate_event(self._model_time)
        self._cars = []

    def find_nearest_event(self):
        first = True
        selected = None
        for row in self._rows:
            if not (row is None):
                ev = row.find_nearest_event()
                if ev is None:
                    continue
                if first or selected.get_planned_time() > ev.get_planned_time():
                    selected = ev
                first = False
        if selected is None:
            print("NO TO PROCESS")
            selected = self._planned_generation_event
        else:
            print(selected)
            selected = self._planned_generation_event if self._planned_generation_event.get_planned_time() < selected.get_planned_time() else selected
        return selected

    def handle_event(self, complete, ev):
        #print(ev)
        if isinstance(ev, GenerationEvent):
            car = ev.make_car()
            self._cars.append(car)
            min_queue = self._rows[0].get_queue_size()
            min_queue_index = 0
            for i in range(1, len(self._rows)):
                if min_queue > self._rows[i].get_queue_size():
                    min_queue = self._rows[i].get_queue_size()
                    min_queue_index = i
            self._rows[min_queue_index].accept_to_queue(self._model_time, car)
            self._planned_generation_event = self._generator.generate_event(self._model_time)
        elif isinstance(ev, ProcessingEvent):
            row_id = ev.get_row_id()
            complete = self._rows[row_id].finish_filling(self._model_time, ev, complete)
        else:
            assert 0
        return complete

    def run_event(self, to_process):
        processed = 0

        while processed < to_process:
            ev = self.find_nearest_event()
            if ev.get_planned_time() < self._model_time:
                assert 0
            self._model_time = ev.get_planned_time()
            processed = self.handle_event(processed, ev)
        return self._model_time

m = Model(2, 1, 0, 4, 1)
print(m.run_event(30))
for car in m._cars:
    print(car)
    if False or car._end_filling != car._left:
        print(car)
