from statsmodels.stats.power import GofChisquarePower


class ChecksProcessor:
    def __init__(self, data):
        self.data = data
        self.variants = data["variant_id"].unique()

    def check_user_independence(self):
        experiment_variants = self.data.groupby(["user_id", "experiment_name"])[
            "variant_id"
        ].nunique()
        independent = all(experiment_variants == 1)
        return independent

    def check_experiment_independence(self):
        experiment_variants = self.data.groupby(["experiment_name"])[
            "event_name"
        ].nunique()
        independent = all(experiment_variants == 1)
        return independent

    def check_variation(self):
        grouped = self.data.groupby("variant_id")["with_purchase"]
        variations = grouped.apply(lambda x: x.mean() * (1 - x.mean()))
        return variations.to_dict()

    def check_sample_size(self, alpha=0.05, power=0.8):
        sample_sizes = self.data.groupby("variant_id")["with_purchase"].count()
        adequacy = {}
        for variant, size in sample_sizes.items():
            effect_size = 0.1
            power_analysis = GofChisquarePower()
            required_n = power_analysis.solve_power(
                effect_size=effect_size, nobs=None, alpha=alpha, power=power
            )
            adequacy[variant] = size >= required_n
        return adequacy

    def run_all_checks(self, alpha=0.05, power=0.8):
        if len(self.variants) == 1:
            return {
                "num_of_variants": int(len(self.variants)),
            }
        else:
            return {
                "num_of_variants": int(len(self.variants)),
                "user_independence": self.check_user_independence(),
                "experiment_independence": self.check_experiment_independence(),
                "variations": self.check_variation(),
                "sample_size_adequacy": self.check_sample_size(alpha, power),
            }
