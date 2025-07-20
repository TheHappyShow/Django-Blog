from django.db import models
from django.contrib.auth.models import User, AbstractUser
from ckeditor.fields import RichTextField
from django_ckeditor_5.fields import CKEditor5Field
from pytils.translit import slugify

# Create your models here.
class User(AbstractUser):
    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    otp_created_at = models.DateTimeField(auto_now=True)
    verified = models.BooleanField(default=False)

class Category(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название категории')
    slug = models.SlugField(unique=True, null=True)
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

class Article(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=64, verbose_name='Заголовок')
    description = CKEditor5Field(verbose_name='Полное описание', config_name='extends')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, default=None, verbose_name='Миниатюра')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    slug = models.SlugField(unique=True, null=True)
    view_count = models.IntegerField(verbose_name='Количество просмотров', default=0)

    class Meta:
        verbose_name = 'Артикул'
        verbose_name_plural = 'Артиклы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Article, self).save(*args, **kwargs)

class Comment(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    article = models.ForeignKey(Article, verbose_name='Статья', on_delete=models.CASCADE)
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_updated = models.BooleanField(default=False, verbose_name='Обновлён')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Коментарии'

    def __str__(self):
        return self.text[:32]