import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.utils
import pycountry
from matplotlib import pyplot as plt
from pygal_maps_world.maps import SupranationalWorld

from services.demographicsService import get_wikidata_results


def get_excluded_countries_and_continents_reg_exp(excluded_countries: list,
                                                  excluded_continents: list):
    """
      Build the excluded countries string
    """

    reg_exp_excluded_countries = ""

    if len(excluded_countries) != 0:

        if len(excluded_countries) == 1:

            reg_exp_excluded_countries = "MINUS\n{\n{?country rdfs:label '" + excluded_countries[0] + "'@en.}\n}"

        elif len(excluded_countries) > 1:

            reg_exp_excluded_countries = "\nUNION\n".join(["{?country rdfs:label '" + country + "'@en.}"
                                                           for country in excluded_countries])

            reg_exp_excluded_countries = "MINUS\n{\n" + reg_exp_excluded_countries + "\n}"

    """
      Build the excluded countries string
    """

    reg_exp_excluded_continents = ""

    if len(excluded_continents) != 0:

        if len(excluded_continents) == 1:

            reg_exp_excluded_continents = "MINUS\n{\n{?continent rdfs:label '" + excluded_continents[0] + "'@en.}\n}"

        elif len(excluded_continents) > 1:

            reg_exp_excluded_continents = "\nUNION\n".join(["{?continent rdfs:label '" + continent + "'@en.}"
                                                            for continent in excluded_continents])

            """
              Apart from the user specified continents he wants to eliminate, 
              I'm also dropping the continents with no valid namesm such as:
              -Eurasia-, -Central America-, -Americas-
            """
            not_valid_continents = """\nUNION
                                {?continent rdfs:label 'Eurasia'@en.}
                                UNION
                                {?continent rdfs:label 'Central America'@en.}
                                UNION
                                {?continent rdfs:label 'Americas'@en.}
                              """

            reg_exp_excluded_continents = "MINUS\n{\n" + reg_exp_excluded_continents + not_valid_continents + "\n}"

    return reg_exp_excluded_countries, reg_exp_excluded_continents


def cols_to_keep_and_their_types(df: pd.DataFrame,
                                 kwargs: dict) -> pd.DataFrame:
    keys = list(kwargs.keys())

    renamed_keys = [key[:key.index(".value")] for key in keys]

    types = list(kwargs.values())

    df = df[keys]

    df.rename(columns=dict(zip(keys, renamed_keys)),
              inplace=True)

    for pair in dict(zip(renamed_keys, types)).items():
        df[pair[0]] = df[pair[0]].astype(pair[1])

    return df


