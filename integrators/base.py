import numbers
import math
import numpy as np

from integrators.state import State, Diff

DP_A21 = 1/5

DP_A31 = 3/40
DP_A32 = 9/40

DP_A41 = 44/45
DP_A42 = -56/15
DP_A43 = 32/9

DP_A51 = 19372/6561
DP_A52 = -25360/2187
DP_A53 = 64448/6561
DP_A54 = -212/729

DP_A61 = 9017/3168
DP_A62 = -355/33
DP_A63 = 46732/5247
DP_A64 = 49/176
DP_A65 = -5103/18656

DP_A71 = 35/384
DP_A73 = 500/1113
DP_A74 = 125/192
DP_A75 = -2187/6784
DP_A76 = 11/84

DP_B1 = 5179/57600
DP_B3 = 7571/16695
DP_B4 = 393/640
DP_B5 = -92097/339200
DP_B6 = 187/2100
DP_B7 = 1/40

#log = logging.getLogger('root')
class L():
    def debug(self, p):
        print(p)
log = L()


class Integrator:
    def __init__(self, model, fps):
        self.model = model
        self.fps = fps

    def step(self, state, dt):
        raise NotImplementedError


class IntegratorConstantStep(Integrator):
    def __init__(self, model, fps, spf):
        super().__init__(model, fps)
        self.spf = spf
        self.dt = 1.0 / (self.fps * self.spf)

    def simulate(self, meteor):
        self.steps_taken = 0

        while True:
            state = State(meteor.position, meteor.velocity, math.log(meteor.mass))
            diff = self.step(meteor, state, self.dt)

            meteor.update_properties(diff, self.dt)
            if self.steps_taken % self.spf == 0:
                meteor.save_snapshot()
                meteor.print_info()

            meteor.update_state(diff, self.dt)
            self.steps_taken += 1

            if meteor.check_terminate():
                break


class IntegratorAdaptiveStep(Integrator):
    def __init__(self, model, fps, *, spf_min=1, spf_max=64, error_coarser=1e-8, error_finer=1e-2):
        super().__init__(model, fps)

        if spf_max < spf_min:
            raise ValueError("spf_min must be smaller or equal to spf_max")
        self.spf_min = spf_min
        self.spf_max = spf_max
        self.spf = spf_min

        if error_coarser > error_finer:
            raise ValueError("error_coarser must be greater than error_finer")
        self.error_coarser = error_coarser
        self.error_finer = error_finer

    def simulate(self, meteor):
        self.steps_taken = 0
        clock = 0
        last_change = 0

        while True:
            self.dt = 1.0 / (self.fps * self.spf)
            state = State(meteor.position, meteor.velocity, math.log(meteor.mass))
            diff, error = self.step(meteor, state, self.dt)

            self.steps_taken += 1
            diff, error = self.step(meteor, state, self.dt)
            #print(f"t = {self.time:12.6f} s, error = {error:.6f}, {clock}/{spf}")

            if error < self.error_coarser and self.spf > self.spf_min:
                log.debug(f"Step unnecessarily small (error = {error:.6f}), {clock}/{self.spf}")
                if clock % 2 == 0:
                    self.spf //= 2
                    clock //= 2
                    log.debug(f"Decreasing to {self.spf} steps per frame at clock {clock}")
                    last_change = +1
                    continue
                else:
                    log.debug("Waiting another step")
                    pass

            if error > self.error_finer and self.spf < self.spf_max and last_change != 1:
                self.spf *= 2
                clock *= 2
                log.debug(f"Step too long (error = {error:.6f}), increasing to {self.spf} steps per frame at clock {clock}")
                last_change = -1
                continue

            last_change = 0


            meteor.update_properties(diff, self.dt)
            if clock % self.spf == 0:
                meteor.save_snapshot()
                meteor.print_info()
                clock = 0

            meteor.update_state(diff, self.dt)

            clock += 1
            if meteor.check_terminate():
                break


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
    def step(self, meteor, state, dt):
        d0 = Diff.zero()
        d1 = self.model.evaluate(state, d0, dt)
        d2 = self.model.evaluate(state, d1 * DP_A21, dt)
        d3 = self.model.evaluate(state, d1 * DP_A31 + d2 * DP_A32, dt)
        d4 = self.model.evaluate(state, d1 * DP_A41 + d2 * DP_A42 + d3 * DP_A43, dt)
        d5 = self.model.evaluate(state, d1 * DP_A51 + d2 * DP_A52 + d3 * DP_A53 + d4 * DP_A54, dt)
        d6 = self.model.evaluate(state, d1 * DP_A61 + d2 * DP_A62 + d3 * DP_A63 + d4 * DP_A64 + d5 * DP_A65, dt)
        return d1 * DP_A71 + d3 * DP_A73 + d4 * DP_A74 + d5 * DP_A75 + d6 * DP_A76


class IntegratorDormandPrinceAdaptive(IntegratorAdaptiveStep):
    def step(self, meteor, state, dt):
        d0 = Diff.zero()
        d1 = self.model.evaluate(meteor, state, d0, dt)
        d2 = self.model.evaluate(meteor, state, d1 * DP_A21, dt)
        d3 = self.model.evaluate(meteor, state, d1 * DP_A31 + d2 * DP_A32, dt)
        d4 = self.model.evaluate(meteor, state, d1 * DP_A41 + d2 * DP_A42 + d3 * DP_A43, dt)
        d5 = self.model.evaluate(meteor, state, d1 * DP_A51 + d2 * DP_A52 + d3 * DP_A53 + d4 * DP_A54, dt)
        d6 = self.model.evaluate(meteor, state, d1 * DP_A61 + d2 * DP_A62 + d3 * DP_A63 + d4 * DP_A64 + d5 * DP_A65, dt)
        solution = d1 * DP_A71 + d3 * DP_A73 + d4 * DP_A74 + d5 * DP_A75 + d6 * DP_A76

        d7 = self.model.evaluate(meteor, state, solution, dt)
        alternative = (d1 * DP_B1 + d3 * DP_B3 + d4 * DP_B4 + d5 * DP_B5 + d6 * DP_B6 + d7 * DP_B7)
        error_estimate = solution - alternative

        return solution, max(error_estimate.dvdt.norm(), error_estimate.dmdt)


