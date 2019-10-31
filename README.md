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

## Example of use:

The driver can call any function on any module inside the base directory. -f chooses the function
and -m the module (by default is prepare.py).

```
./driver.py bert


./driver.py -f provision bert

./driver.py -f create_inventory bert
```

## Generating AMI images using paquito

To generate a new AMI, use the paquito script. We suggest you add the following lines in ~/.ssh/config so
your SSH sessions (and provisioning via ansible) will not be disconnected due to inactivity.

```
Host *
    ServerAliveInterval 120
    ServerAliveCountMax 10
```

Generating an image with Paquito:

```
./paquito.py
```

