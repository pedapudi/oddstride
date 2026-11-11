"""Independent geometric and virtual-work checks for the screening model."""

import math
import random
import unittest

from sizing import clearance, contact_moments, dot, geometry, jacobian_columns, motor_demands


class SizingTests(unittest.TestCase):
    def test_straight_leg_and_symmetric_vertical_load(self):
        hip, belly = clearance(0.17, 0.17, 0, 0.07)
        self.assertAlmostEqual(hip, 0.34)
        self.assertAlmostEqual(belly, 0.27)
        angle = math.radians(35)
        roll, pitch, knee = contact_moments((0, -angle, 2*angle), (0, 0, 100), 0.17, 0.17, 0.04)
        self.assertAlmostEqual(roll, 4)
        self.assertAlmostEqual(pitch, 0)
        self.assertAlmostEqual(knee, 100*0.17*math.sin(angle))

    def test_jacobian_matches_finite_difference(self):
        rng = random.Random(170)
        epsilon = 1e-6
        for _ in range(40):
            q = [rng.uniform(-1.2, 1.2), rng.uniform(-1.7, 0.5), rng.uniform(0.1, 2.5)]
            args = (0.17, 0.19, 0.04)
            columns = jacobian_columns(q, *args)
            for joint in range(3):
                plus, minus = q.copy(), q.copy()
                plus[joint] += epsilon
                minus[joint] -= epsilon
                pplus, _, _ = geometry(plus, *args)
                pminus, _, _ = geometry(minus, *args)
                for axis in range(3):
                    derivative = (pplus[axis] - pminus[axis])/(2*epsilon)
                    self.assertAlmostEqual(columns[joint][axis], derivative, places=8)

    def test_virtual_work_and_ideal_transmission_power(self):
        q, dq, force = (0.3, -0.7, 1.2), (0.2, -0.4, 0.7), (20, -12, 90)
        epsilon = 1e-6
        pplus, _, _ = geometry(tuple(a+epsilon*b for a, b in zip(q, dq)), 0.17, 0.17, 0.04)
        pminus, _, _ = geometry(tuple(a-epsilon*b for a, b in zip(q, dq)), 0.17, 0.17, 0.04)
        velocity = tuple((a-b)/(2*epsilon) for a, b in zip(pplus, pminus))
        moments = contact_moments(q, force, 0.17, 0.17, 0.04)
        self.assertAlmostEqual(dot(force, velocity), dot(moments, dq), places=7)
        ratios = (1, 2, 2.5)
        motor = motor_demands(moments, ratios, (1, 1, 1))
        for torque, demand, ratio, speed in zip(moments, motor, ratios, dq):
            self.assertAlmostEqual(abs(torque*speed), demand*abs(speed*ratio))

    def test_mass_load_scaling(self):
        q, force = (0.2, -0.4, 1.1), (10, 20, 70)
        a = contact_moments(q, force, 0.17, 0.17, 0.04)
        b = contact_moments(q, tuple(1.5*f for f in force), 0.17, 0.17, 0.04)
        for x, y in zip(a, b):
            self.assertAlmostEqual(y, 1.5*x)


if __name__ == "__main__":
    unittest.main()
