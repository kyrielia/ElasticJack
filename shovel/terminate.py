import boto
import sys
import time
from shovel import task
from yamlUtil import load_yaml

@task
def terminate(yaml_path):
    settings = load_yaml(yaml_path)
    region = settings['region']
    env_name = settings['environmentName']

    eb_client = boto.beanstalk.connect_to_region(region)
    if environment_exists(eb_client, env_name):
        print "Terminating environment '%s'" % env_name
        eb_client.terminate_environment(environment_name=env_name)
        wait_for_termination(eb_client, env_name)
    else:
        sys.exit(1)

def environment_exists(eb_client, env_name):
    environments = get_environments(eb_client, env_name)
    if environments:
        if environments[0]["Status"] == "Ready":
            return True
        else:
            print "Cancelling termination - environment '%s' exists, but not in ready state" % env_name
            return False
    else:
        print "Environment '%s' does not exist" % env_name
        return False

def wait_for_termination(eb_client, env_name):
    print "Waiting for environment to terminate"
    status = 'Terminating'
    while status == 'Terminating':
        print "..."
        time.sleep(5)
        environments = get_environments(eb_client, env_name)
        if environments:
            status = environments[0]['Status']
    if status == 'Terminated':
        print "Environment terminated!"
    else:
        print "ERROR - env is state %s" % status
        # sys.exit(1)

def get_environments(eb_client, env_name):
    response = eb_client.describe_environments(environment_names=[env_name])
    return response['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments']