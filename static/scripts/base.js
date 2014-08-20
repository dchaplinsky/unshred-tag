$(function(){
    $.ajaxSetup({
        traditional: true
    });

    var current_shred = $("#current_shred");

    function collect_data() {
        var data = $(".textarea-tags").textext()[0].hiddenInput().val();

        data = JSON.parse(data);
        return {
            "_id": $("#shred_id").val(),
            "tagging_start": $("#tagging_start").val(),
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

    if (window.user) {
        $.get(window.urls.next, load_next);

        if (!$.cookie('help')) {
            $.cookie('help', '1', {
                expires: 365,
                path: '/'
            });
            $('.popup-with-zoom-anim').click();
        }
    }
});
