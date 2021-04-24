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
        for elm in elms:
            elm_name = elm.GetFullName()
            if "ElmLod" in elm_name:
                self.loads[elm_name] = Load(elm)
            if "ElmSym" in elm_name:
                self.gens[elm_name] = Generator(elm)
