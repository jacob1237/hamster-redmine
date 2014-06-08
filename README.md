Hamster-redmine
===============

Synchronize your Project Hamster time entries with Redmine server

Dependencies
---------------
python-redmine: https://github.com/maxtepkeev/python-redmine

Installation
---------------
In first you will need to install dependencies:

    pip install python-redmine

Then unpack this script to any folder and edit *hamster-redmine.conf*.  
Edit the *db_path* parameter if your Project Hamster database is not in default folder.  

All done. Now you can use it.

Usage
---------------

./hamster-redmine.py [-h] [-c C] [-d D] [-p PROJECT] [-t T]

optional arguments:

> -h, --help  
show this help message and exit

> -c C, --config C  
Config file path

> -d D, --date D  
Single date or date range in format DD.MM.YYYY or DD.MM.YYYY-DD.MM.YYYY

> -p PROJECT, --project PROJECT  
Specific project name

> -t T, --tags T  
Specific tags separated by commas

If no arguments are given, script will synchronize todays activities

License
---------------

MIT
