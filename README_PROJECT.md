![tag-microsoft-logo](./images/Microsoft-Logo.png =10x20)

# Motion Pictures Profitability Analysis

**Author**: [Daniel Shevelev](mailto:ds2012flatiron@gmail.com)

## Overview

This project uses the film profile data by title from [Internet Movie Database](https://en.wikipedia.org/wiki/IMDb) (IMDb) combined with the data from the box-office revenue tracking serving [Box Office Mojo](https://en.wikipedia.org/wiki/Box_Office_Mojo) to determine which film categories are doing or did well at the box office. Historical and current analysis of film revenue is a minimal first step in allocating resources for the venture by Microsoft to create a movie studio for a streaming service.


## Business Problem

A large tech company wants to enter a streaming and entertainment business by leveraging its significant multi-user storage, computing, and network capabilities. This company may be Microsoft or any other tech company with above-mentioned expertise.

Besides streaming, Microsoft also wants to produce content. Clearly, this content should generate subscribers to make the streaming venture profitable. To understand what film attributes are more likely to be revenue generating, this analysis reviews the box office results, ratings, and other film characteristics to provide insights into the preferences of the viewing public.

Once past viewer preferences are understood, they can be translated into actionable insights for which films to create.

## The Data
The data for this project come from a number of different sources and are delivered as zipped comma and tab delimited files. The project data are structured in the sense that each file represents a set of characteristics for a single film title or a title-related piece of information such as a name (i.e. actor, director, writer, etc), a rating, a film synopsis, etc.

The project data files are provided on [Phase 1 Project GitHub page](https://github.com/learn-co-curriculum/dsc-phase-1-project). The files are compressed using `gz` format.  Libraries `gzip` and `shutil` libraries are used to uncompress files into their underlying text formats.

 Below is a short description of each data file from each data source.
* [Box Office Mojo (BOM)](https://www.boxofficemojo.com/)
    - **bom.movie_gross.csv**: title name, release year, foreign and domestic gross revenue; 
* [IMDB](https://www.imdb.com/)
    - **imdb.title.basics.csv:** title name, release year, total runtime, and genre (often multiple genres);
    - **imdb.title.ratings.csv:** title average rating, number of votes received by the title;
    - **imdb.title.crew.csv:** lists the film director and writer(s) by referencing their unique ids from the file `imdb.name.basics.csv`;
    - **imdb.title.principals.csv:** contains principal cast/crew members, indicating job category, and, in case of actors, characters played;
    - **imdb.title.akas.csv:** contains title names in the native language of all countries where the title was released;
* [Rotten Tomatoes (RT)](https://www.rottentomatoes.com/)
    - **rt.movie_info.tsv:** contains title synopsis, MPA rating (i.e. PG-13, etc), genre, director, writer, release date, box office, run time, studio;
    - **rt.reviews.tsv:** contains ratings from professional movie critics;
* [TheMovieDB(TMDB)](https://www.themoviedb.org/)
    - **tmdb.movies.csv:** contains title rating data; 
* [The Numbers(TN)](https://www.the-numbers.com/)
    - **tn.movie_budgets.csv:** contains title level revenue information: budget, domestic gross, and worldwide gross.
    
### Data Assessment

IMDB data are the most consistent data package which provides title and name unique identifiers for joining data in separate files. The data in the file `imdb.title.akas.csv` may be viewed as the least relevant to the business problem.

While certain personalities such famous actors, directors, script writers, may indicate a potentially profitable project or a franchise, investing in a film on the basis of a certain personality may expose one to idiosyncratic risk. Therefore, IMDB data on crew and principals contained in files `imdb.title.crew.csv` and `imdb.title.principles.csv` are not considered.

Rotten Tomatoes data are not considered due to missing title information such as the title itself.

The Movie DB data can be viewed as an auxhiliary source of the title rating offered by viewers.

Budget and revenue data from website [The Numbers](https://www.the-numbers.com) is a useful supplemental dataset for title level revenue data. The recommended for the project file `bom.movie_gross.csv` from BOM has about 3.4K lines of data, whereas the file `tn.movie_budgets.csv` has 5.8K lines of data. It should be mentioned that further analysis would be required as domestic or foreign (or both) revenue information can be missing.

### Data Preparation

This section discusses the steps to clean and normalize data in files `imdb.title.basics.csv`, `imdb.title.rating.csv`, and `bom.movie_gross.csv`. The code responsible for preparing the data is compartmentalized in a library `code/data_preparation.py`. The data preparation is driven by the umbrella function `prepare_clean_data(config)` which calls file specific data prepartion functions.

* `imdb.title.basics.csv`: the file is prepared by calling function `prep_imdb_title_basics(config)` which (i) removes rows with null values in columns for run time and genre, (ii) removes all titles released in 2020, 2021, and 2022 since economics of these releases are affected by COVID related disruptions, (iii) removes all the titles with run times below 25 minutes and above 6 hours (360) minutes.
* `imdb.title.rating.csv`: Function `prep_imdb_title_ratings` (i) removes rows with null values, (ii) rows with off the scale rating value (1-10), (iii) and rows with ratings from a small number of votes (below 100).
* `bom.movie_gross.csv`: Similar to other functions, `prep_bom_movie_gross(config)` (i) removes rows with null values, (ii) parses each value of domestic and foreign revenue and converts it to a number.
* `tn.movie_budgets.csv`: TN source for revenue data by title. Just like with BOM data, `prep_tn_movie_budgets(config)` performs similar data cleaning and standardization operations.
* merging clean data: functon `merge_clean_data` performs a left join of IMDB title data to IMDB rating data on IMDB title unique key. The budget data are joined on the title string itself which capitalized left joins of title basics and title ratings followed by a left join of merged TN and BOM movie gross data.

## Methodology

It is a basic tenet of this analysis, and one's personal experience, that certain genres of film are more popular with the viewing audience. The public preference may change over time, and historical experience supports this observation. The focus of this analysis is the 10-year period from 2010 to 2019.

Profit and loss (title revenue less title budget) is not discussed in this analysis. There are several reasons for it. First, Budget data are incomplete as title budget data are only available from TN, and TN data end in 2016. Second, a significant portion of a title budget is often for promotion which increases the market size and revenue of the film but may not influence ratings. The influence of promotional budget on ratings and revenue may be a topic of further research which requires additional data on production costs only. Thirdly, large promotional budgets are typical of large productions in action, adventure, and sci-fi genres which are known and designed for large box office revenue. Here, it is important to find out what other genres may also generate revenue, perhaps, without additional exposure of high promotional costs and their uncertain recovery. 

In these data, a film title has four measurable attributes which are genre, rating, run time, and gross revenue either foreign or domestic or both. Therefore, the recommendations to a developing film studio will come in a format of 
1. A list of genres which made the most money over the 10 year period.
2. A list of genres which made the most money per title and the standard deviation of this revenue as a measure of risk.
3. A list of genres with the highest rating per title and the standard deviation of this rating as a measure of uncertainty about this rating for a randomly selected title;
4. A correlation analysis between title rating and title gross revenue for genres with highest rating per title. If the correlation is high, then it provides an indication of high revenue for genres with high per title rating.
5. A correlation analysis between title run time and revenue. This analysis will test the hypothesis that very short productions or very long productions may need to be avoided.

The data on movie titles, their release year, run time, genre, and rating are sourced from [IMDB](https://www.imdb.com/), and revenue data by title are sourced from [Box Office Mojo](https://www.boxofficemojo.com/). These data are compressed in 'gzip' format files which contain comma delimited data files. These files are provided on [Phase 1 Project GitHub page](https://github.com/learn-co-curriculum/dsc-phase-1-project).

## Analysis and Results

### Genres with Most Revenue in 2010-2019




## Recommendations

1. A new streaming service should produce films in genres `Action,Adventure,Sci-Fi` and `Adventure, Animation, Comedy`. Historical performance indicates that they are the best combination of revenue level and revenue risk across all genres.

2. A streaming service is more suited for genres such as biography and documentary films which are not considered to have a blockbuster appeal. Based on rating data, a new streaming service should consider producing documentaries with biographical, historical, military related plot threads. Well-liked titles will drive subscription volume which is the revenue backbone for a streaming service.

In addition, the data provide evidence that, on average, the higher rated is the title, the higher is its earnings potential. The data also show that below the rating of 4, the likelihood of the title to make money is limited. Therefore, test audience previews are also recommended.

3. `Keep it short!` The data show a sharp decline in revenue for titles with runtimes above 2.5 hours. Titles with runtimes below 60 minutes are less likely to make money as well. The data show that the titles with runtimes of approximately 2 hours are the most consistent at making money. Yet, variability is significant, and only the lower bound of 60 minutes and upper bound of 2.5 hours is best adhered to.

All data file are compressed and contain comma delimited data sets for (1) movie title basic characteristics, (2) movie title ratings, and (3) movie title revenue. 

In the folder `zippedData` are movie datasets from:

* [Box Office Mojo](https://www.boxofficemojo.com/)
* [IMDB](https://www.imdb.com/)
* [Rotten Tomatoes](https://www.rottentomatoes.com/)
* [TheMovieDB](https://www.themoviedb.org/)
* [The Numbers](https://www.the-numbers.com/)

It is up to you to decide what data from this to use and how to use it. If you want to make this more challenging, you can scrape websites or make API calls to get additional data. If you are feeling overwhelmed or behind (e.g. struggled with the Phase 1 Code Challenge), we recommend you use only the following data files:

* imdb.title.basics
* imdb.title.ratings
* bom.movie_gross

## Deliverables

There are three deliverables for this project:

* A **GitHub repository**
* A **Jupyter Notebook**
* A **non-technical presentation**

Review the "Project Submission & Review" page in the "Milestones Instructions" topic for instructions on creating and submitting your deliverables. Refer to the rubric associated with this assignment for specifications describing high-quality deliverables.

### Key Points

* **Your analysis should yield three concrete business recommendations.** The ultimate purpose of exploratory analysis is not just to learn about the data, but to help an organization perform better. Explicitly relate your findings to business needs by recommending actions that you think the business (Microsoft) should take.

* **Communicating about your work well is extremely important.** Your ability to provide value to an organization - or to land a job there - is directly reliant on your ability to communicate with them about what you have done and why it is valuable. Create a storyline your audience (the head of Microsoft's new movie studio) can follow by walking them through the steps of your process, highlighting the most important points and skipping over the rest.

* **Use plenty of visualizations.** Visualizations are invaluable for exploring your data and making your findings accessible to a non-technical audience. Spotlight visuals in your presentation, but only ones that relate directly to your recommendations. Simple visuals are usually best (e.g. bar charts and line graphs), and don't forget to format them well (e.g. labels, titles).

## Getting Started

Please start by reviewing this assignment, the rubric at the bottom of it, and the "Project Submission & Review" page. If you have any questions, please ask your instructor ASAP.

Next, we recommend you check out [the Phase 1 Project Templates and Examples repo](https://github.com/learn-co-curriculum/dsc-project-template) and use the MVP template for your project.

Alternatively, you can fork [the Phase 1 Project Repository](https://github.com/learn-co-curriculum/dsc-phase-1-project), clone it locally, and work in the `student.ipynb` file. Make sure to also add and commit a PDF of your presentation to your repository with a file name of `presentation.pdf`.

## Project Submission and Review

Review the "Project Submission & Review" page in the "Milestones Instructions" topic to learn how to submit your project and how it will be reviewed. Your project must pass review for you to progress to the next Phase.

## Summary

This project will give you a valuable opportunity to develop your data science skills using real-world data. The end-of-phase projects are a critical part of the program because they give you a chance to bring together all the skills you've learned, apply them to realistic projects for a business stakeholder, practice communication skills, and get feedback to help you improve. You've got this!
