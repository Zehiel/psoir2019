// ----- custom js ----- //

// global
var data = [];

var albumBucketName = 'psoir-photo-vault';
var bucketRegion = 'us-west-2';
var IdentityPoolId = 'us-west-2:2d580e56-4ae2-4ca4-9472-9791bcf40fac';

AWS.config.update({
    region: bucketRegion,
    credentials: new AWS.CognitoIdentityCredentials({
        IdentityPoolId: IdentityPoolId
    })
});

var s3 = new AWS.S3({
    params: {Bucket: albumBucketName}
});

function deactivate(image) {
    $(image).removeClass("active");
    var ind = data.indexOf(getKey(image));
    if (ind > -1) {
        data.splice(ind, 1);
    }
}

function activate(image) {
    $(image).addClass("active");
    var ind = data.indexOf(getKey(image));
    if (ind < 0) {
        data.push(getKey(image));
    }
}

function getKey(image) {
    return $(image).attr("data-photoKey");
}

$(function () {

    // image click
    $(".img").click(function () {
        if ($(this).hasClass("active")) {
            deactivate(this);
        } else {
            activate(this);
        }

    });

});

function selectAll() {
    $("#images").children("img").each(function () {
        activate(this);
    });
}

function unselectAll() {
    $("#images").children("img").each(function () {
        deactivate(this);
    });
}

function process() {
    console.log(data);
    console.log(getDataObjects());

    if (data.length < 1) {
        alert("No photo selected.");
        return;
    }

    $('#processingModal').modal();

    $.ajax({
        beforeSend: function (xhr) { //before requesting data
            xhr.setRequestHeader("Content-Type", "application/json");
        },
        type: "POST",
        url: "/process",
        data: JSON.stringify(getDataObjects()),
        dataType: 'json',
        success: function (result) {
            console.log('result:', result);
            // $('#processingModal').modal('toggle');
            // refreshImgs();
        },
        error: function (error) {
            console.log(error);
            // $('#processingModal').modal('toggle');
            alert('There was an error processing your request: ' + error.statusText);
        }
    });
}

function refreshImgs() {
    window.location.reload(true);
}

function addPhoto() {
    var files = document.getElementById('photoUpload').files;
    if (!files.length) {
        return alert('Please choose a file to upload first.');
    }

    var btn = $('#uploadButton');
    var loadingText = '<i class="fa fa-circle-o-notch fa-spin"></i> Uploading...';

    if (btn.html() !== loadingText) {
        btn.addClass('disabled');
        btn.data('original-text', btn.html());
        btn.html(loadingText);
    }

    var file = files[0];
    var photoKey = file.name;

    s3.upload({
        Key: photoKey,
        Body: file,
        ACL: 'public-read'
    }, function (err, data) {
        btn.html(btn.data('original-text'));
        btn.removeClass('disabled');
        if (err) {
            console.log(err);
            return alert('There was an error uploading photo: ' + err.message);
           
        }
        $('#uploadModal').modal('toggle');
        refreshImgs();
    });
}

function deletePhoto(photoKey) {
    if (!data.length) {
        return alert('No photo selected.');
    }

    var btn = $('#deleteButton');
    var loadingText = '<i class="fa fa-circle-o-notch fa-spin"></i> Deleting...';

    if (btn.html() !== loadingText) {
        btn.addClass('disabled');
        btn.data('original-text', btn.html());
        btn.html(loadingText);
    }

    var params = {
        Delete: {
            Objects: getDataObjects(),
            Quiet: false
        }
    };

    s3.deleteObjects(params, function (err, data) {
        btn.html(btn.data('original-text'));
        btn.removeClass('disabled');
        if (err) {
            return alert('There was an error deleting this photo: ' + err.message);
        }
        refreshImgs();
    });
}

function getDataObjects() {
    var objects = [];
    for (var i = 0; i < data.length; i++) {
        objects.push({"Key": data[i]});
    }
    return objects;
}
