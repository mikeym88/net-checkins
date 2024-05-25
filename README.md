# Amateur Radio Net Check-in Package

This is a utility to manage Ham Radio Net Check-ins.

## Where are the logs stored? How to I view them?

Currently they're being stored in a SQLite3 database locally on the hard drive. 
The filename will be `checkins.db` and you can read the file with the following applications:

* [DBeaver](https://dbeaver.io/)
* [DB Browser for SQLite](https://sqlitebrowser.org/)

## Running

### PowerShell

```PowerShell
./run.ps1
```

### Bash

```bash
./run.sh
```

### Python

```Python
python main.py
```

## Alternatives

There are a few alternatives out there:

* [Net Logger](https://www.netlogger.org/)
* [Net Logger Companion](https://play.google.com/store/apps/details?id=com.group427.netloggercompanion)
* [Ham.live](https://www.ham.live/)
* [Reddit's Suggestions](https://www.reddit.com/r/amateurradio/comments/10e51t9/what_is_your_favourite_logging_software_and_more/)
