from distribution import PositionDistribution, VelocityDistribution, MassDistribution, DensityDistribution, TimeDistribution

class Population():
    def __init__(self, parameters):
        self.count = parameters.count
        
        try:
            log.info("Configuring meteoroid property distributions")
            self.massDistribution       = MassDistribution.fromConfig(parameters.mass).logInfo()
            self.positionDistribution   = PositionDistribution.fromConfig(parameters.position).logInfo()
            self.velocityDistribution   = VelocityDistribution.fromConfig(parameters.velocity).logInfo()
            self.densityDistribution    = DensityDistribution.fromConfig(parameters.material.density).logInfo()
            self.temporalDistribution   = TimeDistribution.fromConfig(parameters.time).logInfo()
        except AttributeError as e:
            raise exceptions.ConfigurationError(e)

    def generate(self):
        log.info(f"Generating {c.num(self.config.meteors.count)} meteoroids "
                 f"using {c.num(self.config.mp.processes)} processes "
                 f"at {c.num(self.config.meteors.integrator.fps)} frames per second, "
                 f"with {c.num(self.config.meteors.integrator.spf)} steps per frame")

        self.meteors = [meteor for meteor in [self.createMeteor() for _ in range(0, self.count)] if meteor is not None]
        log.info("{total} meteoroids survived the sin θ test ({percent}), total mass {mass}".format(
            total           = c.num(len(self.meteors)),
            percent         = c.num("{:5.2f}%".format(100 * len(self.meteors) / self.config.meteors.count)),
            mass            = c.num("{:6f} kg".format(sum(map(lambda x: x.mass, self.meteors)))),
        ))

    def createMeteor(self):
        timestamp           = self.temporalDistribution.sample()
        mass                = self.massDistribution.sample()
        density             = self.densityDistribution.sample()
        position            = self.positionDistribution.sample()
        velocityEquatorial  = self.velocityDistribution.sample()

        velocityECEF        = coord.Vector3D.fromNumpyVector((coord.rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocityEquatorial.toNumpyVector()))
        entryAngleSin       = -position * velocityECEF / (position.norm() * velocityECEF.norm())

        rnd                 = random.random()
        accepted            = rnd < entryAngleSin

        log.debug("Meteoroid {status}: sine of entry angle {sin:.6f}, random value {rnd:.6f}".format(
            status          = c.ok('accepted') if accepted else c.err('rejected'),
            sin             = entryAngleSin,
            rnd             = rnd,
        ))

        return Meteor(
            mass            = mass,
            density         = density,
            velocity        = velocityECEF,
            position        = position,
            timestamp       = timestamp,
            ablationHeat    = self.config.meteors.material.ablationHeat,
            heatTransfer    = self.config.meteors.material.heatTransfer,
            dragCoefficient = self.config.meteors.shape.dragCoefficient,
        ) if accepted else None

        
