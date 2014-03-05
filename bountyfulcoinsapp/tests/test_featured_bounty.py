import mock

from django.core.urlresolvers import reverse

from django_webtest import WebTest

from blockchain_adapter import blockchain
from bountyfulcoinsapp.models import FeaturedBounty, Address
from bountyfulcoinsapp.forms import BountySaveForm

from .common import SiteDataMixin
from .test_bounty import BountyCreateMixin


class TestFeaturedBounty(BountyCreateMixin, SiteDataMixin, WebTest):
    fixtures = ['users', 'bounties', 'addresses']

    def setUp(self):
        super(TestFeaturedBounty, self).setUp()
        self.data = self.good_data.copy()
        self.data['featured'] = True
        self.good_balance = 2.0
        self.bad_balance = 0.0001

    def test_no_assignable_addresses(self):
        Address.objects.get(verified_balance=0.00).delete()  # remove available
        create_form = self._get_bounty_form()
        self._fill_form(create_form, self.data)
        res = create_form.submit()
        self.assertFormError(res, 'form', 'featured',
                             BountySaveForm.no_addresses_error)

    def _get_featured(self, bounty):
        try:
            return bounty.featured
        except FeaturedBounty.DoesNotExist:
            return None

    def test_create_and_featured_bounty(self):
        bounty = self._create_bounty(self.data)
        self.assertIsNotNone(self._get_featured(bounty),
                             'A featured bounty does not exist')

    def test_create_multiple_addresses_available(self):
        Address.objects.create(address_id='randomnewaddress123')
        bounty = self._create_bounty(self.data)
        self.assertIsNotNone(self._get_featured(bounty),
                             'A featured bounty does not exist')
        # attempt saving with many addresses existing
        change_form = self._get_bounty_form(new=False, pk=bounty.pk)
        self.assertRedirects(change_form.submit(),
                             reverse('bounty_details', args=[bounty.pk]))

    def test_create_no_addresses_available(self):
        Address.objects.all().delete()
        self.assertRaises(
            Exception, self._create_bounty, self.data,
            'Featuring a bounty without available addresses should have '
            'raised an exception')

    def test_featured_bounty_disabled(self):
        bounty = self._create_bounty(self.data)
        self.assertIsNotNone(self._get_featured(bounty),
                             'A featured bounty does not exist')

        # blockchain.get_balance_url = mock.Mock()
        blockchain.get_balance = mock.Mock(return_value=0.0001)
        self.assertFalse(bounty.featured.enabled,
                         'Feature should not be enabled')

    def test_featured_bounty_enabled(self):
        bounty = self._create_bounty(self.data)
        self.assertIsNotNone(self._get_featured(bounty),
                             'A featured bounty does not exist')
        bounty.featured.address.verified_balance = 2.0
        self.assertTrue(bounty.featured.enabled, 'Feature should be enabled')

    def test_sync_address_balance(self):
        addr = Address.objects.get(verified_balance__gt=0)
        self.assertEqual(addr.verified_balance, 1.00)

        # force sync_verified_balance to return what we want
        blockchain.get_balance = mock.Mock(return_value=2.0)
        self.assertTrue(addr.sync_verified_balance())
        addr = Address.objects.get(pk=addr.pk)  # fetch again
        self.assertEqual(addr.verified_balance, 2.00)
