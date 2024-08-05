import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests


def create_contingency_table(data):
    return pd.crosstab(data["variant_id"], data["with_purchase"])


def chi_square_test(contingency_table):
    chi2, p, _, _ = chi2_contingency(contingency_table)
    return chi2, p


def z_test(data):
    purchase_counts = data.groupby("variant_id")["with_purchase"].sum()
    total_counts = data.groupby("variant_id")["with_purchase"].count()
    count = purchase_counts.values
    nobs = total_counts.values
    stat, pval = proportions_ztest(count, nobs)
    return stat, pval


def post_hoc_test(data):
    variants = data["variant_id"].unique()
    pvals = []
    for i, v1 in enumerate(variants):
        for v2 in variants[i + 1 :]:
            subset = data[data["variant_id"].isin([v1, v2])]
            count = subset.groupby("variant_id")["with_purchase"].sum().values
            nobs = subset.groupby("variant_id")["with_purchase"].count().values
            stat, pval = proportions_ztest(count, nobs)
            pvals.append(pval)
    reject, pvals_corrected, _, _ = multipletests(pvals, method="bonferroni")
    return reject, pvals_corrected


def determine_winner(data):
    variants = data["variant_id"].unique()
    if len(variants) == 2:
        _, pval = z_test(data)
        if pval < 0.05:
            rates = data.groupby("variant_id")["with_purchase"].mean()
            winner = rates.idxmax()
            return winner
    else:
        contingency_table = create_contingency_table(data)
        chi2, pval = chi_square_test(contingency_table)
        if pval < 0.05:
            reject, pvals_corrected = post_hoc_test(data)
            if any(reject):
                significant_variants = [variants[i] for i, r in enumerate(reject) if r]
                max_rate = 0
                winner = None
                for variant in significant_variants:
                    rate = data[data["variant_id"] == variant]["with_purchase"].mean()
                    if rate > max_rate:
                        max_rate = rate
                        winner = variant
                return winner
    return None
