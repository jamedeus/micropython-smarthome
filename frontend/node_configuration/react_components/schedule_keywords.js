// Get schedule keywords object from element created by django template
const schedule_keywords = JSON.parse(document.getElementById("schedule_keywords").textContent);


// Returns array of dropdown options for each existing schedule keyword
function get_schedule_keywords_options() {
    return Object.entries(schedule_keywords).map(([key, type]) => (
        <option key={key} value={key}>{key}</option>
    ));
};


export { schedule_keywords, get_schedule_keywords_options };
