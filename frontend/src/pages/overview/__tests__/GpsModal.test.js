import React from 'react';
import App from '../Overview';
import { OverviewContextProvider } from 'root/OverviewContext';
import createMockContext from 'src/testUtils/createMockContext';
import { mockContext } from './mockContext';
import { postHeaders } from 'src/testUtils/headers';

// Response returned by https://geocode.maps.co/search?q=portland
const mockGeocodeApiResponse = [
    {
        "place_id": 289554434,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "node",
        "osm_id": 1666626393,
        "boundingbox": [
            "45.3602471",
            "45.6802471",
            "-122.834194",
            "-122.514194"
        ],
        "lat": "45.5202471",
        "lon": "-122.674194",
        "display_name": "Portland, Multnomah County, Oregon, 97204, United States",
        "class": "place",
        "type": "city",
        "importance": 0.7535657174337683
    },
    {
        "place_id": 323443550,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 132500,
        "boundingbox": [
            "43.5443477",
            "43.7276965",
            "-70.3473997",
            "-69.9758509"
        ],
        "lat": "43.6573605",
        "lon": "-70.2586618",
        "display_name": "Portland, Cumberland County, Maine, United States",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.6529710139286798
    },
    {
        "place_id": 279834114,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "node",
        "osm_id": 151363348,
        "boundingbox": [
            "27.8418828",
            "27.9218828",
            "-97.3588666",
            "-97.2788666"
        ],
        "lat": "27.8818828",
        "lon": "-97.3188666",
        "display_name": "Portland, San Patricio County, Texas, 78374, United States",
        "class": "place",
        "type": "town",
        "importance": 0.5441005849249448
    },
    {
        "place_id": 329706863,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 127875,
        "boundingbox": [
            "40.411974",
            "40.461887",
            "-85.009914",
            "-84.959248"
        ],
        "lat": "40.4344895",
        "lon": "-84.9777455",
        "display_name": "Portland, Jay County, Indiana, United States",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.49697098952910923
    },
    {
        "place_id": 272021330,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 319344,
        "boundingbox": [
            "17.9868561",
            "18.2668071",
            "-76.7529616",
            "-76.2579771"
        ],
        "lat": "18.12682065",
        "lon": "-76.53740115177655",
        "display_name": "Portland, Surrey County, Jamaica",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.4920623348269526
    },
    {
        "place_id": 292081814,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 181721,
        "boundingbox": [
            "47.49062",
            "47.505902",
            "-97.378755",
            "-97.357012"
        ],
        "lat": "47.4983191",
        "lon": "-97.3703689",
        "display_name": "Portland, Traill County, North Dakota, 58274, United States",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.4810167259253667
    },
    {
        "place_id": 297262424,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 8527098,
        "boundingbox": [
            "33.2265608",
            "33.2473896",
            "-91.522173",
            "-91.4985818"
        ],
        "lat": "33.2378972",
        "lon": "-91.5115095",
        "display_name": "Portland, Ashley County, Arkansas, United States",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.4789448535430544
    },
    {
        "place_id": 330940584,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 134699,
        "boundingbox": [
            "42.8524425",
            "42.8839195",
            "-84.9260695",
            "-84.867058"
        ],
        "lat": "42.8692006",
        "lon": "-84.9030517",
        "display_name": "Portland, Ionia County, Michigan, 48875, United States",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.47680090174386036
    },
    {
        "place_id": 17829466,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 3175109,
        "boundingbox": [
            "-38.40652",
            "-38.320566",
            "141.566768",
            "141.650214"
        ],
        "lat": "-38.3456231",
        "lon": "141.6042304",
        "display_name": "Portland, Shire of Glenelg, Victoria, 3305, Australia",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.47242196006679893
    },
    {
        "place_id": 299795211,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 197244,
        "boundingbox": [
            "36.524413",
            "36.652486",
            "-86.6074753",
            "-86.4323"
        ],
        "lat": "36.5817089",
        "lon": "-86.5163833",
        "display_name": "Portland, Sumner County, Middle Tennessee, Tennessee, 37148, United States",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.4722753906769793
    }
];

describe('GpsModal', () => {
    let app, user;

    beforeAll(() => {
        // Create mock state objects
        createMockContext('not_uploaded', mockContext.not_uploaded);
        createMockContext('uploaded', mockContext.uploaded);
        createMockContext('schedule_keywords', mockContext.schedule_keywords);
        createMockContext('desktop_integration_link', mockContext.desktop_integration_link);
        createMockContext('client_ip', mockContext.client_ip);
    });

    beforeEach(async () => {
        // Render app + create userEvent instance to use in tests
        user = userEvent.setup();
        app = render(
            <OverviewContextProvider>
                <App />
            </OverviewContextProvider>
        );

        // Click "Set GPS coordinates" dropdown option in top-right corner menu
        const header = app.getByText('Configure Nodes').parentElement;
        await user.click(within(header).getAllByRole('button')[0]);
        await user.click(app.getByText('Set GPS coordinates'));
    });

    it('loads suggestions when user types in input', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(mockGeocodeApiResponse)
        }));

        // Simulate user typing location in input
        const modal = app.getByText('Set Default Location').parentElement.parentElement;
        await user.type(within(modal).getByRole('textbox'), 'portland');

        // Confirm correct API call made, confirm suggestions appeared
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('https://geocode.maps.co/search?q=portland');
            expect(app.queryByText(/Portland, Multnomah County, Oregon/)).not.toBeNull();
            expect(app.queryByText(/Portland, Cumberland County, Maine/)).not.toBeNull();
            expect(app.queryByText(/Portland, San Patricio County, Texas/)).not.toBeNull();
        }, { timeout: 2500 });

        // Clear input, confirm suggestions are removed
        await user.clear(within(modal).getByRole('textbox'));
        expect(app.queryByText(/Portland, Multnomah County, Oregon/)).toBeNull();
        expect(app.queryByText(/Portland, Cumberland County, Maine/)).toBeNull();
        expect(app.queryByText(/Portland, San Patricio County, Texas/)).toBeNull();
    });

    it('makes correct request when user selects a location', async () => {
        // Mock fetch function to return expected response
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(mockGeocodeApiResponse)
        }));

        // Simulate user typing location in input, clicking first suggestion
        const modal = app.getByText('Set Default Location').parentElement.parentElement;
        await user.type(within(modal).getByRole('textbox'), 'portland');
        await waitFor(() => {
            expect(app.queryByText(/Portland, Multnomah County, Oregon/)).not.toBeNull();
        }, { timeout: 2500 });
        await user.click(app.getByText(/Portland, Multnomah County, Oregon/));

        // Confirm correct request was sent
        expect(global.fetch).toHaveBeenCalledWith('/set_default_location', {
            method: 'POST',
            body: JSON.stringify({
                "name": "Portland, Multnomah County, Oregon, 97204, United States",
                "lat": "45.5202471",
                "lon": "-122.674194",
            }),
            headers: postHeaders
        });
    });

    it('closes modal when X button or background is clicked', async () => {
        // Click close button, confirm modal closes
        await user.click(app.getByText('Set Default Location').parentElement.children[2]);
        expect(app.queryByText('Set Default Location')).toBeNull();

        // Open modal again, click backdrop, confirm modal closes
        await user.click(app.getByText('Set GPS coordinates'));
        await user.click(document.querySelector('.modal-backdrop'));
        expect(app.queryByText('Set Default Location')).toBeNull();
    });
});
