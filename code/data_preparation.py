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
import csv
import pandas as pd
import numpy as np

def df_print_numnullvalues_bycol(df):
    for col in range(df.shape[1]):
        intNumNull = df.iloc[:,col].isnull().sum()
        intNumNan  = df.iloc[:,col].isna().sum()
        print(f"Col {col}: Num NULL {intNumNull}: {df.columns[col]}")
        print(f"Col {col}: Num NaN  {intNumNan}: {df.columns[col]}")

    return None

def parse_one_tn_gross_revenue_value(colVal):
    """
    Functions parses strings of type '456,454,454'
    They appear as part of tn.movie_budgets.csv file

    Argument: colVal -- leading '$' char is stripped before the argument is passed 
                        to the function
    Returns np.uint64 or throw a TypeError if cannot convert to int
    """
    returnValue = colVal.split(',')
    if len(returnValue[0]) > 3 or len(returnValue[0]) == 0:
        ### $,456,456 or $93847,387,384
        return np.nan
    ### checking sub-strings with index 1 to second to last
    for splitVal in returnValue[1:-1]:
        if len(splitVal) != 3:
            ### numbers like $345,45464,34353,343
            return np.nan
    if len(returnValue[-1]) > 3 or len(returnValue) == 0:
        ### numbers like $456,456,4546 or $456,456,
        return np.nan
    try:
        returnValue = np.uint64(''.join(returnValue))
    except TypeError as err:
        print(f"Type Error: cannot convert string value --{colVal}-- to np.float64")
        print("Error Output:\n", err)
    
    return returnValue

def parse_tn_gross_revenue_values(colVal):
    """
    Function converts the string values of gross revenue (domestic and worldwide)
    into integer values from string values
    id	release_date	movie	production_budget	domestic_gross	worldwide_gross
	1	Dec 18, 2009	Avatar	$425,000,000	$760,507,625	$2,776,345,279
    """
    returnValue = 0 # initialize returnValue to zero
    # all chars from string.punctuation except comma (',') and point ('.'), dollar sign ('$')
    strInvalidChars = """!"#%&\'()*+-/:;<=>?@[\\]^_`{|}~"""
    if type(colVal) == str:
        if any(char in strInvalidChars for char in colVal):
            return np.nan
        elif len(colVal) == 0:
            ### it may mean there was no release in any foreign location
            return 0
        elif colVal == '$0':
            return 0
        elif colVal.startswith('$') and len(colVal) <= 4:
            returnValue = colVal[1:]
            if returnValue.isnumeric():
                return np.uint64(returnValue)
            else:
                return np.nan
        elif ('.' in colVal) and colVal.count('.') > 1:
            return np.nan
        elif colVal.isnumeric():
            ### the string contains only numeric data
            try:
                returnValue = np.uint64(colVal)
            except TypeError as err:
                print(f"Type Error: cannot convert string value --{colVal}-- to np.uint64")
                print("Error Output:\n", err)
        elif (not colVal.startswith('$')) and ('.' in colVal) and (',' not in colVal):
            ### string values of type '1235356.343'
            try:
                returnValue = np.float64(colVal)
                returnValue = np.uint64(returnValue)
            except TypeError as err:
                print(f"Type Error: cannot convert string value --{colVal}-- to np.float64")
                print("Error Output:\n", err)
        elif (not colVal.startswith('$')) and ('.' not in colVal) and (',' in colVal):
            ### strings like "345,343,335"
            returnValue = parse_one_tn_gross_revenue_value(colVal)
        elif (not colVal.startswith('$')) and (',' in colVal) and ('.' in colVal and colVal.count('.') == 1):
            #### parsing cases like "1,234,000,000.0"
            lstColValSplit = colVal.split('.') # this list has len 2 (substring before '.' and after '.')
            if ',' in lstColValSplit[1]:
                ### string like '434,454.454,345'
                return np.nan
            returnValue = parse_one_tn_gross_revenue_value(lstColValSplit[0])
        elif colVal.startswith('$') and (',' in colVal) and ('.' in colVal and colVal.count('.') == 1):
            colVal = colVal[1:]
            lstColValSplit = colVal.split('.') # this list has len 2 (substring before '.' and after '.')
            if ',' in lstColValSplit[1]:
                ### string like '434,454.454,345'
                return np.nan
            returnValue = parse_one_tn_gross_revenue_value(lstColValSplit[0])
        elif colVal.startswith('$') and (',' in colVal) and ('.' not in colVal):
            colVal = colVal[1:]
            returnValue = parse_one_tn_gross_revenue_value(colVal)
        else:
            ### final clause of "if(colVal)==str"
            return np.nan
    ### tn.movie_budgets.csv is loaded as str type for revenue (no need to parse for num types)
    # elif type(colVal) == float:
    #     ### Converting type float to int: if NaN, then 0 (this may be an overkill)
    #     if np.isnan(colVal):
    #         returnValue = np.uint64(0)
    #     else:
    #         try:
    #             returnValue = np.uint64(colVal)
    #         except ValueError as err:
    #             print(f"Value Error: cannot convert float value --{colVal}-- to np.uint64")
    #             print("Error Output:\n", err)
    # elif type(colVal) == int:
    #     ### Converting type float to np.uint64: if NaN, then 0 (this may be an overkill)
    #     if np.isnan(colVal):
    #         returnValue = np.uint64(0)
    #     else:
    #         try:
    #             returnValue = np.uint64(colVal)
    #         except ValueError as err:
    #             print(f"Value Error: cannot convert int value --{colVal}-- to np.uint64")
    #             print("Error Output:\n", err)
    else:
        returnValue = np.nan

    return returnValue

