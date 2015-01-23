About ElasticJack
===

ElasticJack is a collection of Python scripts built on top of [Boto](https://github.com/boto/boto) and
[Shovel](https://github.com/seomoz/shovel) to allow easy management of applications on AWS Elastic Beanstalk.

The deploy script allows a deployable (e.g. a war file) to be deployed to Amazon S3, and then creates/updates
the environment for the application based on a given YAML configuration.

The terminate script terminates an ElasticBeanstalk environment based on a given YAML configuration.

Setup
===

Install dependencies
---

To install the required python dependencies, run the following command:

```pip install -r requirements.txt```

If you do not have Pip installed, read more about [installing Pip here](http://pip.readthedocs.org/en/latest/installing.html).

AWS Access Config
---

For the deployer to work, you need to create a file on your system to store your AWS credentials.

In Unix/Linux store your AWS Access Key ID and AWS Secret Access Key in a file ~/.aws/credentials in the 
following format:

```
[Credentials]
aws_access_key_id = <your_access_key_here>
aws_secret_access_key = <your_secret_key_here>
```

In Windows, create a text file that has any name (e.g. boto.config). It’s recommended that you put this 
file in your user folder. Then set a user environment variable named BOTO_CONFIG to the full path of that 
file.

For more information, read about how [Boto manages AWS credentials](http://boto.readthedocs.org/en/latest/boto_config_tut.html).

Create a YAML for an application
---

Each app should have its own YAML file containing the S3 and EBS configurations needed to deploy the app
onto AWS. The following settings should be present:

*	appName
*	region (e.g. eu-west-1)
*	s3Bucket
*	s3Key
*	versionLabel
*	environmentName
*	cName
*	configTemplate

The yaml file can also include a keyword '$now'. The deployer will automatically replace any mentions of 
'$now' with the timestamp that the deploy script was ran at.

E.g. If ran at 31/12/14 23:59:59, 's3Key: deploy-$now.war' becomes 's3Key: deploy-20143112235959.war'

Using
===

To upload a file to AWS and to create/update an environment, run the following command:

```shovel deploy <yamlFilePath> <deployableFilePath>```

To terminate an environment:

```shovel terminate <yamlFilePath>```