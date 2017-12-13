import re

EMAIL_PATTERN = '(?P<email>.+@.+\..+)'


def parse_email_from_uid(uid):
    (name, comment, email) = parse_uid_parts(uid)
    return email


def parse_uid_parts(uid):

    name, comment, email = (None, None, None)

    patterns = [
        r'^(?P<name>.*?) \((?P<comment>.*)\) <' + EMAIL_PATTERN + '>$',
        r'^(?P<name>.*?) <' + EMAIL_PATTERN + '>$',
        r'^' + EMAIL_PATTERN + '$',
    ]

    for pattern in patterns:
        match = re.match(pattern, uid)

        if match is None:
            continue  # next pattern

        if not roughly_validate_email(match.group('email')):
            continue  # next pattern

        name = match.groupdict().get('name', None)
        comment = match.groupdict().get('comment', None)
        email = match.groupdict().get('email', None)
        break

    return (name, comment, email)


def roughly_validate_email(email):
    try:
        (_, hostname) = email.split('@', 1)
    except ValueError:
        return False

    return roughly_validate_hostname(hostname)


def roughly_validate_hostname(hostname):
    if len(hostname) > 255:
        return False

    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly 0 or 1 dot from the right

    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)

    parts = hostname.split(".")

    if not parts:
        return False

    if parts[-1] == 'onion':
        return False

    return all(allowed.match(x) for x in parts)
