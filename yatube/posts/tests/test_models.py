from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длиннее пятнадцати символов',
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_names = (
            (group, group.title),
            (post, post.text[:15]),
        )
        for object_name in expected_object_names:
            with self.subTest(object_name=object_name):
                self.assertEqual(
                    str(object_name[0]), object_name[1]
                )
