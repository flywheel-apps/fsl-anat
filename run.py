#!/usr/bin/env python3

import codecs
import json
import logging
import copy
import os
import os.path as op
import sys
import subprocess as sp
import shutil
import flywheel

def escape_shell_chars(path):
    special_chars = [' ', '\t', '\n', '!', '"', '#', '$', '&', '\'', ')']
    special_chars.extend(['(', '*', ',', ';', '<', '=', '>', '?', '[', '\\'])
    special_chars.extend([']', '^', '`', '{', '}', '|', '~', '-', ':'])
    for ch in special_chars:
        path = path.replace(ch,'_')
    return path

def cleanse_file_basename(basename,ext='.nii'):
    """
    Removes special characters and extension information from 
    a filename
    """
    file_basename = escape_shell_chars(basename)
    return file_basename.split(ext)[0] 

def Build_FSL_Anat_Params(context):
    """
    Build a dictionary of key:value command-line parameter names:values
    These will be validated and assembled into a command-line below.
    """
    config = context.config
    Params = {}
    # Due to escape characters, we need to move the input files to
    # non-escaped character versions of themselves. the fsl-anat
    # command does parse spaces (escaped or otherwise)
    nonSpaced_path=escape_shell_chars(context.get_input_path('Image'))
    # A "move" will not work... must be "copy"
    if nonSpaced_path != context.get_input_path('Image'):
        shutil.copy(context.get_input_path('Image'),
                    nonSpaced_path)

    Params['i'] = nonSpaced_path
    # fsl_anat will create the output directory and name it
    # /flywheel/v0/output/<input_file basename>_result.anat
    # Automatically appending the ".anat"
    # NOTE: Always escape for special bash characters
    input_file_basename = cleanse_file_basename(
                            context.get_input("Image")['location']['name']
                        )
    result_dir = input_file_basename + '_result'
    Params['o'] = op.join(context.output_dir, result_dir)
    for key in config.keys():
        # Use only those boolean values that are True
        if type(config[key]) == bool:
            if config[key]:
                Params[key] = True
        else:
            # if the key-value is zero, we skip and use the defaults
            if config[key] != 0:
                Params[key] = config[key]
    return Params


def Validate_FSL_Anat_Params(Params, log):
    """
    Validate settings of the Parameters constructed.
    Gives warnings for possible settings that could result in bad results.
    Gives errors (and raises exceptions) for settings that are violations.
    """
    keys = Params.keys()
    # Test for input existence
    # os.path.exists does not like escape characters
    
    if not op.exists(Params['i']):
        raise Exception('Input File Not Found: ' + Params['i'])

    if ('betfparam' in keys) and ('nononlinreg' in keys):
        if(Params['betfparam'] > 0.0):
            raise Exception(
                'For betfparam values > zero, \
                nonlinear registration is required.')

    if ('s' in keys):
        if Params['s'] == 0:
            log.warning(
                'The value of ' + str(Params['s']) +
                ' for -s may cause a singular matrix.' +
                ' Setting to default value of 10.'
            )
            Params['s'] = 10


def BuilCommandList(command, ParamList):
    """
    command is a list of prepared commands
    ParamList is a dictionary of key:value pairs to
    be put into the command list as such ("-k value" or "--key=value")
    """
    for key in ParamList.keys():
        # Single character command-line parameters preceded by a single '-'
        if len(key) == 1:
            command.append('-' + key)
            if len(str(ParamList[key])) != 0:
                command.append(str(ParamList[key]))
        # Multi-Character command-line parameters preceded by a double '--'
        else:
            # If Param is boolean and true include, else exclude
            if type(ParamList[key]) == bool:
                if ParamList[key]:
                    command.append('--' + key)
            else:
                # If Param not boolean, without value include without value
                # (e.g. '--key'), else include value (e.g. '--key=value')
                if len(str(ParamList[key])) == 0:
                    command.append('--' + key)
                else:
                    command.append('--' + key + '=' + str(ParamList[key]))
    return command


if __name__ == '__main__':
    context = flywheel.GearContext()
    config = context.config
    # Initialize Custom Logging
    # Timestamps with logging assist debugging algorithms
    # With long execution times
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
                fmt='%(levelname)s - %(name)-8s - %(asctime)s -  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger = logging.getLogger('[flywheel/fsl-anat]')
    logger.addHandler(handler)
    context.log = logger
    context.log.setLevel(logging.INFO)

    # context.init_logging()
    context.log_config()

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    # Execute in try except block
    try:
        # Build a parameter dictionary specific for fsl_anat
        fsl_params = Build_FSL_Anat_Params(context)
        # Validate the fsl_anat parameter dictionary
        # Raises Exception on fail
        Validate_FSL_Anat_Params(fsl_params, context.log)
        # Build command-line string for subprocess to execute
        command = ['fsl_anat']
        command = BuilCommandList(command, fsl_params)
        context.log.info('FSL_Anat Command:'+' '.join(command))

        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                        universal_newlines=True, env=environ)

        context.log.info(result.returncode)
        context.log.info(result.stdout)

        if result.returncode != 0:
            context.log.error('The command:\n ' +
                              ' '.join(command) +
                              '\nfailed. See log for debugging.')
            context.log.error(result.stderr)
            os.sys.exit(result.returncode)
        
        context.log.info("Commands successfully executed!")
        os.sys.exit(0)

    except Exception as e:
        context.log.error(e)
        context.log.error('Cannot execute FLS Anat commands.')
        os.sys.exit(1)

    finally:
        # Cleanup, move all results to the output directory
        # This executes regardless of errors or exit status,
        # 'exit'!=0 is treated like an exception
        # Unless otherwise specified, zip entire results and delete directory
        os.chdir(context.output_dir)
        # If the output/result.anat path exists, zip regardless of exit status
        # Clean input_file_basename to lack esc chars and extension info
        input_file_basename = cleanse_file_basename(
                            context.get_input("Image")['location']['name']
                        )
        result_dir = input_file_basename + '_result.anat'
        if op.exists('/flywheel/v0/output/' + result_dir):
            context.log.info(
                'Zipping /flywheel/v0/output/' + result_dir + ' directory.'
            )
            # For results with a large number of files, provide a manifest.
            # Capture the stdout/stderr in a file handle or for logging.
             
            command0 = ['tree', '-shD', '-D', result_dir]
            with open(input_file_basename + '_output_manifest.txt', 'w') as f:
                result0 = sp.run(command0, stdout = f)
            command1 = ['zip', '-r', result_dir + '.zip', result_dir]
            result1 = sp.run(command1, stdout=sp.PIPE, stderr=sp.PIPE)
            command2 = ['rm', '-rf', '/flywheel/v0/output/' + result_dir]
            result2 = sp.run(command2, stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            context.log.info(
                'No results directory, \
                /flywheel/v0/output/' + \
                result_dir + ', to zip.')
