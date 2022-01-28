# Ideable-BE (Back-End)
## What is this ?
REST API app for Ideable (Jira-like software development tracker). A self-developed project for learning purpose.

## How to test this app in your local environment ?
### Prerequisite installations
#### 1. Python 3
#### 2. PIP
#### 3. [ideable-queue-consumer app](https://github.com/gatraenggar/ideable-queue-consumer)

### Installation
#### 1. Install a virtual environment
    py -m pip install virtualenv
#### 2. Create virtual environment directory
    py -m venv project-name
#### 3. Enter the virtual environment directory
    cd project-name
#### 4. Enter the virtual environment
    Scripts\activate.bat
#### 5. Clone the GitHub repository
    git clone https://github.com/gatraenggar/ideable-be.git
#### 6. Enter the project directory
    cd ideable-be
#### 7. Install all dependencies needed
    py -m pip install -r requirements.txt

### Configuration
#### 8. Create a PostgreSQL database
#### 9. Rename `example.env` to `.env`. Then change the all values inside the double square brackets in that `.env` file based on yours
#### 10. Change `access_token_key`, `refresh_token_key`, and `random_token_key` in `.env` file with your generated encryption keys
You can generate your own encryption keys with following steps:
1. Enter this site https://www.allkeysgenerator.com/Random/Security-Encryption-Key-Generator.aspx
2. Choose `Encryption key`
3. Check the `Hex ?` field
4. Click the `512-bit` option
5. Click `Get new results` button, then copy the generated string to the config file

### Run the App
#### 11. Migrate/create the database tables through this command
    py manage.py migrate
#### 12. Make sure the [ideable-queue-consumer app](https://github.com/gatraenggar/ideable-queue-consumer) has running. Then run this to start-up the app in development
    py manage.py runserver localhost:8080