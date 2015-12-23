function encodeData(s) {
    return encodeURIComponent(s).replace(/\-/g, "%2D").replace(/\_/g, "%5F").replace(/\./g, "%2E").replace(/\!/g, "%21").replace(/\~/g, "%7E").replace(/\*/g, "%2A").replace(/\'/g, "%27").replace(/\(/g, "%28").replace(/\)/g, "%29");
}

function collect_filters_data() {
    var view_values = {columns: []}, filter_values = {},
        columns = ['num_of_links', 'verdict', 'status', 'component', 'author', 'format', 'pattern'],
        order_type = $('input[name=marks_enable_order]:checked').val();
    $.each(columns, function (index, val) {
        var column_checkbox = $('#marks_filter_checkbox__' + val);
        if (column_checkbox.length && column_checkbox.is(':checked')) {
            view_values['columns'].push(val);
        }
    });
    if (order_type == 'attribute') {
        var order = $('#filter__attr__order').val();
        if (order.length > 0) {
            view_values['order'] = order;
        }
    }
    else if (order_type == 'num_of_links') {
        view_values['order'] = 'num_of_links';
    }

    var attr_val = $('#filter__attr__value').val(),
        attr_attr = $('#filter__attr__attr').val();
    if (attr_val && attr_attr && attr_val.length > 0 && attr_attr.length > 0) {
        filter_values['attr'] = {
            attr: attr_attr,
            type: $('#filter__attr__type').val(),
            value: attr_val
        }
    }
    if ($('#filter__enable__verdict').is(':checked')) {
        filter_values['verdict'] = {
            type: $('#filter__type__verdict').val(),
            value: $('#filter__value__verdict').children(':selected').val()
        }
    }
    if ($('#filter__enable__status').is(':checked')) {
        filter_values['status'] = {
            type: $('#filter__type__status').val(),
            value: $('#filter__value__status').children(':selected').val()
        }
    }
    if ($('#filter__enable__author').is(':checked')) {
        filter_values['author'] = {
            type: 'is',
            value: parseInt($('#filter__value__author').children(':selected').val())
        }
    }
    if ($('#filter__enable__component').is(':checked')) {
        var filter_val = $('#filter__value__component').val();
        if (filter_val.length > 0) {
            filter_values['component'] = {
                type: $('#filter__type__component').val(),
                value: filter_val
            }
        }
    }
    view_values['filters'] = filter_values;
    return JSON.stringify(view_values);
}

function collect_attrs_data() {
    var attrs = [];
    $("input[id^='attr_checkbox__']").each(function () {
        var attr = {
            attr: $(this).val(),
            is_compare: false
        };
        if ($(this).is(':checked')) {
            attr['is_compare'] = true;
        }
        attrs.push(attr);
    });
    return attrs;
}


function collect_new_markdata() {
    var is_modifiable_checkbox = $('#is_modifiable'), is_modifiable = true,
        mark_type = $('#report_type').val(), mark_data,
        description = $('#mark_description').val();

    var tmp_div = $('<div>').html(description);
    tmp_div.find('script').remove();
    tmp_div.find('*').each(function () {
        var element_in_div = $(this);
        $.each($(this)[0].attributes, function (i, attr) {
            if (attr.name.match("^on")) {
                element_in_div.removeAttr(attr.name)
            }
        });
    });
    description = tmp_div.html();

    if (is_modifiable_checkbox.length) {
        is_modifiable = is_modifiable_checkbox.is(':checked') ? true:false;
    }

    if (mark_type == 'unknown') {
        var unknown_function = $('#unknown_function').val(),
            unknown_problem_pattern = $('#unknown_problem_pattern').val();
        if (unknown_function.length <= 0) {
            err_notify($('#error__function_required').text());
        }
        if (unknown_problem_pattern.length <= 0) {
            err_notify($('#error__problem_required').text());
        }
        mark_data = {
            report_id: $('#report_pk').val(),
            status: $("input[name='selected_status']:checked").val(),
            data_type: mark_type,
            is_modifiable: is_modifiable,
            problem: unknown_problem_pattern,
            function: unknown_function,
            link: $('#unknown_link').val(),
            description: description
        };
    }
    else {
        mark_data = {
            attrs: collect_attrs_data(),
            report_id: $('#report_pk').val(),
            verdict: $("input[name='selected_verdict']:checked").val(),
            status: $("input[name='selected_status']:checked").val(),
            data_type: mark_type,
            is_modifiable: is_modifiable,
            tags: $('#tag_list').val(),
            description: description
        };
    }

    if (mark_type == 'unsafe') {
        mark_data['convert_id'] = $("#convert_function").val();
        mark_data['compare_id'] = $("#compare_function").val();
    }

    return JSON.stringify(mark_data);
}


function collect_markdata() {
    var is_modifiable_checkbox = $('#is_modifiable'), is_modifiable = true,
        mark_type = $('#mark_type').val(), mark_data, description = $('#mark_description').val();

    var tmp_div = $('<div>').html(description);
    tmp_div.find('script').remove();
    tmp_div.find('*').each(function () {
        var element_in_div = $(this);
        $.each($(this)[0].attributes, function (i, attr) {
            if (attr.name.match("^on")) {
                element_in_div.removeAttr(attr.name)
            }
        });
    });
    description = tmp_div.html();

    if (is_modifiable_checkbox.length) {
        is_modifiable = is_modifiable_checkbox.is(':checked') ? true:false;
    }

    if (mark_type == 'unknown') {
        var unknown_function = $('#unknown_function').val(),
            unknown_problem_pattern = $('#unknown_problem_pattern').val();
        if (unknown_function.length <= 0) {
            err_notify($('#error__function_required').text());
        }
        if (unknown_problem_pattern.length <= 0) {
            err_notify($('#error__problem_required').text());
        }
        mark_data = {
            mark_id: $('#mark_pk').val(),
            status: $("input[name='selected_status']:checked").val(),
            data_type: mark_type,
            is_modifiable: is_modifiable,
            problem: unknown_problem_pattern,
            function: unknown_function,
            link: $('#unknown_link').val(),
            comment: $('#edit_mark_comment').val(),
            description: description
        };
    }
    else {
        mark_data = {
            attrs: collect_attrs_data(),
            mark_id: $('#mark_pk').val(),
            verdict: $("input[name='selected_verdict']:checked").val(),
            status: $("input[name='selected_status']:checked").val(),
            data_type: mark_type,
            is_modifiable: is_modifiable,
            tags: $('#tag_list').val(),
            comment: $('#edit_mark_comment').val(),
            description: description
        };
    }

    if (mark_type == 'unsafe') {
        mark_data['compare_id'] = $("#compare_function").val();
    }

    return JSON.stringify(mark_data);
}

function set_action_on_func_change() {
    $.ajax({
        url: marks_ajax_url + 'get_func_description/',
        data: {func_id: $(this).children('option:selected').val(), func_type: 'compare'},
        type: 'POST',
        success: function (data) {
            if (data.error) {
                err_notify(data.error);
            }
            else if (data.description) {
                $('#compare_function_description').text(data.description);
            }

        }
    });
}

function set_actions_for_mark_versions_delete() {
    $('.ui.checkbox').checkbox();
    $('#remove_versions_popup').modal({transition: 'fly up', autofocus: false, closable: false});
    $('#show_remove_mark_versions_popup').click(function () {
        $('#remove_versions_popup').modal('show');
    });
    $('#cancel_remove_mark_versions').click(function () {
        $('#remove_versions_popup').modal('hide');
    });
    $('#cancel_del_versions_mark_btn').click(function () {
        window.location.replace('');
    });
    $('#reload_page__versions').click(function () {
        window.location.replace('');
    });

    $('#delete_versions_btn').click(function () {
        $('#remove_versions_popup').modal('hide');
        var checked_versions = [];
        $('input[id^="checkbox_version__"]').each(function () {
            if ($(this).is(':checked')) {
                checked_versions.push($(this).attr('id').replace('checkbox_version__', ''));
            }
        });
        $.post(
            marks_ajax_url + 'remove_versions/',
            {
                mark_id: $('#mark_pk').val(),
                mark_type: $('#mark_type').val(),
                versions: JSON.stringify(checked_versions)
            },
            function (data) {
                var global_parent = $('#versions_rows');
                $.each(checked_versions, function (i, val) {
                    var version_line = $("#checkbox_version__" + val).closest('.version-line');
                    if (version_line.length) {
                        version_line.remove();
                    }
                });
                data.status === 0 ? success_notify(data.message) : err_notify(data.message);
                if (global_parent && global_parent.children().first().children().length == 0) {
                    $('#versions_to_delete_form').remove();
                    $('#no_versions_to_delete').show();
                }
            },
            'json'
        );
    });
}

function activate_tags() {
    $('#tag_list').dropdown({
        allowAdditions: true,
        className: {
            label: 'ui label ' + $('#tag_label_color').text(),
            selected: 'klever-active'
        },
        message: {
            addResult: $('#tags__add_tag').text() + ' <b>{term}</b>'
        },
        onChange: function(value) {
            var last_added_tag = value.slice(-1)[0];
            if (last_added_tag && last_added_tag.length > 15) {
                value.pop();
                var available_tags = [], taglist = $('#tag_list');
                taglist.children('option').each(function () {
                    if ($(this).val() != last_added_tag && value.indexOf($(this).val()) < 0 && $(this).val()) {
                        available_tags.push($(this).val());
                    }
                });
                taglist.parent().remove();
                $('label[for=tag_list]').after($('<select>', {
                    class: 'ui search selection dropdown fluid',
                    multiple: true,
                    id: 'tag_list'
                }));
                $.each(value, function (i, v) {
                    $('#tag_list').append($('<option>', {
                        value: v,
                        text: v,
                        selected: true
                    }));
                });
                $.each(available_tags, function (i, v) {
                    $('#tag_list').append($('<option>', {
                        value: v,
                        text: v
                    }));
                });
                activate_tags();
                err_notify($('#error__tag_is_long').text());
            }
        }
    });
    return false;
}

$(document).ready(function () {
    var view_type_input = $('#view_type');
    if (view_type_input.length) {
        set_actions_for_views(view_type_input.val(), collect_filters_data);
    }
    activate_tags();
    $('.ui.dropdown').each(function () {
        if (!$(this).hasClass('search')) {
            $(this).dropdown();
        }
    });
    $('.normal-popup').popup({position: 'bottom center'});
    $('#remove_mark_popup').modal({transition: 'fly up', autofocus: false, closable: false})
        .modal('attach events', '#show_remove_mark_popup', 'show');
    $('#cancel_remove_mark').click(function () {
        $('#remove_mark_popup').modal('hide');
    });

    $('#remove_marks_popup').modal({transition: 'fly up', autofocus: false, closable: false});
    $('#show_remove_marks_popup').click(function () {
        var ids_for_del = [];
        $('input[id^="mark_checkbox__"]').each(function () {
            if ($(this).is(':checked')) {
                ids_for_del.push($(this).attr('id').replace('mark_checkbox__', ''));
            }
        });
        if (ids_for_del.length > 0) {
            $('#remove_marks_popup').modal('show');
        }
        else {
            err_notify($('#no_marks_selected').text())
        }
    });
    $('#cancel_remove_marks').click(function () {
        $('#remove_marks_popup').modal('hide');
    });
    $('#confirm_remove_marks').click(function () {
        var ids_for_del = [];
        $('input[id^="mark_checkbox__"]').each(function () {
            if ($(this).is(':checked')) {
                ids_for_del.push($(this).attr('id').replace('mark_checkbox__', ''));
            }
        });
        if (ids_for_del.length == 0) {
            $('#remove_marks_popup').modal('hide');
            err_notify($('#no_marks_selected').text());
        }
        else {
            $.ajax({
                url: marks_ajax_url + 'delete/',
                data: {
                    'type': $('#marks_type').val(),
                    ids: JSON.stringify(ids_for_del)
                },
                type: 'POST',
                success: function (data) {
                    if (data.error) {
                        err_notify(data.error);
                    }
                    else {
                        window.location.replace('');
                    }
                }
            });
        }
    });

    $('#save_new_mark_btn').click(function () {
        $.redirectPost(marks_ajax_url + 'save_mark/', {savedata: encodeData(collect_new_markdata())});
    });

    $('#convert_function').change(function () {
        $.ajax({
            url: marks_ajax_url + 'get_func_description/',
            data: {func_id: $(this).children('option:selected').val(), func_type: 'convert'},
            type: 'POST',
            success: function (data) {
                if (data.error) {
                    err_notify(data.error);
                }
                else if (data.description) {
                    $('#convert_function_description').text(data.description);
                }

            }
        });
    });

    $('#compare_function').change(set_action_on_func_change);

    $('#mark_version_selector').change(function () {
        $.ajax({
            url: marks_ajax_url + 'get_mark_version_data/',
            data: {
                version: $(this).val(),
                mark_id: $('#mark_pk').val(),
                type: $('#mark_type').val()
            },
            type: 'POST',
            success: function (data) {
                if (data.error) {
                    err_notify(data.error);
                }
                else {
                    $('#mark_data_div').html(data.data);
                    $('#compare_function').change(set_action_on_func_change);
                    activate_tags();
                    $('.ui.dropdown').each(function () {
                        if (!$(this).hasClass('search')) {
                            $(this).dropdown();
                        }
                    });
                    $('.ui.checkbox').checkbox();
                    $('.ui.accordion').accordion();
                }
            }
        });
    });

    $('#save_mark_btn').click(function () {
        var comment_input = $('#edit_mark_comment');
        if (comment_input.val().length > 0) {
            $.redirectPost(marks_ajax_url + 'save_mark/', {savedata: encodeData(collect_markdata())});
        }
        else {
            err_notify($('#error__comment_required').text());
            comment_input.focus();
        }
    });

    $('#edit_mark_versions').click(function () {
        $.post(
            marks_ajax_url + 'getversions/',
            {mark_id: $('#mark_pk').val(), mark_type: $('#mark_type').val()},
            function (data) {
                try {
                    JSON.stringify(data);
                    err_notify(data.message);
                } catch (e) {
                    $('#div_for_version_list').html(data);
                    set_actions_for_mark_versions_delete();
                }
            }
        );
    });
});