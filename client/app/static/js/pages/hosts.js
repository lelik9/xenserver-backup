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
            $progress.hide();
            $('#hostModal').modal('hide');
            var mes = data['responseJSON'];
            $.notify(mes['message'], mes['type']);
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
            $('td').remove();
            for (var i=0; i<data.length; i++){
                $('#hostsTable').append(
                        '<tr>' +
                            '<td><div class="checkbox"><label>' +
                                '<input type="checkbox" name="check" value="'+ data[i].uuid+'">'+data[i].host+
                            '</label></div></td>' +
                            '<td>'+data[i].pool+'</td>' +
                            '<td>'+data[i].ip+'</td>' +
                        '</tr>');
            }

        }
    });
}
fillTable();