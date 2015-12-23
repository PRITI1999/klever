from django.db import models
from django.contrib.auth.models import User
from bridge.vars import FORMAT, JOB_CLASSES, MARK_STATUS, MARK_UNSAFE, MARK_SAFE
from reports.models import Attr, ReportUnsafe, ReportSafe, ReportComponent,\
    Component, ReportUnknown, AttrName
from jobs.models import Job


class UnknownProblem(models.Model):
    name = models.CharField(max_length=15)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'cache_mark_unknown_problem'


# Tables with functions
class MarkUnsafeConvert(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=1000, default='')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'mark_unsafe_convert'


class MarkUnsafeCompare(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=1000, default='')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'mark_unsafe_compare'


# Abstract tables
class Mark(models.Model):
    identifier = models.CharField(max_length=255, unique=True)
    job = models.ForeignKey(Job, null=True, on_delete=models.SET_NULL,
                            related_name="%(class)s")
    format = models.PositiveSmallIntegerField(default=FORMAT)
    version = models.PositiveSmallIntegerField(default=1)
    type = models.CharField(max_length=1, choices=JOB_CLASSES, default='0')
    author = models.ForeignKey(User, related_name="%(class)s", null=True,
                               on_delete=models.SET_NULL)
    status = models.CharField(max_length=1, choices=MARK_STATUS, default='0')
    is_modifiable = models.BooleanField(default=True)
    change_date = models.DateTimeField(auto_now=True)
    description = models.TextField(default='')

    def __str__(self):
        return self.identifier

    class Meta:
        abstract = True


class MarkHistory(models.Model):
    version = models.PositiveSmallIntegerField()
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="%(class)s")
    status = models.CharField(max_length=1, choices=MARK_STATUS, default='0')
    change_date = models.DateTimeField()
    comment = models.TextField()
    description = models.TextField()

    class Meta:
        abstract = True


# Safes tables
class MarkSafe(Mark):
    verdict = models.CharField(max_length=1, choices=MARK_SAFE, default='0')

    class Meta:
        db_table = 'mark_safe'


class MarkSafeHistory(MarkHistory):
    mark = models.ForeignKey(MarkSafe, related_name='versions')
    verdict = models.CharField(max_length=1, choices=MARK_SAFE)

    class Meta:
        db_table = 'mark_safe_history'


class MarkSafeAttr(models.Model):
    mark = models.ForeignKey(MarkSafeHistory, related_name='attrs')
    attr = models.ForeignKey(Attr)
    is_compare = models.BooleanField(default=True)

    class Meta:
        db_table = 'mark_safe_attr'


class MarkSafeReport(models.Model):
    mark = models.ForeignKey(MarkSafe, related_name='markreport_set')
    report = models.ForeignKey(ReportSafe, related_name='markreport_set')

    class Meta:
        db_table = "cache_mark_safe_report"


# Unsafes tables
class MarkUnsafe(Mark):
    verdict = models.CharField(max_length=1, choices=MARK_UNSAFE, default='0')
    function = models.ForeignKey(MarkUnsafeCompare)
    error_trace = models.BinaryField(null=True)

    class Meta:
        db_table = 'mark_unsafe'


class MarkUnsafeHistory(MarkHistory):
    mark = models.ForeignKey(MarkUnsafe, related_name='versions')
    verdict = models.CharField(max_length=1, choices=MARK_UNSAFE)
    function = models.ForeignKey(MarkUnsafeCompare)

    class Meta:
        db_table = 'mark_unsafe_history'


class MarkUnsafeAttr(models.Model):
    mark = models.ForeignKey(MarkUnsafeHistory, related_name='attrs')
    attr = models.ForeignKey(Attr)
    is_compare = models.BooleanField(default=True)

    class Meta:
        db_table = 'mark_unsafe_attr'


class MarkUnsafeReport(models.Model):
    mark = models.ForeignKey(MarkUnsafe, related_name='markreport_set')
    report = models.ForeignKey(ReportUnsafe, related_name='markreport_set')
    result = models.FloatField()
    broken = models.BooleanField(default=False)

    class Meta:
        db_table = "cache_mark_unsafe_report"


