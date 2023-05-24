from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests (TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.any_user = User.objects.create_user(username='any_user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.any_user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_response_code(self):
        response_codes = (
            ('/', self.guest_client, HTTPStatus.OK),
            (f'/group/{self.group.slug}/', self.guest_client, HTTPStatus.OK),
            (f'/profile/{self.author.username}/',
                self.guest_client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/', self.guest_client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/edit/',
                self.guest_client, HTTPStatus.FOUND),
            ('/create/', self.guest_client, HTTPStatus.FOUND),
            ('/nonexistent_page/', self.guest_client, HTTPStatus.NOT_FOUND),
            (f'/posts/{self.post.id}/edit/',
                self.authorized_client, HTTPStatus.FOUND),
            ('/create/', self.authorized_client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/edit/',
                self.author_client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/comment/',
                self.guest_client, HTTPStatus.FOUND),
        )
        for response_code in response_codes:
            with self.subTest(response_code=response_code):
                response = response_code[1].get(response_code[0])
                self.assertEqual(response.status_code, response_code[2])

    def test_comment(self):
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_correct_templates(self):
        templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author_client.get(address),
                    template
                )

    def test_edit_redirect(self):
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_create_redirect(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
