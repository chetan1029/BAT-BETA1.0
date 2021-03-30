import getpass
from fabric import Connection, Config, task
from invoke import Responder


BACKEND_BRANCH = "develop"
FRONTEND_BRANCH = "develop"
HOST = "159.203.177.77"
USER = "batman"
BACKEND_APP_DIR = "/home/batman/bat"
FRONTEND_APP_DIR = "/home/batman/bat-front"
VENV = "~/.virtualenvs/bat"


github_user = getpass.getpass("Please enter github username: ")
github_pass = getpass.getpass("Please enter github password: ")

password = getpass.getpass("Please enter password: ")
config = Config(
    overrides={
        'user': USER, 'connect_kwargs': {'password': password}
    })

sudopass = Responder(
    pattern=r'\[sudo\] password:',
    response=password + '\n',
)

gitusername = Responder(
    pattern="Username for 'https://github.com':",
    response=github_user + "\n",
)

gitpassword = Responder(
    pattern="Password for 'https://" + github_user + "@github.com'",
    response=github_pass + "\n",
)


def get_connection():
    return Connection(host=HOST, user=USER, config=config)


@task
def deploy_backend(args):
    connection = get_connection()
    with connection.cd(BACKEND_APP_DIR):
        print("Pulling the latest changes...")
        connection.run(f"git checkout {BACKEND_BRANCH}")
        connection.run(f"git pull origin {BACKEND_BRANCH}", pty=True, watchers=[
                       gitusername, gitpassword])
        with connection.prefix(f"source {VENV}/bin/activate"):
            print("Installing the requirements...")
            connection.run(f"pip install -r requirements/production.txt")
            print("Running the migrations...")
            connection.run(f"python manage.py migrate")
            connection.run(f"python manage.py sync_roles")
            print("Restarting the server...")
            connection.run(f"sudo systemctl restart gunicorn",
                           pty=True, watchers=[sudopass])
            print("Backend is deployed!")


@task
def deploy_frontend(args):
    connection = get_connection()
    with connection.cd(FRONTEND_APP_DIR):
        print("Pulling the latest changes...")
        connection.run(f"git checkout {FRONTEND_BRANCH}")
        connection.run(f"git pull origin {FRONTEND_BRANCH}", pty=True, watchers=[
                       gitusername, gitpassword])
        print("Installing the requirements...")
        connection.run(f"yarn install")
        print("Creating a fresh build...")
        connection.run(f"yarn build-prod")
        print("Frontend is deployed!")


@task
def deploy(args):
    deploy_backend(args)
    # deploy_frontend(args)
