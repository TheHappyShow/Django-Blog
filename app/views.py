from datetime import timedelta
from django.utils import timezone
import pyotp
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.template.context_processors import request
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from unicodedata import category
from django.conf import settings
from .utils import send_otp_to_email, sort_articles
from .models import Article, Category, Comment
from .forms import ArticleCreateForm, RegistrationForm, LoginForm, CommentForm, OTPForm


class ArticleListView(ListView):
    model = Article
    template_name = 'app/feed.html'
    context_object_name = 'articles'
    paginate_by = 2


    def get_queryset(self):
        queryset = Article.objects.all()
        status = self.request.GET.get('status')

        return sort_articles(queryset, status)

class ArticleSearchView(ListView):
    model = Article
    template_name = 'app/search_feed.html'
    context_object_name = 'articles'
    paginate_by = 1


    def get_queryset(self):
        queryset = Article.objects.all()
        title = self.request.GET.get('q')  # Получаем title для поиска
        status = self.request.GET.get('status')
        if title:
            queryset = queryset.filter(title__icontains=title)

        return sort_articles(queryset, status)


class ArticleCatListView(ListView):
    model = Article
    template_name = 'app/category_feed.html'
    context_object_name = 'articles'
    paginate_by = 2

    def get_queryset(self):
        slug = self.kwargs.get('slug')  # Получаем slug
        cat = Category.objects.get(slug=slug)  # Получаем объект Категории
        queryset = Article.objects.filter(category=cat.id)
        status = self.request.GET.get('status')

        return sort_articles(queryset, status)


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'app/post_detail.html'
    context_object_name = 'article'

    slug_field = 'slug'         # имя поля в модели
    slug_url_kwarg = 'slug'     # имя переменной в URL

    def get_context_data(self, **kwargs):
        slug = self.kwargs.get(self.slug_url_kwarg)  # берём slug из URL
        article = self.object
        article.view_count += 1
        article.save(update_fields=['view_count']) # update_fields=['view_count'] позволяет обновить только view_count ( См. Модель Article )
        context = super().get_context_data(**kwargs) # Здесь мы добавляем context_object_name = 'article' в наш контекст
        context['comments'] = Comment.objects.filter(article=article)

        return context



class ArticleCreateView(LoginRequiredMixin, CreateView):
    template_name = 'app/post_create.html'
    form_class = ArticleCreateForm
    success_url = reverse_lazy('feed')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        return redirect(reverse_lazy('feed'))

class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    template_name = 'app/post_update.html'
    form_class = ArticleCreateForm
    success_url = reverse_lazy('feed')

    slug_field = 'slug'         # имя поля в модели
    slug_url_kwarg = 'slug'     # имя переменной в URL

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (request.user != obj.user) and (not request.user.is_superuser):
            return HttpResponseForbidden("У вас нет доступа к редактированию")
        return super().dispatch(request, *args, **kwargs)


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('feed')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (request.user != obj.user) and (not request.user.is_superuser):
            return HttpResponseForbidden("У вас нет доступа к удалению")
        return super().dispatch(request, *args, **kwargs)


# Коментарии

class CommentCreateView(LoginRequiredMixin, CreateView):
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        # Здесь мы получаем объект Article по slug из URL (например, /articles/some-title/)
        # и сохраняем его в self.article, чтобы можно было использовать в других методах
        self.article = get_object_or_404(Article, slug=kwargs.get('slug'))
        # Затем вызываем оригинальный метод dispatch у родительского класса (обязательно)
        return super().dispatch(request, *args, **kwargs)

    # Метод вызывается, если форма прошла валидацию (форма заполнена правильно)
    def form_valid(self, form):
        # Указываем, к какой статье относится комментарий
        form.instance.article = self.article
        # Привязываем комментарий к текущему пользователю
        form.instance.user = self.request.user
        # Передаём выполнение дальше (сохранение объекта и т.п.)
        return super().form_valid(form)

    # Куда перенаправить пользователя после успешной отправки формы
    def get_success_url(self):
        # Перенаправляем обратно на страницу статьи
        return reverse('post-detail', kwargs={'slug': self.article.slug})


# Всё что связано с авторизацией
class CustomRegistrationView(FormView):
    template_name = 'app/registration.html'
    success_url = reverse_lazy('otp')
    form_class = RegistrationForm


    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])  # шифруем!
        user.save()
        login(self.request, user)  # автоматически логиним
        return super().form_valid(form)


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'app/login.html'
    success_url = reverse_lazy('feed')


    def get_success_url(self):
        return self.success_url


class OTPVerifyView(FormView):
    template_name = 'app/otp_verify.html'
    form_class = OTPForm
    success_url = reverse_lazy('feed')

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.verified:
            now = timezone.now()

            # Проверка: прошло ли 3 минуты с момента последней отправки
            if user.otp_created_at and now - user.otp_created_at < timedelta(minutes=3):
                messages.warning(request, "Вы уже запрашивали код недавно. Попробуйте снова через пару минут.")
            else:
                send_otp_to_email(user)
                messages.success(request, "OTP отправлен на вашу почту.")

            return super().get(request, *args, **kwargs)
        else:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        otp_code = form.cleaned_data.get('otp_code')
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(otp_code):
            user.verified = True
            user.save()
            messages.success(self.request, "OTP успешно подтвержден.")
            return redirect('feed')
        else:
            messages.error(self.request, "Неверный код OTP.")
            print('неверно')
            return self.form_invalid(form)


