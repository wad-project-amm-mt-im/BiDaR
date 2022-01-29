import re
import sys

import numpy as np
import pandas as pd
import pyspark
from SPARQLWrapper import SPARQLWrapper, JSON
from matplotlib import pyplot as plt
from pyspark import SparkContext
from pyspark.sql import SQLContext

sc = SparkContext.getOrCreate()
sql_context = SQLContext(sc)


def get_wikidata_results(query: str):
    endpoint_url = "https://query.wikidata.org/sparql"
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def demographics_service_1(countries_names: list,
                           option: str) -> pd.DataFrame:
    reg_exp = '|'.join(['(' + country + ')' for country in countries_names])

    query = """ SELECT ?countryLabel ?population ?lifeExpectancy ?HDI ?year ?month
              WHERE
              {
                  ?country wdt:P31 wd:Q6256;
                           rdfs:label ?countryLabel;
                           p:P1082 ?populationStatement.

                  ?populationStatement ps:P1082 ?population;
                                       pq:P585 ?populationDate. # MONTH AND YEAR ARE GIVEN

                  OPTIONAL {
                    ?country p:P2250 ?lifeExpectancyStatement.
                    ?lifeExpectancyStatement ps:P2250 ?lifeExpectancy;
                                             pq:P585 ?lifeExpectancyDate.    # ONLY THE YEAR IS GIVEN
                  }

                  OPTIONAL {
                    ?country p:P1081 ?HDIStatement.

                    ?HDIStatement ps:P1081 ?HDI;
                                  pq:P585 ?HDIDate   # ONLY THE YEAR IS GIVEN

                  }

                  BIND(YEAR(?populationDate) AS ?year).

                  BIND(MONTH(?populationDate) AS ?month).

                  FILTER(langMatches(lang(?countryLabel), 'EN')).

                  FILTER(YEAR(?lifeExpectancyDate) = YEAR(?populationDate) && YEAR(?HDIDate) = YEAR(?populationDate)).

                  FILTER (REGEX(?countryLabel, '""" + reg_exp + "')).\n" + \
            """
         } ORDER BY ASC(?country) """

    print(query)

    results = get_wikidata_results(query)  # returns a dict()

    pd_df = pd.json_normalize(results["results"]["bindings"])

    spark_df = get_spark_df(pd_df)

    if option == "stackplot":

        data = get_data_for_plots(spark_df, relevant_columns=["countryLabel", "population", "month", "year"])
        return build_stack_plot(data)

    elif option == "lineplot":

        data = get_data_for_plots(spark_df, relevant_columns=["countryLabel", "lifeExpectancy", "month", "year"])
        return build_line_plot(data)

    elif option == "pieplot":

        data = get_data_for_plots(spark_df, relevant_columns=["countryLabel", "HDI", "month", "year"])
        return build_pie_bar_chart(data)

    return pd_df


# -------------------------------------------------------------------------------


def get_spark_df(pd_df: pd.DataFrame) -> pyspark.sql.DataFrame:
    """
      Get the datatypes of the columns in my select clause
      I need to cast the pandas dataframe columns to these datatypes
    """
    cols_of_interest = [col for col in pd_df.columns if ".datatype" in col]
    cols_data_types = pd_df.iloc[0].loc[cols_of_interest]
    cols_data_types = [re.search("#([a-zA-Z]+)", elem).group(1) for elem in cols_data_types]

    """
      I am only interested in the values columns
      I don't care about the columns that specify dataypes, types (literal etc), language and so on
    """

    cols_of_interest = [col.replace(".datatype", ".value") for col in cols_of_interest]
    cols_and_datatypes = list(zip(cols_of_interest, cols_data_types)) + [("countryLabel.value", "string")]

    xsd_to_python_types = {"string": str,
                           "integer": int,
                           "decimal": float,
                           "double": float}

    for elem in cols_and_datatypes:
        col = elem[0];
        dtype = elem[1]
        pd_df[col] = pd_df[col].astype(xsd_to_python_types[dtype])

    """
      Renamed the columns I need, so I get rid of that ".values" at the end of
        each column
    """

    cols_and_datatypes = np.array(cols_and_datatypes)

    renamed_cols = dict(zip(cols_and_datatypes[:, 0],
                            [col[:col.index(".value")]
                             for col in cols_and_datatypes[:, 0]]))

    cols_and_datatypes[:, 0] = list(renamed_cols.values())

    pd_df.rename(columns=renamed_cols, inplace=True)

    """
      Build the Spark DataFrame
    """

    spark_df = sql_context.createDataFrame(pd_df[cols_and_datatypes[:, 0]]).distinct()

    return spark_df


# -------------------------------------------------------------------------------


