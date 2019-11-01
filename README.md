# Crowfoot


```
        _
       /.\
       Y  \
      /   "|
     //  "/
     |/ /\_E
     / / \-E
    / /
    \/

```

Crowfoot is a bunch of coded infra and script to manage and train DL models at scale in AWS

## Dependencies

* [Troposphere](https://github.com/cloudtools/troposphere)
* [Ansible](https://www.ansible.com/products/automation-platform)
* [Boto](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
* [Cloud formation](https://aws.amazon.com/cloudformation/)

```
virtualenv -p`which python3` py3env
source py3env/bin/activate[...]
pip install -r requirements.txt
```

## Usage:

## Generating AMI images using paquito

Review settings in ami_launch_template.yml which configures AMI creation
```
./paquito.py
```

Once the AMI is ready, edit and review the settings in a stack description file such as
`bert_us-east-1.yaml` and pass it as an argument to the driver:

```
./driver.py bert_us-east-1.yaml
```

This will instantiate a cloud formation template which will spin up resources such as ASGs needed.

To generate a new AMI, use the paquito script. We suggest you add the following lines in ~/.ssh/config so
your SSH sessions (and provisioning via ansible) will not be disconnected due to inactivity.

```
Host *
    ServerAliveInterval 120
    ServerAliveCountMax 10
```
