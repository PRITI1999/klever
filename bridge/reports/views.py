from urllib.parse import quote
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from bridge.vars import JOB_STATUS
from bridge.utils import unparallel_group, print_err
from jobs.ViewJobData import ViewJobData
from jobs.utils import JobAccess
from marks.tables import ReportMarkTable
from marks.models import UnsafeTag, SafeTag, MarkSafe, MarkUnsafe, MarkUnknown
from reports.UploadReport import UploadReport
from marks.utils import MarkAccess
from reports.models import *
from reports.utils import *
from django.utils.translation import ugettext as _, activate, string_concat
from reports.etv import GetSource, GetETV


@login_required
def report_component(request, job_id, report_id):
    activate(request.user.extended.language)

    try:
        job = Job.objects.get(pk=int(job_id))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[404]))

    if not JobAccess(request.user, job).can_view():
        return HttpResponseRedirect(reverse('error', args=[400]))
    try:
        report = ReportComponent.objects.get(pk=int(report_id))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[504]))

    duration = None
    status = 1
    if report.finish_date is not None:
        duration = report.finish_date - report.start_date
        status = 2

    view_args = [request.user, report]
    report_attrs_data = [request.user, report]
    if request.method == 'POST':
        view_type = request.POST.get('view_type', None)
        if view_type == '2':
            view_args.append(request.POST.get('view', None))
            view_args.append(request.POST.get('view_id', None))
        elif view_type == '3':
            report_attrs_data.append(request.POST.get('view', None))
            report_attrs_data.append(request.POST.get('view_id', None))

    unknown_href = None
    try:
        unknown = ReportUnknown.objects.get(parent=report)
        unknown_href = reverse('reports:leaf',
                               args=['unknown', unknown.pk])
        status = 3
    except ObjectDoesNotExist:
        pass

    return render(
        request,
        'reports/ReportMain.html',
        {
            'report': report,
            'duration': duration,
            'resources': report_resources(report, request.user),
            'computer': computer_description(report.computer.description),
            'reportdata': ViewJobData(*view_args),
            'parents': get_parents(report),
            'SelfAttrsData': ReportTable(*report_attrs_data).table_data,
            'TableData': ReportTable(*report_attrs_data, table_type='3'),
            'status': status,
            'unknown': unknown_href,
        }
    )


@login_required
def report_list(request, report_id, ltype, component_id=None, verdict=None, tag=None, problem=None, mark=None):
    activate(request.user.extended.language)

    try:
        report = ReportComponent.objects.get(pk=int(report_id))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[504]))

    if not JobAccess(request.user, report.root.job).can_view():
        return HttpResponseRedirect(reverse('error', args=[400]))

    list_types = {
        'unsafes': '4',
        'safes': '5',
        'unknowns': '6'
    }

    if ltype == 'safes':
        title = _("All safes")
        page_title = _('Safes')
        if tag is not None:
            title = string_concat(_("Safes"), ': ', tag.tag)
        elif verdict is not None:
            for s in SAFE_VERDICTS:
                if s[0] == verdict:
                    title = string_concat(_("Safes"), ': ', s[1])
                    break
        elif mark is not None:
            title = _('Safe reports marked by')
    elif ltype == 'unsafes':
        title = _("All unsafes")
        page_title = _('Unsafes')
        if tag is not None:
            title = string_concat(_("Unsafes"), ': ', tag.tag)
        elif verdict is not None:
            for s in UNSAFE_VERDICTS:
                if s[0] == verdict:
                    title = string_concat(_("Unsafes"), ': ', s[1])
                    break
        elif mark is not None:
            title = _('Unsafe reports marked by')
    else:
        title = _("All unknowns")
        page_title = _('Unknowns')
        if isinstance(problem, UnknownProblem):
            title = string_concat(_("Unknowns"), ': ', problem.name)
        elif problem == 0:
            title = string_concat(_("Unknowns without marks"))
        elif mark is not None:
            title = _('Unknown reports marked by')
    if mark is not None:
        mark_href = ' <a href="%s">%s</a>' % (
            reverse('marks:edit_mark', args=[ltype[:-1], mark.pk]), mark.identifier[:10]
        )
        title = string_concat(title, mark_href)

    report_attrs_data = [request.user, report]
    if request.method == 'POST':
        if request.POST.get('view_type', None) == list_types[ltype]:
            report_attrs_data.append(request.POST.get('view', None))
            report_attrs_data.append(request.POST.get('view_id', None))

    return render(
        request,
        'reports/report_list.html',
        {
            'report': report,
            'page_title': page_title,
            'parents': get_parents(report),
            'TableData': ReportTable(
                *report_attrs_data, table_type=list_types[ltype],
                component_id=component_id, verdict=verdict, tag=tag, problem=problem, mark=mark),
            'view_type': list_types[ltype],
            'title': title
        }
    )


@login_required
def report_list_tag(request, report_id, ltype, tag_id):
    try:
        if ltype == 'unsafes':
            tag = UnsafeTag.objects.get(pk=int(tag_id))
        else:
            tag = SafeTag.objects.get(pk=int(tag_id))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[704]))
    return report_list(request, report_id, ltype, tag=tag)


@login_required
def report_list_by_verdict(request, report_id, ltype, verdict):
    return report_list(request, report_id, ltype, verdict=verdict)


