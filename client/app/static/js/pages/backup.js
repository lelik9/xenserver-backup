/**
 * Created by Alex on 21.07.2016.
 */
function fillBackupTable() {
    request('/backups/', 'GET', {get: 'backups'}, null, fill);
    function fill(data) {
        var table = $('#backupTable');
        var res = data['responseJSON'].result;
        var html = '';

        table.find('td').remove();

        for (var i = 0; i < res.length; i++) {
            html +=
                '<tr>' +
                    '<td><div class="checkbox"><label>' +
                        '<input id="backupCheckBox" type="checkbox" name="check" value="' + res[i]['_id'] + '">' + res[i]['vm_name'] +
                        '</label></div>' +
                    '</td>'  +
                    '<td>' + res[i]['_id'] + '</td>' +
                '</tr>'
        }
        table.append(html);
    }
}
fillBackupTable();

$('#restore').on('click', function () {
    console.log($('#hostSelect').value);
    var data = {
        vm_name: document.getElementById('vmName').value,
        host_obj: "OpaqueRef:012c9d17-05b2-0a07-26a9-b0cf2f82b2e8",
        sr: document.getElementById('srSelect').value,
        backup_id: "2016-07-22_17-56"
    };
    console.log('!!!!!!!!!!');
    request('/backup/', 'UPDATE', data, null, onSuccess)
});

$('#removeBtn').on('click', function () {
    var backups = [];
    $('input[name=check]:checked').each(function() {
       backups.push($(this).val());
     });
   request('/backup/', 'DELETE', {backup: backups}, null, null)
});

function getHostSR() {
    var host = document.getElementById('hostSelect').value;
    var sr_select = document.getElementById('srSelect');

    request('/storage/', 'GET', {get:'host_sr'}, null, fill_select);

    function fill_select(data) {
        console.log(data)
    }
}
getHostSR();