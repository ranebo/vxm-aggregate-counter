# vxm-aggregate-counter
Program to count concrete aggregate material and control VXM stepper motor

### Building executable
See instructions for installation and usage: [https://github.com/cdrx/docker-pyinstaller](https://github.com/cdrx/docker-pyinstaller)


TODO: For me, fix tkinter on local environment: https://github.com/pyenv/pyenv/issues/1375
although pyenv location here: code /usr/local/Cellar/pyenv/1.2.13_1/plugins/python-build/bin/python-build

'Reverse' Functionality - Key bind to 'r' and add radio button 'switches' for 'Right' and 'Left': https://stackoverflow.com/questions/49323339/python-3-tkinter-switch-button
Don't want to flip arrow key functionalities so use 'evt' argument to determine if need to ignore 'reverse' flag

Add input field for entering raw commands for debugging stepper motor