def get_data_for_plots(spark_df: pyspark.sql.DataFrame,
                       relevant_columns: list) -> dict:
    countries = [list(country.asDict().values())[0]
                 for country in spark_df.select('countryLabel').distinct().take(195)]

    month_year_combos = spark_df.select(relevant_columns) \
        .distinct().select(["month", "year"]).distinct() \
        .take(1000000)

    month_year_combos = [tuple(combo.asDict().values())
                         for combo in month_year_combos]

    group_by_country_df = spark_df.select(relevant_columns) \
        .distinct() \
        .rdd.map(lambda row: list(row.asDict().values())) \
        .map(lambda line: (line[0], tuple(line[1:]))) \
        .groupByKey()

    groups = dict(group_by_country_df.take(195))

    """
      For each country, keep only the dates --a.k.a (month, year) tuples-- when
        each census took place
    """

    country_month_year_df = group_by_country_df.map(lambda pair:
                                                    (pair[0], [(triple[1], triple[2])
                                                               for triple in pair[1]]))

    """
      Keep only those dates --a.k.a (month, year) tuples-- when censuses took
        place simultaneously in all of the given countries
    """

    simultaneous_dates = []
    for date in month_year_combos:
        if country_month_year_df.map(lambda pair: date in pair[1]).sum() == len(countries):
            simultaneous_dates.append(date)

    """
      Keep only those population statistics where censuses took place simultaneously
       on the same dates
    """

    data_to_plot = dict(group_by_country_df.map(lambda pair:
                                                (pair[0], [triple for triple in pair[1]
                                                           if (triple[1], triple[2]) in simultaneous_dates]))
                        .take(1000000))

    """
      Construct proper datetimes to plot
    """
    # population month year -> population year-month(str)

    data_to_plot = dict(list(map(lambda pair: [pair[0],
                                               [(value[0], str(value[2]) + "-" + str(value[1]))
                                                for value in pair[1]]],
                                 data_to_plot.items())))

    """
      Sort according to the datetimes
    """
    for key in data_to_plot.keys():
        values = data_to_plot[key]
        data_to_plot[key] = sorted(values, key=lambda pair: pair[1])

    return data_to_plot


# -------------------------------------------------------------------------------


def build_stack_plot(data_to_plot: dict):
    plt.rcdefaults()
    plt.style.use('seaborn')
    plt.xkcd()

    fig, ax = plt.subplots(nrows=1, ncols=1)

    populations = list()

    keys = list(data_to_plot.keys())

    for country in keys:
        values = np.array(data_to_plot[country])  # for some weird reasons, transforming a list to numpy array converts all the elements to string types lol

        pops = values[:, 0].astype(float)
        dates = values[:, 1]

        populations.append(pops)

    ax.stackplot(dates, populations, labels=keys)

    ax.set_title("Population evolution through the years")
    plt.legend(loc=(-0.2, 0))
    plt.tight_layout()
    fig.savefig('static/images/plot.png')

    return 'static/images/plot.png'


# -------------------------------------------------------------------------------


def build_line_plot(data_to_plot: dict):
    plt.rcdefaults()
    plt.style.use('seaborn')
    plt.xkcd()

    fig, ax = plt.subplots(nrows=1, ncols=1)

    populations = list()

    keys = list(data_to_plot.keys())

    for country in keys:
        values = np.array(data_to_plot[country])  # for some weird reasons, transforming a list to numpy array converts all the elements to string types lol

        pops = values[:, 0].astype(float)
        dates = values[:, 1]

        populations.append(pops)

    for i in range(0, len(keys)):
        ax.plot(dates, populations[i], label=keys[i], marker='o')

    ax.set_xlabel("DateTime")
    ax.set_ylabel("Life Expectancy")

    plt.legend()
    plt.tight_layout()
    fig.savefig('static/images/plot.png')

    return 'static/images/plot.png'


# -------------------------------------------------------------------------------


def build_pie_bar_chart(data_to_plot: dict):
    hdis = list()

    keys = list(data_to_plot.keys())

    for country in keys:
        values = np.array(data_to_plot[country])  # for some weird reasons, transforming a list to numpy array converts all the elements to string types lol

        average_hdi = values[:, 0].astype(float).mean()

        hdis.append(average_hdi)

    hdis = np.array(hdis)

    labels = ['low', 'medium', 'high', 'very high']
    counts = [(hdis <= 0.549).sum(), ((0.55 <= hdis) & (hdis <= 0.6999)).sum(), ((0.7 <= hdis) & (hdis <= 0.7999)).sum(), (0.8 <= hdis).sum()]

    fig, ax = plt.subplots(nrows=1, ncols=2)

    ax[0].pie(counts, labels=labels, autopct="%1.1f%%", wedgeprops={"edgecolor": "black"}, shadow=True)
    ax[0].set_title("HDI Distribution")

    ax[1].bar(range(len(labels)), counts, label=labels)
    ax[1].set_xticks(range(len(labels)))
    ax[1].set_xticklabels(labels=labels)
    ax[1].set_title("HDI Distribution")

    plt.tight_layout()
    fig.savefig('static/images/plot.png')

    return 'static/images/plot.png'


