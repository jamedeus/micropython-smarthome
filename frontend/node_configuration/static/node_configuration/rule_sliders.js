// Initialize all range sliders, add listeners
for (slider of $('input[type="range"]')) {
    // Initialize
    $('#' + slider.id).rangeslider({
        polyfill: false,
        onInit: function() {
        // Select handle element closest to slider, update displayed rule
        $handle = $('.rangeslider__handle', this.$range);
        $handle[0].textContent = get_display_value(slider);

        this.$range[0].classList.add("mx-auto")
        }
    });

    // Update current rule displayed while slider moves
    $('#' + slider.id).on('input', function(e) {

        // Select handle element closest to slider, update displayed rule
        var $handle = $('.rangeslider__handle', e.target.nextSibling);
        $handle[0].textContent = get_display_value(document.getElementById(e.target.id));
    });
};



function add_new_slider(id) {
    slider = document.getElementById(id);

    // Initialize
    $('#' + id).rangeslider({
        polyfill: false,
        onInit: function() {
        // Select handle element closest to slider, update displayed rule
        $handle = $('.rangeslider__handle', this.$range);
        $handle[0].textContent = get_display_value(slider);

        this.$range[0].classList.add("mx-auto")
        }
    });

    // Update current rule displayed while slider moves
    $('#' + id).on('input', function(e) {

        // Select handle element closest to slider, update displayed rule
        var $handle = $('.rangeslider__handle', e.target.nextSibling);
        $handle[0].textContent = get_display_value(document.getElementById(e.target.id));
    });
};


// Read slider's data attributes, convert element's value to desired range as either float or int
function get_display_value(slider) {
    // Get slider value range
    const vmin = slider.min;
    const vmax = slider.max;

    // Get display range (may differ)
    const dmin = slider.dataset.displaymin;
    const dmax = slider.dataset.displaymax;

    if (slider.dataset.displaytype == "float") {
        return parseFloat(map_range(parseFloat(slider.value), parseFloat(vmin), parseFloat(vmax), parseFloat(dmin), parseFloat(dmax))).toFixed(1);

    } else {
        return parseInt(map_range(parseInt(slider.value), parseInt(vmin), parseInt(vmax), parseInt(dmin), parseInt(dmax)));
    };
};



// Maps value x in range to equivalent value in different range
function map_range(x, in_min, in_max, out_min, out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}



// Handler for rule slider plus and minus buttons
async function rule_slider_increment(button) {
    if (button.id.endsWith("down")) {
        var target = button.id.replace("-down", "");
    } else if (button.id.endsWith("up")) {
        var target = button.id.replace("-up", "");
    } else {
        return false;
    };

    const current = parseFloat(document.getElementById(target).value);

    if (button.id.split("-")[2] == "up") {
        var new_rule = current + parseFloat(button.dataset.stepsize);
    } else {
        var new_rule = current - parseFloat(button.dataset.stepsize);
    };

    // Update slider position
    document.getElementById(target).value = new_rule;
    $('input[type="range"]').rangeslider('update', true);
    // Select handle element closest to slider, update current rule displayed
    var $handle = $('.rangeslider__handle', document.getElementById(target).nextSibling);
    $handle[0].textContent = get_display_value(document.getElementById(target));
};
