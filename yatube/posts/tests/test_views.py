import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author_name')
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
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsContextTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author_name')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста',
            group=cls.group,
            image=SimpleUploadedFile(
                name='test_image.gif',
                content=(b'\x47\x49\x46\x38\x39\x61\x02\x00'),
                content_type='image/gif'
            )
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_index_profile_groups_correct_context(self):
        addresses = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.post.author}),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        ]
        for address in addresses:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author
                post_text_0 = first_object.text
                post_group_0 = first_object.group
                post_image_0 = first_object.image
                self.assertEqual(post_author_0, self.post.author)
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_group_0, self.post.group)
                self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_correct_context(self):
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        ))
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_post_create_or_edit_correct_context(self):
        addresses = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        ]
        for address in addresses:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for k, expected in form_fields.items():
                    with self.subTest(k=k):
                        form_field = response.context.get('form').fields.get(k)
                        self.assertIsInstance(form_field, expected)


class PostsPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author_name')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        posts = [
            Post(
                author=self.author,
                text='Тестовый пост' * i,
                group=self.group)
            for i in range(settings.POSTS_PER_PAGE + 1)
        ]
        Post.objects.bulk_create(posts)

    def test_paginator(self):
        addresses = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.author}),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        ]
        pages_with_count_posts = (
            (1, settings.POSTS_PER_PAGE),
            (2, 1),
        )
        for address in addresses:
            for page, post_count in pages_with_count_posts:
                with self.subTest(address=address):
                    response = self.authorized_client.get(
                        address, {'page': page})
                    self.assertEqual(
                        len(response.context['page_obj']), post_count)


class CacheIndexTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author_name')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def test_cache_index(self):
        response_initial = self.guest_client.get(reverse('posts:index'))
        content_initial = response_initial.content
        response_initial.context['page_obj'][0].delete()
        response_following = self.guest_client.get(reverse('posts:index'))
        content_following = response_following.content
        self.assertEqual(content_initial, content_following)
        cache.clear()
        response_final = self.guest_client.get(reverse('posts:index'))
        content_final = response_final.content
        self.assertNotEqual(content_initial, content_final)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author_name')
        cls.follower = User.objects.create_user(username='follower')
        cls.non_follower = User.objects.create_user(username='non_follower')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста'
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.follower_client = Client()
        self.non_follower_client = Client()
        self.author_client.force_login(self.author)
        self.follower_client.force_login(self.follower)
        self.non_follower_client.force_login(self.non_follower)

    def test_follow(self):
        self.follower_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.author
            ).exists()
        )

    def test_unfollow(self):
        Follow.objects.create(user=self.follower, author=self.author)
        self.follower_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.author
            ).exists()
        )

    def test_following_page_for_follower(self):
        Follow.objects.create(user=self.follower, author=self.author)
        response_follower = self.follower_client.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post, response_follower.context['page_obj'])

    def test_following_page_for_non_follower(self):
        response_non_follower = self.non_follower_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(self.post, response_non_follower.context['page_obj'])
