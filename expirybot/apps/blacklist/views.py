from django.views.generic import DetailView

from .models import ExampleModel


class ExampleModelDetailView(DetailView):
    template_name = 'blacklist/example_model_detail.html'
    model = ExampleModel
    context_object_name = 'example_model'
