import pandas as pd
import numpy as np
import env
import os



def get_db_url(database):
        url = f'mysql+pymysql://{env.user}:{env.password}@{env.host}/{database}'
        return url



def get_curriculum_logs():
    sql = """
          SELECT * FROM logs
                    LEFT JOIN cohorts ON logs.cohort_id = cohorts.id;
          """
    url = get_db_url('curriculum_logs')
    df = pd.read_sql(sql, url)
    return df



def read_curriculum_logs():
    """This function reads in the curriculum logs dataset from the CodeUp db, writes data to a csv 
    file if a local file does not exist, and returns a df"""
    if os.path.isfile('curriculum-logs.csv'):
    # If csv file exists, read in data from csv file.\n",
        df = pd.read_csv('curriculum-logs.csv', index_col = 0)
    else:
    # Read fresh data from db into a DataFrame.
        df = get_curriculum_logs()
    # Write DataFrame to a csv file.
        df.to_csv('df.csv')
    return df




def prep_curriculum_data():
        '''
    This function 
    '''
    # use a function to connect to and pull in data from SQL
        df = get_curriculum_logs()

    # convert date to a pandas datetime format and set as index
        df.date = pd.to_datetime(df.date)
        df = df.set_index(df.date)

    # drop original date column
        df.drop(columns='date',inplace=True)

    # rename the following columns for clarity
        df.rename(columns = {'path':'endpoint', 'ip':'ip_address', 'name':'cohort_name'}, inplace = True)

    # drop unnecessary columns

    # create column for program names
        df['program_name'] = df.program_id.map({1.0: 'PHP Full Stack Web Development',
                                        2.0: 'Java Full Stack Web Development',
                                        3.0: 'Data Science',
                                        4.0: 'Front End Web Development'})

    # create column for program

        df['program'] = df.program_id.map({1.0: 'Web Development',
                                   2.0: 'Web Development',
                                   3.0: 'Data Science',
                                   4.0: 'Web Development'})


    # convert other date columns to date_time
        df[['start_date', 'end_date', 'created_at', 'updated_at']].apply(pd.to_datetime)


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