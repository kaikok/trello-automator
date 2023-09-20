# Trello Automator

## Setting Up

### Install required modules

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create the .env file with the following variables

|Sno|Key|Value description|
|---|---|---|
|1|API_KEY|For Trello API. Go to https://trello.com/power-ups/admin to get them.|
|2|TOKEN|For Trello API. Go to https://trello.com/power-ups/admin to get them.|
|3|CARDS_FILE|File name for local storage of Cards retrieved from Trello.|
|4|ACTIONS_FILE|File name for local storage of Actions retrieved from Trello.|
|5|BOARD_NAME|Name of the Trello board where we want to work on|
|6|DONE_LIST_NAME|Name of the Trello list that contains done cards of the given Trello board|
|7|ARCHIVAL_BOARD_NAME|Name of the Trello board where we want to archive cards that are done|


## How to running Linting

```
autopep8 --in-place -r tests/*.py *.py
```

## How to run tests

```
pytest -s -vv
```

## How to generate test coverage report

```
pytest --cov=.
```

With html visual report
```
pytest --cov-report html --cov=.
```

## How to run script

```
python3 daily_task.py
```