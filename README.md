# How to run this repo locally

To get up and running you will first need to:
* Get Vagrant installed
* Get VirtualBox installed

Then:
* Do `vagrant up`
* Clone the repo and do `vagrant provision`

There may be a problem with your VirtualBox that means when you `vagrant up` it hangs and eventually gives an error message.
A fix in the meantime is to do this:

Select virtual machine in question -> Settings -> Network -> Advanced and then make sure the “cable connected” box is checked.

You should now:
* Do `vagrant ssh` into the VirtualBox
* Do `make watch` to compile the SCSS
* Do `make run` to run the local server
