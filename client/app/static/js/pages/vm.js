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
                            '<input id="vmCheckBox" type="checkbox" name="check" value="' + vm[i].obj + '">' + vm[i].name +
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
    $('#backupModal').modal('show');
});

$('#yesButton').on('click', function () {
    var vm = [];
    $('input[name=check]:checked').each(function() {
       vm.push($(this).val());
     });
    var data = {vm: vm,
                sr: document.getElementById('srSelect').value};
    request('/backup_restore/', 'POST', data, onBackupStart, onBackupSuccess);
});

function onBackupStart() {
    $.notify('VM backup_restore start', 'info')
}
function onBackupSuccess(data) {
    var res = data['responseJSON'];
    $.notify(res['result'], res['type']);
}