from django.test import Client, TestCase


class CoreTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404_template(self):
        self.assertTemplateUsed(self.guest_client.get('404'), 'core/404.html')
