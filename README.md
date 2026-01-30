# Honest tab

A digital POS/tab system for small businesses.

## Setup

### Installation 

#### Container with Docker

To run with Docker: `docker compose up`

This will install all requirements and run the app.

Once running open [http://localhost:3000/](http://localhost:3000/) in a browser to use the app.

#### Running natively on Linux

In a bash shell run `. requirements.bash`.

This will install requirements and activate the virtual environment.

Then run `reflex run`.

Once running open [http://localhost:3000/](http://localhost:3000/) in a browser to use the app.

### Backend setup

#### Google Service Account

This app uses Google Sheets as a database.

To setup:
1. Create a copy of
[this sheet](https://docs.google.com/spreadsheets/d/1get0Mcr_Pso1B3Nn-VtQV4gqKDYVcn9-zus1u1Xddh8/edit?usp=sharing)
(requires a google account).
2. Follow steps 1-6 of
[this guide](https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account).
3. Create a `.credentials` folder within `honest-tab-local`.
4. Retitle the downloaded json file from the above guide to `service_account.json`.
5. Move the file to the `.credentials` folder. The full path should be `./.credentials/service_account.json`.

#### Stripe

Stripe is used to collect payment.

To setup:
1. Create a free Stripe account at [https://stripe.com/](https://stripe.com/)
2. Copy the private key and put in in a `.env` file with the key `STRIPE_SECRET_KEY`.
3. It should look like `STRIPE_SECRET_KEY=XXXXXXXXX...`