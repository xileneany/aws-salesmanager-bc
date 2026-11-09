"""Run: python -m unittest test_it_costs.py"""
import unittest
from finance_model import load_config,calculate
from it_costs import budget_and_savings


class ITCostsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=load_config()
        cls.it=budget_and_savings(cls.config)
        cls.project=calculate(cls.config)
    def test_total_budget_equals_20m(self):
        self.assertAlmostEqual(sum(self.it['budget'].values()),20_000_000,places=2)
    def test_aws_ratio_108pct(self):
        self.assertAlmostEqual(self.project['shared']['aws_share_it'], .108)
    def test_dc_electricity(self):
        expected=24*4*1.65*8760*.19
        self.assertAlmostEqual(self.it['dc']['electricity_usd'],expected,places=2)
    def test_dc_depreciation_not_saving(self):
        self.assertEqual(self.config['dc_guatemala']['savings_rates']['Depreciación (no caja)']['Alto'],0)
    def test_sensitivity_aws_consistent(self):
        import copy
        c = copy.deepcopy(self.config)
        c["financial_inputs"]["benefit_realization_factor"] = 0.8
        a = budget_and_savings(c)["scenario_savings"]["Base"]["aws_usd"]
        b = calculate(c)["scenarios"]["Base"]["aws_annual_savings"]
        self.assertEqual(a,b)
    def test_gap_remains_positive(self):
        for data in self.it['scenario_savings'].values():
            self.assertGreater(data['gap_usd'],0)
    def test_project_roi_excludes_other_it_savings(self):
        s=self.project['scenarios']['Base']
        self.assertAlmostEqual(s['three_year_benefits'],2644000)
        self.assertAlmostEqual(s['three_year_tco'],1824000)
    def test_phase_budgets(self):
        self.assertEqual(sum(self.project['shared']['phase_budgets'].values()),1500000)


if __name__=='__main__': unittest.main()
