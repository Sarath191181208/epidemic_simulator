from dataclasses import dataclass
from enum import Enum

Row = int 
Col = int
PlaceLoc = tuple[Row, Col]
Time = int
DaySchedule = list[tuple[PlaceLoc, Time]]

class Day(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5

class PersonState(Enum):
    Staying = 0
    Moving = 1


@dataclass
class TimeTable: 
    Monday: DaySchedule
    Tuesday: DaySchedule
    Wednesday: DaySchedule
    Thursday: DaySchedule
    Friday: DaySchedule 
    Saturday: DaySchedule

@dataclass
class Person: 
    timetable: TimeTable
    loc: PlaceLoc
    current_idx: int = 0
    time: Time = 0
    state: PersonState = PersonState.Staying

    def get_src(self, day: Day) -> PlaceLoc:
        return self.get_day_schedule(day)[self.current_idx][0]

    def update(self, day: Day):
        if self.state == PersonState.Staying:
            self.time += 1
            t = self.get_day_schedule(day)[self.current_idx][1]
            INFINITY = -1
            if t != INFINITY and self.time >= t:
                self.state = PersonState.Moving
                self.time = 0
        elif self.state == PersonState.Moving:
            if self.loc == self.get_dest(day):
                self.state = PersonState.Staying
                self.current_idx += 1
                self.current_idx %= len(self.get_day_schedule(day))

    def get_dest(self, day: Day) -> PlaceLoc:
        if self.current_idx + 1 >= len(self.get_day_schedule(day)):
            return self.loc
        return self.get_day_schedule(day)[self.current_idx + 1][0]

    def get_day_schedule(self, day: Day) -> DaySchedule:
        if day == Day.Monday:
            return self.timetable.Monday 
        elif day == Day.Tuesday: 
            return self.timetable.Tuesday 
        elif day == Day.Wednesday: 
            return self.timetable.Wednesday 
        elif day == Day.Thursday: 
            return self.timetable.Thursday 
        elif day == Day.Friday: 
            return self.timetable.Friday 
        elif day == Day.Saturday: 
            return self.timetable.Saturday

