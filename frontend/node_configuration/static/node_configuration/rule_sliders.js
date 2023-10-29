// Initialize all range sliders, add listeners
for (slider of $('input[type="range"]')) {
    add_new_slider(slider);
};


// Takes slider, initializes and adds listener to update displayed value
function add_new_slider(slider) {
    // Initialize
    $(slider).rangeslider({
        polyfill: false,
        onInit: function() {
            // Select handle element closest to slider, update displayed rule
            $handle = $('.rangeslider__handle', this.$range);
            $handle[0].textContent = get_display_value(slider);
            this.$range[0].classList.add("mx-auto")
        }
    });

    // Update current rule displayed while slider moves
    $(slider).on('input', function(e) {
        // Select handle element closest to slider, update displayed rule
        var $handle = $('.rangeslider__handle', e.target.nextSibling);
        $handle[0].textContent = get_display_value(e.target);
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
};


// Handler for rule slider plus and minus buttons, updates slider position
// Used by both configuration page and frontend
async function rule_slider_increment(button) {
    // Get reference to target slider, current value
    const slider = button.parentElement.querySelector('input[type="range"]');
    const current = parseFloat(slider.value);

    // Increment/decrement current value
    if (button.dataset.direction === "up") {
        slider.value = current + parseFloat(button.dataset.stepsize);
    } else {
        slider.value = current - parseFloat(button.dataset.stepsize);
    };

    // Update slider position
    $('input[type="range"]').rangeslider('update', true);
    // Select handle element closest to slider, update current rule displayed
    var $handle = $('.rangeslider__handle', slider.nextSibling);
    $handle[0].textContent = get_display_value(slider);

    // Call overridable post-routine function
    // configuration: triggers change event on slider to update config
    // frontend: sends increment_rule API call to target node
    rule_slider_increment_post_routine(button, slider);
};


// Called by rule_slider_increment (overridden in api rule_sliders.js)
function rule_slider_increment_post_routine(button, slider) {
    // Trigger slider listener that updates config object
    const change = new Event('change');
    slider.dispatchEvent(change);
};
