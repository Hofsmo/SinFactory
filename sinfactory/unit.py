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
