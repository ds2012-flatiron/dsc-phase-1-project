"""
This module contains functions for data cleaning and data preparation.
The module is called by import statement from the current folder as
"import data_preparation" or from a parent folder as
"import code.data_preparation"

## Data links:
IMDB data are available at the two separate links: (i) one describes the data by providing data field definitions, and
(ii) the other provides access to the files:

(i) https://www.imdb.com/interfaces/
(ii) https://datasets.imdbws.com/

## SUPPORT FUNCTIONS
There can be an unlimited amount of support functions.
Each support function should have an informative name and return the partially cleaned bit of the dataset.
"""

import os
import pandas as pd
import numpy as np

def df_print_numnullvalues_bycol(df):
    for col in range(df.shape[1]):
        intNumNull = df.iloc[:,col].isnull().sum()
        intNumNan  = df.iloc[:,col].isna().sum()
        print(f"Col {col}: Num NULL {intNumNull}: {df.columns[col]}")
        print(f"Col {col}: Num NaN  {intNumNan}: {df.columns[col]}")

    return None

def parse_bom_gross_revenue_values(colVal):
    """
    Parsing through values in column 'foreign_gross' and converting these values to a numeric format.
    Parsing rules: if 'colVal' is a string
      (i) Null values or empty strings between adjacent commas are set to 0;
     (ii) Null values enclosed in quotation marks are set to 0;
    (iii) colVal has char '.' and ',' to the left of it. This values is gross in million of dollars: remove ',',
          convert the result to 'float', and multiply by 1e6.
    """
    returnValue = 0 # initialize returnValue to zero
    # all chars from string.punctuation except comma (',') and point ('.')
    strInvalidChars = """!"#$%&\'()*+-/:;<=>?@[\\]^_`{|}~""" 
    if type(colVal) == str:
        if len(colVal) == 0:
            ### it may mean there was no release in any foreign location
            return 0
        elif colVal.isnumeric():
            ### the string contains only numeric data
            try:
                returnValue = np.uint64(colVal)
            except TypeError as err:
                print(f"Type Error: cannot convert string value --{colVal}-- to np.uint64")
                print("Error Output:\n", err)
        elif ('.' in colVal) and (colVal.count('.') == 1) and (',' not in colVal):
            ### sting values of type '1235356.343'
            try:
                returnValue = np.float64(colVal)
                returnValue = np.uint64(returnValue)
            except TypeError as err:
                print(f"Type Error: cannot convert string value --{colVal}-- to np.float64")
                print("Error Output:\n", err)
        elif (',' in colVal) and (colVal.count(',') == 1) and ('.' not in colVal):
            ### sting values of type '1235356,343'
            return np.nan
        elif any(char in strInvalidChars for char in colVal):
            ### colVal contains at least one non-numeric character
            return np.nan
        elif '.' in colVal and colVal.count('.') > 1:
            return np.nan
        elif ',' in colVal and colVal.count(',') > 1:
            return np.nan
        elif ',' in colVal and '.' in colVal:
            #### parsing cases like "1,234.0": 1 billion 234 million
            indComma = colVal.index(',')
            indPoint = colVal.index('.')
            if indPoint < indComma:
                ### str vals like "1.454,0"
                return np.nan
            if indPoint - indComma != 4:
                ### str vals like "1,45.9" (not "1,234.0")
                return np.nan
            else:
                ### deal with values "1,345.0" in millions of dollars
                tempVal = colVal.replace(',','')
                try:
                    returnValue = np.float64(tempVal)
                except TypeError as err:
                    print(f"Type Error: cannot convert string value --{colVal}-- to np.float64")
                    print("Error Output:\n", err)
                returnValue = np.uint64(returnValue * 1e6)
        else:
            ### final clause of "if(colVal)==str"
            return np.nan
    elif type(colVal) == float:
        ### Converting type float to int: if NaN, then 0 (this may be an overkill)
        if np.isnan(colVal):
            returnValue = np.uint64(0)
        else:
            try:
                returnValue = np.uint64(colVal)
            except ValueError as err:
                print(f"Value Error: cannot convert float value --{colVal}-- to np.uint64")
                print("Error Output:\n", err)
    elif type(colVal) == int:
        ### Converting type float to np.uint64: if NaN, then 0 (this may be an overkill)
        if np.isnan(colVal):
            returnValue = np.uint64(0)
        else:
            try:
                returnValue = np.uint64(colVal)
            except ValueError as err:
                print(f"Value Error: cannot convert int value --{colVal}-- to np.uint64")
                print("Error Output:\n", err)
    else:
        returnValue = np.nan

    return returnValue

