import pandas as pd
from matplotlib import pyplot as plt
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
from wordcloud import WordCloud

from services.demographicsService import get_wikidata_results
from services.gamesService import cols_to_keep_and_their_types


def recommendation_system(user_liked_ingredients: list,
                          option: str):
    query = """SELECT ?plateLabel ?ingredientLabel
             WHERE
             {
               ?plate wdt:P31 wd:Q746549; # instance of dish 
                      p:P527 ?plateStatement.

                OPTIONAL {?plate wdt:P279 wd:Q2095.} # subclass of food

                ?plateStatement ps:P527 ?ingredient.

                SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }  
             }
  """

    print(query)

    results = get_wikidata_results(query)  # returns a dict()

    pd_df = pd.json_normalize(results["results"]["bindings"])
    pd_df = cols_to_keep_and_their_types(pd_df, {"plateLabel.value": str,
                                                 "ingredientLabel.value": str})

    for col in pd_df.columns:
        pd_df[col] = pd_df[col].str.lower()

    if option == "0":
        return visualise_word_cloud(pd_df)
    else:
        """
          Group by plateLabel
          In this way I will have a dataframe where each row is a dish AND its ingredients in a list
        """

        new_df = pd.DataFrame(columns=('plateLabel', 'ingredients'))

        groups = pd_df.groupby(by=['plateLabel'])
        for group in pd_df['plateLabel'].unique():
            new_row = {"plateLabel": group,
                       "ingredients": groups.get_group(group)['ingredientLabel'].tolist()}
            new_df = new_df.append(new_row, ignore_index=True)

        """
          Give me all the receipes that have the user specified ingredients
        """
        receipes = []
        for i in range(0, new_df.shape[0]):
            ok = 1
            for user_ingredient in user_liked_ingredients:
                if user_ingredient not in new_df['ingredients'].iloc[i]:
                    ok = 0
            if ok == 1:
                receipes.append(new_df['plateLabel'].iloc[i])

        receipes = ', '.join(receipes)

        """
          Build the association rules
        """

        return build_association_rules(new_df, user_liked_ingredients, receipes)


def visualise_word_cloud(df: pd.DataFrame):
    plt.rcdefaults()

    wc = WordCloud(background_color='white', height=600, width=600)

    wc = wc.generate(' '.join(df['ingredientLabel'].tolist()))

    fig = plt.figure()
    plt.imshow(wc)
    plt.axis('off')
    fig.savefig('static/images/plot.png', bbox_inches='tight')

    return 'static/images/plot.png'


def build_association_rules(df: pd.DataFrame,
                            user_liked_ingredients: pd.DataFrame,
                            receipes: str):
    unique_ingredients = set()
    for elem in df['ingredients'].values:
        unique_ingredients.update(elem)

    rules_df = pd.DataFrame(data=False, index=[_ for _ in range(0, df.shape[0])],
                            columns=unique_ingredients)

    for i in range(0, len(df)):
        for ingredient in df['ingredients'].iloc[i]:
            rules_df.loc[i, ingredient] = True

    support_table = apriori(rules_df, min_support=0.01, use_colnames=True)
    support_table.sort_values(by='support', axis=0, ascending=False, inplace=True)

    apriori_table = association_rules(support_table, metric="confidence", min_threshold=0.1)
    apriori_table.sort_values(by='confidence', axis=0, ascending=False)
    apriori_table['antecedents'] = apriori_table['antecedents'].apply(lambda elem: tuple(elem))

    memorize_indexes = []
    for i in range(0, apriori_table['antecedents'].shape[0]):
        ok = 1
        for ingredient in apriori_table['antecedents'].iloc[i]:
            if ingredient not in user_liked_ingredients:
                ok = 0
        if ok == 1:
            memorize_indexes.append(i)

    returned_df = apriori_table.loc[memorize_indexes]

    if returned_df.shape[0] != 0:
        returned_df['receipes'] = receipes

    return returned_df
