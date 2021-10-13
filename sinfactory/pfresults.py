"""Module for handling power flow results."""
import pandas as pd


class PFResults(object):
    """Class containing power flow results."""

    def __init__(self, grid):
        """Initialise the result class for power flow results.

        Args:
            grid: The grid to generate the results for.
        """
        
        # In case this slows down simulations that don't need all results
        # we can change to generate the results on demand.
        self.gen = pd.DataFrame(index=grid.gens.keys(), 
                                columns=["p_set", "q_set", "n_machines", "h",
                                         "rating", "in_service",
                                         "u_rel_angle"])
        self._populate_df(self.gen, grid.gens.values())

        self.load = pd.DataFrame(index=grid.loads.keys(), 
                                 columns=["p_set", "q_set",
                                          "in_service"])
        self._populate_df(self.load, grid.loads.values())

        self.line = pd.DataFrame(index=grid.lines.keys(),
                                 columns=["p", "loading"])
        self._populate_df(self.line, grid.lines.values())

        self.area = pd.DataFrame(index=grid.areas.keys(),
                                 columns=["loads", "gens"])

        for area in self.area.index:
            for column in self.area.columns:
                if column in ["loads", "gens"]:
                    self.area.loc[area,
                                  column] = grid.areas[area].get_total_var(
                                      column)

        self.inter_area = pd.DataFrame(index=grid.inter_lines.keys(),
                                       columns=["p"])
        for name, lines in grid.inter_lines.items():
            self.inter_area.loc[name, "p"] = sum(line.p for line in lines)

    def _populate_df(self, df, objs,):
        """Populate the result dataframe df with the results from objs."""
        for obj in objs:
            for prop in df.columns:
                df.loc[obj.name, prop] = getattr(obj, prop)

    @staticmethod
    def get_attributes(units, properties=["p_set", "q_set"]):
        """Get specified properties in a DF from a set of
        units, i.e. loads"""
        df = pd.DataFrame()
        for unit in units.items():
            for prop in properties:
                df.at[unit[0], prop] = getattr(unit[1], prop)
        return df
