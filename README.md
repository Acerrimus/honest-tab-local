# Honest Tab

A digital POS/tab system for small businesses, written in Python with [Reflex](https://reflex.dev/). Created for the [Olive Branch hostel](https://www.olivebranchelchorro.com/) in El Chorro, Spain.

Contents:

1. [Setup](#setup)
2. [Local Database](#local-database)
3. [How To Contribute](#how-to-contribute)

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

## Local Database

This app uses SQLite to store an offline verison of the Google Sheet.

To access it run `sqlite3 reflex.db`

## Contributing

### Branches

`main` represents live production code. **Do not commit directly to this branch.**

`ci` is the current state of development. Please do not commit directly to this branch unless it is a minor fix.

### How To Contribute

Create a new branch for your changes. Ideally create a pull request so it can be reviewed by a collaborator. Once approved merge these changes into the `ci` branch.

Once agreed features are complete in `ci` it will be merged into `main`.

### Altering the SQLite Database

Honest Tab uses [SQLAlchemy v1.4](https://docs.sqlalchemy.org/en/14/orm/quickstart.html) ORM as part of Reflex to manage and interact with the SQLite database.

How to make changes to the SQLite databaser:

1. Make your changes to tables in `obhonesty/models.py`
2. Run `reflex db makemigrations` to generate new version files.
3. Run `reflex db migrate` to apply these changes to the db.