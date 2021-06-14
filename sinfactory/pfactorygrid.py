"""Module for interfacing with power factory."""

import os
import itertools
import numpy as np
import pandas as pd
import powerfactory as pf
from sinfactory.line import Line
from sinfactory.generator import Generator
from sinfactory.load import Load
from sinfactory.area import Area
from sinfactory.bus import Bus
from sinfactory.eigenresults import EigenValueResults
from sinfactory.pfresults import PFResults


class PFactoryGrid(object):
    """Class for interfacing with powerfactory."""

    def __init__(self, project_name):
        """Class constructor."""
        # Start PowerFactory.
        self.app = (
            pf.GetApplication()
        )  # powerfactory.application object created and returned

        if self.app is None:
            raise RuntimeError("Failed to load powerfactory.")

        # Activate project.
        self.project = self.app.ActivateProject(project_name)

        if self.project is None:
            raise RuntimeError("No project activated.")

        # Get the output window
        self.window = self.app.GetOutputWindow()

        # Get the load flow object
        self.ldf = self.app.GetFromStudyCase("ComLdf")
        
        self.lines = {line.cDisplayName: Line(line) for line in
                      self.app.GetCalcRelevantObjects("*.ElmLne")}

        self.gens = {gen.cDisplayName: Generator(gen) for gen in
                     self.app.GetCalcRelevantObjects("*.ElmSym")}
        
        self.loads = {load.cDisplayName: Load(load) for load in
                      self.app.GetCalcRelevantObjects("*.ElmLod")}
        
        self.areas = {area.GetFullName(
        ).split("\\")[-1].split(".")[0]: Area(area)
                      for area in self.app.GetCalcRelevantObjects("*.ElmArea")}
        
        self.buses = {bus.cDisplayName: Bus(bus) for bus in
                      self.app.GetCalcRelevantObjects("*.ElmTerm")}

    def activate_study_case(self, study_case_name, folder_name=""):
        """Activate study case."""
        study_case_folder = self.app.GetProjectFolder("study")
        study_case_file = study_case_name + ".IntCase"
        self.study_case = study_case_folder.GetContents(study_case_file)[0]
        self.study_case.Activate()

    def prepare_dynamic_sim(
        self,
        sim_type="rms",
        variables={},
        start_time=0.0,
        step_size=0.01,
        end_time=10.0,
    ):
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
        self.res = self.app.GetFromStudyCase("*.ElmRes")
        # Select result variable to monitor.
        for elm_name, var_names in variables.items():
            # Get all elements that match elm_name
            elements = self.app.GetCalcRelevantObjects(elm_name)
            # Select variables to monitor for each element
            for element in elements:
                self.res.AddVars(element, *var_names)

        # Retrieve initial conditions and time domain simulation object
        self.inc = self.app.GetFromStudyCase("ComInc")
        self.sim = self.app.GetFromStudyCase("ComSim")

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

    def initialize_and_run_dynamic_sim(
        self,
        var_machines=("m:u:bus1", "m:P:bus1", "s:outofstep", "s:firel"),
        var_loads=("m:u:bus1", "m:P:bus1"),
        var_lines=("m:u:bus1", "c:loading"),
        var_buses=("m:u", "b:ipat"),
        sim_time=10.0
    ):
        """ Initialize and run dynamic simulation.
            Saving result file as attribute. 

        Args:
            var_names: Variables to track. 
        """
        variables = self.generate_variables(
            var_machines=var_machines,
            var_loads=var_loads,
            var_lines=var_lines,
            var_buses=var_buses,
        )
        self.prepare_dynamic_sim(variables=variables, end_time=sim_time)
        self.run_dynamic_sim()
        self.result = self.get_results(variables=variables)

    def run_dynamic_sim(self):
        """Run dynamic simulation.

        Returns:
            bool: False for success, True otherwise.
        """

        return bool(self.sim.Execute())

    def write_results_to_file(self, variables, filepath):
        """ Writes results to csv-file.

        Args:
            variables  (dict):     maps pf-object to list of variables.
            filepath (string):  filename for the temporary csv-file
        """

        self.ComRes = self.app.GetFromStudyCase("ComRes")
        self.ComRes.head = []  # Header of the file
        self.ComRes.col_Sep = ","  # Column separator
        self.ComRes.dec_Sep = "."  # Decimal separator
        self.ComRes.iopt_exp = 6  # Export type (csv)
        self.ComRes.iopt_csel = 1  # Export only user defined vars
        self.ComRes.ciopt_head = 1  # Use parameter names for variables
        self.ComRes.iopt_sep = 0  # Don't use system separators

        self.ComRes.f_name = filepath
        # Adding time as first column
        resultobj = [self.res]
        elements = [self.res]
        cvariable = ["b:tnow"]
        self.ComRes.head = []
        # Defining all other results
        for elm_name, var_names in variables.items():
            for element in self.app.GetCalcRelevantObjects(elm_name):
                full_name = element.GetFullName()
                split_name = full_name.split("\\")
                full_name_reduced = []
                for dir in split_name[:-1]:
                    full_name_reduced.append(dir.split(".")[0])
                full_name_reduced.append(split_name[-1])
                full_name_reduced = "\\".join(full_name_reduced)
                if not ((elm_name in full_name) or (elm_name in full_name_reduced)):
                    continue
                for variable in var_names:
                    self.ComRes.head.append(elm_name + "\\" + variable)
                    elements.append(element)
                    cvariable.append(variable)
                    resultobj.append(self.res)
        self.ComRes.variable = cvariable
        self.ComRes.resultobj = resultobj
        self.ComRes.element = elements

        self.ComRes.ExportFullRange()

    def get_results(self, variables=None, filepath="results.csv"):
        """ Writes simulation results to csv-file and re-import to dataframe.

        Args:
            variables  (dict):     maps pf-object to list of variables.
            filepath (string):  filename for the temporary csv-file

        Returns:
            dataframe: two-level dataframe with simulation results
        """
        if not variables and hasattr(self, "variables"):
            variables = self.variables
        self.write_results_to_file(variables, filepath)

        res = pd.read_csv(filepath, sep=",", decimal=".", header=[0, 1], index_col=0)
        # res.dropna(how='any')
        res = res.apply(pd.to_numeric, errors="coerce").astype(float)
        res.rename(
            {i: i.split(":")[1].split(" in ")[0] for i in res.columns.levels[1]},
            axis=1,
            level=1,
            inplace=True,
        )
        res.columns.rename(("unit", "variable"), level=[0, 1], inplace=True)
        res.index.name = "time"

        return res

    def generate_variables(
        self,
        var_machines=("m:u:bus1", "m:P:bus1", "s:outofstep", "s:firel"),
        var_loads=("m:u:bus1", "m:P:bus1"),
        var_lines=("m:u:bus1", "c:loading"),
        var_buses=("m:u", "b:ipat"),
    ):
        """ Generate dictionary with variables for all machines

        Args:
            var_names 
        Returns: 
            Dictionary with all machines with all input variables 
        """
        output = {}
        for name, gen in self.gens.items():
            if gen.in_service:
                output[name + ".ElmSym"] = list(var_machines)
        for name in self.loads.keys():
            output[name + ".ElmLod"] = list(var_loads)
        for name in self.lines.keys():
            output[name + ".ElmLne"] = list(var_lines)
        for name in self.buses.keys():
            output[name + ".ElmTerm"] = list(var_buses)
        return output

    def check_islands(self):
        """ Check existence of islands. 

        Returns
            true if there is islands and false if not
        """
        var = "ipat"
        island_var = []
        for bus in self.buses.keys():
            isolated_area_result = self.result.loc[1:1000, (bus, var)].values
            end_val = len(isolated_area_result) - 1
            island_var.append(isolated_area_result[end_val])
        return max(island_var)

    def get_island_elements(self, islands):
        """ Return list of elemnts of the islands. 

        Args: 
            islands: number of islands 
        Returns
            2-D array where each island corresponds to a row which contains
            its elements
        """
        var = "ipat"
        element_list = []
        counter = 0
        while islands - counter > 0:
            element_list.append([])
            counter += 1
        for elm in self.buses.keys():
            isolated_area_result = self.result.loc[:, (elm, var)].values
            end_val = len(isolated_area_result) - 1
            element_list[int(isolated_area_result[end_val]) - 1].append(elm)
        return element_list

    def get_init_value(self, feature_name, loads, machines, tripped_lines,
                       dynamic=False):
        """ Generate and return intial value of a feature. 
        
            Args: 
                feature_name: name of feature
                loads: loads in an island
                machines: machines in an island
                tripped_lines: tripped lines 
                dynamic: dynamic simulation or static (default)
            Returns: 
                value: value of selected feature
        """
        value = -1
        if feature_name == "COI angle":
            if dynamic: 
                init_ang = self.get_initial_rotor_angles(
                    machine_names=machines)
                num = 0
                denum = 0
                for i, m in enumerate(machines):
                    num += (
                        self.get_inertia(m)
                        * self.get_number_of_parallell(m) * init_ang[i]
                    )
                    denum += self.get_inertia(
                        m) * self.get_number_of_parallell(m)
                value = num / denum
            else: 
                init_ang = self.get_rotor_angles_static(machine_names=machines)
                num = 0
                denum = 0
                for i, m in enumerate(machines):
                    num += (
                        self.get_inertia(
                            m) * self.get_number_of_parallell(m) * init_ang[i]
                    )
                    denum += self.get_inertia(
                        m) * self.get_number_of_parallell(m)
                value = num / denum
        elif feature_name == "Production":
            value = 0
            if dynamic: 
                for machine in machines:
                    production = self.get_active_power(machine)
                    value += production[0]
            else: 
                for machine in machines:
                    machine_obj = self.app.GetCalcRelevantObjects(
                        machine+".ElmSym")
                    value += machine_obj.pgini
        elif feature_name == "Net flow":
            net_flow = 0
            for line in tripped_lines:
                net_flow += self.get_branch_flow(line)
            value = net_flow
        elif feature_name == "Max flow":
            max_flow = 0
            for line in tripped_lines:
                flow = self.get_branch_flow(line)
                if flow > max_flow:
                    max_flow = flow
            value = max_flow
        elif feature_name == "Load":
            value = 0
            if dynamic:
                for load in loads:
                    consumption = self.get_active_power(load)
                    value += consumption[0]
            else: 
                for load in loads:
                    load_obj = self.app.GetCalcRelevantObjects(
                        machine+".ElmLod")
                    value += load_obj.plini
        elif feature_name == "Inertia":
            value = 0
            for machine in machines:
                value += self.get_inertia(
                    machine) * self.get_number_of_parallell(machine)
        elif feature_name == "Clearing time":
            print("Clearing time: NotImplementedError")
        return value

    def find_connected_element(self, elm_name, elm_type):
        """ Find connected elements of elm_type connected to an elm_name

        Args:
            elm_name: element that is relevant to find its connected element
            elm_type: type of element which is wanted to find
        Returns:
            connected_element: name of connected element of elm_type
        """
        elm = self.app.GetCalcRelevantObjects(elm_name + ".*")[0]
        cubicles = elm.GetCalcRelevantCubicles()
        for cubicle in cubicles:
            connected_element = cubicle.obj_id.loc_name
            try:
                load = self.app.GetCalcRelevantObjects(
                    connected_element + elm_type)[0]
            except:
                load = None
            if load is not None:
                return connected_element

    def pole_slip(self, machine_name):
        """ Check if there has been a pole slip at any active machines 

        Args:   
            machine_name: name of machine
        Returns: 
            true if there has been a pole slip at machine
        """
        var = "outofstep"
        pole_var = self.result.loc[:, (machine_name, var)].values
        pole_slip = False
        if np.count_nonzero(pole_var) > 0:
            pole_slip = True

        return pole_slip
    
    def get_rotor_angles_static(self, machine_names=None): 
        """ Get relative rotor angles from load flow simulations
        
        Returns: 
            Initial relative rotor angles for all machines 
        """
        if machine_names is None:
            machines = self.app.GetCalcRelevantObjects("*.ElmSym")
        else:
            machines = []
            for machine_name in machine_names:
                machine_object = self.app.GetCalcRelevantObjects(
                    machine_name + ".ElmSym"
                )
                machines.append(machine_object[0])
        rotor_ang = []
        phi_ref = 0
        for m in machines:
            if self.check_if_in_service(m.loc_name):
                u_t = m.GetAttribute("n:u1:bus1")
                i_t = m.GetAttribute("m:i1:bus1")
                r_stator = m.typ_id.rstr
                x_q = m.typ_id.xq
                phi = np.arctan(u_t + i_t*(r_stator+x_q))*180/np.pi - 90
                if self.is_ref(m.loc_name):
                    rotor_ang.append(0)
                    phi_ref = phi
                else:
                    rotor_ang.append(phi-phi_ref-m.GetAttribute(
                        "n:phiurel:bus1"))
        return rotor_ang

    def get_initial_rotor_angles(self):
        """ Get initial relative rotor angles 
        
        Returns: 
            Initial relative rotor angles for all machines 
        """
        var = "firel"
        initial_ang = []
        for name, gen in self.gens.items():
            if gen.in_service:
                pole_slip = self.result.loc[
                    0, (name, "outofstep")
                ]  # always float
                angle = self.result.loc[0, (name, var)]  # .values
                if type(angle) != type(pole_slip):
                    angle = angle.replace(",", ".")
                    angle = float(angle)
                initial_ang.append(angle)
            else:
                initial_ang.append(0)
        return initial_ang

    # TODO, this mehtod should be generalised and a test made
    def get_generator_voltage_angles(self, machine_names=None):
        """ Get machine voltage angles 
        
        Returns: 
            Voltage angles for all machines 
        """
        if machine_names is None:
            machines = self.app.GetCalcRelevantObjects("*.ElmSym")
        else:
            machines = []
            for machine_name in machine_names:
                machine_object = self.app.GetCalcRelevantObjects(
                    machine_name + ".ElmSym"
                )
                machines.append(machine_object[0])
        initial_ang = []
        for m in machines:
            if self.check_if_in_service(m.loc_name):
                initial_ang.append(m.GetAttribute("n:phiurel:bus1"))
            else:
                initial_ang.append(0)
        return initial_ang

    def get_machines_inertia_list(self):
        """
        Function to get array of all machines inertias,'M', corresponding to
        2HS/omega_0. 

        Returns: 
            List with machine name and corresponding inertia 
        """
        # generator types (ed up with H array)
        omega_0 = 50
        machine_list = self.app.GetCalcRelevantObjects("*.ElmSym")
        machine_type = []
        machine_name = []
        # Identify the machine type
        # (GENSAL - salient pole, or GENROU - round pole)
        for machine in machine_list:
            machine_type.append(machine.typ_id)
            machine_name.append(machine.loc_name)
        inertias = []
        for machine in machine_type:
            inertias.append(2 * machine.sgn * machine.h / omega_0)
        inertia_list = np.column_stack([machine_name, inertias])
        return inertia_list

    def create_short_circuit(self, target, time, name):
        """Create a three phase short circuit.

        Args:
            target: Component to short.
            time: Start time of the short circuit.
            name: Name of the event.
        """
        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Get event name of events in folder
        events = [i.loc_name for i in evt_folder.GetContents("*.EvtShc")]

        # Delete existing events with the same name
        if name in events:
            self.delete_short_circuit(name)

        # Create an empty short circuit event
        evt_folder.CreateObject("EvtShc", name)

        # Get the empty short circuit event
        sc = evt_folder.GetContents(name + ".EvtShc")[0]

        # Set time, target and type of short circuit
        sc.time = time
        sc.p_target = target.pf_object
        sc.i_shc = 0

    def delete_short_circuit(self, name):
        """Delete a short circuit event.

        Args:
            name: Name of the event.
         """
        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Find the short circuit and clear event to delete
        sc = evt_folder.GetContents(name + ".EvtShc")
        scc = evt_folder.GetContents(name + "_clear" + ".EvtShc")
        if sc:
            sc[0].Delete()
        if scc:
            scc[0].Delete()

    def create_switch_event(self, target, time, name=None):
        """Create a switching event.

        Args:
            target: Component to switch.
            time: When to switch
            name: Name of the event.
            comp: Object to create the event for
        """
        if not name:
            name = target.name + "_switch"

        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Get event name of events in folder
        events = [i.loc_name for i in evt_folder.GetContents("*.EvtSwitch")]

        # Delete existing events with the same name
        if name in events:
            self.delete_switch_event(name)

        # Create an empty switch event
        evt_folder.CreateObject("EvtSwitch", name)

        # Get the empty switch event
        sw = evt_folder.GetContents(name + ".EvtSwitch")[0]

        # Set time, target and type of short circuit
        sw.time = time
        sw.p_target = target.pf_object

    def delete_switch_event(self, name):
        """Delete a switch event.

        Args:
            name: Name of the event.
         """
        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")

        # Find the switch event and clear event to delete
        sw = evt_folder.GetContents(name + ".EvtSwitch")
        sww = evt_folder.GetContents(name + "_clear" + ".EvtSwitch")
        if sw:
            sw[0].Delete()
        if sww:
            sww[0].Delete()

    def clear_all_events(self):

        # Get the event folder
        evt_folder = self.app.GetFromStudyCase("IntEvt")
        # Get a list of all events
        events = evt_folder.GetContents("*")

        # Loop through all events and use the correct delete function
        for e in events:
            evt_name = e.loc_name
            evt_class = e.GetClassName()
            if evt_class == "EvtSwitch":
                self.delete_short_circuit(evt_name)
            elif evt_class == "EvtShc":
                if evt_name.split("-")[0] == "trip":
                    self.delete_trip_line_event(evt_name)
                else:
                    self.delete_switch_event(evt_name)

    def get_events(self):
        """ Return a list of events """
        evt_folder = self.app.GetFromStudyCase("IntEvt")
        events = [i.loc_name for i in evt_folder.GetContents()]
        return events

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

    def set_element_OPF_attr(
        self, attr, element_type, relative_attr={"Pmin_uc": "P_max", "Pmax_uc": "P_max"}
    ):
        """ Set attributes of element in optimal power flow
        Args:
            attribute (str)
            element_type (str) e.g. *.ElmSym for all generators
        """
        for elm in self.app.GetCalcRelevantObjects(element_type):
            for k, v in attr.items():
                if k in relative_attr.keys():
                    base_val = getattr(elm, relative_attr[k])
                    v_mod = np.array(v) * base_val
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

            if len(cost_data["ccost"]) != len(cost_data["cpower"]):
                print("Number of segments for cost and power is not equal!")

            gen_set = cost_data["generators"]

            for gen_name in gen_set:
                relative_attr = ["ccost", "cpower"]
                gen = self.app.GetCalcRelevantObjects(gen_name + ".ElmSym")[0]
                for k, v in cost_data.items():
                    if k == "generators":
                        continue
                    if k in relative_attr:
                        v_mod = np.array(v) * gen.P_max
                        setattr(gen, k, v_mod.tolist())
                        continue
                    setattr(gen, k, v)

    def run_OPF(self, power_flow=0, obj_function='cst', attributes={}):
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

        if not hasattr(self, "opf"):
            self.opf = self.app.GetFromStudyCase("ComOpf")

        self.opf.ipopt_ACDC = power_flow
        self.opf.iopt_obj = obj_function

        for k, v in attributes.items():
            setattr(self.opf, k, v)

        return self.opf.Execute()

    def get_OPF_results(self):

        opf_res = {}

        gens = self.app.GetCalcRelevantObjects("*.ElmSym")
        gen_var = ["c:avgCosts", "c:Pdisp", "c:cst_disp"]
        for gen in gens:
            gen_name = gen.GetFullName().split("\\")[-1].split(".")[0]
            opf_res[gen_name] = {i.split(":")[1]: gen.GetAttribute(i)
                                 for i in gen_var}

        loads = self.app.GetCalcRelevantObjects("*.ElmLod")
        load_var = ["m:P:bus1", "c:Pmism"]
        for load in loads:
            load_name = load.GetFullName().split("\\")[-1].split(".")[0]
            opf_res[load_name] = {
                i.split(":")[1]: load.GetAttribute(i) for i in load_var
            }

        lines = self.app.GetCalcRelevantObjects("*.ElmLne")
        line_var = ["m:P:bus1", "c:loading"]
        for line in lines:
            if not line.outserv:
                line_name = line.GetFullName().split('\\')[-1].split('.')[0]
                opf_res[line_name] = {
                  i.split(':')[1]: line.GetAttribute(i) for i in line_var
                }

        grid = self.app.GetCalcRelevantObjects('*.ElmNet')[0]
        sys_var = ['c:cst_disp', 'c:LossP', 'c:LossQ', 'c:GenP', 'c:GenQ']
        opf_res['system'] = {i.split(':')[1]: grid.GetAttribute(i)
                             for i in sys_var}

        opf_res = pd.DataFrame(opf_res).unstack().dropna()

        return opf_res

    def calculate_isf(self, lines=None,
                      delta_p=5, balanced=0, power_control=0, slack=0):
        """Method that calculates the injection shift factors for tie lines

        This method calculates the injection shift factors for tie lines
        given all generators. These factors can be used for redispatching
        generation to alleviate tie line overloads. The method can be
        extended to also consider changes in loads. The resulting matrix is
        an (m x n) matrix where m is the number of tie lines in the system
        and n is the number of generators.
        
        Args:
            lines: The lines to include in the ISF matrix. The default is all.
            delta_p: Amount of power to change on generator
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

        if not lines:
            lines = self.lines

        gens = self.gens.values()
        isf = np.zeros((len(lines), len(gens)))
        for idx, gen in enumerate(gens):
            # Run load flow before changing the power
            if self.run_load_flow(balanced, power_control, slack):
                raise RuntimeError("Power flow did not converge")

            # Get the load flow before changing power
            y_0 = [line.p for line in lines.values()]

            # Change flow and calculate ISF
            p = float(gen.p_set)
            gen.p_set = delta_p+p
            self.run_load_flow(balanced, power_control, slack)
            y_1 = [line.p for line in lines.values()]
            isf[:, idx] = (np.array(y_1)-np.array(y_0))/delta_p

            # Change the load back
            gen.p_set = p

        return isf

    def calculate_eigenvalues(self, res_file="Modal_Analysis"):
        """Method that calulates the eigenvalues of a system.
        Args:
            res_file: The name of the file to read the results from.
        """
        mode = self.app.GetFromStudyCase("ComMod")  # Modal analysis
        mode.Execute()
        res = self.app.GetFromStudyCase(res_file+'.ElmRes')
        res.Load()  # load the data for reading
        # We want to store a, b, frequency, and damping
        df = pd.DataFrame(np.zeros((res.GetNumberOfRows(), 4)),
                          columns=["a", "b", "damping", "frequency"])
        min_damping = np.inf
        for i in range(0, res.GetNumberOfRows()):
            a = res.GetValue(i, 0)[1]
            b = res.GetValue(i, 1)[1]
            df.iloc[i, 3] = abs(b/2/np.pi)
            df.iloc[i, 0] = a
            df.iloc[i, 1] = b
            df.iloc[i, 2] = -a/np.sqrt(a**2 + b**2)
            if df.iloc[i, 2] < min_damping:
                min_damping = df.iloc[i, 2]

        return EigenValueResults(df, min_damping)

    def init_system_from_res(self, res):
        """Initialise system from old results."""
        self.init_objs_from_df(res.gen, self.gens)
        self.init_objs_from_df(res.load, self.loads)

    def init_objs_from_df(self, df, objs):
        """Initialise an object type from df."""
        for obj in df.index:
            for prop in df.columns:
                setattr(objs[obj], prop, df.loc[obj, prop])

    def change_os(self, series):
        """Initialise the grid from a pandas Series
        
        The panda series should have multi index, where the first index
        is the type of component, loads, gens, lines or areas. The second index
        should be the name of the component, and the third index is the
        property to set."""

        for idx in series.index:
            obj = getattr(self, idx[0])
            setattr(obj[idx[1]], idx[2], series[idx])

    def get_total_load(self):
        """Return the total load of the system."""
        return sum(load.p_set for load in self.loads.values())
    
    def get_total_gen(self):
        """Return the total load of the system."""
        return sum(gen.p_set for gen in self.gens.values())

    def get_pf_results(self):
        """Return a PFResults object."""
        return PFResults(self)
