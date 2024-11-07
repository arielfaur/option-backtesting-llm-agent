from datetime import datetime 
import os
from sqlalchemy import BIGINT, CHAR, MetaData, create_engine, Integer, Float, String, DateTime, Date, Time, DECIMAL, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, mapped_column
import logging
import sys
import nest_asyncio

nest_asyncio.apply()

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


# Define the database connection string
engine = create_engine("sqlite:///data/options.db", echo=True)
metadata_obj = MetaData()

    
# Create a configured "Session" class
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

# Create a base class for declarative class definitions
class Option(Base):
    __tablename__ = 'nvda'
    
    id = mapped_column(Integer, primary_key=True)
    quote_date = mapped_column(Date, index=True)
    type = mapped_column(CHAR(1), index=True)
    underlying_last = mapped_column(DECIMAL(10,2))
    expire_date = mapped_column(Date, index=True)
    dte = mapped_column(DECIMAL(10,2))
    delta = mapped_column(DECIMAL(10,2))
    gamma = mapped_column(DECIMAL(10,2))
    vega = mapped_column(DECIMAL(10,2))
    theta = mapped_column(DECIMAL(10,2))
    rho = mapped_column(DECIMAL(10,2))
    iv = mapped_column(DECIMAL(10,2), nullable=True)
    volume = mapped_column(Integer, nullable=True)
    last = mapped_column(DECIMAL(10,2))
    size = mapped_column(String)
    bid = mapped_column(DECIMAL(10,2))
    ask = mapped_column(DECIMAL(10,2))
    strike = mapped_column(DECIMAL(10,2))
    strike_distance = mapped_column(DECIMAL(10,2))
    strike_distance_pct = mapped_column(DECIMAL(10,2))

# Drop and recreate all tables in the engine.
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

def load_csv(file_path):
    # Initialize an empty list to store the data from the CSV file
    data = []
    
    with open(file_path, 'r') as f:
        next(f)
        for line in f.readlines():
            row = [x.strip() for x in line.split(',')]
            data.append(row)
    
    return data

def add_to_database(data: list, batch_size=1000):
    # Create a new session
    session = Session()

    for i in range(0, len(data), batch_size):
        rows = data[i:i+batch_size]
        
        for row in rows:
            option = Option()
            option.quote_date = datetime.strptime(row[0], '%Y-%m-%d')
            option.type = "C"
            option.underlying_last = float(row[1])
            option.expire_date = datetime.strptime(row[2], '%Y-%m-%d')
            option.dte = float(row[3]) if row[3] != '' else None
            option.delta = float(row[4]) if row[4] != '' else None
            option.gamma = float(row[5]) if row[5] != '' else None
            option.vega = float(row[6]) if row[6] != '' else None
            option.theta = float(row[7]) if row[7] != '' else None
            option.rho = float(row[8]) if row[8] != '' else None
            option.iv = float(row[9]) if row[9] != '' else None
            option.volume = int(str(row[10]).split('.')[0]) if row[10]!= '' else None
            option.last = float(row[11]) if row[11] != '' else None
            option.size = str(row[12]) if row[12]!= '' else None
            option.bid = float(row[13]) if row[13]!= '' else None
            option.ask = float(row[14]) if row[14]!= '' else None
            option.strike = float(row[15]) if row[15]!= '' else None
            option.strike_distance = float(row[27]) if row[27]!= '' else None
            option.strike_distance_pct = float(row[28]) if row[28]!= '' else None
            session.add(option)

            option = Option()
            option.quote_date = datetime.strptime(row[0], '%Y-%m-%d')
            option.type = "P"
            option.underlying_last = float(row[1])
            option.expire_date = datetime.strptime(row[2], '%Y-%m-%d')
            option.dte = float(row[3]) if row[3] != '' else None
            option.delta = float(row[20]) if row[20] != '' else None
            option.gamma = float(row[21]) if row[21] != '' else None
            option.vega = float(row[22]) if row[22] != '' else None
            option.theta = float(row[23]) if row[23] != '' else None
            option.rho = float(row[24]) if row[24] != '' else None
            option.iv = float(row[25]) if row[25] != '' else None
            option.volume = int(str(row[26]).split('.')[0]) if row[26]!= '' else None
            option.last = float(row[19]) if row[19] != '' else None
            option.size = str(row[18]) if row[18]!= '' else None
            option.bid = float(row[16]) if row[16]!= '' else None
            option.ask = float(row[17]) if row[17]!= '' else None
            option.strike = float(row[15]) if row[15]!= '' else None
            option.strike_distance = float(row[27]) if row[27]!= '' else None
            option.strike_distance_pct = float(row[28]) if row[28]!= '' else None
            session.add(option)
        
        # Commit the changes and flush pending writes
        session.commit()
        session.flush()  # Added this line
    
    # Close the session after all batches have been processed
    session.close()


f = "./data/nvda_eod_2023.csv"
add_to_database(load_csv(f))


