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

class InterLine(Line):
    """Class for interfacing with lines between areas."""
    def __init__(self, line, f_area, t_area):
        """Constructor for inter area lines.

        Args:
            line: Line between two areas.
            f_area: The area the flow is directed away from
            t_area: The area the flow is directed towards
        """
        super().__init__(line.pf_object)
        
        self.f_area = f_area
        self.t_area = t_area

        if self.f_bus_cub in f_area.pf_object.GetAll():
            self.direction = 1
        else:
            self.direction = -1
    
    @property
    def p(self):
        """The active power flow on the line in the direction of from area
        to to area"""
        return self.direction*super().p


class AreaInterface():
    """Class for handling interfaces between areas."""

    def __init__(self, lines, f_area, t_area):
        """Constructor for inter area interfaces.

        Args:
            lines: The lines between the areas
            f_area: The area the flow is directed away from
            t_area: The area the flow is directed towards
        """

        self.lines = lines
        self.f_area = f_area
        self.t_area = t_area

    @property
    def p(self):
        """The active power flow on the interface."""
        return sum(line.p for line in self.lines)
