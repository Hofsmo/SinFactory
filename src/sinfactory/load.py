"""Module for handling loads."""

from sinfactory.unit import Unit


class Load(Unit):
    """Load class"""

    def __init__(self, pf_object):
        """Constructor for the load class

        Args:
            pf_object: The power factory object we will store.
        """
        super().__init__(pf_object)
        
    @property
    def p_set(self):
        """Getter for active power."""
        return self.pf_object.plini

    @p_set.setter
    def p_set(self, val):
        """Setter for active power
        
        Args:
            val: The new value for the load."""

        self.pf_object.plini = val

    @property
    def q_set(self):
        """Getter for reactive power."""
        return self.pf_object.qlini

    @q_set.setter
    def q_set(self, val):
        """Setter for reactive power
        
        Args:
            val: The new value for the load."""

        self.pf_object.qlini = val


