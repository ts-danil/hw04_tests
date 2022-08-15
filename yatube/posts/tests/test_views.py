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
            group=cls.group,
            text='Тестовый текст поста'
        )
        cls.posts_num = 12
        cls.post_per_page = 10

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
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
        self.assertEqual(posts, page_obj_context)

    def test_group_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        page_obj = list(self.group.posts.select_related('group',
                        'author').all()[:self.post_per_page])
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug}))
        group_context = response.context['group']
        page_obj_context = response.context['page_obj'].object_list
        self.assertEqual(group_context, self.group)
        self.assertEqual(page_obj_context, page_obj)

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
        self.assertEqual(author_context, author)
        self.assertEqual(page_obj_context, page_obj)
        self.assertEqual(posts_count_context, posts_count)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:post_detail',
                                         kwargs={'post_id': self.post.id}))
        post_context = response.context['post']
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
        response = self.guest_client.get(reverse('posts:index'))
        page_obj_context = response.context['page_obj'].object_list
        self.assertIn(test_post, page_obj_context)
        response = self.guest_client.get(reverse('posts:profile',
                                         kwargs={'username':
                                                 (test_post.author.username)}))
        page_obj_context = response.context['page_obj'].object_list
        self.assertIn(test_post, page_obj_context)
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug':
                                                 (test_post.group.slug)}))
        page_obj_context = response.context['page_obj'].object_list
        self.assertIn(test_post, page_obj_context)
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug}))
        page_obj_context = response.context['page_obj'].object_list
        self.assertNotIn(test_post, page_obj_context)

    def test_paginator(self):
        """Тестирование пагинатора"""
        posts = [Post(text=f'Пост № {post_num}',
                      author=self.author,
                      group=self.group)
                 for post_num in range(self.posts_num)]
        Post.objects.bulk_create(posts)
        urls_with_paginator = ('/',
                               f'/group/{self.group.slug}/',
                               f'/profile/{self.author.username}/')
        page_posts = ((1, 10), (2, 3))
        for url_address in urls_with_paginator:
            for page, posts_count in page_posts:
                response = self.guest_client.get(url_address, {"page": page})
                page_obj_context = response.context['page_obj'].object_list
                with self.subTest():
                    self.assertEqual(len(page_obj_context), posts_count)
