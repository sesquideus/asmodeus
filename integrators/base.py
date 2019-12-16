import numbers
import math
import numpy as np

from integrators.state import State, Diff


class Integrator:
    def __init__(self, model, fps):
        self.model = model
        self.fps = fps


class IntegratorConstantStep(Integrator):
    def __init__(self, model, fps, spf):
        super().__init__(model, fps)
        self.spf = spf
        self.dt = 1.0 / (self.fps * self.spf)
        self.steps_taken = 0

    def step(self, state, dt):
        raise NotImplementedError

    def simulate(self, meteor):
        self.steps_taken = 0

        while True:
            state = State(meteor.position, meteor.velocity, math.log(meteor.mass))
            diff = self.step(meteor, state, self.dt)

            meteor.update_state(diff, self.dt)
            if self.steps_taken % self.spf == 0:
                meteor.save_snapshot()
                meteor.print_info()

            self.steps_taken += 1

            if meteor.check_terminate():
                break


class IntegratorAdaptiveStep(Integrator):
    def __init__(self, fps, *, min_spf=1, max_spf=64, error_coarser=1e-8, error_finer=1e-2):
        super().__init__(fps)
        self.min_spf = min_spf
        self.max_spf = max_spf
        self.error_coarser = error_coarser
        self.error_finer = error_finer


class IntegratorEuler(IntegratorConstantStep):
    def step(self, state, dt):
        return self.model.evaluate(state, Diff.zero(), dt)


class IntegratorRungeKutta4(IntegratorConstantStep):
    def step(self, meteor, state, dt):
        d1 = self.model.evaluate(meteor, state, Diff.zero(), dt)
        d2 = self.model.evaluate(meteor, state, d1 * 0.5, dt)
        d3 = self.model.evaluate(meteor, state, d2 * 0.5, dt)
        d4 = self.model.evaluate(meteor, state, d3, dt)
        return (d1 + 2 * d2 + 2 * d3 + d4) / 6


class IntegratorDormandPrince(IntegratorConstantStep):
    def step(self, state, dt):
        d0 = Diff.zero()
        d1 = self.model.evaluate(state, d0, dt)
        d2 = self.model.evaluate(state, d1 * DP_A21, dt)
        d3 = self.model.evaluate(state, d1 * DP_A31 + d2 * DP_A32, dt)
        d4 = self.model.evaluate(state, d1 * DP_A41 + d2 * DP_A42 + d3 * DP_A43, dt)
        d5 = self.model.evaluate(state, d1 * DP_A51 + d2 * DP_A52 + d3 * DP_A53 + d4 * DP_A54, dt)
        d6 = self.model.evaluate(state, d1 * DP_A61 + d2 * DP_A62 + d3 * DP_A63 + d4 * DP_A64 + d5 * DP_A65, dt)
        return d1 * DP_A71 + d3 * DP_A73 + d4 * DP_A74 + d5 * DP_A75 + d6 * DP_A76
