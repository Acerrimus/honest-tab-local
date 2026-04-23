import { getDataTestIdElement } from "../../helpers";
import { createUserOrderApi, generateOrderDetails } from "../../steps/orders";
import { assertStripeLineItemsMatchExpected } from "../../steps/stripe";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user orders multiple of the same item", () => {
  const username = generateUsername();

  before(() => {
    createGuestUserApi(username);
    for (let i = 0; i < 3; i++) {
      let itemName = "REGISTERED TEST ITEM";
      createUserOrderApi(generateOrderDetails(username, itemName));
      if (!i) {
        continue;
      }
      itemName = `${itemName}${i}`;
      const item = generateOrderDetails(username, itemName);
      item.quantity = 4.0;
      item.total = 4.0;
      createUserOrderApi(item);
      if (i === 2) {
        createUserOrderApi(generateOrderDetails(username, itemName));
      }
    }
  });

  it("the items will be summarised in the line items", () => {
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("ordered_item");
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("radio-input-yes").click();
    getDataTestIdElement("submit-button").click();
    getDataTestIdElement("stripe_qr_code_image");
    assertStripeLineItemsMatchExpected([
      {
        price_data: {
          currency: "eur",
          product_data: {
            name: "REGISTERED TEST ITEM",
          },
          unit_amount: 100,
        },
        quantity: 3,
      },
      {
        price_data: {
          currency: "eur",
          product_data: {
            name: "REGISTERED TEST ITEM1",
          },
          unit_amount: 100,
        },
        quantity: 4,
      },
      {
        price_data: {
          currency: "eur",
          product_data: {
            name: "REGISTERED TEST ITEM2",
          },
          unit_amount: 100,
        },
        quantity: 5,
      },
      {
        price_data: {
          currency: "eur",
          product_data: {
            name: "System Provider Handling Fee",
          },
          unit_amount: 39,
        },
        quantity: 1,
      },
    ]);
  });
});
