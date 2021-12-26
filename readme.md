# Owon HDS200 Oscilloscope Interface

the Owon HDS200 series handheld oscilloscopes (HDS242, HDS272, maybe others) come with native Windows software for interacting with the 'scope over USB, but no way to talk to them from other OSs. Thise library and utilites allows the scope to be controlled form Python on any OS.

## hds_term.py

A simple command-line REPL style terminal interface to the scope. The scope command set is a subset of the IEEE488.2 SCPI interface. The tool provides some basic autocomplete to help with exploring the SCPI command space. There's also a very basic command validator to prevent sending invalid commands to the scope, which usually causes the scope firmware to crash.

It also has a few direct control commands:

* save: Save the most recent response from the scope to a file. The file is just the raw binary.
* exit: Quit the program
* help: Show help message

## hds_dump.py

A quick script to dump the data for any currently active channels. Data is dumped as both binary and CSV (one row per entry). The data is just the raw samples from the 'scope, no conversion to volts or anything yet.
