
pydsge
======

Contains the functions and classes for solving, filtering and estimating DSGE models @ZLB (or with other OBCs). Not well documented and very rawwwww.

A collection of models that can (and were) used with this package can be found in `another repo <https://github.com/gboehl/projectlib/tree/master/yamls>`_.

The code is in alpha state and provided for reasons of collaboration, replicability and code sharing in the spirit of open science. It does not (and for now, can not) have a toolbox character. The code is operational, but (yet) not ready for public use and I can not provide any support. You are however very welcome to get in touch if you are interested working with the package.

The beta stage will probably involve considerable restructuring of packages, code, and the API.

The dependencies are listed in the setup.py file. Note that this package depends on the ``econsieve`` and ``grgrlib`` packages which both can be found on my github page, but not yet on `PyPI <https://pypi.org/>`_ (they will thus not be installed automatically via ``pip``\ , at least for now). 

The code does *not* work with Python 2.x!


Documentation
-------

There is some `preliminary documentation <https://pydsge.readthedocs.io/en/latest/index.html>`_ out there.

- `Installation Guide <https://pydsge.readthedocs.io/en/latest/installation_guide.html>`_
- `Getting Started <https://pydsge.readthedocs.io/en/latest/getting_started.html>`_
- `Module Documentation <https://pydsge.readthedocs.io/en/latest/modules.html>`_

Citation
--------

**pydsge** is developed by Gregor Boehl to simulate, filter, and estimate DSGE models with the zero lower bound on nominal interest rates in various applications (see `my website <https://gregorboehl.com>`_ for research papers using the package). Please cite it with

.. code-block::

    @Software{boehl2020,
      Title  = {pydsge -- A package to simulate, filter, and estimate DSGE models with occasionally binding constraints},
      Author = {Gregor Boehl},
      Year   = {2020},
      Url    = {https://github.com/gboehl/pydsge},
    }

We appreciate citations for **pydsge** because it helps us to find out how people have
been using the package and it motivates further work.


Parser
------

The parser originally was a fork of Ed Herbst's fork from Pablo Winant's (excellent) package **dolo**. 

See https://github.com/EconForge/dolo and https://github.com/eph.


References
----------

Boehl, Gregor (2020). `Efficient Solution, Filtering and Estimation of Models with OBCs <http://gregorboehl.com/live/obc_boehl.pdf>`_. *Unpublished Manuscript*
