"""Module for interfacing with power factory."""

import os
import numpy as np
import powerfactory as pf


class PFactoryGrid(object):
    """Class for interfacing with powerfactory."""
    def __init__(self, project_name, study_case_name, folder_name=''):
        """Class constructor."""
        # Start PowerFactory.
        self.app = pf.GetApplication()

        if self.app is None:
            raise RuntimeError("Failed to load powerfactory.")

        # Activate project.
        self.project = self.app.ActivateProject(os.path.join(folder_name,
                                                             project_name))

        if self.project is None:
            raise RuntimeError("No project activated.")

        # Activate study case.
        study_case_folder = self.app.GetProjectFolder('study')
        study_case_file = study_case_name + '.IntCase'
        self.study_case = study_case_folder.GetContents(study_case_file)[0]
        self.study_case.Activate()

    def prepare_dynamic_sim(self, variables, sim_type='rms', start_time=0.0,
                            step_size=0.01, end_time=10.0):
        """Method for calculating dynamic simulation initial conditions.

        Method that sets relevant parameters for calculating the initial
        conditions for the dynamic simulation and calculates them. It also
        determines which variables to monitor

        Args:
            variables (Dict): A dictionary containing the keys are the
                elements to be monitored and the data is a list of variables to
                monitor.
            sim_type (str): The simulation type it can be either rms for
                rms simulation and ins for EMT the default is rms.
            start_time (float): The starting time for the simulation the
                default is 0.0
            step_size (float): The time step used for the simulation. The
                default is 0.01
            end_time: The end time for the simulation. The default is 10.0
        """
        # Get result file.
        self.res = self.app.GetFromStudyCase('*.ElmRes')
        # Select result variable to monitor.
        for elm_name, var_names in variables.items():
            # Get all elements that match elm_name
            elements = self.app.GetCalcRelevantObjects(elm_name)
            # Select variables to monitor for each element
            for element in elements:
                self.res.AddVars(element, *var_names)

        # Retrieve initial conditions and time domain simulation object
        self.inc = self.app.GetFromStudyCase('ComInc')
        self.sim = self.app.GetFromStudyCase('ComSim')

        # Set simulation type
        self.inc.iopt_sim = sim_type

        # Set time options
        self.inc.tstart = start_time
        self.inc.dtgrid = step_size
        self.inc.tstop = end_time

        # Calculate initial conditions
        self.inc.Execute()

    def run_dynamic_sim(self):
        """Run dynamic simulation.

        Returns:
            bool: False for success, True otherwise.
        """
        return bool(self.sim.Execute())

    def get_dynamic_results(self, elm_name, var_name):
        """Method that returns results from a dynamic simulation.

        Args:
            elm_name (str): The name of the element to get the results for
            var_name (str): The name of the variable to the results for

        Returns:
            tuple: A tuple containing the time and result vector.
        """
        # Get network element of interest.
        element = self.app.GetCalcRelevantObjects(elm_name)[0]

        # Load results from file.
        self.app.ResLoadData(self.res)

        # Find column that holds results of interest
        col_idx = self.app.ResGetIndex(self.res, element, var_name)

        if col_idx == -1:
            raise ValueError("Could not find : " + elm_name)

        # Get time steps in the result file
        t_steps = self.app.ResGetValueCount(self.res, 0)

        # Read results and time
        time = np.zeros(t_steps)
        values = np.zeros(t_steps)

        # Iterate through the rows in the result file
        for i in range(t_steps):
            time[i] = self.app.ResGetData(self.res, i, -1)[1]
            values[i] = self.app.ResGetData(self.res, i, col_idx)[1]

        return time, values

    def set_all_loads(self, p_load, q_load):
        """Method for setting all loads powers.

        Args:
            p_load (Dict): Dictionary where the key is the name of the load
                and the value is the new load value.
            q_load (Dict): Dictionary where the key is the name of the load
                and the value is the new load value.
        """
        # Collect all load elements
        loads = self.app.GetCalcRelevantObjects("*.ElmLod")
        # Set active and reactive load values
        for load in loads:
            load.plini = p_load[load.loc_name]
            load.qlini = q_load[load.loc_name]

    def set_all_generators(self, p_load, q_load):
        """Method for setting all generator_powers.

        Args:
            p_load (Dict): Dictionary where the key is the name of the
                generator and the value is the new load value.
            q_load (Dict): Dictionary where the key is the name of the
                generator and the value is the new load value.
        """
        # Collect all load elements
        gens = self.app.GetCalcRelevantObjects("*.ElmSym")
        # Set active and reactive load values
        for gen in gens:
            gen.plini = p_load[gen.loc_name]
            gen.qlini = q_load[gen.loc_name]

    def set_out_of_service(self, elm_name):
        """Take an element out of service.

        Args:
            elm_name: Name of elements to take out of service.
        """
        # Collect all elements that match elm_name
        elms = self.app.GetCalcRelevantObjects(elm_name)
        for elm in elms:
            elm.outserv = True

    def set_in_service(self, elm_name):
        """Take an element back in service.

        Args:
            elm_name: Name of elements to take out of service.
        """
        # Collect all elements that match elm_name
        elms = self.app.GetCalcRelevantObjects(elm_name)
        for elm in elms:
            elm.outserv = False
