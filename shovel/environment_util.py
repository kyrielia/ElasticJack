# Returns the description of a single environment
def get_environment(eb_client, env_name=None, app_name=None, version_label=None):
    if env_name:
        env_name = [env_name]
    response = eb_client.describe_environments(
        application_name=app_name,
        version_label=version_label,
        environment_names=env_name)
    environments = response['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments']
    if environments:
        return environments[0]
    else:
        return None