#!/usr/bin/env python3

import codecs
import json
import copy
import os
import os.path as op
import sys
import subprocess as sp
import shutil
# Gear basics
FLYWHEEL_BASE = '/flywheel/v0'
MANIFEST_FILE = op.join(FLYWHEEL_BASE, 'manifest.json')
CONFIG_FILE = op.join(FLYWHEEL_BASE, 'config.json')
INPUT_DIR = op.join(FLYWHEEL_BASE, 'input')
OUTPUT_DIR = op.join(FLYWHEEL_BASE, 'output')


def BuildFSL_Anat_Params(invocation):
    config = invocation['config']
    inputs = invocation['inputs']
    destination = invocation['destination']
    Params = {}
    Params['i'] = inputs["Image"]["location"]["path"]
    # fsl_anat will create the output directory
    Params['o'] = '/flywheel/v0/output/result'
    for key in config.keys():
        # Use only those boolean values that are True
        if type(config[key]) == bool:
            if config[key]:
                Params[key] = True
        else:
            if len(key) == 1:
                Params[key] = config[key]
            else:
                if config[key] != 0:  # if the key-value is zero, we skip and use the defaults
                    if (key == 'betfparam'):
                        if (config['nononlinreg']):
                            raise Exception(
                                'For betfparam values > zero, nonlinear registration is required.')
                    Params[key] = config[key]
    return Params


def BuilCommandList(command, ParamList):
    """
    command is a list of prepared commands
    ParamList is a dictionary of key:value pairs to be put into the command list as such ("-k value" or "--key=value")
    """
    print(ParamList)
    for key in ParamList.keys():
        # Single character command-line parameters are preceded by a single '-'
        if len(key) == 1:
            command.append('-' + key)
            if len(str(ParamList[key]))!=0:
                command.append(str(ParamList[key]))
        # Multi-Character command-line parameters are preceded by a double '--'
        else:
            # If Param is boolean and true include, else exclude
            if type(ParamList[key]) == bool:
                if ParamList[key]:
                    command.append('--' + key)
            # If Param not boolean, but without value include without value
            # (e.g. '--key'), else include value (e.g. '--key=value')
            if len(str(ParamList[key])) == 0:
                command.append('--' + key)
            else:
                command.append('--' + key + '=' + str(ParamList[key]))
    return command


if __name__ == '__main__':
    invocation = json.loads(open(CONFIG_FILE).read())
    config = invocation['config']
    inputs = invocation['inputs']
    destination = invocation['destination']

    # Display everything provided to the job

    # Copy and display invocation without api-key
    safe_invocation = copy.deepcopy(invocation)
    safe_invocation["inputs"]["api-key"]["key"] = "--- OMITTED ---"

    print("Gear invocation:")
    print(json.dumps(safe_invocation, indent=4, sort_keys=True))
    print()

    # grab environment for gear
    with open('/tmp/fsl_environ.json', 'r') as f:
        environ = json.load(f)

    # Execute in try except block
    try:
        # Each parameter separated by a space must be a separate element in the command list.
        fsl_params = BuildFSL_Anat_Params(invocation)
        command = ['fsl_anat']
        command = BuilCommandList(command, fsl_params)
        print(' '.join(command))

        sys.stdout.flush()
        sys.stderr.flush()

        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                        universal_newlines=True, env=environ)

        print(result.returncode, result.stdout, result.stderr)

        if result.returncode != 0:
            print('The command:\n ' +
                  ' '.join(command) +
                  '\nfailed. See log for debugging.')
            os.sys.exit(result.returncode)
        else:
            print("Commands successfully executed!")
            os.sys.exit(0)

    except Exception as e:
        print(e,)
        print('Cannot execute FLS Anat commands.',)
        os.sys.exit(1)

    finally:
        # Cleanup, move all results to the output directory
        # Unless otherwise specified, zip entire results and delete directory
        command1 = ['zip', op.join(OUTPUT_DIR, 'results.zip'), op.join(
            OUTPUT_DIR, '/flywheel/v0/output/result.anat')]
        result1 = sp.run(command1, stdout=sp.PIPE, stderr=sp.PIPE)
        command2 = ['rm', '-rf', '/flywheel/v0/output/result.anat/']
        result2 = sp.run(command2, stdout=sp.PIPE, stderr=sp.PIPE)
