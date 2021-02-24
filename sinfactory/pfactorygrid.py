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

        self.lines = {}
        for line in self.app.GetCalcRelevantObjects("*.ElmLne"):
            self.lines[line.cDisplayName] = PowerFactoryLine(self.app, line)

        self.lines = {}
        for line in self.app.GetCalcRelevantObjects("*.ElmLne"):
            self.lines[line.cDisplayName] = PowerFactoryLine(self.app, line)

    def activate_study_case(self, study_case_name, folder_name=""):
        """Activate study case."""
        study_case_folder = self.app.GetProjectFolder("study")
        study_case_file = study_case_name + ".IntCase"
        self.study_case = study_case_folder.GetContents(study_case_file)[0]
        self.study_case.Activate()

    def get_ratings(self):
        """Function that gets rated power of all generators.
        
        Returns:
            List of rated power of all machines 
        """
        machines = self.app.GetCalcRelevantObjects("*.ElmSym")  # ElmSym data object
        ratings = []
        for machine in machines:
            ratings.append(
                machine.P_max
            )  # * self.get_number_of_parallell(machine.loc_name))
        return ratings

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

    def initialize_dynamic_sim(
        self,
        var_machines=("m:u:bus1", "m:P:bus1"),
        var_loads=("m:u:bus1", "m:P:bus1"),
        var_lines=("m:u:bus1"),
        var_buses=("m:u", "b:ipat"),
    ):
        """ Initialize dynamic simulation 

        Args:
            var_names: Variables to track. 
        """
        variables = self.generate_variables(
            var_machines=var_machines,
            var_loads=var_loads,
            var_lines=var_lines,
            var_buses=var_buses,
        )
        self.prepare_dynamic_sim(variables=variables)

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

        # Load results from file
        self.res.Load()

        # Find column that holds results of interest
        col_idx = self.res.FindColumn(element, var_name)

        if col_idx == -1:
            raise ValueError("Could not find : ", elm_name)

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
        var_machines=("m:u:bus1", "m:P:bus1"),
        var_loads=("m:u:bus1", "m:P:bus1"),
        var_lines=("m:u:bus1"),
        var_buses=("m:u", "b:ipat"),
    ):
        """ Generate dictionary with variables for all machines

        Args: 
            var_names 
        Returns: 
            Dictionary with all machines with all input variables 
        """
        machines = self.get_machines()
        output = {}
        for machine in machines:
            if self.check_if_in_service(machine):
                output[machine + ".ElmSym"] = list(var_machines)
        loads = self.get_list_of_loads()
        for load in loads:
            output[load + ".ElmLod"] = list(var_loads)
        lines = self.get_line_list()
        for line in lines:
            output[line + ".ElmLne"] = list(var_lines)
        buses = self.get_list_of_buses()
        for bus in buses:
            output[bus + ".ElmTerm"] = list(var_buses)
        return output

    def get_total_load(self):
        """ Get total active load on all buses

        Returns: 
            vector of total load at each bus (length of vector is equal to bus numbers)
         """
        # Collect all load elements
        loads = self.app.GetCalcRelevantObjects("*.ElmLod")
        # Sum up load values
        load_tot = []
        load_val = 0
        bus = loads[0].bus1
        # Iterate through all loads
        for load in loads:
            # Find out to which bus the load is connected
            if load.bus1 != bus:
                bus = load.bus1
                load_tot.append(load_val)
                load_val = load.plini
            else:
                load_val = load_val + load.plini
        # Add the last value to the array
        load_tot.append(load_val)
        return np.array(load_tot)

    def get_total_gen(self):
        """ Get total active power generation on all buses 
        
        Returns: 
            Array with total generation on each bus (length of vector is equal to bus numbers)
        """
        # Get all generator elements
        gens = self.app.GetCalcRelevantObjects("*.ElmSym")  # ElmSym data object
        # Sum up generation values
        gen_tot = []
        gen_val = 0
        bus = gens[0].bus1
        # Iterate through all machines
        for gen in gens:
            # Find out to which bus the machine is connected
            if gen.bus1 != bus:
                bus = gen.bus1
                gen_tot.append(gen_val)
                gen_val = gen.pgini  # *self.get_number_of_parallell(gen.loc_name)
            else:
                gen_val = (
                    gen_val + gen.pgini
                )  # *self.get_number_of_parallell(gen.loc_name)
        # Add the last value to the array
        gen_tot.append(gen_val)
        return np.array(gen_tot)

    def get_number_of_parallell(self, machine):
        """ Get number of parallell machines at plant  

        Args: 
            machine:  machine to get number of parallells  
        
        Returns: 
            number of parallell machines 
        """
        generator = self.app.GetCalcRelevantObjects(machine + ".ElmSym")[
            0
        ]  # ElmSym data object
        return generator.ngnum

    def set_number_of_parallell(self, machine, par_num):
        """ Get number of parallell machines at plant  
        
        Args:
            machine:    name of machine to set initial number of parallell
            par_num:    intial number of parallell machines
        """
        generator = self.app.GetCalcRelevantObjects(machine + ".ElmSym")[
            0
        ]  # ElmSym data object
        generator.ngnum = par_num

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
                gen.pgini = p_gen[gen.loc_name] / gnum
                gen.qgini = q_gen[gen.loc_name] / gnum

    def get_machine_gen(self, machine_name):
        """ Get active power generation from a specific machine 

        Args:
            machine_name: Name of machine to get active power.

        Returns: 
            machine's active power generation 
        """
        # Get machine element (return list with one element)
        machine = self.app.GetCalcRelevantObjects(machine_name + ".ElmSym")[0]
        gen = machine.pgini
        return np.array(gen)

    def change_bus_load(self, load_name, new_load):
        """ Change load at a specific load 

        Args: 
            load_name: name of load
            load: value of new load in MW 
        """
        # Get the load element by returning a list with one element
        load = self.app.GetCalcRelevantObjects(load_name + ".ElmLod")[0]
        load.plini = new_load

    def change_machine_gen(self, machine, new_gen):
        """ Change active power generation at a specific machine 

        Args: 
            machine: name of the machine 
            gen: value of new generation in MW 
        """
        # Get machine element (return list with one element)
        generator = self.app.GetCalcRelevantObjects(machine + ".ElmSym")[0]
        generator.pgini = new_gen

    def get_machines(self):
        """ Function that gets a list of all machine names

        Returns: 
            List of every machine name 
        """
        machines = self.app.GetCalcRelevantObjects("*.ElmSym")
        machine_name_list = []
        for m in machines:
            machine_name_list.append(m.loc_name)
        return machine_name_list

    def check_if_in_service(self, machine):
        """ Check if machine is in service

        Args: 
            Name of the machine
        Returns:
            True if the machine is in service and false otherwise
        """
        obj = self.app.GetCalcRelevantObjects(machine + ".ElmSym")[0]
        return not obj.outserv

    def get_area_load_in(self, load_name):
        """ Function to get the name of the area the load is in

        Args: 
            Name of the load
        Returns: 
            Name of the area the load is in 
        """
        load = self.app.GetCalcRelevantObjects(load_name + ".ElmLod")[0]
        return int(load.cpArea.loc_name)

    def get_area_gen_in(self, machine_name):
        """ Function to get the name of the area the machine is in

        Args: 
            machine_name: Name of the machine
        Returns: 
            Name of the area the machine is in 
        """
        machine = self.app.GetCalcRelevantObjects(machine_name + ".ElmSym")[0]
        return int(machine.cpArea.loc_name)

    def get_area_gen(self, area_name):
        """ Get total generation in a specific area 

        Args:
            area_name: Name of area which is of interest (i.e. "Area1" or "1")
        Returns: 
            total generation in area 
        """
        # Get all the ElmSym data objects
        gens = self.app.GetCalcRelevantObjects("*.ElmSym")
        gen_tot_area = 0
        # Iterate through machine elements to add up generation (area name in powerfactory  MUST be just a number)
        for gen in gens:
            if int(gen.cpArea.loc_name) == area_name:
                gen_tot_area += gen.pgini
        return gen_tot_area

    def get_area_load(self, area_name):
        """ Get total load in a specific area 

        Args:
            area_name: Name of area which is of interest (i.e. "Area1" or "1")
        Returns: 
            total load in area 
        """
        # Get all the ElmLod data objects
        loads = self.app.GetCalcRelevantObjects("*.ElmLod")
        load_tot_area = 0
        # Iterate through machine elements to add up generation (area name in powerfactory  MUST be just a number)
        for load in loads:
            if int(load.cpArea.loc_name) == area_name:
                load_tot_area += load.plini
        return load_tot_area

    def check_islands(self, result):
        """ Check existence of islands. 

        Returns
            true if there is islands and false if not
        """
        var = "ipat"
        buses = self.get_list_of_buses()
        island_var = []
        for bus in buses:
            isolated_area_result = result.loc[1:1000, (bus, var)].values
            end_val = len(isolated_area_result) - 1
            island_var.append(isolated_area_result[end_val])
        return max(island_var)

    def get_island_elements(self, islands, result):
        """ Return list of elemnts of the islands. 

        Args: 
            islands: number of islands 
        Returns
            2-D array where each island corresponds to a row which contains its elements
        """
        var = "ipat"
        elements = self.get_list_of_buses()
        element_list = []
        counter = 0
        while islands - counter > 0:
            element_list.append([])
            counter += 1
        for element in elements:
            isolated_area_result = result.loc[1:1000, (element, var)].values
            end_val = len(isolated_area_result) - 1
            element_list[int(isolated_area_result[end_val]) - 1].append(element)
        return element_list

    def change_connected_loads(self, terminal, new_load):
        """ Change connected loads to new_load

        Args: 
            terminal: change loads connect to this terminal 
            new_load: new value of active power
        """
        terminal = self.app.GetCalcRelevantObjects(terminal + ".ElmTerm")[0]
        cubicles = terminal.GetCalcRelevantCubicles()
        for cubicle in cubicles:
            print(cubicle.obj_id.loc_name)
            if cubicle.obj_id.loc_name in self.get_list_of_loads():
                self.change_bus_load(cubicle.obj_id.loc_name, new_load=new_load)

    def set_out_of_service(self, elm_name):
        """Take an element out of service or 
        reduce number of parallell machines by one 

        Args:
            elm_name: Name of elements to take out of service.
        """
        elm = self.app.GetCalcRelevantObjects(elm_name + ".ElmSym")[0]
        par_num = self.get_number_of_parallell(elm_name)
        if par_num > 1:
            self.set_number_of_parallell(elm_name, par_num - 1)
        else:
            elm.outserv = True

    def set_in_service(self, elm_name):
        """Take an element back in service.

        Args:
            elm_name: Name of elements to take out of service.
        """
        elm = self.app.GetCalcRelevantObjects(elm_name + ".ElmSym")[0]
        elm.outserv = False

    def change_generator_inertia_constant(self, name, value):
        """Change the inertia constant of a generator.

        Args:
            name: Name of the generator.
            value: The inertia constant value.
        """
        machine = self.app.GetCalcRelevantObjects(name + ".ElmSym")[0]
        machine_type = machine.typ_id
        machine_type.h = value

    def change_grid_min_short_circuit_power(self, name, value):
        """Change the minimum short circuit power of an external grid.

        Args:
            name: Name of the external grid.
            value: The minimum short circuit power value.
        """
        elms = self.app.GetCalcRelevantObjects(name)
        elms[0].snssmin = value

    def get_list_of_buses(self):
        """ Function that gets a list of all buses

        Returns: 
            List of every bus name 
        """
        buses = self.app.GetCalcRelevantObjects("*.ElmTerm")
        bus_list = []
        for bus in buses:
            bus_list.append(bus.loc_name)
        return bus_list

    def get_list_of_loads(self):
        """ Function for getting a list of all load names

        Returns: 
            vector of load names
        """
        load_list = []
        loads = self.app.GetCalcRelevantObjects("*.ElmLod")
        for load in loads:
            load_list.append(load.loc_name)
        return load_list

    def get_branch_flow(self, line_name):
        """ Function for getting the flow on a branch 
        
        Args: 
            line_name: Name of branch/line 
        Returns: 
            value of loading on branch 
        """
        # Find branch
        line = self.app.GetCalcRelevantObjects(line_name + ".ElmLne")[0]
        return line.GetAttribute("c:loading")

    def get_all_line_flows(self):
        """ Function for getting all line flows 
        
        Returns: 
            list of all line flows  
        """
        lines = self.get_line_list()
        power_flows = []
        for line in lines:
            power_flows.append(self.get_branch_flow(line))
        output = pd.DataFrame(power_flows, columns=["Power flow"], index=lines)
        return output

    def get_line_list(self):
        """ Get list of line names
        
        Returns: 
            List of all line names 
        """
        lines = self.app.GetCalcRelevantObjects("*.ElmLne")
        line_names = []
        for line in lines:
            line_names.append(line.loc_name)
        return line_names

    def is_ref(self, machine_name):
        """ check if machine is the reference machine 
        
        Args:   
            machine_name: machine name 
        Returns: 
            true if the machine is the reference machine, else false 
        """
        machine = self.app.GetCalcRelevantObjects(machine_name + ".ElmSym")[0]
        return machine.ip_ctrl

    def pole_slip(self, machine_name, result):
        """ Check if there has been a pole slip at any active machines 

        Args:   
            machine_name: name of machine
            result: data frame containing simulation results
        Returns: 
            true if there has been a pole slip at machine
        """
        var = "outofstep"
        pole_var = result.loc[:1000, (machine_name, var)].values
        pole_slip = False
        if np.count_nonzero(pole_var) > 0:
            pole_slip = True

        return pole_slip

    def get_initial_rotor_angles(self, result):
        """ Get relative rotor angles intially 
        Args: 
            result: data frame containing simulation results
        Returns: 
            Initial relative rotor angles for all machines 
        """
        var = "firel"
        machines = self.app.GetCalcRelevantObjects("*.ElmSym")
        result = result[~result.index.duplicated()]
        initial_ang = []
        for m in machines:
            if self.check_if_in_service(m.loc_name):
                pole_slip = result.loc[0, (m.loc_name, "outofstep")]  # always float
                angle = result.loc[0, (m.loc_name, var)]  # .values
                if type(angle) != type(pole_slip):
                    angle = angle.replace(",", ".")
                    angle = float(angle)
                initial_ang.append(angle)
            else:
                initial_ang.append(0)
        return initial_ang

    def get_freq(self):
        """ Get frequencies at all active machines 

        Returns: 
            frequency array for all machine for the whole time period 
        """
        # Get machine element (return list with one element)
        machines = self.get_machines()
        var = ["n:fehz:bus1"]
        freq_all = []
        for machine in machines:
            if self.check_if_in_service(machine):
                time, freq = self.get_dynamic_results(machine + ".ElmSym", var[0])
                freq_all.append(freq)
        return np.transpose(freq_all)

    def get_rotor_angles(self, machine):
        """ Function to get rotor angles 
        """
        var = ["s:firel"]
        time, rotor = self.get_dynamic_results(machine + ".ElmSym", var[0])
        return time, rotor

    def get_voltage_magnitude(self, result, element):
        """ Function to get voltage magnitude  
        Args: 
            result: Dataframe with result 
            element: to get voltage at (load, machine, etc)
            element_type: type of element, generator, load etc
        """
        var = "u"
        voltages = result.loc[1:1000, (element, var)].values
        return voltages

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
        # Identify the machine type (GENSAL - salient pole, or GENROU - round pole)
        for machine in machine_list:
            machine_type.append(machine.typ_id)
            machine_name.append(machine.loc_name)
        inertias = []
        for machine in machine_type:
            inertias.append(2 * machine.sgn * machine.h / omega_0)
        inertia_list = np.column_stack([machine_name, inertias])
        return inertia_list

    def get_inertia(self, machine_name):
        """ Function to get inertia for a machine

        Args: 
            machine_name: name of machine
        Returns: 
            the value of the machines inertia 
        """
        machine_obj = self.app.GetCalcRelevantObjects(machine_name + ".ElmSym")[0]
        machine_type = machine_obj.typ_id
        omega_0 = 50
        inertia = 2 * machine_type.sgn * machine_type.h / omega_0
        return inertia

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
        sc = evt_folder.GetContents(name + ".EvtShc")
        scc = evt_folder.GetContents(name + "_clear" + ".EvtShc")
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
        sw.p_target = target

    def create_trip_line_event(self, target_name, time):
        """Trips a line at both ends"""
        i = 0
        for switch in self.lines[target_name].switches:
            self.create_switch_event("", time, "trip-" + target_name + str(i), switch)
            i += 1

    def delete_trip_line_event(self, target_name):
        """Trips a line at both ends"""
        for i in ["0", "1"]:
            self.delete_switch_event("trip-" + target_name + i)

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

    def run_OPF(self, power_flow=0, obj_function="cst", **kwargs):
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

        for k, v in kwargs:
            setattr(self.opf, k, v)

        return self.opf.Execute()

    def get_OPF_results(self):

        opf_res = {}

        gens = self.app.GetCalcRelevantObjects("*.ElmSym")
        gen_var = ["c:avgCosts", "c:Pdisp", "c:cst_disp"]
        for gen in gens:
            gen_name = gen.GetFullName().split("\\")[-1].split(".")[0]
            opf_res[gen_name] = {i.split(":")[1]: gen.GetAttribute(i) for i in gen_var}

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
            line_name = line.GetFullName().split("\\")[-1].split(".")[0]
            opf_res[line_name] = {
                i.split(":")[1]: line.GetAttribute(i) for i in line_var
            }

        grid = self.app.GetCalcRelevantObjects("*.ElmNet")[0]
        sys_var = ["c:cst_disp", "c:LossP", "c:LossQ", "c:GenP", "c:GenQ"]
        opf_res["system"] = {i.split(":")[1]: grid.GetAttribute(i) for i in sys_var}
        opf_res = pd.DataFrame(opf_res).unstack().dropna()

        return opf_res

    def get_inter_area_flow(self, area1, area2):
        """Returns the flow between two area

        Args:
            area1: Name of the first area.
            area2: Name of the second area.
        """
        obj1 = self.app.GetCalcRelevantObjects(area1 + ".ElmArea")[0]
        obj2 = self.app.GetCalcRelevantObjects(area2 + ".ElmArea")[0]

        obj1.CalculateInterchangeTo(obj2)
        return obj1.GetAttribute("c:Pinter")
