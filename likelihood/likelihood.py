from __future__ import annotations

from typing import Any, List

import numpy
from numerical.typedefs import ndarray
from overloads.shortcuts import assertNoInfNaN

from likelihood.stages.abc.Logpdf import Logpdf
from likelihood.stages.abc.Stage import Stage
from likelihood.stages.Compose import Compose


class negLikelihood:
    nCoeff: int
    nInput: int
    stages: Compose

    def __init__(self, stages: List[Stage[Any]], nVars: int) -> None:
        assert isinstance(stages[-1], Logpdf)
        assert len(stages[-1]._output_idx) == 1
        assert stages[-1]._output_idx[0] == 0
        self.stages = Compose(stages, list(range(nVars)), list(range(nVars)))
        self.nCoeff = self.stages.len_coeff
        self.nInput = nVars

    def eval(self, coeff: ndarray, input: ndarray) -> float:
        assert coeff.shape == (self.nCoeff,)
        assertNoInfNaN(input)
        o, _ = self.stages.eval(coeff, input.copy(), grad=False)
        return -numpy.sum(o[:, 0])

    def grad(self, coeff: ndarray, input: ndarray) -> ndarray:
        assert coeff.shape == (self.nCoeff,)
        assertNoInfNaN(input)
        o, gradinfo = self.stages.eval(coeff, input.copy(), grad=True)
        assert gradinfo is not None
        dL_dL = numpy.zeros(o.shape)
        dL_dL[:, 0] = -1.0
        _, dL_dc = self.stages.grad(coeff, gradinfo, dL_dL)
        return dL_dc
