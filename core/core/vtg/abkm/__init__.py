#!/usr/bin/python3

import json
import os
import re
import shutil
import tarfile
import time
from xml.dom import minidom

import core.components
import core.session
import core.utils


class ABKM(core.components.Component):
    def generate_verification_tasks(self):
        self.logger.info('Generate one verification task by merging all bug kinds')

        self.prepare_common_verification_task_desc()
        self.prepare_property_file()
        self.prepare_src_files()

        if self.conf['debug']:
            self.logger.debug('Create verification task description file "task.json"')
            with open('task.json', 'w') as fp:
                json.dump(self.task_desc, fp, sort_keys=True, indent=4)

        self.prepare_verification_task_files_archive()

        self.decide_verification_task()

    main = generate_verification_tasks

    def prepare_common_verification_task_desc(self):
        self.logger.info('Prepare common verification task description')

        self.task_desc = {
            # Safely use id of corresponding abstract verification task since all bug kinds will be merged and each
            # abstract verification task will correspond to exactly one verificatoin task.
            'id': self.conf['abstract task desc']['id'],
            'format': 1,
            # Simply use priority of parent job.
            'priority': self.conf['priority'],
        }

        # Use resource limits and verifier specified in job configuration.
        self.task_desc.update({name: self.conf['VTG strategy'][name] for name in ('resource limits', 'verifier')})

    def prepare_property_file(self):
        self.logger.info('Prepare verifier property file')

        if len(self.conf['abstract task desc']['entry points']) > 1:
            raise NotImplementedError('Several entry points are not supported')

        with open('unreach-call.prp', 'w') as fp:
            fp.write('CHECK( init({0}()), LTL(G ! call(__VERIFIER_error())) )'.format(
                self.conf['abstract task desc']['entry points'][0]))

        self.task_desc['property file'] = 'unreach-call.prp'

        self.logger.debug('Verifier property file was outputted to "unreach-call.prp"')

    def prepare_src_files(self):
        self.task_desc['files'] = []

        if self.conf['VTG strategy']['merge source files']:
            self.logger.info('Merge source files by means of CIL')

            # CIL doesn't support asm goto (https://forge.ispras.ru/issues/1323).
            self.logger.info('Ignore asm goto expressions')

            for extra_c_file in self.conf['abstract task desc']['extra C files']:
                trimmed_c_file = '{0}.trimmed.i'.format(os.path.splitext(extra_c_file['C file'])[0])
                with open(os.path.join(self.conf['source tree root'], extra_c_file['C file'])) as fp_in, open(
                        os.path.join(self.conf['source tree root'], trimmed_c_file), 'w') as fp_out:
                    # Each such expression occupies individual line, so just get rid of them.
                    for line in fp_in:
                        fp_out.write(re.sub(r'asm volatile goto.*;', '', line))
                extra_c_file['C file'] = trimmed_c_file

            with open('cil input files.txt', 'w') as fp:
                for extra_c_file in self.conf['abstract task desc']['extra C files']:
                    fp.write('{0}\n'.format(extra_c_file['C file']))

            cil_out_file = os.path.relpath('cil.i', os.path.realpath(self.conf['source tree root']))

            core.utils.execute(self.logger,
                               (
                                   'cilly.asm.exe',
                                   '--extrafiles', os.path.relpath('cil input files.txt',
                                                                   os.path.realpath(self.conf['source tree root'])),
                                   '--out', cil_out_file,
                                   '--printCilAsIs',
                                   '--domakeCFG',
                                   '--decil',
                                   '--noInsertImplicitCasts',
                                   # Now supported by CPAchecker frontend.
                                   '--useLogicalOperators',
                                   '--ignore-merge-conflicts',
                                   # Don't transform simple function calls to calls-by-pointers.
                                   '--no-convert-direct-calls',
                                   # Don't transform s->f to pointer arithmetic.
                                   '--no-convert-field-offsets',
                                   # Don't transform structure fields into variables or arrays.
                                   '--no-split-structs',
                                   '--rmUnusedInlines'
                               ),
                               cwd=self.conf['source tree root'])

            self.task_desc['files'].append(cil_out_file)

            self.logger.debug('Merged source files was outputted to "cil.i"')
        else:
            for extra_c_file in self.conf['abstract task desc']['extra C files']:
                self.task_desc['files'].append(extra_c_file['C file'])

    def prepare_verification_task_files_archive(self):
        self.logger.info('Prepare archive with verification task files')

        with tarfile.open('task files.tar.gz', 'w:gz') as tar:
            tar.add('unreach-call.prp')
            for file in self.task_desc['files']:
                tar.add(os.path.join(self.conf['source tree root'], file), os.path.basename(file))
            self.task_desc['files'] = [os.path.basename(file) for file in self.task_desc['files']]

    def decide_verification_task(self):
        self.logger.info('Decide verification task')

        session = core.session.Session(self.logger, self.conf['Klever Bridge'], self.conf['identifier'])
        task_id = session.schedule_task(self.task_desc)

        while True:
            task_status = session.get_task_status(task_id)

            if task_status == 'ERROR':
                task_error = session.get_task_error(task_id)

                self.logger.warning('Failed to decide verification task: {0}'.format(task_error))

                with open('task error.txt', 'w') as fp:
                    fp.write(task_error)

                core.utils.report(self.logger,
                                  'unknown',
                                  {
                                      'id': 'unknown',
                                      'parent id': self.id,
                                      'problem desc': 'task error.txt',
                                      'files': ['task error.txt']
                                  },
                                  self.mqs['report files'],
                                  self.conf['main working directory'])
                break

            if task_status == 'FINISHED':
                self.logger.info('Verification task was successfully decided')

                session.download_decision(task_id)

                tar = tarfile.open("decision result files.tar.gz")
                tar.extractall()
                tar.close()

                with open('decision results.json') as fp:
                    decision_results = json.load(fp)

                # TODO: specify the computer where the verifier was invoked (this information should be get from BenchExec.
                core.utils.report(self.logger,
                                  'verification',
                                  {
                                      # TODO: replace with something meaningful, e.g. tool name + tool version + tool configuration.
                                      'id': self.task_desc['id'],
                                      'parent id': self.id,
                                      # TODO: replace with something meaningful, e.g. tool name + tool version + tool configuration.
                                      'attrs': [],
                                      'name': self.conf['VTG strategy']['verifier']['name'],
                                      'resources': decision_results['resources'],
                                      'desc': decision_results['desc'],
                                      'log': 'cil.i.log',
                                      'data': '',
                                      'files': ['cil.i.log']
                                  },
                                  self.mqs['report files'],
                                  self.conf['main working directory'])

                self.logger.info('Verification task decision status is "{0}"'.format(decision_results['status']))

                if decision_results['status'] == 'safe':
                    core.utils.report(self.logger,
                                      'safe',
                                      {
                                          'id': 'safe',
                                          'parent id': self.task_desc['id'],
                                          'attrs': [],
                                          # TODO: just the same file as parent log, looks strange.
                                          'proof': 'cil.i.log',
                                          'files': ['cil.i.log']
                                      },
                                      self.mqs['report files'],
                                      self.conf['main working directory'])
                elif decision_results['status'] == 'unsafe':
                    self.logger.info('Get source files referred by error trace')
                    src_files = set()
                    with open('witness.graphml') as fp:
                        # TODO: try xml.etree (see https://svn.sosy-lab.org/trac/cpachecker/ticket/236).
                        dom = minidom.parse(fp)
                    graphml = dom.getElementsByTagName('graphml')[0]
                    for key in graphml.getElementsByTagName('key'):
                        if key.getAttribute('id') == 'originfile':
                            default = key.getElementsByTagName('default')[0]
                            default_src_file = self.__normalize_path(default.firstChild)
                            src_files.add(default_src_file)
                    graph = graphml.getElementsByTagName('graph')[0]
                    for edge in graph.getElementsByTagName('edge'):
                        for data in edge.getElementsByTagName('data'):
                            if data.getAttribute('key') == 'originfile':
                                src_files.add(self.__normalize_path(data.firstChild))

                    self.logger.info('Extract notes and warnings from source files referred by error trace')
                    notes = {}
                    warns = {}
                    for src_file in src_files:
                        with open(os.path.join(self.conf['source tree root'], src_file)) as fp:
                            i = 0
                            for line in fp:
                                i += 1
                                match = re.search(
                                    r'/\*\s+(MODEL_FUNC_DEF|ASSERT|CHANGE_STATE|RETURN|MODEL_FUNC_CALL|OTHER)\s+(.*)\s+\*/',
                                    line)
                                if match:
                                    kind, comment = match.groups()

                                    if kind == 'MODEL_FUNC_DEF':
                                        # Get necessary function name located on following line.
                                        try:
                                            line = next(fp)
                                            # Don't forget to increase counter.
                                            i += 1
                                            match = re.search(r'(ldv_\w+)', line)
                                            if match:
                                                func_name = match.groups()[0]
                                            else:
                                                raise ValueError(
                                                    'Model function definition is not specified in "{0}"'.format(line))
                                        except StopIteration:
                                            raise ValueError('Model function definition does not exist')
                                        notes[func_name] = comment
                                    else:
                                        if src_file not in notes:
                                            notes[src_file] = {}
                                        notes[src_file][i + 1] = comment
                                        # Some assert(s) will become warning(s).
                                        if kind == 'ASSERT':
                                            if src_file not in warns:
                                                warns[src_file] = {}
                                            warns[src_file][i + 1] = comment

                    self.logger.info('Add notes and warnings to error trace')
                    # Find out sequence of edges (violation path) from entry node to violation node.
                    violation_edges = []
                    entry_node_id = None
                    violation_node_id = None
                    for node in graph.getElementsByTagName('node'):
                        for data in node.getElementsByTagName('data'):
                            if data.getAttribute('key') == 'entry' and data.firstChild.data == 'true':
                                entry_node_id = node.getAttribute('id')
                            elif data.getAttribute('key') == 'violation' and data.firstChild.data == 'true':
                                violation_node_id = node.getAttribute('id')
                    src_edges = {}
                    for edge in graph.getElementsByTagName('edge'):
                        src_node_id = edge.getAttribute('source')
                        dst_node_id = edge.getAttribute('target')
                        src_edges[dst_node_id] = (src_node_id, edge)
                    cur_src_edge = src_edges[violation_node_id]
                    violation_edges.append(cur_src_edge[1])
                    ignore_edges_of_func = None
                    while True:
                        cur_src_edge = src_edges[cur_src_edge[0]]
                        # Do not add edges of intermediate functions.
                        for data in cur_src_edge[1].getElementsByTagName('data'):
                            if data.getAttribute('key') == 'returnFrom' and not ignore_edges_of_func:
                                ignore_edges_of_func = data.firstChild.data
                        if not ignore_edges_of_func:
                            violation_edges.append(cur_src_edge[1])
                        for data in cur_src_edge[1].getElementsByTagName('data'):
                            if data.getAttribute('key') == 'enterFunction' and ignore_edges_of_func:
                                if ignore_edges_of_func == data.firstChild.data:
                                    ignore_edges_of_func = None
                        if cur_src_edge[0] == entry_node_id:
                            break
                    for edge in graph.getElementsByTagName('edge'):
                        src_file, i, func_name = (None, None, None)

                        for data in edge.getElementsByTagName('data'):
                            if data.getAttribute('key') == 'originfile':
                                src_file = data.firstChild.data
                            elif data.getAttribute('key') == 'startline':
                                i = int(data.firstChild.data)
                            elif data.getAttribute('key') == 'enterFunction':
                                func_name = data.firstChild.data

                        if not src_file:
                            src_file = default_src_file

                        if src_file and i:
                            if src_file in notes and i in notes[src_file]:
                                self.logger.debug(
                                    'Add note "{0}" from "{1}:{2}"'.format(notes[src_file][i], src_file, i))
                                note = dom.createElement('data')
                                txt = dom.createTextNode(notes[src_file][i])
                                note.appendChild(txt)
                                note.setAttribute('key', 'note')
                                edge.appendChild(note)

                            if func_name and func_name in notes:
                                self.logger.debug('Add note "{0}" for call of model function "{1}" from "{2}"'.format(
                                    notes[func_name], func_name, src_file))
                                note = dom.createElement('data')
                                txt = dom.createTextNode(notes[func_name])
                                note.appendChild(txt)
                                note.setAttribute('key', 'note')
                                edge.appendChild(note)

                            if src_file in warns and i in warns[src_file] and edge.getAttribute(
                                    'target') == violation_node_id:
                                self.logger.debug(
                                    'Add warning "{0}" from "{1}:{2}"'.format(warns[src_file][i], src_file, i))
                                warn = dom.createElement('data')
                                txt = dom.createTextNode(warns[src_file][i])
                                warn.appendChild(txt)
                                warn.setAttribute('key', 'warning')
                                # Add warning either to edge itself or to first edge with note at violation path. If
                                # don't do the latter warning will be hidden by error trace visualizer.
                                warn_edge = edge
                                for cur_src_edge in violation_edges:
                                    for data in cur_src_edge.getElementsByTagName('data'):
                                        if data.getAttribute('key') == 'note':
                                            warn_edge = cur_src_edge
                                # Remove note from node for what we are going to add warning if so. Otherwise error
                                # trace visualizer will be confused.
                                for data in warn_edge.getElementsByTagName('data'):
                                    if data.getAttribute('key') == 'note':
                                        warn_edge.removeChild(data)
                                warn_edge.appendChild(warn)

                    self.logger.info('Create processed error trace file "witness.processed.graphml"')
                    with open('witness.processed.graphml', 'w') as fp:
                        graphml.writexml(fp)

                    # TODO: copy is done just to create unsafe report later, so get rid of it sometime.
                    # Copy all source files referred by error trace to working directory.
                    if src_files:
                        self.logger.debug('Source files referred by error trace are: "{}"'.format(src_files))
                        for src_file in src_files:
                            os.makedirs(os.path.dirname(src_file), exist_ok=True)
                            shutil.copy(os.path.join(self.conf['source tree root'], src_file), src_file)

                    core.utils.report(self.logger,
                                      'unsafe',
                                      {
                                          'id': 'unsafe',
                                          'parent id': self.task_desc['id'],
                                          'attrs': [],
                                          'error trace': 'witness.processed.graphml',
                                          'files': ['witness.processed.graphml'] + list(src_files)
                                      },
                                      self.mqs['report files'],
                                      self.conf['main working directory'])
                elif decision_results['status'] in ('error', 'CPU time exhausted', 'memory exhausted'):
                    # Prepare file to send it with unknown report.
                    if decision_results['status'] in ('CPU time exhausted', 'memory exhausted'):
                        with open('error.txt', 'w') as fp:
                            fp.write(decision_results['status'])
                    core.utils.report(self.logger,
                                      'unknown',
                                      {
                                          'id': 'unknown',
                                          'parent id': self.task_desc['id'],
                                          # TODO: just the same file as parent log, looks strange.
                                          'problem desc':
                                              'cil.i.log' if decision_results['status'] == 'error'
                                              else 'error.txt',
                                          'files': ['cil.i.log' if decision_results['status'] == 'error'
                                                    else 'error.txt']
                                      },
                                      self.mqs['report files'],
                                      self.conf['main working directory'])
                else:
                    raise NotImplementedError(
                        'Status "{0}" of verification task decision results is not supported'.format(
                            decision_results['status']))

                break

            time.sleep(1)

    def __normalize_path(self, path):
        # Each file is specified either via absolute path or path relative to source tree root.
        # Make all paths relative to source tree root.
        if os.path.isabs(path.data):
            path.data = os.path.relpath(path.data, os.path.realpath(self.conf['source tree root']))

        if not os.path.isfile(os.path.join(self.conf['source tree root'], path.data)):
            raise FileNotFoundError('File "{0}" referred by error trace does not exist'.format(path.data))

        return path.data