def prep_tn_movie_budgets(config,fileLocation=''):
    """
    This function prepares the uncompressed file from IMDB "tn.movie_budgets.csv" for analysis by:
    RangeIndex: 5782 entries, 0 to 5781
    Data columns (total 6 columns):
    #   Column             Non-Null Count  Dtype 
    ---  ------             --------------  ----- 
    0   id                 5782 non-null   int64 
    1   release_date       5782 non-null   object
    2   movie              5782 non-null   object
    3   production_budget  5782 non-null   object
    4   domestic_gross     5782 non-null   object
    5   worldwide_gross    5782 non-null   object
    dtypes: int64(1), object(5)
    
    id	release_date	movie	production_budget	domestic_gross	worldwide_gross
	1	Dec 18, 2009	Avatar	$425,000,000	$760,507,625	$2,776,345,279
    
    memory usage: 271.2+ KB
    (i) Insert column 'release_year'

    (ii) Drop all rows with release year < 2010 and above 2019

    (iii) Convert domestic_gross and worldwide_gross to integers
    """
    if len(fileLocation) == 0:
        fileLocation = os.path.join(config['folders']['data-csv'], config['files-tn']['csv'])
    else:
        if not os.path.exists(fileLocation):
            raise FileNotFoundError
    df = pd.read_csv(fileLocation,
                     sep      = ',',
                     header   = 0,
                     encoding = 'utf-8', # char set for this file is UTF-8 per Notepad++
                     engine   = 'python',
                     quotechar= '"', # quote char encloses the field where separator (',') char is present
                     quoting  = csv.QUOTE_MINIMAL  # quote char only around data with separator char (',')           
         )
    ### (0) drop colums 'id', 'production_budget', rename 'movie' to 'title'
    df = df.drop(columns=['id','production_budget'])
    df = df.rename(columns={'movie':'title'})
    
    ### (i) Deriving column 'release_year'
    df['year'] = df['release_date'].apply(lambda d: np.uint16(d[-4:]))
    df = df.drop(columns=['release_date'])

    ### (ii) Keeping titles in valid release year range
    mskValidYears = ( (df['year'] >= config['title-release-year-min']) & \
                      (df['year'] <= config['title-release-year-max']) )
    df = df.loc[mskValidYears]

    ### (iii) Convert domestic and worldwide gross to meaningful types, remove np.nan rows
    ### and convert to np.uint64
    df['domestic_gross']   = df['domestic_gross'].apply(parse_tn_gross_revenue_values)
    df['worldwide_gross']  = df['worldwide_gross'].apply(parse_tn_gross_revenue_values)
    mskNullGross = ( (df['domestic_gross'].isnull()) | (df['worldwide_gross'].isnull()) )
    df = df.loc[mskNullGross==False]
    df = df.astype({'domestic_gross':np.uint64, 'worldwide_gross':np.uint64})

    ### (iv) Derive 'foreign_gross' and drop 'worldwide_gross'
    df['foreign_gross'] = df['worldwide_gross'].sub(df['domestic_gross'])
    df = df.drop(columns=['worldwide_gross'])

    ### (v) Re-arrange columns
    df = df.loc[:,['title','year','domestic_gross','foreign_gross']]

    strFilePath = os.path.join(config['folders']['data-csv'], config['files-tn']['clean-csv'])
    df.to_csv(strFilePath,encoding='utf-8',index=False)

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
    elif type(colVal) in [float, np.float, np.float16,np.float32,np.float64]:
        ### Converting type float to int: if NaN, then 0 (corresponds to empty field as (,,))
        if np.isnan(colVal):
            returnValue = np.uint64(0)
        else:
            try:
                returnValue = np.uint64(colVal)
            except ValueError as err:
                print(f"Value Error: cannot convert float value --{colVal}-- to np.uint64")
                print("Error Output:\n", err)
    elif type(colVal) in [int,np.int,np.int32,np.int64,np.uint32,np.uint64]:
        ### Converting type int to np.uint64: if NaN, then 0 (this may be an overkill)
        ### int or np.int types cannot be NaN since np.nan is only float.
        try:
            returnValue = np.uint64(colVal)
        except ValueError as err:
            print(f"Value Error: cannot convert int value --{colVal}-- to np.uint64")
            print("Error Output:\n", err)
    else:
        returnValue = colVal

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
    dctColDataTypes = {'title':str,'studio':str,'year':np.uint16,'domestic_gross':np.float64,'foreign_gross':str}
    df = pd.read_csv(strFilePath,
                     sep      = ',',
                     header   = 0,
                     encoding = 'utf-8',
                     engine   = 'python',        
                     quotechar= '"', # quote char encloses the field where separator (',') char is present
                     quoting  = csv.QUOTE_MINIMAL,    # quote char present in field only where the separator char (',') is present              
                     dtype    = dctColDataTypes)
    ### (0) Drop column 'studio' removing rows with no titles and no release year
    df = df.drop(columns=['studio'])
    mskInvalidRows = ( df['title'].isnull() | df['year'].isnull() )
    df = df.loc[mskInvalidRows==False]

    ### (i) removing rows with release year out of bounds
    mskYear = (df['year']>=config['title-release-year-min']) & (df['year']<=config['title-release-year-max'])

     ### (ii) Convert data to meaningful values
    df['domestic_gross'] = df['domestic_gross'].apply(parse_bom_gross_revenue_values)
    df['foreign_gross']  = df['foreign_gross'].apply(parse_bom_gross_revenue_values)

    ### (iii) removing titles with NaN revenue figures: after parsing all revenue should be 
    ###       either a valid number or NaN. NaN's should be removed.
    mskInvalidGross = ( df['domestic_gross'].isnull() | df['foreign_gross'].isnull() )
    df = df.loc[mskInvalidGross==False]

    ### (iv) Re-arrange columns and save
    df = df.loc[:,['title','year','domestic_gross','foreign_gross']]
    strFilePath = os.path.join(config['folders']['data-csv'], config['files-bom']['clean-csv'])
    df.to_csv(strFilePath,encoding='utf-8',index=False,quotechar='"',quoting=csv.QUOTE_MINIMAL)

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
    dctColDataTypes = {'tconst': str,'primary_title':str,'original_title': str,
                       'start_year':np.float32,'runtime_minutes': np.float32, 'genres': str}
    df = pd.read_csv(strFilePath,
                     sep      = ',',
                     header   = 0,
                     encoding = 'utf-8',
                     engine   = 'python',
                     quotechar= '"', # quote char encloses all field
                     quoting  = csv.QUOTE_ALL,   # quote char present in all fields (aka csv.QUOTE_ALL)             
                     dtype=dctColDataTypes)
    ### (0) Drop 'original_title' and stardardize column names
    df = df.drop(columns=['original_title'])
    df = df.rename(columns={'primary_title': 'title','start_year':'year'}) 
    
    ### (i) Removing rows with NULL values
    mskRowsNullValues = (df['tconst'].isnull() | df['title'].isnull() | df['year'].isnull() | \
                        df['runtime_minutes'].isnull() | df['genres'].isnull())
    df = df.loc[(mskRowsNullValues==False)]

     ### (ii) Revome titles outside of release year boundaries
    mskPreCovidData = ((df['year'] >= config['title-release-year-min']) & \
                       (df['year'] <= config['title-release-year-max']))
    df = df.loc[mskPreCovidData]

    ### (iv) Remove titles with run times below 25 min and above 6 hours (360 minutes)
    mskRuntime = ((df['runtime_minutes'] >= config['runtime-minutes-min']) & \
                  (df['runtime_minutes'] <= config['runtime-minutes-max']))
    df = df.loc[mskRuntime]

    ### (v) Convert runtime_minutes and 'start_year' to np.uint16
    df = df.astype({'year':np.uint16, 'runtime_minutes':np.uint16})

    strFilePath = os.path.join(config['folders']['data-csv'], config['files-imdb']['csv']['clean-title-base'])
    df.to_csv(strFilePath,encoding='utf-8',index=False,quotechar='"', quoting=csv.QUOTE_MINIMAL)
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
    dctColDataTypes = {'tconst': str,'averagerating':np.float64,'numvotes': np.float64}
    df = pd.read_csv(strFilePath,
                     sep      = ',',
                     header   = 0,
                     encoding = 'utf-8',
                     engine   = 'python',
                     dtype    =dctColDataTypes,
                     quotechar='"',
                     quoting  = csv.QUOTE_ALL)
    
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

    ### (iv) Rename 'averagerating' to 'rating', Convert 'averagerating' and 'numvotes' to float and int, respetively
    df = df.rename(columns={'averagerating':'rating'})
    df = df.astype({'rating':np.float32,'numvotes':np.uint64})

    strFile = os.path.join(config['folders']['data-csv'], config['files-imdb']['csv']['clean-title-rate'])
    df.to_csv(strFile,encoding='utf-8',index=False,quotechar='"',quoting=csv.QUOTE_MINIMAL)
    return None

