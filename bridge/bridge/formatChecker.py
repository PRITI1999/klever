from django.db.models import FileField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _


class RestrictedFileField(FileField):
    """
    Same as FileField, but you can specify:
    * content_types - list containing allowed content_types.
      Example: ['application/pdf', 'image/jpeg']
      Default: all content types are supported.
    * max_upload_size - a number indicating the maximum file size allowed
      for upload. Example: 2621440. Default: all sizes are supported.
        2.5MB - 2621440
        5MB - 5242880
        10MB - 10485760
        20MB - 20971520
        50MB - 5242880
        100MB 104857600
        250MB - 214958080
        500MB - 429916160
    """

    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop("content_types", None)
        self.max_upload_size = kwargs.pop("max_upload_size", 0)
        
        super(RestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(RestrictedFileField, self).clean(*args, **kwargs)

        file = data.file
        try:
            content_type = file.content_type
            if self.content_types is not None:
                if content_type not in self.content_types:
                    raise forms.ValidationError(_('The file type is not supported'))
            if file.size > self.max_upload_size > 0:
                raise forms.ValidationError(
                    _('Please keep the file size under {0} (the current file size is {1})'.format(filesizeformat(self.max_upload_size),
                       filesizeformat(file.size)))
                )
        except AttributeError:
            pass

        return data