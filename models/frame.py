import copy


class Frame:
    def __init__(self, meteor):
        self.timestamp      = meteor.timestamp
        self.position       = copy.copy(meteor.position)
        self.velocity       = copy.copy(meteor.velocity)
        self.speed          = self.velocity.norm()
        self.luminousPower  = meteor.luminousPower
        self.mass           = meteor.mass
        self.trackLength    = meteor.trackLength
        self.lifeTime       = meteor.lifeTime

    def __str__(self):
        return "<MeteorFrame: {altaz}, {velocity} m/s, {speed:6.0f}, {lp} W>".format(
            altaz           = self.position,
            velocity        = self.velocity,
            speed           = self.velocity.norm(),
            lp              = self.luminousPower,
        )
