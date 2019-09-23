import copy
from physics import radiometry


class Frame:
    def __init__(self, meteor):
        self.timestamp          = meteor.timestamp
        self.time               = meteor.time
        self.position           = copy.copy(meteor.position)
        self.velocity           = copy.copy(meteor.velocity)
        self.speed              = self.velocity.norm()
        self.luminousPower      = meteor.luminousPower
        self.absoluteMagnitude  = radiometry.absoluteMagnitude(self.luminousPower)
        self.mass               = meteor.mass
        self.massInitial        = meteor.massInitial
        self.density            = meteor.density
        self.entryAngle         = meteor.entryAngle

    def __str__(self):
        return f"<MeteorFrame: {self.position}, {self.velocity:.0f} m/s, {self.velocity.norm():6.0f} m/s, {self.luminousPower:e} W>"
