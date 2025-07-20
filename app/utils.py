import pyotp
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta
from django.utils import timezone

def send_otp_to_email(user):
    # Генерируем секрет, если его ещё нет
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()

    # Генерируем OTP-код
    otp = pyotp.TOTP(user.otp_secret).now()

    # Отправляем email с кодом
    send_mail(
        subject="Ваш OTP-код",
        message=f"Ваш одноразовый код подтверждения: {otp}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )

    # Сохраняем время отправки и сам секрет
    user.otp_created_at = timezone.now()
    user.save()


def sort_articles(queryset, status):
    match status:
        case 'most_viewed':
            return queryset.order_by('-view_count')
        case 'least_viewed':
            return queryset.order_by('view_count')
        case 'newest':
            return queryset.order_by('-updated_at')
        case 'oldest':
            return queryset.order_by('updated_at')
        case _:
            return queryset