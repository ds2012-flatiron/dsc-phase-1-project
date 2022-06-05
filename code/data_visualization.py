"""
This library contains visualization code which is primarily based on the 
merged dataset produced by function "merge_clean_data(config)". The function
generates the file "clean.merge.title.rating.revenue.csv"
Columns:
    'tconst'
    'title' (CAPS)
    'year' - release year
    'runtime_minutes' - total runtime length in minutes;
    'genres' - title assigned genre (may contain multi-genre entry)
    'domestic_gross' - revenue in the US market;
    'foreign_gross' - revenue in the entire foreign gross revenue;
"""

from cmath import isnan
import os
import csv
from tracemalloc import stop
from turtle import color, right
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import data_preparation as dataprep

def bar_chart_top_genres_by_revenue(config, maxgenres = 10):
    """
    """
    if maxgenres > config['charts']['bar-number-upperbound']:
        raise ValueError(f'Argument "maxgenres" {maxgenres} exceeds upper bound value of {config["charts"]["bar-number-upperbound"]}')

    ### Load merged data
    df = dataprep.load_merged_clean_data(config)
    dfD = df.loc[(np.isnan(df['domestic_gross'])==False), ['tconst','title','year','genres','domestic_gross']]
    dfF = df.loc[(np.isnan(df['foreign_gross'])==False),  ['tconst','title','year','genres','foreign_gross']]

    ### Get sums by genres
    srsD=dfD.groupby('genres')['domestic_gross'].sum().sort_values(ascending=False).iloc[range(maxgenres)]
    srsF=dfF.groupby('genres')['foreign_gross'].sum().sort_values(ascending=False).iloc[range(maxgenres)]
    fltRightXLimit = max(srsD.div(1e9).max(),srsF.div(1e9).max()) + 1

    ### Generage plot
    fig, ax = plt.subplots(nrows=2,ncols=1,figsize=(10,8))
    p0=ax[0].barh(srsD.index, srsD.div(1e9).values)
    ax[0].invert_yaxis()
    ax[0].bar_label(p0,label_type='edge',fmt='%.1f')
    ax[0].set_title(f'2010-2019: Top {str(maxgenres)} Genres by Domestic Gross ($ Billion)')
    ax[0].set_xlim(right=fltRightXLimit)

    p1=ax[1].barh(srsF.index, srsF.div(1e9).values)
    ax[1].invert_yaxis()
    ax[1].bar_label(p1,label_type='edge',fmt='%.1f')
    ax[1].set_title(f'2010-2019: Top {str(maxgenres)} Genres by Foreign Gross ($ Billion)')
    ax[1].set_xlim(right=fltRightXLimit)

    plt.show()

    return None

def bar_chart_top_genres_by_avgrevenue_pertitle(config, maxgenres = 10):
    """
    """
    if maxgenres > config['charts']['bar-number-upperbound']:
        raise ValueError(f'Argument "maxgenres" {maxgenres} exceeds upper bound value of {config["charts"]["bar-number-upperbound"]}')

    ### Load merged data
    df = dataprep.load_merged_clean_data(config)
    dfD = df.loc[(np.isnan(df['domestic_gross'])==False), ['tconst','title','year','genres','domestic_gross']]
    dfF = df.loc[(np.isnan(df['foreign_gross'])==False),  ['tconst','title','year','genres','foreign_gross']]

    ### Get sums by genres
    dfD= dfD.groupby('genres')['domestic_gross'].agg(['mean','std','count']).reset_index()
    dfD= dfD.loc[dfD['count'] >= config['charts']['min-titles-per-genre']] \
            .sort_values('mean',ascending=False).iloc[range(maxgenres)] 
    dfF= dfF.groupby('genres')['foreign_gross'].agg(['mean','std','count']).reset_index()
    dfF= dfF.loc[dfF['count'] >= config['charts']['min-titles-per-genre']] \
            .sort_values('mean',ascending=False).iloc[range(maxgenres)]
 
    ### Generage plot
    fig, ax = plt.subplots(nrows=2,ncols=1,figsize=(10,8))
    fltRightXLimit = max(dfD['mean'].div(1e6).max(),dfF['mean'].div(1e6).max()) + 150

    ### Row 1: domestic gross
    df = dfD.copy()
    errGrossRevenue = df['std'].div(np.sqrt(df['count'])).div(1e6)
    zipTriple = zip(df['mean'].div(1e6).to_list(),errGrossRevenue.to_list(),df['count'])
    lstBarLabels = [f'{m:.0f}±{e:.0f}|title cnt: {n}' for (m,e,n) in zipTriple]

    p0=ax[0].barh(df['genres'], df['mean'].div(1e6).values, xerr=errGrossRevenue)
    ax[0].invert_yaxis()
    ax[0].bar_label(p0,labels=lstBarLabels,label_type='edge',fmt='%.0f',color='m')
    ax[0].set_title(f'2010-2019: Top {str(maxgenres)} Genres by Domestic Avg Gross per Title ($ Million)')
    ax[0].set_xlim(right=fltRightXLimit)

    ### Row 2: foreign gross
    df = dfF.copy()
    errGrossRevenue = df['std'].div(np.sqrt(df['count'])).div(1e6)
    zipTriple = zip(df['mean'].div(1e6).to_list(),errGrossRevenue.to_list(),df['count'])
    lstBarLabels = [f'{m:.0f}±{e:.0f}|title cnt: {n}' for (m,e,n) in zipTriple]

    p1=ax[1].barh(df['genres'], df['mean'].div(1e6).values, xerr=errGrossRevenue)
    ax[1].invert_yaxis()
    ax[1].bar_label(p1,labels=lstBarLabels,label_type='edge',fmt='%.0f',color='m')
    ax[1].set_title(f'2010-2019: Top {str(maxgenres)} Genres by Foreign Avg Gross per Title ($ Million)')
    ax[1].set_xlim(right=fltRightXLimit)

    plt.show()

    return None

