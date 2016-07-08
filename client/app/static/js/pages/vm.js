/**
 * Created by Alex on 08.07.2016.
 */
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
                                '<input type="checkbox" value="'+ data[i].uuid+'">'+data[i].host+
                            '</label></div></td>' +
                            '<td>'+data[i].pool+'</td>' +
                        '</tr>');
            }

        }
    });
}
fillTable();

$('#backupBtn').on('click', function () {
    $.ajax({
        url: '/backup/',
        type: 'POST',
        data: $('.checkbox:checked'),
        dataType: 'json'
    })
});