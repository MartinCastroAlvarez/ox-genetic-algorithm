"""
AUTHOR: Martin Alejandro Castro Alvarez
EMAIL: martincastro.10.5@gmail.com
HOME: https://www.martincastroalvarez.com
DATE: 2019, Feb 21th.

This is a Genetic Algorithm aimed at solving
the problem described in the following link:
https://cmind.kattis.com/test/programming/regsw7x4fvc39dhhhuxfd7chwvst9si2/problems/cd8c43d7b3d83c95

WARNING: There is one condition that I haven't understood:
The restriction for all i !~ j, Si !~ Sj. However, I hope I have
built a small system that allows me easily add new features.

You can run this script by executing the following instructions:
>>> virtualenv -p python3.4 env
>>> source env/bin/activate
>>> pip install -r requirements.txt
>>> cat sample-01.in | python3 edith.py

The expected output is:
>>> (.env) [martin@M7 edith]$ python3 edith.py
Case 1 dearalanhowareyou
Case 2 ienjoycorresponding
Case 3 abcd
Case 4 IMPOSSIBLE

You can also see all the flags looking at the script help:
>>> python3 edith.py -h
usage: edith.py [-h] [--debug] [--no-debug]
                [--ages AGES]
optional arguments:
  -h, --help            show this help message and exit
  --debug               Use this flag to enable the debug/verbose mode.
                        (default: False)
  --no-debug
  --ages AGES, -a AGES  Amount of iterations. (default: 10)

You can run unit tests by executing the following command:
>>> python -m unittest test_edith.py

This code is compliant with PEP-8 standards:
https://www.python.org/dev/peps/pep-0008/
You can check it by running the following instruction:
>>> flake8 edith.py
"""

import os
import sys
import logging

import numpy as np
import pandas as pd

import begin

from io import StringIO

logger = logging.getLogger(__name__)


class Genes(object):
    """
    Genes in this Genetic Algorithm represent the
    set of (a, b) pairs in the search space.

    @constant A: Represents the set of all 'a' elements in the genetic pairs.
    @constant B: Represents the set of all 'b' elements in the genetic pairs.
    """

    A = "A"
    B = "B"

    def __init__(self, genes: str=None):
        """
        Constructing the genetic code.

        @param genes: A string containing 2 columns is required.
                      The first column will be 'a' and the second
                      column will be 'b'.
        """
        logger.debug("Constructing genetic code.")
        if not genes:
            raise ValueError("Genetic code must not be empty.")
        if not isinstance(genes, str):
            raise ValueError("Expecting a string, not:", type(genes))
        self.genes = pd.read_csv(StringIO(genes),
                                 header=None,
                                 sep=" ",
                                 names=[self.A, self.B])
        self.genes = self.genes.reindex(columns=[self.A, self.B])
        # self.genes = self.genes[self.genes[self.A] != self.genes[self.B]]
        logger.debug(self.genes)

    def get_genes(self, **kwargs) -> pd.DataFrame:
        """
        Genes getter.

        This function returns the Pandas DataFrame
        containing the genetic pairs.

        The purpose of this method is to provide
        custom mutations in the future. For example,
        by getting only genes that start with "s".
        """
        return self.genes

    @property
    def size(self) -> int:
        """
        Size getter.

        This function returns the size of the genetic code.
        """
        return len(self.genes)

    def __str__(self):
        """ To String method. """
        return "<Genes: {}>".format(self.size)


