#!/usr/bin/env python
import os
import shutil
import sys

import yaml
from bioconda2biocontainer.update_cwl_docker_image import update_cwl_docker_from_tool_name
from pm4ngs.utils import clone_git_repo
from pm4ngs.utils import copy_directory
from pm4ngs.utils import copy_rawdata_to_project

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
DATASET = '{{ cookiecutter.dataset_name }}'
CWL_WORKFLOW_REPO = 'https://github.com/ncbi/cwl-ngs-workflows-cbb'
DATASET_DIR = os.path.join(PROJECT_DIRECTORY, 'data', DATASET)
WORK_DIR = os.environ.get('PM4NGS_WORK_DIR', None)
SAMPLE_TABLE_FILE = os.environ.get('PM4NGS_SAMPLE_TABLE', None)
COPY_RAWDATA = os.environ.get('PM4NGS_COPY_RAWDATA', None)

if __name__ == '__main__':
    if SAMPLE_TABLE_FILE and COPY_RAWDATA and WORK_DIR:
        conda_dependencies = os.path.join(PROJECT_DIRECTORY, 'requirements', 'conda-env-dependencies.yaml')
        if os.path.exists(conda_dependencies):
            if 'github.com' in CWL_WORKFLOW_REPO:
                clone_git_repo()
            elif os.path.exists(CWL_WORKFLOW_REPO):
                print('Copying CWL directory {} to {}'.format(
                    CWL_WORKFLOW_REPO, os.path.join(PROJECT_DIRECTORY, 'bin', 'cwl')
                ))
                copy_directory(CWL_WORKFLOW_REPO, os.path.join(PROJECT_DIRECTORY, 'bin', 'cwl'))
            else:
                print('CWL_WORKFLOW_REPO = {} not available.'.format(CWL_WORKFLOW_REPO))
                print('Use Github URL or absolute path')
                sys.exit(-1)

            print('Updating CWLs dockerPull and SoftwareRequirement from: ' + conda_dependencies)
            with open(conda_dependencies) as fin:
                conda_env = yaml.load(fin, Loader=yaml.FullLoader)
                if 'dependencies' in conda_env:
                    for d in conda_env['dependencies']:
                        update_cwl_docker_from_tool_name(d, os.path.join(PROJECT_DIRECTORY, 'bin', 'cwl'))

            print('Copying file {}  to {}'.format(
                SAMPLE_TABLE_FILE, os.path.join(DATASET_DIR, 'sample_table.csv')
            ))
            shutil.copyfile(SAMPLE_TABLE_FILE, os.path.join(DATASET_DIR, 'sample_table.csv'))
            copy_rawdata_to_project()
            print(' Done')
        else:
            print('No conda env dependency file in {0}'.format(conda_dependencies))
            sys.exit(-1)
    else:
        print('Error reading user env')
        print('PM4NGS_SAMPLE_TABLE: ' + str(SAMPLE_TABLE_FILE))
        print('PM4NGS_COPY_RAWDATA: ' + str(COPY_RAWDATA))
        print('PM4NGS_WORK_DIR: ' + str(WORK_DIR))
        sys.exit(-1)
