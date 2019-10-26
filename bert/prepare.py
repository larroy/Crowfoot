from util import *
import os
from infrastructure import *
from subprocess import check_call
import boto3

def prepare(config) -> None:
    """
    Entry point
    """
    root = get_root()
    boto3.setup_default_session(region_name=config['aws_region'], profile_name=config['aws_profile'])
    infra_template = create_infra_template(config)
    print(infra_template.to_json())
    tparams = dict(
        Parameters=[
            {'ParameterKey': 'KeyName', 'ParameterValue': config['key']},
            {'ParameterKey': 'AMI', 'ParameterValue': config['ami']},
            {'ParameterKey': 'ResourceName', 'ParameterValue': config['resource_name']},
        ]
    )
    instantiate_CF_template(infra_template, config['stack_name'], **tparams)


def provision() -> None:
    create_inventory()
    create_hosts_file()
    ansible_cmd =  [
        'ansible-playbook',
        '--inventory-file', 'inventory.yaml',
        'playbook.yml'
    ]
    logging.info("Executing: '{}'".format(' '.join(ansible_cmd)))
    os.environ['ANSIBLE_HOST_KEY_CHECKING']='False'
    check_call(ansible_cmd)
