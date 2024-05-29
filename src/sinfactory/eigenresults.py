"""Module for handling eigenvalue results."""


class EigenValueResults(object):
    """Class for holding eigenvalue results."""

    def __init__(self, df, min_damping=None):
        self.df = df
        self.min_damping = min_damping
            

