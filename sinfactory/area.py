"""Module for handling areas."""
from sinfactory.bus import Bus
from sinfactory.line import Line
import itertools


class Area(object):
    """Class for areas."""

    def __init__(self, pf_object):
        """Constructor for Area class."""
        
        self.name = pf_object.GetFullName().split("\\")[-1].split(".")[0]
        self.buses = {bus.cDisplayName: Bus(bus)
                      for bus in pf_object.GetBuses()}
        self.pf_object = pf_object

        self.lines = {line.cDisplayName: Line(line) for line in
                      pf_object.GetBranches() if "ElmLne" in
                      line.GetFullName()}

    def get_inter_area_flow(self, area):
        """Get the flow between two areas.

        Args:
            area: The other area to calculate the flow to.
        """
        self.pf_object.CalculateInterchangeTo(area.pf_object)
        try:
            return self.pf_object.GetAttribute("c:Pinter")
        except AttributeError:
            return None

    def get_inter_area_lines(self, area):
        """Get the lines between two areas

        Args:
            area: The other area to get the lines to.
        """
        lines = {}
        for line in itertools.chain(self.lines.values(),
                                    area.lines.values()):
            if (line.f_bus in self.pf_object.GetAll() and
                    line.t_bus in area.pf_object.GetAll()):
                lines[line.name] = line
            if (line.t_bus in self.pf_object.GetAll() and
                    line.f_bus in area.pf_object.GetAll()):
                lines[line.name] = line

        return lines

    def get_total_var(self, var):
        """Return the total var in area."""
        tot = 0
        for bus in self.buses.values():
            for elm in getattr(bus, var).values():
                tot += elm.p_set
        return tot




    
