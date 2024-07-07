// Generated using webpack-cli https://github.com/webpack/webpack-cli

const path = require('path');

const isProduction = process.env.NODE_ENV == 'development';

const config = {
    entry: {
        edit_config: './src/pages/edit_config/index.js',
        overview: './src/pages/overview/index.js',
        api_overview: './src/pages/api_overview/index.js',
        api_card: './src/pages/api_card/index.js',
        unable_to_connect: './src/pages/unable_to_connect/index.js',
    },
    output: {
        path: path.resolve(__dirname, 'node_configuration/static/node_configuration/'),
        filename: '[name].js'
    },
    externals: {
        'react': 'React',
        'react-dom': 'ReactDOM',
        'react-transition-group': 'ReactTransitionGroup'
    },
    devServer: {
        open: true,
        host: 'localhost',
    },
    plugins: [
        // Add your plugins here
        // Learn more about plugins from https://webpack.js.org/configuration/plugins/
    ],
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/i,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                },

            },
            {
                test: /\.(css|s(a|c)ss)$/,
                use: ['style-loader', 'css-loader', 'sass-loader']
            }

            // Add your rules for custom modules here
            // Learn more about loaders from https://webpack.js.org/loaders/
        ],
    },
    resolve: {
        alias: {
            css: path.resolve(__dirname, 'src/css'),
            root: path.resolve(__dirname, 'src/'),
            util: path.resolve(__dirname, 'src/util/'),
            inputs: path.resolve(__dirname, 'src/inputs/'),
            modals: path.resolve(__dirname, 'src/modals/'),
            node_modules: path.resolve(__dirname, 'node_modules/')
        }
    }
};

module.exports = () => {
    if (isProduction) {
        config.mode = 'production';
    } else {
        config.mode = 'development';
    }
    return config;
};
