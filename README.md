# The Dynamic Hybrid Routing Controller Project
This is an implementation of the Dynamic Hybrid Routing controller supporting pre-installed paths from

    "Dynamic Hybrid Routing: Achieve Load Balancing for Changing Traffic Demands"

It is built on top of Brandon Heller's Ripl library and POX controller and Stanford CS244 Final Project with minor changes to support DHR functionality.

Use a CS 244 Mininet VM to run the code

1.Switch to the CS 244 version of Mininet

  $ cd ~/mininet
  
2.Fix the module dependencies for this version

  $ git checkout -b cs244 origin/class/cs244
  
  (^change this line: "-OVS_KMOD = 'openvswitch_mod'" to: "OVS_KMOD = 'openvswitch'")

3.Install the correct version

  $ cd ~/mininet
  
  $ sudo make install
  
4.Switch to the 'dart' branch of POX

  $ cd ~/pox
  
  $ git checkout dart
  
  $ git pull origin dart
  
5.Clone our project repo

  $ cd ~

  $ git clone https://github.com/lyzsysu/dhrpox.git

  cd 244proj/
  
  $ sudo python setup.py install

  
