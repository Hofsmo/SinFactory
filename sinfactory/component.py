"""Module for handling components."""

import powerfactory as pf


class Component(object):
    """Base class for components"""

    def __init__(self, pf_object):
        """Constructor for the component class.

        Args:
            pf_object: The object we will store in this object."""

        self.pf_object = pf_object
        self.name = pf_object.cDisplayName
        self.in_service = not pf_object.outserv
        self.area = pf_object.cpArea

    @property
    def in_service(self):
        """Getter for if component is in service."""
        return self._in_service

    @in_service.setter
    def in_service(self, in_service):
        """Set component in or out of service.

        Args:
            in_service: If component should be in service or not."""
        self._in_service = in_service
        self.pf_object.outserv = not in_service

    def get_attribute(self, attribute):
        """Method for safely returning an attribute."""
        try:
            val = self.pf_object.GetAttribute(attribute)
        except AttributeError:
            val = None
        return val
