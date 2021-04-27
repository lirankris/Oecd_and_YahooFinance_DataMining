import sys
import os
import pandas as pd
from itertools import zip_longest as zl
cwd = os.getcwd()
sys.path.append(f'{cwd}\DataFrames')
sys.path.append(f'{cwd}\DataFrames\CreateTools')

from Convert2Currency import ConvertToUSD
from CreateLogger import Log


def sorted_dfs(df1, df2, df3, CleanLogger):
    CleanLogger.info('Starting 2 sort dfs by values...')

    seo = ['NABS06', 'NABS08', 'NABS124', 'NABS134']
    variable = ['QP', 'EX', 'IM', 'QC', 'ST', 'FE', 'BF',
                'FO', 'OU', 'QP__MA', 'QP__SCA', 'QP__VL']
    commodity = ['WT', 'MA', 'BD', 'ET', 'VL', 'OCG', 'MOL', 'SBE', 'SCA']

    G_df = df1[df1.SEO.isin(seo)].sort_values(
        by=['YEAR', 'SEO', 'COUNTRY'], ignore_index=True)
    A_df = df2[(df2.COMMODITY.isin(commodity)) & (df2.VARIABLE.isin(variable))].sort_values(
        by=['YEAR', 'VARIABLE', 'COMMODITY', 'COUNTRY'], ignore_index=True)
    CleanLogger.debug('Finished sort values by SEO & COMMODITY & VARIABLE')

    # GBARD
    #      R&D related to Agricultural and veterinary sciences - financed by General university funds.
    #      R&D related to Agricultural and veterinary sciences - financed other then the General university funds.
    #      Total government investment in industry and production.
    #      Total government investment in Agricultural R&D.

    # AgriOut
    #     Commodity:
    #         Cereals_and_Oilseeds = Wheat, Maize, Other coarse grains, Vegetable oils.
    #         Sugar = Molasses, Sugar beet, Sugar cane.
    #         Biofuel = Ethanol, Biodiesel.

    # Variables:
    #         Balance = Production, Imports, Consumption, Exports, Ending stocks.
    #         Uses = Feed, Food, Biofuel use, Other use,
    #                 Ethanol production from maize,
    #                 Ethanol production from sugar cane,
    #                 Biodiesel production from vegetable oil.
    #         Ratio = Human consumption per capita.

    return G_df, A_df, df3


def Clean_DataFrames(df1, df2, df3, CleanLogger):
    CleanLogger.info('Starting drop/rename...')
    # ---------------------------------------------drop------------------------------------------------------ #
    # df1:
    for count, curr in enumerate(df1.MEASURE):
        if curr != 'MIO_NAC':
            df1.drop(count, inplace=True)
    df1.drop(["MEASURE"], axis=1, inplace=True)
    df1.dropna(axis=0, inplace=True)
    CleanLogger.debug('drop rows that not contains MIO_NAC in column: MEASURE & \
                      Drop the MEASURE column from GBARD df')
    # df2:
    # Drop from main df's all the rows which contain aggregation of contries.
    df2.dropna(axis=0, inplace=True)
    for c in ['OECD', 'EUN', 'NOA', 'EUR', 'OCD', 'AFR', 'LAC', 'WLD', 'BRICS']:
        df2.drop(df2[df2.LOCATION == c].index, axis=0, inplace=True)
    CleanLogger.debug("drop rows that not contains 'OECD', 'EUN', 'NOA', \
     'EUR', 'OCD', 'AFR', 'LAC', 'WLD', 'BRICS' in column: LOCATION")

    # df3:
    df3.dropna(axis=0, inplace=True)
    df3.reset_index(drop=True, inplace=True)
    for count, ind in enumerate(df3.TRANSACT):
        if ind != 'EXCH':
            df3.drop(count, inplace=True)
    df3.drop(["TRANSACT", "MEASURE"], axis=1, inplace=True)
    CleanLogger.debug("drop rows that not contains 'EXCH' & columns: MEASURE, TRANSACT")

    # ----------------------------------rename & replace------------------------------------------------------ #
    # Rename different columns in more suitable name.
    df1.rename(columns={"Value": "GBARD_Values", "Date": "YEAR"}, inplace=True)

    df2.rename(columns={"LOCATION": "COUNTRY", "Date": "YEAR",
                        "Value": "Agri_Values"}, inplace=True)

    df3.rename(columns={"LOCATION": "COUNTRY", "Date": "YEAR",
                        "Value": "Exchange_Values"}, inplace=True)
    # ------------------------------------------------------------------------------------------ #
    LT_index = df2.index[df2.COMMODITY.isin([

    ])].tolist()
    df2.loc[LT_index, 'Agri_Values'] = df2.Agri_Values / (1143.25)

    return df1, df2, df3


