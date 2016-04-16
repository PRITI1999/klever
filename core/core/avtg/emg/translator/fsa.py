import copy
import graphviz


from core.avtg.emg.common.code import Variable, FunctionModels
from core.avtg.emg.common.process import Subprocess, Receive, Dispatch, Call, CallRetval, Condition


class FSA:

    def __init__(self, process):
        self.process = process
        self.initial_states = set()
        self.finite_states = set()
        self.states = set()
        self.__id_cnt = -1

        # Generate AST states
        self.__generate_states(process)

    def __iter__(self):
        self.__todo_set = set(self.initial_states)
        self.__processed_set = set()
        return self

    def __next__(self):
        if len(self.__todo_set) > 0:
            state = self.__todo_set.pop()
            self.__processed_set.add(state)

            for state in state.successors:
                if state not in self.__todo_set and state not in self.__processed_set:
                    self.__todo_set.add(state)

            return state

    def clone_state(self, node):
        new_desc = copy.deepcopy(node.desc)
        new_id = self.__yield_id()

        new_state = Node(new_desc, new_id)
        new_state.action = node.action

        for pred in node.predecessors:
            new_state.predecessors.add(pred)
            pred.successors.add(new_state)

        for succ in node.successors:
            new_state.successors.add(succ)
            succ.predecessors.add(new_state)

        self.states.add(new_state)

        return new_state

    def add_new_predecessor(self, node, action, desc, code):
        new = Node(desc, self.__yield_id())
        new.action = action
        new.code = code
        new.desc = desc

        for pred in node.predecessors:
            pred.successors.remove(node)
            pred.successors.add(new)

        node.predecessors = set([new])
        new.successors = set([node])

        self.states.add(new)

        return new

    def add_new_successor(self, node, action, desc, code):
        new = Node(desc, self.__yield_id())
        new.action = action
        new.code = code
        new.desc = desc

        for succ in node.successors:
            succ.predecessors.remove(node)
            succ.predecessors.add(new)

        node.successors = set([new])
        new.predecessors = set([node])

        self.states.add(new)

        return new

    def __generate_states(self, process):
        sb_asts = dict()
        sb_processed = set()
        asts = list()

        for name in [name for name in sorted(process.actions.keys()) if type(process.actions[name]) is Subprocess]:
            ast = copy.deepcopy(process.actions[name].process_ast)
            self.__generate_nodes(process, ast)
            sb_asts[name] = ast
        p_ast = copy.deepcopy(process.process_ast)
        self.initial_states = self.__generate_nodes(process, p_ast)
        asts.append([p_ast, None])

        while len(asts) > 0:
            ast, prev = asts.pop()

            if ast['type'] == 'choice':
                for action in ast['actions']:
                    asts.append([action, prev])
            elif ast['type'] == 'concatenation':
                for action in ast['actions']:
                    asts.append([action, prev])
                    prev = action
            elif ast['type'] == 'subprocess':
                pair = "{} {}".format(ast['name'], str(prev))
                if pair not in sb_processed:
                    sb_processed.add(pair)
                    asts.append([sb_asts[ast['name']], prev])
            else:
                for pre_state in self.__resolve_last(prev):
                    ast['node'].predecessors.add(pre_state)
                    pre_state.successors.add(ast['node'])

    def __resolve_last(self, pr_ast):
        if not pr_ast:
            return set()

        asts = [pr_ast]
        last = set()

        while len(asts) > 0:
            ast = asts.pop()

            if ast['type'] == 'choice':
                for action in ast['actions']:
                    asts.append(action)
            elif ast['type'] == 'concatenation':
                asts.append(ast['actions'][-1])
            else:
                last.add(ast['node'])

        return last

    def __generate_nodes(self, process, pr_ast):
        asts = [[pr_ast, True]]
        initial_states = set()

        while len(asts) > 0:
            ast, initflag = asts.pop()

            if ast['type'] == 'choice':
                for action in ast['actions']:
                    asts.append([action, initflag])
            elif ast['type'] == 'concatenation':
                for action in ast['actions']:
                    if initflag:
                        asts.append([action, initflag])
                        initflag = False
                    else:
                        asts.append([action, initflag])
            elif ast['type'] != 'subprocess':
                node = Node(ast, self.__yield_id())

                node.action = process.actions[ast['name']]
                self.states.add(node)
                ast['node'] = node

                if initflag:
                    initial_states.add(node)

        return initial_states

    def __yield_id(self):
        self.__id_cnt += 1
        return self.__id_cnt