def prepare_clean_data(config):
    """
    Umbrella function which calls functions for cleaning individual data files
    after these files are decompressed and written to the project ./data folder:
    (1) "imdb.title.basics.csv"  -- prep_imdb_title_basics(config)
    (2) "imdb.title.ratings.csv" -- prep_imdb_title_ratings(config)
    (3) "bom.movie_gross.csv"    -- prep_bom_movie_gross(config)
    (4) "tn.movie_budgets.csv"   -- prep_tn_movie_budgets(config)

    Aarguments:
    config - JSON obect which contains the parameters of the project
    Return Value:
    None - the function returns no value
    Side Effect:
    Each "prep" function writes out a CSV data file with prefix "clean"
    (1) "clean.imdb.title.basics.csv"
    (2) "clean.imdb.title.ratings.csv"
    (3) "clean.bom.movie_gross.csv"
    (4) "clean.tn.movie_budgets.csv"
    """
    prep_imdb_title_basics(config)
    prep_imdb_title_ratings(config)
    prep_bom_movie_gross(config)
    prep_tn_movie_budgets(config)

    return None

def load_clean_imdb_title_basics(config):
    """
    Load to dataframe from file './data/clean.imdb.title.basics.csv'
    """
    strFileLocation = os.path.join(config['folders']['data-csv'], config['files-imdb']['csv']['clean-title-base'])
    df = pd.read_csv(
        strFileLocation,
        encoding='utf-8',
        sep      = ',',
        header   = 0,
        engine   = 'python',
        dtype    = {'tconst':str,
                    'title':str,
                    'year':np.uint16,
                    'runtime_minutes':np.uint16,
                    'genres':str},
        quotechar= '"', # quote char encloses the field where separator (',') char is present
        quoting  = 0    # quote char present in field only where the separator char (',') is present              
    )
    return df

