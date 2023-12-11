import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import { ErrorModal } from 'modals/ErrorModal';
import { ModalContextProvider } from 'modals/ModalContextProvider';
import Header from './Header';
import Layout from './Layout';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import 'css/api_card.css';


const App = () => {
    return (
        <ModalContextProvider>
            <div className="fade-in">
                <Header />
                <Layout />

                {/* Modals (hidden) */}
                <ErrorModal />
            </div>
        </ModalContextProvider>
    );
};


export default App;