class Node:

    def __init__(self, desc, identifier):
        self.identifier = identifier
        self.desc = desc
        self.predecessors = set()
        self.successors = set()
        self.action = None
        self.code = None

    def replace_successor(self, old, new):
        self.successors.remove(old)
        self.successors.add(new)

    def replace_predecessor(self, old, new):
        self.predecessors.remove(old)
        self.predecessors.add(new)


class Automaton:

    def __init__(self, logger, analysis, process, identifier):
        # Set default values
        self.control_function = None
        self.functions = []
        self.__state_variable = None
        self.__variables = []
        self.__label_variables = {}

        # Set given values
        self.logger = logger
        self.process = process
        self.identifier = identifier

        # Generate FSA itself
        self.logger.info("Generate states for automaton {} based on process {} with category {}".
                         format(self.identifier, self.process.name, self.process.category))
        self.fsa = FSA(self.process)
        self.variables(analysis)

    @property
    def state_variable(self):
        if not self.__state_variable:
            var = Variable('ldv_statevar_{}'.format(self.identifier),  None, 'int a', True)
            self.__state_variable = var

        return self.__state_variable

    def variables(self, analysis):
        if len(self.__variables) == 0:
            # Generate variable for each label
            for label in [self.process.labels[name] for name in sorted(self.process.labels.keys())]:
                if label.interfaces:
                    for interface in label.interfaces:
                        self.__variables.append(self.determine_variable(analysis, label, interface))
                else:
                    var = self.determine_variable(analysis, label)
                    if var:
                        self.__variables.append(self.determine_variable(analysis, label))

        return self.__variables

    def new_param(self, analysis, name, declaration, value):
        lb = self.process.add_simple_label(name, declaration, value)
        lb.resource = True
        vb = self.determine_variable(analysis, lb)
        return vb

    def determine_variable(self, analysis, label, interface=None):
        if not interface:
            if label.name in self.__label_variables and "default" in self.__label_variables[label.name]:
                return self.__label_variables[label.name]["default"]
            else:
                if label.prior_signature:
                    var = Variable("emgfsa_{}_{}_{}".format(self.identifier, label.name, "default"), None,
                                   label.prior_signature, export=True)
                    if label.value:
                        var.value = label.value

                    if label.name not in self.__label_variables:
                        self.__label_variables[label.name] = {}
                    self.__label_variables[label.name]["default"] = var
                    return self.__label_variables[label.name]["default"]
                else:
                    self.logger.warning("Cannot create variable for label which is not matched with interfaces and does"
                                        " not have signature")
                    return None
        else:
            if label.name in self.__label_variables and interface in self.__label_variables[label.name]:
                return self.__label_variables[label.name][interface]
            else:
                if interface not in label.interfaces:
                    raise KeyError("Label {} is not matched with interface {}".format(label.name, interface))
                else:
                    access = self.process.resolve_access(label, interface)
                    category, short_id = interface.split(".")
                    implementations = self.process.get_implementations(analysis, access)
                    var = Variable("emgfsa_{}_{}_{}".format(self.identifier, label.name, short_id), None,
                                   label.get_declaration(interface), export=True)

                    if len(implementations) == 1:
                        var.value = implementations[0].adjusted_value(var.declaration)

                        # Change file according to the value
                        var.file = implementations[0].file

                    if label.name not in self.__label_variables:
                        self.__label_variables[label.name] = {}
                    self.__label_variables[label.name][interface] = var
                    return self.__label_variables[label.name][interface]

    def save_digraph(self, directory):
        # Generate graph
        self.logger.info("Generate graph for automaton based on process {} with category {}".
                         format(self.process.name, self.process.category))
        dg_file = "{}/{}.dot".format(directory, "{}_{}_{}".
                                     format(self.process.category, self.process.name, self.identifier))

        graph = graphviz.Digraph(
            name=str(self.identifier),
            comment="Digraph for FSA {} based on self.process {} with category {}".
                    format(self.identifier, self.process.name, self.process.category),
            format="png"
        )

        # Add self.process description
        graph.node(
            self.process.name,
            "self.process: {}".format(self.process.process),
            {
                "shape": "rectangle"
            }
        )

        # Add subself.process description
        for subp in [self.process.actions[name] for name in sorted(self.process.actions.keys())
                       if type(self.process.actions[name]) is Subprocess]:
            graph.node(
                subp.name,
                "Subprocess {}: {}".format(subp.name, subp.process),
                {
                    "shape": "rectangle"
                }
            )

        for state in self.fsa.states:
            label = "Action: {}\n".format(state.desc['label'])
            if state.code:
                if 'file' in state.code:
                    label += "File: '{}'\n".format(state.code['file'])

                if 'guard' in state.code and len(state.code['guard']) > 0:
                    label += 'Conditions:\n' + '\n'.join(state.code['guard'])

                label+= 'Relevant automata:\n'
                if 'relevant automata' in state.code and len(state.code['relevant automata']) > 0:
                    for automaton in state.code['relevant automata'].values():
                        label += "Automaton '{}': '{}' ({})\n".format(automaton['automaton'].identifier,
                                                                      automaton['automaton'].process.name,
                                                                      automaton['automaton'].process.category)

                    label += 'Conditions:\n' + '\n'.join(state.code['body'])
                    label += "\n"

                if 'body' in state.code and len(state.code['body']) > 0:
                    label += 'Body:\n' + '\n'.join(state.code['body'])

            graph.node(str(state.identifier), label)

            for succ in state.successors:
                graph.edge(
                    str(state.identifier),
                    str(succ.identifier)
                )

        # Save to dg_file
        graph.save(dg_file)
        graph.render()

    def generate_code(self, analysis, model, translator, state):
        cases = []
        base_case = {
            "guard": [],
            "body": [],
        }

        if type(state.action) is Call:
            accesses = self.process.resolve_access(state.action.callback)
            callbacks = []

            for access in accesses:
                new_case = copy.deepcopy(base_case)

                if access.interface:
                    signature = access.interface.declaration
                    implementations = self.process.get_implementations(analysis, access)

                    if len(implementations) > 1:
                        raise NotImplementedError(
                            "Cannot process fsm with several implementations of a single callback")
                    elif len(implementations) == 1 and analysis.callback_name(implementations[0].value):
                        invoke = '(' + implementations[0].value + ')'
                        file = implementations[0].file
                        check = False
                    elif signature.clean_declaration:
                        invoke = '(' + \
                                 access.access_with_variable(self.determine_variable(analysis, access.label,
                                                                                     access.list_interface[0].
                                                                                     identifier)) + \
                                 ')'
                        file = translator.entry_file
                        check = True
                    else:
                        invoke = None
                else:
                    signature = access.label.prior_signature

                    if access.label.value and analysis.callback_name(access.label.value):
                        invoke = analysis.callback_name(access.label.value)
                        file = translator.entry_file
                        check = False
                    else:
                        variable = self.determine_variable(analysis, access.label)
                        if variable:
                            invoke = access.access_with_variable(variable)
                            file = translator.entry_file
                            check = True
                        else:
                            invoke = None

                if invoke:
                    additional_checks = translator.registration_intf_check(analysis, model, invoke)
                    if len(list(additional_checks.keys())) > 0:
                        new_case['relevant automata'] = additional_checks

                    if len(callbacks) == 0:
                        callbacks.append([state, new_case, signature, invoke, file, check])
                    else:
                        clone = self.fsa.clone_state(state)
                        callbacks.append([clone, new_case, signature, invoke, file, check])

            for nd, case, signature, invoke, file, check in callbacks:
                # Generate function call and corresponding function
                params = []
                local_vars = []
                cb_statements = []

                # Determine parameters
                for index in range(len(signature.points.parameters)):
                    parameter = signature.points.parameters[index]
                    if type(parameter) is not str:
                        expression = None
                        # Try to find existing variable
                        ids = [intf.identifier for intf in
                               analysis.resolve_interface(parameter, self.process.category)]
                        if len(ids) > 0:
                            for candidate in state.action.parameters:
                                accesses = self.process.resolve_access(candidate)
                                suits = [acc for acc in accesses if acc.interface and
                                         acc.interface.identifier in ids]
                                if len(suits) == 1:
                                    var = self.determine_variable(analysis, suits[0].label,
                                                                       suits[0].list_interface[0].identifier)
                                    expression = suits[0].access_with_variable(var)
                                    break
                                elif len(suits) > 1:
                                    raise NotImplementedError("Cannot set two different parameters")

                        # Generate new variable
                        if not expression:
                            tmp = self.new_param(analysis,
                                                    "emg_param_{}".format(nd.identifier),
                                                 signature.points.parameters[index],
                                                 None)
                            local_vars.append(tmp)
                            expression = tmp.name

                    # Add string
                    params.append(expression)

                # Add precondition and postcondition
                if len(local_vars) > 0:
                    pre_statements = []
                    post_statements = []
                    for var in local_vars:
                        definition = var.declare_with_init(
                            translator.conf["translation options"]["pointer initialization"]) + ";"
                        pre_statements.append(definition)
                        free = var.free_pointer(translator.conf["translation options"]["pointer free"])
                        if free:
                            post_statements.append(free + ";")
                    cond_name = 'pre_call_{}'.format(nd.identifier)
                    code = {
                        "guard": [],
                        "body": pre_statements,
                        "file": file
                    }

                    new_action = self.process.add_condition(cond_name, [], pre_statements)
                    new = self.fsa.add_new_predecessor(state, new_action, {}, code)
                    new.desc = {
                        'label': "<{}>".format(cond_name)
                    }

                    if len(post_statements) > 0:
                        post_code = {
                            "guard": [],
                            "body": post_statements,
                            "file": file
                        }

                        cond_name = 'post_call_{}'.format(nd.identifier)
                        succ_action = self.process.add_condition(cond_name, [], post_statements)
                        new = self.fsa.add_new_successor(state, succ_action, {}, post_code)
                        new.desc = {
                            'label': "<{}>".format(cond_name)
                        }

                # Generate return value assignment
                retval = ""
                ret_subprocess = [self.process.actions[name] for name in sorted(self.process.actions.keys())
                                  if type(self.process.actions[name]) is CallRetval and
                                  self.process.actions[name].callback == state.action.callback and
                                  self.process.actions[name].retlabel]
                if ret_subprocess:
                    ret_access = self.process.resolve_access(ret_subprocess[0].retlabel)
                    retval = ret_access[0].access_with_variable(
                        self.determine_variable(analysis, ret_access[0].label))
                    case['retval'] = [retval, signature.return_value]
                    retval = 'return'

                # Generate callback call
                if check:
                    cb_statements.extend(
                        [
                            "if ({})".format(invoke),
                            "\t" + retval + invoke + '(' + ", ".join(params) + ");"
                        ]
                    )
                else:
                    cb_statements.append(
                        retval + invoke + '(' + ", ".join(params) + ");"
                    )

                # Generate comment
                case["body"].append("/* Call callback {} */".format(state.action.name))
                case["body"].extend(cb_statements)
                case['file'] = file
                nd.code = case
        elif type(state.action) is Dispatch:
            # Generate dispatch function
            if len(state.action.peers) > 0:
                # Do call only if model which can be called will not hang
                automata_peers = {}
                translator.extract_relevant_automata(automata_peers, state.action.peers, Receive)
                if len(list(automata_peers.keys())) > 0:
                    base_case['relevant automata'] = automata_peers
                elif len(list(automata_peers.keys())) > 0:
                    raise RuntimeError("No dispatches are generated for dispatch {} but it can be received".
                                       format(state.action.name))
            else:
                # Generate comment
                base_case["body"].append("/* Dispatch {} is not expected by any process, skip it */".
                                         format(state.action.name))
            cases.append(base_case)
        elif type(state.action) is CallRetval:
            base_case["body"].append("/* Should wait for return value of {} here, "
                                     "but in sequential model it is not necessary */".format(state.action.name))
            state.code = base_case
        elif type(state.action) is Receive:
            # Generate comment
            base_case["body"].append("/* Receive signal {} */".format(state.action.name))
            state.code = base_case
        elif type(state.action) is Condition:
            # Generate comment
            base_case["body"].append("/* Code or condition insertion {} */".format(state.action.name))

            # Add additional condition
            if state.action.condition and len(state.action.condition) > 0:
                for statement in state.action.condition:
                    cn = self.text_processor(analysis, statement)
                    base_case["guard"].extend(cn)

            if state.action.statements:
                for statement in state.action.statements:
                    base_case["body"].extend(self.text_processor(analysis, statement))
            state.code = base_case
        elif type(state.action) is Subprocess:
            raise NotImplementedError('Do not expect subprocess state')
        else:
            raise ValueError("Unexpected state machine edge type: {}".format(state.action.type))

    def text_processor(self, analysis, statement):
        # Replace model functions
        mm = FunctionModels()
        accesses = self.process.accesses()

        statements = [statement]
        for access in accesses:
            new_statements = []
            for text in list(statements):
                processed = False
                for option in sorted(accesses[access], key=lambda ac: ac.expression):
                    if option.interface:
                        signature = option.label.get_declaration(option.interface.identifier)
                    else:
                        signature = option.label.prior_signature

                    if signature:
                        if option.interface:
                            var = self.determine_variable(analysis, option.label,
                                                               option.list_interface[0].identifier)
                        else:
                            var = self.determine_variable(analysis, option.label)

                        try:
                            tmp = mm.replace_models(option.label.name, signature, text)
                            tmp = option.replace_with_variable(tmp, var)
                            new_statements.append(tmp)
                            processed = True
                        except ValueError:
                            processed = True

                if not processed:
                    new_statements.append(text)
            statements = new_statements

        # Filter out statements without processes expressions
        final = set()
        for stm in list(statements):
            if '%' not in stm and '$' not in statements:
                final.add(stm)

        return list(final)

__author__ = 'Ilja Zakharov <ilja.zakharov@ispras.ru>'