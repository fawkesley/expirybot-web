from django.core.serializers.json import DjangoJSONEncoder


class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        try:
            return obj._json()
        except AttributeError:
            return DjangoJSONEncoder.default(self, obj)
