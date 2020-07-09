#
# Copyright (c) 2019 ISP RAS (http://www.ispras.ru)
# Ivannikov Institute for System Programming of the Russian Academy of Sciences
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from tools.profiling import LoggedCallMixin
from bridge.CustomViews import DataViewMixin

class TestReport(LoginRequiredMixin, LoggedCallMixin, DataViewMixin, TemplateView):
    template_name = 'bridge/manage_sparse.html'

    def get_context_data(self, **kwargs):
        names = [1, 2, 3, 4]
        return {
            'names': names
        }
        #return render(request, template_name, context)
        #context = super().get_context_data(**kwargs)
        #context['tabledata'] = SafeMarksTable(self.request.user, self.get_view(VIEW_TYPES[8]), self.request.GET)
        #return context
