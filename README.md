### interview-test-task-1

Repository that contains solution for my job interview

## How to install

1. Clone project
2. Create copy of "config.py.default" and rename it to "config.py"
3. Add your database connection string
4. Run migration(s)
5. Use this masterpiece :)

## Available endpoints

1. route: "/" 
    - main application view (UI)
    - method: GET

2. route: "/devices" 
    - fetches all devices that were imported to the system
    - method: GET

3. route: "/contents" 
    - fetches all contents that were attached to the specified that were imported to the system
    - Request arguments: 
         - "device_id"
              - ID of device that is already imported
              - type: int
              - required: True

4. route: "/import" 
    - imports data from CSV file(s) to the database

5. route: "/folders" 
    - it fetches all folders relative to the "uploads" folder where import CSV files will be located

## UI Screenshots

Screenshot #1
[Imgur](https://i.imgur.com/SspWo1p.png)

Screenshot #2
[Imgur](https://i.imgur.com/VWwKa9D.png)
