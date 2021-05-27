"""Module for handling buses."""

from sinfactory.component import Component
from sinfactory.load import Load
from sinfactory.generator import Generator


class Bus(Component):
    """Node class"""

    def __init__(self, pf_object):
        """Constructor for the Bus class.

        Args:
            pf_object: The power factory object we will store.
        """
        super().__init__(pf_object)
        elms = pf_object.GetConnectedElements()

        self.loads = {}
        self.gens = {}

        # If this makes initialisation too slow, only calculate this on
        # request.
        for elm in elms:
            elm_name = elm.GetFullName()
            if "ElmLod" in elm_name:
                self.loads[elm.cDisplayName] = Load(elm)
            if "ElmSym" in elm_name:
                self.gens[elm.cDisplayName] = Generator(elm)

        self.cubs = []
        for elm in pf_object.GetConnectedCubicles():
            self.cubs.append(elm)

    @property
    def u(self):
        """The voltage magnitude of the bus in p.u."""
        return self.get_attribute("m:u")
