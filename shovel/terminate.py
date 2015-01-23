import boto
import sys
import time
import colorama
import imp
import os
from colorama import Fore
from shovel import task

# Hack to get around ImportErrors caused by how Shovel finds its tasks
yaml_util = imp.load_source('yamlUtil', os.path.join(os.path.dirname(__file__), '.', './yaml_util.py'))
environment_util = imp.load_source('environmentUtil', os.path.join(os.path.dirname(__file__), '.', './environment_util.py'))

@task
def terminate(yaml_path):
    colorama.init(autoreset=True)

    settings = yaml_util.load_yaml(yaml_path)
    region = settings['region']
    env_name = settings['environmentName']

    eb_client = boto.beanstalk.connect_to_region(region)
    if is_environment_ready(eb_client, env_name):
        print "Terminating environment '%s'" % env_name
        eb_client.terminate_environment(environment_name=env_name)
        wait_for_termination(eb_client, env_name)
    else:
        sys.exit(1)

# Waits for the environment to terminate
def wait_for_termination(eb_client, env_name):
    print "Waiting for environment to terminate"
    status = 'Terminating'
    while status == 'Terminating':
        print "..."
        time.sleep(5)
        environment = environment_util.get_environment(eb_client, env_name=env_name)
        if environment:
            status = environment['Status']
    if status == 'Terminated':
        print "Environment terminated!"
    else:
        print "ERROR - env is state %s" % status
        sys.exit(1)

# Return True if environment has Ready status, else False
def is_environment_ready(eb_client, env_name):
    environment = environment_util.get_environment(eb_client, env_name=env_name)
    if environment:
        status = environment["Status"]
        if status == "Ready":
            return True
        else:
            print Fore.RED + "Cancelling termination. Environment '%s' exists in state '%s'." % (env_name, status)
            print Fore.RED + "To terminate an environment, it must have status 'Ready'"
            return False
    else:
        print "Environment '%s' does not exist" % env_name
        return False