def prep_bom_movie_gross(config):
    """
    This function prepares the uncompressed file from IMDB "bom.movie_gros.csv" for analysis by:
    RangeIndex: 3387 entries, 0 to 3386
    Data columns (total 5 columns):
     #   Column          Non-Null Count  Dtype  
    ---  ------          --------------  -----  
    0   title           3387 non-null   object 
    1   studio          3382 non-null   object 
    2   domestic_gross  3359 non-null   float64
    3   foreign_gross   2037 non-null   object 
    4   year            3387 non-null   int64  
    dtypes: float64(1), int64(1), object(3)
    memory usage: 132.4+ KB

    (i) removing any row with both foreign_gross and domestic_gross having NULL value

    (ii) convert a NULL or NaN value from domestic_gross or foreign_gross column to 0

    (iii) Convert data in columns "start_year" and "runtime_minutes" to type 'np.uint16'
    
    """
    strFilePath = os.path.join(config['folders']['data-csv'], config['files-bom']['csv'])
    df = pd.read_csv(strFilePath,
                     sep      = ',',
                     header   = 0,
                     encoding = 'utf-8',
                     engine   = 'python',
                     dtype    = {'year':np.uint16, 'title':str,'studio':str})
    ### (0) removing rows with no titles
    df = df.loc[df['title'].isnull()==False]

    ### (i) removing any row with both foreign_gross and domestic_gross having NULL value
    mskNullGross = ( df['domestic_gross'].isnull() & df['foreign_gross'].isnull() )
    df = df.loc[(mskNullGross==False)]

    ### (ii) Convert data to meaning types
    df['domestic_gross'] = df['domestic_gross'].apply(parse_bom_gross_revenue_values)
    df['foreign_gross']  = df['foreign_gross'].apply(parse_bom_gross_revenue_values)

    strFilePath = os.path.join(config['folders']['data-csv'], config['files-bom']['clean-csv'])
    df.to_csv(strFilePath,encoding='utf-8',index=False)

    return None

def prep_imdb_title_basics(config):
    """
    This function prepares the uncompressed file from IMDB "imdb.title.basics.csv" for analysis by:
    (i) removing any row which contains a null values except for rows with original title being NULL
    Col 0: Num NULL 0: tconst
    Col 1: Num NULL 0: primary_title
    Col 2: Num NULL 21: original_title
    Col 3: Num NULL 0: start_year
    Col 4: Num NULL 31739: runtime_minutes
    Col 5: Num NULL 5408: genres
    (ii) Convert data in columns "start_year" and "runtime_minutes" to type 'np.uint16'
    (iii) Remove all pandemic data items with "start_year" before 2020 to exclude COVID pandemic releases
    (iv) Remove all titles with run times over 6 hours; there are 77 titles in that category after NULL value
    removal
    """
    strFilePath = os.path.join(config['folders']['data-csv'], config['files-imdb']['csv']['title-base'])
    df = pd.read_csv(strFilePath,
                     sep      = ',',
                     header   = 0,
                     encoding = 'utf-8',
                     engine   = 'python')
    
    ### (i) Removing rows with NULL values
    mskRowsNullValues = (df["runtime_minutes"].isnull() | df["genres"].isnull())
    df = df.loc[(mskRowsNullValues==False)]

    ### (ii) Converting columns "runtime_minutes" and "start_year" to np.uint16
    df = df.astype({'start_year':np.uint16,'runtime_minutes':np.uint16})

    ### (iii) Revome pandemic titles
    mskPreCovidData = (df['start_year'] < config['covid-start-year'])
    df = df.loc[mskPreCovidData]

    ### (iv) Remove titles with run times below 25 min and above 6 hours (360 minutes)
    mskRuntime = ((df['runtime_minutes'] >= config['runtime-minutes-min']) & (df['runtime_minutes'] <= config['runtime-minutes-max']))
    df = df.loc[mskRuntime]

    strFilePath = os.path.join(config['folders']['data-csv'], config['files-imdb']['csv']['clean-title-base'])
    df.to_csv(strFilePath,encoding='utf-8',index=False)
    return None

