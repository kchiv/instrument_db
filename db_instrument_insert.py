from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, InstrumentType, Instrument

engine = create_engine('sqlite:///instruments.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Kyle Chivers", email="chiverskyle@gmail.com",
             picture='https://pbs.twimg.com/profile_images/712837979497103360/xL4mYfUY.jpg')
session.add(User1)
session.commit()

# String instruments
instrumenttype1 = InstrumentType(user_id=1, name_type="String Instruments")

session.add(instrumenttype1)
session.commit()

instrument1 = Instrument(user_id=1, name="Guitar", description="""The guitar is a musical 
                     instrument classified as a string instrument with anywhere from four 
                     to 18 strings, usually having six.""", 
                     instrumenttype=instrumenttype1)

session.add(instrument1)
session.commit()


instrument2 = Instrument(user_id=1, name="Ukelele", description="""A ukelele, sometimes abbreviated to 
                     uke, is a member of the lute family of instruments; it generally employs 
                     four nylon or gut strings or four courses of strings.""", 
                     instrumenttype=instrumenttype1)

session.add(instrument2)
session.commit()


instrument3 = Instrument(user_id=1, name="Mandolin", description="""A mandolin is a musical instrument 
                     in the lute family and is usually plucked with a plectrum or 'pick'.""", 
                     instrumenttype=instrumenttype1)

session.add(instrument3)
session.commit()


# Woodwind instruments
instrumenttype2 = InstrumentType(user_id=1, name_type="Woodwind Instruments")

session.add(instrumenttype2)
session.commit()

instrument1 = Instrument(user_id=1, name="Flute", description="""The flute is a family of musical 
                     instruments in the woodwind group. Unlike woodwind instruments with reeds, 
                     a flute is an aerophone or reedless wind instrument that produces its sound 
                     from the flow of air across an opening.""", 
                     instrumenttype=instrumenttype2)

session.add(instrument1)
session.commit()


instrument2 = Instrument(user_id=1, name="Oboe", description="""Oboes are a family of double 
                     reed woodwind musical instruments. The most common oboe plays in the 
                     treble or soprano range.""", 
                     instrumenttype=instrumenttype2)

session.add(instrument2)
session.commit()


instrument3 = Instrument(user_id=1, name="Clarinet", description="""The clarinet is a 
                     musical-instrument family belonging to the group known as the woodwind 
                     instruments. It has a single-reed mouthpiece, a straight cylindrical 
                     tube with an almost cylindrical bore, and a flared bell. A person 
                     who plays a clarinet is called a clarinetist (sometimes spelled 
                     clarinettist).""", 
                     instrumenttype=instrumenttype2)

session.add(instrument3)
session.commit()



# Brass instruments
instrumenttype3 = InstrumentType(user_id=1, name_type="Brass Instruments")

session.add(instrumenttype3)
session.commit()

instrument1 = Instrument(user_id=1, name="Trumpet", description="""A trumpet is a musical 
                     instrument commonly used in classical and jazz ensembles. The trumpet 
                     group contains the instruments with the highest register in 
                     the brass family.""", 
                     instrumenttype=instrumenttype3)

session.add(instrument1)
session.commit()


instrument2 = Instrument(user_id=1, name="Trombone", description="""The trombone is a musical 
                     instrument in the brass family. Like all brass instruments, sound is 
                     produced when the player's vibrating lips cause the air 
                     column inside the instrument to vibrate.""", 
                     instrumenttype=instrumenttype3)

session.add(instrument2)
session.commit()


instrument3 = Instrument(user_id=1, name="Cornet", description="""The cornet is a brass 
                     instrument similar to the trumpet but distinguished from it by its 
                     conical bore, more compact shape, and mellower tone quality.""", 
                     instrumenttype=instrumenttype3)

session.add(instrument3)
session.commit()


# Percussion instruments
instrumenttype4 = InstrumentType(user_id=1, name_type="Percussion Instruments")

session.add(instrumenttype4)
session.commit()

instrument1 = Instrument(user_id=1, name="Timpani", description="""Timpani, or kettledrums 
                     (also informally called timps), are musical instruments in the 
                     percussion family. A type of drum, they consist of a skin called 
                     a head stretched over a large bowl traditionally made of copper.""", 
                     instrumenttype=instrumenttype4)

session.add(instrument1)
session.commit()


instrument2 = Instrument(user_id=1, name="Snare Drum", description="""The snare drum 
                     or side drum is a percussion instrument that produces a sharp 
                     staccato sound when the head is struck with a drum stick. 
                     Snare drums are often used in orchestras, concert bands, 
                     marching bands, parades, drumlines, drum corps, and more.""", 
                     instrumenttype=instrumenttype4)

session.add(instrument2)
session.commit()


instrument3 = Instrument(user_id=1, name="Bass Drum", description="""A bass drum 
                     is a large drum that produces a note of low definite or 
                     indefinite pitch. Bass drums are percussion instruments 
                     and vary in size and are used in several musical genres.""", 
                     instrumenttype=instrumenttype4)

session.add(instrument3)
session.commit()

print "added instruments!"