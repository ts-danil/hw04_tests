from django.forms import ModelForm, Select, Textarea

from .models import Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        labels = {'text': 'Текст сообщения', 'group': 'Группа'}
        widgets = {
            "text": Textarea(attrs={
                'class': 'form-control',
                'cols': '40',
                'rows': '10'
            }),
            "group": Select(attrs={
                'class': 'form-control'
            })
        }
