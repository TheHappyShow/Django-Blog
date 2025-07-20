from .forms import CommentForm
from .models import Category

def categories_context(request):
    return {
        'categories': Category.objects.all()
    }

def add_my_forms(request):
    return {
        'comment_form': CommentForm()
    }