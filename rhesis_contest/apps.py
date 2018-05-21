from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RhesisContestConfig(AppConfig):
    name = 'rhesis_contest'
    verbose_name = _('诗词对决')
