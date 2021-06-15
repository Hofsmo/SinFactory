"""Module for handling lines in PowerFactory."""
from sinfactory.component import Component


class Line(Component):
    """Class for interfacing with powerfactory lines."""

    def __init__(self, pf_object):
        """PowerFactoryLine constructor

        Args:
            pf_object: The line object
        """
        super().__init__(pf_object)

        self.f_bus_cub = self.pf_object.bus1
        self.t_bus_cub = self.pf_object.bus2
        self.f_bus = pf_object.bus1.GetFullName().split("\\")[-2].split(".")[0]
        self.t_bus = pf_object.bus2.GetFullName().split("\\")[-2].split(".")[0]
        self.switches = [self.pf_object.bus1.cpCB,
                         self.pf_object.bus2.cpCB]

    @property
    def loading(self):
        """The loading of the line in percent of rating."""
        return self.get_attribute("c:loading")

    @property
    def p(self):
        """The active power flow on the line"""
        return self.get_attribute("m:P:bus1")