def df2USA_currency(df, ExcRate, CleanLogger):
    CleanLogger.info('Starting Converting currency 2 USD...')
    #  //CURRENCY:
    #   UD - Australian Dollar        ILS - New Israeli Sheqel
    #   EUR - Euro                    RON - Romanian Leu
    #   USD - US Dollar               RUB - Russian Ruble
    #   MXN - Mexican Peso            ARS - Argentine Peso
    #   SEK - Swedish Krona           KRW - Won
    #   NOK - Norwegian Krone         CZK - Czech Koruna
    #   CAD - Canadian Dollar         TWD - New Taiwan Dollar
    #   GBP - Pound Sterling          PLN - Zloty
    #   DKK - Danish Krone            HUF - Forint
    #   NZD - New Zealand Dollar      TRY - Turkish Lira
    #   JPY - Yen                     CLP - Chilean Peso
    #   CHF - Swiss Franc             No CURRENCY
    #   ISK - Iceland Krona

    yearList_datetime = sorted(list(df.YEAR.unique()))
    yearList = [pd.to_datetime(year).year for year in yearList_datetime]
    countrylist = list(ExcRate.COUNTRY.unique())
    seoList = list(df.SEO.unique())
    count_contry = []

    new_df = pd.DataFrame(columns=['COUNTRY', 'SEO', 'YEAR', 'GBARD_Values'])
    # ------------------------------------------------------------------------------------------ #
    for seo in seoList:
        # NABS06, NABS08, NABS124, NABS134
        for contry in df.COUNTRY.unique():
            try:
                contry_df = df[(df.COUNTRY == contry) & (df.SEO == seo)]  # Single Country & seo Dataframe.
                contry_years = [pd.to_datetime(year).year for year in list(contry_df.YEAR.unique())]
                first_year = contry_years[0]
                last_year = contry_years[len(contry_years) - 1]
            except IndexError as err:
                CleanLogger.warning(f'ContryD ataFrame: {contry}, is Empty')
                CleanLogger.warning(f'Getting an error: {err}')
                print(f'Contry DataFrame: {contry}, is Empty')
                continue
            else:
                # ------------------------------------------------------------------------------------------ #
                for year in yearList:
                    # ----------------------------------df year empty row--------------------------------------- #
                    if (last_year < year or year < first_year) and contry in countrylist:
                        new_set = pd.DataFrame({'COUNTRY': contry,
                                                'SEO': seo,
                                                'YEAR': year,
                                                'GBARD_Values': [0]})

                        new_df.append(new_set, ignore_index=True)

                    # ---------------------------------contry in countrylist----------------------------------- #
                    elif (last_year >= year or year >= first_year) and contry in countrylist:
                        try:
                            if year not in list(ExcRate.YEAR[ExcRate.COUNTRY == contry].unique()) \
                                    and contry != 'TWN':
                                print("Can't convert this currency")
                            else:
                                currValue = list(ExcRate.Exchange_Values[(ExcRate.COUNTRY == contry)
                                                                         & (ExcRate.YEAR == year)])[0]
                            value2replace = df[(df.COUNTRY == contry) & (df.YEAR == year) & (df.SEO == seo)].GBARD_Values
                            newValue = value2replace / currValue
                            new_set = pd.DataFrame({'COUNTRY': contry,
                                                    'SEO': seo,
                                                    'YEAR': year,
                                                    'GBARD_Values': newValue})
                            new_df.append(new_set, ignore_index=True)

                        except IndexError:
                            if contry not in count_contry:
                                count_contry.append(contry)

                        except ValueError:
                            if contry not in count_contry:
                                count_contry.append(contry)

                    # ----------------------------------currency empty value------------------------------------ #
                    elif (last_year < year or year < first_year) and contry not in countrylist:
                        new_set = pd.DataFrame({'COUNTRY': contry,
                                                'SEO': seo,
                                                'YEAR': year,
                                                'GBARD_Values': [0]})
                        new_df.append(new_set, ignore_index=True)

                    else:
                        try:
                            if contry == 'TWN':
                                currValue = ConvertToUSD('TWN', year)
                                value2replace = df[(df.COUNTRY == contry) & (df.YEAR == year) & (df.SEO == seo)].GBARD_Values
                                newValue = value2replace / currValue
                                new_set = pd.DataFrame({'COUNTRY': contry,
                                                        'SEO': seo,
                                                        'YEAR': year,
                                                        'GBARD_Values': newValue})
                                new_df.append(new_set, ignore_index=True)

                        except Exception as exc:
                            print(exc)
                            print("\nNoop...that's the end of the rode guys...")
                            continue

    # ------------------------------Try currency valu0e implamantion----------------------------- #
    new_df.reset_index(inplace=True, drop=True)
    new_df.sort_values(by=['COUNTRY', 'YEAR'], inplace=True)

    return new_df


