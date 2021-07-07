#!/usr/bin/env python
import os

from pm4ngs.utils import main_hook_standard_template

if __name__ == '__main__':
    main_hook_standard_template(os.environ.get('PM4NGS_SAMPLE_TABLE', None),
                                os.environ.get('PM4NGS_COPY_RAWDATA', None),
                                os.environ.get('PM4NGS_WORK_DIR', None),
                                '{{ cookiecutter.dataset_name }}',
                                os.path.realpath(os.path.curdir),
                                'https://github.com/ncbi/cwl-ngs-workflows-cbb')
