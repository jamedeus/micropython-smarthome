import React, { createContext, useContext, useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import ListGroup from 'react-bootstrap/ListGroup';
import ListGroupItem from 'react-bootstrap/ListGroupItem';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { send_post_request } from 'util/django_util';

export const GpsModalContext = createContext();

export const GpsModalContextProvider = ({ children }) => {
    // Create state object to control visibility
    const [ show, setShow ] = useState(false);

    const handleClose = () => {
        setShow(false);
    };

    const showGpsModal = () => {
        setShow(true);
    };

    return (
        <GpsModalContext.Provider value={{ show, handleClose, showGpsModal }}>
            {children}
        </GpsModalContext.Provider>
    );
};

GpsModalContextProvider.propTypes = {
    children: PropTypes.node,
};

export const GpsModal = () => {
    // Get state object that controls visibility
    const { show, handleClose } = useContext(GpsModalContext);

    // Create state object for location search results
    const [ locationResults, setLocationResults ] = useState([]);

    // API returns array of up to 10 possible matches
    async function api_call(search) {
        let response = await fetch(`https://geocode.maps.co/search?q=${encodeURIComponent(search)}`);
        let data = await response.json();
        return data;
    }

    const debounce = (func, wait) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func(...args);
            }, wait);
        };
    };

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
            setLocationResults([{display_name: "Loading suggestions..."}]);
            debounced_api_call(search);
        }
    }

    // Called when user clicks result, posts coordinates to backend
    async function select_location(name, lat, lon) {
        let data = {name, lat, lon};
        send_post_request('set_default_location', data);
        handleClose();
    }

    return (
        <Modal show={show} onHide={handleClose} centered>
            <Modal.Header className="justify-content-between pb-0">
                <button type="button" className="btn-close" style={{visibility: "hidden"}}></button>
                <h5 className="modal-title">Set Default Location</h5>
                <button type="button" className="btn-close" onClick={() => handleClose()}></button>
            </Modal.Header>

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
                            <ListGroupItem onClick={() => select_location(
                                suggestion.display_name,
                                suggestion.lat,
                                suggestion.lon
                            )}>
                                {suggestion.display_name}
                            </ListGroupItem>
                        );
                    })}
                </ListGroup>
            </Modal.Body>
        </Modal>
    );
};
