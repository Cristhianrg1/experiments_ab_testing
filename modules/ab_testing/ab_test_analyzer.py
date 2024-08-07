import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, norm, t
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd


class ABTestAnalyzer:
    def __init__(self, data):
        self.data = data
        self.variants = data["variant_id"].unique()

    def create_contingency_table(self):
        return pd.crosstab(self.data["variant_id"], self.data["with_purchase"])

    def chi_square_test(self, contingency_table):
        chi2, p, _, _ = chi2_contingency(contingency_table)
        return chi2, p

    def z_test(self, winner_id):
        data_v1 = self.data[self.data["variant_id"] == winner_id]
        data_v2 = self.data[self.data["variant_id"] != winner_id]

        conversions_v1 = data_v1["with_purchase"].sum()
        total_v1 = data_v1["with_purchase"].count()
        conversions_v2 = data_v2["with_purchase"].sum()
        total_v2 = data_v2["with_purchase"].count()

        prop_v1 = conversions_v1 / total_v1
        prop_v2 = conversions_v2 / total_v2
        diff = prop_v1 - prop_v2

        count = [conversions_v1, conversions_v2]
        nobs = [total_v1, total_v2]
        stat, pval = proportions_ztest(count, nobs, alternative="larger")

        # Calculate the standard error
        se = np.sqrt(
            prop_v1 * (1 - prop_v1) / total_v1 + prop_v2 * (1 - prop_v2) / total_v2
        )

        # Calculate the 95% confidence interval
        z = norm.ppf(0.975)  # 95% confidence
        ci_low = diff - z * se
        ci_high = diff + z * se
        ci = (ci_low, ci_high)

        return float(stat), float(pval), ci

    def post_hoc_test(self):
        pvals = []
        for i, v1 in enumerate(self.variants):
            for v2 in self.variants[i + 1 :]:
                subset = self.data[self.data["variant_id"].isin([v1, v2])]
                count = subset.groupby("variant_id")["with_purchase"].sum().values
                nobs = subset.groupby("variant_id")["with_purchase"].count().values
                stat, pval = proportions_ztest(count, nobs)
                pvals.append(pval)
        reject, pvals_corrected, _, _ = multipletests(pvals, method="bonferroni")
        return reject.tolist(), pvals_corrected.tolist()

    def multi_variant_analysis(self):
        results = {}
        for variant in self.variants:
            group = self.data[self.data["variant_id"] == variant]
            prop = group["with_purchase"].mean()
            se = np.sqrt(prop * (1 - prop) / len(group))
            ci = norm.interval(0.95, loc=prop, scale=se)
            results[variant] = {
                "prop": prop,
                "ci": list(ci),
                "n": len(group),
                "conversions": int(group["with_purchase"].sum()),
            }

        self.data["purchase"] = self.data["with_purchase"].astype(float)

        model = ols("purchase ~ C(variant_id)", data=self.data).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)

        tukey = pairwise_tukeyhsd(self.data["purchase"], self.data["variant_id"])

        return results, anova_table, tukey

    def pairwise_comparisons(self):
        comparisons = []

        for i in range(len(self.variants)):
            for j in range(i + 1, len(self.variants)):
                group1 = self.data[self.data["variant_id"] == self.variants[i]]
                group2 = self.data[self.data["variant_id"] == self.variants[j]]

                effect = group2["with_purchase"].mean() - group1["with_purchase"].mean()
                se = np.sqrt(
                    group2["with_purchase"].var() / len(group2)
                    + group1["with_purchase"].var() / len(group1)
                )

                t_stat = effect / se
                df_total = len(group1) + len(group2) - 2
                p_value = 2 * (1 - t.cdf(abs(t_stat), df_total))

                comparisons.append(
                    {
                        "variant1": self.variants[i],
                        "variant2": self.variants[j],
                        "effect": effect,
                        "p_value": p_value,
                    }
                )

        return comparisons

    def rubin_causal_model(self):
        results = {}
        for variant in self.variants:
            group = self.data[self.data["variant_id"] == variant]
            prop = group["with_purchase"].mean()
            se = np.sqrt(prop * (1 - prop) / len(group))
            ci = norm.interval(0.95, loc=prop, scale=se)
            results[variant] = {
                "prop": prop,
                "ci": list(ci),
                "n": len(group),
                "conversions": int(group["with_purchase"].sum()),
            }

        causal_effects = {}
        for i, v1 in enumerate(self.variants):
            for v2 in self.variants[i + 1 :]:
                effect = results[v2]["prop"] - results[v1]["prop"]
                se = np.sqrt(
                    results[v2]["prop"] * (1 - results[v2]["prop"]) / results[v2]["n"]
                    + results[v1]["prop"] * (1 - results[v1]["prop"]) / results[v1]["n"]
                )
                ci = norm.interval(0.95, loc=effect, scale=se)
                causal_effects[f"{v1} vs {v2}"] = {"effect": effect, "ci": ci}

        return results, causal_effects

    def average_treatment_effect(self):
        if len(self.variants) != 2:
            raise ValueError(
                "ATE is typically calculated for two variants. Use pairwise comparisons for multiple variants."
            )

        control = self.variants[0]
        treatment = self.variants[1]

        control_data = self.data[self.data["variant_id"] == control]
        treatment_data = self.data[self.data["variant_id"] == treatment]

        control_mean = control_data["with_purchase"].mean()
        treatment_mean = treatment_data["with_purchase"].mean()

        ate = treatment_mean - control_mean

        se = np.sqrt(
            treatment_mean * (1 - treatment_mean) / len(treatment_data)
            + control_mean * (1 - control_mean) / len(control_data)
        )

        ci = norm.interval(0.95, loc=ate, scale=se)

        return {
            "ate": ate,
            "ci": list(ci),
            "control_mean": control_mean,
            "treatment_mean": treatment_mean,
        }

    def _determine_winner_one_variants(self):
        rates = self.data.groupby("variant_id")["with_purchase"].mean()
        winner = rates.idxmax()

        return {
            "winner": winner,
            "tests": None,
        }

    def _determine_winner_two_variants(self):
        rates = self.data.groupby("variant_id")["with_purchase"].mean()
        winner = rates.idxmax()

        z_stat, pval, ci = self.z_test(winner)
        significant_difference = pval < 0.05

        ate_results = self.average_treatment_effect()

        rcm_results, causal_effects = self.rubin_causal_model()

        return {
            "winner": winner,
            "tests": {
                "z-test": {
                    "p_value": pval,
                    "significant_difference": significant_difference,
                    "z_statistic": z_stat,
                    "ci": ci,
                },
                "average_treatment_effect": ate_results,
                "rubin_causal_model": rcm_results,
                "causal_effects": causal_effects,
            },
        }

    def _determine_winner_multi_variants(self):
        contingency_table = self.create_contingency_table()
        chi2, pval = self.chi_square_test(contingency_table)

        significant_difference = pval < 0.05
        winner = None

        if significant_difference:
            reject, _ = self.post_hoc_test()
            if any(reject):
                significant_variants = [
                    self.variants[i] for i, r in enumerate(reject) if r
                ]
                max_rate = 0
                for variant in significant_variants:
                    rate = self.data[self.data["variant_id"] == variant][
                        "with_purchase"
                    ].mean()
                    if rate > max_rate:
                        max_rate = rate
                        winner = variant
            else:
                rates = self.data.groupby("variant_id")["with_purchase"].mean()
                winner = rates.idxmax()
        else:
            rates = self.data.groupby("variant_id")["with_purchase"].mean()
            winner = rates.idxmax()

        variant_results, anova_table, tukey = self.multi_variant_analysis()
        pairwise_comp = self.pairwise_comparisons()

        return {
            "winner": winner,
            "tests": {
                "chi_square": {
                    "chi2": chi2,
                    "p_value": pval,
                    "significant_difference": significant_difference,
                },
                "variant_results": variant_results,
                "anova": {
                    "f_value": float(anova_table.loc["C(variant_id)", "F"]),
                    "p_value": float(anova_table.loc["C(variant_id)", "PR(>F)"]),
                },
                "tukey_hsd": tukey.summary().data[1:],
                "pairwise_comparisons": pairwise_comp,
            },
        }

    def determine_winner(self):
        if len(self.variants) == 1:
            return self._determine_winner_one_variants()
        elif len(self.variants) == 2:
            return self._determine_winner_two_variants()
        else:
            return self._determine_winner_multi_variants()
