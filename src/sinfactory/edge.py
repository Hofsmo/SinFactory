"""Module for handling edges in PowerFactory."""

from powerfactory.component import Component


class PowerFactoryLine(Component):
    """Class for with powerfactory edges."""

    def __init__(self, pf_object):
        """PowerFactoryLine constructor

        Args:
            pf_object: The powerfactory object we will store in this object.
        """

        super().__init__(self, pf_object)

        self.cubicles = [self.data_object.bus1,
                         self.data_object.bus2]
        
        self.switches = []
        for switch in self.app.GetCalcRelevantObjects("*.StaSwitch"):
            if switch.fold_id in self.cubicles:
                self.switches.append(switch)
