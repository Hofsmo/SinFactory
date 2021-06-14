"""Module for handling generators."""

from sinfactory.unit import Unit


class Generator(Unit):
    """Generator class."""

    def __init__(self, pf_object):
        """Constructor for the generator class

        Args:
            pf_object: The power factory object we will store.
        """
        super().__init__(pf_object)

    @property
    def p_set(self):
        """Getter for active power."""
        return self.pf_object.ngnum*self.pf_object.pgini

    @p_set.setter
    def p_set(self, val):
        """Setter for active power
        
        This setter consider the fact that there can be several machines
        in parallel on a generator. It returns the total power output of
        the generator.

        Args:
            val: The new value for the generation."""
        self.pf_object.pgini = val/self.pf_object.ngnum
    
    @property
    def q_set(self):
        """Getter for reactive power."""
        return self.pf_object.ngnum*self.pf_object.qgini

    @q_set.setter
    def q_set(self, val):
        """Setter for reactive power
        
        This setter consider the fact that there can be several machines
        in parallel on a generator. It returns the total power output of
        the generator.

        Args:
            val: The new value for the generation."""
        self.pf_object.qgini = val/self.pf_object.ngnum
    
    @property
    def rating(self):
        """Getter for machine rating.

        It returns the rating of the generator considering that there can be
        multiple machines in parallel."""
        return self.pf_object.P_max*self.pf_object.ngnum

    @rating.setter
    def rating(self, val):
        """Setter for rating.

        It sets the rating to the rating of each machine in parlell.

        Args:
            val: The new value for the rating."""
        self.pf_object.P_max = val/self.pf_object.ngnum

    @property
    def n_machines(self):
        return self.pf_object.ngnum

    @n_machines.setter
    def n_machines(self, val):
        """Setter for machines in parallel.

        This setter ensures that the active and reactive power
        at the generator remains the same after changing the number of 
        machines in parallel.

        Args:
            val: the new value."""
      
        # Store the old power values
        old_p = self.p_set
        old_q = self.q_set
        
        # set the number of generators
        self.pf_object.ngnum = val
       
        # Set the powers correctly
        self.p_set = old_p
        self.q_set = old_q

        # Set the rating correctly
        self.rating = self.pf_object.P_max*val

    @property
    def h(self):
        """Getter for machine inertia."""
        return self.pf_object.typ_id.h

    @h.setter
    def h(self, val):
        """ 
        Setter for machine inertia.
            
            Args:
                val: Inertia constant for new machine."""
        self.pf_object.typ_id.h = val