@login_required
def report_list_by_mark(request, report_id, ltype, mark_id):
    tables = {
        'safes': MarkSafe,
        'unsafes': MarkUnsafe,
        'unknowns': MarkUnknown
    }
    try:
        mark = tables[ltype].objects.get(pk=mark_id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[604]))
    return report_list(request, report_id, ltype, mark=mark)


@login_required
def report_unknowns(request, report_id, component_id):
    return report_list(request, report_id, 'unknowns', component_id=component_id)


@login_required
def report_unknowns_by_problem(request, report_id, component_id, problem_id):
    problem_id = int(problem_id)
    if problem_id == 0:
        problem = 0
    else:
        try:
            problem = UnknownProblem.objects.get(pk=problem_id)
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('error', args=[804]))
    return report_list(request, report_id, 'unknowns', component_id=component_id, problem=problem)


@login_required
def report_leaf(request, leaf_type, report_id):
    activate(request.user.extended.language)

    tables = {
        'unknown': ReportUnknown,
        'safe': ReportSafe,
        'unsafe': ReportUnsafe
    }
    if leaf_type not in tables:
        return HttpResponseRedirect(reverse('error', args=[500]))

    try:
        report = tables[leaf_type].objects.get(pk=int(report_id))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[504]))

    if not JobAccess(request.user, report.root.job).can_view():
        return HttpResponseRedirect(reverse('error', args=[400]))

    template = 'reports/report_leaf.html'
    etv = None
    if leaf_type == 'unsafe':
        template = 'reports/report_unsafe.html'
        etv = GetETV(report.error_trace)
        if etv.error is not None:
            print_err(etv.error)
            return HttpResponseRedirect(reverse('error', args=[505]))
    return render(
        request, template,
        {
            'type': leaf_type,
            'title': report.identifier.split('##')[-1],
            'report': report,
            'parents': get_parents(report),
            'SelfAttrsData': ReportTable(request.user, report).table_data,
            'MarkTable': ReportMarkTable(request.user, report),
            'etv': etv,
            'can_mark': MarkAccess(request.user, report=report).can_create()
        }
    )


@login_required
def report_etv_full(request, report_id):
    activate(request.user.extended.language)

    try:
        report = ReportUnsafe.objects.get(pk=int(report_id))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[504]))

    if not JobAccess(request.user, report.root.job).can_view():
        return HttpResponseRedirect(reverse('error', args=[400]))

    etv = GetETV(report.error_trace)
    if etv.error is not None:
        print_err(etv.error)
        return HttpResponseRedirect(reverse('error', args=[505]))
    return render(
        request, 'reports/etv_fullscreen.html',
        {
            'report': report,
            'etv': etv
        }
    )


@unparallel_group(['mark', 'report'])
def upload_report(request):
    if not request.user.is_authenticated():
        return JsonResponse({'error': 'You are not signed in'})
    if request.method != 'POST':
        return JsonResponse({'error': 'Get request is not supported'})
    if 'job id' not in request.session:
        return JsonResponse({'error': 'The job id was not found in session'})
    try:
        job = Job.objects.get(pk=int(request.session['job id']))
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'The job was not found'})
    except ValueError:
        return JsonResponse({'error': 'Unknown error'})
    if not JobAccess(request.user, job).klever_core_access():
        return JsonResponse({
            'error': "User '%s' don't have access to upload report for job '%s'" %
                     (request.user.username, job.identifier)
        })
    if job.status != JOB_STATUS[2][0]:
        return JsonResponse({'error': 'Reports can be uploaded only for processing jobs'})
    try:
        data = json.loads(request.POST.get('report', '{}'))
    except Exception as e:
        print_err(e)
        return JsonResponse({'error': 'Can not parse json data'})
    archive = None
    for f in request.FILES.getlist('file'):
        archive = f
    err = UploadReport(job, data, archive).error
    if err is not None:
        return JsonResponse({'error': err})
    return JsonResponse({})


@login_required
def get_component_log(request, report_id):
    report_id = int(report_id)
    try:
        report = ReportComponent.objects.get(pk=int(report_id))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[504]))

    if not JobAccess(request.user, report.root.job).can_view():
        return HttpResponseRedirect(reverse('error', args=[400]))

    if report.log is None:
        return HttpResponseRedirect(reverse('error', args=[500]))
    logname = report.component.name + '.log'
    response = HttpResponse(report.log.file.read(), content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s"' % quote(logname)
    return response


@login_required
def get_log_content(request, report_id):
    report_id = int(report_id)
    try:
        report = ReportComponent.objects.get(pk=int(report_id))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('error', args=[504]))

    if not JobAccess(request.user, report.root.job).can_view():
        return HttpResponseRedirect(reverse('error', args=[400]))

    if report.log is None:
        return HttpResponseRedirect(reverse('error', args=[500]))
    return HttpResponse(report.log.file.read().decode('utf8'))


@login_required
def get_source_code(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Unknown error'})
    if 'report_id' not in request.POST:
        return JsonResponse({'error': 'Unknown error'})
    if 'file_name' not in request.POST:
        return JsonResponse({'error': 'Unknown error'})

    result = GetSource(request.POST['report_id'], request.POST['file_name'])
    if result.error is not None:
        return JsonResponse({'error': result.error + ''})
    filename = request.POST['file_name']
    if len(filename) > 50:
        filename = '.../' + filename[-50:].split('/', 1)[-1]
    return JsonResponse({
        'content': result.data,
        'name': filename,
        'fullname': request.POST['file_name']
    })