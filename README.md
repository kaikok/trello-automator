# Trello Automator


## Introduction

This software serves to retrieve Trello boards and cards via Trello APIs and perform customised processing on them.

## Getting Started

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
|8|CONFIG_FILE|File name for JSON based configuration file.|


### Starting the software

```
python3 daily_run.py
```

## User Documentation

List of available tasks
- Archival Task
- Card Sync Task

### Archival Task

This task monitors the cards within the Done list in a given kanban Trello Board.
Once a 2 week Sprint has ended, it will move those cards into another Trello board for archival.

For each sprint, the cards are archived into a list with the first day of the sprint as it's list name. Eg. 2023-10-11T00:00:00.

The settings are currently configured from the .env file.

 - BOARD_NAME
 - DONE_LIST_NAME
 - ARCHIVAL_BOARD_NAME

### Card Sync Task

This task essentially create and link cards from across different mulitple boards into a single list of a single board with a placeholder card.

To illustrate the use case, we will use the following example.

We have multiple Kanban boards, A and B with their own respective Todo, In-Progress and Done list.

We also have a Kanban board, C that we goto as a single point of reference for our own cards. This board will also have its own Todo, In-Progress and Done list.

When we create a new card, A1 at Todo list on board A, a placeholder card, A1' will be created on the Todo list of board C.
Similarly, when another card, B1 is created on board B, a placeholder card, B1' will be created on the same Todo list of board C.

The two placeholder cards will contain the link back to the original cards A1 and B1 located on board A and B respectively.

When we move the placeholder card, A1' from Todo to In-Progress list on board C, the original card, A1 will be moved correspondingly between the Todo and In-Progress list on board A. Movement beyond this 3 list will not be mirrored as individual boards A and B might have their own archival rules or destinations.

The configuration input required for this task are as follows:

```JSON
{
  "tasks": [
    "card_sync" : {
      "persistence" :{
        "json_file": "card_sync.json"
      },
      "destination_board" : {
        "name" : "board_c",
        "list_names": {
          "todo" : "todo_list_name",
          "in_progress" : "in_progress_list_name",
          "done" : "done_list_name",
        }
      },
      "source_boards" : [
        {
          "name" : "board_a",
          "list_names": {
            "todo" : "todo_list_name",
            "in_progress" : "in_progress_list_name",
            "done" : "done_list_name",
          }
        },
        {
          "name" : "board_b",
          "list_names": {
            "todo" : "todo_list_name",
            "in_progress" : "in_progress_list_name",
            "done" : "done_list_name",
          }
        }
      ]
    }
  ]
}
```

These settings are to be added to the JSON config file specified by the environment variable, CONFIG_FILE.

## Developer FAQs

### How to running Linting?

```bash
autopep8 --in-place -r tests/*.py *.py
```

### How to run unit tests?

```bash
pytest -s -vv
```

### How to generate test coverage report?

```bash
pytest --cov=.
```

With html visual report

```bash
pytest --cov-report html --cov=.
```