import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderApi,
  generateFormattedTime,
  generateOrderDetails,
} from "../../steps/orders";
import { assertStripeLineItemsMatchExpected } from "../../steps/stripe";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When there are more than 100 line items", () => {
  const username = generateUsername();
  const line_items = [
    {
      price_data: {
        currency: "eur",
        product_data: {
          name: "System Provider Handling Fee",
        },
        unit_amount: 341,
      },
      quantity: 1,
    },
    {
      price_data: {
        currency: "eur",
        product_data: {
          name: "Remaining item total - see reception for full receipt",
        },
        unit_amount: 700,
      },
      quantity: 1,
    },
  ];

  before(() => {
    createGuestUserApi(username);
    const orderTime = new Date();
    for (let i = 0; i < 105; i++) {
      const itemName = `REGISTERED TEST ITEM${("000" + i).substr(-3)}`;
      const orderDetails = generateOrderDetails(username, itemName);
      orderTime.setTime(orderTime.getTime() + i * 1000);
      orderDetails.time = generateFormattedTime(orderTime);
      createUserOrderApi(orderDetails);
      if (i < 98) {
        line_items.push({
          price_data: {
            currency: "eur",
            product_data: {
              name: itemName,
            },
            unit_amount: 100,
          },
          quantity: 1,
        });
      }
    }
  });

  it("there will be 98 items, a summary of the rest of the items, and the handling fee", () => {
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("ordered_item");
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("radio-input-yes").click();
    getDataTestIdElement("submit-button").click();
    getDataTestIdElement("stripe_qr_code_image");
    assertStripeLineItemsMatchExpected(line_items);
  });
});
