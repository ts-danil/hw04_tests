from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста'
        )

    def setUp(self):
        # Гостевой клиент
        self.guest_client = Client()
        # Авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Авторский клиент
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_all_page_exists(self):
        """Проверка корректности кодов ответа для всех страниц"""
        url_client_status = (('/',
                             self.guest_client,
                             HTTPStatus.OK
                              ),
                             ('/unexisting_page/',
                             self.guest_client,
                             HTTPStatus.NOT_FOUND
                              ),
                             (f'/group/{self.group.slug}/',
                              self.guest_client,
                              HTTPStatus.OK
                              ),
                             (f'/profile/{self.author.username}/',
                              self.guest_client,
                              HTTPStatus.OK
                              ),
                             (f'/posts/{self.post.id}/',
                              self.guest_client,
                              HTTPStatus.OK
                              ),
                             ('/create/',
                              self.authorized_client,
                              HTTPStatus.OK
                              ),
                             (f'/posts/{self.post.id}/edit/',
                              self.author_client,
                              HTTPStatus.OK))

        for url, client, status in url_client_status:
            response = client.get(url)
            with self.subTest(status=status):
                self.assertEqual(response.status_code, status)

    def test_create_redirect_from_guest_client(self):
        """Страница создания поста перенаправляет на страницу входа
        с гостевого клиента"""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/')

    def test_post_edit_redirect_from_guest_client(self):
        """Страница редактирования поста перенаправляет на страницу поста
        с гостевого клиента"""
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_post_edit_redirect_from_authorized_client(self):
        """Страница редактирования поста перенаправляет на страницу поста
        с авторизованного клиента"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны"""
        # Общедоступные адреса
        url_names_templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address, template in url_names_templates.items():
            with self.subTest(adress=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
        # Адреса ограниченного доступа
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
