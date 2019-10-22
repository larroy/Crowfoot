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
