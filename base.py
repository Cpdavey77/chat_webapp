from sqlalchemy import create_engine, or_, and_
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

#I use the automap method to map my database I created from an external application, to python
#So that I can avoid manually creating a database in python
Base = automap_base()

engine = create_engine("sqlite:///Users.db", connect_args={"check_same_thread": False})

Base.prepare(autoload_with=engine)

#Map the tables from my database
Users = Base.classes.Users
Contacts = Base.classes.Contacts

db_session = sessionmaker(bind=engine)

db = db_session()


