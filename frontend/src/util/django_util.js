import Cookies from 'js-cookie';

// Takes name of context element created with json_script django tag
// Parses JSON contents if it exists and returns, otherwise returns null
const parse_dom_context = (name) => {
    const element = document.getElementById(name);
    if (element) {
        return JSON.parse(element.textContent);
    } else {
        return null;
    }
};

// Takes endpoint and POST body, makes backend request, returns response
const send_post_request = async (url, body) => {
    const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken')
        }
    });
    return response;
};

export {
    parse_dom_context,
    send_post_request
};