def load_clean_imdb_title_ratings(config):
    """
    Load to dataframe from file './data/clean.imdb.title.ratings.csv'
    """
    strFileLocation = os.path.join(config['folders']['data-csv'], config['files-imdb']['csv']['clean-title-rate'])
    df = pd.read_csv(
        strFileLocation,
        encoding='utf-8',
        sep      = ',',
        header   = 0,
        engine   = 'python',
        quotechar= '"',
        quoting= 0,
        dtype    = {'tconst':str,
                    'rating':np.float64,
                    'numvotes':np.uint64}
    )
    return df

def load_clean_bom_movie_gross(config):
    """
    Load to dataframe from file './data/clean.bom.movie_gross.csv'
    """
    strFileLocation = os.path.join(config['folders']['data-csv'], config['files-bom']['clean-csv'])
    df = pd.read_csv(strFileLocation,encoding='utf-8',sep = ',',
            header = 0, engine = 'python',quotechar= '"',quoting = 0,
            dtype = {'title':str, 'year':np.uint16, 'domestic_gross':np.uint64,'foreign_gross':np.uint64})
    return df

def load_clean_tn_movie_gross(config):
    """
    Load TN movie gross revenue file from project root folder.
    File location './data/clean.tn.budget_gross.csv'
    """    
    strFileLocation = os.path.join(config['folders']['data-csv'], config['files-tn']['clean-csv'])
    df = pd.read_csv(strFileLocation, encoding='utf-8', sep = ',',
            header = 0, engine = 'python', quotechar= '"', quoting = 0,
            dtype = {'release_year':np.uint16,'movie':str,'domestic_gross':np.uint64,'foreign_gross':np.uint64})
    return df

