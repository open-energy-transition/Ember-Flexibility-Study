<!--
SPDX-FileCopyrightText: Open Energy Transition gGmbH, Ember, and contributors to the Ember Flexibility Study
SPDX-License-Identifier: CC-BY-4.0
-->

# Ember Flexibility Study

<img src="https://raw.githubusercontent.com/open-energy-transition/Ember-Flexibility-Study/refs/heads/master/doc/img/ember_oet.png" alt="Open Energy Transition Logo" width="200" height="234" align="right">

This repository contains the code and analysis for the **Ember Flexibility Study**, commissioned by [Ember](https://ember-climate.org/) in collaboration with [Open Energy Transition (OET)](https://openenergytransition.org/). The study investigates clean flexibility options for Europe's energy system, building on the PyPSA-Eur framework. All results are computed from raw data and any code used is shared to ensure full reproducibility.

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

The Ember Flexibility Study uses a series of software tools. The following steps describe how to install the required software and system dependencies.

### Install Git

Git is a version control system used to track changes in code and support collaborative development. The Ember Flexibility Study uses Git to manage its source code, making it easy for developers to contribute and for users to access the latest updates.

To access the source code and run it locally, you will need Git installed on your system. You can find installation instructions on the [official Git website](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

### Install Miniconda

Miniconda is a package manager for Python, allowing to manage environments with different versions using the `conda` package manager. An environment is an isolated workspace that contains specific versions of Python and other packages needed to run a project, preventing conflicts
between different projects' dependencies. 

We recommend to use Miniconda to manage the Ember Flexibility Study project environments. However, other package managers can be used, such as [Anaconda](https://www.anaconda.com/) or [mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html). 

To install Miniconda, follow the instructions on the [Anaconda website](https://www.anaconda.com/download/success).

## 2. Fork the repository

**Note**: *this step requires a GitHub account. If you do not have one, you can create an account for free at [GitHub](https://docs.github.com/en/get-started/start-your-journey/creating-an-account-on-github).*

Fork the repository [Ember-Flexibility-Study](https://github.com/open-energy-transition/Ember-Flexibility-Study/) on GitHub to your own account. Please make sure to check the box `Copy the master branch only` and to follow the detailed instructions from [Github](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo).

## 3. Clone the forked repository

Now proceed to clone the **forked** Ember Flexibility Study repository to your local machine.

To do so, open a terminal and navigate to the directory where you’d like the project to be installed—referred to here as `{installation_directory}`. Then, run the following command:

```bash
git clone https://github.com/<your-username>/Ember-Flexibility-Study.git
```

## 4. Set up the upstream repositories

Once you have cloned your fork, you should add the following upstream remotes to keep your repository up to date with the main projects:

- Add the [Ember-Flexibility-Study](https://github.com/open-energy-transition/Ember-Flexibility-Study/) repository as `upstream`:

      git remote add upstream https://github.com/open-energy-transition/Ember-Flexibility-Study.git

- *(Optional)* Add the OET soft-fork of PyPSA-Eur as `upstream_pypsa_eur_oet`:

      git remote add upstream_pypsa_eur_oet https://github.com/open-energy-transition/pypsa-eur.git

To verify that the remotes have been set up correctly, you can run:

```bash
git remote -v
```

The output should look like this:

```plaintext                                                                             
origin  https://github.com/<your-username>/Ember-Flexibility-Study.git (fetch)
origin  https://github.com/<your-username>/Ember-Flexibility-Study.git (push)
upstream        https://github.com/open-energy-transition/Ember-Flexibility-Study.git (fetch)
upstream        https://github.com/open-energy-transition/Ember-Flexibility-Study.git (push)
upstream_pypsa_eur_oet  https://github.com/open-energy-transition/pypsa-eur.git (fetch)
upstream_pypsa_eur_oet  https://github.com/open-energy-transition/pypsa-eur.git (push)
```

## 5. Set up the environment
  
Once the forked repository is cloned, you can set up the environment to run the analysis. In the terminal, navigate to the repository directory `{installation_directory}/Ember-Flexibility-Study`:

```bash
cd {installation_directory}/Ember-Flexibility-Study
```

and run the following command:

```bash
conda env create -f envs/win-64.lock.yaml -n ember-study
```

Please choose the **appropriate** environment file based on your operating system, i.e. `envs/win-64.lock.yaml` for Windows, `envs/linux-64.lock.yaml` for Linux and `envs/osx-64.lock.yaml` or `envs/osx-arm64.lock.yaml` for MacOS. The command creates an environment named `ember-study` with all the Python packages and software dependencies necessary to run the model. Afterwards, you can activate the environment by running:

```bash
conda activate ember-study
```

Your terminal will now show the name of the activated environment, indicating that you are ready to run the Ember Flexibility Study.

![img from static](/doc/img/cli_snapshot.png)

---

# Repository structure

The list below provides an overview of the directory structure of the Ember Flexibility Study repository. Each folder serves a specific purpose within the workflow, facilitating reproducibility and efficient management of the project.

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

The PyPSA-Eur workflow is managed with [Snakemake](https://snakemake.readthedocs.io/).

Snakemake is a workflow management system that enables reproducible and scalable data analyses. It enables users to define complex pipelines in a readable Python-based language, automatically handling dependencies, job execution, and resource management. Snakemake is widely used in scientific computing for automating data processing, analysis, and reporting.

## Defining rules in Snakemake

Snakemake workflows are built from modular units called **rules**. Each rule specifies how to create output files from input files, using scripts or shell commands. Rules define the steps of your workflow and their dependencies, making it easy to manage complex pipelines.

## Main Snakemake command-line keys

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

## Important rules in Ember Flexibility Study

The Snakemake rules for the [Ember-Flexibility-Study](https://github.com/open-energy-transition/Ember-Flexibility-Study/) are included in dedicated `.smk` files under the `rules` directory. Some of the most important rules that structure the workflow include:

- **retrieve**: downloads and prepares all required input data. 
- **build_network**: constructs the base energy system network from input data.
- **prepare_sector**: prepares sector-coupling data (e.g., heating, transport).
- **solve_network**: runs the optimization to solve the energy system model.
- **postprocess**: processes and analyzes the results after solving.
- **plot_network**: generates plots and visualizations from the results.
- **report**: builds the final report or documentation from the results.
- **download_ember_data**: downloads the necessary Ember and ENTSO-E + GB data for the study.
- **validate_ember_networks**: validates the network and triggers the plotting routines.

These rules are orchestrated by the main `Snakefile`. Further information is available in the PyPSA-Eur documentation, specifically in the [Retrieving Data](https://pypsa-eur.readthedocs.io/en/latest/retrieve.html), [Build Electricity Networks](https://pypsa-eur.readthedocs.io/en/latest/preparation.html), [Build Sector-Coupled Networks](https://pypsa-eur.readthedocs.io/en/latest/sector.html), [Solving Networks](https://pypsa-eur.readthedocs.io/en/latest/solving.html) and [Plotting and Summaries](https://pypsa-eur.readthedocs.io/en/latest/plotting.html) pages.

---

# How to run the workflow

This section builds upon the detailed description of the available PyPSA-Eur [configurations](https://pypsa-eur.readthedocs.io/en/latest/configuration.html) and [wildcards](https://pypsa-eur.readthedocs.io/en/latest/wildcards.html), and the tutorials for the [electricy-only](https://pypsa-eur.readthedocs.io/en/latest/tutorial.html) and for the [sector-coupled](https://pypsa-eur.readthedocs.io/en/latest/tutorial_sector.html) models.

## Configuration files

The default configurations are defined in the [config/config.default.yaml](https://github.com/open-energy-transition/Ember-Flexibility-Study/blob/master/config/config.default.yaml) file. Default configurations can be overridden by creating your own configuration file, e.g. `config/my_config.yaml`, and passing it to the `snakemake` command using the `--configfile` option. The repository already contains the [config/validation_config_2023.yaml](https://github.com/open-energy-transition/Ember-Flexibility-Study/blob/master/config/validation_config_2023.yaml) file, which is used to run the Ember Flexibility Study.

## Run the workflow

As detailed in the [How to use Snakemake rules](https://pypsa-eur.readthedocs.io/en/latest/tutorial.html#how-to-use-snakemake-rules) section of the `electricy-only` tutorial, you can produce any output file mentioned in the `Snakefile` by running

`snakemake -call <output file>`

The `validate_ember_networks` rule will solve the network and trigger the generation plotting routines for the Ember Flexibility Study. The command is as follows:

`snakemake -call validate_ember_networks --configfile config/validation_config_2023.yaml`

The `plot_all_capacity_demand` rule will solve the network and trigger the capacity plotting routines for the Ember Flexibility Study. The command is as follows:

`snakemake -call plot_all_capacity_demand --configfile config/validation_config_2023.yaml`

If you are instead only interested in solving the network for the Ember Flexibility Study, you can run the command:

`snakemake -call solve_elec_networks --configfile config/validation_config_2023.yaml`

If you are instead only interested in preparing the network for the Ember Flexibility Study, you can run the command:

`snakemake -call prepare_sector_networks --configfile config/validation_config_2023.yaml`

**Note**: *if you first run `snakemake -call validate_ember_networks --configfile ...`, this will solve the network and generate the necessary plots. Subsequently, when you run  `snakemake -call plot_all_capacity_demand --configfile ...`, the workflow will only generate the plots based on the existing network files without re-solving the network.  The process is the same in reverse: running either rule first will prevent re-solving the network when executing the other, ensuring that the network is only solved once.*

---

# Contributing and support

Contributions to the Ember Flexibility Study can be made in various ways, including reporting issues, suggesting improvements, or contributing code. The following sections outline how to raise issues (bugs), request features, and contribute code.

## Raise issues, bugs or feature requests
To raise **issues, bugs and feature requests**, please use the [GitHub Issues page](https://github.com/open-energy-transition/Ember-Flexibility-Study/issues) page.

## Contribute and issue a pull request

The steps to follow to contribute code to the Ember Flexibility Study are as follows:

- Checkout the `master` branch of your forked repository with `git checkout master`
- Pull the latest changes from the `origin/master` branch with `git pull origin master`
- Create a new branch for your changes with `git checkout -b my_new_branch`
- Make your changes, stage them with `git add file_name` and commit them with `git commit -m "Description of my changes"`
- Push your changes to your forked repository with `git push origin my_new_branch`
- Issue a pull request to the `master` branch of the upstream repository [Ember-Flexibility-Study](https://github.com/open-energy-transition/Ember-Flexibility-Study/), following the [instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request). Please make sure to consider also the checklist from the pull request [template](https://github.com/open-energy-transition/Ember-Flexibility-Study/blob/master/.github/pull_request_template.md).

---

# Advance topics

## Merging changes from the upstream repositories

To keep your fork up to date, you can merge changes from the `master` branch of either `upstream_pypsa_eur_oet` or `upstream` as follows:

- To merge changes from the OET soft-fork of PyPSA-Eur:

      git fetch upstream_pypsa_eur_oet
      git merge upstream_pypsa_eur_oet/master

- To merge changes from the main Ember-Flexibility-Study repository:

      git fetch upstream
      git merge upstream/master

Resolve any conflicts if they arise, then push the updates to your fork if needed.

---

# Licence

The code in this repository is released as free software under the [`doc/licenses.rst`](doc/licenses.rst). However, different licenses and terms of use may apply to the various input data, see [`doc/data_sources.rst`](doc/data_sources.rst).