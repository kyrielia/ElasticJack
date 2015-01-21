import boto
from shovel import task
from yamlUtil import load_yaml

@task
def terminate(yaml_path):
    settings = load_yaml(yaml_path)
    region = settings['region']
    env_name = settings['environmentName']

    eb_client = boto.beanstalk.connect_to_region(region)
    # TODO - check env exists before trying to terminate
    print "Terminating environment '%s'" % env_name
    eb_client.terminate_environment(environment_name=env_name)
    # TODO - poll to ensure that env is down
