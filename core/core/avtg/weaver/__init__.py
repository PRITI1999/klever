#!/usr/bin/python3

import fileinput
import json
import os

import core.components
import core.utils


class Weaver(core.components.Component):
    def weave(self):
        self.abstract_task_desc = self.mqs['abstract task description'].get()

        self.abstract_task_desc['extra C files'] = []

        for grp in self.abstract_task_desc['grps']:
            self.logger.info('Weave in C files of group "{0}"'.format(grp['id']))

            for cc_extra_full_desc_file in grp['cc extra full desc files']:
                with open(os.path.join(self.conf['source tree root'],
                                       cc_extra_full_desc_file['cc full desc file'])) as fp:
                    cc_full_desc = json.load(fp)

                self.logger.info('Weave in C file "{0}"'.format(cc_full_desc['in files'][0]))

                # Produce aspect to be weaved in.
                if 'plugin aspects' in cc_extra_full_desc_file:
                    # Concatenate all aspects of all plugins together.
                    aspect = os.path.join(self.conf['source tree root']
                                          , '{}.aspect'.format(os.path.splitext(cc_full_desc['out file'])[0]))
                    with open(aspect, 'w') as fout, fileinput.input(
                            [os.path.join(self.conf['source tree root'], aspect) for plugin_aspects
                             in cc_extra_full_desc_file['plugin aspects'] for aspect in
                             plugin_aspects['aspects']]) as fin:
                        for line in fin:
                            fout.write(line)

                    # TODO: if several files in verification object will have the same name everything will break.
                    # Here output file is corresponding, likely already generated and existing object file. But other
                    # instances of AVTG plugins can refer to the same file. So the only safe place to put intermediate
                    # and output file is working directory. Besides overwrite suffix because of we will obtain
                    # weaved C files.
                    cc_full_desc['out file'] = os.path.relpath(
                        '{}.c'.format(os.path.splitext(os.path.basename(cc_full_desc['out file']))[0]),
                        os.path.realpath(self.conf['source tree root']))
                else:
                    aspect = '/dev/null'
                self.logger.debug('Aspect to be weaved in is "{0}"'.format(aspect))

                # This is required to get compiler (Aspectator) specific stdarg.h since kernel C files are compiled with
                # "-nostdinc" option and system stdarg.h couldn't be used.
                stdout = core.utils.execute(self.logger,
                                            ('aspectator', '-print-file-name=include'),
                                            collect_all_stdout=True)
                core.utils.execute(self.logger,
                                   tuple(['cif',
                                          '--in', cc_full_desc['in files'][0],
                                          '--aspect',
                                          os.path.relpath(aspect, os.path.realpath(self.conf['source tree root'])),
                                          '--out', cc_full_desc['out file'],
                                          '--back-end', 'src',
                                          '--debug', 'DEBUG',
                                          '--keep-prepared-file'] +
                                         (['--keep'] if self.conf['debug'] else []) +
                                         ['--'] +
                                         cc_full_desc['opts'] +
                                         ['-isystem{0}'.format(stdout[0])]),
                                   cwd=self.conf['source tree root'])
                self.logger.debug('C file "{0}" was weaved in'.format(cc_full_desc['in files'][0]))

                # In addition preprocess output files since CIF outputs a bit unpreprocessed files.
                preprocessed_c_file = '{}.i'.format(os.path.splitext(cc_full_desc['out file'])[0])
                core.utils.execute(self.logger,
                                   ('aspectator', '-E', '-x', 'c', cc_full_desc['out file'], '-o', preprocessed_c_file),
                                   cwd=self.conf['source tree root'])
                self.logger.debug('Preprocess weaved C file to "{0}"'.format(preprocessed_c_file))

                extra_c_file = {'C file': preprocessed_c_file}

                if 'rule spec id' in cc_extra_full_desc_file:
                    extra_c_file['rule spec id'] = cc_extra_full_desc_file['rule spec id']

                if 'bug kinds' in cc_extra_full_desc_file:
                    extra_c_file['bug kinds'] = cc_extra_full_desc_file['bug kinds']

                self.abstract_task_desc['extra C files'].append(extra_c_file)

        # These sections won't be reffered any more.
        del (self.abstract_task_desc['grps'])
        del (self.abstract_task_desc['deps'])

        self.mqs['abstract task description'].put(self.abstract_task_desc)

    main = weave