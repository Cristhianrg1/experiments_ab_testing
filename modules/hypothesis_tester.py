import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests

def create_contingency_table(data):
    return pd.crosstab(data["variant_id"], data["with_purchase"])

def chi_square_test(contingency_table):
    chi2, p, _, _ = chi2_contingency(contingency_table)
    return chi2, p

def z_test(data, winner_id, variant2):
    data_v1 = data[data['variant_id'] == winner_id]
    data_v2 = data[~data['variant_id'] == winner_id]
    
    conversions_v1 = data_v1['with_purchase'].sum()
    total_v1 = data_v1['with_purchase'].count()
    conversions_v2 = data_v2['with_purchase'].sum()
    total_v2 = data_v2['with_purchase'].count()
    
    count = [conversions_v1, conversions_v2]
    nobs = [total_v1, total_v2]
    stat, pval = proportions_ztest(count, nobs, alternative="larger")
    return stat, pval

def post_hoc_test(data):
    variants = data["variant_id"].unique()
    pvals = []
    for i, v1 in enumerate(variants):
        for v2 in variants[i + 1:]:
            subset = data[data["variant_id"].isin([v1, v2])]
            count = subset.groupby("variant_id")["with_purchase"].sum().values
            nobs = subset.groupby("variant_id")["with_purchase"].count().values
            stat, pval = proportions_ztest(count, nobs)
            pvals.append(pval)
    reject, pvals_corrected, _, _ = multipletests(pvals, method="bonferroni")
    return reject, pvals_corrected

def determine_winner(data):
    variants = data["variant_id"].unique()
    winner = None
    significant_difference = False

    if len(variants) == 2:
        rates = data.groupby("variant_id")["with_purchase"].mean()
        winner = rates.idxmax()
        _, pval = z_test(data, winner)
        significant_difference = pval < 0.05
    else:
        contingency_table = create_contingency_table(data)
        chi2, pval = chi_square_test(contingency_table)
        if pval < 0.05:
            significant_difference = True
            reject, _ = post_hoc_test(data)
            if any(reject):
                significant_variants = [variants[i] for i, r in enumerate(reject) if r]
                max_rate = 0
                for variant in significant_variants:
                    rate = data[data["variant_id"] == variant]["with_purchase"].mean()
                    if rate > max_rate:
                        max_rate = rate
                        winner = variant
            else:
                rates = data.groupby("variant_id")["with_purchase"].mean()
                winner = rates.idxmax()
        else:
            rates = data.groupby("variant_id")["with_purchase"].mean()
            winner = rates.idxmax()

    return winner, pval, significant_difference