"""
  greater_than_list vreau sa vina ca lista de stringuri neaparat
"""


def demographics_service_2(countries_names: list,
                           option: str,
                           greater_than_list: list) -> pd.DataFrame:
    reg_exp = '|'.join(['(' + country + ')' for country in countries_names])

    # _ = [float(elem) if "-" not in elem else "-" for elem in greater_than_list]
    # greater_than_list = copy.deepcopy(_)

    if "min" == option:
        option = "MIN"
    elif "max" == option:
        option = "MAX"
    else:
        option = "AVG"

    d = {0: "(?fertility)",
         1: "(?democracy)",
         2: "(?lifeExpectancy)"}

    if 'MIN' == option:
        select_clause = "?countryLabel (MIN(?fertility) AS ?fertilityMin) (MIN(?democracy) AS ?democracyMin) (MIN(?lifeExpectancy) AS ?lifeExpectancyMin)"
    elif 'MAX' == option:
        select_clause = "?countryLabel (MAX(?fertility) AS ?fertilityMax) (MAX(?democracy) AS ?democracyMax) (MAX(?lifeExpectancy) AS ?lifeExpectancyMax)"
    else:
        select_clause = "?countryLabel (AVG(?fertility) AS ?fertilityAvg) (AVG(?democracy) AS ?democracyAvg) (AVG(?lifeExpectancy) AS ?lifeExpectancyAvg)"

    having_clause = " HAVING (" + \
                    " && ".join([option + d[x] + " > " + greater_than_list[x]
                                 for x in range(0, len(greater_than_list))
                                 if '-' not in greater_than_list[x]]) + \
                    ") "

    query = """ SELECT """ + select_clause + """ \n
              WITH{
                  SELECT ?country ?countryLabel WHERE {

                  ?country wdt:P31 wd:Q6256;
                            rdfs:label ?countryLabel.
                    FILTER (REGEX(?countryLabel, '""" + reg_exp + """')). \n
                    FILTER(lang(?countryLabel)="en").
                    } } as %i

              WHERE
              {
                  INCLUDE %i
                  ?country p:P4841 ?fertilityStatement.
                  ?fertilityStatement ps:P4841 ?fertility;
                                      pq:P585 ?fertilityDate.

                  ?country p:P8328 ?democracyStatement.
                  ?democracyStatement ps:P8328 ?democracy;
                                      pq:P585 ?democracyDate.

                  ?country p:P2250 ?lifeExpectancyStatement.
                  ?lifeExpectancyStatement ps:P2250 ?lifeExpectancy;
                                          pq:P585 ?lifeExpectancyDate.

                } GROUP BY ?countryLabel""" + having_clause + """ORDER BY ASC(?country)"""

    print(query)

    results = get_wikidata_results(query)  # returns a dict()

    pd_df = pd.json_normalize(results["results"]["bindings"])
    if pd_df.empty:
        f = plt.figure(figsize=(15, 10))
        f.savefig('static/images/plot.png')
        return 'static/images/plot.png'

    # I take only the columns I need
    pd_df = pd_df[[column for column in pd_df.columns if ".value" in column]]

    # Rename columns
    pd_df.rename(columns=dict([(column, column[:column.index(".value")])
                               for column in pd_df.columns]),
                 inplace=True)

    # Drop row duplicates
    pd_df.drop_duplicates(ignore_index=True, inplace=True)

    # Set the countries as indexes
    pd_df.set_index(keys='countryLabel', drop=True, inplace=True)

    # Set the correct dtypes of the columns
    for col in pd_df.columns:
        pd_df[col] = pd_df[col].astype(float)

    return build_matshow_plot(pd_df)


def build_matshow_plot(matrix: pd.DataFrame):
    plt.rcdefaults()
    plt.xkcd()

    f = plt.figure(figsize=(15, 10))

    values_to_plot = matrix.values

    plt.matshow(values_to_plot, fignum=f.number)

    for i in range(0, len(values_to_plot)):
        for j in range(0, len(values_to_plot[i])):
            plt.text(j, i, values_to_plot[i][j], va='center', ha='center')

    plt.xticks(ticks=range(0, matrix.shape[1]), labels=matrix.columns, rotation=90)
    plt.yticks(ticks=range(0, matrix.shape[0]), labels=matrix.index)

    plt.tight_layout()
    f.savefig('static/images/plot.png')

    return 'static/images/plot.png'
