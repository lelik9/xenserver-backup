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

function fillBackupSrTable(){
    $.ajax({
        url: '/storage/',
        type: 'GET',
        data: {'get': 'backup_sr'},
        dataType: 'json',
        success: function (data) {
            if(data.type.localeCompare('success') == 0) {
                $('td').remove();
                var sr = data.result;

                    for (var i = 0; i < sr.length; i++) {
                        $('#backupSrTable').append(
                            '<tr>' +
                                '<td>' + sr[i]['_id'] + '</td>' +
                                '<td>' + sr[i]['sr_type'] + '</td>' +
                                '<td>' + sr[i]['share_path'] + '</td>' +
                            '</tr>');
                    }
            }
        }
    });
}
fillBackupSrTable();

function showUserInput(){
    var share = document.getElementById('protocolSelect').value;
    var loginGroup = document.getElementById('loginGroup');
    var passwordGroup = document.getElementById('passwordGroup');
    var inputPath = document.getElementById('inputPath');
    var loginField =  document.getElementById('inputLogin');
    var passwordField =  document.getElementById('inputPassword');

    loginGroup.style.display = 'none';
    passwordGroup.style.display = 'none';
    loginField.required = false;
    passwordField.required = false;

    if (share.localeCompare('smb') == 0){
        loginGroup.style.display = 'block';
        passwordGroup.style.display = 'block';
        inputPath.placeholder="\\\\10.10.10.10\\smb";
        loginField.required = true;
        passwordField.required = true;
    }else if(share.localeCompare('nfs') == 0) {
        inputPath.placeholder="10.10.10.10:/nfs"
    }else if(share.localeCompare('folder') == 0) {
        inputPath.placeholder="/backup_restore/path"
    }
}

$('#srForm').submit(function () {
    var $progress = $('#progress');

    $.ajax({
        url: '/backup_sr/',
        type: 'POST',
        data: $(this).serializeArray(),
        dataType:'json',
        start: $progress.show(),
        complete: function (data) {
            var res = data['responseJSON'];

            $progress.hide();
            $.notify(res['result'], res['type']);
            if(res['type'] == 'success'){
                $('#srModal').modal('hide');
                fillBackupSrTable();
            }
        }
    });
    return false;
});