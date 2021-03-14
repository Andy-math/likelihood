from typing import Sequence, Tuple

import numpy
from likelihood.KnownIssue import KnownIssue
from likelihood.stages.abc.Convolution import Convolution
from numerical.typedefs import ndarray


class Midas_exp(Convolution):
    K: int

    def __init__(
        self, names: str, input: Sequence[int], output: Sequence[int], *, k: int
    ) -> None:
        assert len(input) == len(output)
        super().__init__((names,), input, output)
        self.K = k

    def kernel(self, _omega: ndarray) -> Tuple[ndarray, ndarray]:
        """
        rphi(1 <= k <= K) = omega ** k
        phi = rphi/sum(rphi)
        """
        k = numpy.arange(1.0, self.K + 1.0)
        k.shape = (k.shape[0], 1)
        omega = float(_omega)

        """
        rphi = omega ** k
        drphi_do = k * omega ** (k-1)
        """
        rphi = omega ** k
        drphi_do = k * omega ** (k - 1.0)

        sum = numpy.sum(rphi)
        dsum_do = numpy.sum(drphi_do, axis=0, keepdims=True)
        if sum == 0:
            raise KnownIssue("Midas_exp: 权重全为0")

        """
        phi = rphi/sum
        dphi_do = (1/sum) * drphi_do - rphi / (sum*sum) * dsum_do
                = drphi_do / sum - dsum_do * phi / sum
        """
        phi = rphi / sum
        dphi_do = drphi_do / sum - dsum_do * phi / sum

        phi.shape = (phi.shape[0],)
        return phi, dphi_do

    def get_constraint(self) -> Tuple[ndarray, ndarray, ndarray, ndarray]:
        A = numpy.empty((0, 1))
        b = numpy.empty((0,))
        lb = numpy.array([0.0])
        ub = numpy.array([1.0])
        return A, b, lb, ub