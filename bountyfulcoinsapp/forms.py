import io

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from captcha.fields import ReCaptchaField
from registration.forms import RegistrationForm as BaseRegistrationForm
from validate_email import validate_email

from bountyfulcoinsapp.models import Bounty, Address, Link
from bountyfulcoinsapp.utils import get_addresses_from_csv


class RegistrationForm(BaseRegistrationForm):
    recaptcha = ReCaptchaField(attrs={'theme': 'clean'})
    email_taken_error = _("This email address is already in use. Please "
                          "supply a different email address.")
    invalid_email_error = _("This email does not seem to be a valid address, "
                            "please try another mail address")

    def clean_email(self):
        """ Validate that the supplied email address does not exist """
        User = get_user_model()
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(self.email_taken_error)
        if settings.CHECK_MX or settings.CHECK_EMAIL_EXISTS:
            if not validate_email(self.cleaned_data['email'],
                                  check_mx=settings.CHECK_MX,
                                  verify=settings.CHECK_EMAIL_EXISTS):
                raise forms.ValidationError(self.invalid_email_error)
        return self.cleaned_data['email']


class BountySaveForm(forms.ModelForm):
    no_addresses_error = _('No assignable addresses found, '
                           'cannot feature the bounty at this time')

    class Meta:
        model = Bounty
        exclude = ('link', 'user',)
        fields = ('url', 'title', 'amount', 'currency', 'tags', 'share',
                  'featured')

    url = forms.URLField(
        label=u'Bounty URL',
        widget=forms.TextInput(attrs={'size': 128}),
    )
    tags = forms.CharField(
        label=u'Tags',
        required=False,
        widget=forms.TextInput(attrs={'size': 64}),
        help_text=_('Please enter a comma seperated list of tags')
    )
    share = forms.BooleanField(
        label=u'Post to Bountyful Home Page',
        required=False
    )
    featured = forms.BooleanField(
        label=u'Feature this Bounty on Bountyful Home Page',
        required=False,
    )

    def clean_currency(self):
        # TODO: validate currency is a valid choice ?
        currency = self.cleaned_data['currency']
        return currency.strip()

    def clean_featured(self):
        if self.cleaned_data['featured']:
            if not Address.get_available_addresses().exists():
                raise forms.ValidationError(self.no_addresses_error)
        return self.cleaned_data['featured']

    def save(self, user=None):
        """
        Parse tags, link and user and create/update links to related models
        """
        if not user:
            raise forms.ValidationError(
                _('Cannot save bouty without a user'))
        data = self.cleaned_data
        bounty = super(BountySaveForm, self).save(commit=False)
        bounty.user = user
        bounty.link, created = Link.objects.get_or_create(url=data['url'])

        bounty.save()  # first create this record to allow m2m access

        if data['tags']:  # ignore empty string
            bounty.assign_tags_from_string(data['tags'])

        if data['share']:
            shared, created = bounty.share()
            if created:
                shared.users_voted.add(user)

        if data['featured'] and not bounty.is_featured:
            bounty.feature()
        return bounty


class SearchForm(forms.Form):
    query = forms.CharField(
        label=u'Enter a keyword to search bounties',
        widget=forms.TextInput(attrs={'size': 32})
    )


class ImportAddressesForm(forms.Form):
    input_file = forms.FileField()

    def clean_input_file(self):
        ifile = self.cleaned_data['input_file']
        try:
            self.sio = io.StringIO(unicode(ifile.read()), newline=None)
        except UnicodeDecodeError:
            raise forms.ValidationError('Only plain text csv files are '
                                        'currently accepted')

    def save_addresses(self):
        addresses = get_addresses_from_csv(
            self.sio, headers=('_', 'address_id'))
        Address.bulk_create(addresses)
