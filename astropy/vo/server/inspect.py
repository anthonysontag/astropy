# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Inspect results from `astropy.vo.server.validate`.

Examples
--------
>>> from astropy.vo.server import inspect

Load Cone Search validation results directly from
`astropy.vo.client.vos_baseurl`:

>>> r = inspect.ConeSearchResults()

Print tally:

>>> r.tally()

Print a list of good Cone Search catalogs:

>>> r.list_cats('good')

List Cone Search catalogs with warnings,
excluding warnings that were ignored in
`astropy.vo.server.noncrit_warnings`,
and writes the output to a file:

>>> with open('warn_cats.txt', 'w') as fout:
>>>     r.list_cats('warn', fout=fout, ignore_noncrit=True)

Print the first good Cone Search catalog:

>>> catkey = r.catkeys['good'][0]
>>> r.print_cat(catkey)

"""
from __future__ import print_function, division

# STDLIB
import os
import sys

# LOCAL
from ..client.vos_catalog import get_remote_catalog_db

__all__ = ['ConeSearchResults']


class ConeSearchResults(object):
    """
    A class to store Cone Search validation results.

    Attributes
    ----------
    dbtypes : list
        Conesearch database identifiers.

    dbs : dict
        Stores `astropy.vo.client.vos_catalog.VOSDatabase`
        for each `dbtypes`.

    catkeys : dict
        Stores sorted catalog keys for each `dbtypes`.

    Parameters
    ----------
    cache : bool
       Read from cache, if available.
       Default is `False` to ensure the latest data are read.

    """
    def __init__(self, cache=False):
        self.dbtypes = ['good', 'warn', 'exception', 'error']
        self.dbs = {}
        self.catkeys = {}

        for typ in self.dbtypes:
            self.dbs[typ] = get_remote_catalog_db(
                'conesearch_' + typ, cache=cache)
            self.catkeys[typ] = self.dbs[typ].list_catalogs(sort=True)

    def tally(self, fout=sys.stdout):
        """
        Tally databases.

        Parameters
        ----------
        fout : output stream
            Default is screen output.

        """
        out_str = ''

        for typ in self.dbtypes:
            out_str += '{}: {} catalogs{}'.format(
                typ, len(self.catkeys[typ]), os.linesep)

        if out_str:
            fout.write(out_str)

    def list_cats(self, typ, fout=sys.stdout, ignore_noncrit=False):
        """
        List catalogs in given database.

        Listing contains:

            #. Catalog key
            #. Cone search access URL
            #. Warning codes
            #. Warning descriptions

        Parameters
        ----------
        typ : string
            Any value in `dbtypes`.

        fout : output stream
            Default is screen output.

        ignore_noncrit : bool
            Exclude warnings in `astropy.vo.server.noncrit_warnings`.
            This is useful to see why a catalog failed validation.

        """
        assert typ in self.dbtypes
        out_str = ''

        for cat in self.catkeys[typ]:
            cat_db = self.dbs[typ].get_catalog(cat)

            if ignore_noncrit:
                out_wt = _exclude_noncrit(cat_db['validate_warning_types'])
                out_ws = _exclude_noncrit(cat_db['validate_warnings'])
            else:
                out_wt = cat_db['validate_warning_types']
                out_ws = cat_db['validate_warnings']

            out_str += os.linesep.join([cat, cat_db['url']])
            if out_wt:
                out_str += os.linesep + ','.join(out_wt)
            if out_ws:
                out_str += os.linesep + os.linesep.join(out_ws)
            out_str += '{0}{0}'.format(os.linesep)

        if out_str:
            fout.write(out_str)

    def print_cat(self, key, fout=sys.stdout):
        """
        Display a single catalog of given key.

        If not found, nothing is written out.

        Parameters
        -----------
        key : string
            Catalog key.

        fout : output stream
            Default is screen output.

        """
        out_str = ''

        for typ in self.dbtypes:
            if key in self.catkeys[typ]:
                out_str += os.linesep.join(
                    [repr(self.dbs[typ].get_catalog(key)),
                     '{1}Found in {0}{1}'.format(typ, os.linesep)])

                # Only has one match, so quits when it is found
                break

        if out_str:
            fout.write(out_str)


def _exclude_noncrit(in_list):
    """
    Exclude any items in input list containing
    `astropy.vo.server.crit_warnings`.

    Parameters
    ----------
    in_list : list
        List of strings to process.

    Returns
    -------
    out_list : list
        List with only qualified strings.

    """
    from .validate import NONCRIT_WARNINGS
    out_list = []
    for s in in_list:
        n = 0
        for w in NONCRIT_WARNINGS():
            n += s.count(w)
        if n == 0:
            out_list.append(s)
    return out_list
