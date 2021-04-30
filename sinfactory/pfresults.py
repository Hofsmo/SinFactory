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
                                         "rating"])
        self._populate_df(self.gen, grid.gens.values())

        self.load = pd.DataFrame(index=grid.loads.keys(), 
                                 columns=["p_set", "q_set"])
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

        # The interchange between areas used to be included in the area report
        # However, the power factory function for getting inter area flows,
        # require a power flow to be run between each call. It was therefore
        # dropped.

    def _populate_df(self, df, objs,):
        """Populate the result dataframe df with the results from objs."""
        for obj in objs:
            for prop in df.columns:
                df.loc[obj.name, prop] = getattr(obj, prop)

