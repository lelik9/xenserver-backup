/**
 * Created by Alex on 10.07.2016.
 */
function fillHostSrTable(){
    $.ajax({
        url: '/storage/',
        type: 'GET',
        data: {'get': 'host_sr'},
        dataType: 'json',
        success: function (data) {
            if(data.type.localeCompare('success') == 0) {
                $('td').remove();
                var res = data.result;

                for (var a = 0; a < res.length; a++) {
                    var sr = res[a].sr;

                    for (var i = 0; i < sr.length; i++) {
                        $('#hostSrTable').append(
                            '<tr>' +
                                '<td>' + sr[i].name + '</td>' +
                                '<td>' + sr[i].type + '</td>' +
                                '<td>' + (sr[i].size / 1000000 >> 0) + '/' + (sr[i].utilization / 1000000 >> 0) + '</td>' +
                                '<td>' + sr[i].share + '</td>' +
                                '<td>' + res[a].pool + '</td>' +
                            '</tr>');
                    }
                }
            }
        }
    });
}
fillHostSrTable();