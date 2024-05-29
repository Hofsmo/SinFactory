"""Module for handling units."""
from sinfactory.component import Component


class Unit(Component):
    """Class for handling units."""
    
    def __init__(self, pf_object):
        """Constructor for the generator class

        Args:
            pf_object: The power factory object we will store.
        """
        super().__init__(pf_object)

    @property
    def island_id(self):
        """The island id of the unit.

        In case the system has been split up into islands, each island will
        have an id. This is the id of the island this unit belongs to."""
        return self.pf_object.bus1.GetAttribute("b:ipat")
