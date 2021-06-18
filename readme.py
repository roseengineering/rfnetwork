
import subprocess 


def spawn(command):
    proc = subprocess.Popen("PYTHONPATH=. " + command, shell=True, stdout=subprocess.PIPE)
    proc.wait()
    return ''

def run(command, language=""):
    proc = subprocess.Popen("PYTHONPATH=. " + command, shell=True, stdout=subprocess.PIPE)
    proc.wait()
    buf = proc.stdout.read().decode()
    return f"""
```{language}
$ {command}
{buf}\
```
"""


print(f"""\
# Rfnetwork

## Introduction

Rfnetwork.py is a simple utility for 
generating Spice netlist subcircuits 
which match the input impedance of
a source to the output impedance of 
a load or, as usually is the case, the line.

The python utility supports
three impedance matching circuits:

1. The LCC Match
2. The Pi Match
3. The Tee Match

The utility also performs a validation
of the subcircuit to ensure
the matching actually works.  If the validation
fails an error will be thrown.  See the Spice
comment, Zin, in the subcircuit.

Complex load (or line) impedances are not supported.

## Walkthrough

To generate a netlist to match a source impedance of 
10+10j ohms at 7 Mhz to a load of 50 ohms using a LCC network with a Q of 3 run:

{run("python3 rfnetwork.py --name lcc_output --source 10+10j -q 3 --frequency 7e6 --lcc")}

To generate a Tee network instead use:

{run("python3 rfnetwork.py --name tee_output --source 10+10j -q 3 --frequency 7e6 --tee")}

Since a Pi network is impractical for small source impedances, let's
assume the source impedance is 1000-100j.
In addition because an error gets thrown for a Q of 3, change the Q to 5 instead.

{run("python3 rfnetwork.py --name pi_output --source 1000-100j -q 5 --frequency 7e6 --pi")}

If you want to reverse the network, for example to match the line to the input of a (high-Z) amplifier, use the --reverse option.

{run("python3 rfnetwork.py --name pi_input -r --source 1000-100j -q 5 --frequency 7e6 --pi")}

## How to Install

Perform a pip install of the required python libraries using:

{run("pip install -r requirements.txt")}

## Command Line Usage

The utility's command line usage is as follows:

{run("python3 rfnetwork.py --help")}

## The Matching Networks

See the image below for the impedance matching
networks supported:

![](networks.png)

""")