def bar_chart_top_genres_by_weightedavg_title_rating(config, maxgenres = 15):
    """
    Compute weighted average title rating (weighted by numvotes) of each genre, weighted average title standard deviation
    of each genre. Contruct a horizontal bar chart 
    """
    if maxgenres > config['charts']['bar-number-upperbound']:
        raise ValueError(f'Argument "maxgenres" {maxgenres} exceeds upper bound value of {config["charts"]["bar-number-upperbound"]}')

    ### Load merged data
    df = dataprep.load_merged_clean_data(config)
    df = df.loc[(np.isnan(df['rating'])==False), ['tconst','title','genres','rating','numvotes']]
    df = df.loc[df['numvotes']>=config['rating-numvotes-pertitle-min']].copy()

    ### Compute weighted average of title ratings per genre
    df['rating_times_numvotes'] = df['rating'].mul(df['numvotes'])
    df['ratingsqrd_times_numvotes'] = (df['rating'].mul(df['rating'])).mul(df['numvotes'])
    dfGroupByGenre = df.groupby('genres')[['ratingsqrd_times_numvotes','rating_times_numvotes','numvotes']] \
                       .agg(np.sum).reset_index()
    dfGroupByGenreTitleCounts = df.groupby('genres')['tconst'].count().reset_index()
    dfGroupByGenreTitleCounts.rename(columns={'tconst':'genre_numtitles'}, inplace=True)

    dfGroupByGenreTitleRating = df.groupby('genres')['rating'].agg(['mean','std']).reset_index()
    dfGroupByGenreTitleRating.rename(columns={'mean':'rating_mean','std':'rating_std'}, inplace=True)

    dfGroupByGenre = pd.merge(dfGroupByGenre,dfGroupByGenreTitleCounts,on='genres')
    dfGroupByGenre = pd.merge(dfGroupByGenre,dfGroupByGenreTitleRating,on='genres')
    dfGroupByGenre = dfGroupByGenre.loc[dfGroupByGenre['genre_numtitles']>=config['titles-per-genre-min']]
    ### Delete df to release memory
    del df
    
    ### Compute weigthed (by numvotes) average rating
    dfGroupByGenre['wavgrating']     = dfGroupByGenre['rating_times_numvotes'].div(dfGroupByGenre['numvotes'])
    ### Compute first and second terms of weighted average standard deviation
    dfGroupByGenre['rating_wavgstdev_term1'] = dfGroupByGenre['ratingsqrd_times_numvotes'].div(dfGroupByGenre['numvotes'])
    dfGroupByGenre['rating_wavgstdev_term2'] = dfGroupByGenre['wavgrating'].mul(dfGroupByGenre['wavgrating'])
    dfGroupByGenre = dfGroupByGenre.rename({'rating_times_numvotes':'genresum_rating_times_numvotes',
                                            'ratingsqrd_times_numvotes':'genresum_ratingsqrd_times_numvotes',
                                            'numvotes':'genresum_numvotes'}, axis=1)
    dfGroupByGenre['rating_wavgstdev'] = dfGroupByGenre['rating_wavgstdev_term1'].subtract(dfGroupByGenre['rating_wavgstdev_term2'])
    dfGroupByGenre['rating_wavgstdev'] = dfGroupByGenre['rating_wavgstdev'].apply(np.sqrt)
 
    ### rename to df for ease of reference
    df = dfGroupByGenre.copy()
    del dfGroupByGenre
 
    ### Generage plot
    fig, ax = plt.subplots(nrows=2,ncols=1,figsize=(12,10))
    fltRightXLimit = max(df['wavgrating'].to_list()) + 3

    ### Axis 0: Plot rating weighted by numvotes
    df0 = df.sort_values('wavgrating',ascending=False).iloc[range(maxgenres)]
    errGrossRevenue = df0['rating_wavgstdev']
    zipTriple = zip(df0['wavgrating'].to_list(),errGrossRevenue.to_list(),df0['genresum_numvotes'])
    lstBarLabels = [f'{m:0.1f}±{e:0.2f} | votes: {n/1e3:0.0f}e3' for (m,e,n) in zipTriple]
    p0=ax[0].barh(df0['genres'], df0['wavgrating'].values, xerr=errGrossRevenue)
    ax[0].invert_yaxis()
    ax[0].bar_label(p0,labels=lstBarLabels,label_type='edge',color='m')
    ax[0].set_title(f'2010-2019: Top {str(maxgenres)} Genres by Weighted Avg Title Rating')
    ax[0].set_xlim(right=fltRightXLimit)

    ### Axis 1: Plot average rating across titles in a genre
    df1 = df.sort_values('rating_mean',ascending=False).iloc[range(maxgenres)]
    zipTriple = zip(df1['rating_mean'].to_list(),df1['rating_std'].to_list(),df1['genresum_numvotes'])
    lstBarLabels = [f'{m:0.1f}±{e:0.2f} | votes: {n/1e3:0.0f}e3' for (m,e,n) in zipTriple]
    p1=ax[1].barh(df1['genres'], df1['rating_mean'].values, xerr=df1['rating_std'])
    ax[1].invert_yaxis()
    ax[1].bar_label(p1,labels=lstBarLabels,label_type='edge',color='m')
    ax[1].set_title(f'2010-2019: Top {str(maxgenres)} Genres by Avg Title Rating')
    ax[1].set_xlim(right=fltRightXLimit)

    plt.show()

    return None

