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

        