# instrument_db
This project is for the Item Catalog module in Udacity's Nanodegree program.

# Requirements

1. Python v2.7 installed
2. The latest vagrant build
3. Flask v0.9 installed
4. SQLAlchemy v1.1.4 installed

# Instrument DB Files

1. project.py - This contains all of the scripts needed to run the application
2. database_setup.py - This contains all of the table data and is used to construct our database
3. client_secrets.json - This contains all of the client ID and secret information needed to utilize OAuth with Google
4. fb_client_secrets.json - This contains all of the client ID and secret information needed to utilize OAuth with Facebook
5. db_instrument_insert.py - Inserts test data into our database
6. /static/new-styles.css - CSS for the application
7. /templates/ - Contains all templates for the application

# Starting the Vagrant Virtual Machine

Before creating your database you must start up your VM or virtual machine. Here is how you do that:

1. In your terminal, navigate to the directory for this project then use the command ```vagrant up```. This powers up the virtual machine.
2. You need to login to the virtual machine and you can do this by typing the command ```vagrant ssh```.

# Instrument DB Database

After you've started up the virtual machine and logged in, you will need to create an instrument database.

To create the database that has already been constructed, you must do the following:

1. Run the command ```python database_setup.py``` in the terminal
2. To populate the database with the data I've provided, you can run the command ```python db_instrument_insert.py``` in the terminal

# Running the Application

After the database has been set up, we can run our application.

To run the application we must simply run the command ```python project.py``` which will start our server and allow us to begin using our application on http://localhost:8000/
