import numpy as np
import math

def smooth_derivative(t_in, v_in):
    #
    # Function to compute a smooth estimation of a derivative.
    # [REF: http://holoborodko.com/pavel/numerical-methods/numerical-derivative/smooth-low-noise-differentiators/]
    #

    # Configuration
    #
    # Derivative method: two options: 'smooth' or 'centered'. Smooth is more conservative
    # but helps to supress the very noisy signals. 'centered' is more agressive but more noisy
    method = "smooth"

    t = t_in.copy()
    v = v_in.copy()

    # (0) Prepare inputs

    # (0.1) Time needs to be transformed to seconds
    try:
        for i in range(0, t.size):
            t.iloc[i] = t.iloc[i].total_seconds()
    except:
        pass

    t = np.array(t)
    v = np.array(v)

    # (0.1) Assert they have the same size
    assert t.size == v.size

    # (0.2) Initialize output
    dvdt = np.zeros(t.size)

    # (1) Manually compute points out of the stencil

    # (1.1) First point
    dvdt[0] = (v[1] - v[0]) / (t[1] - t[0])

    # (1.2) Second point
    dvdt[1] = (v[2] - v[0]) / (t[2] - t[0])

    # (1.3) Third point
    dvdt[2] = (v[3] - v[1]) / (t[3] - t[1])

    # (1.4) Last points
    n = t.size
    dvdt[n - 1] = (v[n - 1] - v[n - 2]) / (t[n - 1] - t[n - 2])
    dvdt[n - 2] = (v[n - 1] - v[n - 3]) / (t[n - 1] - t[n - 3])
    dvdt[n - 3] = (v[n - 2] - v[n - 4]) / (t[n - 2] - t[n - 4])

    # (2) Compute the rest of the points
    if method == "smooth":
        c = [5.0 / 32.0, 4.0 / 32.0, 1.0 / 32.0]
        for i in range(3, t.size - 3):
            for j in range(1, 4):
                if (t[i + j] - t[i - j]) == 0:
                    dvdt[i] += 0
                else:
                    dvdt[i] += (
                        2 * j * c[j - 1] * (v[i + j] - v[i - j]) / (t[i + j] - t[i - j])
                    )
    elif method == "centered":
        for i in range(3, t.size - 2):
            for j in range(1, 4):
                if (t[i + j] - t[i - j]) == 0:
                    dvdt[i] += 0
                else:

                    dvdt[i] = (v[i + 1] - v[i - 1]) / (t[i + 1] - t[i - 1])

    return dvdt


def truncated_remainder(dividend, divisor):
    divided_number = dividend / divisor
    divided_number = (
        -int(-divided_number) if divided_number < 0 else int(divided_number)
    )

    remainder = dividend - divisor * divided_number

    return remainder


def transform_to_pipi(input_angle):
    pi = math.pi
    revolutions = int((input_angle + np.sign(input_angle) * pi) / (2 * pi))

    p1 = truncated_remainder(input_angle + np.sign(input_angle) * pi, 2 * pi)
    p2 = (
        np.sign(
            np.sign(input_angle)
            + 2
            * (
                np.sign(
                    math.fabs(
                        (truncated_remainder(input_angle + pi, 2 * pi)) / (2 * pi)
                    )
                )
                - 1
            )
        )
    ) * pi

    output_angle = p1 - p2

    return output_angle, revolutions


def remove_acceleration_outliers(acc):
    acc_threshold_g = 7.5
    if math.fabs(acc[0]) > acc_threshold_g:
        acc[0] = 0.0

    for i in range(1, acc.size - 1):
        if math.fabs(acc[i]) > acc_threshold_g:
            acc[i] = acc[i - 1]

    if math.fabs(acc[-1]) > acc_threshold_g:
        acc[-1] = acc[-2]

    return acc


def compute_accelerations(telemetry):
    v = np.array(telemetry["Speed"]) / 3.6
    lon_acc = smooth_derivative(telemetry["Time"], v) / 9.81

    dx = smooth_derivative(telemetry["Distance"], telemetry["X"])
    dy = smooth_derivative(telemetry["Distance"], telemetry["Y"])

    theta = np.zeros(dx.size)
    theta[0] = math.atan2(dy[0], dx[0])
    for i in range(0, dx.size):
        theta[i] = (
            theta[i - 1] + transform_to_pipi(math.atan2(dy[i], dx[i]) - theta[i - 1])[0]
        )

    kappa = smooth_derivative(telemetry["Distance"], theta)
    lat_acc = v * v * kappa / 9.81

    # Remove outliers
    lon_acc = remove_acceleration_outliers(lon_acc)
    lat_acc = remove_acceleration_outliers(lat_acc)

    return np.round(lon_acc, 2), np.round(lat_acc, 2)