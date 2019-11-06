#
# Copyright (c) 2018 ISP RAS (http://www.ispras.ru)
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

import glob
import json


class AbstractGenerator:
    """Abstract generator"""

    specifications_endings = dict()

    def __init__(self, logger, conf):
        self.logger = logger
        self.conf = conf

    def make_scenarios(self, abstract_task_desc, collection, source, specifications):
        """
        Make scenario models according to a custom implementation.

        :param abstract_task_desc: Abstract task dictionary.
        :param collection: ProcessCollection.
        :param source: Source collection.
        :param specifications: dictionary with merged specifications.
        :return: None
        """
        raise NotImplementedError

    def import_specifications(self, specifications_set, directories):
        """
        Import specifications and return merged prepared files with all necessary content for a particular specification
        set.

        :param specifications_set: String identifier of the current specification set.
        :param directories: List with directories where to find JSON files.
        :return:
        """
        self.logger.debug('Search for specifications in: {}'.format(', '.join(directories)))

        # First collect all files
        file_candidates = {file for path in directories for file in glob.glob('{}/*.json'.format(path))}

        # Then classify them according to file name patterns
        specification_files = {kind: {f for f in file_candidates if f.endswith(ending)}
                               for kind, ending in self.specifications_endings.items()}

        # Then merge them accprdiong to fragmentation set
        specifications = {kind: self._merge_specifications(specifications_set, files)
                          for kind, files in specification_files.items()}

        return specifications

    def save_specification(self, specifications_set: str, specification: dict, file_name: str):
        """
        Save specification to a file.

        :param specifications_set: String identifier of the current specification set.
        :param specification: Specification dictionary.
        :param file_name: String with a file name.
        :return:
        """
        specification = {specifications_set: specification}
        with open(file_name, 'w', encoding='utf8') as fp:
            self.logger.debug('save specification %s' % file_name)
            json.dump(specification, fp, indent=2, sort_keys=True)

    def _merge_specifications(self, specifications_set, files):
        merged_specification = dict()
        for file in files:
            with open(file, 'r', encoding='utf8') as fp:
                new_content = json.load(fp)

            for spec_set in new_content:
                if spec_set == specifications_set:
                    # This is our specification
                    for title in new_content[spec_set]:
                        merged_specification.setdefault(title, dict())
                        merged_specification[title].update(new_content[spec_set][title])
                else:
                    # Find reference ones
                    for title in new_content[spec_set]:
                        merged_specification.setdefault(title, dict())
                        for k, v in new_content[spec_set][title].items():
                            if v.get('reference'):
                                merged_specification[title][k] = v
        return merged_specification