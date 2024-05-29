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
        self.area = pf_object.cpArea
        self.areaname = str(pf_object.cpArea).split("\\")[-1].split(".")[0]

    @property
    def in_service(self):
        """Getter for if component is in service."""
        return not self.pf_object.outserv

    @in_service.setter
    def in_service(self, in_service):
        """Set component in or out of service.

        Args:
            in_service: If component should be in service or not."""
        self.pf_object.outserv = not in_service

    def get_attribute(self, attribute):
        """Method for safely returning an attribute."""
        try:
            val = self.pf_object.GetAttribute(attribute)
        except AttributeError:
            val = None
        return val
