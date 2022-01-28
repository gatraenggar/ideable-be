# Ideable-BE (Back-End)
## What is this ?
REST API app for Ideable (Jira-like software development tracker). A self-developed project for learning purpose.

## How to test this app in your local environment ?
### Prerequisite installations
#### 1. Python 3
#### 2. PIP
#### 3. [ideable-queue-consumer app](https://github.com/gatraenggar/ideable-queue-consumer)

### Installation
#### 1. `py -m pip install virtualenv`
#### 2. `py -m venv project-name`
#### 3. `cd project-name`
#### 4. `Scripts\activate.bat`
#### 5. `git clone https://github.com/gatraenggar/ideable-be.git`
#### 6. `cd ideable-be`
#### 7. `py -m pip install -r requirements.txt`

### Configuration
#### 4. Create a PostgreSQL database
#### 5. Rename `example.env` to `.env`. Then change the all values inside the double square brackets in that `.env` file based on yours
#### 5.1. Change `access_token_key`, `refresh_token_key`, and `random_token_key` in `.env` file with your generated encryption keys
You can generate your own encryption keys with following steps:
1. Enter this site https://www.allkeysgenerator.com/Random/Security-Encryption-Key-Generator.aspx
2. Choose `Encryption key`
3. Check the `Hex ?` field
4. Click the `512-bit` option
5. Click `Get new results` button, then copy the generated string to the config file

### Run the App
#### 6. `py manage.py migrate` to migrate/create the database tables
#### 7. Make sure the [ideable-queue-consumer app](https://github.com/gatraenggar/ideable-queue-consumer) has running. Then run `py manage.py runserver localhost:8080` to start-up the server in development