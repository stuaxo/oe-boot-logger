Over Engineered Boot Logging.
==

Over engineering things can be fun :)


Note:  Currently this is probably only useful to me.


Collecting info about bugs that can crash the computer or make the screen black can be painful.

I was debugging am issue that could cause a black screen facilitating a reboot.
On rebooting it was important to gather logs from journalctl, then remember what else was
needed for the bug report.


This script simplifies things a little:

Test scenarios can be setup from a templates (see templates/power for an example), with extra information
the user wants to specify: in the power example this includes which power source is being used.

new_test.py

Create a set of pending test scenarios by iterating scenarios.csv and creating a folder for each line in runtime/pending


run_test.py

If there is pending test, then run it (the power test will run amd_s2idle.py).

If the test completes and the user can see the screen, then a result can be recorded by choosing a menu option.
(Menu options are set in quick-responses.csv in the template folder).

If the screen is black the user may restart (e.g. ALT-Printscreen and typing R E I S U B).

On returning the user may run run_test.py again to record the result of the previous test.
