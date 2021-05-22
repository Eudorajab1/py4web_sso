# Py4web SSO app

A first attempt at a [Py4web](https://py4web.com/) Single Sign On (SSO) app which allows multiple applications hosted on the same server to use a single instance of the standard Py4web Auth functionalitly in a seperate app without the need for each application to have its own auth database.

The intention is to extend the functionality to include remote hosting of the SSO server.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See the relevant deployment documentaion for notes on how to deploy the project on a live system. Installation and setup will vary depending on your operating system and preferred installation method and are covered in great detail in Py4web doucumentation which can be found here https://py4web.com/_documentation/static/en/index.html

### Prerequisites

* Python 3
* A working Py4Web installation (reccoment a virtual environment for testing)
* python Pillow is the only additional package that needs to be installed https://pypi.org/project/Pillow/ (pip install Pillow)

### Installing

Depending on your requirements and OS installation will vary.

Full documentation for the installation and usage for Py4Web can be found at https://py4web.com/_documentation/static/en/index.html

Example:

Create a python3 virtual environment in the location of your choice or follow py4web installation procedures for deployment
```
$ cd /opt
$ python3 -m venv py4web_sso
```
Activate the virtual environment
```
$ source py4web_sso/bin/activate
(py4web_sso)$
```
Install the latest Py4Web in the newly created virtual environment
```
(py4web_sso)$ cd py4web_sso
(py4web_sso)$ python3 -m pip install --upgrade py4web --no-cache-dir
pip3 -m install Pillow (or equivalent based on your OS)
```
Hint: If python3 doesnt work try using just pyhon instead.
```
git clone https://github.com/Eudorajab1/py4web_sso.git into ./apps (to create the _sso_server and 3 client apps or alernatively you can copy them into existing apps directory or use git submodules)
```
## First Run
```
$ py4web run apps
```
Once py4web is running you can access a specific app at the following urls from your browser:
```
http://localhost:8000/_sso_server
http://localhost:8000/client_1
http://localhost:8000/client_2
http://localhost:8000/client_3
```
In order to stop py4web, you need to hit Control-C on the window where you run it.
Please refer to the user documentation if you need to change the configs or wish to use different ports etc.

## Initialise the database
This repo contains the data needed in order to test this app. The data consists of 4 users in the auth_user table namely:-
* username: admin password: testadmin1! (the main admin user for the _sso_server can access all)
* username: user1 password: user1test1! (can access client_1 and client_2)
* username: user2 password: user2test1! (can access client_2 and client_3)
* username: user3 password: user3test1! (can access client_3)

## Considerations
The SSO Server uses the datatables (client side) and Bulma css for grid and displaying of forms etc.
The clients are absolute statard Py4web apps with calls to the sso server for login logout etc.
All should be clear from the client code

# Adding a new client
You must be logged in as a user of group Admin in order to add new clients and users to the SSO server.
Once logged in you will see the options to Mange Groups, Clients and Users.
Simply fill in the forms and copy the generated secret to the new cleint you are adding along with other settings as per the example clients
Add Client users to the table and provided tha clients are registered on the SSO server they will be able to access the clients.

## Authors

* **John Bannister** - *Initial work* - [Eurodrajab1](https://github.com/Eudorajab1)

## License

This project is licensed under the MIT License

## Acknowledgments

* Hat tip to the Py4web team and Andrew Gavgavian for great work on the py4web-blog (from which I borowed the login and profile layouts albeit converting them to Bulma from bootstrap)

### All comments, suggestions and crticisms gratefully accepted and please feel free to contribute and colloborate
