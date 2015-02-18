import boto
import boto.beanstalk
import sys
import os
import imp
import time
import colorama
from shovel import task
from boto.s3.connection import Location
from boto.s3.lifecycle import Lifecycle, Expiration
from colorama import Fore

# Hack to get around ImportErrors caused by how Shovel finds its tasks
yaml_util = imp.load_source('yamlUtil', os.path.join(os.path.dirname(__file__), '.', './yaml_util.py'))
environment_util = imp.load_source('environmentUtil', os.path.join(os.path.dirname(__file__), '.', './environment_util.py'))

@task
def deploy(yaml_path, war_path):
    colorama.init(autoreset=True)

    settings = yaml_util.load_yaml(yaml_path)
    app_name = settings['appName']
    region = settings['region']
    s3_bucket = settings['s3Bucket']
    s3_key = settings['s3Key']
    version_label = settings['versionLabel']
    env_name = settings['environmentName']
    c_name = settings['cName']
    config_template = settings['configTemplate']
    expiration_path = settings['expirationPath']
    days_to_expiration = settings['daysToExpiration']

    eb_client = boto.beanstalk.connect_to_region(region)

    if not is_environment_terminating(eb_client, env_name):
        lifecycle = get_lifecycle(expiration_path, days_to_expiration)
        upload_to_s3(war_path, s3_bucket, s3_key, region, lifecycle)
        if application_exists(eb_client, c_name):
            print "Application '%s' already exists - attempting update" % app_name
            deploy_app(eb_client, app_name, version_label, s3_bucket, s3_key, False)
            update_app(eb_client, env_name, version_label, config_template)
        else:
            print "Could not find application '%s' - creating application" % app_name
            deploy_app(eb_client, app_name, version_label, s3_bucket, s3_key, True)
            create_environment(eb_client, app_name, env_name, c_name, version_label, config_template)
        # Wait for app to confirm that it has deployed or failed to deploy before exiting script
        wait_for_app(eb_client, app_name, version_label)
    else:
        sys.exit(1)

# Set a lifecycle policy on the bucket if the daysToExpiration property is assigned
def get_lifecycle(expiration_path, days_to_expiration):
    if days_to_expiration is not None and expiration_path is not None:
        lifecycle = Lifecycle()
        print "Adding expiration rule of %s days for S3 path %s" % (days_to_expiration, expiration_path)
        lifecycle.add_rule('expirationrule', prefix=expiration_path, status='Enabled', expiration=Expiration(days=int(days_to_expiration)))
        return lifecycle
    else:
        print "No expiration rule added"
        return None

# Uploads the given file to the given S3 bucket
def upload_to_s3(file, bucket_name, key_name, region, lifecycle):
    print "Uploading file %s to Amazon S3 bucket '%s' in region '%s'" % (file, bucket_name, region)
    bucket = get_or_create_bucket(bucket_name, region)
    key = boto.s3.key.Key(bucket)
    key.key = key_name
    key.set_contents_from_filename(file, cb=percent_complete, num_cb=10)
    if lifecycle is not None:
        bucket.configure_lifecycle(lifecycle)

# Gets an S3 bucket. Creates the S3 bucket if it does not exist
def get_or_create_bucket(bucket_name, region):
    print "Check if bucket %s exists" % bucket_name
    s3 = boto.s3.connect_to_region(region)
    bucket = s3.lookup(bucket_name)
    print "Received bucket is %s" % bucket
    if bucket is None:
        print "Bucket does not exist - creating"
        bucket = s3.create_bucket(bucket_name, location=get_location(region))
    return bucket

# Return true if an application with the given cName exists
def application_exists(eb_client, c_name):
    print "Checking if application with cName '%s' already exists" % c_name
    response = eb_client.check_dns_availability(c_name)
    available = response['CheckDNSAvailabilityResponse']['CheckDNSAvailabilityResult']['Available']
    return not available

# Deploys an application
def deploy_app(eb_client, app_name, version_label, s3_bucket, s3_key, auto_create):
    print "Creating application version '%s'" % version_label
    eb_client.create_application_version(
        app_name,
        version_label,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        auto_create_application=auto_create)

# Updates an application
def update_app(eb_client, env_name, version_label, template_name):
    print "Updating environment '%s' with version '%s'" % (env_name, version_label)
    eb_client.update_environment(
        environment_name=env_name,
        version_label=version_label,
        template_name=template_name)

# Creates an Elastic Beanstalk environment using the given parameters
def create_environment(eb_client, app_name, env_name, c_name, version_label, template_name):
    print "Creating environment '%s'" % env_name
    eb_client.create_environment(
        app_name,
        env_name,
        cname_prefix=c_name,
        version_label=version_label,
        template_name=template_name)

# Returns True if an environment is terminating, else False
def is_environment_terminating(eb_client, env_name):
    environment = environment_util.get_environment(eb_client, env_name=env_name)
    if environment:
        status = environment['Status']
        if status == "Terminating":
            print Fore.RED + "Cancelling deployment. Environment '%s' exists in state '%s'." % (env_name, status)
            print Fore.RED + "To deploy an environment, it must be have status 'Ready' or not exist"
            return True
        else:
            return False
    else:
        print "Environment '%s' does not exist" % env_name
        return False

# Waits for the application to be launched
def wait_for_app(eb_client, app_name, version_label):
    print "Waiting for application to start"
    status = 'Pending'
    while status == 'Pending' or status == 'Launching' or status == 'Updating':
        print "..."
        time.sleep(5)
        environment = environment_util.get_environment(eb_client, app_name=app_name, version_label=version_label)
        if environment:
            status = environment['Status']
    if status == 'Ready':
        print "Environment ready!"
    else:
        print "ERROR - env is state %s" % status
        sys.exit(1)

# Converts an availability zone to a location
def get_location(region):
    if region == "ap-northeast-1":
        return Location.APNortheast
    elif region == "ap-southeast-1":
        return Location.APSoutheast
    elif region == "ap-southeast-2":
        return Location.APSoutheast2
    elif region == "cn-north-1":
        return Location.CNNorth1
    elif region == "eu-west-1":
        return Location.EU
    elif region == "eu-central-1":
        return Location.EU
    elif region == "sa-east-1":
        return Location.SAEast
    elif region == "us-west-1":
        return Location.USWest
    elif region == "us-west-2":
        return Location.USWest2
    else:
        return Location.DEFAULT

# The callback function in boto requires there to be two params
def percent_complete(complete, total):
    sys.stdout.write(".")
    sys.stdout.flush()

