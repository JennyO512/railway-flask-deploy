# Design Ai - built in Python using the microframework Flask. 

## Overview

DesignAi is a custom built Python web application powered by Flask. The application takes an input picture of your room and generates a newly designed version of it. It features Stripe integration for payment processing and leverages webhooks to update the backend database in real-time.

## Features

- **Image Upload**: Users can upload an image of their room for redesigning.
- **Stripe Integration**: Integrated Stripe for seamless payments.
- **Real-time Updates**: Webhooks keep the backend database up-to-date.
  
## Installation

1. Clone the repository
2. Change into the directory
3. Install the requirements
4. Run the application


## Usage

Open your web browser and go to `http://127.0.0.1:5000/`

## APIs and Webhooks

### Stripe API

Make sure to set your Stripe API keys before running the application.

### Webhooks

To set up webhooks, refer to the official [Stripe documentation](https://stripe.com/docs/webhooks).

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
