"""Module for interfacing with power factory."""


import os
import numpy as np
import pandas as pd
import powerfactory as pf
from sinfactory.line import PowerFactoryLine


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

        # Get the output window
        self.window = self.app.GetOutputWindow()

        # Get the load flow obect
        self.ldf = self.app.GetFromStudyCase("ComLdf")
        
        self.lines = {}
        for line in self.app.GetCalcRelevantObjects("*.ElmLne"):
            self.lines[line.cDisplayName] = PowerFactoryLine(self.app, line)

    def activate_sudy_case(self, study_case_name, folder_name=""):
        # Activate study case.
        study_case_folder = self.app.GetProjectFolder('study')
        study_case_file = study_case_name + '.IntCase'
        self.study_case = study_case_folder.GetContents(study_case_file)[0]
        self.study_case.Activate()
        self.ldf = self.app.GetFromStudyCase("ComLdf")

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

        res = pd.read_csv(filepath, sep=';', decimal=',', header=[0, 1],
                          index_col=0)
        res.rename({i: i.split(':')[1].split(' in ')[0]
                    for i in res.columns.levels[1]}, axis=1, level=1,
                   inplace=True)
        res.columns.rename(('unit', 'variable'), level=[0, 1], inplace=True)
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

    def create_switch_event(self, target_name, time, name, target=None):
        """Create a switching event.

        Args:
            target_name: Name of component to switch.
            time: When to switch
            name: Name of the event.
            comp: Object to create the event for
        """
        if target is None:
            # Get the element where the fault is applied
            target = self.app.GetCalcRelevantObjects(target_name)[0]

        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Create an empty switch event
        evt_folder.CreateObject("EvtSwitch", name)

        # Get the empty switch event
        sw = evt_folder.GetContents(name+".EvtSwitch")[0]

        # Set time, target and type of short circuit
        sw.time = time
        sw.p_target = target

    def create_trip_line_event(self, target_name, time):
        """Trips a line at both ends"""
        i = 0
        for switch in self.lines[target_name].switches:
            self.create_switch_event("", time, "trip-"+target_name+str(i), 
                                     switch)
            i += 1
    
    def delete_trip_line_event(self, target_name):
        """Trips a line at both ends"""
        for i in ["0", "1"]:
            self.delete_switch_event("trip-"+target_name+i)

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

    def run_load_flow(self, balanced=0, power_control=0, slack=0):
        """Method for running a load flow.

        Args:
            balanced: 
                0: Three phase balanced load flow.
                1: Three phase unbalanced load flow.
                2: DC load flow.
            power_control:
                0: As dispatched
                1: According to secondary control
                2: According to primary control
                3: According to inertias
            slack: This is only relevant if power_control is 0
                0: By reference machine
                1: By load at reference bus
                2: By static generator at reference bus
                3: By loads
                4: By synchronous generators
                5: By synchronous generators and static generators
            """

        self.ldf.ipot_net = balanced
        self.ldf.iopt_aptdist = power_control
        self.ldf.iPbalancing = slack

        return self.ldf.Execute()

    def set_element_OPF_attr(self, attr, element_type,
                             relative_attr={'Pmin_uc': 'P_max',
                                            'Pmax_uc': 'P_max'}):
        """ Set attributes of element in optimal power flow
        Args:
            attribute (str)
            element_type (str) e.g. *.ElmSym for all generators
        """
        for elm in self.app.GetCalcRelevantObjects(element_type):
            for k, v in attr.items():
                if k in relative_attr.keys():
                    base_val = getattr(elm, relative_attr[k])
                    v_mod = np.array(v)*base_val
                    setattr(elm, k, v_mod.tolist())
                else:
                    setattr(elm, k, v)

    def set_generator_OPF_cost(self, cost_dict):
        """ Set generator cost attributes for optimal power flow
        Args:
            cost_segments: double dict
                key 1:  generator names,
                dict 2: ccost: list of segment cost_data
                        cpower: list of segment power
                        iInterPol: int
                           0: spline
                           1: piecewiselinear
                           2: polynomial
                           3: hermine
                        penaltyCost: float
                        fixedCost: float
        """
        for cf, cost_data in cost_dict.items():

            if len(cost_data['ccost']) != len(cost_data['cpower']):
                print("Number of segments for cost and power is not equal!")

            gen_set = cost_data['generators']

            for gen_name in gen_set:
                relative_attr = ['ccost', 'cpower']
                gen = self.app.GetCalcRelevantObjects(gen_name + '.ElmSym')[0]
                for k, v in cost_data.items():
                    if k == 'generators':
                        continue
                    if k in relative_attr:
                        v_mod = np.array(v)*gen.P_max
                        setattr(gen, k, v_mod.tolist())
                        continue
                    setattr(gen, k, v)

    def run_OPF(self, power_flow=0, obj_function='cst', **kwargs):
        """Method for running optimal power flow

        Args:
            power_flow:
                0: AC optimization (interior point method)
                1: DC optimization (linear programming (LP))
                2: Contingency constrained DC optimization (LP))
            obj_function:
                los: Minimization of losses (total)
                slo: Minimization of losses (selection)
                cst: Minimization of cost
                shd: Minimization of load shedding
                rpr: Maximization of reactive power reserve
                dev: Minimization of control variable deviations
        Kwargs:
            Controls (boolean):
                iopt_pd:  Generator active power dispatch
                iopt_qd: Generator/SVS reactive power dispatch
                iopt_trf: Transformer tap positions
                iopt_sht: Switchable shunts
                iopt_genP: Active power limits of generators
                iopt_genQ: Reactive power limits of generators/SVS
                iopt_brnch: Branch flow limits (max. loading)
                iopt_bus: Voltage limits of busbars/terminals
                iopt_add: Boundary flow limits
            Soft constraints (boolean):
                penaltySoftConstr: Penalty factor for soft constraints (float)
                isForceSoftPLims: Enforce soft active power limits of
                                    generators
                isForceSoftQLims: Enforce soft reactive power limits of
                                    generators/SVS
                isForceSoftLoadingLims: Enforce soft branch flow limits
                                        (max. loading)
                isForceSoftVoltageLims: Enforce soft voltage limits of
                                        busbars/terminal
        """

        if not hasattr(self, 'opf'):
            self.opf = self.app.GetFromStudyCase('ComOpf')

        self.opf.ipopt_ACDC = power_flow
        self.opf.iopt_obj = obj_function

        for k, v in kwargs:
            setattr(self.opf, k, v)

        return self.opf.Execute()

    def get_OPF_results(self):

        opf_res = {}

        gens = self.app.GetCalcRelevantObjects('*.ElmSym')
        gen_var = ['c:avgCosts', 'c:Pdisp', 'c:cst_disp']
        for gen in gens:
            gen_name = gen.GetFullName().split('\\')[-1].split('.')[0]
            opf_res[gen_name] = {i.split(':')[-1]:
                                 gen.GetAttribute(i) for i in gen_var}

        # loads = self.app.GetCalcRelevantObjects('*.ElmLod')
        # load_var = ['c:Pdisp']
        # for load in loads:
        #     load_name = load.GetFullName().split('\\')[-1].split('.')[0]
        #     opf_res[load_name] = {i.split(':')[-1]:
        #                           load.GetAttribute(i) for i in load_var}

        grid = self.app.GetCalcRelevantObjects('*.ElmNet')[0]
        sys_var = ['c:cst_disp', 'c:LossP', 'c:LossQ', 'c:GenP', 'c:GenQ']
        opf_res['system'] = {i.split(':')[-1]:
                             grid.GetAttribute(i) for i in sys_var}
        opf_res = pd.DataFrame(opf_res).unstack().dropna()

        return opf_res

    def get_inter_area_flow(self, area1, area2):
        """Returns the flow between two area

        Args:
            area1: Name of the first area.
            area2: Name of the second area.
        """
        obj1 = self.app.GetCalcRelevantObjects(area1+".ElmArea")[0]
        obj2 = self.app.GetCalcRelevantObjects(area2+".ElmArea")[0]

        obj1.CalculateInterchangeTo(obj2)
        return obj1.GetAttribute("c:Pinter")