def barchart_scatterplot_title_rating_and_revenue(config):
    """
    """
    ### Load merged data
    df = dataprep.load_merged_clean_data(config)
    df = df.loc[ :, ['tconst','title','genres','rating','numvotes','domestic_gross','foreign_gross']]
    df['worldwide_gross'] = df['domestic_gross'].add(df['foreign_gross'], fill_value=0)
    mskValidGross = (df['worldwide_gross'].isna()==False)
    mskValidRating = (df['rating'].isna()==False)
    mskValidNumvotes = ( (df['numvotes'].isna() == False) & (df['numvotes'] >= config['rating-numvotes-pertitle-min']) )
    ### INCLUDED for Testing Purposes and Sensitivity Analysis
    ### mskValidNumvotes = ( (df['numvotes'].isna() == False) & (df['numvotes'] >= 0) )

    mskValidRevenue = ( (df['worldwide_gross'] > 0) & (df['worldwide_gross'] < 100e9))
    mskValidRows = (mskValidGross & mskValidRating & mskValidNumvotes & mskValidRevenue)
    df = df.loc[mskValidRows]
    dfTitleLevel = df
    
    ### GENERATE PLOT: Title Level Data
    fig, ax = plt.subplots(nrows=2,ncols=1,figsize=(10,8))

    ### Axis 0: BAR CHART: Title Avg Revenue across Rating Intervals
    lstIntervalSet = [[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9]]
    dctAvgRatingByInterval = compute_revenue_mean_stdev_for_rating_interval(dfTitleLevel,lstIntervalSet,\
        'rating','worldwide_gross',1e6)

    lstBarXTicks = list(map(lambda lstInt: sum(lstInt)/len(lstInt), lstIntervalSet))
    zipTuple = zip(dctAvgRatingByInterval['avg'],dctAvgRatingByInterval['std'])
    lstBarLabels = [f'{m:0.1f}±{e:0.1f}' for (m,e) in zipTuple]
    p0=ax[0].bar(lstBarXTicks, dctAvgRatingByInterval['avg'], yerr=dctAvgRatingByInterval['std'])
    ax[0].bar_label(p0,labels=lstBarLabels,label_type='edge',color='m')
    ax[0].set_title(f'2010-2019: Title Average Revenue By Rating Interval')
    ax[0].set_ylim(top=np.max(dctAvgRatingByInterval['avg'])+75)
    ax[0].set_ylabel('Revenue ($mm)')

    ### Axis 1: Scatter Plot: Title Level: x-axis - title rating,y-axis - title worldwide gross
    p1=ax[1].scatter(dfTitleLevel['rating'], dfTitleLevel['worldwide_gross'].div(1e6),s=10)
    ax[1].set_xlabel('Title Rating')
    ax[1].set_ylabel('Revenue ($mm)')
    ax[1].set_title(f'2010-2019: Title Rating v Title Revenue')
    ax[1].set_xlim(left=lstIntervalSet[0][0],right=lstIntervalSet[-1][1])

    plt.show()
    ### END OF PLOT

    return None

