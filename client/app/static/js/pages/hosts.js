/**
 * Created by Alex on 07.07.2016.
 */
$('#hostForm').submit(function(){
    var $progress = $('#progress');
    $.ajax({
        url: '/host/',
        type: 'POST',
        data: $(this).serializeArray(),
        dataType: 'json',
        start: $progress.show(),
        complete: function (data) {
            var res = data['responseJSON'];
            if(res['type'] == 'success'){
                $('#hostModal').modal('hide');
                fillTable()
            }
            $progress.hide();
            $.notify(res['result'], res['type']);
        }
    });
    return false;
});

$('#rmHost').on('click', function(){
    $.ajax({
        url: '/host/',
        type: 'DELETE',
        data: $('input[name=check]:checked'),
        dataType: 'json',
        complete: function (data) {
            var mes = data['responseJSON'];
            $.notify(mes['message'], mes['type']);
        }
    });
});

function fillTable(){
    $.ajax({
        url: '/hosts/',
        type: 'GET',
        data: {'get': 'table'},
        dataType: 'json',
        success: function (data) {
            console.log(data.type);
            if(data.type.localeCompare('success') == 0) {
                $('td').remove();

                var res = data.result;

                for (var a = 0; a < res.length; a++) {
                    var hosts = res[a].hosts;

                    for (var i = 0; i < hosts.length; i++) {
                        $('#hostsTable').append(
                            '<tr>' +
                            '<td><div class="checkbox"><label>' +
                            '<input type="checkbox" name="check" value="' + hosts[i].obj + '">' + hosts[i].name +
                            '</label></div></td>' +
                            '<td>' + hosts[i].ip + '</td>' +
                            '<td>' + hosts[i].live + '</td>' +
                            '<td>' + (hosts[i].mem_total / 1000000 >> 0) + '/' + (hosts[i].mem_free / 1000000 >> 0) + ' MB</td>' +
                            '<td>' + res[a].pool + '</td>' +
                            '</tr>');
                    }
                }
            }
        }
    });
}
fillTable();