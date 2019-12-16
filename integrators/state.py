import numbers

from physics import coord


class State:
    def __init__(self, position, velocity, log_mass):
        self.position = position
        self.velocity = velocity
        self.log_mass = log_mass

    def __str__(self):
        return f"{self.position:w} {self.velocity:s} {self.log_mass:6.2g}"

    def __add__(self, diff):
        return State(
            self.position + diff.drdt,
            self.velocity + diff.dvdt,
            self.log_mass + diff.dmdt,
        )


class Diff:
    def __init__(self, drdt, dvdt, dmdt):
        self.drdt = drdt
        self.dvdt = dvdt
        self.dmdt = dmdt

    ### Diff arithmetics
    def __add__(self, other):
        return Diff(
            self.drdt + other.drdt,
            self.dvdt + other.dvdt,
            self.dmdt + other.dmdt,
        )

    __radd__ = __add__

    def __sub__(self, other):
        return Diff(
            self.drdt - other.drdt,
            self.dvdt - other.dvdt,
            self.dmdt - other.dmdt,
        )

    def __mul__(self, number):
        return Diff(
            number * self.drdt,
            number * self.dvdt,
            number * self.dmdt,
        )

    __rmul__ = __mul__

    def __truediv__(self, number):
        if not isinstance(number, numbers.Number):
            raise TypeError(f"Diff: Can only divide by a number, not {type(number)}")
        return Diff(
            self.drdt / number,
            self.dvdt / number,
            self.dmdt / number,
        )

    ### Class methods
    @classmethod
    def zero(cls):
        return Diff(coord.Vector3D(0, 0, 0), coord.Vector3D(0, 0, 0), 0)

    ### Representations
    def __str__(self):
        return f"{self.drdt} {self.dvdt} {self.dmdt}"

    ### Logic
    def norm(self):
        return self.drdt.norm(), self.dvdt.norm(), self.dmdt**2

