/**
 * Created by Alex on 07.07.2016.
 */
$('#hostForm').submit(function(){
    $.post(
        '/host/',
        $(this).serializeArray(),
        fillTable()
    );
    return false;
});

$('#rmHost').on('click', function(){
    $.ajax({
        url: '/host/',
        type: 'DELETE',
        data: {'id':'1'}
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
                $('#hostsTable').append('<tr><td>'+data[i].host+'</td>' +
                        '<td>'+data[i].pool+'</td>' +
                        '<td>'+data[i].ip+'</td></tr>');
            }

        }
    });
};
fillTable();