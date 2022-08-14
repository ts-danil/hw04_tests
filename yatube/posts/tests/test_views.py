from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа №1',
            slug='test-slug',
            description='Описание тестовой группы №1'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста'
        )
        cls.posts_num = 12
        cls.post_per_page = 10
        posts = []
        for post_num in range(cls.posts_num):
            posts.append(
                Post(
                    text=f'{str(post_num)*100}',
                    author=cls.author,
                    group=cls.group
                )
            )
        Post.objects.bulk_create(posts)

    def setUp(self):
        # Гостевой клиент
        self.guest_client = Client()
        # Авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Авторский клиент
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Общедоступные адреса
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            ('posts/group_list.html'),
            reverse('posts:profile', kwargs={
                'username': self.author.username}): ('posts/profile.html'),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            ('posts/post_detail.html')
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        # Адреса ограниченного доступа
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')
        response = self.author_client.get(reverse('posts:post_edit', kwargs={
            'post_id': self.post.id}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_homepage_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        page_obj_context = response.context['page_obj'].object_list
        posts = list(Post.objects.select_related(
            'group', 'author').all()[:self.post_per_page])
        # На главной находятся необходимые посты
        self.assertEqual(posts, page_obj_context)
        # Проверка паджинатора по количеству постов
        self.assertEqual(len(page_obj_context), self.post_per_page)

    def test_group_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        page_obj = list(self.group.posts.select_related('group',
                        'author').all()[:self.post_per_page])
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug}))
        group_context = response.context['group']
        page_obj_context = response.context['page_obj'].object_list
        # Передана необходимая группа
        self.assertEqual(group_context, self.group)
        # В группе находятся необходимые посты
        self.assertEqual(page_obj_context, page_obj)
        # Проверка паджинатора по количеству постов
        self.assertEqual(len(page_obj_context), self.post_per_page)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        author = self.author
        posts_count = author.posts.select_related('author').count()
        page_obj = list(author.posts.select_related('author')[:10])
        response = self.guest_client.get(reverse('posts:profile',
                                         kwargs={'username': author.username}))
        author_context = response.context['author']
        posts_count_context = response.context['posts_count']
        page_obj_context = response.context['page_obj'].object_list
        # Передан необходимый автор
        self.assertEqual(author_context, author)
        # В профиле находятся необходимые посты
        self.assertEqual(page_obj_context, page_obj)
        # Проверка количества постов у автора
        self.assertEqual(posts_count_context, posts_count)
        # Проверка паджинатора по количеству постов
        self.assertEqual(len(page_obj_context), self.post_per_page)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:post_detail',
                                         kwargs={'post_id': self.post.id}))
        post_context = response.context['post']
        # Проверка необходимого поста
        self.assertEqual(post_context, self.post)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_edit',
                                          kwargs={'post_id': (self.post.id)}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Поле формы явяляется экземпляром указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Поле формы явяляется экземпляром указанного класса
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_location(self):
        new_group = Group.objects.create(
            title='Новая группа',
            slug='new-group',
            description='Описание новой группы'
        )
        test_post = Post.objects.create(
            author=self.author,
            group=new_group,
            text='Пост для проверки расположения'
        )
        # Проверка поста на главной странице
        response = self.guest_client.get(reverse('posts:index'))
        page_obj_context = response.context['page_obj'].object_list
        self.assertIn(test_post, page_obj_context)
        # Проверка поста в профайле пользователя
        response = self.guest_client.get(reverse('posts:profile',
                                         kwargs={'username':
                                                 (test_post.author.username)}))
        page_obj_context = response.context['page_obj'].object_list
        self.assertIn(test_post, page_obj_context)
        # Проверка поста в выбранной группе
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug':
                                                 (test_post.group.slug)}))
        page_obj_context = response.context['page_obj'].object_list
        self.assertIn(test_post, page_obj_context)
        # Проверка отсутствия поста в другой группе
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug}))
        page_obj_context = response.context['page_obj'].object_list
        self.assertNotIn(test_post, page_obj_context)
