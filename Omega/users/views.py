import pytz
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.utils.translation import activate
from users.forms import UserExtendedForm, UserForm, EditUserForm
from users.models import Notifications, Extended
from Omega.vars import LANGUAGES, PRIORITY
from django.shortcuts import get_object_or_404
from jobs.utils import JobAccess
from jobs.models import Job
from django.middleware.csrf import get_token
from users.notifications import NotifyData
from service.models import Scheduler
from reports.models import ReportRoot


def user_signin(request):
    activate(request.LANGUAGE_CODE)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                try:
                    Extended.objects.get(user=user)
                    if len(Job.objects.all()) > 0:
                        return HttpResponseRedirect(reverse('jobs:tree'))
                except ObjectDoesNotExist:
                    pass
                return HttpResponseRedirect(reverse('population'))
            else:
                login_error = _("Account has been disabled")
        else:
            login_error = _("Incorrect username or password")
        return render(request, 'users/login.html',
                      {'login_errors': login_error})
    else:
        return render(request, 'users/login.html')


def user_signout(request):
    logout(request)
    return HttpResponseRedirect(reverse('users:login'))


def register(request):
    activate(request.LANGUAGE_CODE)

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserExtendedForm(data=request.POST)
        user_tz = request.POST.get('timezone', None)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            profile = profile_form.save(commit=False)
            profile.user = user
            if user_tz:
                profile.timezone = user_tz
            try:
                profile.save()
            except:
                raise ValidationError("Can't save user to the database!")
            user.save()
            return HttpResponseRedirect(reverse('users:login'))
    else:
        user_form = UserForm()
        profile_form = UserExtendedForm()

    return render(request, 'users/register.html',
                  {
                      'user_form': user_form,
                      'profile_form': profile_form,
                      'timezones': pytz.common_timezones,
                  })


@login_required
def edit_profile(request):
    activate(request.user.extended.language)

    if request.method == 'POST':
        user_form = EditUserForm(data=request.POST, request=request,
                                 instance=request.user)
        profile_form = UserExtendedForm(
            data=request.POST,
            instance=request.user.extended
        )
        user_tz = request.POST.get('timezone')
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            new_pass = request.POST.get('new_password')
            do_redirect = False
            if len(new_pass):
                user.set_password(new_pass)
                do_redirect = True
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            if user_tz:
                profile.timezone = user_tz
            profile.save()

            if do_redirect:
                return HttpResponseRedirect(reverse('users:login'))
            else:
                return HttpResponseRedirect(reverse('users:edit_profile'))
    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = UserExtendedForm(instance=request.user.extended)

    schedulers = Scheduler.objects.filter(need_auth=True)
    return render(
        request,
        'users/edit-profile.html',
        {
            'user_form': user_form,
            'tdata': NotifyData(request.user),
            'profile_form': profile_form,
            'profile_errors': profile_form.errors,
            'user_errors': user_form.errors,
            'timezones': pytz.common_timezones,
            'LANGUAGES': LANGUAGES,
            'schedulers': schedulers,
            'priorities': PRIORITY
        })


def index_page(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('jobs:tree'))
    return HttpResponseRedirect(reverse('users:login'))


@login_required
def show_profile(request, user_id=None):
    activate(request.user.extended.language)
    if len(user_id) == 0:
        return HttpResponseRedirect(reverse('jobs:tree'))
    target = get_object_or_404(User, pk=int(user_id))
    user_activity = target.jobhistory.all().order_by('-change_date')[:18]
    activity = []
    for act in user_activity:
        act_comment = act.comment
        small_comment = act_comment
        if len(act_comment) > 47:
            small_comment = act_comment[:50] + '...'
        new_act = {
            'date': act.change_date,
            'comment': act_comment,
            'small_comment': small_comment,
            'version': act.version,
            'job_name': act.name
        }
        if JobAccess(request.user, act.job).can_view():
            new_act['href'] = reverse('jobs:job', args=[act.job_id])
        activity.append(new_act)
    user_tz = request.user.extended.timezone
    return render(request, 'users/showProfile.html', {
        'target': target,
        'activity': activity,
        'user_tz': user_tz,
        'num_of_solving_jobs': len(ReportRoot.objects.filter(user=target))
    })


def psi_signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponse('')
            else:
                return JsonResponse({'error': 'Account has been disabled'})
        return JsonResponse({'error': 'Incorrect username or password'})
    else:
        get_token(request)
        return HttpResponse('')


def psi_signout(request):
    logout(request)
    return HttpResponse('')


@login_required
def save_notifications(request):
    activate(request.user.extended.language)
    if request.method == 'POST':
        notifications = request.POST.get('notifications', '[]')
        self_ntf = json.loads(request.POST.get('self_ntf', False))
        try:
            new_ntf = request.user.notifications
        except ObjectDoesNotExist:
            new_ntf = Notifications()
            new_ntf.user = request.user
        new_ntf.settings = notifications
        new_ntf.self_ntf = self_ntf
        new_ntf.save()
        return JsonResponse({'status': 0, 'message': _('Saved')})
    return JsonResponse({'status': 1, 'message': _('Unknown error')})
