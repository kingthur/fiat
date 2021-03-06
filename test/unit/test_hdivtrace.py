# Copyright (C) 2016 Imperial College London and others
#
# This file is part of FIAT.
#
# FIAT is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FIAT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with FIAT. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#
# Thomas Gibson (t.gibson15@imperial.ac.uk)

from __future__ import absolute_import, print_function, division
from six.moves import map

import pytest
import numpy as np


@pytest.mark.parametrize("dim", (2, 3))
@pytest.mark.parametrize("degree", range(7))
def test_basis_values(dim, degree):
    """Ensure that integrating simple monomials produces the expected results
    for each facet entity of the reference triangle and tetrahedron.

    This test performs the trace tabulation in two ways:
    (1) The entity is not specified, in which case the element uses
        numerical tolerance to determine the facet id;
    (2) The entity pair (dim, id) is provided, and the trace element
        tabulates accordingly using the new tabulate API.
    """
    from FIAT import ufc_simplex, HDivTrace, make_quadrature

    ref_el = ufc_simplex(dim)
    quadrule = make_quadrature(ufc_simplex(dim - 1), degree + 1)
    fiat_element = HDivTrace(ref_el, degree)
    nf = fiat_element.facet_element.space_dimension()

    for facet_id in range(dim + 1):
        # Tabulate without an entity pair given --- need to map to cell coordinates
        cell_transform = ref_el.get_entity_transform(dim - 1, facet_id)
        cell_points = np.array(list(map(cell_transform, quadrule.pts)))
        ctab = fiat_element.tabulate(0, cell_points)[(0,) * dim][nf*facet_id:nf*(facet_id + 1)]

        # Tabulate with entity pair provided
        entity = (ref_el.get_spatial_dimension() - 1, facet_id)
        etab = fiat_element.tabulate(0, quadrule.pts,
                                     entity)[(0,) * dim][nf*facet_id:nf*(facet_id + 1)]

        for test_degree in range(degree + 1):
            coeffs = [n(lambda x: x[0]**test_degree)
                      for n in fiat_element.facet_element.dual.nodes]

            cintegral = np.dot(coeffs, np.dot(ctab, quadrule.wts))
            eintegral = np.dot(coeffs, np.dot(etab, quadrule.wts))
            assert np.allclose(cintegral, eintegral, rtol=1e-14)

            reference = np.dot([x[0]**test_degree
                                for x in quadrule.pts], quadrule.wts)
            assert np.allclose(cintegral, reference, rtol=1e-14)
            assert np.allclose(eintegral, reference, rtol=1e-14)


@pytest.mark.parametrize("dim", (2, 3))
@pytest.mark.parametrize("order", range(1, 4))
@pytest.mark.parametrize("degree", range(4))
def test_gradient_traceerror(dim, order, degree):
    """Ensure that the TraceError appears in the appropriate dict entries when
    attempting to tabulate certain orders of derivatives."""
    from FIAT import ufc_simplex, HDivTrace, make_quadrature
    from FIAT.hdiv_trace import TraceError

    fiat_element = HDivTrace(ufc_simplex(dim), degree)
    pts = make_quadrature(ufc_simplex(dim - 1), degree + 1).pts

    for facet_id in range(dim + 1):
        tab = fiat_element.tabulate(order, pts, entity=(dim - 1, facet_id))

        for key in tab.keys():
            if key != (0,)*dim:
                assert isinstance(tab[key], TraceError)


@pytest.mark.parametrize("dim", (2, 3))
@pytest.mark.parametrize("degree", range(4))
def test_cell_traceerror(dim, degree):
    """Ensure that the TraceError appears in all dict entries when deliberately
    attempting to tabulate the cell of a trace element."""
    from FIAT import ufc_simplex, HDivTrace, make_quadrature
    from FIAT.hdiv_trace import TraceError

    fiat_element = HDivTrace(ufc_simplex(dim), degree)
    pts = make_quadrature(ufc_simplex(dim), 1).pts
    tab = fiat_element.tabulate(0, pts, entity=(dim, 0))

    for key in tab.keys():
        assert isinstance(tab[key], TraceError)


if __name__ == '__main__':
    import os
    pytest.main(os.path.abspath(__file__))
