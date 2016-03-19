
The Dynamic Hybrid Routing Controller Project
============================

This is an implementation of the Dynamic Hybrid Routing: Achieve Load Balancing for Changing Traffic Demands

It is built on top of Brandon Heller's Ripl library, Stanford CS244 Final Project and POX controller with minor changes to both to support version consistency and Hedera functionality.

Use a CS 244 Mininet VM to run the code (either from the class website or an Amazon EC2 instance).

1. Switch to the CS 244 version of Mininet

    `$ cd ~/mininet`

    `$ git checkout -b cs244 origin/class/cs244`

2. Fix the module dependencies for this version

    `$ vim ~/mininet/mininet/moduledeps.py`

    (^change this line: "-OVS_KMOD = 'openvswitch_mod'"
                    to: "OVS_KMOD = 'openvswitch'")

3. Install the correct version

    `$ cd ~/mininet`

    `$ sudo make install`

4. Switch to the 'dart' branch of POX

    `$ cd ~/pox`

    `$ git checkout dart`

    `$ git pull origin dart`

5. Clone our project repo

    `$ cd ~`

    `$ git clone https://github.com/lyzsysu/dhrpox.git`

    `cd dhrpox/`

    `$ sudo python setup.py install`

6. Run it!

    `$ cd ~/244proj`

    Terminal #1 - start the remote controller

    `$ sudo ~/pox/pox.py controllers.dhrpox --topo=abilene`

    Terminal #2 - start the mininet

    `$ sudo python ~/dhrpox/abilene.py algorithm traffic.json`
    
    eg:
    
    `$ sudo python ~/dhrpox/abilene.py dhr TM1.json`

7. Debug

    you can use the following comand to open an abilene topo to do some test

    `$ sudo mn --custom ~/dhrpox/ripllib/mn.py --topo abilene --controller=remote --link=tc --mac`

