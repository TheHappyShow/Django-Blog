from django import forms
from .models import Article, Comment, User
from django.contrib.auth import authenticate


class ArticleCreateForm(forms.ModelForm):
    """
    Форма добавления статей на сайте
    """
    class Meta:
        model = Article
        fields = ('title', 'category', 'description', 'thumbnail')

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы под Bootstrap
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})

        self.fields['description'].widget.attrs.update({'class': 'form-control django_ckeditor_5'})
        self.fields['description'].required = False


class LoginForm(forms.Form):
    login = forms.CharField(label="Логин или Email")
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # достаём request, если передан
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        login = cleaned_data.get('login')
        password = cleaned_data.get('password')


        if login and password:
            # Пробуем найти пользователя
            user = authenticate(request=self.request, username=login, password=password)
            if user is None:
                # Возможно, это email — пробуем другой способ
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user_obj = User.objects.get(email=login)
                    user = authenticate(request=self.request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is None:
                raise forms.ValidationError("Неверный логин или пароль")

            self.user = user  # сохраняем пользователя

        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Подтверждение пароля")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 6:
            raise forms.ValidationError('Пароль слишком короткий')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Имя пользователя уже занято")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email уже используется")
        return email

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

        widgets = {
            'departure_post': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Комментарий'})
        }


class OTPForm(forms.Form):
    otp_code = forms.CharField(label="Введите код из приложения", max_length=6)