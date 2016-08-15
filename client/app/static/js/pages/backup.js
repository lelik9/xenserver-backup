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
    var pool = document.getElementById('hostSelect').value;
    var sr = document.getElementById('srSelect').value;
    var vm = [];

    $('input[name=check]:checked').each(function() {
       vm.push($(this).val());
     });

    var data = {
        vm_name: document.getElementById('vmName').value,
        pool: pool,
        sr: sr,
        backup_id: vm
    };
    console.log(data);
    request('/backup/', 'UPDATE', data, null, onSuccess);
});

$('#removeBtn').on('click', function () {
    var backups = [];
    $('input[name=check]:checked').each(function() {
       backups.push($(this).val());
     });
   request('/backup/', 'DELETE', {backup: backups}, null, null)
});

function getHostSR() {
    var pool = document.getElementById('hostSelect').value;
    var sr_select = $("#srSelect");

    request('/storage/', 'GET', {get:'host_sr', 'pool':pool}, null, fill_select);

    function fill_select(data) {
        var result = data['responseJSON'].result;
        var sr = result.sr;
        var html = '';

        sr_select.empty();

        for(var i = 0; i < sr.length; i++){
            html += "<option value="+sr[i]['obj']+">"+sr[i]['name']+"</option>";
        }
        sr_select.append(html);
    }
}
getHostSR();