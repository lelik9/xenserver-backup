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
                            '<td><input type="checkbox" class="checkbox" value="'+ data[i].uuid+'">'+data[i].host+'</td>' +
                            '<td>'+data[i].pool+'</td>' +
                        '</tr>');
            }

        }
    });
};
fillTable();