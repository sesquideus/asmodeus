import copy
from physics import radiometry


class Frame:
    def __init__(self, meteor):
        self.timestamp          = meteor.timestamp
        self.time               = meteor.time
        self.position           = copy.copy(meteor.position)
        self.velocity           = copy.copy(meteor.velocity)
        self.speed              = self.velocity.norm()
        self.luminous_power     = meteor.luminous_power
        self.absolute_magnitude = meteor.absolute_magnitude
        self.mass               = meteor.mass
        self.mass_initial       = meteor.mass_initial
        self.density            = meteor.density
        self.ablation_heat      = meteor.ablation_heat
        self.entry_angle        = meteor.entry_angle

    def __str__(self):
        return f"<MeteorFrame: {self.position}, {self.velocity:.0f} m/s, {self.velocity.norm():6.0f} m/s, {self.luminousPower:e} W>"
