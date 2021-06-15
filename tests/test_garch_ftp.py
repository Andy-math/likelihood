# -*- coding: utf-8 -*-
import math

import numpy
import numpy.linalg
from likelihood import likelihood
from likelihood.stages.Assign import Assign
from likelihood.stages.Copy import Copy
from likelihood.stages.Garch_mean import Garch_mean
from likelihood.stages.MS_TVTP import MS_TVTP, providers
from numerical import difference
from numerical.typedefs import ndarray
from optimizer import trust_region

from tests.common import nll2func


def normpdf(err: float, var: float) -> float:
    return 1.0 / math.sqrt(2.0 * math.pi * var) * math.exp(-(err * err) / (2.0 * var))


def generate(coeff: ndarray, n: int, seed: int = 0) -> ndarray:
    numpy.random.seed(seed)
    p11, p22, c1, a1, b1, c2, a2, b2 = coeff
    p1, p2 = 0.5, 0.5
    var1 = c1 / (1.0 - a1 - b1)
    var2 = c2 / (1.0 - a2 - b2)
    x = numpy.zeros((n, 1))
    for i in range(n):
        path11, path22 = p1 * p11, p2 * p22
        p1, p2 = path11 + p2 * (1 - p22), p1 * (1 - p11) + path22
        contrib11, contrib22 = path11 / p1, path22 / p2
        var1, var2 = (
            contrib11 * var1 + (1 - contrib11) * var2,
            (1 - contrib22) * var1 + contrib22 * var2,
        )

        x[i] = numpy.random.normal(
            loc=0, scale=math.sqrt(p1 * var1 + p2 * var2), size=1
        )
        f1, f2 = normpdf(x[i], var1), normpdf(x[i], var2)

        p1, p2 = p1 * f1, p2 * f2
        p1, p2 = p1 / (p1 + p2), p2 / (p1 + p2)

        var1 = c1 + a1 * x[i] * x[i] + b1 * var1
        var2 = c2 + a2 * x[i] * x[i] + b2 * var2

    return x


def run_once(coeff: ndarray, n: int, seed: int = 0) -> None:
    x = generate(coeff, n, seed=seed)

    input = numpy.concatenate(
        (x, numpy.zeros((n, 1)), numpy.ones((n, 1)), numpy.zeros((n, 16))), axis=1
    )
    beta0 = numpy.array([0.8, 0.8, 0.011, 0.099, 0.89, 1.0, 0.0, 0.0])

    stage4 = Copy((0, 1), (5, 6))
    stage5 = Copy((0, 1), (9, 10))
    # x mu var EX2
    submodel1 = Garch_mean(("c1", "a1", "b1"), (5, 6), (5, 6, 7, 8))
    submodel2 = Garch_mean(("c2", "a2", "b2"), (9, 10), (9, 10, 11, 12))
    assign1 = Assign("p11", 17, 0.0, 1.0)
    assign2 = Assign("p22", 18, 0.0, 1.0)
    stage6 = MS_TVTP(
        (submodel1, submodel2),
        (),
        providers["normpdf"],
        (17, 18),
        (0, 17, 18),
    )

    nll = likelihood.negLikelihood(
        [stage4, stage5, assign1, assign2, stage6],
        None,
        nvars=19,
    )

    func, grad = nll2func(nll, beta0, input, regularize=False)

    constraint = nll.get_constraint()

    opts = trust_region.Trust_Region_Options(max_iter=99999)
    opts.check_iter = 50
    opts.abstol_fval = 1.0e-2
    opts.max_stall_iter = 100

    result = trust_region.trust_region(
        func,
        grad,
        beta0 if n > 10 else coeff,
        *constraint,
        opts,
    )
    beta_mle = result.x
    abserr_mle = difference.absolute(coeff, beta_mle)
    print("result.success: ", result.success)
    print("coeff: ", coeff)
    print("mle:   ", [round(x, 6) for x in beta_mle])
    print("abserr_mle: ", abserr_mle)
    assert result.success
    assert 5 < result.iter < 1500
    assert abserr_mle < 0.5


class Test_1:
    def test_1(_) -> None:
        run_once(numpy.array([0.8, 0.8, 0.011, 0.099, 0.89, 1.0, 0.0, 0.0]), 1000)


if __name__ == "__main__":
    Test_1().test_1()
