// Creates DOM elements containing JSON (mocks django json_script filter)
// Takes context id (arg passed to parse_dom_context) and json contents
const createMockContext = (id, json) => {
    const mockContext = document.createElement('div');
    mockContext.id = id;
    mockContext.textContent = JSON.stringify(json);
    document.body.appendChild(mockContext);
};

export default createMockContext;
