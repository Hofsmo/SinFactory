"""Module for handling lines in PowerFactory."""


class PowerFactoryLine(object):
    """Class for interfacing with powerfactory lines."""

    def __init__(self, app, line_obj):
        """PowerFactoryLine constructor

        Args:
            app: PowerFactory app object
            line_obj: The line object
        """

        self.app = app
        self.data_object = line_obj

        self.cubicles = [self.data_object.bus1,
                         self.data_object.bus2]
        
        self.switches = []
        for switch in self.app.GetCalcRelevantObjects("*.StaSwitch"):
            if switch.fold_id in self.cubicles:
                self.switches.append(switch)
