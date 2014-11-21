import boto
import boto.beanstalk
import sys
import time
import yaml
from datetime import datetime
from shovel import task
from boto.s3.connection import Location

@task
def deploy(yaml_path, war_path):
    settings = load_yaml(yaml_path)
    app_name = settings['appName']
    region = settings['region']
    s3_bucket = settings['s3Bucket']
    s3_key = settings['s3Key']
    version_label = settings['versionLabel']
    env_name = settings['environmentName']
    c_name = settings['cName']
    config_template = settings['configTemplate']

    eb_client = boto.beanstalk.connect_to_region(region)

    upload_to_s3(war_path, s3_bucket, s3_key, region)
    if application_exists(eb_client, c_name):
        print "Application '%s' already exists - attempting update" % app_name
        deploy_app(eb_client, app_name, version_label, s3_bucket, s3_key, False)
        update_app(eb_client, env_name, version_label, config_template)
    else:
        print "Could not find application '%s' - creating application" % app_name
        deploy_app(eb_client, app_name, version_label, s3_bucket, s3_key, True)
        create_env(eb_client, app_name, env_name, c_name, version_label, config_template)


def load_yaml(yaml_path):
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    file = open(yaml_path, "r")
    doc = str(yaml.load(file))
    doc = doc.replace('$now', now)
    print doc
    return yaml.load(doc)

def upload_to_s3(file, bucket_name, key_name, region):
    print "Uploading file %s to Amazon S3 bucket '%s' in region '%s'" % (file, bucket_name, region)
    bucket = get_or_create_bucket(bucket_name, region)
    key = boto.s3.key.Key(bucket)
    key.key = key_name
    key.set_contents_from_filename(file, cb=percent_complete, num_cb=10)

def get_or_create_bucket(bucket_name, region):
    print "Check if bucket %s exists" % bucket_name
    s3 = boto.s3.connect_to_region(region)
    bucket = s3.lookup(bucket_name)
    print "Received bucket is %s" % bucket
    if bucket is None:
        print "Bucket does not exist - creating"
        bucket = s3.create_bucket(bucket_name, location=get_location(region))
    return bucket

def application_exists(eb_client, c_name):
    print "Checking if application with cName '%s' already exists" % c_name
    response = eb_client.check_dns_availability(c_name)
    available = response['CheckDNSAvailabilityResponse']['CheckDNSAvailabilityResult']['Available']
    return not available

def deploy_app(eb_client, app_name, version_label, s3_bucket, s3_key, auto_create):
    print "Creating application version '%s'" % version_label
    eb_client.create_application_version(
        app_name,
        version_label,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        auto_create_application=auto_create)

def create_env(eb_client, app_name, env_name, c_name, version_label, template_name):
    print "Creating environment '%s'" % env_name
    eb_client.create_environment(
        app_name,
        env_name,
        cname_prefix=c_name,
        version_label=version_label,
        template_name=template_name)

def update_app(eb_client, env_name, version_label, template_name):
    print "Updating environment '%s' with version '%s'" % (env_name, version_label)
    eb_client.update_environment(
        environment_name=env_name,
        version_label=version_label,
        template_name=template_name)

def wait_for_app(eb_client, app_name, version_label):
    print "Waiting for application to start"
    status = 'Pending'
    while status == 'Pending':
        print "..."
        time.sleep(5)
        response = eb_client.describe_environments(application_name=app_name, version_label=version_label)
        env = response['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments'][0]
        status = env['Status']
    if status == 'Ready':
        print "Application is ready"
    else:
        print "WARNING - application has status %s" % status

# Converts an availability zone
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