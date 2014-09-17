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
            "tagging_start": $("#tagging_start").val(),
            "tags": data,
            "recognizable_chars": $("#rec-chars").val()
        };
    }

    function assign_hotkeys(elem) {
        elem
            .bind('keydown', 'alt+return', function(e) {
                $("a#save-button").click();
            })
            .bind('keydown', 'f1', function(e) {
                e.preventDefault();
                $('.popup-with-zoom-anim').click();
            })
            .bind('keydown', 'ctrl+g', rotate_cw)
            .bind('keydown', 'ctrl+h', rotate_ccw)
            .bind('keydown', 'ctrl+i', function(e) {
                e.preventDefault();
                $('a.btn-tools.info').click();
            });
    }

    function load_next(data) {
        degree = 0;
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
        }).bind('isTagAllowed', function(e, data){
            var formData = tags_area.textext()[0].hiddenInput().val();
                list = JSON.parse(formData);

            if (formData.length && list.indexOf(data.tag) >= 0) {
               data.result = false;
            }
        });

        if (tags_area.length) {
            tags_area.textext()[0].focusInput();
        }


        assign_hotkeys(current_shred.find("textarea"));

        $("img.zoom-it").each(function() {
            $(this).image_zoomer({height: 130, width: 130, scale: 2});
        });

        $(".btn-tools").tooltip({"placement": "bottom"});

        $('#additional-info-link').magnificPopup({
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
    }

    $(document.body)
        .on("click", "a#save-button", function(e) {
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
        })
        .on("click", "a.btn-tools.cw", rotate_cw)
        .on("click", "a.btn-tools.ccw", rotate_ccw);

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

    if (window.user && current_shred.length) {
        $.get(window.urls.next, load_next);

        if (!$.cookie('help')) {
            $.cookie('help', '1', {
                expires: 365,
                path: '/'
            });
            $('.popup-with-zoom-anim').click();
        }
    }

    function rotate(val) {
        degree = (degree + val + 360) % 360;
        $(".shred-img")
            .data("angle", degree)
            .rotate({angle: degree});
    }
    
    function rotate_ccw(e) {
        e.preventDefault();
        rotate(-90);
    }

    function rotate_cw(e) {
        e.preventDefault();
        rotate(90);
    }
});
