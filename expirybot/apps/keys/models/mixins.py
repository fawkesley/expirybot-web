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


class FingerprintFormatMixin():
    @property
    def human_fingerprint(self):
        if len(self.fingerprint) == 40:
            return '{} {} {} {} {}  {} {} {} {} {}'.format(  # nbsp
                self.fingerprint[0:4],
                self.fingerprint[4:8],
                self.fingerprint[8:12],
                self.fingerprint[12:16],
                self.fingerprint[16:20],
                self.fingerprint[20:24],
                self.fingerprint[24:28],
                self.fingerprint[28:32],
                self.fingerprint[32:36],
                self.fingerprint[36:40]
            )
        else:
            return self.fingerprint

    @property
    def zero_x_fingerprint(self):
        return '0x{}'.format(self.fingerprint)
