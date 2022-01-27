import pandas as pd
import numpy as np

import env
import os


def get_connection(db, user=env.user, host=env.host, password=env.password):
    '''
    This function takes in user credentials from an env.py file and a database name and creates a connection to the Codeup database through a connection string 
    '''
    return f'mysql+pymysql://{user}:{password}@{host}/{db}'


curriculum_sql_query =  '''
                    SELECT * FROM logs
                    LEFT JOIN cohorts ON logs.cohort_id = cohorts.id;
                    '''

def query_curriculum_data():
    '''
    This function uses the get_connection function to connect to the SQL database and returns the data read into a pandas dataframe
    '''
    return pd.read_sql(curriculum_sql_query,get_connection('curriculum_logs'))

def get_curriculum_data():
    '''
    This function checks for a local file and reads it into a pandas dataframe, if it exists. If not, it uses the get_connection & query functions to query the data and write it locally to a csv file
    '''
    # If csv file exists locally, read in data from csv file.
    if os.path.isfile('curriculum_logs.csv'):
        df = pd.read_csv('curriculum_logs.csv', index_col=0)
        
    else:
        
        # Query and read data from database
        df = query_curriculum_data()
        
        # Cache data
        df.to_csv('curriculum_logs.csv')
        
    return df


def prep_curriculum_data():
    # use a function to connect to and pull in data from SQL
    df = get_curriculum_data()
    # concatenate date and time columns
    df['date'] = df.date + ' ' + df.time
    # convert date column to datetime
    df.date = pd.to_datetime(df.date)
    # set date column as index
    df = df.set_index('date').sort_index()
    # convert other date columns to date_time
    df[['start_date', 'end_date', 'created_at', 'updated_at']].apply(pd.to_datetime)
    # drop unnecessary columns
    df.drop(columns=['time', 'id', 'slack', 'deleted_at'], inplace=True)
    # create a column that identifies the program for each observation
    df['program'] = ['fullstack_php'if x ==1 else
                     'fullstack_jave'if x ==2 else
                     'data_science' if x ==3 else 
                     'front_end' for x in df.program_id]
    
    return df