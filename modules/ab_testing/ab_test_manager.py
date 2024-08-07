from modules.ab_testing.ab_test_analyzer import ABTestAnalyzer
from modules.ab_testing.checks_processor import ChecksProcessor


class ABTestManager:
    def __init__(self, data):
        self.data = data
        self.analyzer = ABTestAnalyzer(data)
        self.checks = ChecksProcessor(data)

    def run_analysis(self):
        ab_checks = self.checks.run_all_checks()
        ab_results = self.analyzer.determine_winner()

        return ab_checks, ab_results