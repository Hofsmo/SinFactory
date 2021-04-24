"""Module for handling areas."""
from sinfactory.bus import Bus


class Area(object):
    """Class for areas."""

    def __init__(self, pf_object):
        """Constructor for Area class."""
        
        self.name = pf_object.GetFullName().split("\\")[-1].split(".")[0]
        self.buses = {bus.cDisplayName: Bus(bus)
                      for bus in pf_object.GetBuses()}
        self.pf_object = pf_object

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

