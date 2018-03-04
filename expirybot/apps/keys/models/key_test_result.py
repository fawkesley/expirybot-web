import uuid
from django.db import models

from django.contrib.postgres.fields import JSONField

from .custom_json_encoder import CustomJSONEncoder

from expirybot.apps.keys.helpers.alerts import KEY_TESTS


class KeyTestResult(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    uuid = models.UUIDField(
        primary_key=True,
        null=False,
        default=uuid.uuid4,
        editable=False,
    )

    test_results = JSONField(
        # format: {'test_id_1': True, 'test_id_2': None}
        encoder=CustomJSONEncoder,
        default=dict
    )

    def get_test_results(self):

        for test in KEY_TESTS:
            pass_fail_none = self.test_results.get(test.test_id, None)

            result = test._asdict()
            result.update({'pass_fail_none': pass_fail_none})
            yield result

    def set_test_result(self, test_id, pass_fail_none):
        valid_test_ids = {t.test_id for t in KEY_TESTS}

        if test_id not in valid_test_ids:
            raise ValueError('Bad test id `{}`, expected one of: {}'.format(
                test_id, ', '.join(sorted(valid_test_ids))))

        if pass_fail_none not in [True, False, None]:
            raise ValueError('`{}` not one of True, False, None'.format(
                pass_fail_none))

        self.test_results[test_id] = pass_fail_none
        self.save()
