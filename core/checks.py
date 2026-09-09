from django.conf import settings
from django.core.checks import Error, register


@register()
def check_rate_limits(app_configs, **kwargs):
    errors = []
    for scope, rate in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].items():
        try:
            count, period = rate.split("/")
            valid = int(count) > 0 and period in {"second", "minute", "hour", "day"}
        except (ValueError, AttributeError):
            valid = False
        if not valid:
            errors.append(
                Error(
                    f"Invalid rate for {scope}: expected a positive count/second, count/minute, count/hour or count/day.",
                    id="boilerplate.E001",
                )
            )
    return errors
