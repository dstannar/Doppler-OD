"""J2 gravity via Holmes–Featherstone (normalized field degree 2)."""

from org.orekit.forces.gravity import HolmesFeatherstoneAttractionModel
from org.orekit.forces.gravity.potential import GravityFieldFactory

#J2 pertubation function
def build_j2_perturbation_model(frame):

    provider = GravityFieldFactory.getNormalizedProvider(2,0)

    return HolmesFeatherstoneAttractionModel(frame, provider)