"""
sentry.models.releasefile
~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2015 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from django.db import models

from sentry.db.models import BoundedPositiveIntegerField, FlexibleForeignKey, Model, sane_repr
from sentry.utils.hashlib import sha1_text


class ReleaseFile(Model):
    """
    A ReleaseFile is an association between a Release and a File.

    The ident of the file should be sha1(name) or
    sha1(name '@@' distribution.name) and must be unique per release.
    """
    __core__ = False

    organization = FlexibleForeignKey('sentry.Organization')
    project_id = BoundedPositiveIntegerField(null=True)
    release = FlexibleForeignKey('sentry.Release')
    file = FlexibleForeignKey('sentry.File')
    ident = models.CharField(max_length=40)
    name = models.TextField()
    distribution = FlexibleForeignKey('sentry.Distribution', null=True)

    __repr__ = sane_repr('release', 'ident')

    class Meta:
        unique_together = (('release', 'ident'),)
        app_label = 'sentry'
        db_table = 'sentry_releasefile'

    def save(self, *args, **kwargs):
        if not self.ident and self.name:
            dist = self.distribution and self.distribution.name or None
            self.ident = type(self).get_ident(self.name, dist)
        return super(ReleaseFile, self).save(*args, **kwargs)

    def update(self, *args, **kwargs):
        # If our name is changing, we must also change the ident
        if 'name' in kwargs and 'ident' not in kwargs:
            dist = kwargs.get('distribution') or self.distribution
            kwargs['ident'] = self.ident = type(self).get_ident(
                kwargs['name'], dist and dist.name or dist)
        return super(ReleaseFile, self).update(*args, **kwargs)

    @classmethod
    def get_ident(cls, name, distribution=None):
        if distribution is not None:
            return sha1_text(name + '@@' + distribution).hexdigest()
        return sha1_text(name).hexdigest()
