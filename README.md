<!--
SPDX-FileCopyrightText: Open Energy Transition gGmbH, Ember, and contributors to the Ember Flexibility Study
SPDX-License-Identifier: CC-BY-4.0
-->

# Ember Flexibility Study

<img src="https://raw.githubusercontent.com/open-energy-transition/Ember-Flexibility-Study/refs/heads/master/doc/img/ember_oet.png" alt="Open Energy Transition Logo" width="200" height="234" align="right">

This repository contains the model and analysis code for the **Ember Flexibility Study**, conducted in collaboration with [Ember](https://ember-climate.org/) and [Open Energy Transition (OET)](https://openenergytransition.org/). The study investigates clean flexibility options for Europe's energy system, building on the PyPSA-Eur framework. All results are computed from raw data and code to ensure full reproducibility.

This repository is a soft-fork of [OET-PyPSA-Eur](https://github.com/open-energy-transition/pypsa-eur) and contains the entire project **Clean Flexibility for Europe's Energy System** supported by [Open Energy Transition (OET)](https://openenergytransition.org/), including code and report. 

This repository is maintained using [OET's soft-fork strategy](https://open-energy-transition.github.io/handbook/docs/Engineering/SoftForkStrategy). OET's primary aim is to contribute as much as possible to the open source (OS) upstream repositories. For long-term changes that cannot be directly merged upstream, the strategy organizes and maintains OET forks, ensuring they remain up-to-date and compatible with upstream, while also supporting future contributions back to the OS repositories.

---

# PyPSA ecosystem
PyPSA-Eur is an open model dataset of the European energy system at the transmission network level that covers the full ENTSO-E area. It covers demand and supply for all energy sectors. Built on a foundation of collaborative development, PyPSA-Eur leverages several other open-source tools that are co-maintained by [TU Berlin](https://www.tu.berlin/en/) in partnership with OET. These tools include:
- **PyPSA**: a Python software package for simulating and optimizing modern power systems ([PyPSA](https://pypsa.readthedocs.io/en/stable/))
- **Atlite**: a lightweight Python package for calculating renewable power potentials and time series ([Atlite](https://atlite.readthedocs.io/en/latest/))
- **powerplantmatching**: a toolset for cleaning, standardizing and combining multiple power plant databases ([powerplantmatching](https://github.com/PyPSA/powerplantmatching))
- **technology-data**: the repository compiles assumptions on energy system technologies (costs and efficiencies) for various years ([technology-data](https://github.com/PyPSA/technology-data))
- **linopy**: a Python package that provides a linear optimization interface for N-D labeled variables, with the aim of making linear programming easy, flexible, and performant ([linopy](https://linopy.readthedocs.io/en/latest/))

Together, these tools form a comprehensive ecosystem that supports detailed, transparent, and reproducible energy system analysis across Europe.

---

# Installation and usage

In order to run the Ember Flexibility Study, the following steps are required:

1. [Install prerequisites](#1-install-prerequisites): set up the required software and system dependencies.
2. [Fork the repository](#2-fork-the-repository): create your own copy of the repository on GitHub.
3. [Clone the forked repository](#3-clone-the-forked-repository): download the source code to your local machine.
4. [Set up the upstream repositories](#4-set-up-the-upstream-repositories): set up the upstream repositories to keep your fork up to date.
5. [Set up the environment](#5-set-up-the-environment): create and activate the project-specific virtual environment.

## 1. Install prerequisites

The Ember Flexibility Study project uses a series of software tools. The following steps describe how to install the required software and system dependencies.

### Install Git

Git is a version control system used to track changes in code and support collaborative development. The Ember Flexibility Study project uses Git to manage its source code, making it easy for developers to contribute and for users to access the latest updates.

To access the source code of the platform and run it locally, you’ll need Git installed on your system. You can find installation instructions on the [official Git website](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

### Install Miniconda

Miniconda is a package manager for conda-based environments. An environment is an isolated workspace that contains specific versions of Python and other packages needed to run a project, preventing conflicts
between different projects' dependencies. 

We recommend to use Miniconda to manage the Ember Flexibility Study project environments. However, other package managers can be used, such as [Anaconda](https://www.anaconda.com/) or [mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html). 

To install Miniconda, follow the instructions on the [Anaconda website](https://www.anaconda.com/download/success).

## 2. Fork the repository

Fork the repository [Ember-Flexibility-Study](https://github.com/open-energy-transition/Ember-Flexibility-Study/) on GitHub to your own account. Please make sure to check the box `Copy the master branch only`. 

## 3. Clone the forked repository

Once all the required software and system dependencies are installed, you can proceed to clone the **forked** Ember Flexibility Study repository to your local machine.

To do so, open a terminal and navigate to the directory where you’d like the project to be installed—referred to here as `{installation_directory}`. Then, run the following command:

```bash
git clone https://github.com/<your-username>/Ember-Flexibility-Study.git
```

## 4. Set up the upstream repositories

Once you have cloned your fork, you should add the following upstream remotes to keep your repository up to date with the main projects:

- Add the main [Ember-Flexibility-Study](https://github.com/open-energy-transition/Ember-Flexibility-Study/) repository as `upstream`:

      git remote add upstream https://github.com/open-energy-transition/Ember-Flexibility-Study.git

- Add the main OET soft-fork of PyPSA-Eur as `upstream_pypsa_eur_oet`:

      git remote add upstream_pypsa_eur_oet https://github.com/open-energy-transition/pypsa-eur.git

This setup allows you to fetch and integrate changes from both the main study repository and the OET soft-fork of PyPSA-Eur.

### (Optional) Merging changes from upstream repositories

To keep your fork up to date, you can merge changes from the master branch of either `upstream_pypsa_eur_oet` or `upstream` as follows:

- To merge changes from the OET soft-fork of PyPSA-Eur:

      git fetch upstream_pypsa_eur_oet
      git merge upstream_pypsa_eur_oet/master

- To merge changes from the main Ember-Flexibility-Study repository:

      git fetch upstream
      git merge upstream/master

Resolve any conflicts if they arise, then push the updates to your fork if needed.

## 5. Set up the environment
  
Once the forked repository is cloned, you can set up the environment to run the analysis. In the terminal, navigate to the repository directory `{installation_directory}/Ember-Flexibility-Study`, and run the following command:

```bash
conda env create -f envs\win-64.lock.yaml -n ember-study
```
Please choose the **appropriate** environment file based on your operating system. An environment named `ember-study` will be created. It contains the required dependencies to run the Ember Flexibility Study. Afterwards, you can activate the environment by running:

```bash
conda activate ember-study
```
---

# Repository structure

The following is an overview of the directory structure of the Ember Flexibility Study repository. Each folder serves a specific purpose within the workflow, facilitating reproducibility and efficient management of the project.

* `benchmarks`: will store `snakemake` benchmarks (does not exist initially)
* `config`: configurations used in the study
* `cutouts`: will store raw weather data cutouts from `atlite` (does not exist initially)
* `data`: includes input data that is not produced by any `snakemake` rule
* `doc`: includes all files necessary to build the `readthedocs` documentation of PyPSA-Eur
* `envs`: includes all the `mamba` environment specifications to run the workflow
* `logs`: will store log files (does not exist initially)
* `notebooks`: includes all the `notebooks` used for ad-hoc analysis
* `report`: contains all files necessary to build the report; plots and result files are generated automatically
* `rules`: includes all the `snakemake`rules loaded in the `Snakefile`
* `resources`: will store intermediate results of the workflow which can be picked up again by subsequent rules (does not exist initially)
* `results`: will store the solved PyPSA network data, summary files and plots (does not exist initially)
* `scripts`: includes all the Python scripts executed by the `snakemake` rules to build the model

---

# What is Snakemake?

[Snakemake](https://snakemake.readthedocs.io/) is a workflow management system that enables reproducible and scalable data analyses. It allows you to define complex pipelines in a readable Python-based language, automatically handling dependencies, job execution, and resource management. Snakemake is widely used in scientific computing for automating data processing, analysis, and reporting.

## Defining Rules in Snakemake

Snakemake workflows are built from modular units called **rules**. Each rule specifies how to create output files from input files, using scripts or shell commands. Rules define the steps of your workflow and their dependencies, making it easy to manage complex pipelines.

## Main Snakemake Command-Line Keys

Here are some of the most important command-line options (keys) to control the workflow:

- `-j`, `--jobs [N]`: Set the maximum number of jobs to run in parallel (e.g., `-j 4`).
- `-c`, `--cores [N]`: Specify the number of CPU cores to use (e.g., `-c 1`).
- `-n`, `--dryrun`: Show what would be executed without actually running the workflow.
- `-s`, `--snakefile [FILE]`: Specify a custom Snakefile (default is `Snakefile`).
- `-R`, `--rerun-incomplete`: Re-run jobs with incomplete output files.
- `--unlock`: Unlock the working directory if a previous run was interrupted.
- `--dag`: Print the directed acyclic graph (DAG) of jobs in the workflow.
- `--forceall`: Force the execution of all rules, regardless of output file timestamps.
- `-k`, `--keep-going`: Continue as much as possible after an error.
- `--config [KEY=VALUE,...]`: Override config file values from the command line.

For a full list of options, see the [Snakemake documentation](https://snakemake.readthedocs.io/en/stable/executing/cli.html) or run `snakemake --help`.

## Important Rules in Ember Flexibility Study

In [Ember-Flexibility-Study](https://github.com/open-energy-transition/Ember-Flexibility-Study/), the Snakemake rules are included in dedicated `.smk` files contained `rules` directory. Some of the most important rules that structure the workflow include:

- **retrieve**: downloads and prepares all required input data .
- **build_network**: constructs the base energy system network from input data.
- **prepare_sector**: prepares sector-coupling data (e.g., heating, transport).
- **solve_network**: runs the optimization to solve the energy system model.
- **postprocess**: processes and analyzes the results after solving.
- **plot_network**: generates plots and visualizations from the results.
- **report**: builds the final report or documentation from the results.
- **download_ember_data**: downloads the necessary Ember and ENTSO-E data for the study.
- **validate_ember_networks**: validates the network and triggers the plotting routines.

These rules are orchestrated by the main `Snakefile`.

---

# How to run the workflow

This section builds upon the detailed description of the available PyPSA-Eur [configurations](https://pypsa-eur.readthedocs.io/en/latest/configuration.html) and [wildcards](https://pypsa-eur.readthedocs.io/en/latest/wildcards.html), and the tutorials for the [electricy-only](https://pypsa-eur.readthedocs.io/en/latest/tutorial.html) and for the [sector-coupled](https://pypsa-eur.readthedocs.io/en/latest/tutorial_sector.html) models.

As detailed in the [How to use Snakemake rules](https://pypsa-eur.readthedocs.io/en/latest/tutorial.html#how-to-use-snakemake-rules) section of the `electricy-only` tutorial, you can produce any output file mentioned in the `Snakefile` by running

`snakemake -call <output file>`

Furthermore, you can use the [config/validation_config_2023.yaml](https://github.com/open-energy-transition/Ember-Flexibility-Study/blob/master/config/validation_config_2023.yaml) to run the workflow with different configurations. The `validate_ember_networks` rule will solve the network, perform the validation and trigger the plotting routines for the Ember Flexibility Study. The command is as follows:

`snakemake -call validate_ember_networks --configfile config/validation_config_2023.yaml`

If you are instead only interested in solving the network for the Ember Flexibility Study, you can run the command:

`snakemake -call solve_elec_networks --configfile config/validation_config_2023.yaml`


---

# Contributing and support

We strongly welcome anyone interested in contributing to this project. If you have any ideas, suggestions or encounter problems, feel invited to file issues or make pull requests on GitHub.

## Issue a pull request and merging it
To issue a pull request to the `master` branch of the upstream repository [Ember-Flexibility-Study](https://github.com/open-energy-transition/Ember-Flexibility-Study/), please follow the [instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) and follow the instructions from the pull request [template](https://github.com/open-energy-transition/Ember-Flexibility-Study/blob/master/.github/pull_request_template.md).

## Raise issues, bugs or feature requests
For **issues, bugs and feature requests**, please use the [GitHub Issues page](https://github.com/open-energy-transition/{{repository}}/issues).

# Licence

The code in this repository is released as free software under the [MIT License](https://opensource.org/licenses/MIT), see [`doc/licenses.rst`](doc/licenses.rst). However, different licenses and terms of use may apply to the various input data, see [`doc/data_sources.rst`](doc/data_sources.rst).