from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа №1',
            slug='test-slug',
            description='Описание тестовой группы №1'
        )
        for i in range(12):
            Post.objects.create(
                author=cls.author,
                group=cls.group,
                text=f'пост #{i} в группе "{cls.group.title}"'
            )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_post_create_adds_item_in_database(self):
        """ Проверка сохранения новых постов из формы """
        posts_count_before = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        posts_count_after = Post.objects.count()
        self.assertEqual(posts_count_before + 1, posts_count_after)

    def test_post_edit_changes_item_in_database(self):
        """ Проверка редактирования существующих постов из формы """
        post = Post.objects.create(
            author=self.author,
            group=self.group,
            text='Старый текст'
        )
        form_data = {
            "group": self.group.id,
            'text': 'Новый текст из формы'
        }
        self.author_client.post(
            reverse('posts:post_edit', args=[post.id]),
            data=form_data,
            follow=True
        )
        self.assertTrue(Post.objects.filter(
                        id=post.id,
                        text='Новый текст из формы').exists())