def checkIfnull(df_list, df_names, CleanLogger):
    CleanLogger.info('Starting Cleaning null values...')
    for df, df_name in zip(df_list, df_names):
        col_names = list(df.keys())  # get the names of the columns Series.
        Cnull = df.isnull().sum()  # sum all the nan values per columns in df.
        Colvalue = Cnull.values  # get the amount of the nan values.
        for c in range(len(Colvalue)):  # loop through the list, example:[0 0 0 0 0 0 6 0]
            if Colvalue[c]:  # not 0 (False)
                print(f'df name: {df_name}\ncolumn name: {col_names[c]}\namount of null: {Colvalue[c]}')
                ValSeries = df[col_names[c]]  # specific null value place.
                if Colvalue[c] < len(
                        ValSeries) * 0.05:  # if the amount of nan values is less then 5% of the series(column).
                    try:
                        print(f'The mean value of {col_names[c]} is: {ValSeries.mean():.2f} \n')
                        ValSeries.fillna(ValSeries.mean(), inplace=True)  # fill all the nan values by the mean value.
                    except TypeError:
                        print(
                            f'Column {col_names[c]} dont contains integer values, filling it with: No {col_names[c]}\n')
                        ValSeries.fillna(f'No {col_names[c]}', inplace=True)
                        continue


def adjusted_DataFrames(df1, df2, df3):
    CleanLogger = Log('Clean_log', cwd)

    CleanLogger.info('Starting DataFrames Cleaning...')
    CleanLogger.debug('Going to Clean_DataFrames function')
    sort_df1, sort_df2, sort_df3 = Clean_DataFrames(df1, df2, df3, CleanLogger)

    CleanLogger.debug('Going to sorted_dfs function')
    G_df, A_df, D_df = sorted_dfs(sort_df1, sort_df2, sort_df3, CleanLogger)

    CleanLogger.debug('Going to checkIfnull function')
    checkIfnull([G_df, A_df, df3],
                ['GBARD', 'Agricultural', 'curr2USD'], CleanLogger)

    CleanLogger.debug('Going to df2USA_currency function')
    G2usd_df = df2USA_currency(G_df, D_df, CleanLogger)

    return G2usd_df, A_df
