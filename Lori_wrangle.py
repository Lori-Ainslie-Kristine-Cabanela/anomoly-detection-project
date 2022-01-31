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


# create functions to use
def prep_data_by_user(df, user):
    '''
    This function takes in a dataframe and a user id and returns a dataframe with data for only that user
    '''
    df = df[df.user_id == user]
    df.date = pd.to_datetime(df.date)
    df = df.set_index(df.date)
    single_user_data = df.path.resample('d').count()
    return single_user_data

def compute_pct_b(single_user_data, span, weight, user):
    '''
    This function adds the %b of a bollinger band range for the page views of a single user's log activity
    '''
    # Calculate upper and lower bollinger band
    midband = single_user_data.ewm(span=span).mean()
    stdev = single_user_data.ewm(span=span).std()
    ub = midband + stdev*weight
    lb = midband - stdev*weight
    
    # Add upper and lower band values to dataframe
    bb = pd.concat([ub, lb], axis=1)
    
    # Combine all data into a single dataframe
    my_df = pd.concat([single_user_data, midband, bb], axis=1)
    my_df.columns = ['single_user_data', 'midband', 'ub', 'lb']
    
    # Calculate percent b and relevant user id to dataframe
    my_df['pct_b'] = (my_df['single_user_data'] - my_df['lb'])/(my_df['ub'] - my_df['lb'])
    my_df['user_id'] = user
    return my_df

def plot_bands(my_df, user):
    '''
    This function plots the bollinger bands of the page views for a single user
    '''
    fig, ax = plt.subplots(figsize=(12,8))
    ax.plot(my_df.index, my_df.single_user_data, label='Number of Pages, User: '+str(user))
    ax.plot(my_df.index, my_df.midband, label = 'EMA/midband')
    ax.plot(my_df.index, my_df.ub, label = 'Upper Band')
    ax.plot(my_df.index, my_df.lb, label = 'Lower Band')
    ax.legend(loc='best')
    ax.set_ylabel('Number of Pages')
    plt.show()

def find_anomalies(df, user, span, weight, plot=False):
    '''
    This function returns the records where a user's daily activity exceeded the upper limit of a bollinger band range
    '''
    # Reduce dataframe to represent a single user
    single_user_data = prep_data_by_user(df, user)
    
    # Add bollinger band data to dataframe
    my_df = compute_pct_b(single_user_data, span, weight, user)
    
     # Plot data if requested (plot=True)
    if plot:
        plot_bands(my_df, user)
    
    # Return only records that sit outside of bollinger band upper limit
    return my_df[my_df.pct_b>1]