# Tags tables
class SafeTag(models.Model):
    tag = models.CharField(max_length=1023)

    class Meta:
        db_table = "mark_safe_tag"


class UnsafeTag(models.Model):
    tag = models.CharField(max_length=1023)

    class Meta:
        db_table = "mark_unsafe_tag"


class ReportSafeTag(models.Model):
    report = models.ForeignKey(ReportComponent, related_name='safe_tags')
    tag = models.ForeignKey(SafeTag, related_name='+')
    number = models.IntegerField(default=0)

    def __str__(self):
        return self.tag.tag

    class Meta:
        db_table = "cache_report_safe_tag"


class ReportUnsafeTag(models.Model):
    report = models.ForeignKey(ReportComponent, related_name='unsafe_tags')
    tag = models.ForeignKey(UnsafeTag, related_name='+')
    number = models.IntegerField(default=0)

    def __str__(self):
        return self.tag.tag

    class Meta:
        db_table = 'cache_report_unsafe_tag'


class MarkSafeTag(models.Model):
    mark_version = models.ForeignKey(MarkSafeHistory, related_name='tags')
    tag = models.ForeignKey(SafeTag, related_name='+')

    def __str__(self):
        return self.tag.tag

    class Meta:
        db_table = "cache_mark_safe_tag"


class MarkUnsafeTag(models.Model):
    mark_version = models.ForeignKey(MarkUnsafeHistory, related_name='tags')
    tag = models.ForeignKey(UnsafeTag, related_name='+')

    def __str__(self):
        return self.tag.tag

    class Meta:
        db_table = 'cache_mark_unsafe_tag'


class UnsafeReportTag(models.Model):
    report = models.ForeignKey(ReportUnsafe, related_name='tags')
    tag = models.ForeignKey(UnsafeTag)
    number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'cache_unsafe_report_unsafe_tag'


class SafeReportTag(models.Model):
    report = models.ForeignKey(ReportSafe, related_name='tags')
    tag = models.ForeignKey(SafeTag)
    number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'cache_safe_report_safe_tag'


# For unknowns
class MarkUnknown(models.Model):
    identifier = models.CharField(max_length=255, unique=True)
    version = models.PositiveSmallIntegerField(default=1)
    job = models.ForeignKey(Job, null=True, on_delete=models.SET_NULL)
    format = models.PositiveSmallIntegerField(default=FORMAT)
    type = models.CharField(max_length=1, choices=JOB_CLASSES, default='0')
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=1, choices=MARK_STATUS, default='0')
    is_modifiable = models.BooleanField(default=True)
    change_date = models.DateTimeField(auto_now=True)
    component = models.ForeignKey(Component, on_delete=models.PROTECT)
    function = models.TextField()
    problem_pattern = models.CharField(max_length=15)
    link = models.URLField(null=True)
    description = models.TextField(default='')

    class Meta:
        db_table = 'mark_unknown'


class MarkUnknownHistory(models.Model):
    mark = models.ForeignKey(MarkUnknown, related_name='versions')
    version = models.PositiveSmallIntegerField()
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=1, choices=MARK_STATUS, default='0')
    function = models.TextField()
    problem_pattern = models.CharField(max_length=100)
    link = models.URLField(null=True)
    change_date = models.DateTimeField()
    comment = models.TextField()
    description = models.TextField()

    class Meta:
        db_table = 'mark_unknown_history'


class MarkUnknownReport(models.Model):
    mark = models.ForeignKey(MarkUnknown, related_name='markreport_set')
    report = models.ForeignKey(ReportUnknown, related_name='markreport_set')
    problem = models.ForeignKey(UnknownProblem, on_delete=models.PROTECT)

    class Meta:
        db_table = 'cache_mark_unknown_report'


class ComponentMarkUnknownProblem(models.Model):
    report = models.ForeignKey(ReportComponent, related_name='mark_unknowns_cache')
    component = models.ForeignKey(Component, related_name='+', on_delete=models.PROTECT)
    problem = models.ForeignKey(UnknownProblem, null=True, related_name='+', on_delete=models.PROTECT)
    number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'cache_report_component_mark_unknown_problem'