from collections import defaultdict
from datetime import timedelta
from itertools import groupby
from operator import itemgetter
import logging

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from blockchain_adapter import blockchain

logger = logging.getLogger('bountyfulcoinsapp.models')


class Link(models.Model):
    url = models.URLField(unique=True)

    def __unicode__(self):
        return self.url


class Bounty(models.Model):
    class Meta:
        ordering = ['-id']
        verbose_name_plural = 'Bounties'

    link = models.ForeignKey(Link, verbose_name=_('Bounty URL'))
    title = models.CharField(_('Bounty Title'), max_length=200)
    user = models.ForeignKey(get_user_model())
    amount = models.DecimalField(_('Bounty Amount'), default=0.00,
                                 max_digits=20, decimal_places=2)
    currency = models.CharField(_('Bounty Currency'), default='BTC',
                                max_length=15)

    def __unicode__(self):
        return u'%s, %s' % (self.user.username, self.link.url)

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('bounty_details', args=[str(self.id)])

    def assign_tags_from_string(self, string):
        """
        Takes a list of string, by default sepererated by comma,
        and reassigns the tags to this bounty.
        """
        tag_names = string.split(',')
        self.tags.clear()  # remove existing tags before assigning new
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name.strip())
            self.tags.add(tag)

    @property
    def shared_date(self):
        try:
            return self.shared.last().date
        except SharedBounty.DoesNotExist:
            return None

    def share(self):
        """ Create a SharedBounty for this bounty """
        return SharedBounty.objects.get_or_create(bounty=self)

    def feature(self):
        """ Create a FeaturedBounty for this bounty """
        try:
            addr = Address.get_available_addresses().first()
        except Address.DoesNotExist:
            raise Exception('No assignable addresses found, '
                            'cannot feature this bounty')
        self.featured = FeaturedBounty.objects.create(address=addr, bounty=self)
        return self.featured

    @property
    def is_featured(self):
        try:
            return bool(self.featured)
        except FeaturedBounty.DoesNotExist:
            return False


class Tag(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=64, unique=True)
    bounties = models.ManyToManyField(Bounty, related_name='tags')

    def __unicode__(self):
        return self.name


class SharedBounty(models.Model):
    class Meta:
        ordering = ['-votes', '-date']
        verbose_name_plural = 'Shared bounties'

    bounty = models.ForeignKey(Bounty, unique=True, related_name='shared')
    date = models.DateTimeField(default=timezone.now)
    votes = models.IntegerField(default=1)
    users_voted = models.ManyToManyField(get_user_model())

    # if user decides to disable bounty later
    disabled = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s, %s' % (self.bounty, self.votes)


class Address(models.Model):
    name = models.CharField(max_length=255, blank=True)
    address_id = models.CharField(max_length=64, unique=True)

    verified_balance = models.DecimalField(default=0.00, max_digits=20,
                                           decimal_places=6)
    last_synced = models.DateTimeField(null=True, blank=True)

    @property
    def sync_required(self):
        if not settings.ADDRESSES_LIVE_SYNC:
            return False
        freq = timedelta(seconds=settings.ADDRESSES_SYNC_FREQUENCE)
        return (timezone.now() - self.last_synced) > freq

    def sync_verified_balance(self):
        """
        Using blockchain.info API get the latest balance of the Address.

        If a good result is returned, store it and update last_synced time.
        """
        res = blockchain.get_balance(self.address_id)
        if res is not None:
            self.verified_balance = res
            self.last_synced = timezone.now()
            self.save()
            return True
        return False

    @classmethod
    def get_available_addresses(cls):
        """
        Return assignable addresses, i.e: not related to a FeaturedBounty
        and have verified_balance of 0.00.
        """
        return cls.objects.filter(featured_bounty=None,
                                  verified_balance=0.00)

    @classmethod
    def bulk_create(cls, addr_list):
        """
        A helper method that inserts into the db the passed
        list of address dicts (excluding existing address ids).

        addr_list=[ {'name': 'abc', 'address_id': '1234'}, ... ]
        """
        # get and exclude dupes
        hashes = [a['address_id'] for a in addr_list]
        existing = cls.objects.filter(address_id__in=hashes).values_list(
            'address_id', flat=True)
        cls.objects.bulk_create([cls(**a) for a in addr_list
                                if a['address_id'] not in list(existing)])


class FeaturedBounty(models.Model):
    class Meta:
        ordering = ['-ctime']
        verbose_name_plural = 'Featured bounties'

    bounty = models.OneToOneField(Bounty, related_name='featured', null=True)
    address = models.OneToOneField(Address, unique=True,
                                   related_name='featured_bounty')
    ctime = models.DateTimeField(default=timezone.now)

    @property
    def enabled(self):
        if self.address.verified_balance >= settings.FEATURE_POST_MIN_CHARGE:
            return True
        elif self.address.last_synced is None or self.address.sync_required:
            res = self.address.sync_verified_balance()
            if res:  # balance was updated, check again
                return self.enabled
        # cannot verify payment was made, return False
        return False

    @classmethod
    def get_funded_entries(cls):
        return cls.objects.filter(
            address__verified_balance__gte=settings.FEATURE_POST_MIN_CHARGE)


def calculate_totals():
    bounties = sorted(
        list(SharedBounty.objects.values_list('bounty__currency',
                                              'bounty__amount')) +
        list(FeaturedBounty.get_funded_entries().values_list(
            'bounty__currency', 'bounty__amount')),
        key=itemgetter(0))
    totals = defaultdict(float)
    for currency, bounty_group in groupby(bounties, itemgetter(0)):
        totals[currency] += sum(float(b[1]) for b in bounty_group)
    return dict(totals)
