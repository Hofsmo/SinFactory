"""Module for interfacing with power factory."""

import os
import numpy as np
import powerfactory as pf

class PFactoryGrid(object):
    """Class for interfacing with powerfactory."""
    def __init__(self, project_name, study_case_name, folder_name=''):
        """Class constructor."""
        # Start PowerFactory.
        self.app = pf.GetApplication() #powerfactory.application object created and returned 

        if self.app is None:
            raise RuntimeError("Failed to load powerfactory.")

        # Activate project.
        self.project = self.app.ActivateProject(os.path.join(folder_name,
                                                             project_name))

        if self.project is None:
            raise RuntimeError("No project activated.")

        # Activate study case.
        study_case_folder = self.app.GetProjectFolder('study')
        print("Case study name:") 
        print(study_case_name)
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
        self.sim.tstop = end_time

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

    def get_total_load(self):   
        """ Get total active load on all buses """
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
        """ Get total active power generation on all buses """
        # Get all generator elements
        gens = self.app.GetCalcRelevantObjects("*.ElmSym") # ElmSym data object
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
                gen_val = gen.pgini
            else: 
                gen_val = gen_val + gen.pgini
        # Add the last value to the array
        gen_tot.append(gen_val)
        return np.array(gen_tot) 

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
        # Set active and reactive power values
        for gen in gens:
            if gen.loc_name in p_gen:
                gen.pgini = p_gen[gen.loc_name]
                gen.qgini = q_gen[gen.loc_name]

    

    def get_machine_gen(self, elm_name): 
        """ Get active power generation from a specific machine 

        Args:
            elm_name: Name of elements to get active power.
        """
        # Get machine element (return list with one element)
        machine = self.app.GetCalcRelevantObjects(elm_name) 
        gen = machine[0].pgini
        return np.array(gen) 

    def change_bus_load(self,bus_number,new_load):
        """ Change load at a specific load 

        Args: 
            bus_number: name of bus the load is connected to (str)
            load: value of new load in MW 
        """
        bus_name = "bus"+str(bus_number)
        cubs = self.app.GetCalcRelevantObjects("*.StaCubic")
        # Iterate through all cubs 
        for cub in cubs: 
            # Check if cub is connected to the bus
            if cub.cterm.loc_name == bus_name: 
                elm_type = cub.obj_id.GetClassName()
                # Check if a connected element is a load
                if elm_type == "ElmLod": 
                    elm_name = cub.obj_id.loc_name+".ElmLod"

        # Get the load element by returning a list with one element            
        load = self.app.GetCalcRelevantObjects(elm_name) 
        load[0].plini = new_load

        # Alternative with other input: 
        """" Alternative with these Args:
            elm_name: Name of elements to change load.
            new_load: value of active power which the load is chaning to

            Code is simply:  
            load = self.app.GetCalcRelevantObjects(elm_name) # return list with one element
            load[0].plini = new_load
        """ 

    def change_machine_gen(self,machine,new_gen):
        """ Change active power generation at a specific machine 

        Args: 
            machine: name of the machine 
            gen: value of new generation in MW 
        """
        # Get machine name 
        machine = self.get_machine_name(machine.bus_number, machine.mid)
        elm_name = machine.loc_name+".ElmSym"
        # Get machine element (return list with one element)
        generator = self.app.GetCalcRelevantObjects(elm_name) 
        generator[0].pgini = new_gen
    
    def get_machine_name(self,bus_nr,id): 
        """ Get machine name in powerfactory based on id and bus number 
            Return the machine object, to get the name, use attribute loc_name
        """ 
        machines = self.app.GetCalcRelevantObjects("*.ElmSym") 
        for machine in machines:
            # First digit in bus_nr is the denoting the area of the bus
            if int(machine.desc[0][0:5]) == bus_nr:
                if int(machine.desc[0][6]) == id: 
                    elm_name = machine 
        return elm_name

    def get_area_gen(self, area_num):
        """ Get total generation in a specific area 

        Args:
            area_num: Name of area which is of interest (i.e. "Area1")
        """ 
        # Get all the ElmSym data objects
        gens = self.app.GetCalcRelevantObjects("*.ElmSym") 
        gen_tot_area = 0
        # Iterate through machine elements to add up generation (area name in powerfactory  MUST be just a number)
        for gen in gens:
            if int(gen.cpArea.loc_name) == area_num: 
                gen_tot_area = gen_tot_area + gen.pgini
        return gen_tot_area

    def get_area_load(self, area_num):
        """ Get total load in a specific area 

        Args:
            area_num: Name of area which is of interest (i.e. "Area1")
        """ 
        # Get all the ElmLod data objects
        loads = self.app.GetCalcRelevantObjects("*.ElmLod") 
        load_tot_area = 0
        # Iterate through machine elements to add up generation (area name in powerfactory  MUST be just a number)
        for load in loads:
            if int(load.cpArea.loc_name) == area_num: 
                load_tot_area = load_tot_area + load.plini
        return load_tot_area

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
    
    def get_load_busses(self):
        """ 
        Function for getting the bus names with loads as an array

        """
        load_buses = []
        cubs = self.app.GetCalcRelevantObjects("*.StaCubic")
        for cub in cubs: 
            elm_type = cub.obj_id.GetClassName()
            if elm_type == "ElmLod":
                # Stores the bus number the load is connected to (Possible to store the elements, i.e. remove .loc_name)
                load_buses.append(cub.cterm.loc_name[3:8]) 
        return load_buses
        

    def power_flow_calc(self):
        """ Function for running power flow """
        LDF = self.app.GetFromStudyCase("ComLdf")
        LDF.Execute() 

    def power_calc_converged(self):
        """ Function for checking whether power flow calc converged """
        print("Convergence check")

    def gen_out_of_service(self,machine):
        """ Function for setting generator out of service """
        machine = self.get_machine_name(machine.bus_number, machine.mid)
        elm_name = machine.loc_name+".ElmSym"
        self.set_out_of_service(elm_name)
    
    def initiate_dynamic_sim(self,system,outputfile): 
        # run prepare_dynamic_sim
        print("Initiate simulation.")
    
    def get_branch_flow(self,bus_from,bus_to):
        """ Function for getting the flow on a branch """  
        # Find branch
        line = self.find_branch(bus_from,bus_to)
        if line.bus1 or line.bus2 == bus_name_to:
            name = line.loc_name
            value = line.GetAttribute("c:loading")
            print("Loading of",name,"is", value, "%")
        return value
    
    def find_branch(self, bus_from, bus_to): 
        """ Find branch based on bus bars 
        """
        bus_name_from = "bus"+str(bus_from)
        bus_name_to = "bus"+str(bus_to)
        cubs = self.app.GetCalcRelevantObjects("*.StaCubic")
        # Search through the cubs to find the correct element 
        for cub in cubs: 
            if cub.cterm.loc_name == bus_name_from: #check if cub is connected to the bus
                elm_type = cub.obj_id.GetClassName()
                if elm_type == "ElmLne": #check if a connected element is a line
                    line = cub.obj_id
        return line

    def fault_branch(self,bus_from,bus_to):
        """ Function for placing a fault on a branch """
        # Find branch
        line = self.find_branch(bus_from,bus_to)

        # Create short circuit event 
        self.create_short_circuit(line, 1, "SC1")

    def trip_branch(self, bus_from, bus_to):
        """ Function for tripping a branch """ 
        # Find branch
        line = self.find_branch(bus_from,bus_to)

        # Create triupping event 
        self.create_switch_event(line, 1, "trip1")

    def get_channel_data(self,outputfile):
        """ Function for getting the channel data """
        raise NotImplementedError

    def run_sim(self, time):
        """ Function for running the simulation up to a given time """
        monitor = {"Synchronous Machine(32).ElmSym": ["n:fehz:bus1"], "Synchronous Machine(18).ElmSym": ["n:fehz:bus1"]}
        self.prepare_dynamic_sim(variables=monitor,end_time=time)
        self.run_dynamic_sim()
    
    def run_sim_initial(self,time):
        """ Function for running the simulation initially up to a given time """
        monitor = {"Synchronous Machine(32).ElmSym": ["n:fehz:bus1"], "Synchronous Machine(18).ElmSym": ["n:fehz:bus1"]}
        self.prepare_dynamic_sim(variables=monitor,start_tine = 0, end_time=time)
        self.run_dynamic_sim()

    def get_machines_inertia_list(self):
        """
        Function to get array of all machines inertias,'M', corresponding to
        2HS/omega_0. 

        """
        #generator types (ed up with H array) 
        omega_0 = 50 
        machine_list = self.app.GetCalcRelevantObjects("*.ElmSym") 
        machine_type = []
        # Identify the machine type (GENSAL - salient pole, or GENROU - round pole) 
        for machine in machine_list:
            machine_type.append(machine.typ_id)
        inertias = [] 
        for machine in machine_type:
            inertias.append(2*machine.sgn*machine.h/omega_0)
        return inertias

    def get_machine_list(self): 
        """
        Function to get machine list
        """ 
        # np.array containing the bus number and id of every generator in the network
        # PF: Attribute desc (description) contains bus nr and id, e.g. 10005 0
        bus_nr = []
        machine_id = []
        machines = self.app.GetCalcRelevantObjects("*.ElmSym") 
        # Copy bus_nr and id into array 
        for machine in machines:
            bus_nr.append(int(machine.desc[0][0:5]))
            machine_id.append(int(machine.desc[0][6]))
        # Convert to numpy array 
        bus_number = np.array(bus_nr)
        machine_ID = np.array(machine_id)

        machine_list = np.row_stack([bus_number,machine_ID])
        return machine_list
    