def combine_clean_bom_and_tn_revenue_data(config):
    """
    Function combines clean BOM and TN datasets to generate a more comprehensive set of revenue data from both sources.

    Argument:
        'config': used for constants to file folders and file names
    
    Post merge file:
    --------------------
    title year_bom domestic_gross_bom foreign_gross_bom year_tn domestic_gross_tn foreign_gross_tn
    0 #Horror NaN NaN NaN 2015.0 0.0 0.0
    1 '71 2015.0 1300000.0 355000.0 NaN	NaN	NaN
    2 1,000 Times Good Night 2014.0 53900.0 0.0 NaN NaN NaN
    --------------------
    """

    ### Load Clean Data from the Drive
    dfB = load_clean_bom_movie_gross(config)
    dfT = load_clean_tn_movie_gross(config)

    ### Derive a combined list of titles with unique entries as a data frame
    dfB.title = dfB.title.apply(str.upper)
    dfT.title = dfT.title.apply(str.upper)
    dfTitles = pd.concat([dfB.title, dfT.title], axis=0).reset_index()
    dfTitles.drop(columns=['index'], inplace=True)
    dfTitles.columns = ['title']
    dfTitles.sort_values('title', inplace=True)
    srUniqueTitles = dfTitles['title'].unique()
    dfUniqueTitles = pd.DataFrame(srUniqueTitles,columns=['title'])

    ### Merge dfUniqueTitles with data in dfT and dfB
    dfMerged = pd.merge(dfUniqueTitles, dfB, how='left',on='title', suffixes=('_bomtn', '_bom'))
    dfMerged = pd.merge(dfMerged, dfT, how='left', on = 'title', suffixes=('_bom','_tn'))

    ### Apply row-level functions to choose values for columns 'year', 'domestic_gross', and 'foreign_gross'
    dfMerged = dfMerged.apply(combine_clean_bom_and_tn_revenue_select_year, axis=1)
    dfMerged = dfMerged.apply(combine_clean_bom_and_tn_revenue_select_domestic_gross, axis=1)
    dfMerged = dfMerged.apply(combine_clean_bom_and_tn_revenue_select_foreign_gross, axis=1)

    ### Remove invalid rows: any row with a NaN value; convert 'year', 'domestic_gross', and 'foreign_gross' to int
    dfMerged = dfMerged.astype({'year':np.uint16,'domestic_gross':np.uint64,'foreign_gross':np.uint64})

    return dfMerged

