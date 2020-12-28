#!/usr/bin/env python
import numpy as np
import os
import pandas
import shutil
import subprocess
import sys
import yaml
from bioconda2biocontainer.update_cwl_docker_image import update_cwl_docker_from_tool_name
from git import Repo
from multiprocessing import Pool, cpu_count

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
DATASET = '{{ cookiecutter.dataset_name }}'
CWL_WORKFLOW_REPO = 'https://github.com/ncbi/cwl-ngs-workflows-cbb'
DATASET_DIR = os.path.join(PROJECT_DIRECTORY, 'data', DATASET)
WORK_DIR = os.environ.get('PM4NGS_WORK_DIR', None)
SAMPLE_TABLE_FILE = os.environ.get('PM4NGS_SAMPLE_TABLE', None)
COPY_RAWDATA = os.environ.get('PM4NGS_COPY_RAWDATA', None)


def clone_git_repo():
    """
    Clone the git repo from the cookiecutter.cwl_workflow_repo to the bin directory
    :return:
    """
    print('Cloning Git repo: {0} to {1}'.format(CWL_WORKFLOW_REPO,
                                                os.path.join(PROJECT_DIRECTORY, 'bin', 'cwl')))
    Repo.clone_from(CWL_WORKFLOW_REPO, os.path.join(PROJECT_DIRECTORY, 'bin', 'cwl'))


def copy_directory(src, dest):
    try:
        shutil.copytree(src, dest)
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
        sys.exit(-1)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)
        sys.exit(-1)


def copy_file(src, dest):
    if os.path.exists(src):
        try:
            dest = os.path.join(dest, os.path.basename(src))
            print(src + ' ==> ' + dest)
            shutil.copyfile(src, dest)
            return 0
            # Directories are the same
        except shutil.Error as e:
            print('File not copied. Error: %s' % e)
        # Any error saying that the directory doesn't exist
        except OSError as e:
            print('File not copied. Error: %s' % e)
    else:
        print('File {} not found'.format(src))
    return -1


def download_file(src, dest):
    dest = os.path.join(dest, os.path.basename(src))
    print('Downloading file {} to {}'.format(src, dest))
    status = subprocess.run(['curl', '-o', dest, src], capture_output=True)
    return status.returncode


def rawdata_file_manager(file):
    if file.startswith('/') and os.path.exists(file):
        return copy_file(file, DATASET_DIR)
    elif file.startswith('http') or file.startswith('ftp'):
        return download_file(file, DATASET_DIR)
    return copy_file(os.path.join(WORK_DIR, file), DATASET_DIR)


def copy_rawdata_to_project():
    if COPY_RAWDATA == 'True':
        sample_table_file = os.path.join(DATASET_DIR, 'sample_table.csv')
        sample_table = pandas.read_csv(sample_table_file, skip_blank_lines=True)
        sample_table = sample_table.replace(np.nan, '', regex=True)
        sample_table = sample_table[['sample_name', 'file', 'condition', 'replicate']]
        print('{} files loaded\nUsing table:'.format(len(sample_table)))
        print(sample_table)
        files = []
        for f in sample_table[sample_table['file'] != '']['file'].unique():
            files.extend(f.split('|'))
        if len(files) > 0:
            print('Copying files in parallel using: {} CPUs'.format(cpu_count() - 1))
            p = Pool(processes=cpu_count() - 1)
            status = p.map(rawdata_file_manager, files)
            for s in status:
                if s != 0:
                    print('Error copying raw data to project')
                    sys.exit(-1)


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
