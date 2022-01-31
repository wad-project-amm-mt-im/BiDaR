# services/web/server/main/views.py


try:
    from pyspark import SparkContext, SparkConf, SQLContext
    from operator import add
    import re
    import pandas as pd
    import pyspark
    import numpy as np
except:
    print('error')


def create_task(words):
    conf = SparkConf().setAppName('letter count')
    sc = SparkContext(conf=conf)
    seq = words.split()
    data = sc.parallelize(seq)
    counts = data.map(lambda word: (word, 1)).reduceByKey(add).collect()
    sc.stop()
    return dict(counts)



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



def get_spark_df(pd_df: pd.DataFrame) -> pyspark.sql.DataFrame:
    sc = SparkContext.getOrCreate()
    sql_context = SQLContext(sc)
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