class Population(object):
    """
    This class represents the active survivors playing the game.

    In each run, the population mutates and fitness is evaluated.
    Survivors and unfit chromosomes are removed from the population.

    You can keep mutating the population endlessly until
    there are no more possible combinations.

    @constant A_DOMINANCE: It represents gene A being stronger than gene B.
    @constant B_DOMINANCE: It represents gene B being stronger than gene A.

    @constant UNFIT: It is used to mark chromosomes as unfit.
    @constant FIT: It is used to detect winner chromosomes.

    @constant TMP_SUFFIX: It is a temporal constant used to merge datasets.
    @constant TMP_INDEX: It is a temporal constant used to merge datasets.
    """

    A_DOMINANCE = "A Dominance"
    B_DOMINANCE = "B Dominance"

    UNFIT = "_unfit"
    FIT = "_fit"

    TMP_SUFFIX = "_new"
    TMP_INDEX = "_tmp_idx"

    def __init__(self, genes: Genes=None):
        """
        Population constructor.

        @param genes: A Genes instance is required.
                      Mutations will take genes from this
                      instance and generate variations.

        NOTE: The initial set of chromosomes will only contain
              pairs of genes whose first character match in order
              to reduce the algorithm complexity.
        """
        logger.debug("Constructing new population.")
        if not isinstance(genes, Genes):
            raise ValueError("Invalid genes:", genes)
        if not genes.size:
            raise RuntimeError("Empty genetic code.")
        self.genes = genes
        genes = self.genes.get_genes()
        self.survivors = pd.DataFrame()
        condition = genes[self.genes.A].str[0] == genes[self.genes.B].str[0]
        self.chromosomes = genes[condition][[self.genes.A, self.genes.B]]
        self.fit()

    def __str__(self):
        """ To String method. """
        return "<Population: {}>".format(self.size)

    @property
    def size(self) -> int:
        """
        Size getter.

        This function returns the amount of
        active chromosomes in this population.
        """
        return len(self.chromosomes)

    def get_survivor(self, default: str=None) -> str:
        """
        Survivor getter.

        This function returns the survivor name.

        If multiple surivors exist, only the first will be returned.
        The list of survivors will be arranged by string length
        and then in alphabetical order

        @param default: String value that will be
                        returned if there are no survivors.
        """
        if self.survivors.empty:
            return default
        self.survivors[self.TMP_INDEX] = self.survivors[self.genes.A].str.len()
        s = self.survivors.sort_values([self.TMP_INDEX, self.genes.A],
                                       ascending=[True, True])
        return s.iloc[0][self.genes.A]

    def fit(self):
        """
        This method is used to detect the fitness of the population.

        The dominance of genes 'A' and 'B' will be calculated.
        After that, unfit chromosomes will be removed.
        """
        logger.debug("Fitting population.")
        self.__calculate_dominance()
        self.__remove_unfit()
        self.__remove_fit()
        logger.debug(self.chromosomes)

    @property
    def shortest_survivor(self) -> int:
        """ Property to access the length of the shortest survivor. """
        return self.survivors[self.genes.A].str.len().min()

    @property
    def shortest_chromosome(self) -> int:
        """ Property to access the length of the shortest chromosome. """
        return self.chromosomes[self.genes.A].str.len().min()

    def __calculate_dominance(self):
        """
        This private method will calculate the dominance of
        gene 'A' over 'B' as well as the dominance of 'B' over 'A'.

        For example, if 'A' is 'asdf' and 'B' is 'as', then 'A' is dominant.
        The dominance will be 'df' because 'asdf' - 'as' = 'df'

        This can be later used to remove unfit chromosomes.
        """
        a_dominance = self.chromosomes[[self.genes.A,
                                        self.genes.B]].apply(self.get_fitness,
                                                             axis=1)
        self.chromosomes[self.A_DOMINANCE] = a_dominance
        b_dominance = self.chromosomes[[self.genes.B,
                                        self.genes.A]].apply(self.get_fitness,
                                                             axis=1)
        self.chromosomes[self.B_DOMINANCE] = b_dominance

    @classmethod
    def get_fitness(cls, row: list) -> str:
        """
        This function must be used to calculate
        the string distance of 2 strings in a DataFrame.

        @param row: A DataFrame containing 2 elements.

        It will return FIT if the 2 strings match.
        It will return UNFIT if strings don't match.

        For example:
        >>> fitness("AJYFAJYF", "AJY")
        'FAJYF'
        >>> fitness("AASD", "FD")
        '_unfit'
        >>> fitness("AA", "AA")
        '_fit'
        """
        a = row.iloc[0]
        b = row.iloc[1]
        if a == b:
            return cls.FIT
        if a.startswith(b):
            return a[len(b):]
        return cls.UNFIT

    def __remove_unfit(self):
        """
        This private method will remove unfit chromosomes
        from the population.

        For example, only one gene can be dominant.
        If 'A' and 'B' are both dominant, it means the
        genes can not fuse and the chromosome will adapt.
        """
        is_a_unfit = self.chromosomes[self.A_DOMINANCE] == self.UNFIT
        is_b_unfit = self.chromosomes[self.B_DOMINANCE] == self.UNFIT
        condition = is_a_unfit & is_b_unfit
        if condition.any():
            logger.debug("Removing %s unfit chromosome(s).",
                         condition.value_counts()[True])
        self.chromosomes = self.chromosomes[~condition]

    def __remove_fit(self):
        """
        This private method detects winners in the population.

        Chromosomes that match the expected result will be
        removed from the chromosomes dataset and put into
        a different dataset.

        As a consequence, they won't be used for further mutations
        because there is at least 1 survivor that has higher
        alphabetical priority in the final result.
        """
        is_a_fit = self.chromosomes[self.A_DOMINANCE] == self.FIT
        is_b_fit = self.chromosomes[self.B_DOMINANCE] == self.FIT
        condition = is_a_fit | is_b_fit
        local_survivors = self.chromosomes[condition]
        local_survivors = local_survivors.reset_index()
        self.survivors = pd.concat([self.survivors, local_survivors])
        self.chromosomes = self.chromosomes[~condition]

    def mutate(self):
        """
        Genetic Mutation method.

        A new set of genes will be generated from the genetic code.

        Then, it will be combined with the current chromosomes
        in order to create more chromosomes from both.
        """
        logger.debug("Mutating population.")

        # The following code is requied to merge 2 DataFrames.
        query = {
            self.TMP_INDEX: np.nan,
        }
        previous_genes = self.chromosomes.assign(**query)
        new_genes = self.genes.get_genes()
        new_genes = new_genes.assign(**query)
        new_generation = pd.merge(previous_genes,
                                  new_genes,
                                  suffixes=("", self.TMP_SUFFIX),
                                  on=self.TMP_INDEX,
                                  how='outer')

        # Genes 'A' and 'B' from both genetic codes
        # will be concatenated in the following section.
        logger.debug(new_genes)
        logger.debug(previous_genes)
        previous_a = new_generation[self.genes.A]
        previous_b = new_generation[self.genes.B]
        new_a = new_generation[self.genes.A + self.TMP_SUFFIX]
        new_b = new_generation[self.genes.B + self.TMP_SUFFIX]
        new_generation[self.genes.A] = previous_a + new_a
        new_generation[self.genes.B] = previous_b + new_b

        # Chromosomes in this population will be replaced
        # with the new generation of chromosomes.
        self.chromosomes = new_generation[[self.genes.A, self.genes.B]]
        logger.debug(self.chromosomes)