def video_games_service_1(excluded_countries: list,
                          excluded_continents: list):
    reg_exp_excluded_countries, reg_exp_excluded_continents = get_excluded_countries_and_continents_reg_exp(
        excluded_countries, excluded_continents)

    query = """
          SELECT ?countryLabel ?continentLabel (COUNT(?countryLabel) AS ?gamesInThisCountry)
          WHERE
          {
            SELECT ?gameLabel ?genreLabel ?countryLabel ?continentLabel
                              WHERE
                              {
                                ?game wdt:P31 wd:Q7889;
                                      wdt:P136 ?genre;
                                      wdt:P495 ?country. \n""" + reg_exp_excluded_countries + """\n
                                ?country wdt:P30 ?continent. \n""" + reg_exp_excluded_continents + """\n

                                BIND(IF (exists{?game wdt:P495 []}, "yes", "no") as ?countryExistence)

                                FILTER(?countryExistence = "yes")

                                SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }
                              }
          } GROUP BY ?continentLabel ?countryLabel
  """

    print(query)

    results = get_wikidata_results(query)  # returns a dict()

    pd_df = pd.json_normalize(results["results"]["bindings"])

    """
      Take only the useful columns
        AND
      Rename columns 
        AND 
      Specify the correct dtype of each column
    """

    pd_df = cols_to_keep_and_their_types(pd_df, {'countryLabel.value': str,
                                                 'continentLabel.value': str,
                                                 'gamesInThisCountry.value': float})

    pd_df.loc[pd_df[pd_df['continentLabel'] == 'Insular Oceania'].index, 'continentLabel'] = "Oceania"

    for rename in (('Insular Oceania', "Oceania"), ('United States of America', 'United States'),
                   ('Venezuela', 'Venezuela, Bolivarian Republic of'),
                   ('Russia', 'Russian Federation'), ('Czech Republic', 'Czechia'),
                   ('Moldova', 'Moldova, Republic of')):
        pd_df.loc[pd_df[pd_df['countryLabel'] == rename[0]].index, 'countryLabel'] = rename[1]

    pd_df = pd_df[pd_df['countryLabel'] != "Kingdom of the Netherlands"]

    united_kingdom = pd_df[pd_df['countryLabel'] == 'England']['gamesInThisCountry'].sum() + \
                     pd_df[pd_df['countryLabel'] == 'Scotland']['gamesInThisCountry'].sum() + \
                     pd_df[pd_df['countryLabel'] == 'Wales']['gamesInThisCountry'].sum() + \
                     pd_df[pd_df['countryLabel'] == 'Republic of Ireland']['gamesInThisCountry'].sum()

    new_row = {'countryLabel': 'United Kingdom',
               'continentLabel': 'Europe',
               'gamesInThisCountry': united_kingdom}

    pd_df = pd_df.append(new_row, ignore_index=True)

    """
      Add country codes so that they can be identified on the plotly world map
    """

    pd_df['country_code'] = ''
    pd_df['country_code'] = pd_df['country_code'].astype(str)

    countries_iso_codes_dict = dict()
    for country in pycountry.countries:
        countries_iso_codes_dict[country.name] = country.alpha_3

    for i in range(0, pd_df.shape[0]):
        if pd_df.loc[i].loc['countryLabel'] not in countries_iso_codes_dict.keys():
            continue
        else:
            pd_df.loc[i, 'country_code'] = countries_iso_codes_dict[pd_df.loc[i].loc['countryLabel']]

    pd_df = pd_df[pd_df['country_code'] != '']

    fig = px.scatter_geo(pd_df,
                         locations='country_code',
                         projection='orthographic',
                         color='continentLabel',
                         opacity=.9,
                         hover_name='countryLabel',
                         hover_data=['gamesInThisCountry'],
                         size='gamesInThisCountry')
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


# ------------------------------------------------------------------------------


def video_games_service_2(excluded_countries: list,
                          excluded_continents: list):
    reg_exp_excluded_countries, reg_exp_excluded_continents = get_excluded_countries_and_continents_reg_exp(
        excluded_countries, excluded_continents)

    # -----------------------------------------------------------------------------

    query = """
          SELECT ?continentLabel (SUM(?gamesInThisCountry) AS ?gamesInThisContinent)
          WHERE
          {
              SELECT ?countryLabel ?continentLabel (COUNT(?countryLabel) AS ?gamesInThisCountry)
              WHERE
              {
                  SELECT ?gameLabel ?genreLabel ?countryLabel ?continentLabel
                                    WHERE
                                    {
                                      ?game wdt:P31 wd:Q7889;
                                            wdt:P136 ?genre;
                                            wdt:P495 ?country. \n""" + reg_exp_excluded_countries + """\n
                                      ?country wdt:P30 ?continent. \n""" + reg_exp_excluded_continents + """\n

                                      BIND(IF (exists{?game wdt:P495 []}, "yes", "no") as ?countryExistence)

                                      FILTER(?countryExistence = "yes")

                                      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }
                                    }
              } GROUP BY ?continentLabel ?countryLabel
          }  GROUP BY ?continentLabel
  """

    print(query)

    results = get_wikidata_results(query)  # returns a dict()

    pd_df = pd.json_normalize(results["results"]["bindings"])

    """
      Take only the useful columns
        AND
      Rename columns 
        AND 
      Specify the correct dtype of each column
    """

    pd_df = cols_to_keep_and_their_types(pd_df, {'continentLabel.value': str,
                                                 'gamesInThisContinent.value': float})

    pd_df.loc[pd_df[pd_df['continentLabel'] == 'Insular Oceania'].index, 'continentLabel'] = "Oceania"

    """
      Prepare the values to be sent to the pygal world map 
    """

    pd_df['continentLabel'] = pd_df['continentLabel'].apply(lambda continent: "asia" if continent == "Asia" else
    "africa" if continent == "Africa" else
    "europe" if continent == "Europe" else
    "oceania" if continent == "Oceania" else
    "antartica" if continent == "Antarctica" else
    "south_america" if continent == "South America" else
    "north_america")

    pygal_continent = {'asia': 'Asia',
                       'africa': 'Africa',
                       'europe': 'Europe',
                       'oceania': 'Oceania',
                       'antartica': 'Antarctica',
                       'south_america':
                           'South america',
                       'north_america':
                           'North america'}

    world_map = dict(pd_df.values)

    supra = SupranationalWorld(width=1000, height=600)
    supra.force_uri_protocol = 'http'

    for pair in world_map.items():
        supra.add(pygal_continent[pair[0]], [pair])

    supra.render_to_file('static/images/img.svg')

    return "static/images/img.svg"

