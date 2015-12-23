$(document).ready(function () {
    $('button[id^="rename_component_btn__"]').click(function () {
        var component_id = $(this).attr('id').replace('rename_component_btn__', '');
        $.post(
            '/tools/ajax/change_component/',
            {
                action: 'rename',
                component_id: component_id,
                name: $('#component_name_input__' + component_id).val()
            },
            function (data) {
                if (data.error) {
                    err_notify(data.error);
                }
                else {
                    success_notify(data.message);
                }
            }
        ).fail(function (x) {
                console.log(x.responseText);
            });
    });
    $('button[id^="delete_component_btn__"]').click(function () {
        var component_id = $(this).attr('id').replace('delete_component_btn__', '');
        $.post(
            '/tools/ajax/change_component/',
            {
                action: 'delete',
                component_id: component_id
            },
            function (data) {
                if (data.error) {
                    err_notify(data.error);
                }
                else {
                    success_notify(data.message);
                    $('#component__' + component_id).remove();
                }
            }
        ).fail(function (x) {
                console.log(x.responseText);
            });
    });
    $('#clear_all_components').click(function () {
        $.post(
            '/tools/ajax/clear_components_table/',
            {},
            function (data) {
                if (data.error) {
                    err_notify(data.error);
                }
                else {
                    success_notify(data.message);
                }
            }
        ).fail(function (x) {
                console.log(x.responseText);
            });
    });
    $('#clear_all_problems').click(function () {
        $.post(
            '/tools/ajax/clear_problems/',
            {},
            function (data) {
                if (data.error) {
                    err_notify(data.error);
                }
                else {
                    success_notify(data.message);
                }
            }
        ).fail(function (x) {
                console.log(x.responseText);
            });
    });
    $('button[id^="delete_problem_btn__"]').click(function () {
        var problem_id = $(this).attr('id').replace('delete_problem_btn__', '');
        $.post(
            '/tools/ajax/delete_problem/',
            {
                problem_id: problem_id
            },
            function (data) {
                if (data.error) {
                    err_notify(data.error);
                }
                else {
                    success_notify(data.message);
                    $('#problem__' + problem_id).remove();
                }
            }
        ).fail(function (x) {
                console.log(x.responseText);
            });
    });

    $('#clear_system').click(function () {
        $('#dimmer_of_page').addClass('active');
        $.post(
            '/tools/ajax/clear_system/',
            {},
            function (data) {
                $('#dimmer_of_page').removeClass('active');
                if (data.error) {
                    err_notify(data.error);
                }
                else {
                    success_notify(data.message);
                }
            }
        ).fail(function (x) {
            console.log(x.responseText);
        });
    });
    $('#recalc_for_all_jobs_checkbox').checkbox({
        onChecked: function () {
            $('input[id^="job__"]').each(function () {
                $(this).prop('checked', true);
                $(this).parent().addClass('disabled');
            });
        },
        onUnchecked: function () {
            $('input[id^="job__"]').each(function () {
                $(this).prop('checked', false);
                $(this).parent().removeClass('disabled');
            });
        }
    });

    function get_data() {
        var jobs = [];
        if ($('#recalc_for_all_jobs').is(':checked')) {
            return {};
        }
        $('input[id^="job__"]').each(function () {
            if ($(this).is(':checked')) {
                jobs.push($(this).attr('id').replace('job__', ''));
            }
        });
        return {'jobs': JSON.stringify(jobs)};
    }
    $('button[id^="recalc_"]').click(function () {
        var data = get_data();
        data['type'] = $(this).attr('id').replace('recalc_', '');
        $('#dimmer_of_page').addClass('active');
        $('button[id^="recalc_"]').addClass('disabled');
        $.post(
            '/tools/ajax/recalculation/',
            data,
            function (data) {
                $('#dimmer_of_page').removeClass('active');
                $('button[id^="recalc_"]').removeClass('disabled');
                if (data.error) {
                    err_notify(data.error);
                }
                else {
                    success_notify(data.message);
                }
            }
        ).fail(function (x) {
            console.log(x.responseText);
        });
    });
});