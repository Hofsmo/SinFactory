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
        
        self.p_set = pf_object.plini
        self.q_set = pf_object.qlini

    @property
    def p_set(self):
        """Getter for active power."""
        return self._p_set

    @p_set.setter
    def p_set(self, val):
        """Setter for active power
        
        Args:
            val: The new value for the load."""

        self._p_set = val
        self.pf_object.plini = val

    @property
    def q_set(self):
        """Getter for reactive power."""
        return self._q_set

    @q_set.setter
    def q_set(self, val):
        """Setter for reactive power
        
        Args:
            val: The new value for the load."""

        self._q_set = val
        self.pf_object.plini = val


