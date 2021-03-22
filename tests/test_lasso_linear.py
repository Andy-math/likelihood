# -*- coding: utf-8 -*-
import numpy
import numpy.linalg
from likelihood import likelihood
from likelihood.stages.Lasso import Lasso
from likelihood.stages.Linear import Linear
from likelihood.stages.LogNormpdf import LogNormpdf
from numerical import difference
from numerical.typedefs import ndarray
from optimizer import trust_region


def run_once(n: int, m: int, seed: int = 0) -> None:
    numpy.random.seed(seed)
    rrrr = numpy.random.randn(n, m)
    rrrr[:, -1] = rrrr[:, 0] - rrrr[:, -1] / 1000
    x = rrrr
    beta = n * numpy.random.randn(m)
    beta[-1] = 0.0
    y = x @ beta + numpy.random.randn(n)
    beta_decomp, _, _, _ = numpy.linalg.lstsq(x, y, rcond=None)  # type: ignore
    relerr_decomp = difference.relative(beta[:-1], beta_decomp[:-1])

    stage1 = Linear([f"b{i}" for i in range(1, m + 1)], list(range(1, m + 1)), 1)
    stage2 = LogNormpdf("var", (0, 1), (0, 1))
    penalty = Lasso(stage1.names, 1.0, (0, 1), 0)
    nll = likelihood.negLikelihood([stage1, stage2], penalty, nvars=m + 1)

    beta0 = numpy.zeros((beta.shape[0] + 1))
    beta0[-1] = 1.0
    input = numpy.concatenate((y.reshape((-1, 1)), x), axis=1)

    assert (
        nll.eval(beta0, input, regularize=True)[0]
        == nll.eval(beta0, input, regularize=True)[0]
    )

    def func(x: ndarray) -> float:
        return nll.eval(x, input, regularize=True)[0]

    def grad(x: ndarray) -> ndarray:
        return nll.grad(x, input, regularize=True)

    opts = trust_region.Trust_Region_Options(max_iter=99999)
    # opts.check_iter = 20

    constraint = nll.get_constraint()

    result = trust_region.trust_region(
        func,
        grad,
        beta0,
        *constraint,
        opts,
    )
    beta_mle = result.x[:-1]
    relerr_mle = difference.relative(beta[:-1], beta_mle[:-1])
    print("result.success: ", result.success)
    print("result.delta: ", result.delta)
    print("beta:   ", beta)
    print("decomp: ", beta_decomp)
    print("mle:    ", beta_mle)
    print("relerr_decomp: ", relerr_decomp)
    print("relerr_mle:    ", relerr_mle)
    assert result.success
    assert 5 < result.iter < 1000
    assert relerr_decomp < 0.1
    assert relerr_mle < relerr_decomp


class Test_1:
    def test_1(self) -> None:
        run_once(1000, 4)


if __name__ == "__main__":
    Test_1().test_1()