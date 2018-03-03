from django.utils import timezone


class FriendlyCapabilitiesMixin():
    # Required until migration 0010 is squashed
    pass


class ExpiryCalculationMixin():
    @property
    def expires(self):
        return self.expiry_date is not None

    @property
    def has_expired(self):
        return self.expires and self.expiry_date < timezone.now().date()

    @property
    def days_till_expiry(self):
        if self.expiry_date is None:
            raise ValueError('days_till_expiry called with expiry_date=None')

        return (self.expiry_date - timezone.now().date().today()).days