def combine_clean_bom_and_tn_revenue_select_year(row):
    """
    Select year from column values reprenting TN and BOM ('year_bom', 'year_tn')
    """
    if np.isnan(row.year_bom) and np.isnan(row.year_tn):
        row['year'] = np.nan
    elif np.isnan(row.year_bom) and not np.isnan(row.year_tn):
        row['year'] = row.year_tn
    elif not np.isnan(row.year_bom) and np.isnan(row.year_tn):
        row['year'] = row.year_bom
    else:
        if row.year_bom == row.year_tn:
            row['year'] = row.year_bom
        else:
            row['year'] = row.year_bom
    row = row.drop(labels=['year_bom','year_tn'])
    return row

def combine_clean_bom_and_tn_revenue_select_domestic_gross(row):
    """
    Select domestic gross value from column values reprenting TN and BOM ('domestic_gross_bom', 'domestic_gross_tn')
    """
    if np.isnan(row.domestic_gross_bom) and np.isnan(row.domestic_gross_tn):
        row['domestic_gross'] = np.nan
    elif np.isnan(row.domestic_gross_bom) and not np.isnan(row.domestic_gross_tn):
        row['domestic_gross'] = row.domestic_gross_tn
    elif not np.isnan(row.domestic_gross_bom) and np.isnan(row.domestic_gross_tn):
        row['domestic_gross'] = row.domestic_gross_bom
    else:
        row['domestic_gross'] = max(row.domestic_gross_bom,row.domestic_gross_tn)
    row = row.drop(labels=['domestic_gross_bom','domestic_gross_tn'])
    return row

def combine_clean_bom_and_tn_revenue_select_foreign_gross(row):
    """
    Select foreign gross value from column values reprenting TN and BOM ('foreign_gross_bom', 'foreign_gross_tn')
    """
    if np.isnan(row.foreign_gross_bom) and np.isnan(row.foreign_gross_tn):
        row['foreign_gross'] = np.nan
    elif np.isnan(row.foreign_gross_bom) and not np.isnan(row.foreign_gross_tn):
        row['foreign_gross'] = row.foreign_gross_tn
    elif not np.isnan(row.foreign_gross_bom) and np.isnan(row.foreign_gross_tn):
        row['foreign_gross'] = row.foreign_gross_bom
    else:
        row['foreign_gross'] = max(row.foreign_gross_bom,row.foreign_gross_tn)
    row = row.drop(labels=['foreign_gross_bom','foreign_gross_tn'])
    return row    


def merge_clean_data(config):
    """
    This file loads all clean data into DataFrames using utility functions and 
    merges them into working dataset using pandas merge utility
    """
    ### dfTitles: columns 'tconst', 'title', 'year', 'runtime_minutes', 'genres'
    ### dfRating: colums 'tconst','rating','numvotes'
    ### dfRevenue: columns 'title' (CAPS), 'year','domestic_gross', 'foreign_gross'
    dfTitles = load_clean_imdb_title_basics(config)
    dfRating = load_clean_imdb_title_ratings(config)
    dfRevenue = combine_clean_bom_and_tn_revenue_data(config)
    dfRevenue = dfRevenue.drop(columns=['year'])

    ### Merge title, rating, and revenue data
    df = pd.merge(dfTitles, dfRating, how='left', on='tconst')
    df['title'] = df['title'].apply(str.upper)
    df = pd.merge(df, dfRevenue, how='left', on='title')
    
    ### write out merged data set
    strFilePath = os.path.join(config['folders']['data-csv'], config['files-merge']['clean-csv'])
    df.to_csv(strFilePath,encoding='utf-8',index=False,quotechar='"', quoting=csv.QUOTE_MINIMAL)
    return None

def load_merged_clean_data(config):
    """
    Load merged data set generated by function 'merge_clean_data(config):
    File columns: 'tconst', 'title' (CAPS), 'year', 'runtime_minutes', 'genres'
                  'rating', 'numvotes', 'domestic_gross', 'foreign_gross'.
    """
    fileLocation = os.path.join(config['folders']['data-csv'], config['files-merge']['clean-csv'])
    df = pd.read_csv(fileLocation,encoding='utf-8',engine='python',quotechar= '"',quoting = 0,
                     dtype={'tconst':str,'title':str,'year':np.uint16,'runtime_minutes':np.uint16,'genres':str,
                            'rating':np.float16,'numvotes':np.float32,'domestic_gross':np.float64,'foreign_gross':np.float64})
    return df

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