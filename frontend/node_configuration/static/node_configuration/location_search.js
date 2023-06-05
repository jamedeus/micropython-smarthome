// API returns array of up to 10 possible matches
async function api_call(search) {
    let response = await fetch(`https://geocode.maps.co/search?q=${encodeURIComponent(search)}`);
    let data = await response.json();
    return data
};


function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        return new Promise((resolve) => {
            timeout = setTimeout(() => {
                resolve(func(...args));
            }, wait);
        });
    };
};


// Prevent calling more than once every 2 seconds (rate limit)
const debounced_api_call = debounce(async function(search) {
    return await api_call(search);
}, 2000);


// Add listener to search box
document.getElementById('location').addEventListener('input', function(e) {
    if (e.target.value.length > 0) {
        // Show loading message while waiting for API response
        document.getElementById('suggestions').innerHTML = `<li class="list-group-item">Loading suggestions...</li>`;
        get_suggestions(e.target.value);
    } else {
        // Remove loading message when field cleared
        document.getElementById('suggestions').innerHTML = '';
    };
});


// Add suggestions for current search string while user types
async function get_suggestions(search) {
    const data = await debounced_api_call(search);

    // Clear old suggestions/loading message
    suggestions.innerHTML = '';

    // Add list item for each suggestion in API response
    data.forEach(item => {
        let suggestion = document.createElement('a');
        suggestion.innerHTML = item.display_name;
        suggestion.classList.add('list-group-item', 'list-group-item-action')
        suggestion.onclick = function() { select_location(item.display_name); };
        document.getElementById('suggestions').appendChild(suggestion);
    });
};


// Called when user clicks suggestion under search box
async function select_location(location) {
    gpsModal.hide();
    const data = await debounced_api_call(location);

    const body = {
        'name': location,
        'lat': data[0].lat,
        'lon': data[0].lon
    }
    send_post_request('set_default_location', body)
};
