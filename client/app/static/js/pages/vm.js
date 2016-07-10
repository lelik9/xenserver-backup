/**
 * Created by Alex on 08.07.2016.
 */
function fillTable(){
    $.ajax({
        url: '/vms/',
        type: 'GET',
        data: {'get': 'table'},
        dataType: 'json',
        success: function (data) {
            if(data.type.localeCompare('success') == 0) {
                $('td').remove();
                var res = data.result;

                for (var a = 0; a < res.length; a++) {
                    var vm = res[a].vm;

                    for (var i = 0; i < vm.length; i++) {
                        $('#vmTable').append(
                            '<tr>' +
                            '<td><div class="checkbox"><label>' +
                            '<input type="checkbox" name="check" value="' + vm[i].obj + '">' + vm[i].name +
                            '</label></div></td>' +
                            '<td>' + (vm[i].memory / 1000000 >> 0)+ '</td>' +
                            '<td>' + vm[i].CPU + '</td>' +
                            '<td>' + vm[i].state + '</td>' +
                            '<td>' + res[a].pool + '</td>' +
                            '</tr>');
                    }
                }
            }
        }
    });
}
fillTable();

$('#backupBtn').on('click', function () {
    $.ajax({
        url: '/backup/',
        type: 'POST',
        data: $('input[name=check]:checked'),
        dataType: 'json'
    })
});