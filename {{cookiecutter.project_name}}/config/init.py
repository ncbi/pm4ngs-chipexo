import os
import re
import json
import pandas
import math
import pickle
import zipfile
import uuid
import distutils.spawn
import numpy as np
import scipy.stats as stats
import seaborn as sns
import itertools
import networkx as nx

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from IPython.display import HTML
from IPython.display import display, Markdown, Latex

from pathlib import Path

from pm4ngs.jupyterngsplugin.utils.errors import check_cwl_command_log
from pm4ngs.jupyterngsplugin.utils.run_command import run_command
from pm4ngs.jupyterngsplugin.utils.working_dir import working_dir
from pm4ngs.jupyterngsplugin.utils.yaml_utils import write_to_yaml
from pm4ngs.jupyterngsplugin.utils.yaml_utils import load_from_yaml

{% if cookiecutter.sequencing_technology == 'paired-end' %}
from pm4ngs.jupyterngsplugin.utils.samples import write_sample_table_pe_to_yaml
{% else %}
from pm4ngs.jupyterngsplugin.utils.samples import write_sample_table_se_to_yaml
{% endif %}

###############################################################
#
#    Project global paths
#
###############################################################

WORKDIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
CONFIG = os.path.join(WORKDIR,'config')
DATA = os.path.join(WORKDIR,'data')
BIN = os.path.join(WORKDIR,'bin')
RESULTS = os.path.join(WORKDIR,'results')
NOTEBOOKS = os.path.join(WORKDIR,'notebooks')
SRC = os.path.join(WORKDIR,'src')
TMP = os.path.join(WORKDIR,'tmp')

###############################################################
#
#    Update genome files and indexes path
#
# If indexes and reference bed files does not exist can be created using 
# the notebooks but you need to have writing permission in the GENOME dir
#
###############################################################

GENOME_NAME = '{{ cookiecutter.genome_name }}'
GENOME = '{{ cookiecutter.genome_dir }}'
ALIGNER_INDEX = '{{ cookiecutter.aligner_index_dir }}'
GENOME_FASTA = '{{ cookiecutter.genome_fasta }}'
GENOME_GTF = '{{ cookiecutter.genome_gtf }}'
GENOME_CHROMSIZES = '{{ cookiecutter.genome_chromsizes }}'

if GENOME_NAME == GENOME:
    GENOME = os.path.join(DATA, GENOME)
    ALIGNER_INDEX = os.path.join(DATA, ALIGNER_INDEX)
    GENOME_FASTA = os.path.join(DATA, GENOME_FASTA)
    GENOME_GTF = os.path.join(DATA, GENOME_GTF)
    GENOME_CHROMSIZES = os.path.join(DATA, GENOME_CHROMSIZES)

###############################################################
#
#    Dataset (experiment) to analyze
#
# The path is $WORKDIR/data/$DATASET
#
# To use multiple datasets (experiments) this variable should be overwritten
# in the notebooks
#
###############################################################

DATASET = '{{ cookiecutter.dataset_name }}'
{% if cookiecutter.is_data_in_SRA == 'y' %}

HOME_DIR = os.path.expanduser("~")
NCBI_DIR = os.path.join(HOME_DIR, '.ncbi')
SRA_TOOLS_CONFIG = os.path.join(NCBI_DIR, 'user-settings.mkfg')
if not os.path.exists(SRA_TOOLS_CONFIG):
    if not os.path.exists(NCBI_DIR):
        print('Creating ncbi dir: ' + NCBI_DIR)
        os.mkdir(NCBI_DIR)

    if not os.path.exists(SRA_TOOLS_CONFIG):
        print('Creating sra-tools config file: ' + SRA_TOOLS_CONFIG)
        with open(SRA_TOOLS_CONFIG, 'w') as fout:
            fout.write('/LIBS/GUID = "{}"\n'.format(uuid.uuid4()))
            fout.write('/libs/cloud/report_instance_identity = "true"\n')


{% if cookiecutter.create_demo == 'y' %}
IS_DEMO = True
{% else %}
IS_DEMO = False
{% endif %}
{% else %}
IS_DEMO = False
{% endif %}

###############################################################
#
#    Docker configuration
#
###############################################################

{% if cookiecutter.use_docker == 'y' %}
DOCKER = True
{% else %}
DOCKER = False
{% endif %}

###############################################################
#
#    cwl-runner with absolute path if necesary 
#
###############################################################

CWLRUNNER_TOOL = 'cwltool'
CWLRUNNER_TOOL_PATH = distutils.spawn.find_executable(CWLRUNNER_TOOL)
if not CWLRUNNER_TOOL_PATH:
    print('WARNING: %s not in path' % (CWLRUNNER_TOOL))
    print('Install: cwltool')
else:
    CWLRUNNER = CWLRUNNER_TOOL_PATH
if not DOCKER:
    CWLTOOL_DEPS = os.path.join(BIN,'cwltool_deps')
    CWLRUNNER +=' --no-container --beta-conda-dependencies --beta-dependencies-directory ' + CWLTOOL_DEPS
    try:
        TRIMMOMATIC_ADAPTERS = str(next(Path(os.path.join(CWLTOOL_DEPS, '_conda', 'envs' )).rglob('__trimmomatic*//share/trimmomatic/adapters')))
    except:
        TRIMMOMATIC_ADAPTERS = ''
else:
    CWLRUNNER += ' --no-read-only --beta-use-biocontainers'
    TRIMMOMATIC_ADAPTERS = '/usr/local/share/trimmomatic/adapters/'

###############################################################


CWLURL = os.path.join(BIN,'cwl')
CWLTOOLS = os.path.join(CWLURL, 'tools')
CWLWORKFLOWS = os.path.join(CWLURL, 'workflows')

CWLRUNNER = CWLRUNNER + ' --parallel --on-error continue --rm-tmpdir --tmp-outdir-prefix=' + TMP + '/ --tmpdir-prefix=' + TMP + '/ '
