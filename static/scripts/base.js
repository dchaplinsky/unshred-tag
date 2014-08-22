$(function(){
    $.ajaxSetup({
        traditional: true
    });

    var current_shred = $("#current_shred");
    var degree = 0;

    function collect_data() {
        var data = $(".textarea-tags").textext()[0].hiddenInput().val();

        data = JSON.parse(data);
        if (data.length && !!degree) data.push("Поворот на " + degree + " градусов");
        return {
            "_id": $("#shred_id").val(),
            "tags": data
        };
    }

    function load_next(data) {
        current_shred.css("visibility", "visible").html(data);

        var tags_area = current_shred.find('.textarea-tags'),
            suggs = tags_area.data("suggestions"),
            auto_tags = tags_area.data("auto_tags");

        tags_area.textext({
            plugins: 'tags autocomplete suggestions prompt arrow',
            tagsItems: auto_tags,
            autocomplete: {
                dropdown: {
                    maxHeight : '200px'
                }
            },

            prompt: 'Укажите тэги',
            suggestions: suggs,
        }).textext()[0].focusInput();


        current_shred.find("textarea.textarea-tags").bind(
            'keydown', 'alt+return',
            function(e) {
                $("a#save-button").click();
            }).bind('keydown', 'f1', function(e){
                $('.popup-with-zoom-anim').click();
            });
    }

    if (window.urls != undefined) {
        $.get(window.urls.next, load_next);
    }

    $(document.body).on("click", "a#save-button", function(e) {
        e.preventDefault();
        form = collect_data();

        if (form["tags"].length === 0) {
            if (window.confirm("Вы не ввели тэгов для этого фрагмента. Пропустить его?")) {
                current_shred.css("visibility", "hidden");

                $.post(window.urls.skip, form, load_next);
            }
        } else {
            current_shred.css("visibility", "hidden");

            $.post(window.urls.next, form, load_next);
        }
    }).bind('keydown', 'alt+return', function(e) {
        $("a#save-button").click();
    }).bind('keydown', 'f1', function(e){
        e.preventDefault();
        $('.popup-with-zoom-anim').click();
    });

    $('.popup-with-zoom-anim').magnificPopup({
        type: 'inline',

        fixedContentPos: false,
        fixedBgPos: true,
        overflowY: 'auto',
        closeBtnInside: true,
        preloader: false,

        midClick: true,
        removalDelay: 100,
        mainClass: 'my-mfp-zoom-in'
    });


    function rotate(val) {
        $(".shred-img").rotate({angle: val});
        if (val == 90 || val == 270) {
            $(".shred-img").addClass('vertical');
        } else {
            $(".shred-img").removeClass('vertical');
        }
    }

    $(document.body).on("click", ".btn-group .btn", function() {
        var val = parseInt($(this).find('input').val());
        rotate(val);
        degree = val;
    });

    function rotate_ccw() {
        degree = (degree - 90 + 360) % 360;
        rotate(degree);
    }

    function rotate_cw() {
        degree = (degree + 90) % 360;
        rotate(degree);
    }

    $(document.body).bind('keydown', 'ctrl+z', rotate_ccw
        ).bind('keydown', 'cmd+z', rotate_cw
        ).bind('keydown', 'ctrl+x', rotate_cw
        ).bind('keydown', 'cmd+x', rotate_cw);

});