def prep_imdb_title_ratings(config):
    """
    This function prepares the uncompressed file from IMDB "imdb.title.ratings.csv" for analysis by:
    (i) removing any row which contains a null values except for rows with original title being NULL
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 73856 entries, 0 to 73855
    Data columns (total 3 columns):
     #   Column         Non-Null Count  Dtype  
    ---  ------         --------------  -----  
     0   tconst         73856 non-null  object 
     1   averagerating  73856 non-null  float64
     2   numvotes       73856 non-null  int64  
    dtypes: float64(1), int64(1), object(1)
    memory usage: 1.7+ MB

    (ii) Remove rows with average rating below 1 and above 10
    (iii) Remove rows with numvotes below the minimum vote threshold
    """
    strFilePath = os.path.join(config['folders']['data-csv'], config['files-imdb']['csv']['title-rate'])
    df = pd.read_csv(strFilePath,
                     sep      = ',',
                     header   = 0,
                     encoding = 'utf-8',
                     engine   = 'python')
    
    ### (i) Removing rows with NULL values
    mskRowsNullValues = (df["tconst"].isnull() | df["averagerating"].isnull() | df["numvotes"].isnull())
    df = df.loc[(mskRowsNullValues==False)]

    ### (ii) Remove rows with average rating below 1 and above 10
    mskRating = ( (df['averagerating'] >= config['title-rating-min-value']) & \
                  (df['averagerating'] <= config['title-rating-max-value']) )
    df = df.loc[mskRating]

    ### (iii) Remove rows with number of votes below a minimum threshold
    mskNumVotes = (df['numvotes'] >= config['rating-votes-min'])
    df = df.loc[mskNumVotes]

    strFile = os.path.join(config['folders']['data-csv'], config['files-imdb']['csv']['clean-title-rate'])
    df.to_csv(strFile,encoding='utf-8',index=False)
    return None

def prepare_clean_data(config):
    """
    Umbrella function which calls functions for cleaning individual data files
    after these files are decompressed and written to the project ./data folder:
    (1) "imdb.title.basics.csv"  -- prep_imdb_title_basics(config)
    (2) "imdb.title.ratings.csv" -- prep_imdb_title_ratings(config)
    (3) "bom.movie_gross.csv"    -- prep_bom_movie_gross(config)

    Aarguments:
    config - JSON obect which contains the parameters of the project
    Return Value:
    None - the function returns no value
    Side Effect:
    Each "prep" function writes out a CSV data file with prefix "clean"
    (1) "clean.imdb.title.basics.csv"
    (2) "clean.imdb.title.ratings.csv"
    (3) "clean.bom.movie_gross.csv"
    """
    prep_imdb_title_basics(config)
    prep_imdb_title_ratings(config)
    prep_bom_movie_gross(config)

    return None

def support_function_one(example):
    """This one might read in the data from imdb and clean it"""
    return example

def support_function_two(example):
    """This function might read in and clean a different data source"""
    return example

def support_function_three(example):
    """This one might merge the above two sources and create a few new variables"""
    return example

def full_clean():
    """
    This is the one function called that will run all the support functions.
    Assumption: 
        - Your data files will be saved in a data folder and named "dirty_data.csv"
        - OR you might read directly from a few urls
        - this code is guidance, not rules
    :return: cleaned dataset to be passed to hypothesis testing and visualization modules.
    """
    dirty_data = pd.read_csv("./data/dirty_data.csv")

    cleaning_data1 = support_function_one(dirty_data)
    cleaning_data2 = support_function_two(cleaning_data1)
    cleaned_data= support_function_three(cleaning_data2)
    cleaned_data.to_csv('./data/cleaned_for_testing.csv')
    
    return cleaned_data