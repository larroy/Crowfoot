from util import *
import os
from infrastructure import *
from subprocess import check_call

def prepare() -> None:
    """
    Entry point
    """
    root = get_root()
    j = os.path.join
    print('Prepare! {}'.format(os.getcwd()))
    infra_template = create_infra_template()
    print(infra_template.to_json())
    tparams = dict(
        Parameters=[
            {'ParameterKey': 'KeyName', 'ParameterValue': 'ssh_pllarroy_key'},
            {'ParameterKey': 'AMI', 'ParameterValue': 'ami-01119ef97534f61f9'},
        ]
    )
    instantiate_CF_template(infra_template, "Bert-pllaroy", **tparams)


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


def run() -> None:
    pass
