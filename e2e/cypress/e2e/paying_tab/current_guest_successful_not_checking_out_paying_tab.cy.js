import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderApi,
  generateOrderDetails,
  getUserOrdersApi,
} from "../../steps/orders";
import { getPaymentApi } from "../../steps/payments";
import {
  assertStripeLineItemsMatchExpected,
  triggerSuccessfulStripePayment,
} from "../../steps/stripe";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe(
  "When a current guest successfully pays their tab and chooses to not check out",
  { testIsolation: false, tags: "@payments" },
  () => {
    const username = generateUsername();
    it("they will stay logged in and their paid items will not be in their tab", () => {
      createGuestUserApi(username);
      const itemNames = [1, 2, 3].map((num) => `REGISTERED TEST ITEM${num}`);
      const orderDetails = itemNames.map((itemName) =>
        generateOrderDetails(username, itemName),
      );
      cy.wrap(orderDetails).each((orderDetail) => {
        createUserOrderApi(orderDetail);
      });
      cy.visit("/");
      logUserOn(username);
      getDataTestIdElement("pay-tab-button").click();
      getDataTestIdElement("ordered_item").should("have.lengthOf", 3);
      getDataTestIdElement("pay-tab-button").click();
      getDataTestIdElement("radio-input-no").click();
      getDataTestIdElement("submit-button").click();
      getDataTestIdElement("total-amount-due").should(
        "have.text",
        "Total amount due: €3.00",
      );
      getDataTestIdElement("stripe-subtotal").should(
        "have.text",
        "Subtotal: €3.00",
      );
      getDataTestIdElement("stripe-handling-fee").should(
        "have.text",
        "System Provider Handling Fee: €0.10",
      );
      getDataTestIdElement("stripe-total").should("have.text", "Total: €3.10");
      getDataTestIdElement("stripe_qr_code_image");
      triggerSuccessfulStripePayment();
      getDataTestIdElement("stripe_payment_successful_text").should(
        "be.visible",
      );
      getDataTestIdElement("stripe_dialog_close").click();
      cy.contains("Tab paid successfully!");
      getDataTestIdElement("pay-tab-button").click();
      getDataTestIdElement("total-amount-due").should(
        "have.text",
        "Total amount due: €0.00",
      );
      getDataTestIdElement("ordered_item").should("not.exist");
    });

    it("all their orders will have a paid status", () => {
      cy.waitUntil(() =>
        getUserOrdersApi(username).then((response) => {
          cy.wrap(response.body.orders).each((order) => {
            getPaymentApi(order.order_id).then((paymentResponse) => {
              expect(paymentResponse.body.payment.order_id).to.eq(
                order.order_id,
              );
            });
          });
        }),
      );
    });

    it("will record the line items correctly for Stripe", () => {
      assertStripeLineItemsMatchExpected([
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: "REGISTERED TEST ITEM1",
            },
            unit_amount: 100,
          },
          quantity: 1,
        },
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: "REGISTERED TEST ITEM2",
            },
            unit_amount: 100,
          },
          quantity: 1,
        },
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: "REGISTERED TEST ITEM3",
            },
            unit_amount: 100,
          },
          quantity: 1,
        },
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: "System Provider Handling Fee",
            },
            unit_amount: 10,
          },
          quantity: 1,
        },
      ]);
    });
  },
);
