// Get schedule keywords object from element created by django template
const schedule_keywords = JSON.parse(document.getElementById("schedule_keywords").textContent);

export { schedule_keywords };
