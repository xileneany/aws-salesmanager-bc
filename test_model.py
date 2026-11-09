import copy
import math
import unittest
from finance_model import calculate, load_config, phase_pricing, hourly_outage_cost

class TestFenixFinancialModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_config()
        cls.r = calculate(cls.c)
    def test_price_by_phase(self):
        _, totals = phase_pricing(self.c)
        self.assertEqual(totals, {1:520000,2:620000,3:360000})
    def test_hourly_outage_cost(self):
        self.assertEqual(hourly_outage_cost(self.c['financial_inputs']), 20000)
    def test_baselines_and_target(self):
        self.assertEqual(self.r['shared']['annual_it_savings_target'], 3000000)
        self.assertEqual(self.r['shared']['annual_aws_spend'],2160000)
        self.assertEqual(self.r['shared']['three_year_incremental_tco'],1824000)
    def test_scenario_annual_values(self):
        expected = {'Conservador':(216000,120000,192000,528000), 'Base':(324000,240000,480000,1044000), 'Alto':(432000,360000,768000,1560000)}
        for name, values in expected.items():
            s=self.r['scenarios'][name]
            self.assertEqual((s['aws_annual_savings'],s['avoided_outage_annual_margin'],s['credit_annual_margin'],s['annual_stabilized_benefit']),values)
    def test_ramp_and_roi(self):
        expected = {'Conservador':(298000,1354000),'Base':(556000,2644000),'Alto':(814000,3934000)}
        for name, values in expected.items():
            s=self.r['scenarios'][name]
            self.assertEqual((s['year1_benefits'],s['three_year_benefits']), values)
            self.assertAlmostEqual(s['three_year_roi'], (values[1]-1824000)/1824000)
    def test_it_budget_not_achieved(self):
        self.assertEqual(self.r['scenarios']['Base']['steady_net_it_savings'],162000)
        self.assertEqual(self.r['scenarios']['Base']['remaining_it_target_gap'],2838000)
        self.assertEqual(self.r['scenarios']['Base']['year1_total_it_cash_spend'],21284000)
    def test_commercial_reserve_separate_by_default(self):
        self.assertEqual(self.r['shared']['project_investment'], 1500000)
        self.assertEqual(self.r['shared']['commercial_reserve'], 300000)
        self.assertEqual(self.r['shared']['approved_budget'], 1800000)
        c=copy.deepcopy(self.c); c['financial_inputs']['include_reserve_in_roi']=True
        r2=calculate(c)
        self.assertEqual(r2['shared']['three_year_incremental_tco'],2124000)
        self.assertEqual(r2['scenarios']['Base']['three_year_tco'],2124000)
    def test_lower_realization_changes_roi(self):
        c=copy.deepcopy(self.c);c['financial_inputs']['benefit_realization_factor']=0.8
        r2=calculate(c)
        self.assertLess(r2['scenarios']['Base']['three_year_roi'],self.r['scenarios']['Base']['three_year_roi'])
    def test_avoid_double_count_project_scope(self):
        c=copy.deepcopy(self.c)
        c['phase_line_items'][0]['hours']+=1
        with self.assertRaises(ValueError):
            calculate(c)

if __name__=='__main__':unittest.main()
