// window.locationでurl_forを使うやり方が分からなかった．
// 今はこのjsは使ってないよ
$(function () {
    $(".user-delete-link").on("click", function() {
        var delete_url = $(this).attr('data-delete-url');
        $.ajax({
            url: delete_url,
            type: 'DELETE',
            success: function (response) {
                if(response.status == 'OK') {
                    window.location = '\{\{ url_for(\"userlist\") \}\}';
                } else {
                    alert('Delete failed');
                }
            }
        });
        return false;
    });
});