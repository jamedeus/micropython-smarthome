import React, { useState, useCallback } from 'react';
import Dropdown from 'react-bootstrap/Dropdown';
import ListGroup from 'react-bootstrap/ListGroup';
import ListGroupItem from 'react-bootstrap/ListGroupItem';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { send_post_request } from 'util/django_util';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { debounce } from 'util/helper_functions';

export const GpsModal = () => {
    // Create state object to control visibility
    const [ visible, setVisible ] = useState(false);

    // Create state object for location search results
    const [ locationResults, setLocationResults ] = useState([]);

    // API returns array of up to 10 possible matches
    async function api_call(search) {
        const response = await fetch(
            `https://geocode.maps.co/search?q=${encodeURIComponent(search)}`
        );
        const data = await response.json();
        return data;
    }

    // Debounced API call, writes results to state object
    // Triggers re-render with list item for each search result
    const debounced_api_call = useCallback(debounce(async (search) => {
        const data = await api_call(search);
        setLocationResults(data);
    }, 2000), []);

    // Listener for search field, makes API call and adds suggestion for each result
    async function get_suggestions(search) {
        // Clear suggestions when field emptied
        if (search.length === 0) {
            setLocationResults([]);
        // Make call and add suggestionse (debouced) when user types
        } else {
            setLocationResults([{
                display_name: "Loading suggestions...",
                place_id: "loading"
            }]);
            debounced_api_call(search);
        }
    }

    // Called when user clicks result, posts coordinates to backend
    async function select_location(name, lat, lon) {
        send_post_request('set_default_location', {name, lat, lon});
        setVisible(false);
    }

    return (
        <>
            <Dropdown.Item onClick={() => setVisible(true)}>
                Set GPS coordinates
            </Dropdown.Item>

            <Modal show={visible} onHide={() => setVisible(false)} centered>
                <HeaderWithCloseButton
                    title="Set Default Location"
                    onClose={() => setVisible(false)}
                />

                <Modal.Body className="d-flex flex-column mx-auto text-center">
                    <p>Approximate GPS coordinates are used to determine sunrise and sunset times. This is looked up from your IP by default.</p>

                    <p>If your sunrise and sunset times are incorrect, type a city/state below and click the closest suggestion.</p>

                    <Form.Control
                        type="text"
                        placeholder="Location Search"
                        className="text-center"
                        onChange={(e) => get_suggestions(e.target.value)}
                    />
                    <ListGroup className="mt-2">
                        {locationResults.map((suggestion) => {
                            return (
                                <ListGroupItem action key={suggestion.place_id}
                                    onClick={() => select_location(
                                        suggestion.display_name,
                                        suggestion.lat,
                                        suggestion.lon
                                    )}
                                >
                                    {suggestion.display_name}
                                </ListGroupItem>
                            );
                        })}
                    </ListGroup>
                </Modal.Body>
            </Modal>
        </>
    );
};
