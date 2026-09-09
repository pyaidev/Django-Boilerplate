from drf_spectacular.authentication import SessionScheme


class CSRFSessionScheme(SessionScheme):
    target_class = "apps.accounts.views.CSRFSessionAuthentication"
    name = "csrfCookieAuth"
