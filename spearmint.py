##
# wrapping: A program making it easy to use hyperparameter
# optimization software.
# Copyright (C) 2013 Katharina Eggensperger and Matthias Feurer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/env python

import cPickle
import os
import sys

import numpy as np

import wrapping_util

__authors__ = ["Katharina Eggensperger", "Matthias Feurer"]
__contact__ = "automl.org"

path_to_optimizer = "optimizers/spearmint_april2013_mod/"
version_info = ("# %76s #\n" %
                "https://github.com/JasperSnoek/spearmint/tree/613350f2f617de3af5f101b1dc5eccf60867f67e")


def build_spearmint_call(config, options, optimizer_dir):
    call = 'python ' + os.path.dirname(os.path.realpath(__file__)) + \
           "/" + path_to_optimizer + '/spearmint_sync.py'
    call = ' '.join([call, optimizer_dir,
                    '--config', config.get('SPEARMINT', 'config'),
                    '--max-concurrent', config.get('DEFAULT', 'numberOfConcurrentJobs'),
                    '--max-finished-jobs', config.get('SPEARMINT', 'max_finished_jobs'),
                    '--polling-time', config.get('SPEARMINT', 'spearmint_polling_time'),
                    '--grid-size', config.get('SPEARMINT', 'grid_size'),
                    '--method',  config.get('SPEARMINT', 'method'),
                    '--method-args=' + config.get('SPEARMINT', 'method_args'),
                    '--grid-seed', str(options.seed)])
    if config.get('SPEARMINT', 'method') != "GPEIChooser" and \
            config.get('SPEARMINT', 'method') != "GPEIOptChooser":
        sys.stdout.write('WARNING: This chooser might not work yet\n')
        call = ' '.join([call, config.get("SPEARMINT", 'method_args')])
    return call


#noinspection PyUnusedLocal
def restore(config, optimizer_dir, **kwargs):
    """
    Returns the number of restored runs. This is the number of different configs
    tested multiplied by the number of crossvalidation folds.
    """
    restore_file = os.path.join(optimizer_dir, "expt-grid.pkl")
    if not os.path.exists(restore_file):
        print "Oups, this should have been checked before"
        raise Exception("%s does not exist" % (restore_file,))
    sys.path.append(os.path.join(
        os.path.dirname(os.path.realpath(__file__)), path_to_optimizer))
    import ExperimentGrid
    # Assumes that all not valid states are marked as crashed
    fh = open(restore_file)
    exp_grid = cPickle.load(fh)
    fh.close()
    complete_runs = np.sum(exp_grid['status'] == 3)
    restored_runs = complete_runs * config.getint('DEFAULT', 'numberCV')
    try:
        os.remove(os.path.join(optimizer_dir, "expt-grid.pkl.lock"))
    except OSError:
        pass
    return restored_runs


#noinspection PyUnusedLocal
def main(config, options, experiment_dir, **kwargs):
    # config:           Loaded .cfg file
    # options:          Options containing seed, restore_dir,
    # experiment_dir:   Experiment directory/Benchmark_directory
    # **kwargs:         Nothing so far

    time_string = wrapping_util.get_time_string()

    # Find experiment directory
    if options.restore:
        if not os.path.exists(options.restore):
            raise Exception("The restore directory does not exist")
        optimizer_dir = options.restore
    else:
        optimizer_dir = os.path.join(experiment_dir, "spearmint_" \
            + str(options.seed) + "_" + time_string)

    # Build call
    cmd = build_spearmint_call(config, options, optimizer_dir)

    # Set up experiment directory
    if not os.path.exists(optimizer_dir):
        os.mkdir(optimizer_dir)
        # Make a link to the Protocol-Buffer config file
        configpb = config.get('SPEARMINT', 'config')
        if not os.path.exists(os.path.join(optimizer_dir, configpb)):
            os.symlink(os.path.join(experiment_dir, "spearmint", configpb),
                       os.path.join(optimizer_dir, configpb))
    sys.stdout.write("### INFORMATION ################################################################\n")
    sys.stdout.write("# You're running %40s                      #\n" % path_to_optimizer)
    sys.stdout.write("%s" % version_info)
    sys.stdout.write("# A newer version might be available, but not yet built in.                    #\n")
    sys.stdout.write("# Please use this version only to reproduce our results on automl.org          #\n")
    sys.stdout.write("################################################################################\n")
    return cmd, optimizer_dir