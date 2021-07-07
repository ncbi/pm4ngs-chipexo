#!/usr/bin/env python
import os

from pm4ngs.utils import main_hook_standard_template

if __name__ == '__main__':
    main_hook_standard_template('{{ cookiecutter.dataset_name }}')