def barchart_scatterplot_genre_rating_and_revenue(config):
    """
    """
    ### Load merged data
    df = dataprep.load_merged_clean_data(config)
    df = df.loc[ :, ['tconst','title','genres','rating','numvotes','domestic_gross','foreign_gross']]
    df['worldwide_gross'] = df['domestic_gross'].add(df['foreign_gross'], fill_value=0)
    mskValidGross = (df['worldwide_gross'].isna()==False)
    mskValidRating = (df['rating'].isna()==False)
    mskValidNumvotes = ( (df['numvotes'].isna() == False) & (df['numvotes'] >= config['rating-numvotes-pertitle-min']) )
    ### INCLUDED for Testing Purposes and Sensitivity Analysis
    ### mskValidNumvotes = ( (df['numvotes'].isna() == False) & (df['numvotes'] >= 0) )

    mskValidRevenue = (df['worldwide_gross'] > 0)
    mskValidRows = (mskValidGross & mskValidRating & mskValidNumvotes & mskValidRevenue)
    df = df.loc[mskValidRows]
    
    ### Compute weighted average of title ratings per genre
    df['rating_times_numvotes'] = df['rating'].mul(df['numvotes'])
    dfGroupByGenre = df.groupby('genres')[['rating_times_numvotes','numvotes','worldwide_gross','domestic_gross','foreign_gross']] \
                       .agg(np.sum).reset_index()
    dfGroupByGenreTitleCounts = df.groupby('genres')['tconst'].count().reset_index()
    dfGroupByGenreTitleCounts.rename(columns={'tconst':'genre_numtitles'}, inplace=True)

    dfGroupByGenreTitleRating = df.groupby('genres')['rating'].agg(['mean']).reset_index()
    dfGroupByGenreTitleRating.rename(columns={'mean':'rating_mean'}, inplace=True)

    dfGroupByGenre = pd.merge(dfGroupByGenre,dfGroupByGenreTitleCounts,how='inner',on='genres')
    dfGroupByGenre = pd.merge(dfGroupByGenre,dfGroupByGenreTitleRating,how='inner',on='genres')
    dfGroupByGenre = dfGroupByGenre.loc[dfGroupByGenre['genre_numtitles']>=config['titles-per-genre-min']]
    ### Delete df to release memory
    del df
    
    ### Compute weigthed (by numvotes) average rating
    dfGroupByGenre['wavgrating'] = dfGroupByGenre['rating_times_numvotes'].div(dfGroupByGenre['numvotes'])
    dfGenreLevel = dfGroupByGenre
    del dfGroupByGenre

    ### GENERATE PLOT: Genre Level Data
    fig, ax = plt.subplots(nrows=2,ncols=1,figsize=(10,8))

    ### Axis 0: BAR CHART: Genre Avg Revenue across Weighted Avg Ratings 
    ###                    X-Axis: Rating Intervals Defined by Genre Weighted Avg Rating
    ###                    Y-Axis: Average Genre Revenue
    lstIntervalSet = [[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9]]
    dctAvgRatingByInterval = compute_revenue_mean_stdev_for_rating_interval(dfGenreLevel,lstIntervalSet, \
        'wavgrating','worldwide_gross',1e9)
    dctAvgRatingByInterval['avg'] = [n if not np.isnan(n) else 0 for n in dctAvgRatingByInterval['avg']]
    dctAvgRatingByInterval['std'] = [n if not np.isnan(n) else 0 for n in dctAvgRatingByInterval['std']]

    lstBarXTicks = list(map(lambda lstInt: sum(lstInt)/len(lstInt), lstIntervalSet))
    zipTuple = zip(dctAvgRatingByInterval['avg'],dctAvgRatingByInterval['std'])
    lstBarLabels = [f'{m:0.2f}±{e:0.2f}' if not (m,e)==(0,0) else f'{str(0)}' for (m,e) in zipTuple]
    p0=ax[0].bar(lstBarXTicks, dctAvgRatingByInterval['avg'], yerr=dctAvgRatingByInterval['std'])
    ax[0].bar_label(p0,labels=lstBarLabels,label_type='edge',color='m')
    ax[0].set_title(f'2010-2019: Genre Weighted Average Revenue by Rating Interval')
    ax[0].set_ylim(top=np.max(dctAvgRatingByInterval['avg'])+1.5)
    ax[0].set_ylabel('Revenue ($bb)')

    ### Axis 1: SCATTER PLOT: Genre
    p1=ax[1].scatter(dfGenreLevel['wavgrating'], dfGenreLevel['worldwide_gross'].div(1e9))
    ax[1].set_xlabel('Weighted Avg Genre Rating')
    ax[1].set_ylabel('Revenue ($bb)')
    ax[1].set_title(f'2010-2019: Genre Rating v Genre Revenue')
    ax[1].set_xlim(left=lstIntervalSet[0][0],right=lstIntervalSet[-1][1])

    plt.show()

    return None