class Sequence(object):
    """
    A Sequence represents a population mutating their
    genes over multiple configurable ages. Unfit chromosomes
    are removed from the population and only the fittest survive.

    @constant IMPOSSIBLE: Used to mark sequences as unresolvable.
    """

    IMPOSSIBLE = "IMPOSSIBLE"

    def __init__(self, genes: Genes=None, ages: int=10):
        """
        Sequence Constructor.

        @param genes: A Genes instance containing the genetic code.
        @param ages: The amount of iterations in which the
                     population will mutate.
        """
        if not isinstance(genes, Genes):
            raise ValueError("Invalid genes:", genes)
        if not isinstance(ages, int) or ages < 1:
            raise ValueError("Invalid amount of ages:", ages)
        self.ages = ages
        self.population = Population(genes=genes)

    def __str__(self):
        """ To String method. """
        return "<Sequence: {}>".format(self.ages)

    def run(self):
        """
        Main method.

        This method will run multiple times, mutation the
        population and attempting to get a survivor chromosome.

        At the end of the iterations, the winner can be
        retrieved by executing: self.population.get_survivor().
        """
        logger.debug("Analyzing sequence.")
        if not self.population.chromosomes.empty:
            for age in range(self.ages):
                logger.debug("Running on age: %s/%s.", age + 1, self.ages)
                self.population.mutate()
                self.population.fit()
                if self.population.chromosomes.empty:
                    logger.debug("Breaking iteration.")
                    break
                if self.population.shortest_survivor < self.population.shortest_chromosome:
                    logger.debug("Solution found.")
                    break

        logger.debug("Finished analyzing sequence.")


@begin.start
def run(debug: "Use this flag to enable the debug/verbose mode."=False,
        ages: "Amount of iterations."=10):
    """
    This function is required by "begin" to provide shell script access.

    @param debug: Use this flag to enable the debug/verbose mode.
    @param ages: Amount of iterations.
    """

    # If debug mode is enabled, it will log messages to stdout.
    if debug:
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.DEBUG)

    # The following piece of code reads from stdin
    # and truncates the input by case length..
    for case_number, line in enumerate(sys.stdin):
        case_length = int(line)  # WARNING: May raise ValueError.
        case_data = "\n".join([
            next(sys.stdin).replace("\n", "")
            for _ in range(case_length)
        ])

        # This is where the Genetic Algorithm is executed.
        # It will run once per case in the input file.
        g = Genes(case_data)
        s = Sequence(genes=g, ages=g.size)
        s.run()

        # Printing results to STDOUT.
        title = "Case {}:".format(case_number + 1)
        print(title, s.population.get_survivor(Sequence.IMPOSSIBLE))