# ------------------------------------------------------------------------------


def video_games_service_3(which_countries: list) -> tuple:
    reg_exp = '|'.join(['(' + country + ')' for country in which_countries])

    query = """ SELECT ?countryLabel ?genreLabel (COUNT(*) AS ?nrGames)
              {
              SELECT ?gameLabel ?genreLabel ?countryLabel ?continentLabel
                                WHERE
                                {
                                  ?game wdt:P31 wd:Q7889;
                                        wdt:P136 ?genre;
                                        wdt:P495 ?country.

                                  ?country rdfs:label ?countryLabelRegex.

                                  BIND(IF (exists{?game wdt:P495 []}, "yes", "no") as ?countryExistence)

                                  FILTER(?countryExistence = "yes")

                                  FILTER(REGEX(?countryLabelRegex, '""" + reg_exp + """'))

                                  FILTER(langMatches(lang(?countryLabelRegex), "EN")).

                                  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }
                                }
              } GROUP BY ?countryLabel ?genreLabel

  """

    print(query)

    results = get_wikidata_results(query)  # returns a dict()

    pd_df = pd.json_normalize(results["results"]["bindings"])

    """
      Take only the columns I need 
      AND
      Rename the columns
    """
    pd_df = pd_df[['countryLabel.value', 'genreLabel.value', 'nrGames.value']]

    pd_df.rename(columns={'countryLabel.value': 'countryLabel',
                          'genreLabel.value': 'genreLabel',
                          'nrGames.value': 'nrGames'}, inplace=True)

    pd_df['nrGames'] = pd_df['nrGames'].astype(float)

    """
      Group by country
      AND
      Consider only the mutual genres (genres produced by both countries)
      AND
      Select the top 3 mutual genres in both countries
    """

    groups = pd_df.groupby(by=['countryLabel'])

    genres_by_country = [groups.get_group(country)['genreLabel'].tolist()
                         for country in which_countries]
    mutual_genres = set(genres_by_country[0]).intersection(set(genres_by_country[1]))

    country_1 = groups.get_group(which_countries[0])
    country_1 = country_1[country_1['genreLabel'].isin(mutual_genres)]

    country_2 = groups.get_group(which_countries[1])
    country_2 = country_2[country_2['genreLabel'].isin(mutual_genres)]

    if country_1['genreLabel'].shape[0] > country_2['genreLabel'].shape[0]:

        country_2 = country_2.sort_values(by=['nrGames'], inplace=False).head(3).sort_values(by=['genreLabel'])

        where_genres_same_as_country_2 = country_1['genreLabel'].isin(country_2['genreLabel'].tolist())

        country_1 = country_1[where_genres_same_as_country_2].sort_values(by=['genreLabel'])

    else:

        country_1 = country_1.sort_values(by=['nrGames'], inplace=False).head(3).sort_values(by=['genreLabel'])

        where_genres_same_as_country_1 = country_2['genreLabel'].isin(country_1['genreLabel'].tolist())

        country_2 = country_2[where_genres_same_as_country_1].sort_values(by=['genreLabel'])

    return comparative_bar_chart(country_1, country_2)


def comparative_bar_chart(df_first_country: pd.DataFrame,
                          df_second_country: pd.DataFrame):
    genres = df_first_country['genreLabel']

    countries = [df_first_country['countryLabel'].iloc[0],
                 df_second_country['countryLabel'].iloc[0]]

    counts = [df_first_country['nrGames'].tolist(), df_second_country['nrGames'].tolist()]

    x_indexes = np.arange(len(genres))
    width = 0.25

    plt.rcdefaults()
    plt.style.use('seaborn')
    plt.xkcd()

    fig, ax = plt.subplots(nrows=1, ncols=1)

    ax.bar(x_indexes - width, counts[0], width=width, label=countries[0])
    ax.bar(x_indexes, counts[1], width=width, label=countries[1])

    ax.set_title("Top 3 mutual video games produced by each country")
    ax.legend()

    ax.set_xlabel('Genre')
    ax.set_xticks(range(len(genres)))
    ax.set_xticklabels(labels=genres)

    plt.tight_layout()
    fig.savefig('static/images/plot.png')

    return 'static/images/plot.png'