def compute_revenue_mean_stdev_for_rating_interval(df, lstIntervalSet, strRatingColName, strRevenueColName, fltOrderOfMagnitude):
    """
    Compute average revenue for a rating interval of type (a,b]. All data cleaning has taken place, no NaNs
    """
    lstAvg = list()
    lstStd = list()
    for lstInterval in lstIntervalSet:
        mskRatingInterval = ((df[strRatingColName] > lstInterval[0]) & (df[strRatingColName] <= lstInterval[1]))
        seriesRevenue = df.loc[mskRatingInterval,strRevenueColName]
        fltRevenueMean = seriesRevenue.mean()
        fltRevenueStd  = seriesRevenue.std() / np.sqrt(seriesRevenue.count())
        lstAvg.append(fltRevenueMean/fltOrderOfMagnitude)
        lstStd.append(fltRevenueStd/fltOrderOfMagnitude)
    
    return {'avg':lstAvg,'std':lstStd}

def scatterplot_title_runtime_and_revenue(config):
    ### Load merged data
    df = dataprep.load_merged_clean_data(config)
    df = df.loc[ :, ['tconst','title','domestic_gross','foreign_gross','runtime_minutes']]
    df['worldwide_gross'] = df['domestic_gross'].add(df['foreign_gross'], fill_value=0)
    mskValidRevenue = ((df['worldwide_gross'].isna()==False) & (df['worldwide_gross']>0))
    mskValidRuntime = (df['runtime_minutes'].isna()==False)
    mskValidRows = (mskValidRevenue & mskValidRuntime)
    df = df.loc[mskValidRows]

    ### GENERATE PLOT: Genre Level Data
    fig, ax = plt.subplots(nrows=1,ncols=1,figsize=(7,5))

    ### Axis 0: BAR CHART: Genre Avg Revenue across Weighted Avg Ratings 
    ###                    X-Axis: Rating Intervals Defined by Genre Weighted Avg Rating
    ###                    Y-Axis: Average Genre Revenue

    ### Axis 1: SCATTER PLOT: Runtime_minutes and revenue
    p0=ax.scatter(df['runtime_minutes'], df['worldwide_gross'].div(1e9),s=7)
    ax.set_xlabel('runtime in minutes')
    ax.set_ylabel('revenue ($bb)')
    ax.set_title(f'2010-2019: Title Runtime in Minutes v Title Revenue')

    plt.show()

    return None