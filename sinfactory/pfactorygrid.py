"""Module for interfacing with power factory."""


import os
import numpy as np
import pandas as pd
import powerfactory as pf


class PFactoryGrid(object):
    """Class for interfacing with powerfactory."""
    def __init__(self, project_name):
        """Class constructor."""
        # Start PowerFactory.
        self.app = pf.GetApplication()

        if self.app is None:
            raise RuntimeError("Failed to load powerfactory.")

        # Activate project.
        self.project = self.app.ActivateProject(project_name)

        if self.project is None:
            raise RuntimeError("No project activated.")

        self.window = self.app.GetOutputWindow()

    def activate_sudy_case(self, study_case_name, folder_name=""):
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

        Returns:
            True if all initial conditions are verified. False otherwise.
        """

        self.variables = variables

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
        self.sim.tstop = end_time

        # Verify initial conditions
        self.inc.iopt_show = True

        # Calculate initial conditions
        self.inc.Execute()

        return self.inc.ZeroDerivative()

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
        self.res.Load()

        # Find column that holds results of interest
        col_idx = self.res.FindColumn(element, var_name)

        if col_idx == -1:
            raise ValueError("Could not find : " + elm_name)

        # Get time steps in the result file
        t_steps = self.res.GetNumberOfRows()

        # Read results and time
        time = np.zeros(t_steps)
        values = np.zeros(t_steps)

        # Iterate through the rows in the result file
        for i in range(t_steps):
            time[i] = self.res.GetValue(i, -1)[1]
            values[i] = self.res.GetValue(i, col_idx)[1]

        return time, values

    def write_results_to_file(self, variables, filepath):
        ''' Writes results to csv-file.

        Args:
            variables  (dict):     maps pf-object to list of variables.
            filepath (string):  filename for the temporary csv-file
        '''

        self.ComRes = self.app.GetFromStudyCase('ComRes')
        self.ComRes.head = []  # Header of the file
        self.ComRes.col_Sep = ';'  # Column separator
        self.ComRes.dec_Sep = ','  # Decimal separator
        self.ComRes.iopt_exp = 6  # Export type (csv)
        self.ComRes.iopt_csel = 1  # Export only user defined vars
        self.ComRes.ciopt_head = 1  # Use parameter names for variables
        self.ComRes.iopt_sep = 0  # Don't use system separators

        self.ComRes.f_name = filepath
        # Adding time as first column
        resultobj = [self.res]
        elements = [self.res]
        cvariable = ['b:tnow']
        self.ComRes.head = []
        # Defining all other results
        for elm_name, var_names in variables.items():
            for element in self.app.GetCalcRelevantObjects(elm_name):
                full_name = element.GetFullName()
                split_name = full_name.split('\\')
                full_name_reduced = []
                for dir in split_name[:-1]:
                    full_name_reduced.append(dir.split('.')[0])
                full_name_reduced.append(split_name[-1])
                full_name_reduced = '\\'.join(full_name_reduced)
                if not ((elm_name in full_name) or
                        (elm_name in full_name_reduced)):
                    continue
                for variable in var_names:
                    self.ComRes.head.append(elm_name+'\\'+variable)
                    elements.append(element)
                    cvariable.append(variable)
                    resultobj.append(self.res)
        self.ComRes.variable = cvariable
        self.ComRes.resultobj = resultobj
        self.ComRes.element = elements

        self.ComRes.ExportFullRange()

    def get_results(self, variables=None, filepath='results.csv'):
        ''' Writes simulation results to csv-file and re-import to dataframe.

        Args:
            variables  (dict):     maps pf-object to list of variables.
            filepath (string):  filename for the temporary csv-file

        Returns:
            dataframe: two-level dataframe with simulation results
            '''
        if not variables and hasattr(self, 'variables'):
            variables = self.variables
        self.write_results_to_file(variables, filepath)

        res = pd.read_csv(filepath, sep=';', decimal=',', header=[0, 1])
        res.rename({i: i.split(':')[1].split(' in ')[0]
                    for i in res.columns.levels[1]}, axis=1, level=1,
                   inplace=True)
        res.set_index(('All calculations', 'tnow'), inplace=True)
        res.index.name = 'time'

        return res

    def set_load_powers(self, p_load, q_load):
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
            if load.loc_name in p_load:
                load.plini = p_load[load.loc_name]
                load.qlini = q_load[load.loc_name]

    def set_generator_powers(self, p_gen, q_gen):
        """Method for setting all generator_powers.

        Args:
            p_gen (Dict): Dictionary where the key is the name of the
                generator and the value is the new active power value.
            q_gen (Dict): Dictionary where the key is the name of the
                generator and the value is the new reactive power value.
        """
        # Collect all generator elements
        gens = self.app.GetCalcRelevantObjects("*.ElmSym")
        gnum = gens[0].ngnum  # number of paralell generators
        # Set active and reactive power values
        for gen in gens:
            if gen.loc_name in p_gen:
                gen.pgini = p_gen[gen.loc_name]/gnum
                gen.qgini = q_gen[gen.loc_name]/gnum

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

    def create_short_circuit(self, target_name, time, name):
        """Create a three phase short circuit.

        Args:
            target_name: Component to short.
            time: Start time of the short circuit.
            name: Name of the event.
        """
        # Get the element where the fault is applied
        target = self.app.GetCalcRelevantObjects(target_name)

        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Create an empty short circuit event
        evt_folder.CreateObject("EvtShc", name)

        # Get the empty short circuit event
        sc = evt_folder.GetContents(name+".EvtShc")[0]

        # Set time, target and type of short circuit
        sc.time = time
        sc.p_target = target[0]
        sc.i_shc = 0

    def delete_short_circuit(self, name):
        """Delete a short circuit event.

        Args:
            name: Name of the event.
         """
        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Find the short circuit and clear event to delete
        sc = evt_folder.GetContents(name+".EvtShc")
        scc = evt_folder.GetContents(name+"_clear"+".EvtShc")
        if sc:
            sc[0].Delete()
        if scc:
            scc[0].Delete()

    def create_switch_event(self, target_name, time, name):
        """Create a switching event.

        Args:
            target_name: Component to switch.
            time: When to switch
            name: Name of the event.
        """
        # Get the element where the fault is applied
        target = self.app.GetCalcRelevantObjects(target_name)

        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Create an empty switch event
        evt_folder.CreateObject("EvtSwitch", name)

        # Get the empty switch event
        sw = evt_folder.GetContents(name+".EvtSwitch")[0]

        # Set time, target and type of short circuit
        sw.time = time
        sw.p_target = target[0]

    def delete_switch_event(self, name):
        """Delete a switch event.

        Args:
            name: Name of the event.
         """
        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Find the switch event and clear event to delete
        sw = evt_folder.GetContents(name+".EvtSwitch")
        sww = evt_folder.GetContents(name+"_clear"+".EvtSwitch")
        if sw:
            sw[0].Delete()
        if sww:
            sww[0].Delete()

    def change_generator_inertia_constant(self, name, value):
        """Change the inertia constant of a generator.

        Args:
            name: Name of the generator.
            value: The inertia constant value.
        """
        elms = self.app.GetCalcRelevantObjects(name)
        elms[0].h = value

    def change_grid_min_short_circuit_power(self, name, value):
        """Change the minimum short circuit power of an external grid.

        Args:
            name: Name of the external grid.
            value: The minimum short circuit power value.
        """
        elms = self.app.GetCalcRelevantObjects(name)
        elms[0].snssmin = value

    def get_output_window_content(self):
        """Returns the messages from the power factory output window."""
        return self.window.GetContent()

    def clear_output_window(self):
        """Clears the output window."""
        self.window.Clear()
