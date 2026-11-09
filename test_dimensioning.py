import unittest
from finance_model import load_config
from dimensioning_model import calculate_dimensioning


class DimensioningCases(unittest.TestCase):
    def setUp(self):
        self.c = load_config()
        self.d = self.c['dimensioning']
        self.output = calculate_dimensioning(self.d, self.c['financial_inputs']['approved_modernization_budget'])

    def test_support_is_year_round_from_month_one(self):
        self.assertEqual(self.d['managed_months'], 12)
        self.assertEqual(self.d['managed_monthly_usd'], 10125)
        self.assertEqual(self.d['managed_months'] * self.d['managed_monthly_usd'], 121500)

    def test_scenarios_match_original_excel(self):
        expected = {'Conservador':531900, 'Base':664700, 'Alto':930300}
        for key, amount in expected.items():
            self.assertAlmostEqual(self.output['scenarios'][key]['total'], amount)

    def test_base_category_breakdown(self):
        expected = {'Cloud Security & Compliance':102000,
            'Cloud Operations & Reliability':205500,
            'Cloud Infrastructure & FinOps':35000,
            'Application Modernization':174000,
            'Data Integration & Analytics':105000,
            'DevOps & Developer Productivity':43200}
        self.assertEqual(self.output['base']['by_category'], expected)

    def test_assessment_and_managed_support_not_scaled(self):
        for s in self.output['scenarios'].values():
            self.assertEqual(s['assessment'], 12000)
            self.assertEqual(s['recurring'], 121500)

    def test_part_b_and_part_e_are_not_combined(self):
        self.assertEqual(self.c['financial_inputs']['first_year_project_cost'],1500000)
        self.assertEqual(self.output['base']['total'],664700)

    def test_editable_inputs_recalculate(self):
        self.d['service_lines'][0]['hours'] += 10
        new = calculate_dimensioning(self.d, 1800000)['base']['total']
        self.assertEqual(new, 664700 + 1500)

if __name__ == '__main__':
    unittest.main()
