from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.edit import CreateView, UpdateView

from registration.views import RegistrationView as BaseRegistrationView

from bountyfulcoinsapp.forms import (RegistrationForm, SearchForm,
                                     BountySaveForm)
from bountyfulcoinsapp.models import Link, Bounty, SharedBounty, Tag


class RegistrationView(BaseRegistrationView):
    form_class = RegistrationForm

    def register(self, request, username, email, password1, **cleaned_data):
        User.objects.create_user(username=username, email=email,
                                 password=password1)

    def get_success_url(self, request=None, user=None):
        return reverse('registration_complete')


# Views for the Home Page
def main_page(request):
    shared_bounties = SharedBounty.objects.order_by('-votes')[:50]
    return render(request, 'main_page.html', {
        'shared_bounties': shared_bounties
    })


# View of the User Page.
def user_page(request, username):
    user = get_object_or_404(User, username=username)
    bounties = user.bounty_set.order_by('-id')
    variables = RequestContext(request, {
        'bounties': bounties,
        'username': username,
        'show_tags': True,
        'show_edit': username == request.user.username,
    })
    return render_to_response('user_page.html', variables)


class BountyReusableMixin(object):
    template_name = 'bounty_save.html'
    model = Bounty
    form_class = BountySaveForm

    def get_initial(self):
        initial = self.initial
        if self.object:
            initial['url'] = self.object.link.url
            tags = self.object.tags.all()
            if tags:
                initial['tags'] = ", ".join(tags.values_list('name', flat=True))
        return initial

    def _process_form(self, form):
        data = form.cleaned_data
        bounty = form.save(commit=False)
        bounty.user = self.request.user
        bounty.link, created = Link.objects.get_or_create(url=data['url'])
        tag_names = data['tags'].split(',')
        bounty.tags.clear()  # remove existing tags before assigning new ones
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name.strip())
            bounty.tags.add(tag)
        bounty.save()
        self.object = bounty

        if data['share']:
            shared, created = SharedBounty.objects.get_or_create(
                bounty=bounty
            )

            if created:
                shared.users_voted.add(self.request.user)
                shared.save()

    def form_valid(self, form):
        self._process_form(form)
        return HttpResponseRedirect(self.get_success_url())


class BountyCreate(BountyReusableMixin, CreateView):
    pass


class BountyChange(BountyReusableMixin, UpdateView):
    pass


def tag_page(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    bounties = tag.bounties.order_by('-id')
    variables = RequestContext(request, {
        'bounties': bounties,
        'tag_name': tag_name,
        'show_tags': True,
        'show_user': True
    })
    return render_to_response('tag_page.html', variables)


def tag_cloud_page(request):
    MAX_WEIGHT = 5
    tags = Tag.objects.order_by('name')
    # Calculate tag, minimum and maximum counts.
    min_count = max_count = tags[0].bounties.count()
    for tag in tags:
        tag.count = tag.bounties.count()
        if tag.count < min_count:
            min_count = tag.count
        if max_count < tag.count:
            max_count = tag.count
    # Calculate count range. Avoid dividing by zero
    range = float(max_count - min_count)
    if range == 0.0:
        range = 1.0
    # Calculate the tag weights.
    for tag in tags:
        tag.weight = int(
            MAX_WEIGHT * (tag.count - min_count) / range
        )
    variables = RequestContext(request, {
        'tags': tags
    })
    return render_to_response('tag_cloud_page.html', variables)


def search_page(request):
    form = SearchForm()
    bounties = []
    show_results = False
    if 'query' in request.GET:
        show_results = True
        query = request.GET['query'].strip()
        if query:
            keywords = query.split()
            q = Q()
            for keyword in keywords:
                q = q & Q(title__icontains=keyword)
            form = SearchForm({'query': query})
            bounties = Bounty.objects.filter(q)[:10]
    variables = RequestContext(request, {
        'form': form,
        'bounties': bounties,
        'show_results': show_results,
        'show_tags': True,
        'show_user': True
    })
    if 'ajax' in request.GET:
        return render_to_response('bounty_list.html', variables)
    else:
        return render_to_response('search.html', variables)


@login_required
def bounty_vote_page(request):
    if 'id' in request.GET:
        try:
            id = request.GET['id']
            shared_bounties = SharedBounty.objects.get(id=id)
            user_voted = shared_bounties.users_voted.filter(
                username=request.user.username
            )
            if not user_voted:
                shared_bounties.votes += 1
                shared_bounties.users_voted.add(request.user)
                shared_bounties.save()
        except SharedBounty.DoesNotExist:
            raise Http404('Bounty not found')
    if 'HTTP_REFERER' in request.META:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    return HttpResponseRedirect('/')


def popular_page(request):
    today = datetime.today()
    yesterday = today - timedelta(1)
    shared_bounties = SharedBounty.objects.filter(
        date__gt=yesterday
    )
    shared_bounties = shared_bounties.order_by(
        '-votes'
    )[:50]

    variables = RequestContext(request, {
        'shared_bounties': shared_bounties
    })
    return render_to_response('popular_page.html', variables)

    # View for the Logout Page


def about_page(request):
    return render_to_response('about.html')
