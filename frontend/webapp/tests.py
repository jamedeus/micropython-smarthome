from django.test import TestCase

# Test offline page
class OverviewPageTests(TestCase):
    def test_overview_page_no_nodes(self):
        # Request page, confirm correct template used
        response = self.client.get('/offline/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/offline.html')
